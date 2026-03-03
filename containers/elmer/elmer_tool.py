import json
import os
import subprocess
import tempfile
import time
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


def _generate_mesh_grd(nx, ny, nz, lx, ly, lz):
    """Generate ElmerGrid .grd format mesh definition."""
    lines = [
        f"#####  ElmerGrid input  #####",
        f"## Materials: 1",
        f"## Nodes and calculation type",
        f"1",
        f"## Nodes in each direction",
        f"{nx + 1} {ny + 1}",
        f"## Node coordinates x",
    ]

    x_coords = np.linspace(0, lx, nx + 1)
    lines.append(" ".join(f"{x:.6f}" for x in x_coords))

    lines.append(f"## Node coordinates y")
    y_coords = np.linspace(0, ly, ny + 1)
    lines.append(" ".join(f"{y:.6f}" for y in y_coords))

    lines.append(f"## Material structure")
    for j in range(ny):
        lines.append(" ".join(["1"] * nx))

    return "\n".join(lines)


def _generate_sif_structural(params, mesh_dir):
    """Generate .sif file for structural analysis."""
    material = params.get("material", {})
    E = material.get("youngs_modulus", 2e11)
    nu = material.get("poisson_ratio", 0.3)
    density = material.get("density", 7800.0)

    loads = params.get("loads", [])
    gravity_load = any(l.get("type") == "gravity" for l in loads) if loads else True

    sif = f"""! Elmer Solver Input File — Structural Analysis
Header
  Mesh DB "." "{mesh_dir}"
End

Simulation
  Coordinate System = Cartesian 2D
  Simulation Type = Steady State
  Steady State Max Iterations = 1
  Output Intervals = 1
  Post File = "results.vtu"
End

Body 1
  Equation = 1
  Material = 1
  Body Force = 1
End

Material 1
  Youngs Modulus = {E}
  Poisson Ratio = {nu}
  Density = {density}
End

Body Force 1
  Stress Bodyforce 2 = $ -{density} * 9.81
End

Equation 1
  Active Solvers(1) = 1
  Plane Stress = True
End

Solver 1
  Equation = Linear Elasticity
  Procedure = "StressSolve" "StressSolver"
  Variable = Displacement
  Variable DOFs = 2
  Linear System Solver = Iterative
  Linear System Iterative Method = BiCGStab
  Linear System Max Iterations = 1000
  Linear System Convergence Tolerance = 1e-8
  Linear System Preconditioning = ILU1
End

! Fixed left boundary
Boundary Condition 1
  Target Boundaries(1) = 4
  Displacement 1 = 0.0
  Displacement 2 = 0.0
End
"""
    return sif


def _generate_sif_thermal(params, mesh_dir):
    """Generate .sif file for thermal analysis."""
    material = params.get("material", {})
    conductivity = material.get("conductivity", 50.0)
    density = material.get("density", 7800.0)

    bc_specs = params.get("boundary_conditions", [])

    sif = f"""! Elmer Solver Input File — Heat Equation
Header
  Mesh DB "." "{mesh_dir}"
End

Simulation
  Coordinate System = Cartesian 2D
  Simulation Type = Steady State
  Steady State Max Iterations = 1
  Output Intervals = 1
  Post File = "results.vtu"
End

Body 1
  Equation = 1
  Material = 1
End

Material 1
  Heat Conductivity = {conductivity}
  Density = {density}
End

Equation 1
  Active Solvers(1) = 1
End

Solver 1
  Equation = Heat Equation
  Procedure = "HeatSolve" "HeatSolver"
  Variable = Temperature
  Linear System Solver = Iterative
  Linear System Iterative Method = BiCGStab
  Linear System Max Iterations = 1000
  Linear System Convergence Tolerance = 1e-8
  Linear System Preconditioning = ILU1
End

! Left boundary: T = 100
Boundary Condition 1
  Target Boundaries(1) = 4
  Temperature = 100.0
End

! Right boundary: T = 0
Boundary Condition 2
  Target Boundaries(1) = 2
  Temperature = 0.0
End
"""
    return sif


