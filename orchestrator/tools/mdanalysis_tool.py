import io
import os
import tempfile
from typing import Any
import numpy as np
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result, get_result_data


class MDAnalysisTool(SimulationTool):
    name = "MDAnalysis"
    key = "mdanalysis"
    layer = "analysis"

    ANALYSIS_TYPES = {"rmsd", "rmsf", "rg", "contacts", "ramachandran", "hbonds"}

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        analysis_type = params.get("analysis_type", "rmsd")
        if analysis_type not in self.ANALYSIS_TYPES:
            raise ValueError(f"Unknown analysis_type: {analysis_type}. Supported: {self.ANALYSIS_TYPES}")

        if "source_job_id" not in params and "trajectory_data" not in params:
            raise ValueError("Either source_job_id or trajectory_data is required")

        params.setdefault("analysis_type", "rmsd")
        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        params = self.validate_params(params)
        analysis_type = params["analysis_type"]

        # Get trajectory data from source job or inline
        if "source_job_id" in params and params["source_job_id"]:
            project = params.get("project", "_default")
            source_data = get_result_data(params["source_job_id"], project)
            if source_data is not None and source_data.get("frames"):
                frames = source_data["frames"]
                n_atoms = source_data.get("n_atoms", 0)
                energies = source_data.get("energies", [])
            elif "trajectory_data" in params:
                # Source job has no frame data; fall through to inline trajectory
                traj = params["trajectory_data"]
                frames = traj.get("frames", [])
                n_atoms = traj.get("n_atoms", len(frames[0]) if frames else 0)
                energies = traj.get("energies", [])
            else:
                raise ValueError(f"Source job {params['source_job_id']} has no trajectory frames")
        elif "trajectory_data" in params:
            traj = params["trajectory_data"]
            frames = traj.get("frames", [])
            n_atoms = traj.get("n_atoms", len(frames[0]) if frames else 0)
            energies = traj.get("energies", [])
        else:
            raise ValueError("No trajectory data available")

        if not frames:
            raise ValueError("No frames in trajectory data")

        positions = np.array(frames)  # (n_frames, n_atoms, 3)

        # Dispatch to analysis method
        if analysis_type == "rmsd":
            result_data = self._compute_rmsd(positions)
        elif analysis_type == "rmsf":
            result_data = self._compute_rmsf(positions)
        elif analysis_type == "rg":
            result_data = self._compute_rg(positions)
        elif analysis_type == "contacts":
            result_data = self._compute_contacts(positions, params.get("cutoff", 5.0))
        elif analysis_type == "ramachandran":
            result_data = self._compute_ramachandran(positions, n_atoms)
        elif analysis_type == "hbonds":
            result_data = self._compute_hbonds(positions, params.get("cutoff", 3.5))

        result_data["tool"] = "mdanalysis"
        result_data["analysis_type"] = analysis_type
        result_data["n_frames"] = len(frames)
        result_data["n_atoms"] = n_atoms
        if "source_job_id" in params:
            result_data["source_job_id"] = params["source_job_id"]

        return result_data

    def _compute_rmsd(self, positions: np.ndarray) -> dict:
        """RMSD relative to first frame."""
        ref = positions[0]
        rmsd_values = []
        for frame in positions:
            diff = frame - ref
            rmsd = np.sqrt(np.mean(np.sum(diff ** 2, axis=1)))
            rmsd_values.append(float(rmsd))

        return {
            "times": list(range(len(rmsd_values))),
            "rmsd": rmsd_values,
            "mean_rmsd": float(np.mean(rmsd_values)),
            "max_rmsd": float(np.max(rmsd_values)),
        }

    def _compute_rmsf(self, positions: np.ndarray) -> dict:
        """Per-atom RMSF over trajectory."""
        mean_pos = np.mean(positions, axis=0)
        diff = positions - mean_pos
        rmsf = np.sqrt(np.mean(np.sum(diff ** 2, axis=2), axis=0))

        return {
            "atom_indices": list(range(len(rmsf))),
            "rmsf": rmsf.tolist(),
            "mean_rmsf": float(np.mean(rmsf)),
        }

    def _compute_rg(self, positions: np.ndarray) -> dict:
        """Radius of gyration over trajectory."""
        rg_values = []
        for frame in positions:
            com = np.mean(frame, axis=0)
            diff = frame - com
            rg = np.sqrt(np.mean(np.sum(diff ** 2, axis=1)))
            rg_values.append(float(rg))

        return {
            "times": list(range(len(rg_values))),
            "rg": rg_values,
            "mean_rg": float(np.mean(rg_values)),
        }

    def _compute_contacts(self, positions: np.ndarray, cutoff: float = 5.0) -> dict:
        """Contact map from last frame."""
        last_frame = positions[-1]
        n = len(last_frame)
        contact_map = np.zeros((n, n))

        for i in range(n):
            for j in range(i + 1, n):
                dist = np.linalg.norm(last_frame[i] - last_frame[j])
                if dist < cutoff:
                    contact_map[i, j] = 1
                    contact_map[j, i] = 1

        # Count contacts per frame
        contacts_per_frame = []
        for frame in positions:
            count = 0
            for i in range(n):
                for j in range(i + 1, n):
                    if np.linalg.norm(frame[i] - frame[j]) < cutoff:
                        count += 1
            contacts_per_frame.append(count)

        return {
            "contact_map": contact_map.tolist(),
            "contacts_per_frame": contacts_per_frame,
            "times": list(range(len(contacts_per_frame))),
            "cutoff": cutoff,
        }

    def _compute_ramachandran(self, positions: np.ndarray, n_atoms: int) -> dict:
        """Simplified backbone dihedral analysis."""
        # For a proper Ramachandran we need backbone atom identification.
        # Here we compute sequential dihedral angles as a proxy.
        phi_values = []
        psi_values = []

        for frame in positions:
            if n_atoms < 4:
                continue
            # Compute sequential dihedrals for every 4 consecutive atoms
            for i in range(0, min(n_atoms - 3, 20)):  # Limit for performance
                d = self._dihedral(frame[i], frame[i+1], frame[i+2], frame[i+3])
                if i % 2 == 0:
                    phi_values.append(float(d))
                else:
                    psi_values.append(float(d))

        return {
            "phi": phi_values,
            "psi": psi_values,
        }

    def _compute_hbonds(self, positions: np.ndarray, cutoff: float = 3.5) -> dict:
        """Simplified hydrogen bond count (distance-based)."""
        hbond_counts = []
        for frame in positions:
            n = len(frame)
            count = 0
            for i in range(n):
                for j in range(i + 1, min(n, i + 10)):  # Local pairs only
                    dist = np.linalg.norm(frame[i] - frame[j])
                    if dist < cutoff:
                        count += 1
            hbond_counts.append(count)

        return {
            "times": list(range(len(hbond_counts))),
            "hbond_count": hbond_counts,
            "mean_hbonds": float(np.mean(hbond_counts)) if hbond_counts else 0,
            "cutoff": cutoff,
        }

    @staticmethod
    def _dihedral(p1, p2, p3, p4) -> float:
        """Compute dihedral angle in degrees."""
        b1 = p2 - p1
        b2 = p3 - p2
        b3 = p4 - p3

        n1 = np.cross(b1, b2)
        n2 = np.cross(b2, b3)

        n1_norm = np.linalg.norm(n1)
        n2_norm = np.linalg.norm(n2)

        if n1_norm < 1e-10 or n2_norm < 1e-10:
            return 0.0

        n1 = n1 / n1_norm
        n2 = n2 / n2_norm

        m1 = np.cross(n1, b2 / np.linalg.norm(b2))
        x = np.dot(n1, n2)
        y = np.dot(m1, n2)

        return float(np.degrees(np.arctan2(y, x)))

    def get_default_params(self) -> dict[str, Any]:
        return {
            "analysis_type": "rmsd",
            "source_job_id": "",
        }


@celery_app.task(name="tools.mdanalysis_tool.run_mdanalysis", bind=True)
def run_mdanalysis(self, params: dict, project: str = "_default",
                   label: str | None = None) -> dict:
    tool = MDAnalysisTool()

    self.update_state(state="PROGRESS", meta={
        "progress": 0.0,
        "message": f"Starting {params.get('analysis_type', 'rmsd').upper()} analysis"
    })

    try:
        # Pass project to params so source_job_id lookup works
        params["project"] = project
        self.update_state(state="PROGRESS", meta={"progress": 0.2, "message": "Loading trajectory data"})
        result = tool.run(params)
    except Exception as e:
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    save_result(self.request.id, "mdanalysis", result, project, label)

    return result
