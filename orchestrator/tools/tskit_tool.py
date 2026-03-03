from typing import Any
import numpy as np
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result, load_result


class TreeSequenceTool(SimulationTool):
    """tskit — tree sequence analysis and manipulation.

    Provides post-hoc analysis of tree sequences produced by SLiM or msprime.
    Supports windowed diversity, Fst, and recapitation via pyslim.
    """

    name = "tskit"
    key = "tskit"
    layer = "evolution"

    SIMULATION_TYPES = {"tree_analysis", "diversity", "fst", "recapitate"}

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type", "tree_analysis")
        if sim_type not in self.SIMULATION_TYPES:
            raise ValueError(f"Unknown simulation_type: {sim_type}")
        params.setdefault("simulation_type", sim_type)
        params.setdefault("n_windows", 20)

        if sim_type == "fst":
            if "sample_sets" not in params:
                raise ValueError("sample_sets is required for fst analysis")

        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        import tskit

        params = self.validate_params(params)
        sim_type = params["simulation_type"]

        # Load tree sequence from a previous job result
        ts = self._load_tree_sequence(params, tskit)

        if sim_type == "tree_analysis":
            return self._run_tree_analysis(ts, params)
        elif sim_type == "diversity":
            return self._run_diversity(ts, params)
        elif sim_type == "fst":
            return self._run_fst(ts, params)
        elif sim_type == "recapitate":
            return self._run_recapitate(ts, params)

    def _load_tree_sequence(self, params, tskit):
        """Load a tree sequence from a previous job's result directory."""
        source_job_id = params.get("source_job_id")
        if not source_job_id:
            raise ValueError("source_job_id is required — reference a previous SLiM or msprime job")

        # Try to find the .trees file in the result directory
        import os
        import glob
        results_dir = os.getenv("RESULTS_DIR", "/data/results")

        # Search all project dirs for the job
        for project_dir in glob.glob(os.path.join(results_dir, "*")):
            trees_dir = os.path.join(project_dir, source_job_id)
            if os.path.isdir(trees_dir):
                # Look for .trees files
                trees_files = glob.glob(os.path.join(trees_dir, "*.trees"))
                if trees_files:
                    return tskit.load(trees_files[0])

                # If no .trees file, check if the result has tree sequence data
                result_path = os.path.join(trees_dir, "result.json")
                if os.path.exists(result_path):
                    import json
                    with open(result_path) as f:
                        result = json.load(f)

                    # If the result came from msprime, regenerate the tree sequence
                    if result.get("tool") == "msprime":
                        return self._regenerate_from_msprime(result)

        raise FileNotFoundError(
            f"No tree sequence data found for job {source_job_id}. "
            "Ensure the source job completed and produced tree sequence output."
        )

    def _regenerate_from_msprime(self, result):
        """Re-run msprime to get a tree sequence (since msprime stores stats, not .trees)."""
        import msprime

        params = {
            "n_samples": result.get("n_samples", 50),
            "sequence_length": result.get("sequence_length", 100_000),
            "population_size": result.get("population_size", 10_000),
        }

        ts = msprime.sim_ancestry(
            samples=params["n_samples"],
            sequence_length=params["sequence_length"],
            population_size=params["population_size"],
            random_seed=42,
        )
        return msprime.sim_mutations(ts, rate=1e-8, random_seed=42)

    def _run_tree_analysis(self, ts, params):
        """Basic tree sequence summary statistics."""
        n_trees = ts.num_trees
        n_mutations = ts.num_mutations
        n_samples = ts.num_samples
        seq_len = int(ts.sequence_length)

        # Mean TMRCA
        total_bl = sum(t.total_branch_length for t in ts.trees())
        mean_tmrca = total_bl / n_trees if n_trees > 0 else 0.0

        # First N tree topologies (simplified)
        tree_info = []
        for i, tree in enumerate(ts.trees()):
            if i >= 10:
                break
            tree_info.append({
                "index": i,
                "interval": [float(tree.interval.left), float(tree.interval.right)],
                "num_roots": tree.num_roots,
                "total_branch_length": float(tree.total_branch_length),
            })

        return {
            "tool": "tskit",
            "simulation_type": "tree_analysis",
            "n_trees": n_trees,
            "n_mutations": n_mutations,
            "n_samples": n_samples,
            "sequence_length": seq_len,
            "mean_tmrca": mean_tmrca,
            "trees": tree_info,
            "allele_frequencies": {"bins": [], "counts": []},
            "windowed_diversity": {"positions": [], "pi": []},
            "windowed_tajimas_d": {"positions": [], "D": []},
        }

    def _run_diversity(self, ts, params):
        """Windowed nucleotide diversity + Tajima's D + SFS."""
        n_windows = params.get("n_windows", 20)
        seq_len = int(ts.sequence_length)

        # SFS
        afs = ts.allele_frequency_spectrum(polarised=True, span_normalise=False)
        sfs = afs[1:-1].tolist() if len(afs) > 2 else afs.tolist()
        sfs_bins = list(range(1, len(sfs) + 1))

        # Windowed stats
        windows = np.linspace(0, seq_len, n_windows + 1).astype(int).tolist()
        window_centers = [(windows[i] + windows[i + 1]) / 2 for i in range(len(windows) - 1)]

        diversity = ts.diversity(windows=windows)
        div_vals = diversity.tolist() if hasattr(diversity, "tolist") else [float(diversity)]

        tajimas_d = ts.Tajimas_D(windows=windows)
        td_vals = tajimas_d.tolist() if hasattr(tajimas_d, "tolist") else [float(tajimas_d)]

        return {
            "tool": "tskit",
            "simulation_type": "diversity",
            "n_trees": ts.num_trees,
            "n_mutations": ts.num_mutations,
            "n_samples": ts.num_samples,
            "sequence_length": seq_len,
            "allele_frequencies": {"bins": sfs_bins, "counts": sfs},
            "windowed_diversity": {"positions": window_centers, "pi": div_vals},
            "windowed_tajimas_d": {"positions": window_centers, "D": td_vals},
        }

    def _run_fst(self, ts, params):
        """Multi-population Fst between sample sets."""
        sample_sets = params["sample_sets"]
        n_windows = params.get("n_windows", 20)
        seq_len = int(ts.sequence_length)

        windows = np.linspace(0, seq_len, n_windows + 1).astype(int).tolist()
        window_centers = [(windows[i] + windows[i + 1]) / 2 for i in range(len(windows) - 1)]

        # Compute pairwise Fst
        fst_values = []
        population_pairs = []
        for i in range(len(sample_sets)):
            for j in range(i + 1, len(sample_sets)):
                fst = ts.Fst([sample_sets[i], sample_sets[j]], windows=windows)
                fst_list = fst.tolist() if hasattr(fst, "tolist") else [float(fst)]
                fst_values.append(fst_list)
                population_pairs.append([i, j])

        return {
            "tool": "tskit",
            "simulation_type": "fst",
            "n_trees": ts.num_trees,
            "n_mutations": ts.num_mutations,
            "n_samples": ts.num_samples,
            "sequence_length": seq_len,
            "fst_values": fst_values,
            "population_pairs": population_pairs,
            "windowed_diversity": {"positions": window_centers, "pi": []},
            "windowed_tajimas_d": {"positions": window_centers, "D": []},
            "allele_frequencies": {"bins": [], "counts": []},
        }

    def _run_recapitate(self, ts, params):
        """Recapitate a SLiM tree sequence using pyslim + msprime coalescent."""
        import pyslim
        import msprime

        pop_size = params.get("population_size", 10_000)
        rec_rate = params.get("recombination_rate", 1e-8)
        mut_rate = params.get("mutation_rate", 1e-8)

        # Recapitate: add coalescent history above the SLiM tree sequence
        rts = pyslim.recapitate(ts, recombination_rate=rec_rate, ancestral_Ne=pop_size)

        # Add neutral mutations if the tree sequence lacks them
        if rts.num_mutations == 0:
            rts = msprime.sim_mutations(rts, rate=mut_rate, random_seed=42)

        # Compute stats on the recapitated tree sequence
        n_windows = params.get("n_windows", 20)
        seq_len = int(rts.sequence_length)
        windows = np.linspace(0, seq_len, n_windows + 1).astype(int).tolist()
        window_centers = [(windows[i] + windows[i + 1]) / 2 for i in range(len(windows) - 1)]

        afs = rts.allele_frequency_spectrum(polarised=True, span_normalise=False)
        sfs = afs[1:-1].tolist() if len(afs) > 2 else afs.tolist()
        sfs_bins = list(range(1, len(sfs) + 1))

        diversity = rts.diversity(windows=windows)
        div_vals = diversity.tolist() if hasattr(diversity, "tolist") else [float(diversity)]

        tajimas_d = rts.Tajimas_D(windows=windows)
        td_vals = tajimas_d.tolist() if hasattr(tajimas_d, "tolist") else [float(tajimas_d)]

        return {
            "tool": "tskit",
            "simulation_type": "recapitate",
            "n_trees": rts.num_trees,
            "n_mutations": rts.num_mutations,
            "n_samples": rts.num_samples,
            "sequence_length": seq_len,
            "allele_frequencies": {"bins": sfs_bins, "counts": sfs},
            "windowed_diversity": {"positions": window_centers, "pi": div_vals},
            "windowed_tajimas_d": {"positions": window_centers, "D": td_vals},
            "population_size": pop_size,
        }

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "diversity",
            "source_job_id": "",
            "n_windows": 20,
        }


@celery_app.task(name="tools.tskit_tool.run_tskit", bind=True)
def run_tskit(self, params: dict, project: str = "_default",
              label: str | None = None) -> dict:
    tool = TreeSequenceTool()

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting tskit analysis"})

    try:
        result = tool.run(params)
    except Exception as e:
        self.update_state(state="FAILURE", meta={"message": str(e)})
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})

    save_result(self.request.id, "tskit", result, project, label)

    return result
