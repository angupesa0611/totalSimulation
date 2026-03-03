import json
import os
from datetime import datetime, timezone
import numpy as np
from worker import app


def _save_result(job_id, tool, data, project="_default", label=None):
    results_dir = os.getenv("RESULTS_DIR", "/data/results")
    project_dir = os.path.join(results_dir, project)
    os.makedirs(project_dir, exist_ok=True)
    run_dir = os.path.join(project_dir, job_id)
    os.makedirs(run_dir, exist_ok=True)

    metadata = {
        "job_id": job_id, "tool": tool, "project": project,
        "label": label, "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with open(os.path.join(run_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
    with open(os.path.join(run_dir, "result.json"), "w") as f:
        json.dump(data, f)

    index_path = os.path.join(project_dir, "_index.json")
    index = []
    if os.path.exists(index_path):
        with open(index_path) as f:
            index = json.load(f)
    index.append(metadata)
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)
    return run_dir


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


@app.task(name="tools.qiskit_tool.run_qiskit", bind=True)
def run_qiskit(self, params, project="_default", label=None):
    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting Qiskit simulation"})

    sim_type = params.get("simulation_type", "circuit_simulation")

    try:
        if sim_type == "circuit_simulation":
            result = _run_circuit_simulation(params)
        elif sim_type == "vqe":
            result = _run_vqe(params)
        elif sim_type == "transpilation":
            result = _run_transpilation(params)
        elif sim_type == "stabilizer_codes":
            result = _run_stabilizer_codes(params)
        else:
            raise ValueError(f"Unknown simulation_type: {sim_type}")
    except Exception as e:
        self.update_state(state="FAILURE", meta={"message": str(e)})
        raise

    result["tool"] = "qiskit"
    result["simulation_type"] = sim_type

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    _save_result(self.request.id, "qiskit", result, project, label)
    return result


def _run_circuit_simulation(params):
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

        # Also run with measurements for counts
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
        # QASM simulation with measurements
        qc_m = qc.copy()
        qc_m.measure_all()
        sim = AerSimulator()
        t_qc = transpile(qc_m, sim)
        job = sim.run(t_qc, shots=n_shots)
        counts = job.result().get_counts()

        # Compute probabilities from counts
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


def _run_vqe(params):
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator
    from qiskit.circuit import ParameterVector

    n_qubits = params.get("n_qubits", 2)
    ham_terms = params.get("hamiltonian", [
        {"coeff": -0.5, "pauli_string": "II"},
        {"coeff": 0.5, "pauli_string": "ZZ"},
    ])
    ansatz_type = params.get("ansatz", "hardware_efficient")
    optimizer_name = params.get("optimizer", "cobyla")
    max_iterations = params.get("max_iterations", 100)

    from qiskit.quantum_info import SparsePauliOp

    # Build Hamiltonian
    pauli_list = [(term["pauli_string"], term["coeff"]) for term in ham_terms]
    H = SparsePauliOp.from_list(pauli_list)

    # Build parameterized ansatz
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

    # Simple optimization loop
    from scipy.optimize import minimize

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


def _run_transpilation(params):
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


def _run_stabilizer_codes(params):
    """Build and simulate syndrome measurement circuits from stabilizer generators."""
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator

    generators = params.get("generators", ["XXXX", "ZZZZ"])
    n_shots = params.get("n_shots", 1024)

    if not generators:
        raise ValueError("stabilizer_codes requires 'generators' param (list of Pauli strings)")

    n_data = len(generators[0])
    n_ancilla = len(generators)
    n_total = n_data + n_ancilla

    # Build syndrome measurement circuit
    qc = QuantumCircuit(n_total, n_ancilla)

    pauli_gate_map = {"X": "cx", "Y": "cy", "Z": "cz"}

    for g_idx, gen_str in enumerate(generators):
        ancilla_qubit = n_data + g_idx

        # Prepare ancilla in |+> for X/Y measurements
        qc.h(ancilla_qubit)

        # Apply controlled Pauli gates
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

        # Measure ancilla
        qc.h(ancilla_qubit)
        qc.measure(ancilla_qubit, g_idx)

    # Simulate
    sim = AerSimulator()
    t_qc = transpile(qc, sim)
    job = sim.run(t_qc, shots=n_shots)
    counts = job.result().get_counts()

    # Analyze syndromes
    syndrome_results = {}
    for bitstring, count in counts.items():
        clean = bitstring.replace(" ", "")
        syndrome_results[clean] = int(count)

    # Count no-error syndromes (all zeros)
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
