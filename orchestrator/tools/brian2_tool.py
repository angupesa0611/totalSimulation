from typing import Any
import numpy as np
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result


def _convert_copasi_to_current(copasi_result, target_species=None, I_max=2.0):
    """Convert COPASI concentration time-series to Brian2 input current.

    COPASI operates in seconds; Brian2 operates in milliseconds.
    Concentrations are normalized to [0, I_max] nA.

    Args:
        copasi_result: Result dict from BasiCO (must have 'times' and 'species')
        target_species: Which species concentration to use as current driver.
                        If None, uses the first species.
        I_max: Maximum current in nA (default 2.0)

    Returns:
        dict with 'times_ms' and 'values_nA' arrays
    """
    times_s = np.array(copasi_result["times"])
    species = copasi_result["species"]

    if target_species and target_species in species:
        concentrations = np.array(species[target_species])
    else:
        # Use first species
        first_key = next(iter(species))
        concentrations = np.array(species[first_key])

    # Convert seconds to milliseconds
    times_ms = (times_s * 1000.0).tolist()

    # Normalize concentration to [0, I_max] nA
    c_min = float(np.min(concentrations))
    c_max = float(np.max(concentrations))
    if c_max - c_min > 1e-15:
        normalized = (concentrations - c_min) / (c_max - c_min) * I_max
    else:
        normalized = np.full_like(concentrations, I_max / 2)

    return {
        "times_ms": times_ms,
        "values_nA": normalized.tolist(),
    }


