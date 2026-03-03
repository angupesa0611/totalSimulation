from typing import Any
import numpy as np
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result


class MsprimeTool(SimulationTool):
    name = "msprime"
    key = "msprime"
    layer = "evolution"

    SIMULATION_TYPES = {
        "coalescent", "demographic_model", "selective_sweep", "recombination",
    }

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type", "coalescent")
        if sim_type not in self.SIMULATION_TYPES:
            raise ValueError(f"Unknown simulation_type: {sim_type}")
        params.setdefault("simulation_type", sim_type)
        params.setdefault("n_samples", 50)
        params.setdefault("sequence_length", 100_000)
        params.setdefault("recombination_rate", 1e-8)
        params.setdefault("mutation_rate", 1e-8)
        params.setdefault("population_size", 10_000)
        params.setdefault("n_windows", 20)

        if params["n_samples"] < 2 or params["n_samples"] > 1000:
            raise ValueError("n_samples must be between 2 and 1000")
        if params["sequence_length"] < 100 or params["sequence_length"] > 10_000_000:
            raise ValueError("sequence_length must be between 100 and 10,000,000")

        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        import msprime
        import tskit

        params = self.validate_params(params)
        sim_type = params["simulation_type"]

        if sim_type == "coalescent":
            return self._run_coalescent(params, msprime)
        elif sim_type == "demographic_model":
            return self._run_demographic(params, msprime)
        elif sim_type == "selective_sweep":
            return self._run_sweep(params, msprime)
        elif sim_type == "recombination":
            return self._run_recombination(params, msprime)

    def _run_coalescent(self, params, msprime):
        seed = params.get("random_seed")

        ts = msprime.sim_ancestry(
            samples=params["n_samples"],
            sequence_length=params["sequence_length"],
            recombination_rate=params["recombination_rate"],
            population_size=params["population_size"],
            random_seed=seed,
        )

        mts = msprime.sim_mutations(
            ts,
            rate=params["mutation_rate"],
            random_seed=seed,
        )

        return self._compute_stats(mts, params)

    def _run_demographic(self, params, msprime):
        seed = params.get("random_seed")
        events = params.get("demographic_events", [])

        demography = msprime.Demography()
        demography.add_population(
            name="pop0",
            initial_size=params["population_size"],
        )

        for event in events:
            event_type = event.get("type", "size_change")
            time = event.get("time", 100)
            if event_type == "size_change":
                demography.add_population_parameters_change(
                    time=time,
                    population="pop0",
                    initial_size=event.get("size", params["population_size"]),
                )
            elif event_type == "bottleneck":
                demography.add_population_parameters_change(
                    time=time,
                    population="pop0",
                    initial_size=event.get("size", 100),
                )
                # Recovery
                recovery_time = event.get("recovery_time", time + 50)
                demography.add_population_parameters_change(
                    time=recovery_time,
                    population="pop0",
                    initial_size=params["population_size"],
                )

        ts = msprime.sim_ancestry(
            samples=params["n_samples"],
            sequence_length=params["sequence_length"],
            recombination_rate=params["recombination_rate"],
            demography=demography,
            random_seed=seed,
        )

        mts = msprime.sim_mutations(
            ts,
            rate=params["mutation_rate"],
            random_seed=seed,
        )

        result = self._compute_stats(mts, params)

        # Add population size history
        pop_sizes = [{"time": 0, "size": params["population_size"]}]
        for event in events:
            pop_sizes.append({
                "time": event.get("time", 100),
                "size": event.get("size", params["population_size"]),
            })
        result["population_sizes"] = pop_sizes

        return result

    def _run_sweep(self, params, msprime):
        seed = params.get("random_seed")
        sel_coeff = params.get("selection_coefficient", 0.01)
        sweep_pos = params.get("sweep_position", params["sequence_length"] / 2)

        # Simulate with a selective sweep using the built-in model
        sweep_model = msprime.SweepGenicSelection(
            position=int(sweep_pos),
            start_frequency=1.0 / (2 * params["population_size"]),
            end_frequency=1.0 - 1.0 / (2 * params["population_size"]),
            s=sel_coeff,
            dt=1e-6,
        )

        ts = msprime.sim_ancestry(
            samples=params["n_samples"],
            sequence_length=params["sequence_length"],
            recombination_rate=params["recombination_rate"],
            population_size=params["population_size"],
            model=[sweep_model, msprime.StandardCoalescent()],
            random_seed=seed,
        )

        mts = msprime.sim_mutations(
            ts,
            rate=params["mutation_rate"],
            random_seed=seed,
        )

        result = self._compute_stats(mts, params)
        result["selection_coefficient"] = sel_coeff
        result["sweep_position"] = sweep_pos
        return result

    def _run_recombination(self, params, msprime):
        seed = params.get("random_seed")

        # Use a recombination rate map with hotspots
        positions = [0, params["sequence_length"] // 3, 2 * params["sequence_length"] // 3, params["sequence_length"]]
        rates = [params["recombination_rate"], params["recombination_rate"] * 10, params["recombination_rate"]]

        rate_map = msprime.RateMap(position=positions, rate=rates)

        ts = msprime.sim_ancestry(
            samples=params["n_samples"],
            sequence_length=params["sequence_length"],
            recombination_rate=rate_map,
            population_size=params["population_size"],
            random_seed=seed,
        )

        mts = msprime.sim_mutations(
            ts,
            rate=params["mutation_rate"],
            random_seed=seed,
        )

        result = self._compute_stats(mts, params)
        result["recombination_hotspots"] = [
            {"start": positions[1], "end": positions[2], "rate_multiplier": 10},
        ]
        return result

    def _compute_stats(self, mts, params):
        """Compute population genetics summary statistics."""
        n_windows = params["n_windows"]

        # Basic counts
        n_trees = mts.num_trees
        n_mutations = mts.num_mutations
        seq_len = int(mts.sequence_length)

        # Site frequency spectrum (allele frequencies)
        afs = mts.allele_frequency_spectrum(polarised=True, span_normalise=False)
        # Skip first (monomorphic ancestral) and last (monomorphic derived) entries
        sfs = afs[1:-1].tolist() if len(afs) > 2 else afs.tolist()
        sfs_bins = list(range(1, len(sfs) + 1))

        # Mean TMRCA
        total_tmrca = 0.0
        count = 0
        for tree in mts.trees():
            total_tmrca += tree.total_branch_length
            count += 1
        mean_tmrca = total_tmrca / count if count > 0 else 0.0

        # Windowed diversity (pi)
        windows = np.linspace(0, seq_len, n_windows + 1).astype(int).tolist()
        diversity = mts.diversity(windows=windows)
        diversity_values = diversity.tolist() if hasattr(diversity, "tolist") else [float(diversity)]
        window_centers = [(windows[i] + windows[i + 1]) / 2 for i in range(len(windows) - 1)]

        # Windowed Tajima's D
        tajimas_d = mts.Tajimas_D(windows=windows)
        tajimas_d_values = tajimas_d.tolist() if hasattr(tajimas_d, "tolist") else [float(tajimas_d)]

        return {
            "tool": "msprime",
            "simulation_type": params["simulation_type"],
            "n_trees": n_trees,
            "n_mutations": n_mutations,
            "sequence_length": seq_len,
            "mean_tmrca": mean_tmrca,
            "allele_frequencies": {
                "bins": sfs_bins,
                "counts": sfs,
            },
            "windowed_diversity": {
                "positions": window_centers,
                "pi": diversity_values,
            },
            "windowed_tajimas_d": {
                "positions": window_centers,
                "D": tajimas_d_values,
            },
            "n_samples": params["n_samples"],
            "population_size": params["population_size"],
        }

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "coalescent",
            "n_samples": 50,
            "sequence_length": 100_000,
            "recombination_rate": 1e-8,
            "mutation_rate": 1e-8,
            "population_size": 10_000,
            "random_seed": 42,
            "n_windows": 20,
        }


@celery_app.task(name="tools.msprime_tool.run_msprime", bind=True)
def run_msprime(self, params: dict, project: str = "_default",
                label: str | None = None) -> dict:
    tool = MsprimeTool()

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting msprime simulation"})

    try:
        result = tool.run(params)
    except Exception as e:
        self.update_state(state="FAILURE", meta={"message": str(e)})
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})

    save_result(self.request.id, "msprime", result, project, label)

    return result
