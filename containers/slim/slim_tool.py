"""SLiM — forward-time evolutionary simulation via Eidos scripting.

SLiM is a compiled C++ binary that runs its own Eidos scripting language.
This tool generates Eidos scripts from templates, executes them via subprocess,
and parses the resulting .trees files with tskit for population genetics statistics.

Simulation types:
  - neutral_evolution: Wright-Fisher neutral mutations with tree sequence recording
  - selection: Beneficial/deleterious mutations with configurable selection coefficient
  - nucleotide_evolution: Nucleotide-level mutation model (A/C/G/T)
  - spatial: 2D continuous-space non-Wright-Fisher model with dispersal
"""

import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone

import numpy as np
import tskit

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


# ── Eidos Script Templates ─────────────────────────────────────────────

NEUTRAL_TEMPLATE = """\
initialize() {{
    initializeTreeSeq();
    initializeMutationRate({mutation_rate});
    initializeMutationType("m1", 0.5, "f", 0.0);
    initializeGenomicElementType("g1", m1, 1.0);
    initializeGenomicElement(g1, 0, {seq_length_minus1});
    initializeRecombinationRate({recombination_rate});
}}
1 early() {{
    sim.addSubpop("p1", {population_size});
}}
{n_generations} late() {{
    sim.treeSeqOutput("{output_path}");
    sim.simulationFinished();
}}
"""

SELECTION_TEMPLATE = """\
initialize() {{
    initializeTreeSeq();
    initializeMutationRate({mutation_rate});
    initializeMutationType("m1", 0.5, "f", 0.0);        // neutral
    initializeMutationType("m2", 0.5, "f", {sel_coeff}); // selected
    initializeGenomicElementType("g1", c(m1, m2), c(0.9, 0.1));
    initializeGenomicElement(g1, 0, {seq_length_minus1});
    initializeRecombinationRate({recombination_rate});
}}
1 early() {{
    sim.addSubpop("p1", {population_size});
}}
{n_generations} late() {{
    sim.treeSeqOutput("{output_path}");
    sim.simulationFinished();
}}
"""

NUCLEOTIDE_TEMPLATE = """\
initialize() {{
    initializeSLiMModelType("nonWF");
    initializeTreeSeq();
    initializeMutationTypeNuc("m1", 0.5, "f", 0.0);
    initializeGenomicElementType("g1", m1, 1.0, mutMatrix=c(0.0, {mu}, {mu}, {mu},
                                                             {mu}, 0.0, {mu}, {mu},
                                                             {mu}, {mu}, 0.0, {mu},
                                                             {mu}, {mu}, {mu}, 0.0));
    initializeGenomicElement(g1, 0, {seq_length_minus1});
    initializeRecombinationRate({recombination_rate});
}}
reproduction(p1) {{
    subpop.addCrossed(individual, subpop.sampleIndividuals(1));
}}
1 early() {{
    sim.addSubpop("p1", {population_size});
}}
early() {{
    p1.fitnessScaling = {population_size} / p1.individualCount;
}}
{n_generations} late() {{
    sim.treeSeqOutput("{output_path}");
    sim.simulationFinished();
}}
"""

SPATIAL_TEMPLATE = """\
initialize() {{
    initializeSLiMModelType("nonWF");
    initializeTreeSeq();
    initializeSLiMOptions(dimensionality="xy");
    initializeMutationRate({mutation_rate});
    initializeMutationType("m1", 0.5, "f", 0.0);
    initializeGenomicElementType("g1", m1, 1.0);
    initializeGenomicElement(g1, 0, {seq_length_minus1});
    initializeRecombinationRate({recombination_rate});
    initializeInteractionType(1, "xy", reciprocal=T, maxDistance=0.3);
    i1.setInteractionFunction("n", 1.0, 0.1);
}}
reproduction() {{
    mate = i1.drawByStrength(individual, 1);
    if (mate.size())
        subpop.addCrossed(individual, mate);
}}
1 early() {{
    sim.addSubpop("p1", {population_size});
    p1.setSpatialBounds(c(0.0, 0.0, 1.0, 1.0));
    p1.individuals.setSpatialPosition(p1.pointUniform(p1.individualCount));
}}
early() {{
    i1.evaluate(p1);
    p1.fitnessScaling = {population_size} / p1.individualCount;
}}
late() {{
    // Spatial dispersal
    for (ind in p1.individuals) {{
        newPos = ind.spatialPosition + rnorm(2, 0, 0.02);
        ind.setSpatialPosition(p1.pointReflected(newPos));
    }}
}}
{n_generations} late() {{
    sim.treeSeqOutput("{output_path}");
    sim.simulationFinished();
}}
"""


