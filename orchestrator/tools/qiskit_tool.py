"""Qiskit — quantum circuit simulation, VQE, transpilation, stabilizer codes.

Simulation types:
  - circuit_simulation: Build and run quantum circuits (QASM or statevector backend)
  - vqe: Variational Quantum Eigensolver for ground state energy
  - transpilation: Optimize circuits for a target basis gate set
  - stabilizer_codes: Syndrome measurement circuits for quantum error correction
"""

from typing import Any

import numpy as np
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result


def _export_qasm(circuit):
    """Export circuit as OpenQASM string for QuTiP coupling."""
    from qiskit.qasm2 import dumps
    return dumps(circuit)


def _build_circuit(n_qubits, gates):
    """Build a Qiskit QuantumCircuit from gate list."""
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(n_qubits, n_qubits)

    gate_map = {
        "h": "h", "x": "x", "y": "y", "z": "z",
        "s": "s", "t": "t", "sdg": "sdg", "tdg": "tdg",
        "cx": "cx", "cnot": "cx", "cz": "cz", "swap": "swap",
        "ccx": "ccx", "toffoli": "ccx",
        "rx": "rx", "ry": "ry", "rz": "rz",
    }

    for g in gates:
        name = g["name"].lower()
        qubits = g.get("qubits", g.get("wires", [0]))
        gate_params = g.get("params", [])

        if name not in gate_map:
            continue

        method_name = gate_map[name]
        method = getattr(qc, method_name)

        if gate_params:
            method(*gate_params, *qubits)
        else:
            method(*qubits)

    return qc


