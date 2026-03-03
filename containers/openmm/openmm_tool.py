import io
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


def _get_platform():
    """Get best available OpenMM platform."""
    import openmm
    preferred = os.getenv("OPENMM_PLATFORM", "CUDA")
    try:
        return openmm.Platform.getPlatformByName(preferred)
    except Exception:
        try:
            return openmm.Platform.getPlatformByName("OpenCL")
        except Exception:
            return openmm.Platform.getPlatformByName("CPU")


@app.task(name="tools.openmm_tool.run_openmm", bind=True)
def run_openmm(self, params: dict, project: str = "_default",
               label: str | None = None) -> dict:
    import openmm
    import openmm.app as app_mm
    import openmm.unit as unit

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Setting up OpenMM simulation"})

    pdb_content = params.get("pdb_content", "")
    if not pdb_content:
        raise ValueError("pdb_content is required")

    forcefield_files = params.get("forcefield", ["amber14-all.xml", "amber14/tip3pfb.xml"])
    integrator_type = params.get("integrator", "langevin")
    temperature = params.get("temperature", 300.0)
    friction = params.get("friction", 1.0)
    dt = params.get("dt", 0.002)
    steps = params.get("steps", 10000)
    report_interval = params.get("report_interval", 100)
    minimize = params.get("minimize", True)

    # Parse PDB
    pdb_io = io.StringIO(pdb_content)
    pdb = app_mm.PDBFile(pdb_io)

    # Force field
    forcefield = app_mm.ForceField(*forcefield_files)
    system = forcefield.createSystem(
        pdb.topology,
        nonbondedMethod=app_mm.NoCutoff,
        constraints=app_mm.HBonds,
    )

    # Integrator
    if integrator_type == "langevin":
        integrator = openmm.LangevinMiddleIntegrator(
            temperature * unit.kelvin,
            friction / unit.picosecond,
            dt * unit.picoseconds,
        )
    elif integrator_type == "verlet":
        integrator = openmm.VerletIntegrator(dt * unit.picoseconds)
    elif integrator_type == "brownian":
        integrator = openmm.BrownianIntegrator(
            temperature * unit.kelvin,
            friction / unit.picosecond,
            dt * unit.picoseconds,
        )
    else:
        raise ValueError(f"Unknown integrator: {integrator_type}")

    platform = _get_platform()
    simulation = app_mm.Simulation(pdb.topology, system, integrator, platform)
    simulation.context.setPositions(pdb.positions)

    self.update_state(state="PROGRESS", meta={"progress": 0.1, "message": f"Using platform: {platform.getName()}"})

    # Minimize
    if minimize:
        self.update_state(state="PROGRESS", meta={"progress": 0.15, "message": "Energy minimization"})
        simulation.minimizeEnergy()

    # Set velocities
    simulation.context.setVelocitiesToTemperature(temperature * unit.kelvin)

    # Run simulation collecting frames
    n_frames = steps // report_interval
    energies = []
    pdb_frames = []

    self.update_state(state="PROGRESS", meta={"progress": 0.2, "message": "Running MD simulation"})

    for i in range(n_frames):
        simulation.step(report_interval)
        state = simulation.context.getState(getEnergy=True, getPositions=True)

        pe = state.getPotentialEnergy().value_in_unit(unit.kilojoules_per_mole)
        ke = state.getKineticEnergy().value_in_unit(unit.kilojoules_per_mole)
        energies.append({"step": (i + 1) * report_interval, "potential": pe, "kinetic": ke, "total": pe + ke})

        # Get positions as list for JSON
        positions = state.getPositions(asNumpy=True).value_in_unit(unit.angstrom)
        pdb_frames.append(positions.tolist())

        progress = 0.2 + 0.7 * (i + 1) / n_frames
        self.update_state(state="PROGRESS", meta={
            "progress": progress,
            "message": f"Step {(i+1)*report_interval}/{steps}",
        })

    result = {
        "tool": "openmm",
        "platform": platform.getName(),
        "n_frames": n_frames,
        "energies": energies,
        "frames": pdb_frames,
        "n_atoms": simulation.topology.getNumAtoms(),
        "params": {
            "integrator": integrator_type,
            "temperature": temperature,
            "steps": steps,
            "dt": dt,
        },
    }

    self.update_state(state="PROGRESS", meta={"progress": 0.95, "message": "Saving results"})
    _save_result(self.request.id, "openmm", result, project, label)

    return result