def _compute_stats(ts, params):
    """Compute population genetics statistics from a tree sequence (same format as msprime)."""
    n_samples = min(params.get("n_samples", 50), ts.num_samples)
    n_windows = params.get("n_windows", 20)
    seq_len = int(ts.sequence_length)

    # Simplify to n_samples if needed
    if n_samples < ts.num_samples:
        rng = np.random.default_rng(42)
        sample_ids = rng.choice(ts.samples(), size=n_samples, replace=False).tolist()
        ts = ts.simplify(samples=sample_ids)

    n_trees = ts.num_trees
    n_mutations = ts.num_mutations

    # Site frequency spectrum
    afs = ts.allele_frequency_spectrum(polarised=True, span_normalise=False)
    sfs = afs[1:-1].tolist() if len(afs) > 2 else afs.tolist()
    sfs_bins = list(range(1, len(sfs) + 1))

    # Mean TMRCA
    total_tmrca = 0.0
    count = 0
    for tree in ts.trees():
        total_tmrca += tree.total_branch_length
        count += 1
    mean_tmrca = total_tmrca / count if count > 0 else 0.0

    # Windowed diversity
    windows = np.linspace(0, seq_len, n_windows + 1).astype(int).tolist()
    diversity = ts.diversity(windows=windows)
    diversity_values = diversity.tolist() if hasattr(diversity, "tolist") else [float(diversity)]
    window_centers = [(windows[i] + windows[i + 1]) / 2 for i in range(len(windows) - 1)]

    # Windowed Tajima's D
    tajimas_d = ts.Tajimas_D(windows=windows)
    tajimas_d_values = tajimas_d.tolist() if hasattr(tajimas_d, "tolist") else [float(tajimas_d)]

    # Mutation log (first 100 mutations)
    mutation_log = []
    for mut in ts.mutations():
        if len(mutation_log) >= 100:
            break
        mutation_log.append({
            "position": int(mut.position),
            "time": float(mut.time),
            "type": "neutral",
        })

    return {
        "allele_frequencies": {"bins": sfs_bins, "counts": sfs},
        "windowed_diversity": {"positions": window_centers, "pi": diversity_values},
        "windowed_tajimas_d": {"positions": window_centers, "D": tajimas_d_values},
        "n_trees": n_trees,
        "n_mutations": n_mutations,
        "sequence_length": seq_len,
        "mean_tmrca": mean_tmrca,
        "n_samples": n_samples,
        "mutation_log": mutation_log,
    }