class QiskitTool(SimulationTool):
    name = "Qiskit"
    key = "qiskit"
    layer = "quantum-computing"

    SIMULATION_TYPES = {"circuit_simulation", "vqe", "transpilation", "stabilizer_codes"}

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type", "circuit_simulation")
        if sim_type not in self.SIMULATION_TYPES:
            raise ValueError(f"Unknown simulation_type: {sim_type}. Supported: {self.SIMULATION_TYPES}")
        params.setdefault("simulation_type", sim_type)
        params.setdefault("n_qubits", 2)
        params.setdefault("n_shots", 1024)
        params.setdefault("gates", [{"name": "h", "qubits": [0]}, {"name": "cx", "qubits": [0, 1]}])
        params.setdefault("backend", "qasm")
        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        params = self.validate_params(params)
        sim_type = params["simulation_type"]

        if sim_type == "circuit_simulation":
            result = self._run_circuit_simulation(params)
        elif sim_type == "vqe":
            result = self._run_vqe(params)
        elif sim_type == "transpilation":
            result = self._run_transpilation(params)
        elif sim_type == "stabilizer_codes":
            result = self._run_stabilizer_codes(params)

        result["tool"] = "qiskit"
        result["simulation_type"] = sim_type
        return result

    def _run_circuit_simulation(self, params):
        from qiskit import QuantumCircuit, transpile
        from qiskit_aer import AerSimulator

        n_qubits = params.get("n_qubits", 2)
        gates = params.get("gates", [{"name": "h", "qubits": [0]}, {"name": "cx", "qubits": [0, 1]}])
        n_shots = params.get("n_shots", 1024)
        backend_type = params.get("backend", "qasm")

        qc = _build_circuit(n_qubits, gates)

        if backend_type == "statevector":
            sim = AerSimulator(method="statevector")
            qc_sv = qc.copy()
            qc_sv.save_statevector()
            t_qc = transpile(qc_sv, sim)
            job = sim.run(t_qc)
            result = job.result()
            sv = result.get_statevector()
            sv_array = np.array(sv)
            probs = np.abs(sv_array) ** 2

            qc_m = qc.copy()
            qc_m.measure_all()
            sim_qasm = AerSimulator()
            t_qc_m = transpile(qc_m, sim_qasm)
            job_m = sim_qasm.run(t_qc_m, shots=n_shots)
            counts = job_m.result().get_counts()

            return {
                "counts": {str(k): int(v) for k, v in counts.items()},
                "probabilities": probs.tolist(),
                "statevector_real": sv_array.real.tolist(),
                "statevector_imag": sv_array.imag.tolist(),
                "n_qubits": n_qubits,
                "depth": qc.depth(),
                "n_gates": qc.size(),
                "qasm_str": _export_qasm(qc),
            }
        else:
            qc_m = qc.copy()
            qc_m.measure_all()
            sim = AerSimulator()
            t_qc = transpile(qc_m, sim)
            job = sim.run(t_qc, shots=n_shots)
            counts = job.result().get_counts()

            total = sum(counts.values())
            n_states = 2 ** n_qubits
            probs = [0.0] * n_states
            for bitstring, count in counts.items():
                idx = int(bitstring.replace(" ", ""), 2)
                if idx < n_states:
                    probs[idx] = count / total

            return {
                "counts": {str(k): int(v) for k, v in counts.items()},
                "probabilities": probs,
                "statevector_real": [],
                "statevector_imag": [],
                "n_qubits": n_qubits,
                "depth": qc.depth(),
                "n_gates": qc.size(),
                "qasm_str": _export_qasm(qc),
            }

    def _run_vqe(self, params):
        from qiskit import QuantumCircuit, transpile
        from qiskit_aer import AerSimulator
        from qiskit.circuit import ParameterVector
        from qiskit.quantum_info import SparsePauliOp
        from scipy.optimize import minimize

        n_qubits = params.get("n_qubits", 2)
        ham_terms = params.get("hamiltonian", [
            {"coeff": -0.5, "pauli_string": "II"},
            {"coeff": 0.5, "pauli_string": "ZZ"},
        ])
        ansatz_type = params.get("ansatz", "hardware_efficient")
        optimizer_name = params.get("optimizer", "cobyla")
        max_iterations = params.get("max_iterations", 100)

        pauli_list = [(term["pauli_string"], term["coeff"]) for term in ham_terms]
        H = SparsePauliOp.from_list(pauli_list)

        if ansatz_type == "hardware_efficient":
            n_params = n_qubits * 3
            theta = ParameterVector("θ", n_params)
            qc = QuantumCircuit(n_qubits)
            for i in range(n_qubits):
                qc.ry(theta[i * 3], i)
                qc.rz(theta[i * 3 + 1], i)
            for i in range(n_qubits - 1):
                qc.cx(i, i + 1)
            for i in range(n_qubits):
                qc.ry(theta[i * 3 + 2], i)
        else:
            n_params = n_qubits * 2
            theta = ParameterVector("θ", n_params)
            qc = QuantumCircuit(n_qubits)
            for i in range(n_qubits):
                qc.ry(theta[i * 2], i)
                qc.rz(theta[i * 2 + 1], i)
            for i in range(n_qubits - 1):
                qc.cx(i, i + 1)

        sim = AerSimulator(method="statevector")

        def cost_function(param_values):
            bound_qc = qc.assign_parameters(param_values)
            bound_qc.save_statevector()
            t_qc = transpile(bound_qc, sim)
            job = sim.run(t_qc)
            sv = job.result().get_statevector()
            energy = float(np.real(sv.expectation_value(H)))
            return energy

        x0 = np.random.uniform(-np.pi, np.pi, n_params)
        energies = []
        iterations_list = []

        def callback(xk):
            energy = cost_function(xk)
            energies.append(energy)
            iterations_list.append(len(energies))

        method = "COBYLA" if optimizer_name == "cobyla" else "Nelder-Mead"
        res = minimize(cost_function, x0, method=method, callback=callback,
                       options={"maxiter": max_iterations})

        if not energies:
            energies = [float(res.fun)]
            iterations_list = [1]

        return {
            "ground_state_energy": float(res.fun),
            "optimal_params": res.x.tolist(),
            "convergence": {
                "iterations": iterations_list,
                "energies": energies,
            },
            "n_qubits": n_qubits,
            "qasm_str": _export_qasm(qc.assign_parameters(res.x)),
        }

    def _run_transpilation(self, params):
        from qiskit import transpile

        n_qubits = params.get("n_qubits", 2)
        gates = params.get("gates", [{"name": "h", "qubits": [0]}, {"name": "cx", "qubits": [0, 1]}])
        optimization_level = params.get("optimization_level", 1)
        basis_gates = params.get("basis_gates", ["cx", "id", "rz", "sx", "x"])

        qc = _build_circuit(n_qubits, gates)
        original_depth = qc.depth()
        original_gates = qc.size()

        t_qc = transpile(qc, basis_gates=basis_gates, optimization_level=optimization_level)
        optimized_depth = t_qc.depth()
        optimized_gates = t_qc.size()

        return {
            "original_depth": original_depth,
            "optimized_depth": optimized_depth,
            "original_gates": original_gates,
            "optimized_gates": optimized_gates,
            "qasm_str": _export_qasm(t_qc),
        }

    def _run_stabilizer_codes(self, params):
        from qiskit import QuantumCircuit, transpile
        from qiskit_aer import AerSimulator

        generators = params.get("generators", ["XXXX", "ZZZZ"])
        n_shots = params.get("n_shots", 1024)

        if not generators:
            raise ValueError("stabilizer_codes requires 'generators' param (list of Pauli strings)")

        n_data = len(generators[0])
        n_ancilla = len(generators)
        n_total = n_data + n_ancilla

        qc = QuantumCircuit(n_total, n_ancilla)

        for g_idx, gen_str in enumerate(generators):
            ancilla_qubit = n_data + g_idx
            qc.h(ancilla_qubit)

            for q_idx, pauli in enumerate(gen_str):
                if pauli == "I":
                    continue
                elif pauli == "X":
                    qc.cx(ancilla_qubit, q_idx)
                elif pauli == "Y":
                    qc.sdg(q_idx)
                    qc.cx(ancilla_qubit, q_idx)
                    qc.s(q_idx)
                elif pauli == "Z":
                    qc.cz(ancilla_qubit, q_idx)

            qc.h(ancilla_qubit)
            qc.measure(ancilla_qubit, g_idx)

        sim = AerSimulator()
        t_qc = transpile(qc, sim)
        job = sim.run(t_qc, shots=n_shots)
        counts = job.result().get_counts()

        syndrome_results = {}
        for bitstring, count in counts.items():
            clean = bitstring.replace(" ", "")
            syndrome_results[clean] = int(count)

        no_error_key = "0" * n_ancilla
        no_error_count = syndrome_results.get(no_error_key, 0)
        no_error_rate = no_error_count / n_shots if n_shots > 0 else 0

        return {
            "generators": generators,
            "syndrome_results": syndrome_results,
            "n_qubits": n_total,
            "n_data_qubits": n_data,
            "n_ancilla_qubits": n_ancilla,
            "circuit_depth": qc.depth(),
            "no_error_rate": no_error_rate,
            "n_shots": n_shots,
            "qasm_str": _export_qasm(qc),
        }

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "circuit_simulation",
            "n_qubits": 2,
            "gates": [{"name": "h", "qubits": [0]}, {"name": "cx", "qubits": [0, 1]}],
            "n_shots": 1024,
            "backend": "qasm",
        }


@celery_app.task(name="tools.qiskit_tool.run_qiskit", bind=True)
def run_qiskit(self, params: dict, project: str = "_default",
               label: str | None = None) -> dict:
    tool = QiskitTool()

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting Qiskit simulation"})

    try:
        sim_type = params.get("simulation_type", "circuit_simulation")
        self.update_state(state="PROGRESS", meta={"progress": 0.1, "message": f"Running {sim_type}"})
        result = tool.run(params)
    except Exception as e:
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    save_result(self.request.id, "qiskit", result, project, label)

    return result
