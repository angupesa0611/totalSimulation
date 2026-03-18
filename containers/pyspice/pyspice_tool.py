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


def _build_circuit(params):
    """Build a PySpice circuit from component list or netlist."""
    from PySpice.Spice.Netlist import Circuit
    from PySpice.Unit import u_V, u_Ohm, u_F, u_H, u_A

    circuit = Circuit("Simulation")

    components = params.get("components", [])
    for comp in components:
        ctype = comp["type"].upper()
        name = comp["name"]
        nodes = comp["nodes"]
        value = comp["value"]

        n1, n2 = str(nodes[0]), str(nodes[1])
        # Convert '0' to circuit.gnd
        gnd = circuit.gnd

        if ctype == "V":
            circuit.V(name.replace("V", ""), n1 if n1 != "0" else gnd, n2 if n2 != "0" else gnd, value @ u_V)
        elif ctype == "I":
            circuit.I(name.replace("I", ""), n1 if n1 != "0" else gnd, n2 if n2 != "0" else gnd, value @ u_A)
        elif ctype == "R":
            circuit.R(name.replace("R", ""), n1 if n1 != "0" else gnd, n2 if n2 != "0" else gnd, value @ u_Ohm)
        elif ctype == "C":
            circuit.C(name.replace("C", ""), n1 if n1 != "0" else gnd, n2 if n2 != "0" else gnd, value @ u_F)
        elif ctype == "L":
            circuit.L(name.replace("L", ""), n1 if n1 != "0" else gnd, n2 if n2 != "0" else gnd, value @ u_H)

    return circuit


@app.task(name="tools.pyspice_tool.run_pyspice", bind=True)
def run_pyspice(self, params, project="_default", label=None):
    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting PySpice simulation"})

    sim_type = params.get("simulation_type", "dc_operating_point")

    try:
        if sim_type == "dc_operating_point":
            result = _run_dc_operating_point(params)
        elif sim_type == "ac_analysis":
            result = _run_ac_analysis(params)
        elif sim_type == "transient_analysis":
            result = _run_transient_analysis(params)
        else:
            raise ValueError(f"Unknown simulation_type: {sim_type}")
    except Exception as e:
        raise

    result["tool"] = "pyspice"
    result["simulation_type"] = sim_type

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    _save_result(self.request.id, "pyspice", result, project, label)
    return result


def _run_dc_operating_point(params):
    circuit = _build_circuit(params)
    simulator = circuit.simulator(temperature=25, nominal_temperature=25)
    analysis = simulator.operating_point()

    node_voltages = {}
    for node in analysis.nodes.values():
        node_voltages[str(node)] = float(node)

    branch_currents = {}
    for branch in analysis.branches.values():
        branch_currents[str(branch)] = float(branch)

    return {
        "node_voltages": node_voltages,
        "branch_currents": branch_currents,
    }


def _run_ac_analysis(params):
    from PySpice.Unit import u_Hz

    circuit = _build_circuit(params)
    simulator = circuit.simulator(temperature=25, nominal_temperature=25)

    f_start = params.get("f_start", 1)
    f_stop = params.get("f_stop", 1e6)
    n_points = params.get("n_points", 100)

    analysis = simulator.ac(
        start_frequency=f_start @ u_Hz,
        stop_frequency=f_stop @ u_Hz,
        number_of_points=n_points,
        variation="dec",
    )

    frequencies = np.array(analysis.frequency).tolist()

    # Get output node voltage magnitude and phase
    magnitude_dB = {}
    phase_deg = {}

    for node_name in analysis.nodes:
        node_data = np.array(analysis[node_name])
        magnitude_dB[node_name] = (20 * np.log10(np.abs(node_data))).tolist()
        phase_deg[node_name] = np.degrees(np.angle(node_data)).tolist()

    return {
        "frequencies_Hz": frequencies,
        "magnitude_dB": magnitude_dB,
        "phase_deg": phase_deg,
    }


def _run_transient_analysis(params):
    from PySpice.Unit import u_s

    circuit = _build_circuit(params)
    simulator = circuit.simulator(temperature=25, nominal_temperature=25)

    step_time = params.get("step_time", 1e-6)
    end_time = params.get("end_time", 0.005)

    analysis = simulator.transient(
        step_time=step_time @ u_s,
        end_time=end_time @ u_s,
    )

    times = np.array(analysis.time).tolist()

    voltages = {}
    for node_name in analysis.nodes:
        voltages[node_name] = np.array(analysis[node_name]).tolist()

    currents = {}
    for branch_name in analysis.branches:
        currents[branch_name] = np.array(analysis[branch_name]).tolist()

    return {
        "times_s": times,
        "voltages": voltages,
        "currents": currents,
    }