def _run_slim_script(script: str, output_path: str, timeout: int = 280) -> tskit.TreeSequence:
    """Write an Eidos script to a tempfile, run slim, and load the output tree sequence."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".slim", delete=False) as f:
        f.write(script)
        script_path = f.name

    try:
        result = subprocess.run(
            ["slim", script_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            raise RuntimeError(f"SLiM failed (exit {result.returncode}): {result.stderr[:500]}")

        return tskit.load(output_path)
    finally:
        if os.path.exists(script_path):
            os.unlink(script_path)


def _run_neutral(params: dict) -> dict:
    pop_size = params.get("population_size", 500)
    n_gens = params.get("n_generations", 1000)
    mut_rate = params.get("mutation_rate", 1e-7)
    rec_rate = params.get("recombination_rate", 1e-8)
    seq_len = params.get("sequence_length", 100_000)

    with tempfile.NamedTemporaryFile(suffix=".trees", delete=False) as tf:
        output_path = tf.name

    try:
        script = NEUTRAL_TEMPLATE.format(
            mutation_rate=mut_rate,
            recombination_rate=rec_rate,
            seq_length_minus1=seq_len - 1,
            population_size=pop_size,
            n_generations=n_gens,
            output_path=output_path,
        )
        ts = _run_slim_script(script, output_path)
        stats = _compute_stats(ts, params)
        stats.update({
            "tool": "slim",
            "simulation_type": "neutral_evolution",
            "population_size": pop_size,
            "n_generations": n_gens,
        })
        return stats
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def _run_selection(params: dict) -> dict:
    pop_size = params.get("population_size", 500)
    n_gens = params.get("n_generations", 1000)
    mut_rate = params.get("mutation_rate", 1e-7)
    rec_rate = params.get("recombination_rate", 1e-8)
    seq_len = params.get("sequence_length", 100_000)
    sel_coeff = params.get("selection_coefficient", 0.01)

    with tempfile.NamedTemporaryFile(suffix=".trees", delete=False) as tf:
        output_path = tf.name

    try:
        script = SELECTION_TEMPLATE.format(
            mutation_rate=mut_rate,
            recombination_rate=rec_rate,
            seq_length_minus1=seq_len - 1,
            population_size=pop_size,
            n_generations=n_gens,
            sel_coeff=sel_coeff,
            output_path=output_path,
        )
        ts = _run_slim_script(script, output_path)
        stats = _compute_stats(ts, params)
        stats.update({
            "tool": "slim",
            "simulation_type": "selection",
            "population_size": pop_size,
            "n_generations": n_gens,
            "selection_coefficient": sel_coeff,
        })
        return stats
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def _run_nucleotide(params: dict) -> dict:
    pop_size = params.get("population_size", 500)
    n_gens = params.get("n_generations", 500)
    mut_rate = params.get("mutation_rate", 1e-7)
    rec_rate = params.get("recombination_rate", 1e-8)
    seq_len = params.get("sequence_length", 10_000)

    with tempfile.NamedTemporaryFile(suffix=".trees", delete=False) as tf:
        output_path = tf.name

    try:
        script = NUCLEOTIDE_TEMPLATE.format(
            mu=mut_rate,
            recombination_rate=rec_rate,
            seq_length_minus1=seq_len - 1,
            population_size=pop_size,
            n_generations=n_gens,
            output_path=output_path,
        )
        ts = _run_slim_script(script, output_path)
        stats = _compute_stats(ts, params)
        stats.update({
            "tool": "slim",
            "simulation_type": "nucleotide_evolution",
            "population_size": pop_size,
            "n_generations": n_gens,
        })
        return stats
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def _run_spatial(params: dict) -> dict:
    pop_size = params.get("population_size", 200)
    n_gens = params.get("n_generations", 500)
    mut_rate = params.get("mutation_rate", 1e-7)
    rec_rate = params.get("recombination_rate", 1e-8)
    seq_len = params.get("sequence_length", 50_000)

    with tempfile.NamedTemporaryFile(suffix=".trees", delete=False) as tf:
        output_path = tf.name

    try:
        script = SPATIAL_TEMPLATE.format(
            mutation_rate=mut_rate,
            recombination_rate=rec_rate,
            seq_length_minus1=seq_len - 1,
            population_size=pop_size,
            n_generations=n_gens,
            output_path=output_path,
        )
        ts = _run_slim_script(script, output_path)
        stats = _compute_stats(ts, params)
        stats.update({
            "tool": "slim",
            "simulation_type": "spatial",
            "population_size": pop_size,
            "n_generations": n_gens,
        })
        return stats
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


@app.task(name="tools.slim_tool.run_slim", bind=True, soft_time_limit=300)
def run_slim(self, params: dict, project: str = "_default",
             label: str | None = None) -> dict:
    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting SLiM simulation"})

    sim_type = params.get("simulation_type", "neutral_evolution")

    runners = {
        "neutral_evolution": _run_neutral,
        "selection": _run_selection,
        "nucleotide_evolution": _run_nucleotide,
        "spatial": _run_spatial,
    }

    if sim_type not in runners:
        raise ValueError(f"Unknown simulation_type: {sim_type}. Must be one of {list(runners.keys())}")

    self.update_state(state="PROGRESS", meta={"progress": 0.1, "message": f"Running SLiM {sim_type}"})

    result = runners[sim_type](params)

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    _save_result(self.request.id, "slim", result, project, label)

    return result
