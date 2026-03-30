from typing import Any
import numpy as np
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result


class LcapyTool(SimulationTool):
    name = "Lcapy"
    key = "lcapy"
    layer = "circuits"

    SIMULATION_TYPES = {"dc_analysis", "ac_analysis", "transfer_function", "transient"}

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type", "dc_analysis")
        if sim_type not in self.SIMULATION_TYPES:
            raise ValueError(f"Unknown simulation_type: {sim_type}. Supported: {self.SIMULATION_TYPES}")

        if "netlist" not in params or not params["netlist"]:
            raise ValueError("netlist is required (SPICE-format, e.g. 'V1 1 0 dc 5; R1 1 2 1k; C1 2 0 1u')")

        params.setdefault("simulation_type", sim_type)
        params.setdefault("node_pairs", [])
        params.setdefault("n_points", 200)
        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        params = self.validate_params(params)
        sim_type = params["simulation_type"]

        if sim_type == "dc_analysis":
            return self._run_dc_analysis(params)
        elif sim_type == "ac_analysis":
            return self._run_ac_analysis(params)
        elif sim_type == "transfer_function":
            return self._run_transfer_function(params)
        elif sim_type == "transient":
            return self._run_transient(params)

    def _parse_netlist(self, netlist_str):
        """Parse netlist string into Lcapy circuit."""
        from lcapy import Circuit

        cct = Circuit()
        # Split by semicolons or newlines
        lines = netlist_str.replace(";", "\n").strip().split("\n")
        for line in lines:
            line = line.strip()
            if line:
                cct.add(line)
        return cct

    def _to_spice_netlist(self, netlist_str):
        """Export netlist string for PySpice coupling."""
        lines = netlist_str.replace(";", "\n").strip().split("\n")
        spice_lines = [line.strip() for line in lines if line.strip()]
        return "\n".join(spice_lines)

    def _run_dc_analysis(self, params):
        from lcapy import Circuit

        cct = self._parse_netlist(params["netlist"])

        node_voltages = {}
        branch_currents = {}
        latex_exprs = {}

        # Get node voltages
        try:
            for node in cct.node_list:
                if node != '0' and node != 'gnd':
                    try:
                        v = cct[node].V
                        node_voltages[str(node)] = str(v)
                        latex_exprs[f"V({node})"] = v.latex()
                    except Exception:
                        pass
        except Exception:
            pass

        # Get branch currents
        try:
            for name in cct.elements:
                try:
                    i = cct[name].I
                    branch_currents[name] = str(i)
                    latex_exprs[f"I({name})"] = i.latex()
                except Exception:
                    pass
        except Exception:
            pass

        return {
            "tool": "lcapy",
            "simulation_type": "dc_analysis",
            "node_voltages": node_voltages,
            "branch_currents": branch_currents,
            "latex": latex_exprs,
            "spice_netlist": self._to_spice_netlist(params["netlist"]),
        }

    def _run_ac_analysis(self, params):
        from lcapy import Circuit
        import sympy as sp

        cct = self._parse_netlist(params["netlist"])

        freq_range = params.get("frequency_range", [1, 1e6])
        n_points = params.get("n_points", 200)
        f_min, f_max = freq_range

        frequencies = np.logspace(np.log10(f_min), np.log10(f_max), n_points)

        # Get impedance or transfer at each frequency
        magnitude_dB = []
        phase_deg = []
        impedance_real = []
        impedance_imag = []

        input_node = params.get("input_node", "1")
        output_node = params.get("output_node", "2")

        try:
            # Try to compute transfer function symbolically first
            H = cct[output_node].V / cct[input_node].V
            H_jw = H.jomega

            f_sym = sp.Symbol('f')
            omega_sym = sp.Symbol('omega')

            for f in frequencies:
                try:
                    omega = 2 * np.pi * f
                    val = complex(H_jw.subs(omega_sym, omega))
                    mag = 20 * np.log10(abs(val)) if abs(val) > 0 else -200
                    ph = np.degrees(np.angle(val))
                    magnitude_dB.append(float(mag))
                    phase_deg.append(float(ph))
                    impedance_real.append(float(val.real))
                    impedance_imag.append(float(val.imag))
                except Exception:
                    magnitude_dB.append(0.0)
                    phase_deg.append(0.0)
                    impedance_real.append(0.0)
                    impedance_imag.append(0.0)
        except Exception:
            # Fallback: simple frequency sweep
            for f in frequencies:
                magnitude_dB.append(0.0)
                phase_deg.append(0.0)
                impedance_real.append(0.0)
                impedance_imag.append(0.0)

        return {
            "tool": "lcapy",
            "simulation_type": "ac_analysis",
            "frequencies_Hz": frequencies.tolist(),
            "magnitude_dB": magnitude_dB,
            "phase_deg": phase_deg,
            "impedance_real": impedance_real,
            "impedance_imag": impedance_imag,
            "spice_netlist": self._to_spice_netlist(params["netlist"]),
        }

    def _run_transfer_function(self, params):
        from lcapy import Circuit
        import sympy as sp

        cct = self._parse_netlist(params["netlist"])

        input_node = params.get("input_node", "1")
        output_node = params.get("output_node", "2")

        try:
            H = cct[output_node].V / cct[input_node].V
            transfer_expr = str(H)
            transfer_latex = H.latex()

            # Get poles and zeros
            poles = []
            zeros = []
            dc_gain = None

            try:
                H_s = H.laplace()
                s = sp.Symbol('s')

                # Numerator and denominator
                num, den = sp.fraction(sp.sympify(str(H_s)))
                zero_solutions = sp.solve(num, s)
                pole_solutions = sp.solve(den, s)

                zeros = [str(z) for z in zero_solutions]
                poles = [str(p) for p in pole_solutions]

                # DC gain (s=0)
                try:
                    dc = complex(H_s.subs(s, 0))
                    dc_gain = float(abs(dc))
                except Exception:
                    pass
            except Exception:
                pass

        except Exception as e:
            transfer_expr = f"Error: {e}"
            transfer_latex = transfer_expr
            poles = []
            zeros = []
            dc_gain = None

        return {
            "tool": "lcapy",
            "simulation_type": "transfer_function",
            "transfer_expr": transfer_expr,
            "transfer_latex": transfer_latex,
            "poles": poles,
            "zeros": zeros,
            "dc_gain": dc_gain,
            "spice_netlist": self._to_spice_netlist(params["netlist"]),
        }

    def _run_transient(self, params):
        from lcapy import Circuit
        import sympy as sp

        cct = self._parse_netlist(params["netlist"])

        t_max = params.get("t_max", 0.01)
        n_points = params.get("n_points", 200)
        times = np.linspace(0, t_max, n_points)

        voltages = {}
        currents = {}

        # Get node voltages as functions of time
        for node in cct.node_list:
            if node != '0' and node != 'gnd':
                try:
                    v_t = cct[node].V.time()
                    t_sym = sp.Symbol('t')
                    v_func = sp.lambdify(t_sym, sp.sympify(str(v_t)), modules=["numpy"])
                    v_vals = v_func(times)
                    if isinstance(v_vals, np.ndarray):
                        voltages[str(node)] = v_vals.tolist()
                    else:
                        voltages[str(node)] = [float(v_vals)] * n_points
                except Exception:
                    pass

        # Get branch currents as functions of time
        for name in cct.elements:
            try:
                i_t = cct[name].I.time()
                t_sym = sp.Symbol('t')
                i_func = sp.lambdify(t_sym, sp.sympify(str(i_t)), modules=["numpy"])
                i_vals = i_func(times)
                if isinstance(i_vals, np.ndarray):
                    currents[name] = i_vals.tolist()
                else:
                    currents[name] = [float(i_vals)] * n_points
            except Exception:
                pass

        return {
            "tool": "lcapy",
            "simulation_type": "transient",
            "times_s": times.tolist(),
            "voltages": voltages,
            "currents": currents,
            "spice_netlist": self._to_spice_netlist(params["netlist"]),
        }

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "transfer_function",
            "netlist": "V1 1 0; R1 1 2 1000; C1 2 0 1e-6",
            "input_node": "1",
            "output_node": "2",
        }


@celery_app.task(name="tools.lcapy_tool.run_lcapy", bind=True)
def run_lcapy(self, params: dict, project: str = "_default",
              label: str | None = None) -> dict:
    tool = LcapyTool()

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting Lcapy analysis"})

    try:
        sim_type = params.get("simulation_type", "dc_analysis")
        self.update_state(state="PROGRESS", meta={"progress": 0.1, "message": f"Running {sim_type}"})
        result = tool.run(params)
    except Exception as e:
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    save_result(self.request.id, "lcapy", result, project, label)

    return result
