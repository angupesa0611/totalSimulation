from typing import Any
import numpy as np
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result


class TelluriumTool(SimulationTool):
    name = "Tellurium"
    key = "tellurium"
    layer = "systems-biology"

    SIMULATION_TYPES = {
        "antimony_timecourse", "sbml_timecourse", "steady_state",
        "parameter_scan", "metabolic_control",
    }

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type", "antimony_timecourse")
        if sim_type not in self.SIMULATION_TYPES:
            raise ValueError(f"Unknown simulation_type: {sim_type}")
        params.setdefault("simulation_type", sim_type)

        if sim_type in ("antimony_timecourse", "steady_state", "parameter_scan", "metabolic_control"):
            if "antimony_model" not in params or not params["antimony_model"]:
                raise ValueError("antimony_model string is required")
        elif sim_type == "sbml_timecourse":
            if "sbml_model" not in params or not params["sbml_model"]:
                raise ValueError("sbml_model string is required")

        params.setdefault("start_time", 0.0)
        params.setdefault("end_time", 100.0)
        params.setdefault("n_points", 200)
        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        import tellurium as te

        params = self.validate_params(params)
        sim_type = params["simulation_type"]

        if sim_type == "antimony_timecourse":
            return self._run_antimony(params, te)
        elif sim_type == "sbml_timecourse":
            return self._run_sbml(params, te)
        elif sim_type == "steady_state":
            return self._run_steady_state(params, te)
        elif sim_type == "parameter_scan":
            return self._run_parameter_scan(params, te)
        elif sim_type == "metabolic_control":
            return self._run_mca(params, te)

    def _run_antimony(self, params, te):
        r = te.loada(params["antimony_model"])
        result = r.simulate(
            params["start_time"],
            params["end_time"],
            params["n_points"],
        )

        times = result[:, 0].tolist()
        species = {}
        col_names = result.colnames
        for i, name in enumerate(col_names):
            if i == 0:
                continue  # skip time column
            clean_name = name.replace("[", "").replace("]", "")
            species[clean_name] = result[:, i].tolist()

        # Always export SBML for pipeline coupling
        sbml_export = r.getCurrentSBML()

        return {
            "tool": "tellurium",
            "simulation_type": "antimony_timecourse",
            "times": times,
            "species": species,
            "sbml_export": sbml_export,
            "n_species": len(species),
        }

    def _run_sbml(self, params, te):
        r = te.loadSBMLModel(params["sbml_model"])
        result = r.simulate(
            params["start_time"],
            params["end_time"],
            params["n_points"],
        )

        times = result[:, 0].tolist()
        species = {}
        col_names = result.colnames
        for i, name in enumerate(col_names):
            if i == 0:
                continue
            clean_name = name.replace("[", "").replace("]", "")
            species[clean_name] = result[:, i].tolist()

        sbml_export = r.getCurrentSBML()

        return {
            "tool": "tellurium",
            "simulation_type": "sbml_timecourse",
            "times": times,
            "species": species,
            "sbml_export": sbml_export,
            "n_species": len(species),
        }

    def _run_steady_state(self, params, te):
        r = te.loada(params["antimony_model"])
        r.steadyState()

        species_ids = r.getFloatingSpeciesIds()
        steady_state_values = {}
        concentrations = r.getFloatingSpeciesConcentrations()
        for sid, conc in zip(species_ids, concentrations):
            steady_state_values[sid] = float(conc)

        sbml_export = r.getCurrentSBML()

        return {
            "tool": "tellurium",
            "simulation_type": "steady_state",
            "steady_state_values": steady_state_values,
            "sbml_export": sbml_export,
        }

    def _run_parameter_scan(self, params, te):
        r = te.loada(params["antimony_model"])

        scan_param = params.get("scan_parameter")
        scan_range = params.get("scan_range", [0.1, 10.0])
        scan_points = params.get("scan_points", 20)

        if not scan_param:
            raise ValueError("scan_parameter is required for parameter_scan")

        scan_values = np.linspace(scan_range[0], scan_range[1], scan_points).tolist()
        scan_results = []

        for val in scan_values:
            r.reset()
            r.setValue(scan_param, val)
            r.steadyState()

            species_ids = r.getFloatingSpeciesIds()
            concentrations = r.getFloatingSpeciesConcentrations()
            point = {}
            for sid, conc in zip(species_ids, concentrations):
                point[sid] = float(conc)
            scan_results.append(point)

        sbml_export = r.getCurrentSBML()

        return {
            "tool": "tellurium",
            "simulation_type": "parameter_scan",
            "scan_parameter": scan_param,
            "scan_values": scan_values,
            "scan_results": scan_results,
            "sbml_export": sbml_export,
        }

    def _run_mca(self, params, te):
        r = te.loada(params["antimony_model"])
        r.steadyState()

        # Flux control coefficients
        fcc_ids = r.getFluxControlCoefficientIds()
        fcc_matrix = r.getScaledFluxControlCoefficientMatrix()
        flux_control = {}
        if fcc_matrix is not None:
            rows = fcc_matrix.rownames if hasattr(fcc_matrix, "rownames") else []
            cols = fcc_matrix.colnames if hasattr(fcc_matrix, "colnames") else []
            data = np.array(fcc_matrix).tolist() if hasattr(fcc_matrix, "__array__") else []
            flux_control = {"rows": list(rows), "cols": list(cols), "data": data}

        # Concentration control coefficients
        ccc_matrix = r.getScaledConcentrationControlCoefficientMatrix()
        conc_control = {}
        if ccc_matrix is not None:
            rows = ccc_matrix.rownames if hasattr(ccc_matrix, "rownames") else []
            cols = ccc_matrix.colnames if hasattr(ccc_matrix, "colnames") else []
            data = np.array(ccc_matrix).tolist() if hasattr(ccc_matrix, "__array__") else []
            conc_control = {"rows": list(rows), "cols": list(cols), "data": data}

        sbml_export = r.getCurrentSBML()

        return {
            "tool": "tellurium",
            "simulation_type": "metabolic_control",
            "flux_control_coefficients": flux_control,
            "concentration_control_coefficients": conc_control,
            "sbml_export": sbml_export,
        }

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "antimony_timecourse",
            "antimony_model": (
                "model pathway\n"
                "  S1 -> S2; k1*S1;\n"
                "  S2 -> S3; k2*S2;\n"
                "  S3 -> ; k3*S3;\n"
                "  S1 = 10; S2 = 0; S3 = 0;\n"
                "  k1 = 0.1; k2 = 0.05; k3 = 0.02;\n"
                "end"
            ),
            "start_time": 0.0,
            "end_time": 200.0,
            "n_points": 200,
        }


@celery_app.task(name="tools.tellurium_tool.run_tellurium", bind=True)
def run_tellurium(self, params: dict, project: str = "_default",
                  label: str | None = None) -> dict:
    tool = TelluriumTool()

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting Tellurium simulation"})

    try:
        result = tool.run(params)
    except Exception as e:
        self.update_state(state="FAILURE", meta={"message": str(e)})
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})

    save_result(self.request.id, "tellurium", result, project, label)

    return result
