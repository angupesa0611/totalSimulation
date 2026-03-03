"""Format converters for trajectory and structure data.

Used by MDAnalysis tool and MD containers to convert
native formats (PDB, XTC, DCD) to JSON-serializable data.
"""
import json
import os
import tempfile


def pdb_to_json(pdb_content: str) -> dict:
    """Parse PDB content string into a dict of atom data."""
    atoms = []
    for line in pdb_content.strip().split("\n"):
        if line.startswith(("ATOM", "HETATM")):
            atoms.append({
                "serial": int(line[6:11].strip()),
                "name": line[12:16].strip(),
                "resname": line[17:20].strip(),
                "chain": line[21:22].strip(),
                "resid": int(line[22:26].strip()),
                "x": float(line[30:38]),
                "y": float(line[38:46]),
                "z": float(line[46:54]),
                "element": line[76:78].strip() if len(line) > 76 else "",
            })
    return {"atoms": atoms, "n_atoms": len(atoms)}


def frames_to_pdb(frames: list, atom_names: list[str] | None = None,
                  resnames: list[str] | None = None) -> str:
    """Convert frame coordinate arrays to multi-model PDB string."""
    lines = []
    n_atoms = len(frames[0]) if frames else 0

    for model_idx, frame in enumerate(frames):
        lines.append(f"MODEL     {model_idx + 1}")
        for i, pos in enumerate(frame):
            name = (atom_names[i] if atom_names and i < len(atom_names)
                    else f"C{i+1:>3}")
            resname = (resnames[i] if resnames and i < len(resnames)
                       else "UNK")
            x, y, z = pos[0], pos[1], pos[2]
            lines.append(
                f"ATOM  {i+1:>5} {name:<4} {resname:>3} A{1:>4}    "
                f"{x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00"
            )
        lines.append("ENDMDL")
    lines.append("END")
    return "\n".join(lines)


def xtc_to_json(topology_path: str, trajectory_path: str,
                stride: int = 1) -> dict:
    """Convert XTC trajectory to JSON frames using MDAnalysis.

    Args:
        topology_path: Path to topology file (GRO, PDB, etc.)
        trajectory_path: Path to XTC trajectory file
        stride: Read every Nth frame

    Returns:
        dict with frames, n_atoms, n_frames
    """
    import MDAnalysis as mda
    u = mda.Universe(topology_path, trajectory_path)
    frames = []
    for ts in u.trajectory[::stride]:
        frames.append(ts.positions.tolist())

    return {
        "frames": frames,
        "n_atoms": u.atoms.n_atoms,
        "n_frames": len(frames),
        "atom_names": list(u.atoms.names),
        "resnames": list(u.atoms.resnames),
    }


def dcd_to_json(topology_path: str, trajectory_path: str,
                stride: int = 1) -> dict:
    """Convert DCD trajectory to JSON frames using MDAnalysis.

    Same interface as xtc_to_json — MDAnalysis handles format detection.
    """
    import MDAnalysis as mda
    u = mda.Universe(topology_path, trajectory_path)
    frames = []
    for ts in u.trajectory[::stride]:
        frames.append(ts.positions.tolist())

    return {
        "frames": frames,
        "n_atoms": u.atoms.n_atoms,
        "n_frames": len(frames),
        "atom_names": list(u.atoms.names),
        "resnames": list(u.atoms.resnames),
    }
