import json
import os
import subprocess
import tempfile
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


@app.task(name="tools.namd_tool.run_namd", bind=True)
def run_namd(self, params: dict, project: str = "_default",
             label: str | None = None) -> dict:
    import MDAnalysis as mda

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Setting up NAMD simulation"})

    pdb_content = params.get("pdb_content", "")
    psf_content = params.get("psf_content", "")
    namd_conf = params.get("namd_conf", "")
    parameter_files = params.get("parameter_files", {})

    if not pdb_content:
        raise ValueError("pdb_content is required")
    if not psf_content:
        raise ValueError("psf_content is required")
    if not namd_conf:
        raise ValueError("namd_conf is required (NAMD configuration file content)")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write input files
        pdb_path = os.path.join(tmpdir, "input.pdb")
        psf_path = os.path.join(tmpdir, "input.psf")
        conf_path = os.path.join(tmpdir, "run.namd")
        dcd_path = os.path.join(tmpdir, "output.dcd")

        with open(pdb_path, "w") as f:
            f.write(pdb_content)
        with open(psf_path, "w") as f:
            f.write(psf_content)

        # Write parameter files
        for filename, content in parameter_files.items():
            param_path = os.path.join(tmpdir, filename)
            with open(param_path, "w") as f:
                f.write(content)

        # Write NAMD config
        with open(conf_path, "w") as f:
            f.write(namd_conf)

        # Run NAMD
        self.update_state(state="PROGRESS", meta={"progress": 0.15, "message": "Running NAMD simulation"})

        # Try namd3 first, then namd2
        namd_cmd = "namd3"
        result = subprocess.run(
            [namd_cmd, "+p1", conf_path],
            capture_output=True, text=True, cwd=tmpdir,
        )

        if result.returncode != 0:
            # Try namd2
            namd_cmd = "namd2"
            result = subprocess.run(
                [namd_cmd, "+p1", conf_path],
                capture_output=True, text=True, cwd=tmpdir,
            )
            if result.returncode != 0:
                raise RuntimeError(f"NAMD failed: {result.stderr}")

        self.update_state(state="PROGRESS", meta={"progress": 0.7, "message": "Converting trajectory to JSON"})

        # Find DCD output file
        dcd_files = [f for f in os.listdir(tmpdir) if f.endswith(".dcd")]
        if not dcd_files:
            raise RuntimeError("No DCD trajectory output found")

        dcd_path = os.path.join(tmpdir, dcd_files[0])

        # Convert DCD to JSON using MDAnalysis
        u = mda.Universe(psf_path, dcd_path)
        frames = []
        energies = []

        for i, ts in enumerate(u.trajectory):
            frames.append(ts.positions.tolist())
            energies.append({
                "step": i,
                "potential": 0.0,
                "kinetic": 0.0,
                "total": 0.0,
            })

            if i % 10 == 0:
                progress = 0.7 + 0.2 * (i / max(len(u.trajectory), 1))
                self.update_state(state="PROGRESS", meta={
                    "progress": progress,
                    "message": f"Converting frame {i}/{len(u.trajectory)}"
                })

        # Try to parse energies from NAMD stdout
        try:
            _parse_namd_energies(result.stdout, energies)
        except Exception:
            pass

        sim_result = {
            "tool": "namd",
            "n_frames": len(frames),
            "n_atoms": u.atoms.n_atoms,
            "frames": frames,
            "energies": energies,
            "atom_names": list(u.atoms.names),
            "resnames": list(u.atoms.resnames),
        }

    self.update_state(state="PROGRESS", meta={"progress": 0.95, "message": "Saving results"})
    _save_result(self.request.id, "namd", sim_result, project, label)

    return sim_result


def _parse_namd_energies(stdout: str, energies: list):
    """Parse NAMD ENERGY output lines."""
    energy_idx = 0
    for line in stdout.split("\n"):
        if line.startswith("ENERGY:") and energy_idx < len(energies):
            parts = line.split()
            if len(parts) >= 14:
                try:
                    # NAMD ENERGY format: TS BOND ANGLE DIHED IMPRP ELECT VDW BOUNDARY MISC KINETIC TOTAL TEMP POTENTIAL TOTAL3
                    energies[energy_idx]["potential"] = float(parts[12])
                    energies[energy_idx]["kinetic"] = float(parts[10])
                    energies[energy_idx]["total"] = float(parts[11])
                    energy_idx += 1
                except (ValueError, IndexError):
                    pass
