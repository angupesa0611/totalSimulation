from typing import Any
import numpy as np
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result


class SimuPOPTool(SimulationTool):
    """simuPOP — forward-time population genetics with complex mating and migration.

    Provides Wright-Fisher random mating, island-model migration, and selection+drift
    simulations with allele frequency tracking over generations.
    """

    name = "simuPOP"
    key = "simupop"
    layer = "evolution"

    SIMULATION_TYPES = {"random_mating", "migration", "selection_drift"}

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type", "random_mating")
        if sim_type not in self.SIMULATION_TYPES:
            raise ValueError(f"Unknown simulation_type: {sim_type}")
        params.setdefault("simulation_type", sim_type)
        params.setdefault("population_size", 1000)
        params.setdefault("n_generations", 200)
        params.setdefault("n_loci", 1)
        params.setdefault("initial_freq", 0.5)

        if sim_type == "migration":
            params.setdefault("n_populations", 3)
            params.setdefault("migration_rate", 0.01)

        if sim_type == "selection_drift":
            params.setdefault("fitness", {"AA": 1.0, "Aa": 1.0, "aa": 0.9})

        if params["population_size"] < 10 or params["population_size"] > 100_000:
            raise ValueError("population_size must be between 10 and 100,000")
        if params["n_generations"] < 1 or params["n_generations"] > 10_000:
            raise ValueError("n_generations must be between 1 and 10,000")

        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        import simuPOP as sim

        params = self.validate_params(params)
        sim_type = params["simulation_type"]

        if sim_type == "random_mating":
            return self._run_random_mating(params, sim)
        elif sim_type == "migration":
            return self._run_migration(params, sim)
        elif sim_type == "selection_drift":
            return self._run_selection_drift(params, sim)

    def _run_random_mating(self, params, sim):
        """Wright-Fisher random mating with allele frequency tracking."""
        pop_size = params["population_size"]
        n_gens = params["n_generations"]
        n_loci = params["n_loci"]
        init_freq = params["initial_freq"]

        pop = sim.Population(size=pop_size, loci=n_loci)
        sim.initGenotype(pop, freq=[1 - init_freq, init_freq])

        # Track allele frequencies over time
        generations = []
        frequencies = []

        def record_freq(pop):
            stat = sim.Stat(alleleFreq=list(range(n_loci)))
            stat.apply(pop)
            freq = pop.dvars().alleleFreq[0].get(1, 0.0)
            generations.append(pop.dvars().gen)
            frequencies.append(float(freq))
            return True

        pop.evolve(
            initOps=[sim.InitSex()],
            preOps=[sim.PyOperator(func=record_freq)],
            matingScheme=sim.RandomMating(),
            gen=n_gens,
        )

        # Final allele frequency spectrum (across loci if n_loci > 1)
        sim.Stat(alleleFreq=list(range(n_loci))).apply(pop)
        final_freqs = [pop.dvars().alleleFreq[i].get(1, 0.0) for i in range(n_loci)]
        sfs_bins, sfs_counts = self._compute_sfs(final_freqs)

        return {
            "tool": "simupop",
            "simulation_type": "random_mating",
            "allele_frequencies": {"bins": sfs_bins, "counts": sfs_counts},
            "allele_trajectory": {"generations": generations, "frequencies": frequencies},
            "n_populations": 1,
            "population_size": pop_size,
            "n_generations": n_gens,
            "n_loci": n_loci,
            "initial_freq": init_freq,
            "windowed_diversity": {"positions": [], "pi": []},
            "windowed_tajimas_d": {"positions": [], "D": []},
        }

    def _run_migration(self, params, sim):
        """Island model with migration between multiple populations."""
        pop_size = params["population_size"]
        n_gens = params["n_generations"]
        n_loci = params["n_loci"]
        init_freq = params["initial_freq"]
        n_pops = params["n_populations"]
        mig_rate = params["migration_rate"]

        pop = sim.Population(size=[pop_size] * n_pops, loci=n_loci)

        # Different initial frequencies per population
        rng = np.random.default_rng(42)
        for i in range(n_pops):
            freq = max(0.01, min(0.99, init_freq + rng.normal(0, 0.1)))
            sim.initGenotype(pop, freq=[1 - freq, freq], subPops=[i])

        # Migration matrix (island model: equal migration between all pops)
        mig_matrix = []
        for i in range(n_pops):
            row = []
            for j in range(n_pops):
                if i == j:
                    row.append(0.0)
                else:
                    row.append(mig_rate / (n_pops - 1))
            mig_matrix.append(row)

        # Track per-population allele frequencies
        generations = []
        pop_frequencies = {i: [] for i in range(n_pops)}

        def record_freq(pop):
            stat = sim.Stat(alleleFreq=list(range(n_loci)), subPops=list(range(n_pops)))
            stat.apply(pop)
            gen = pop.dvars().gen
            generations.append(gen)
            for i in range(n_pops):
                freq = pop.dvars(i).alleleFreq[0].get(1, 0.0)
                pop_frequencies[i].append(float(freq))
            return True

        pop.evolve(
            initOps=[sim.InitSex()],
            preOps=[
                sim.Migrator(rate=mig_matrix),
                sim.PyOperator(func=record_freq),
            ],
            matingScheme=sim.RandomMating(),
            gen=n_gens,
        )

        # Overall trajectory (mean across populations)
        mean_freq = [
            float(np.mean([pop_frequencies[p][g] for p in range(n_pops)]))
            for g in range(len(generations))
        ]

        return {
            "tool": "simupop",
            "simulation_type": "migration",
            "allele_frequencies": {"bins": [], "counts": []},
            "allele_trajectory": {"generations": generations, "frequencies": mean_freq},
            "population_trajectories": {
                str(i): pop_frequencies[i] for i in range(n_pops)
            },
            "n_populations": n_pops,
            "population_size": pop_size,
            "n_generations": n_gens,
            "n_loci": n_loci,
            "migration_rate": mig_rate,
            "windowed_diversity": {"positions": [], "pi": []},
            "windowed_tajimas_d": {"positions": [], "D": []},
        }

    def _run_selection_drift(self, params, sim):
        """Selection + drift with configurable genotype fitness values."""
        pop_size = params["population_size"]
        n_gens = params["n_generations"]
        n_loci = params["n_loci"]
        init_freq = params["initial_freq"]
        fitness = params["fitness"]

        # Parse fitness values
        fit_AA = fitness.get("AA", 1.0)
        fit_Aa = fitness.get("Aa", 1.0)
        fit_aa = fitness.get("aa", 0.9)

        pop = sim.Population(size=pop_size, loci=n_loci)
        sim.initGenotype(pop, freq=[1 - init_freq, init_freq])

        generations = []
        frequencies = []

        def record_freq(pop):
            stat = sim.Stat(alleleFreq=list(range(n_loci)))
            stat.apply(pop)
            freq = pop.dvars().alleleFreq[0].get(1, 0.0)
            generations.append(pop.dvars().gen)
            frequencies.append(float(freq))
            return True

        pop.evolve(
            initOps=[sim.InitSex()],
            preOps=[
                sim.MapSelector(loci=0, fitness={
                    (0, 0): fit_AA,
                    (0, 1): fit_Aa,
                    (1, 0): fit_Aa,
                    (1, 1): fit_aa,
                }),
                sim.PyOperator(func=record_freq),
            ],
            matingScheme=sim.RandomMating(),
            gen=n_gens,
        )

        return {
            "tool": "simupop",
            "simulation_type": "selection_drift",
            "allele_frequencies": {"bins": [], "counts": []},
            "allele_trajectory": {"generations": generations, "frequencies": frequencies},
            "n_populations": 1,
            "population_size": pop_size,
            "n_generations": n_gens,
            "n_loci": n_loci,
            "fitness": {"AA": fit_AA, "Aa": fit_Aa, "aa": fit_aa},
            "windowed_diversity": {"positions": [], "pi": []},
            "windowed_tajimas_d": {"positions": [], "D": []},
        }

    def _compute_sfs(self, freqs):
        """Compute a simple site frequency spectrum from a list of allele frequencies."""
        if not freqs:
            return [], []
        n_bins = 10
        counts, edges = np.histogram(freqs, bins=n_bins, range=(0, 1))
        bin_centers = [(edges[i] + edges[i + 1]) / 2 for i in range(len(edges) - 1)]
        return [round(b, 2) for b in bin_centers], counts.tolist()

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "random_mating",
            "population_size": 1000,
            "n_generations": 200,
            "n_loci": 1,
            "initial_freq": 0.5,
        }


@celery_app.task(name="tools.simupop_tool.run_simupop", bind=True)
def run_simupop(self, params: dict, project: str = "_default",
                label: str | None = None) -> dict:
    tool = SimuPOPTool()

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting simuPOP simulation"})

    try:
        result = tool.run(params)
    except Exception as e:
        self.update_state(state="FAILURE", meta={"message": str(e)})
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})

    save_result(self.request.id, "simupop", result, project, label)

    return result