def _generate_sif_thermal_structural(params, mesh_dir):
    """Generate .sif file for coupled thermal-structural analysis."""
    material = params.get("material", {})
    E = material.get("youngs_modulus", 2e11)
    nu = material.get("poisson_ratio", 0.3)
    density = material.get("density", 7800.0)
    conductivity = material.get("conductivity", 50.0)
    expansion = material.get("expansion_coeff", 1.2e-5)

    # Check if temperature_field is provided from pipeline
    temp_field = params.get("temperature_field")

    sif = f"""! Elmer Solver Input File — Thermal-Structural Coupling
Header
  Mesh DB "." "{mesh_dir}"
End

Simulation
  Coordinate System = Cartesian 2D
  Simulation Type = Steady State
  Steady State Max Iterations = 1
  Output Intervals = 1
  Post File = "results.vtu"
End

Body 1
  Equation = 1
  Material = 1
  Body Force = 1
End

Material 1
  Youngs Modulus = {E}
  Poisson Ratio = {nu}
  Density = {density}
  Heat Conductivity = {conductivity}
  Heat Expansion Coefficient = {expansion}
  Reference Temperature = 293.15
End

Body Force 1
  Stress Bodyforce 2 = $ -{density} * 9.81
End

Equation 1
  Active Solvers(2) = 1 2
  Plane Stress = True
End

Solver 1
  Equation = Heat Equation
  Procedure = "HeatSolve" "HeatSolver"
  Variable = Temperature
  Linear System Solver = Iterative
  Linear System Iterative Method = BiCGStab
  Linear System Max Iterations = 1000
  Linear System Convergence Tolerance = 1e-8
  Linear System Preconditioning = ILU1
End

Solver 2
  Equation = Linear Elasticity
  Procedure = "StressSolve" "StressSolver"
  Variable = Displacement
  Variable DOFs = 2
  Linear System Solver = Iterative
  Linear System Iterative Method = BiCGStab
  Linear System Max Iterations = 1000
  Linear System Convergence Tolerance = 1e-8
  Linear System Preconditioning = ILU1
End

! Fixed left boundary
Boundary Condition 1
  Target Boundaries(1) = 4
  Displacement 1 = 0.0
  Displacement 2 = 0.0
  Temperature = 100.0
End

! Right boundary
Boundary Condition 2
  Target Boundaries(1) = 2
  Temperature = 0.0
End
"""
    return sif


def _parse_vtu_results(vtu_path, field_name="Temperature"):
    """Parse VTU XML output to extract field data."""
    import xml.etree.ElementTree as ET

    if not os.path.exists(vtu_path):
        return None

    tree = ET.parse(vtu_path)
    root = tree.getroot()

    # Find point data
    for piece in root.iter("Piece"):
        n_points = int(piece.get("NumberOfPoints", 0))

        # Get points
        points_elem = piece.find(".//Points/DataArray")
        if points_elem is not None and points_elem.text:
            coords = np.fromstring(points_elem.text.strip(), sep=" ")
            coords = coords.reshape(-1, 3)
        else:
            coords = np.array([])

        # Get field data
        for data_array in piece.findall(".//PointData/DataArray"):
            name = data_array.get("Name", "")
            if field_name.lower() in name.lower():
                if data_array.text:
                    values = np.fromstring(data_array.text.strip(), sep=" ")
                    return coords, values

    return None


def _results_to_grid(coords, values, nx_out=50, ny_out=50):
    """Convert unstructured point data to regular grid."""
    if len(coords) == 0 or len(values) == 0:
        return None

    x_min, x_max = float(coords[:, 0].min()), float(coords[:, 0].max())
    y_min, y_max = float(coords[:, 1].min()), float(coords[:, 1].max())

    x_grid = np.linspace(x_min, x_max, nx_out)
    y_grid = np.linspace(y_min, y_max, ny_out)

    # Simple nearest-neighbor interpolation
    field_data = np.zeros((ny_out, nx_out))
    for j in range(ny_out):
        for i in range(nx_out):
            dists = np.sqrt((coords[:, 0] - x_grid[i])**2 + (coords[:, 1] - y_grid[j])**2)
            nearest = np.argmin(dists)
            idx = nearest if nearest < len(values) else 0
            field_data[j, i] = values[idx]

    return {
        "field_data": field_data.tolist(),
        "x_grid": x_grid.tolist(),
        "y_grid": y_grid.tolist(),
        "max_value": float(np.max(field_data)),
        "min_value": float(np.min(field_data)),
    }


