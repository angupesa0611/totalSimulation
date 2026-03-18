"""Meep tool — FDTD electromagnetic simulation."""

import json
import os
from typing import Any

import numpy as np
from worker import app as celery_app


RESULTS_DIR = os.getenv("RESULTS_DIR", "/data/results")


def save_result(job_id, tool, result, project="_default", label=None):
    """Save result to the shared results directory."""
    project_dir = os.path.join(RESULTS_DIR, project)
    os.makedirs(project_dir, exist_ok=True)

    entry = {
        "job_id": job_id,
        "tool": tool,
        "label": label,
        "result": result,
    }

    result_path = os.path.join(project_dir, f"{job_id}.json")
    with open(result_path, "w") as f:
        json.dump(entry, f)

    # Update index
    index_path = os.path.join(project_dir, "_index.json")
    index = []
    if os.path.exists(index_path):
        with open(index_path) as f:
            index = json.load(f)

    index.append({
        "job_id": job_id,
        "tool": tool,
        "label": label or f"{tool} simulation",
    })
    with open(index_path, "w") as f:
        json.dump(index, f)


def run_waveguide_bend(p: dict) -> dict[str, Any]:
    import meep as mp

    resolution = int(p.get("resolution", 30))
    sx = p.get("sx", 16.0)
    sy = p.get("sy", 16.0)
    pad = p.get("padding", 4.0)
    wg_width = p.get("waveguide_width", 1.0)
    wavelength = p.get("wavelength", 1.55)
    n_core = p.get("n_core", 3.4)
    dpml = p.get("pml_thickness", 1.0)

    cell = mp.Vector3(sx + 2 * dpml, sy + 2 * dpml)
    pml_layers = [mp.PML(dpml)]

    # Waveguide geometry: horizontal + vertical segments forming 90-degree bend
    geometry = [
        # Horizontal waveguide (left to center)
        mp.Block(
            center=mp.Vector3(-sx / 4, 0),
            size=mp.Vector3(sx / 2, wg_width, mp.inf),
            material=mp.Medium(index=n_core),
        ),
        # Vertical waveguide (center to top)
        mp.Block(
            center=mp.Vector3(0, sy / 4),
            size=mp.Vector3(wg_width, sy / 2, mp.inf),
            material=mp.Medium(index=n_core),
        ),
    ]

    fcen = 1.0 / wavelength
    df = 0.2 * fcen
    sources = [
        mp.Source(
            mp.GaussianSource(fcen, fwidth=df),
            component=mp.Ez,
            center=mp.Vector3(-sx / 2 + dpml + 0.5, 0),
            size=mp.Vector3(0, wg_width),
        )
    ]

    sim = mp.Simulation(
        cell_size=cell,
        boundary_layers=pml_layers,
        geometry=geometry,
        sources=sources,
        resolution=resolution,
    )

    # Run until fields decay
    run_time = p.get("run_time", 200)
    sim.run(until=run_time)

    # Get Ez field slice
    ez_data = sim.get_array(center=mp.Vector3(), size=mp.Vector3(sx, sy), component=mp.Ez)

    return {
        "tool": "meep",
        "simulation_type": "waveguide_bend",
        "resolution": resolution,
        "wavelength_um": wavelength,
        "n_core": n_core,
        "field_ez": ez_data.tolist(),
        "field_shape": list(ez_data.shape),
        "x_range": [-sx / 2, sx / 2],
        "y_range": [-sy / 2, sy / 2],
        "params": p,
    }


def run_ring_resonator(p: dict) -> dict[str, Any]:
    import meep as mp

    resolution = int(p.get("resolution", 30))
    n_core = p.get("n_core", 3.4)
    ring_radius = p.get("ring_radius", 5.0)
    wg_width = p.get("waveguide_width", 1.0)
    gap = p.get("gap", 0.1)
    wavelength = p.get("wavelength", 1.55)
    sx = 2 * ring_radius + 8
    sy = 2 * ring_radius + 8
    dpml = 1.0

    cell = mp.Vector3(sx + 2 * dpml, sy + 2 * dpml)
    pml_layers = [mp.PML(dpml)]

    geometry = [
        # Bus waveguide
        mp.Block(
            center=mp.Vector3(0, -(ring_radius + gap + wg_width / 2)),
            size=mp.Vector3(mp.inf, wg_width, mp.inf),
            material=mp.Medium(index=n_core),
        ),
        # Ring (cylinder - inner cylinder)
        mp.Cylinder(
            radius=ring_radius + wg_width / 2,
            height=mp.inf,
            material=mp.Medium(index=n_core),
            center=mp.Vector3(0, 0),
        ),
        mp.Cylinder(
            radius=ring_radius - wg_width / 2,
            height=mp.inf,
            material=mp.Medium(index=1.0),
            center=mp.Vector3(0, 0),
        ),
    ]

    fcen = 1.0 / wavelength
    df = 0.15 * fcen
    sources = [
        mp.Source(
            mp.GaussianSource(fcen, fwidth=df),
            component=mp.Ez,
            center=mp.Vector3(-sx / 2 + dpml + 0.5, -(ring_radius + gap + wg_width / 2)),
            size=mp.Vector3(0, wg_width),
        )
    ]

    sim = mp.Simulation(
        cell_size=cell,
        boundary_layers=pml_layers,
        geometry=geometry,
        sources=sources,
        resolution=resolution,
    )

    run_time = p.get("run_time", 400)
    sim.run(until=run_time)

    ez_data = sim.get_array(center=mp.Vector3(), size=mp.Vector3(sx, sy), component=mp.Ez)

    return {
        "tool": "meep",
        "simulation_type": "ring_resonator",
        "ring_radius": ring_radius,
        "gap": gap,
        "wavelength_um": wavelength,
        "field_ez": ez_data.tolist(),
        "field_shape": list(ez_data.shape),
        "x_range": [-sx / 2, sx / 2],
        "y_range": [-sy / 2, sy / 2],
        "params": p,
    }