class Brian2Tool(SimulationTool):
    name = "Brian2"
    key = "brian2"
    layer = "neuroscience"

    SIMULATION_TYPES = {"lif", "hodgkin_huxley", "izhikevich", "custom_equations"}

    # Izhikevich neuron type presets (a, b, c, d)
    IZHIKEVICH_TYPES = {
        "RS": (0.02, 0.2, -65.0, 8.0),    # Regular spiking
        "IB": (0.02, 0.2, -55.0, 4.0),    # Intrinsically bursting
        "CH": (0.02, 0.2, -50.0, 2.0),    # Chattering
        "FS": (0.1, 0.2, -65.0, 2.0),     # Fast spiking
        "LTS": (0.02, 0.25, -65.0, 2.0),  # Low-threshold spiking
    }

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type", "lif")
        if sim_type not in self.SIMULATION_TYPES:
            raise ValueError(f"Unknown simulation_type: {sim_type}")
        params.setdefault("simulation_type", sim_type)
        params.setdefault("n_neurons", 100)
        params.setdefault("duration_ms", 500.0)
        params.setdefault("dt_ms", 0.1)

        if params["n_neurons"] < 1 or params["n_neurons"] > 10000:
            raise ValueError("n_neurons must be between 1 and 10000")
        if params["duration_ms"] < 1 or params["duration_ms"] > 10000:
            raise ValueError("duration_ms must be between 1 and 10000")

        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        import brian2
        brian2.prefs.codegen.target = "numpy"

        params = self.validate_params(params)
        sim_type = params["simulation_type"]

        # Handle pipeline input: convert COPASI result to current
        if "input_current_timeseries" in params and params["input_current_timeseries"]:
            copasi_data = params["input_current_timeseries"]
            target_species = params.get("target_species")
            converted = _convert_copasi_to_current(copasi_data, target_species)
            params["_converted_current"] = converted

        if sim_type == "lif":
            return self._run_lif(params, brian2)
        elif sim_type == "hodgkin_huxley":
            return self._run_hh(params, brian2)
        elif sim_type == "izhikevich":
            return self._run_izhikevich(params, brian2)
        elif sim_type == "custom_equations":
            return self._run_custom(params, brian2)

    def _run_lif(self, params, brian2):
        brian2.start_scope()

        n_neurons = params["n_neurons"]
        duration = params["duration_ms"] * brian2.ms
        dt = params["dt_ms"] * brian2.ms
        brian2.defaultclock.dt = dt

        lif_params = params.get("lif", {})
        tau_m = lif_params.get("tau_m", 10.0) * brian2.ms
        v_rest = lif_params.get("v_rest", -65.0) * brian2.mV
        v_threshold = lif_params.get("v_threshold", -50.0) * brian2.mV
        v_reset = lif_params.get("v_reset", -65.0) * brian2.mV
        tau_refrac = lif_params.get("tau_refrac", 2.0) * brian2.ms

        eqs = """
        dv/dt = (v_rest - v + I) / tau_m : volt (unless refractory)
        I : volt
        """

        G = brian2.NeuronGroup(
            n_neurons, eqs,
            threshold="v > v_threshold",
            reset="v = v_reset",
            refractory=tau_refrac,
            method="euler",
        )
        G.v = v_rest

        # Input: either from pipeline or Poisson input
        converted = params.get("_converted_current")
        if converted:
            # Use time-varying current from COPASI pipeline
            times_ms = np.array(converted["times_ms"])
            values_nA = np.array(converted["values_nA"])
            # Create TimedArray for current injection
            # Convert nA to voltage-equivalent (I term in LIF has volt units)
            current_values = values_nA * 20.0  # scale factor: nA -> mV equivalent
            ta = brian2.TimedArray(current_values * brian2.mV, dt=brian2.ms * (times_ms[1] - times_ms[0]) if len(times_ms) > 1 else brian2.ms)
            G.run_regularly("I = ta(t)", dt=brian2.defaultclock.dt)
        else:
            input_rate = lif_params.get("input_rate_hz", 15.0) * brian2.Hz
            weight = lif_params.get("weight", 1.5) * brian2.mV
            P = brian2.PoissonInput(G, "v", N=1, rate=input_rate, weight=weight)

        # Monitors
        spike_mon = brian2.SpikeMonitor(G)
        n_record = min(5, n_neurons)
        state_mon = brian2.StateMonitor(G, "v", record=range(n_record))

        brian2.run(duration)

        return self._build_result(params, spike_mon, state_mon, brian2, n_record)

    def _run_hh(self, params, brian2):
        brian2.start_scope()

        n_neurons = params["n_neurons"]
        duration = params["duration_ms"] * brian2.ms
        dt = params["dt_ms"] * brian2.ms
        brian2.defaultclock.dt = dt

        hh_params = params.get("hodgkin_huxley", {})
        I_ext = hh_params.get("I_ext", 10.0)
        g_Na = hh_params.get("g_Na", 120.0)
        g_K = hh_params.get("g_K", 36.0)
        g_L = hh_params.get("g_L", 0.3)

        area = 20000 * brian2.umetre ** 2
        Cm = 1 * brian2.ufarad * brian2.cm ** -2 * area
        gl = g_L * brian2.msiemens * brian2.cm ** -2 * area
        El = -54.387 * brian2.mV
        EK = -77.0 * brian2.mV
        ENa = 50.0 * brian2.mV
        g_na = g_Na * brian2.msiemens * brian2.cm ** -2 * area
        g_kd = g_K * brian2.msiemens * brian2.cm ** -2 * area
        VT = -63.0 * brian2.mV

        eqs = brian2.Equations("""
        dv/dt = (gl*(El-v) - g_na*(m*m*m)*h*(v-ENa) - g_kd*(n*n*n*n)*(v-EK) + I_inj)/Cm : volt
        dm/dt = 0.32*(brian2.mV**-1)*4*brian2.mV/brian2.ms/(exprel(-(v-VT-13*brian2.mV)/(4*brian2.mV)))*(1-m)-0.28*(brian2.mV**-1)*5*brian2.mV/brian2.ms/(exprel((v-VT-40*brian2.mV)/(5*brian2.mV)))*m : 1
        dn/dt = 0.032*(brian2.mV**-1)*5*brian2.mV/brian2.ms/(exprel(-(v-VT-15*brian2.mV)/(5*brian2.mV)))*(1-n)-0.5/brian2.ms*exp(-(v-VT-10*brian2.mV)/(40*brian2.mV))*n : 1
        dh/dt = 0.128/brian2.ms*exp(-(v-VT-17*brian2.mV)/(18*brian2.mV))*(1-h)-4./brian2.ms/(1+exp(-(v-VT-40*brian2.mV)/(5*brian2.mV)))*h : 1
        I_inj : amp
        """)

        G = brian2.NeuronGroup(n_neurons, eqs, threshold="v > -20*mV",
                               refractory=3 * brian2.ms, method="exponential_euler")
        G.v = El
        G.I_inj = I_ext * brian2.nA

        spike_mon = brian2.SpikeMonitor(G)
        n_record = min(5, n_neurons)
        state_mon = brian2.StateMonitor(G, "v", record=range(n_record))

        brian2.run(duration)

        return self._build_result(params, spike_mon, state_mon, brian2, n_record)

    def _run_izhikevich(self, params, brian2):
        brian2.start_scope()

        n_neurons = params["n_neurons"]
        duration = params["duration_ms"] * brian2.ms
        dt = params["dt_ms"] * brian2.ms
        brian2.defaultclock.dt = dt

        iz_params = params.get("izhikevich", {})
        neuron_type = iz_params.get("neuron_type", "RS")
        I_ext = iz_params.get("I_ext", 10.0)

        a, b, c, d = self.IZHIKEVICH_TYPES.get(neuron_type, self.IZHIKEVICH_TYPES["RS"])

        eqs = """
        dv/dt = (0.04*v**2/mV + 5*v + 140*mV - u + I) / ms : volt
        du/dt = a_iz * (b_iz*v - u) / ms : volt
        I : volt
        a_iz : 1
        b_iz : 1
        """

        G = brian2.NeuronGroup(
            n_neurons, eqs,
            threshold="v >= 30*mV",
            reset="v = c_iz*mV; u += d_iz*mV",
            method="euler",
            namespace={"c_iz": c, "d_iz": d},
        )
        G.v = c * brian2.mV
        G.u = b * c * brian2.mV
        G.a_iz = a
        G.b_iz = b
        G.I = I_ext * brian2.mV

        spike_mon = brian2.SpikeMonitor(G)
        n_record = min(5, n_neurons)
        state_mon = brian2.StateMonitor(G, "v", record=range(n_record))

        brian2.run(duration)

        return self._build_result(params, spike_mon, state_mon, brian2, n_record)

    def _run_custom(self, params, brian2):
        brian2.start_scope()

        n_neurons = params["n_neurons"]
        duration = params["duration_ms"] * brian2.ms
        dt = params["dt_ms"] * brian2.ms
        brian2.defaultclock.dt = dt

        equations = params.get("equations", "dv/dt = -v / (10*ms) : volt")
        threshold_cond = params.get("threshold", "v > -50*mV")
        reset_cond = params.get("reset", "v = -65*mV")

        G = brian2.NeuronGroup(
            n_neurons, equations,
            threshold=threshold_cond,
            reset=reset_cond,
            method="euler",
        )
        # Apply user-provided initial value or default
        init_str = params.get("initial_value", "").strip()
        if init_str:
            # Parse "N*mV" format safely
            import re
            m = re.match(r'^(-?[\d.]+)\s*\*\s*mV$', init_str)
            if m:
                G.v = float(m.group(1)) * brian2.mV
            else:
                G.v = -65.0 * brian2.mV
        else:
            G.v = -65.0 * brian2.mV

        spike_mon = brian2.SpikeMonitor(G)
        n_record = min(5, n_neurons)
        state_mon = brian2.StateMonitor(G, "v", record=range(n_record))

        brian2.run(duration)

        return self._build_result(params, spike_mon, state_mon, brian2, n_record)

    def _build_result(self, params, spike_mon, state_mon, brian2, n_record):
        # Extract spike trains
        spike_times = np.array(spike_mon.t / brian2.ms).tolist()
        spike_ids = np.array(spike_mon.i).tolist()

        # Extract voltage traces
        voltage_times = np.array(state_mon.t / brian2.ms).tolist()
        neurons = {}
        for idx in range(n_record):
            neurons[str(idx)] = np.array(state_mon.v[idx] / brian2.mV).tolist()

        # Firing rates
        n_neurons = params["n_neurons"]
        duration_s = params["duration_ms"] / 1000.0
        total_spikes = len(spike_times)
        mean_hz = total_spikes / (n_neurons * duration_s) if duration_s > 0 else 0.0

        per_neuron = np.zeros(n_neurons)
        for nid in spike_ids:
            if 0 <= nid < n_neurons:
                per_neuron[int(nid)] += 1
        per_neuron = (per_neuron / duration_s).tolist() if duration_s > 0 else per_neuron.tolist()

        return {
            "tool": "brian2",
            "simulation_type": params["simulation_type"],
            "spike_trains": {
                "times_ms": spike_times,
                "neuron_ids": spike_ids,
            },
            "voltage_traces": {
                "times_ms": voltage_times,
                "neurons": neurons,
            },
            "firing_rates": {
                "mean_hz": mean_hz,
                "per_neuron": per_neuron,
            },
            "n_neurons": n_neurons,
            "n_spikes": total_spikes,
            "duration_ms": params["duration_ms"],
        }

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "lif",
            "n_neurons": 100,
            "duration_ms": 500.0,
            "dt_ms": 0.1,
            "lif": {
                "tau_m": 10.0,
                "v_rest": -65.0,
                "v_threshold": -50.0,
                "v_reset": -65.0,
                "tau_refrac": 2.0,
                "input_rate_hz": 15.0,
                "weight": 1.5,
            },
        }


@celery_app.task(name="tools.brian2_tool.run_brian2", bind=True)
def run_brian2(self, params: dict, project: str = "_default",
               label: str | None = None) -> dict:
    tool = Brian2Tool()

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting Brian2 simulation"})

    try:
        result = tool.run(params)
    except Exception as e:
        self.update_state(state="FAILURE", meta={"message": str(e)})
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})

    save_result(self.request.id, "brian2", result, project, label)

    return result
