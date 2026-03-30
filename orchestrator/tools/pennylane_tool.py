from typing import Any
import numpy as np
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result


class PennyLaneTool(SimulationTool):
    name = "PennyLane"
    key = "pennylane"
    layer = "circuits"

    SIMULATION_TYPES = {"vqe", "circuit_simulation", "parameter_optimization"}

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type", "circuit_simulation")
        if sim_type not in self.SIMULATION_TYPES:
            raise ValueError(f"Unknown simulation_type: {sim_type}. Supported: {self.SIMULATION_TYPES}")

        params.setdefault("simulation_type", sim_type)
        params.setdefault("n_qubits", 2)
        params.setdefault("max_iterations", 100)
        params.setdefault("step_size", 0.4)
        params.setdefault("n_shots", 1000)
        params.setdefault("ansatz", "basic")
        params.setdefault("optimizer", "gradient_descent")
        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        params = self.validate_params(params)
        sim_type = params["simulation_type"]

        if sim_type == "vqe":
            return self._run_vqe(params)
        elif sim_type == "circuit_simulation":
            return self._run_circuit_simulation(params)
        elif sim_type == "parameter_optimization":
            return self._run_parameter_optimization(params)

    def _build_hamiltonian(self, ham_terms):
        """Build PennyLane Hamiltonian from list of {coeff, pauli_string} dicts."""
        import pennylane as qml

        coeffs = []
        obs = []

        pauli_map = {"I": qml.Identity, "X": qml.PauliX, "Y": qml.PauliY, "Z": qml.PauliZ}

        for term in ham_terms:
            coeff = term["coeff"]
            pauli_str = term["pauli_string"]

            # Build tensor product of Pauli operators
            operators = []
            for i, p in enumerate(pauli_str):
                if p in pauli_map:
                    operators.append(pauli_map[p](i))

            if operators:
                obs_term = operators[0]
                for op in operators[1:]:
                    obs_term = obs_term @ op
                coeffs.append(coeff)
                obs.append(obs_term)

        return qml.dot(coeffs, obs)

    def _run_vqe(self, params):
        import pennylane as qml

        n_qubits = params["n_qubits"]
        max_iterations = params["max_iterations"]
        step_size = params["step_size"]
        ansatz_type = params.get("ansatz", "basic")

        ham_terms = params.get("hamiltonian", [
            {"coeff": -0.5, "pauli_string": "II"},
            {"coeff": 0.5, "pauli_string": "ZZ"},
        ])

        H = self._build_hamiltonian(ham_terms)
        dev = qml.device("default.qubit", wires=n_qubits)

        n_params = n_qubits * 3 if ansatz_type == "hardware_efficient" else n_qubits * 2

        @qml.qnode(dev)
        def circuit(theta):
            if ansatz_type == "hardware_efficient":
                for i in range(n_qubits):
                    qml.RY(theta[i * 3], wires=i)
                    qml.RZ(theta[i * 3 + 1], wires=i)
                for i in range(n_qubits - 1):
                    qml.CNOT(wires=[i, i + 1])
                for i in range(n_qubits):
                    qml.RY(theta[i * 3 + 2], wires=i)
            else:
                for i in range(n_qubits):
                    qml.RY(theta[i * 2], wires=i)
                    qml.RZ(theta[i * 2 + 1], wires=i)
                for i in range(n_qubits - 1):
                    qml.CNOT(wires=[i, i + 1])
            return qml.expval(H)

        # Choose optimizer
        if params.get("optimizer") == "adam":
            opt = qml.AdamOptimizer(stepsize=step_size)
        else:
            opt = qml.GradientDescentOptimizer(stepsize=step_size)

        theta = np.random.uniform(-np.pi, np.pi, n_params)

        energies = []
        iterations = []

        for i in range(max_iterations):
            theta, energy = opt.step_and_cost(circuit, theta)
            energies.append(float(energy))
            iterations.append(i)

        return {
            "tool": "pennylane",
            "simulation_type": "vqe",
            "ground_state_energy": float(energies[-1]),
            "optimal_params": theta.tolist(),
            "convergence": {
                "iterations": iterations,
                "energies": energies,
            },
            "n_qubits": n_qubits,
            "gate_sequence": self._params_to_gates(theta, n_qubits, ansatz_type),
        }

    def _params_to_gates(self, theta, n_qubits, ansatz_type):
        """Convert VQE parameters to gate sequence for Qiskit coupling."""
        gates = []
        if ansatz_type == "hardware_efficient":
            for i in range(n_qubits):
                gates.append({"name": "ry", "wires": [i], "params": [float(theta[i * 3])]})
                gates.append({"name": "rz", "wires": [i], "params": [float(theta[i * 3 + 1])]})
            for i in range(n_qubits - 1):
                gates.append({"name": "cx", "wires": [i, i + 1], "params": []})
            for i in range(n_qubits):
                gates.append({"name": "ry", "wires": [i], "params": [float(theta[i * 3 + 2])]})
        else:
            for i in range(n_qubits):
                gates.append({"name": "ry", "wires": [i], "params": [float(theta[i * 2])]})
                gates.append({"name": "rz", "wires": [i], "params": [float(theta[i * 2 + 1])]})
            for i in range(n_qubits - 1):
                gates.append({"name": "cx", "wires": [i, i + 1], "params": []})
        return gates

    def _run_circuit_simulation(self, params):
        import pennylane as qml

        n_qubits = params["n_qubits"]
        gates = params.get("gates", [{"name": "h", "wires": [0]}, {"name": "cx", "wires": [0, 1]}])
        n_shots = params.get("n_shots", 1000)

        dev_exact = qml.device("default.qubit", wires=n_qubits)
        dev_shots = qml.device("default.qubit", wires=n_qubits, shots=n_shots)

        gate_map = {
            "h": qml.Hadamard, "x": qml.PauliX, "y": qml.PauliY, "z": qml.PauliZ,
            "cx": qml.CNOT, "cnot": qml.CNOT, "cz": qml.CZ, "swap": qml.SWAP,
            "rx": qml.RX, "ry": qml.RY, "rz": qml.RZ,
            "s": qml.S, "t": qml.T, "toffoli": qml.Toffoli,
        }

        def apply_gates():
            for g in gates:
                gate_name = g["name"].lower()
                wires = g.get("wires", [0])
                gate_params = g.get("params", [])
                if gate_name in gate_map:
                    gate_cls = gate_map[gate_name]
                    if gate_params:
                        gate_cls(*gate_params, wires=wires)
                    else:
                        gate_cls(wires=wires)

        @qml.qnode(dev_exact)
        def exact_circuit():
            apply_gates()
            return qml.state()

        @qml.qnode(dev_shots)
        def sample_circuit():
            apply_gates()
            return qml.counts()

        # Get exact statevector
        state = exact_circuit()
        probs = np.abs(state) ** 2

        # Get measurement counts
        counts = sample_circuit()
        # Ensure counts are proper format
        counts_dict = {}
        for k, v in counts.items():
            if isinstance(k, int):
                counts_dict[format(k, f'0{n_qubits}b')] = int(v)
            else:
                counts_dict[str(k)] = int(v)

        return {
            "tool": "pennylane",
            "simulation_type": "circuit_simulation",
            "statevector_real": state.real.tolist(),
            "statevector_imag": state.imag.tolist(),
            "probabilities": probs.tolist(),
            "measurement_counts": counts_dict,
            "n_qubits": n_qubits,
            "gate_sequence": gates,
        }

    def _run_parameter_optimization(self, params):
        import pennylane as qml

        n_qubits = params["n_qubits"]
        target_state = params.get("target_state")
        ansatz_type = params.get("ansatz", "basic")
        max_iterations = params.get("max_iterations", 100)

        dev = qml.device("default.qubit", wires=n_qubits)

        if target_state is None:
            # Default: try to prepare |+...+> state
            target = np.ones(2 ** n_qubits) / np.sqrt(2 ** n_qubits)
        else:
            target = np.array(target_state, dtype=complex)
            target = target / np.linalg.norm(target)

        n_params = n_qubits * 3 if ansatz_type == "hardware_efficient" else n_qubits * 2

        @qml.qnode(dev)
        def circuit(theta):
            if ansatz_type == "hardware_efficient":
                for i in range(n_qubits):
                    qml.RY(theta[i * 3], wires=i)
                    qml.RZ(theta[i * 3 + 1], wires=i)
                for i in range(n_qubits - 1):
                    qml.CNOT(wires=[i, i + 1])
                for i in range(n_qubits):
                    qml.RY(theta[i * 3 + 2], wires=i)
            else:
                for i in range(n_qubits):
                    qml.RY(theta[i * 2], wires=i)
                    qml.RZ(theta[i * 2 + 1], wires=i)
                for i in range(n_qubits - 1):
                    qml.CNOT(wires=[i, i + 1])
            return qml.state()

        def cost_fn(theta):
            state = circuit(theta)
            fidelity = float(np.abs(np.vdot(target, state)) ** 2)
            return 1.0 - fidelity

        opt = qml.GradientDescentOptimizer(stepsize=0.4)
        theta = np.random.uniform(-np.pi, np.pi, n_params)

        costs = []
        iterations = []

        for i in range(max_iterations):
            theta = opt.step(cost_fn, theta)
            cost = cost_fn(theta)
            costs.append(float(cost))
            iterations.append(i)

        final_fidelity = 1.0 - costs[-1]

        return {
            "tool": "pennylane",
            "simulation_type": "parameter_optimization",
            "optimal_params": theta.tolist(),
            "fidelity": float(final_fidelity),
            "convergence": {
                "iterations": iterations,
                "costs": costs,
            },
            "n_qubits": n_qubits,
        }

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "circuit_simulation",
            "n_qubits": 2,
            "gates": [
                {"name": "h", "wires": [0]},
                {"name": "cx", "wires": [0, 1]},
            ],
            "n_shots": 1000,
        }


@celery_app.task(name="tools.pennylane_tool.run_pennylane", bind=True)
def run_pennylane(self, params: dict, project: str = "_default",
                  label: str | None = None) -> dict:
    tool = PennyLaneTool()

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting PennyLane computation"})

    try:
        sim_type = params.get("simulation_type", "circuit_simulation")
        self.update_state(state="PROGRESS", meta={"progress": 0.1, "message": f"Running {sim_type}"})
        result = tool.run(params)
    except Exception as e:
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    save_result(self.request.id, "pennylane", result, project, label)

    return result
