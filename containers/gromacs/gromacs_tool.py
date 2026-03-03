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


@app.task(name="tools.gromacs_tool.run_gromacs", bind=True)
def run_gromacs(self, params: dict, project: str = "_default",
                label: str | None = None) -> dict:
    import MDAnalysis as mda

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Setting up GROMACS simulation"})

    gro_content = params.get("gro_content", "")
    top_content = params.get("top_content", "")
    mdp_content = params.get("mdp_content", "")

    if not gro_content:
        raise ValueError("gro_content is required (.gro file content)")
    if not top_content:
        raise ValueError("top_content is required (.top file content)")
    if not mdp_content:
        raise ValueError("mdp_content is required (.mdp file content)")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write input files
        gro_path = os.path.join(tmpdir, "input.gro")
        top_path = os.path.join(tmpdir, "topol.top")
        mdp_path = os.path.join(tmpdir, "run.mdp")
        tpr_path = os.path.join(tmpdir, "run.tpr")
        trr_path = os.path.join(tmpdir, "traj.trr")
        xtc_path = os.path.join(tmpdir, "traj.xtc")
        edr_path = os.path.join(tmpdir, "ener.edr")
        log_path = os.path.join(tmpdir, "md.log")
        confout_path = os.path.join(tmpdir, "confout.gro")

        with open(gro_path, "w") as f:
            f.write(gro_content)
        with open(top_path, "w") as f:
            f.write(top_content)
        with open(mdp_path, "w") as f:
            f.write(mdp_content)

        # grompp: generate run input
        self.update_state(state="PROGRESS", meta={"progress": 0.1, "message": "Running gmx grompp"})
        result = subprocess.run(
            ["gmx", "grompp", "-f", mdp_path, "-c", gro_path, "-p", top_path,
             "-o", tpr_path, "-maxwarn", "5"],
            capture_output=True, text=True, cwd=tmpdir,
        )
        if result.returncode != 0:
            raise RuntimeError(f"grompp failed: {result.stderr}")

        # mdrun: run simulation
        self.update_state(state="PROGRESS", meta={"progress": 0.2, "message": "Running gmx mdrun"})
        result = subprocess.run(
            ["gmx", "mdrun", "-deffnm", "run", "-s", tpr_path,
             "-o", trr_path, "-x", xtc_path, "-e", edr_path,
             "-g", log_path, "-c", confout_path, "-ntomp", "1"],
            capture_output=True, text=True, cwd=tmpdir,
        )
        if result.returncode != 0:
            raise RuntimeError(f"mdrun failed: {result.stderr}")

        self.update_state(state="PROGRESS", meta={"progress": 0.7, "message": "Converting trajectory to JSON"})

        # Convert trajectory using MDAnalysis
        traj_file = xtc_path if os.path.exists(xtc_path) else trr_path
        if not os.path.exists(traj_file):
            raise RuntimeError("No trajectory output found")

        # Use confout or input gro as topology for MDAnalysis
        topo_file = confout_path if os.path.exists(confout_path) else gro_path
        u = mda.Universe(topo_file, traj_file)

        frames = []
        energies = []
        for i, ts in enumerate(u.trajectory):
            frames.append(ts.positions.tolist())
            # MDAnalysis doesn't read energies from XTC; we report frame index
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

        # Try to parse energy from log
        try:
            _parse_gromacs_energies(log_path, energies)
        except Exception:
            pass

        sim_result = {
            "tool": "gromacs",
            "n_frames": len(frames),
            "n_atoms": u.atoms.n_atoms,
            "frames": frames,
            "energies": energies,
            "atom_names": list(u.atoms.names),
            "resnames": list(u.atoms.resnames),
        }

    self.update_state(state="PROGRESS", meta={"progress": 0.95, "message": "Saving results"})
    _save_result(self.request.id, "gromacs", sim_result, project, label)

    return sim_result


def _parse_gromacs_energies(log_path: str, energies: list):
    """Best-effort parsing of energies from GROMACS log file."""
    if not os.path.exists(log_path):
        return

    with open(log_path) as f:
        content = f.read()

    # Very basic parsing — GROMACS logs aren't easily parsed without gmx energy
    # This is best-effort; production use would run `gmx energy`
    lines = content.split("\n")
    energy_idx = 0
    for i, line in enumerate(lines):
        if "Potential" in line and "Kinetic" in line:
            # Next line has values
            if i + 1 < len(lines):
                vals = lines[i + 1].split()
                if len(vals) >= 2 and energy_idx < len(energies):
                    try:
                        energies[energy_idx]["potential"] = float(vals[0])
                        energies[energy_idx]["kinetic"] = float(vals[1])
                        energies[energy_idx]["total"] = float(vals[0]) + float(vals[1])
                        energy_idx += 1
                    except (ValueError, IndexError):
                        pass
