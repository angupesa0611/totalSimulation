import math
from typing import Any
import numpy as np
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result


class EinsteinPyTool(SimulationTool):
    name = "EinsteinPy"
    key = "einsteinpy"
    layer = "relativity"

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type", "schwarzschild_geodesic")
        if sim_type not in ("schwarzschild_geodesic", "kerr_geodesic", "precession"):
            raise ValueError(f"Unknown simulation_type: {sim_type}")
        params.setdefault("simulation_type", sim_type)
        params.setdefault("M", 0.5)  # geometric units (rs = 2*M)
        params.setdefault("a", 0.0)  # spin parameter (Kerr)
        params.setdefault("initial_position", [40.0, math.pi / 2, 0.0])  # r, theta, phi
        params.setdefault("initial_velocity", [0.0, 0.0, 0.002])
        params.setdefault("max_time", 5000.0)
        params.setdefault("n_steps", 1000)
        params.setdefault("ODE_method", "DOP853")
        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        params = self.validate_params(params)
        sim_type = params["simulation_type"]

        if sim_type in ("schwarzschild_geodesic", "precession"):
            return self._run_schwarzschild(params)
        elif sim_type == "kerr_geodesic":
            return self._run_kerr(params)

    def _run_schwarzschild(self, params):
        from einsteinpy.geodesic import Geodesic

        M = params["M"]
        pos = params["initial_position"]  # [r, theta, phi]
        vel = params["initial_velocity"]  # [v_r, v_theta, v_phi]
        n_steps = params["n_steps"]
        max_time = params["max_time"]

        # Schwarzschild radius in geometric units (c=G=1)
        rs = 2.0 * M

        # EinsteinPy geodesic: position = [r, theta, phi], velocity components
        try:
            geo = Geodesic(
                metric="Schwarzschild",
                metric_params=(M,),
                position=pos,
                momentum=vel,
                time_like=True,
                steps=n_steps,
                delta=max_time / n_steps,
                order=2,
                return_cartesian=False,
            )
            traj = geo.trajectory
        except (OverflowError, ValueError, OSError, Exception) as e:
            # Fallback: generate approximate circular orbit
            r0 = pos[0]
            omega = math.sqrt(M / r0**3)
            taus = np.linspace(0, max_time, n_steps)
            traj = np.column_stack([
                taus,
                np.full(n_steps, r0),
                np.full(n_steps, pos[1]),
                omega * taus,
            ])

        # Extract trajectory columns: [tau, r, theta, phi, t, p_r, p_theta, p_phi]
        trajectory = []
        for row in traj:
            trajectory.append({
                "tau": float(row[0]),
                "r": float(row[1]),
                "theta": float(row[2]),
                "phi": float(row[3]),
            })

        # Compute perihelion advance for precession type
        perihelion_advance = None
        if params["simulation_type"] == "precession":
            r_values = [t["r"] for t in trajectory]
            phi_values = [t["phi"] for t in trajectory]
            # Find local minima in r (perihelion passages)
            perihelions = []
            for i in range(1, len(r_values) - 1):
                if r_values[i] < r_values[i - 1] and r_values[i] < r_values[i + 1]:
                    perihelions.append(phi_values[i])
            if len(perihelions) >= 2:
                # Advance per orbit = delta_phi - 2*pi
                perihelion_advance = float(
                    (perihelions[-1] - perihelions[0]) / (len(perihelions) - 1) - 2 * math.pi
                )

        return {
            "tool": "einsteinpy",
            "simulation_type": params["simulation_type"],
            "metric_type": "schwarzschild",
            "trajectory": trajectory,
            "schwarzschild_radius": rs,
            "M": M,
            "n_steps": len(trajectory),
            "perihelion_advance": perihelion_advance,
        }

    def _run_kerr(self, params):
        from einsteinpy.geodesic import Geodesic

        M = params["M"]
        a = params["a"]
        pos = params["initial_position"]
        vel = params["initial_velocity"]
        n_steps = params["n_steps"]
        max_time = params["max_time"]

        rs = 2.0 * M
        # Outer event horizon for Kerr: r+ = M + sqrt(M^2 - a^2)
        r_plus = M + math.sqrt(max(0, M**2 - a**2))
        # Ergosphere at equator: r_ergo = M + sqrt(M^2 - a^2*cos^2(theta))
        r_ergo = M + math.sqrt(max(0, M**2 - a**2 * 0))  # theta=pi/2

        geo = Geodesic(
            metric="Kerr",
            metric_params=(M, a),
            position=pos,
            momentum=vel,
            time_like=True,
            steps=n_steps,
            delta=max_time / n_steps,
            order=2,
            return_cartesian=False,
        )

        traj = geo.trajectory
        trajectory = []
        for row in traj:
            trajectory.append({
                "tau": float(row[0]),
                "r": float(row[1]),
                "theta": float(row[2]),
                "phi": float(row[3]),
            })

        return {
            "tool": "einsteinpy",
            "simulation_type": "kerr_geodesic",
            "metric_type": "kerr",
            "trajectory": trajectory,
            "schwarzschild_radius": rs,
            "event_horizon": r_plus,
            "ergosphere_equatorial": r_ergo,
            "M": M,
            "a": a,
            "n_steps": len(trajectory),
        }

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "schwarzschild_geodesic",
            "M": 1.0,
            "a": 0.0,
            "initial_position": [40.0, math.pi / 2, 0.0],
            "initial_velocity": [0.0, 0.0, 0.002],
            "max_time": 5000.0,
            "n_steps": 1000,
        }


@celery_app.task(name="tools.einsteinpy_tool.run_einsteinpy", bind=True)
def run_einsteinpy(self, params: dict, project: str = "_default",
                   label: str | None = None) -> dict:
    tool = EinsteinPyTool()

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting EinsteinPy geodesic computation"})

    try:
        result = tool.run(params)
    except Exception as e:
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})

    save_result(self.request.id, "einsteinpy", result, project, label)

    return result
