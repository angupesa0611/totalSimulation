from typing import Any
import numpy as np
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result


class ControlTool(SimulationTool):
    name = "python-control"
    key = "control"
    layer = "engineering"

    SIMULATION_TYPES = {"transfer_function", "state_space", "bode_plot", "nyquist_plot", "root_locus", "step_response"}

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type", "transfer_function")
        if sim_type not in self.SIMULATION_TYPES:
            raise ValueError(f"Unknown simulation_type: {sim_type}. Supported: {self.SIMULATION_TYPES}")

        params.setdefault("simulation_type", sim_type)
        params.setdefault("numerator", [1])
        params.setdefault("denominator", [1, 1])
        params.setdefault("t_final", 10.0)

        # Normalize split omega fields from frontend
        if "omega_min" in params or "omega_max" in params:
            params["omega_range"] = [
                params.pop("omega_min", 0.01),
                params.pop("omega_max", 1000),
            ]
        params.setdefault("omega_range", [0.01, 1000])

        # Normalize split k_range fields from frontend
        if "k_min" in params or "k_max" in params:
            params["k_range"] = [
                params.pop("k_min", 0),
                params.pop("k_max", 100),
            ]

        # Normalize state-space matrix names from frontend
        for m in ("A", "B", "C", "D"):
            if f"{m}_matrix" in params:
                params[m] = params.pop(f"{m}_matrix")

        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        params = self.validate_params(params)
        sim_type = params["simulation_type"]

        if sim_type == "transfer_function":
            return self._run_transfer_function(params)
        elif sim_type == "state_space":
            return self._run_state_space(params)
        elif sim_type == "bode_plot":
            return self._run_bode_plot(params)
        elif sim_type == "nyquist_plot":
            return self._run_nyquist_plot(params)
        elif sim_type == "root_locus":
            return self._run_root_locus(params)
        elif sim_type == "step_response":
            return self._run_step_response(params)

    def _run_transfer_function(self, params):
        import control as ct

        num = params["numerator"]
        den = params["denominator"]
        sys = ct.TransferFunction(num, den)

        poles = np.roots(den)
        zeros = np.roots(num)
        is_stable = all(p.real < 0 for p in poles)
        dc_gain = float(num[-1] / den[-1]) if den[-1] != 0 else float('inf')

        return {
            "tool": "control",
            "simulation_type": "transfer_function",
            "numerator": num,
            "denominator": den,
            "poles_real": [float(p.real) for p in poles],
            "poles_imag": [float(p.imag) for p in poles],
            "zeros_real": [float(z.real) for z in zeros],
            "zeros_imag": [float(z.imag) for z in zeros],
            "dc_gain": dc_gain,
            "is_stable": is_stable,
        }

    def _run_state_space(self, params):
        import control as ct

        A = np.array(params["A"])
        B = np.array(params["B"])
        C = np.array(params["C"])
        D = np.array(params["D"])
        sys = ct.StateSpace(A, B, C, D)

        poles = np.linalg.eigvals(A)
        is_stable = all(p.real < 0 for p in poles)

        return {
            "tool": "control",
            "simulation_type": "state_space",
            "poles_real": [float(p.real) for p in poles],
            "poles_imag": [float(p.imag) for p in poles],
            "is_stable": is_stable,
            "n_states": int(A.shape[0]),
            "n_inputs": int(B.shape[1]) if B.ndim > 1 else 1,
            "n_outputs": int(C.shape[0]) if C.ndim > 1 else 1,
        }

    def _run_bode_plot(self, params):
        import control as ct

        num = params["numerator"]
        den = params["denominator"]
        sys = ct.TransferFunction(num, den)

        omega_range = params.get("omega_range", [0.01, 1000])
        omega = np.logspace(np.log10(omega_range[0]), np.log10(omega_range[1]), 500)

        response = ct.frequency_response(sys, omega)
        mag = np.abs(response.fresp).flatten()
        phase = np.angle(response.fresp, deg=True).flatten()
        mag_db = 20 * np.log10(mag)

        # Gain and phase margins
        try:
            gm, pm, wcg, wcp = ct.margin(sys)
            gm_db = float(20 * np.log10(gm)) if gm and gm != float('inf') else None
            pm_deg = float(pm) if pm else None
            crossover_freq = float(wcp) if wcp else None
        except Exception:
            gm_db = None
            pm_deg = None
            crossover_freq = None

        return {
            "tool": "control",
            "simulation_type": "bode_plot",
            "frequencies_rad": omega.tolist(),
            "magnitude_dB": mag_db.tolist(),
            "phase_deg": phase.tolist(),
            "gain_margin_dB": gm_db,
            "phase_margin_deg": pm_deg,
            "crossover_freq": crossover_freq,
        }

    def _run_nyquist_plot(self, params):
        import control as ct

        num = params["numerator"]
        den = params["denominator"]
        sys = ct.TransferFunction(num, den)

        omega_range = params.get("omega_range", [0.01, 1000])
        omega = np.logspace(np.log10(omega_range[0]), np.log10(omega_range[1]), 500)

        response = ct.frequency_response(sys, omega)
        fresp = response.fresp.flatten()
        real_part = np.real(fresp)
        imag_part = np.imag(fresp)

        # Stability via Nyquist criterion
        poles = np.roots(den)
        is_stable = all(p.real < 0 for p in poles)

        return {
            "tool": "control",
            "simulation_type": "nyquist_plot",
            "real": real_part.tolist(),
            "imag": imag_part.tolist(),
            "frequencies_rad": omega.tolist(),
            "is_stable": is_stable,
        }

    def _run_root_locus(self, params):
        import control as ct

        num = params["numerator"]
        den = params["denominator"]
        sys = ct.TransferFunction(num, den)

        k_range = params.get("k_range", [0, 100])
        gains = np.linspace(k_range[0], k_range[1], 500)

        roots_real = []
        roots_imag = []
        valid_gains = []

        for k in gains:
            closed_den = np.polyadd(den, np.polymul([k], num))
            r = np.roots(closed_den)
            roots_real.append([float(x.real) for x in r])
            roots_imag.append([float(x.imag) for x in r])
            valid_gains.append(float(k))

        return {
            "tool": "control",
            "simulation_type": "root_locus",
            "gains": valid_gains,
            "roots_real": roots_real,
            "roots_imag": roots_imag,
        }

    def _run_step_response(self, params):
        import control as ct

        if "A" in params:
            A = np.array(params["A"])
            B = np.array(params["B"])
            C = np.array(params["C"])
            D = np.array(params["D"])
            sys = ct.StateSpace(A, B, C, D)
        else:
            num = params["numerator"]
            den = params["denominator"]
            sys = ct.TransferFunction(num, den)

        t_final = params.get("t_final", 10.0)
        t = np.linspace(0, t_final, 1000)
        response = ct.step_response(sys, t)
        times = response.time.tolist()
        y = response.outputs.flatten().tolist()

        # Step response metrics
        y_arr = np.array(y)
        steady_state = float(y_arr[-1]) if len(y_arr) > 0 else 0.0

        # Settling time (2% band)
        settling_time = None
        if abs(steady_state) > 1e-10:
            band = 0.02 * abs(steady_state)
            for i in range(len(y_arr) - 1, -1, -1):
                if abs(y_arr[i] - steady_state) > band:
                    settling_time = float(times[min(i + 1, len(times) - 1)])
                    break

        # Overshoot
        if abs(steady_state) > 1e-10:
            peak = float(np.max(y_arr))
            overshoot_pct = float((peak - steady_state) / steady_state * 100)
            overshoot_pct = max(0, overshoot_pct)
        else:
            overshoot_pct = 0.0

        # Rise time (10% to 90%)
        rise_time = None
        if abs(steady_state) > 1e-10:
            t10 = None
            t90 = None
            for i, val in enumerate(y_arr):
                if t10 is None and val >= 0.1 * steady_state:
                    t10 = times[i]
                if t90 is None and val >= 0.9 * steady_state:
                    t90 = times[i]
            if t10 is not None and t90 is not None:
                rise_time = t90 - t10

        return {
            "tool": "control",
            "simulation_type": "step_response",
            "times": times,
            "response": y,
            "settling_time": settling_time,
            "overshoot_pct": overshoot_pct,
            "rise_time": rise_time,
            "steady_state": steady_state,
        }

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "bode_plot",
            "numerator": [1],
            "denominator": [0.001, 1],
            "omega_range": [0.1, 100000],
        }


@celery_app.task(name="tools.control_tool.run_control", bind=True)
def run_control(self, params: dict, project: str = "_default",
                label: str | None = None) -> dict:
    tool = ControlTool()

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting control systems analysis"})

    try:
        sim_type = params.get("simulation_type", "transfer_function")
        self.update_state(state="PROGRESS", meta={"progress": 0.1, "message": f"Running {sim_type}"})
        result = tool.run(params)
    except Exception as e:
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    save_result(self.request.id, "control", result, project, label)

    return result
