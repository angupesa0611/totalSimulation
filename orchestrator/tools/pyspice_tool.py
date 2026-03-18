"""PySpice — SPICE circuit simulation via ngspice backend.

Simulation types:
  - dc_operating_point: DC operating point analysis (node voltages, branch currents)
  - ac_analysis: AC frequency sweep (Bode plot data)
  - transient_analysis: Time-domain transient simulation
"""

from typing import Any

import numpy as np
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result


def _build_circuit(params):
    """Build a PySpice circuit from component list."""
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


class PySpiceTool(SimulationTool):
    name = "PySpice"
    key = "pyspice"
    layer = "circuits"

    SIMULATION_TYPES = {"dc_operating_point", "ac_analysis", "transient_analysis"}

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type", "dc_operating_point")
        if sim_type not in self.SIMULATION_TYPES:
            raise ValueError(f"Unknown simulation_type: {sim_type}. Supported: {self.SIMULATION_TYPES}")
        if not params.get("components"):
            raise ValueError("components list is required")
        params.setdefault("simulation_type", sim_type)
        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        params = self.validate_params(params)
        sim_type = params["simulation_type"]

        if sim_type == "dc_operating_point":
            result = self._run_dc_operating_point(params)
        elif sim_type == "ac_analysis":
            result = self._run_ac_analysis(params)
        elif sim_type == "transient_analysis":
            result = self._run_transient_analysis(params)

        result["tool"] = "pyspice"
        result["simulation_type"] = sim_type
        return result

    def _run_dc_operating_point(self, params):
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

    def _run_ac_analysis(self, params):
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

    def _run_transient_analysis(self, params):
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

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "dc_operating_point",
            "components": [
                {"type": "V", "name": "V1", "nodes": ["1", "0"], "value": 5},
                {"type": "R", "name": "R1", "nodes": ["1", "2"], "value": 1000},
                {"type": "R", "name": "R2", "nodes": ["2", "0"], "value": 2000},
            ],
        }


@celery_app.task(name="tools.pyspice_tool.run_pyspice", bind=True)
def run_pyspice(self, params: dict, project: str = "_default",
                label: str | None = None) -> dict:
    tool = PySpiceTool()

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting PySpice simulation"})

    try:
        sim_type = params.get("simulation_type", "dc_operating_point")
        self.update_state(state="PROGRESS", meta={"progress": 0.1, "message": f"Running {sim_type}"})
        result = tool.run(params)
    except Exception as e:
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    save_result(self.request.id, "pyspice", result, project, label)

    return result
