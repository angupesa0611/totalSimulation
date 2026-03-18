"""Open Babel — universal chemical format converter and 3D optimizer.

Supports 110+ molecular formats via the Open Babel library (pybel wrapper).
Simulation types:
  - convert: Convert between molecular file formats (SMILES, SDF, MOL2, PDB, XYZ, etc.)
  - optimize_3d: Generate 3D coordinates and optimize with a force field (MMFF94, UFF, GAFF)
  - protonate: Add hydrogens at a specified pH
"""

from typing import Any

from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result


SUPPORTED_FORMATS = [
    "smi", "sdf", "mol", "mol2", "pdb", "xyz", "cml", "inchi", "inchikey",
    "can", "cdx", "cif", "gjf", "gro", "lmpdat", "mcif", "mmcif",
]


class OpenBabelTool(SimulationTool):
    name = "Open Babel"
    key = "openbabel"
    layer = "cheminformatics"

    SIMULATION_TYPES = {"convert", "optimize_3d", "protonate"}

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type", "convert")
        if sim_type not in self.SIMULATION_TYPES:
            raise ValueError(f"Unknown simulation_type: {sim_type}. Supported: {self.SIMULATION_TYPES}")
        if not params.get("source_data"):
            raise ValueError("source_data is required")
        params.setdefault("simulation_type", sim_type)
        params.setdefault("source_format", "smi")
        params.setdefault("target_format", "sdf")
        params.setdefault("force_field", "mmff94")
        params.setdefault("steps", 500)
        params.setdefault("ph", 7.4)
        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        params = self.validate_params(params)
        sim_type = params["simulation_type"]

        runners = {
            "convert": self._run_convert,
            "optimize_3d": self._run_optimize_3d,
            "protonate": self._run_protonate,
        }

        return runners[sim_type](params)

    def _run_convert(self, params):
        from openbabel import pybel

        source_format = params.get("source_format", "smi")
        target_format = params.get("target_format", "sdf")
        source_data = params["source_data"]

        mol = pybel.readstring(source_format, source_data)
        output = mol.write(target_format)

        return {
            "tool": "openbabel",
            "simulation_type": "convert",
            "source_format": source_format,
            "target_format": target_format,
            "output_data": output.strip(),
            "formula": mol.formula,
            "molecular_weight": mol.molwt,
            "n_atoms": len(mol.atoms),
        }

    def _run_optimize_3d(self, params):
        from openbabel import pybel

        source_format = params.get("source_format", "smi")
        source_data = params["source_data"]
        force_field = params.get("force_field", "mmff94")
        steps = params.get("steps", 500)

        mol = pybel.readstring(source_format, source_data)
        mol.addh()
        mol.make3D()

        from openbabel import openbabel as ob
        ff = ob.OBForceField.FindForceField(force_field.lower())
        ff.Setup(mol.OBMol)
        ff.ConjugateGradients(steps)
        ff.GetCoordinates(mol.OBMol)
        final_energy = ff.Energy()

        coords = []
        elements = []
        for atom in mol.atoms:
            coords.append(list(atom.coords))
            elements.append(atom.type.split(".")[0] if "." in atom.type else atom.type)

        return {
            "tool": "openbabel",
            "simulation_type": "optimize_3d",
            "force_field": force_field,
            "steps": steps,
            "energy": float(final_energy),
            "formula": mol.formula,
            "molecular_weight": mol.molwt,
            "n_atoms": len(mol.atoms),
            "coordinates": coords,
            "elements": elements,
            "output_pdb": mol.write("pdb").strip(),
            "output_sdf": mol.write("sdf").strip(),
            "output_xyz": mol.write("xyz").strip(),
        }

    def _run_protonate(self, params):
        from openbabel import pybel

        source_format = params.get("source_format", "smi")
        source_data = params["source_data"]
        ph = params.get("ph", 7.4)

        mol = pybel.readstring(source_format, source_data)
        n_atoms_before = len(mol.atoms)

        mol.OBMol.AddHydrogens(False, True, ph)

        n_atoms_after = len(mol.atoms)

        return {
            "tool": "openbabel",
            "simulation_type": "protonate",
            "ph": ph,
            "formula_before": mol.formula,
            "n_atoms_before": n_atoms_before,
            "n_atoms_after": n_atoms_after,
            "hydrogens_added": n_atoms_after - n_atoms_before,
            "output_smi": mol.write("smi").strip(),
            "output_sdf": mol.write("sdf").strip(),
            "formula": mol.formula,
            "molecular_weight": mol.molwt,
        }

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "convert",
            "source_format": "smi",
            "target_format": "sdf",
            "source_data": "c1ccccc1",
        }


@celery_app.task(name="tools.openbabel_tool.run_openbabel", bind=True, soft_time_limit=120)
def run_openbabel(self, params: dict, project: str = "_default",
                  label: str | None = None) -> dict:
    tool = OpenBabelTool()

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting Open Babel"})

    try:
        sim_type = params.get("simulation_type", "convert")
        self.update_state(state="PROGRESS", meta={"progress": 0.2, "message": f"Running {sim_type}"})
        result = tool.run(params)
    except Exception as e:
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    save_result(self.request.id, "openbabel", result, project, label)

    return result
