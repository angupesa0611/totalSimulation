"""Open Babel — universal chemical format converter and 3D optimizer.

Supports 110+ molecular formats via the Open Babel library (pybel wrapper).
Simulation types:
  - convert: Convert between molecular file formats (SMILES, SDF, MOL2, PDB, XYZ, etc.)
  - optimize_3d: Generate 3D coordinates and optimize with a force field (MMFF94, UFF, GAFF)
  - protonate: Add hydrogens at a specified pH
"""

import json
import os
from datetime import datetime, timezone

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


SUPPORTED_FORMATS = [
    "smi", "sdf", "mol", "mol2", "pdb", "xyz", "cml", "inchi", "inchikey",
    "can", "cdx", "cif", "gjf", "gro", "lmpdat", "mcif", "mmcif",
]


def _run_convert(params: dict) -> dict:
    """Convert molecular data between formats."""
    from openbabel import pybel

    source_format = params.get("source_format", "smi")
    target_format = params.get("target_format", "sdf")
    source_data = params.get("source_data", "")

    if not source_data:
        raise ValueError("source_data is required")

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


def _run_optimize_3d(params: dict) -> dict:
    """Generate 3D coordinates and optimize geometry with a force field."""
    from openbabel import pybel

    source_format = params.get("source_format", "smi")
    source_data = params.get("source_data", "")
    force_field = params.get("force_field", "mmff94")
    steps = params.get("steps", 500)

    if not source_data:
        raise ValueError("source_data is required")

    mol = pybel.readstring(source_format, source_data)
    mol.addh()
    mol.make3D()

    ff = pybel._forcefields[force_field.lower()]
    ff.Setup(mol.OBMol)
    ff.ConjugateGradients(steps)
    ff.GetCoordinates(mol.OBMol)
    final_energy = ff.Energy()

    # Extract atom coordinates
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


def _run_protonate(params: dict) -> dict:
    """Add hydrogens at a specified pH."""
    from openbabel import pybel

    source_format = params.get("source_format", "smi")
    source_data = params.get("source_data", "")
    ph = params.get("ph", 7.4)

    if not source_data:
        raise ValueError("source_data is required")

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


@app.task(name="tools.openbabel_tool.run_openbabel", bind=True, soft_time_limit=120)
def run_openbabel(self, params: dict, project: str = "_default",
                  label: str | None = None) -> dict:
    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting Open Babel"})

    sim_type = params.get("simulation_type", "convert")

    runners = {
        "convert": _run_convert,
        "optimize_3d": _run_optimize_3d,
        "protonate": _run_protonate,
    }

    if sim_type not in runners:
        raise ValueError(f"Unknown simulation_type: {sim_type}. Must be one of {list(runners.keys())}")

    self.update_state(state="PROGRESS", meta={"progress": 0.2, "message": f"Running {sim_type}"})

    result = runners[sim_type](params)

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    _save_result(self.request.id, "openbabel", result, project, label)

    return result
