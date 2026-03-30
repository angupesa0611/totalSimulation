from typing import Any
import numpy as np
import qutip
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result


class QuTiPTool(SimulationTool):
    name = "QuTiP"
    key = "qutip"
    layer = "quantum"

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        if "system_type" not in params:
            raise ValueError("system_type is required")
        valid_types = ["qubit_rabi", "spin_chain", "jaynes_cummings"]
        if params["system_type"] not in valid_types:
            raise ValueError(f"system_type must be one of {valid_types}")
        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        params = self.validate_params(params)
        system_type = params["system_type"]

        if system_type == "qubit_rabi":
            return self._run_rabi(params.get("qubit_rabi", {}))
        elif system_type == "spin_chain":
            return self._run_spin_chain(params.get("spin_chain", {}))
        elif system_type == "jaynes_cummings":
            return self._run_jaynes_cummings(params.get("jaynes_cummings", {}))

    def _run_rabi(self, p: dict) -> dict[str, Any]:
        omega = p.get("omega", 1.0)
        delta = p.get("delta", 0.0)
        psi0_type = p.get("psi0", "ground")
        tmax = p.get("tmax", 25.0)
        n_steps = p.get("n_steps", 500)

        # Hamiltonian: H = delta/2 * sigma_z + omega/2 * sigma_x
        H = delta / 2 * qutip.sigmaz() + omega / 2 * qutip.sigmax()

        # Initial state
        if psi0_type == "excited":
            psi0 = qutip.basis(2, 0)
        elif psi0_type == "superposition":
            psi0 = (qutip.basis(2, 0) + qutip.basis(2, 1)).unit()
        else:  # ground
            psi0 = qutip.basis(2, 1)

        tlist = np.linspace(0, tmax, n_steps)
        e_ops = [qutip.sigmaz(), qutip.sigmax(), qutip.sigmay()]
        result = qutip.sesolve(H, psi0, tlist, e_ops=e_ops)

        # Bloch sphere coordinates
        bx = np.array(result.expect[1])
        by = np.array(result.expect[2])
        bz = np.array(result.expect[0])

        return {
            "tool": "qutip",
            "system_type": "qubit_rabi",
            "times": tlist.tolist(),
            "expect": {
                "sigma_z": result.expect[0].tolist(),
                "sigma_x": result.expect[1].tolist(),
                "sigma_y": result.expect[2].tolist(),
            },
            "bloch": {
                "x": bx.tolist(),
                "y": by.tolist(),
                "z": bz.tolist(),
            },
            "params": {"omega": omega, "delta": delta, "psi0": psi0_type},
        }

    def _run_spin_chain(self, p: dict) -> dict[str, Any]:
        n_spins = p.get("n_spins", 4)
        J = p.get("J", 1.0)
        B = p.get("B", 0.5)
        tmax = p.get("tmax", 20.0)
        n_steps = p.get("n_steps", 500)

        # Build Heisenberg chain Hamiltonian
        si = qutip.qeye(2)
        sx = qutip.sigmax()
        sy = qutip.sigmay()
        sz = qutip.sigmaz()

        def _op_at(op, j, n):
            ops = [si] * n
            ops[j] = op
            return qutip.tensor(ops)

        H = 0
        for i in range(n_spins - 1):
            H += J * (_op_at(sx, i, n_spins) * _op_at(sx, i + 1, n_spins) +
                      _op_at(sy, i, n_spins) * _op_at(sy, i + 1, n_spins) +
                      _op_at(sz, i, n_spins) * _op_at(sz, i + 1, n_spins))
        for i in range(n_spins):
            H += B * _op_at(sz, i, n_spins)

        # Initial state: configurable via comma-separated 0/1 string or default
        init_str = p.get("initial_state", "")
        if init_str and isinstance(init_str, str):
            bits = [int(b.strip()) for b in init_str.split(",") if b.strip() in ("0", "1")]
            if len(bits) == n_spins:
                psi0_list = [qutip.basis(2, b) for b in bits]
            else:
                psi0_list = [qutip.basis(2, 0)] + [qutip.basis(2, 1)] * (n_spins - 1)
        else:
            psi0_list = [qutip.basis(2, 0)] + [qutip.basis(2, 1)] * (n_spins - 1)
        psi0 = qutip.tensor(psi0_list)

        tlist = np.linspace(0, tmax, n_steps)
        e_ops = [_op_at(sz, i, n_spins) for i in range(n_spins)]
        result = qutip.sesolve(H, psi0, tlist, e_ops=e_ops)

        return {
            "tool": "qutip",
            "system_type": "spin_chain",
            "times": tlist.tolist(),
            "expect": {
                f"sz_{i}": result.expect[i].tolist() for i in range(n_spins)
            },
            "params": {"n_spins": n_spins, "J": J, "B": B},
        }

    def _run_jaynes_cummings(self, p: dict) -> dict[str, Any]:
        n_photons = p.get("n_photons", 5)
        omega_a = p.get("omega_a", 1.0)
        omega_c = p.get("omega_c", 1.0)
        g = p.get("g", 0.1)
        kappa = p.get("kappa", 0.05)
        gamma = p.get("gamma", 0.01)
        tmax = p.get("tmax", 50.0)
        n_steps = p.get("n_steps", 500)

        # Operators
        a = qutip.tensor(qutip.destroy(n_photons), qutip.qeye(2))
        sm = qutip.tensor(qutip.qeye(n_photons), qutip.destroy(2))

        H = omega_c * a.dag() * a + omega_a / 2 * qutip.tensor(
            qutip.qeye(n_photons), qutip.sigmaz()
        ) + g * (a.dag() * sm + a * sm.dag())

        c_ops = []
        if kappa > 0:
            c_ops.append(np.sqrt(kappa) * a)
        if gamma > 0:
            c_ops.append(np.sqrt(gamma) * sm)

        # Initial: atom excited, cavity vacuum
        psi0 = qutip.tensor(qutip.basis(n_photons, 0), qutip.basis(2, 0))

        tlist = np.linspace(0, tmax, n_steps)
        n_op = a.dag() * a
        sz_op = qutip.tensor(qutip.qeye(n_photons), qutip.sigmaz())
        e_ops = [n_op, sz_op]

        result = qutip.mesolve(H, psi0, tlist, c_ops=c_ops, e_ops=e_ops)

        return {
            "tool": "qutip",
            "system_type": "jaynes_cummings",
            "times": tlist.tolist(),
            "expect": {
                "photon_number": result.expect[0].tolist(),
                "sigma_z": result.expect[1].tolist(),
            },
            "params": {
                "n_photons": n_photons, "omega_a": omega_a,
                "omega_c": omega_c, "g": g, "kappa": kappa, "gamma": gamma,
            },
        }

    def get_default_params(self) -> dict[str, Any]:
        return {
            "system_type": "qubit_rabi",
            "qubit_rabi": {
                "omega": 1.0, "delta": 0.0, "psi0": "ground",
                "tmax": 25.0, "n_steps": 500,
            },
        }


@celery_app.task(name="tools.qutip_tool.run_qutip", bind=True)
def run_qutip(self, params: dict, project: str = "_default",
              label: str | None = None) -> dict:
    tool = QuTiPTool()

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting QuTiP simulation"})

    try:
        result = tool.run(params)
    except Exception as e:
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})

    save_result(self.request.id, "qutip", result, project, label)

    return result