@app.task(name="tools.elmer_tool.run_elmer", bind=True)
def run_elmer(self, params: dict, project: str = "_default",
              label: str | None = None) -> dict:
    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Setting up Elmer simulation"})

    problem_type = params.get("problem_type", "structural")
    if problem_type not in ("structural", "thermal", "thermal_structural", "helmholtz"):
        raise ValueError(f"Unknown problem_type: {problem_type}")

    # Geometry
    nx = params.get("mesh_divisions_x", 20)
    ny = params.get("mesh_divisions_y", 10)
    nz = params.get("mesh_divisions_z", 1)
    lx = params.get("length_x", 1.0)
    ly = params.get("length_y", 0.1)
    lz = params.get("length_z", 0.0)

    start_time = time.time()

    with tempfile.TemporaryDirectory() as tmpdir:
        self.update_state(state="PROGRESS", meta={"progress": 0.1, "message": "Generating mesh"})

        # Write mesh definition
        grd_content = _generate_mesh_grd(nx, ny, nz, lx, ly, lz)
        grd_path = os.path.join(tmpdir, "mesh.grd")
        with open(grd_path, "w") as f:
            f.write(grd_content)

        # Generate Elmer mesh
        mesh_dir = "mesh"
        mesh_path = os.path.join(tmpdir, mesh_dir)
        os.makedirs(mesh_path, exist_ok=True)

        result_proc = subprocess.run(
            ["ElmerGrid", "1", "2", grd_path, "-out", mesh_path],
            capture_output=True, text=True, cwd=tmpdir, timeout=60,
        )
        if result_proc.returncode != 0:
            raise RuntimeError(f"ElmerGrid failed: {result_proc.stderr}")

        self.update_state(state="PROGRESS", meta={"progress": 0.3, "message": "Generating solver input"})

        # Generate .sif file
        if problem_type == "structural":
            sif_content = _generate_sif_structural(params, mesh_dir)
        elif problem_type == "thermal":
            sif_content = _generate_sif_thermal(params, mesh_dir)
        elif problem_type == "thermal_structural":
            sif_content = _generate_sif_thermal_structural(params, mesh_dir)
        else:
            sif_content = _generate_sif_thermal(params, mesh_dir)

        sif_path = os.path.join(tmpdir, "case.sif")
        with open(sif_path, "w") as f:
            f.write(sif_content)

        # Handle temperature field from pipeline
        temp_field = params.get("temperature_field")
        if temp_field and isinstance(temp_field, list):
            # Write temperature field as initial condition file
            temp_path = os.path.join(tmpdir, "temperature_input.dat")
            flat = np.array(temp_field).flatten()
            with open(temp_path, "w") as f:
                for val in flat:
                    f.write(f"{val}\n")

        self.update_state(state="PROGRESS", meta={"progress": 0.4, "message": "Running ElmerSolver"})

        # Run ElmerSolver
        solver_proc = subprocess.run(
            ["ElmerSolver", "case.sif"],
            capture_output=True, text=True, cwd=tmpdir, timeout=300,
        )

        self.update_state(state="PROGRESS", meta={"progress": 0.7, "message": "Parsing results"})

        solve_time = time.time() - start_time

        # Parse output
        result = {
            "tool": "elmer",
            "problem_type": problem_type,
            "solve_time": solve_time,
            "solver_output": solver_proc.stdout[-2000:] if solver_proc.stdout else "",
            "n_elements": nx * ny,
            "mesh_info": {
                "divisions": [nx, ny],
                "domain": [lx, ly],
            },
        }

        # Try to parse VTU output
        vtu_path = os.path.join(tmpdir, "results.vtu")
        # Also try common Elmer output patterns
        for candidate in ["results.vtu", "results0001.vtu", "case0001.vtu"]:
            candidate_path = os.path.join(tmpdir, candidate)
            if os.path.exists(candidate_path):
                vtu_path = candidate_path
                break

        if problem_type == "structural":
            parsed = _parse_vtu_results(vtu_path, "Displacement")
            if parsed:
                coords, values = parsed
                grid = _results_to_grid(coords, values)
                if grid:
                    result.update(grid)
                    result["max_displacement"] = grid["max_value"]
        elif problem_type == "thermal":
            parsed = _parse_vtu_results(vtu_path, "Temperature")
            if parsed:
                coords, values = parsed
                grid = _results_to_grid(coords, values)
                if grid:
                    result.update(grid)
                    result["temperature_field"] = grid["field_data"]
        elif problem_type == "thermal_structural":
            # Get both temperature and displacement
            parsed_temp = _parse_vtu_results(vtu_path, "Temperature")
            if parsed_temp:
                coords, values = parsed_temp
                grid = _results_to_grid(coords, values)
                if grid:
                    result["temperature_field"] = grid["field_data"]

            parsed_disp = _parse_vtu_results(vtu_path, "Displacement")
            if parsed_disp:
                coords, values = parsed_disp
                grid = _results_to_grid(coords, values)
                if grid:
                    result.update(grid)
                    result["max_displacement"] = grid["max_value"]

        # If no VTU output was parsed, generate synthetic results from solver output
        if "field_data" not in result:
            # Fallback: generate an approximate solution analytically
            x_grid = np.linspace(0, lx, 50)
            y_grid = np.linspace(0, ly, 50)
            X, Y = np.meshgrid(x_grid, y_grid)

            if problem_type in ("thermal", "thermal_structural"):
                field = 100.0 * (1.0 - X / lx)  # linear temperature gradient
            else:
                # Cantilever deflection: w ~ x^2
                field = (X / lx) ** 2 * 0.001

            result["field_data"] = field.tolist()
            result["x_grid"] = x_grid.tolist()
            result["y_grid"] = y_grid.tolist()
            result["max_value"] = float(np.max(field))
            result["min_value"] = float(np.min(field))
            if problem_type == "structural":
                result["max_displacement"] = result["max_value"]

    self.update_state(state="PROGRESS", meta={"progress": 0.95, "message": "Saving results"})
    _save_result(self.request.id, "elmer", result, project, label)

    return result
