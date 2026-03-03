import json
import os
from datetime import datetime, timezone

import numpy as np
from worker import app


def _save_result(job_id: str, tool: str, data: dict, project: str = "_default",
                 label: str | None = None) -> str:
    """Save result to shared /data/results volume."""
    results_dir = os.getenv("RESULTS_DIR", "/data/results")
    project_dir = os.path.join(results_dir, project)
    os.makedirs(project_dir, exist_ok=True)
    run_dir = os.path.join(project_dir, job_id)
    os.makedirs(run_dir, exist_ok=True)

    metadata = {
        "job_id": job_id,
        "tool": tool,
        "project": project,
        "label": label,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with open(os.path.join(run_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
    with open(os.path.join(run_dir, "result.json"), "w") as f:
        json.dump(data, f)

    # Update index
    index_path = os.path.join(project_dir, "_index.json")
    index = []
    if os.path.exists(index_path):
        with open(index_path) as f:
            index = json.load(f)
    index.append(metadata)
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)

    return run_dir


@app.task(name="tools.nest_tool.run_nest", bind=True)
def run_nest(self, params: dict, project: str = "_default",
             label: str | None = None) -> dict:
    import nest

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Setting up NEST simulation"})

    sim_type = params.get("simulation_type", "balanced_network")
    if sim_type not in ("balanced_network", "cortical_column", "synfire_chain", "stdp_learning"):
        raise ValueError(f"Unknown simulation_type: {sim_type}")

    duration_ms = params.get("duration_ms", 500.0)
    dt_ms = params.get("dt_ms", 0.1)
    record_n = params.get("record_n_neurons", 50)

    nest.ResetKernel()
    nest.SetKernelStatus({"resolution": dt_ms})

    if sim_type == "balanced_network":
        result = _run_balanced(params, nest, duration_ms, record_n)
    elif sim_type == "cortical_column":
        result = _run_cortical(params, nest, duration_ms, record_n)
    elif sim_type == "synfire_chain":
        result = _run_synfire(params, nest, duration_ms, record_n)
    elif sim_type == "stdp_learning":
        result = _run_stdp(params, nest, duration_ms, record_n)

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    _save_result(self.request.id, "nest", result, project, label)

    return result


def _run_balanced(params, nest, duration_ms, record_n):
    """Brunel 2000 balanced network."""
    bp = params.get("balanced_network", {})
    n_exc = bp.get("n_excitatory", 4000)
    n_inh = bp.get("n_inhibitory", 1000)
    neuron_model = bp.get("neuron_model", "iaf_psc_alpha")
    conn_prob = bp.get("connection_probability", 0.1)
    w_exc = bp.get("weight_exc", 0.1)
    w_inh_factor = bp.get("weight_inh_factor", -5.0)
    delay = bp.get("delay_ms", 1.5)
    external_rate = bp.get("external_rate_hz", 8000.0)

    n_total = n_exc + n_inh

    # Create neurons
    exc_neurons = nest.Create(neuron_model, n_exc)
    inh_neurons = nest.Create(neuron_model, n_inh)
    all_neurons = exc_neurons + inh_neurons

    # External Poisson input
    noise = nest.Create("poisson_generator", params={"rate": external_rate})

    # Detectors
    n_record_actual = min(record_n, n_total)
    spike_rec = nest.Create("spike_recorder")
    vm_rec = nest.Create("multimeter", params={"record_from": ["V_m"], "interval": 1.0})

    # Connect noise to all neurons
    nest.Connect(noise, all_neurons, syn_spec={"weight": w_exc, "delay": delay})

    # Recurrent connections
    nest.Connect(exc_neurons, all_neurons,
                 conn_spec={"rule": "pairwise_bernoulli", "p": conn_prob},
                 syn_spec={"weight": w_exc, "delay": delay})
    nest.Connect(inh_neurons, all_neurons,
                 conn_spec={"rule": "pairwise_bernoulli", "p": conn_prob},
                 syn_spec={"weight": w_exc * w_inh_factor, "delay": delay})

    # Connect recorders
    nest.Connect(all_neurons[:n_record_actual], spike_rec)
    nest.Connect(vm_rec, all_neurons[:min(5, n_record_actual)])

    # Simulate
    nest.Simulate(duration_ms)

    return _extract_results(spike_rec, vm_rec, n_total, duration_ms, "balanced_network")


def _run_cortical(params, nest, duration_ms, record_n):
    """Simplified cortical column model (2-population)."""
    cp = params.get("cortical_column", {})
    n_exc = cp.get("n_excitatory", 800)
    n_inh = cp.get("n_inhibitory", 200)
    external_rate = cp.get("external_rate_hz", 5000.0)

    exc_neurons = nest.Create("iaf_psc_alpha", n_exc)
    inh_neurons = nest.Create("iaf_psc_alpha", n_inh)
    all_neurons = exc_neurons + inh_neurons

    noise = nest.Create("poisson_generator", params={"rate": external_rate})
    spike_rec = nest.Create("spike_recorder")
    vm_rec = nest.Create("multimeter", params={"record_from": ["V_m"], "interval": 1.0})

    n_total = n_exc + n_inh
    n_rec = min(record_n, n_total)

    nest.Connect(noise, all_neurons, syn_spec={"weight": 0.1, "delay": 1.0})
    nest.Connect(exc_neurons, all_neurons,
                 conn_spec={"rule": "pairwise_bernoulli", "p": 0.1},
                 syn_spec={"weight": 0.1, "delay": 1.5})
    nest.Connect(inh_neurons, all_neurons,
                 conn_spec={"rule": "pairwise_bernoulli", "p": 0.1},
                 syn_spec={"weight": -0.4, "delay": 0.8})

    nest.Connect(all_neurons[:n_rec], spike_rec)
    nest.Connect(vm_rec, all_neurons[:min(5, n_rec)])

    nest.Simulate(duration_ms)

    return _extract_results(spike_rec, vm_rec, n_total, duration_ms, "cortical_column")


def _run_synfire(params, nest, duration_ms, record_n):
    """Synfire chain — sequential activation of neuron groups."""
    sp = params.get("synfire_chain", {})
    n_groups = sp.get("n_groups", 10)
    group_size = sp.get("group_size", 100)
    w = sp.get("weight", 0.3)

    groups = []
    for _ in range(n_groups):
        groups.append(nest.Create("iaf_psc_alpha", group_size))

    # Chain connections
    for i in range(n_groups - 1):
        nest.Connect(groups[i], groups[i + 1],
                     conn_spec={"rule": "pairwise_bernoulli", "p": 0.5},
                     syn_spec={"weight": w, "delay": 2.0})

    # Initial kick to first group
    stim = nest.Create("spike_generator", params={"spike_times": [10.0]})
    nest.Connect(stim, groups[0], syn_spec={"weight": 5.0, "delay": 1.0})

    n_total = n_groups * group_size
    all_neurons = groups[0]
    for g in groups[1:]:
        all_neurons = all_neurons + g

    spike_rec = nest.Create("spike_recorder")
    vm_rec = nest.Create("multimeter", params={"record_from": ["V_m"], "interval": 1.0})

    n_rec = min(record_n, n_total)
    nest.Connect(all_neurons[:n_rec], spike_rec)
    nest.Connect(vm_rec, all_neurons[:min(5, n_rec)])

    nest.Simulate(duration_ms)

    return _extract_results(spike_rec, vm_rec, n_total, duration_ms, "synfire_chain")


def _run_stdp(params, nest, duration_ms, record_n):
    """STDP learning demonstration."""
    sp = params.get("stdp_learning", {})
    n_pre = sp.get("n_pre", 100)
    n_post = sp.get("n_post", 10)
    input_rate = sp.get("input_rate_hz", 10.0)

    pre_neurons = nest.Create("poisson_generator", n_pre, params={"rate": input_rate})
    post_neurons = nest.Create("iaf_psc_alpha", n_post)

    # Parrot neurons to relay Poisson spikes
    parrots = nest.Create("parrot_neuron", n_pre)
    nest.Connect(pre_neurons, parrots, "one_to_one")

    # STDP synapses
    nest.Connect(parrots, post_neurons,
                 conn_spec={"rule": "all_to_all"},
                 syn_spec={"synapse_model": "stdp_synapse",
                           "weight": 0.5,
                           "delay": 1.0})

    n_total = n_post
    spike_rec = nest.Create("spike_recorder")
    vm_rec = nest.Create("multimeter", params={"record_from": ["V_m"], "interval": 1.0})

    nest.Connect(post_neurons[:min(record_n, n_post)], spike_rec)
    nest.Connect(vm_rec, post_neurons[:min(5, n_post)])

    nest.Simulate(duration_ms)

    return _extract_results(spike_rec, vm_rec, n_total, duration_ms, "stdp_learning")


def _extract_results(spike_rec, vm_rec, n_total, duration_ms, sim_type):
    """Extract spike trains and voltage traces from NEST recorders."""
    events = spike_rec.get("events")
    spike_times = events["times"].tolist() if hasattr(events["times"], "tolist") else list(events["times"])
    spike_senders = events["senders"].tolist() if hasattr(events["senders"], "tolist") else list(events["senders"])

    # Downsample if too many spikes
    max_spikes = 500_000
    if len(spike_times) > max_spikes:
        indices = np.sort(np.random.choice(len(spike_times), max_spikes, replace=False))
        spike_times = [spike_times[i] for i in indices]
        spike_senders = [spike_senders[i] for i in indices]

    # Voltage traces
    vm_events = vm_rec.get("events")
    vm_times = vm_events["times"].tolist() if hasattr(vm_events["times"], "tolist") else list(vm_events["times"])
    vm_senders = vm_events["senders"].tolist() if hasattr(vm_events["senders"], "tolist") else list(vm_events["senders"])
    vm_values = vm_events["V_m"].tolist() if hasattr(vm_events["V_m"], "tolist") else list(vm_events["V_m"])

    # Group voltage by neuron
    neurons = {}
    unique_senders = sorted(set(vm_senders))
    for sender in unique_senders[:5]:
        mask = [i for i, s in enumerate(vm_senders) if s == sender]
        neurons[str(sender)] = [vm_values[i] for i in mask]

    # Unique voltage times
    voltage_times = sorted(set(vm_times))

    # Firing rates
    total_spikes = len(spike_times)
    duration_s = duration_ms / 1000.0
    mean_hz = total_spikes / (n_total * duration_s) if duration_s > 0 and n_total > 0 else 0.0

    return {
        "tool": "nest",
        "simulation_type": sim_type,
        "spike_trains": {
            "times_ms": spike_times,
            "neuron_ids": spike_senders,
        },
        "voltage_traces": {
            "times_ms": voltage_times,
            "neurons": neurons,
        },
        "firing_rates": {
            "mean_hz": mean_hz,
        },
        "n_neurons": n_total,
        "n_spikes": total_spikes,
        "duration_ms": duration_ms,
    }
