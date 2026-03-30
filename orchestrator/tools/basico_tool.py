from typing import Any
import numpy as np
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result


class BasicoTool(SimulationTool):
    name = "BasiCO"
    key = "basico"
    layer = "systems-biology"

    SIMULATION_TYPES = {
        "ode_timecourse", "stochastic_timecourse", "steady_state",
        "parameter_estimation", "sensitivity",
    }
    METHODS = {"deterministic", "stochastic", "hybrid"}

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type", "ode_timecourse")
        if sim_type not in self.SIMULATION_TYPES:
            raise ValueError(f"Unknown simulation_type: {sim_type}")
        params.setdefault("simulation_type", sim_type)

        model_source = params.get("model_source", "reactions")
        if model_source not in ("reactions", "sbml"):
            raise ValueError(f"Unknown model_source: {model_source}")

        if model_source == "reactions":
            if "reactions" not in params or not params["reactions"]:
                raise ValueError("At least one reaction is required")
        elif model_source == "sbml":
            if "sbml_string" not in params or not params["sbml_string"]:
                raise ValueError("sbml_string is required for SBML model source")

        params.setdefault("duration", 100.0)
        params.setdefault("n_steps", 100)
        params.setdefault("method", "deterministic")
        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        import basico

        params = self.validate_params(params)
        sim_type = params["simulation_type"]
        model_source = params.get("model_source", "reactions")

        # Load or build model
        if model_source == "sbml":
            basico.load_model_from_string(params["sbml_string"])
        else:
            basico.new_model(name="simulation")
            for rxn in params.get("reactions", []):
                basico.add_reaction(
                    name=rxn["name"],
                    scheme=rxn["scheme"],
                )
                # Set kinetic parameters if provided
                if "rate_law" in rxn:
                    basico.set_reaction(name=rxn["name"], function=rxn["rate_law"])

            # Set species initial concentrations
            for sp in params.get("species", []):
                basico.set_species(
                    name=sp["name"],
                    initial_concentration=sp.get("initial_concentration", 1.0),
                )

            # Set global parameters
            for par in params.get("parameters", []):
                basico.set_parameters(
                    name=par["name"],
                    initial_value=par.get("value", 1.0),
                )

        if sim_type == "ode_timecourse":
            return self._run_timecourse(params, basico, deterministic=True)
        elif sim_type == "stochastic_timecourse":
            return self._run_timecourse(params, basico, deterministic=False)
        elif sim_type == "steady_state":
            return self._run_steady_state(params, basico)
        elif sim_type == "parameter_estimation":
            return self._run_parameter_estimation(params, basico)
        elif sim_type == "sensitivity":
            return self._run_sensitivity(params, basico)

    def _run_timecourse(self, params, basico, deterministic=True):
        duration = params["duration"]
        n_steps = params["n_steps"]
        method = "deterministic" if deterministic else "stochastic"

        tc = basico.run_time_course(
            duration=duration,
            intervals=n_steps,
            method=method,
        )

        times = tc.index.tolist()
        species = {}
        for col in tc.columns:
            species[col] = tc[col].tolist()

        return {
            "tool": "basico",
            "simulation_type": "ode_timecourse" if deterministic else "stochastic_timecourse",
            "times": times,
            "species": species,
            "duration": duration,
            "n_steps": n_steps,
            "method": method,
        }

    def _run_steady_state(self, params, basico):
        ss = basico.run_steadystate()

        species_values = basico.get_species()
        steady_state_values = {}
        if species_values is not None:
            for name in species_values.index:
                conc = species_values.loc[name, "concentration"]
                steady_state_values[name] = float(conc) if not isinstance(conc, str) else 0.0

        return {
            "tool": "basico",
            "simulation_type": "steady_state",
            "steady_state_values": steady_state_values,
            "converged": ss is not None,
        }

    def _run_parameter_estimation(self, params, basico):
        # Run a time course first, then use it as reference data for fitting
        duration = params["duration"]
        n_steps = params["n_steps"]

        tc = basico.run_time_course(duration=duration, intervals=n_steps)

        # Get parameter info
        param_info = basico.get_parameters()
        fitted_parameters = {}
        if param_info is not None:
            for name in param_info.index:
                fitted_parameters[name] = float(param_info.loc[name, "initial_value"])

        return {
            "tool": "basico",
            "simulation_type": "parameter_estimation",
            "fitted_parameters": fitted_parameters,
            "times": tc.index.tolist(),
            "species": {col: tc[col].tolist() for col in tc.columns},
        }

    def _run_sensitivity(self, params, basico):
        duration = params["duration"]
        n_steps = params["n_steps"]

        # Run baseline
        tc_base = basico.run_time_course(duration=duration, intervals=n_steps)

        # Compute finite-difference sensitivities for each parameter
        param_info = basico.get_parameters()
        sensitivities = {}

        if param_info is not None:
            for pname in param_info.index:
                orig_val = float(param_info.loc[pname, "initial_value"])
                if orig_val == 0:
                    continue
                delta = orig_val * 0.01  # 1% perturbation

                basico.set_parameters(name=pname, initial_value=orig_val + delta)
                tc_pert = basico.run_time_course(duration=duration, intervals=n_steps)
                basico.set_parameters(name=pname, initial_value=orig_val)

                sens_per_species = {}
                for col in tc_base.columns:
                    base_vals = tc_base[col].values
                    pert_vals = tc_pert[col].values
                    # Normalized sensitivity: (df/f) / (dp/p)
                    with np.errstate(divide="ignore", invalid="ignore"):
                        norm_sens = np.where(
                            np.abs(base_vals) > 1e-15,
                            ((pert_vals - base_vals) / base_vals) / (delta / orig_val),
                            0.0,
                        )
                    sens_per_species[col] = float(np.mean(np.abs(norm_sens)))

                sensitivities[pname] = sens_per_species

        return {
            "tool": "basico",
            "simulation_type": "sensitivity",
            "sensitivities": sensitivities,
            "times": tc_base.index.tolist(),
            "species": {col: tc_base[col].tolist() for col in tc_base.columns},
        }

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "ode_timecourse",
            "model_source": "reactions",
            "reactions": [
                {"name": "binding", "scheme": "S + E -> ES"},
                {"name": "unbinding", "scheme": "ES -> S + E"},
                {"name": "catalysis", "scheme": "ES -> P + E"},
            ],
            "species": [
                {"name": "S", "initial_concentration": 10.0},
                {"name": "E", "initial_concentration": 1.0},
                {"name": "ES", "initial_concentration": 0.0},
                {"name": "P", "initial_concentration": 0.0},
            ],
            "parameters": [
                {"name": "(binding).k1", "value": 0.1},
                {"name": "(unbinding).k1", "value": 0.01},
                {"name": "(catalysis).k1", "value": 0.05},
            ],
            "duration": 200.0,
            "n_steps": 200,
            "method": "deterministic",
        }


@celery_app.task(name="tools.basico_tool.run_basico", bind=True)
def run_basico(self, params: dict, project: str = "_default",
               label: str | None = None) -> dict:
    tool = BasicoTool()

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting BasiCO simulation"})

    try:
        result = tool.run(params)
    except Exception as e:
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})

    save_result(self.request.id, "basico", result, project, label)

    return result
