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


@app.task(name="tools.psi4_tool.run_psi4", bind=True)
def run_psi4(self, params: dict, project: str = "_default",
             label: str | None = None) -> dict:
    import psi4

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Setting up Psi4 calculation"})

    geometry = params.get("geometry", "")
    if not geometry:
        raise ValueError("geometry is required (Psi4 geometry string)")

    method = params.get("method", "hf").lower()
    basis = params.get("basis", "cc-pvdz")
    charge = params.get("charge", 0)
    multiplicity = params.get("multiplicity", 1)

    # Set memory and threads
    psi4.set_memory(params.get("memory", "2 GB"))
    psi4.core.set_num_threads(params.get("threads", 2))
    psi4.core.set_output_file("/tmp/psi4_output.dat", False)

    # Build molecule
    mol_str = f"{charge} {multiplicity}\n{geometry}"
    mol = psi4.geometry(mol_str)

    self.update_state(state="PROGRESS", meta={
        "progress": 0.1,
        "message": f"Running {method.upper()}/{basis} calculation"
    })

    # Check if SAPT calculation
    is_sapt = method.startswith("sapt")

    if is_sapt:
        # SAPT requires a dimer (two fragments separated by --)
        energy, wfn = psi4.energy(f"{method}/{basis}", molecule=mol, return_wfn=True)

        self.update_state(state="PROGRESS", meta={"progress": 0.7, "message": "Extracting SAPT components"})

        # Extract SAPT components
        sapt_data = {
            "total_energy": float(energy),
            "electrostatics": float(psi4.variable("SAPT ELST ENERGY")),
            "exchange": float(psi4.variable("SAPT EXCH ENERGY")),
            "induction": float(psi4.variable("SAPT IND ENERGY")),
            "dispersion": float(psi4.variable("SAPT DISP ENERGY")),
            "interaction_energy": float(psi4.variable("SAPT TOTAL ENERGY")),
        }

        result = {
            "tool": "psi4",
            "method": method,
            "basis": basis,
            "is_sapt": True,
            "sapt": sapt_data,
            "total_energy": float(energy),
            "n_atoms": mol.natom(),
        }
    else:
        # Standard energy calculation
        energy, wfn = psi4.energy(f"{method}/{basis}", molecule=mol, return_wfn=True)

        self.update_state(state="PROGRESS", meta={"progress": 0.7, "message": "Extracting properties"})

        # Orbital energies
        orbital_energies = []
        try:
            eps = wfn.epsilon_a()
            orbital_energies = [float(eps.get(i)) for i in range(eps.dim())]
        except Exception:
            pass

        # Dipole moment
        dipole = []
        try:
            psi4.oeprop(wfn, "DIPOLE")
            dx = float(psi4.variable("SCF DIPOLE X"))
            dy = float(psi4.variable("SCF DIPOLE Y"))
            dz = float(psi4.variable("SCF DIPOLE Z"))
            dipole = [dx, dy, dz]
        except Exception:
            pass

        result = {
            "tool": "psi4",
            "method": method,
            "basis": basis,
            "is_sapt": False,
            "total_energy": float(energy),
            "orbital_energies": orbital_energies,
            "dipole_moment": dipole,
            "n_atoms": mol.natom(),
            "charge": charge,
            "multiplicity": multiplicity,
        }

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    _save_result(self.request.id, "psi4", result, project, label)

    # Clean up
    psi4.core.clean()

    return result
