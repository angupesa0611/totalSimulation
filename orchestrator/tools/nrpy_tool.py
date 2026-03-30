import math
from typing import Any
import numpy as np
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result


class NRPyTool(SimulationTool):
    name = "NRPy+"
    key = "nrpy"
    layer = "relativity"

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type", "brill_lindquist")
        if sim_type not in ("brill_lindquist", "gw_strain", "tov_star"):
            raise ValueError(f"Unknown simulation_type: {sim_type}")
        params.setdefault("simulation_type", sim_type)
        params.setdefault("mass_ratio", 1.0)
        params.setdefault("separation", 10.0)
        params.setdefault("spin1", 0.0)
        params.setdefault("spin2", 0.0)
        params.setdefault("grid_points", 200)
        params.setdefault("total_mass_solar", 60.0)
        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        params = self.validate_params(params)
        sim_type = params["simulation_type"]

        if sim_type == "brill_lindquist":
            return self._brill_lindquist(params)
        elif sim_type == "gw_strain":
            return self._gw_strain(params)
        elif sim_type == "tov_star":
            return self._tov_star(params)

    def _brill_lindquist(self, params):
        """Brill-Lindquist initial data for two black holes."""
        q = params["mass_ratio"]
        d = params["separation"]
        n = params["grid_points"]

        m1 = 1.0 / (1.0 + q)
        m2 = q / (1.0 + q)

        # 2D grid in the equatorial plane
        extent = d * 2.0
        x = np.linspace(-extent, extent, n)
        y = np.linspace(-extent, extent, n)
        X, Y = np.meshgrid(x, y)

        # BH positions along x-axis
        x1, y1 = -d / 2, 0.0
        x2, y2 = d / 2, 0.0

        # Distances from each BH (regularized)
        r1 = np.sqrt((X - x1) ** 2 + (Y - y1) ** 2 + 0.01)
        r2 = np.sqrt((X - x2) ** 2 + (Y - y2) ** 2 + 0.01)

        # Conformal factor: psi = 1 + m1/(2*r1) + m2/(2*r2)
        psi = 1.0 + m1 / (2.0 * r1) + m2 / (2.0 * r2)

        # ADM mass = m1 + m2 (for Brill-Lindquist at infinite separation)
        adm_mass = m1 + m2

        return {
            "tool": "nrpy",
            "simulation_type": "brill_lindquist",
            "conformal_factor": psi.tolist(),
            "grid_x": x.tolist(),
            "grid_y": y.tolist(),
            "ADM_mass": float(adm_mass),
            "mass1": float(m1),
            "mass2": float(m2),
            "separation": d,
            "grid_points": n,
        }

    def _gw_strain(self, params):
        """Approximate gravitational wave strain from BBH inspiral-merger-ringdown."""
        q = params["mass_ratio"]
        M_total = params["total_mass_solar"]
        spin1 = params["spin1"]
        spin2 = params["spin2"]
        n_points = params["grid_points"]

        # Masses
        m1 = M_total / (1.0 + q)
        m2 = M_total * q / (1.0 + q)
        eta = m1 * m2 / M_total**2  # symmetric mass ratio
        M_chirp = M_total * eta**(3.0 / 5.0)

        # Time array (geometric units: G=c=1, then convert)
        # Use Newtonian inspiral approximation + phenomenological merger/ringdown
        G = 6.674e-11
        c = 3e8
        M_sun = 1.989e30
        M_total_kg = M_total * M_sun
        t_scale = G * M_total_kg / c**3  # time in seconds per M

        # Inspiral phase: frequency evolves as f(t) ~ (t_c - t)^{-3/8}
        t_merger = 5.0  # in units of M_total
        t = np.linspace(-10.0, 2.0, n_points)
        dt = t[1] - t[0]

        h_plus = np.zeros(n_points)
        h_cross = np.zeros(n_points)
        frequency = np.zeros(n_points)

        for i, ti in enumerate(t):
            if ti < 0:
                # Inspiral: Newtonian quadrupole formula
                tau = max(abs(ti), 0.01)
                f_gw = 0.1 * tau**(-3.0 / 8.0) * eta**(3.0 / 8.0)
                amplitude = 4.0 * eta * tau**(-1.0 / 4.0)
                phase = -2.0 * (tau**(5.0 / 8.0)) / (5.0 * eta**(3.0 / 8.0))
                h_plus[i] = amplitude * np.cos(2.0 * np.pi * f_gw * ti + phase)
                h_cross[i] = amplitude * np.sin(2.0 * np.pi * f_gw * ti + phase)
                frequency[i] = f_gw
            elif ti < 0.5:
                # Merger: peak amplitude
                amplitude = 4.0 * eta * np.exp(-((ti) ** 2) / 0.1)
                f_peak = 0.1 * eta**(3.0 / 8.0) * 0.01**(-3.0 / 8.0)
                phase = 2.0 * np.pi * f_peak * ti
                h_plus[i] = amplitude * np.cos(phase)
                h_cross[i] = amplitude * np.sin(phase)
                frequency[i] = f_peak
            else:
                # Ringdown: damped sinusoid
                # QNM frequency ~ 0.05/(M_final), damping ~ 0.05/(M_final)
                f_qnm = 0.08 * (1.0 - 0.63 * (1.0 - spin1)**0.3)
                tau_damp = 0.5
                amplitude = 2.0 * eta * np.exp(-(ti - 0.5) / tau_damp)
                phase = 2.0 * np.pi * f_qnm * (ti - 0.5)
                h_plus[i] = amplitude * np.cos(phase)
                h_cross[i] = amplitude * np.sin(phase)
                frequency[i] = f_qnm

        # Convert time to physical units (seconds)
        t_physical = (t * t_scale).tolist()

        # Peak frequency in Hz
        peak_freq = float(np.max(frequency)) / t_scale

        return {
            "tool": "nrpy",
            "simulation_type": "gw_strain",
            "h_plus": h_plus.tolist(),
            "h_cross": h_cross.tolist(),
            "time": t_physical,
            "frequency": frequency.tolist(),
            "peak_frequency": peak_freq,
            "merger_time": float(0.0),
            "total_mass_solar": M_total,
            "mass_ratio": q,
            "chirp_mass": float(M_chirp),
            "symmetric_mass_ratio": float(eta),
        }

    def _tov_star(self, params):
        """Tolman-Oppenheimer-Volkoff equation for neutron star structure."""
        n_points = params["grid_points"]
        central_density = params.get("central_density", 5e17)  # kg/m^3

        G = 6.674e-11
        c = 3e8
        M_sun = 1.989e30

        # Simple polytropic EOS: P = K * rho^Gamma
        K = 1e5  # polytropic constant (geometric units adjusted)
        Gamma = 2.0

        def pressure(rho):
            return K * rho**Gamma

        def drho_dp(rho):
            if rho <= 0:
                return 0
            return 1.0 / (K * Gamma * rho**(Gamma - 1))

        # Integrate TOV equations
        r_max = 20000.0  # meters
        dr = r_max / n_points

        r_arr = [0.0]
        m_arr = [0.0]
        p_arr = [pressure(central_density)]
        rho_arr = [central_density]

        r = dr  # start slightly off center
        m = (4.0 / 3.0) * math.pi * central_density * dr**3
        p = pressure(central_density)
        rho = central_density

        for i in range(1, n_points):
            if p <= 0 or rho <= 0:
                break

            # TOV equation: dp/dr = -G(rho + P/c^2)(m + 4*pi*r^3*P/c^2) / (r^2(1 - 2Gm/(rc^2)))
            numerator = -G * (rho + p / c**2) * (m + 4 * math.pi * r**3 * p / c**2)
            denominator = r**2 * (1 - 2 * G * m / (r * c**2))

            if abs(denominator) < 1e-30:
                break

            dp_dr = numerator / denominator
            dm_dr = 4 * math.pi * r**2 * rho

            p += dp_dr * dr
            m += dm_dr * dr
            r += dr

            if p > 0:
                # Invert EOS to get density from pressure
                rho = (p / K) ** (1.0 / Gamma)
            else:
                p = 0
                rho = 0

            r_arr.append(r)
            m_arr.append(m)
            p_arr.append(max(0, p))
            rho_arr.append(max(0, rho))

        # Find stellar surface (where p -> 0)
        star_radius = r_arr[-1]
        star_mass = m_arr[-1] / M_sun  # in solar masses

        # Convert radius to km
        r_km = [ri / 1000.0 for ri in r_arr]

        return {
            "tool": "nrpy",
            "simulation_type": "tov_star",
            "pressure": p_arr,
            "density": rho_arr,
            "radius": r_km,
            "mass": [mi / M_sun for mi in m_arr],
            "central_density": central_density,
            "star_radius_km": star_radius / 1000.0,
            "star_mass_solar": star_mass,
            "n_points": len(r_arr),
        }

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "gw_strain",
            "mass_ratio": 1.0,
            "total_mass_solar": 60.0,
            "spin1": 0.0,
            "spin2": 0.0,
            "grid_points": 500,
        }


@celery_app.task(name="tools.nrpy_tool.run_nrpy", bind=True)
def run_nrpy(self, params: dict, project: str = "_default",
             label: str | None = None) -> dict:
    tool = NRPyTool()

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting NRPy+ computation"})

    try:
        result = tool.run(params)
    except Exception as e:
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})

    save_result(self.request.id, "nrpy", result, project, label)

    return result