def run_photonic_crystal(p: dict) -> dict[str, Any]:
    import meep as mp

    resolution = int(p.get("resolution", 32))
    n_rod = p.get("n_rod", 3.4)
    rod_radius = p.get("rod_radius", 0.2)
    lattice_constant = p.get("lattice_constant", 1.0)
    nx = int(p.get("nx", 7))
    ny = int(p.get("ny", 7))
    wavelength = p.get("wavelength", 1.55)

    sx = nx * lattice_constant
    sy = ny * lattice_constant
    dpml = 1.0

    cell = mp.Vector3(sx + 2 * dpml, sy + 2 * dpml)
    pml_layers = [mp.PML(dpml)]

    geometry = []
    for i in range(nx):
        for j in range(ny):
            cx = (i - nx // 2) * lattice_constant
            cy = (j - ny // 2) * lattice_constant
            geometry.append(
                mp.Cylinder(
                    radius=rod_radius,
                    height=mp.inf,
                    material=mp.Medium(index=n_rod),
                    center=mp.Vector3(cx, cy),
                )
            )

    fcen = 1.0 / wavelength
    df = 0.3 * fcen
    sources = [
        mp.Source(
            mp.GaussianSource(fcen, fwidth=df),
            component=mp.Ez,
            center=mp.Vector3(-sx / 2 + dpml, 0),
        )
    ]

    sim = mp.Simulation(
        cell_size=cell,
        boundary_layers=pml_layers,
        geometry=geometry,
        sources=sources,
        resolution=resolution,
    )

    sim.run(until=p.get("run_time", 200))

    ez_data = sim.get_array(center=mp.Vector3(), size=mp.Vector3(sx, sy), component=mp.Ez)

    return {
        "tool": "meep",
        "simulation_type": "photonic_crystal",
        "n_rod": n_rod,
        "rod_radius": rod_radius,
        "lattice_constant": lattice_constant,
        "field_ez": ez_data.tolist(),
        "field_shape": list(ez_data.shape),
        "x_range": [-sx / 2, sx / 2],
        "y_range": [-sy / 2, sy / 2],
        "params": p,
    }


def run_dipole_radiation(p: dict) -> dict[str, Any]:
    import meep as mp

    resolution = int(p.get("resolution", 30))
    wavelength = p.get("wavelength", 1.0)
    sx = p.get("sx", 16.0)
    sy = p.get("sy", 16.0)
    dpml = 1.5

    cell = mp.Vector3(sx + 2 * dpml, sy + 2 * dpml)
    pml_layers = [mp.PML(dpml)]

    fcen = 1.0 / wavelength
    sources = [
        mp.Source(
            mp.GaussianSource(fcen, fwidth=0.2 * fcen),
            component=mp.Ez,
            center=mp.Vector3(0, 0),
        )
    ]

    sim = mp.Simulation(
        cell_size=cell,
        boundary_layers=pml_layers,
        sources=sources,
        resolution=resolution,
    )

    sim.run(until=p.get("run_time", 100))

    ez_data = sim.get_array(center=mp.Vector3(), size=mp.Vector3(sx, sy), component=mp.Ez)

    return {
        "tool": "meep",
        "simulation_type": "dipole_radiation",
        "wavelength": wavelength,
        "field_ez": ez_data.tolist(),
        "field_shape": list(ez_data.shape),
        "x_range": [-sx / 2, sx / 2],
        "y_range": [-sy / 2, sy / 2],
        "params": p,
    }


@celery_app.task(name="tools.meep_tool.run_meep", bind=True)
def run_meep(self, params: dict, project: str = "_default",
             label: str | None = None) -> dict:
    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting Meep FDTD simulation"})

    sim_type = params.get("simulation_type")
    valid = ("waveguide_bend", "ring_resonator", "photonic_crystal", "dipole_radiation")
    if sim_type not in valid:
        raise ValueError(f"simulation_type must be one of: {valid}")

    sub_params = params.get(sim_type, {})

    if sim_type == "waveguide_bend":
        result = run_waveguide_bend(sub_params)
    elif sim_type == "ring_resonator":
        result = run_ring_resonator(sub_params)
    elif sim_type == "photonic_crystal":
        result = run_photonic_crystal(sub_params)
    elif sim_type == "dipole_radiation":
        result = run_dipole_radiation(sub_params)

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    save_result(self.request.id, "meep", result, project, label)
    return result
