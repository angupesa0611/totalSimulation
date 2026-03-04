import math
from typing import Any
import numpy as np
import rebound
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result

GR_CORRECTIONS = {"none", "gr", "gr_full", "gr_potential"}
EXTRA_FORCES = {"radiation_pressure", "tides_constant_time_lag"}


class REBOUNDTool(SimulationTool):
    name = "REBOUND"
    key = "rebound"
    layer = "astrophysics"

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        if "particles" not in params or not params["particles"]:
            raise ValueError("At least one particle required")
        if "tmax" not in params:
            raise ValueError("tmax is required")
        params.setdefault("integrator", "ias15")
        params.setdefault("n_outputs", 500)
        params.setdefault("gr_correction", "none")
        params.setdefault("extra_forces", [])
        if params["gr_correction"] not in GR_CORRECTIONS:
            raise ValueError(f"gr_correction must be one of {GR_CORRECTIONS}")
        for f in params["extra_forces"]:
            if f not in EXTRA_FORCES:
                raise ValueError(f"Unknown extra force: {f}. Must be one of {EXTRA_FORCES}")
        return params

    def _attach_reboundx(self, sim, params):
        """Attach REBOUNDx effects (GR corrections, extra forces) to the simulation."""
        gr = params["gr_correction"]
        extras = params["extra_forces"]
        if gr == "none" and not extras:
            return None

        import reboundx
        rebx = reboundx.Extras(sim)
        c_au_yr = 63241.077  # speed of light in AU/yr

        if gr != "none":
            effect = rebx.load_force(gr)
            rebx.add_force(effect)
            effect.params["c"] = c_au_yr

        for force_name in extras:
            effect = rebx.load_force(force_name)
            rebx.add_force(effect)
            if force_name == "radiation_pressure":
                effect.params["c"] = c_au_yr

        return rebx

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        params = self.validate_params(params)
        sim = rebound.Simulation()
        sim.integrator = params["integrator"]
        sim.units = ("yr", "AU", "Msun")

        if params.get("dt"):
            sim.dt = params["dt"]

        # Add particles
        names = []
        for p in params["particles"]:
            name = p.pop("name", None)
            names.append(name or f"particle_{len(names)}")
            # Strip client-only keys (e.g. _mode)
            for k in [k for k in p if k.startswith("_")]:
                p.pop(k)
            if "a" in p:
                primary_ref = p.pop("primary", 0)
                # Resolve string name to integer index
                if isinstance(primary_ref, str):
                    try:
                        primary_ref = names.index(primary_ref)
                    except ValueError:
                        primary_ref = 0
                primary = sim.particles[primary_ref] if sim.N > 0 else None
                sim.add(primary=primary, **p)
            else:
                sim.add(**p)

        sim.move_to_com()

        if params["integrator"] == "whfast":
            sim.ri_whfast.safe_mode = 0

        # Attach REBOUNDx effects
        self._attach_reboundx(sim, params)

        n_outputs = params["n_outputs"]
        tmax = params["tmax"]
        times = np.linspace(0, tmax, n_outputs)

        n_particles = sim.N
        positions = np.zeros((n_outputs, n_particles, 3))
        energies = np.zeros(n_outputs)

        # Track orbital elements for precession measurement
        track_precession = params["gr_correction"] != "none" and n_particles >= 2
        omegas = np.zeros(n_outputs) if track_precession else None

        for i, t in enumerate(times):
            sim.integrate(t)
            for j in range(n_particles):
                p = sim.particles[j]
                positions[i, j] = [p.x, p.y, p.z]
            energies[i] = sim.energy()
            if track_precession:
                orb = sim.particles[1].calculate_orbit(primary=sim.particles[0])
                omegas[i] = orb.omega

        result = {
            "tool": "rebound",
            "names": names,
            "times": times.tolist(),
            "positions": positions.tolist(),
            "energies": energies.tolist(),
            "n_particles": n_particles,
            "integrator": params["integrator"],
            "gr_correction": params["gr_correction"],
            "extra_forces": params["extra_forces"],
        }

        if track_precession and omegas is not None:
            result["omega_precession"] = omegas.tolist()
            # Compute total precession in arcseconds
            delta_omega_rad = omegas[-1] - omegas[0]
            delta_omega_arcsec = np.degrees(delta_omega_rad) * 3600
            result["total_precession_arcsec"] = float(delta_omega_arcsec)
            result["simulation_time_yr"] = float(tmax)

        return result

    def get_default_params(self) -> dict[str, Any]:
        return {
            "particles": [
                {"name": "Sun", "m": 1.0},
                {"name": "Earth", "m": 3.0e-6, "a": 1.0, "e": 0.0167},
            ],
            "integrator": "whfast",
            "tmax": 2 * math.pi,
            "n_outputs": 200,
            "dt": 0.01,
            "gr_correction": "none",
            "extra_forces": [],
        }


@celery_app.task(name="tools.rebound_tool.run_rebound", bind=True)
def run_rebound(self, params: dict, project: str = "_default",
                label: str | None = None) -> dict:
    tool = REBOUNDTool()

    # Update progress
    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting REBOUND simulation"})

    try:
        result = tool.run(params)
    except Exception as e:
        self.update_state(state="FAILURE", meta={"message": str(e)})
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})

    save_result(self.request.id, "rebound", result, project, label)

    return result
