"""Strawberry Fields tool — quantum photonics simulation."""

from typing import Any

import numpy as np

# Strawberry Fields 0.23 uses scipy.integrate.simps which was removed in scipy >= 1.14.
# Monkey-patch the alias before importing SF.
from scipy.integrate import simpson
import scipy.integrate
if not hasattr(scipy.integrate, "simps"):
    scipy.integrate.simps = simpson

from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result


class StrawberryFieldsTool(SimulationTool):
    name = "Strawberry Fields"
    key = "strawberryfields"
    layer = "optics"

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type")
        valid = ("squeezed_state", "hong_ou_mandel", "boson_sampling", "gaussian_state")
        if sim_type not in valid:
            raise ValueError(f"simulation_type must be one of: {valid}")
        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        params = self.validate_params(params)
        sim_type = params["simulation_type"]

        if sim_type == "squeezed_state":
            return self._run_squeezed(params.get("squeezed_state", {}))
        elif sim_type == "hong_ou_mandel":
            return self._run_hom(params.get("hong_ou_mandel", {}))
        elif sim_type == "boson_sampling":
            return self._run_boson_sampling(params.get("boson_sampling", {}))
        elif sim_type == "gaussian_state":
            return self._run_gaussian(params.get("gaussian_state", {}))

    def _run_squeezed(self, p: dict) -> dict[str, Any]:
        import strawberryfields as sf
        from strawberryfields.ops import Sgate, MeasureFock

        r = p.get("squeezing_param", 0.5)
        phi = p.get("phase", 0.0)
        cutoff = int(p.get("cutoff_dim", 20))
        n_shots = int(p.get("n_shots", 1000))

        prog = sf.Program(1)
        with prog.context as q:
            Sgate(r, phi) | q[0]
            MeasureFock() | q[0]

        eng = sf.Engine("fock", backend_options={"cutoff_dim": cutoff})

        # Run multiple shots
        counts = {}
        for _ in range(n_shots):
            result = eng.run(prog)
            n = int(result.samples[0][0])
            counts[n] = counts.get(n, 0) + 1

        # Photon number distribution
        max_n = max(counts.keys()) if counts else 0
        photon_numbers = list(range(max_n + 1))
        probabilities = [counts.get(n, 0) / n_shots for n in photon_numbers]

        return {
            "tool": "strawberryfields",
            "simulation_type": "squeezed_state",
            "squeezing_param": r,
            "phase": phi,
            "cutoff_dim": cutoff,
            "n_shots": n_shots,
            "photon_numbers": photon_numbers,
            "probabilities": probabilities,
            "mean_photon_number": float(np.sinh(r) ** 2),
            "params": p,
        }

    def _run_hom(self, p: dict) -> dict[str, Any]:
        import strawberryfields as sf
        from strawberryfields.ops import Fock, BSgate, MeasureFock

        cutoff = int(p.get("cutoff_dim", 10))
        n_shots = int(p.get("n_shots", 1000))
        theta = p.get("beam_splitter_angle", np.pi / 4)  # 50:50 by default

        prog = sf.Program(2)
        with prog.context as q:
            Fock(1) | q[0]
            Fock(1) | q[1]
            BSgate(theta, 0) | (q[0], q[1])
            MeasureFock() | q[0]
            MeasureFock() | q[1]

        eng = sf.Engine("fock", backend_options={"cutoff_dim": cutoff})

        coincidence_counts = {"00": 0, "11": 0, "20": 0, "02": 0}
        for _ in range(n_shots):
            result = eng.run(prog)
            n0 = int(result.samples[0][0])
            n1 = int(result.samples[0][1])
            key = f"{n0}{n1}"
            coincidence_counts[key] = coincidence_counts.get(key, 0) + 1

        # Sweep beam splitter angle for HOM dip
        angles = np.linspace(0, np.pi / 2, 50).tolist()
        coincidence_probs = []
        for th in angles:
            # Analytical: P(1,1) = cos(2*th)^2 for input |1,1>
            coincidence_probs.append(float(np.cos(2 * th) ** 2))

        return {
            "tool": "strawberryfields",
            "simulation_type": "hong_ou_mandel",
            "beam_splitter_angle": theta,
            "cutoff_dim": cutoff,
            "n_shots": n_shots,
            "coincidence_counts": coincidence_counts,
            "hom_dip_angles": angles,
            "hom_dip_probabilities": coincidence_probs,
            "params": p,
        }

    def _run_boson_sampling(self, p: dict) -> dict[str, Any]:
        import strawberryfields as sf
        from strawberryfields.ops import Fock, Interferometer, MeasureFock

        n_modes = int(p.get("n_modes", 4))
        n_photons = int(p.get("n_photons", 2))
        n_shots = int(p.get("n_shots", 500))
        cutoff = int(p.get("cutoff_dim", 7))

        # Random unitary for the interferometer
        from scipy.stats import unitary_group
        U = unitary_group.rvs(n_modes)

        prog = sf.Program(n_modes)
        with prog.context as q:
            for i in range(min(n_photons, n_modes)):
                Fock(1) | q[i]
            Interferometer(U) | q

            for i in range(n_modes):
                MeasureFock() | q[i]

        eng = sf.Engine("fock", backend_options={"cutoff_dim": cutoff})

        samples = []
        output_counts = {}
        for _ in range(n_shots):
            result = eng.run(prog)
            sample = tuple(int(s) for s in result.samples[0])
            samples.append(list(sample))
            key = str(sample)
            output_counts[key] = output_counts.get(key, 0) + 1

        # Sort by frequency
        sorted_outputs = sorted(output_counts.items(), key=lambda x: -x[1])[:20]

        return {
            "tool": "strawberryfields",
            "simulation_type": "boson_sampling",
            "n_modes": n_modes,
            "n_photons": n_photons,
            "n_shots": n_shots,
            "top_outputs": [{"pattern": k, "count": v} for k, v in sorted_outputs],
            "unitary_real": np.real(U).tolist(),
            "unitary_imag": np.imag(U).tolist(),
            "params": p,
        }

    def _run_gaussian(self, p: dict) -> dict[str, Any]:
        import strawberryfields as sf
        from strawberryfields.ops import Sgate, Dgate, BSgate

        n_modes = int(p.get("n_modes", 2))
        r = p.get("squeezing_param", 0.5)
        alpha = p.get("displacement", 1.0)

        prog = sf.Program(n_modes)
        with prog.context as q:
            Sgate(r) | q[0]
            Dgate(alpha) | q[0]
            if n_modes > 1:
                BSgate(np.pi / 4, 0) | (q[0], q[1])

        eng = sf.Engine("gaussian")
        result = eng.run(prog)

        state = result.state
        means = state.means().tolist()
        cov = state.cov().tolist()

        # Wigner function for first mode (xvec grid)
        xvec = np.linspace(-5, 5, 100)
        pvec = np.linspace(-5, 5, 100)
        W = state.wigner(0, xvec, pvec)

        return {
            "tool": "strawberryfields",
            "simulation_type": "gaussian_state",
            "n_modes": n_modes,
            "squeezing_param": r,
            "displacement": alpha,
            "means": means,
            "covariance": cov,
            "wigner_x": xvec.tolist(),
            "wigner_p": pvec.tolist(),
            "wigner_W": W.tolist(),
            "params": p,
        }

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "hong_ou_mandel",
            "hong_ou_mandel": {
                "cutoff_dim": 10,
                "n_shots": 1000,
                "beam_splitter_angle": 0.7854,
            },
        }


@celery_app.task(name="tools.strawberryfields_tool.run_strawberryfields", bind=True)
def run_strawberryfields(self, params: dict, project: str = "_default",
                         label: str | None = None) -> dict:
    tool = StrawberryFieldsTool()
    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting Strawberry Fields simulation"})

    try:
        result = tool.run(params)
    except Exception as e:
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    save_result(self.request.id, "strawberryfields", result, project, label)
    return result
