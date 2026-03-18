import json
import os
import re
import subprocess
import tempfile
import time
from datetime import datetime, timezone
import numpy as np
from worker import app


def _save_result(job_id, tool, data, project="_default", label=None):
    results_dir = os.getenv("RESULTS_DIR", "/data/results")
    project_dir = os.path.join(results_dir, project)
    os.makedirs(project_dir, exist_ok=True)
    run_dir = os.path.join(project_dir, job_id)
    os.makedirs(run_dir, exist_ok=True)

    metadata = {
        "job_id": job_id, "tool": tool, "project": project,
        "label": label, "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with open(os.path.join(run_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
    with open(os.path.join(run_dir, "result.json"), "w") as f:
        json.dump(data, f)

    index_path = os.path.join(project_dir, "_index.json")
    index = []
    if os.path.exists(index_path):
        with open(index_path) as f:
            index = json.load(f)
    index.append(metadata)
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)
    return run_dir


def _write_foam_dict(filepath, header_class, header_object, content):
    """Write an OpenFOAM dictionary file."""
    header = f"""FoamFile
{{
    version     2.0;
    format      ascii;
    class       {header_class};
    object      {header_object};
}}
"""
    with open(filepath, "w") as f:
        f.write(header)
        f.write(content)


def _setup_cavity_case(case_dir, params):
    """Set up a lid-driven cavity case."""
    re_num = params.get("re", 100)
    n_cells = params.get("n_cells", [20, 20, 1])
    end_time = params.get("end_time", 0.5)
    write_interval = params.get("write_interval", 0.1)
    nx, ny, nz = n_cells

    # Kinematic viscosity for Re=100 with U=1, L=0.1
    nu = 0.1 / re_num

    # system/controlDict
    _write_foam_dict(os.path.join(case_dir, "system", "controlDict"),
                     "dictionary", "controlDict", f"""
application     icoFoam;
startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         {end_time};
deltaT          0.005;
writeControl    timeStep;
writeInterval   {int(write_interval / 0.005)};
purgeWrite      0;
writeFormat     ascii;
writePrecision  6;
writeCompression off;
timeFormat      general;
timePrecision   6;
runTimeModifiable true;
""")

    # system/fvSchemes
    _write_foam_dict(os.path.join(case_dir, "system", "fvSchemes"),
                     "dictionary", "fvSchemes", """
ddtSchemes
{
    default         Euler;
}
gradSchemes
{
    default         Gauss linear;
}
divSchemes
{
    default         none;
    div(phi,U)      Gauss linear;
}
laplacianSchemes
{
    default         Gauss linear corrected;
}
interpolationSchemes
{
    default         linear;
}
snGradSchemes
{
    default         corrected;
}
""")

    # system/fvSolution
    _write_foam_dict(os.path.join(case_dir, "system", "fvSolution"),
                     "dictionary", "fvSolution", """
solvers
{
    p
    {
        solver          PCG;
        preconditioner  DIC;
        tolerance       1e-06;
        relTol          0.05;
    }
    pFinal
    {
        $p;
        relTol          0;
    }
    U
    {
        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-05;
        relTol          0;
    }
}
PISO
{
    nCorrectors     2;
    nNonOrthogonalCorrectors 0;
    pRefCell        0;
    pRefValue       0;
}
""")

    # system/blockMeshDict
    _write_foam_dict(os.path.join(case_dir, "system", "blockMeshDict"),
                     "dictionary", "blockMeshDict", f"""
scale   0.1;
vertices
(
    (0 0 0)
    (1 0 0)
    (1 1 0)
    (0 1 0)
    (0 0 0.1)
    (1 0 0.1)
    (1 1 0.1)
    (0 1 0.1)
);
blocks
(
    hex (0 1 2 3 4 5 6 7) ({nx} {ny} {nz}) simpleGrading (1 1 1)
);
edges
(
);
boundary
(
    movingWall
    {{
        type wall;
        faces
        (
            (3 7 6 2)
        );
    }}
    fixedWalls
    {{
        type wall;
        faces
        (
            (0 4 7 3)
            (2 6 5 1)
            (1 5 4 0)
        );
    }}
    frontAndBack
    {{
        type empty;
        faces
        (
            (0 3 2 1)
            (4 5 6 7)
        );
    }}
);
""")

    # constant/physicalProperties (OpenFOAM 11+ naming)
    _write_foam_dict(os.path.join(case_dir, "constant", "physicalProperties"),
                     "dictionary", "physicalProperties", f"""
nu              [0 2 -1 0 0 0 0] {nu};
""")

    # 0/U
    _write_foam_dict(os.path.join(case_dir, "0", "U"),
                     "volVectorField", "U", """
dimensions      [0 1 -1 0 0 0 0];
internalField   uniform (0 0 0);
boundaryField
{
    movingWall
    {
        type            fixedValue;
        value           uniform (1 0 0);
    }
    fixedWalls
    {
        type            noSlip;
    }
    frontAndBack
    {
        type            empty;
    }
}
""")

    # 0/p
    _write_foam_dict(os.path.join(case_dir, "0", "p"),
                     "volScalarField", "p", """
dimensions      [0 2 -2 0 0 0 0];
internalField   uniform 0;
boundaryField
{
    movingWall
    {
        type            zeroGradient;
    }
    fixedWalls
    {
        type            zeroGradient;
    }
    frontAndBack
    {
        type            empty;
    }
}
""")


def _setup_pipe_flow_case(case_dir, params):
    """Set up a pipe flow case."""
    diameter = params.get("diameter", 0.1)
    length = params.get("length", 1.0)
    velocity_inlet = params.get("velocity_inlet", 1.0)
    n_cells = params.get("n_cells", [50, 10, 1])
    end_time = params.get("end_time", 1.0)
    nx, ny, nz = n_cells
    nu = 1e-3  # Water-like

    _write_foam_dict(os.path.join(case_dir, "system", "controlDict"),
                     "dictionary", "controlDict", f"""
application     icoFoam;
startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         {end_time};
deltaT          0.001;
writeControl    timeStep;
writeInterval   100;
purgeWrite      0;
writeFormat     ascii;
writePrecision  6;
writeCompression off;
timeFormat      general;
timePrecision   6;
runTimeModifiable true;
""")

    _write_foam_dict(os.path.join(case_dir, "system", "fvSchemes"),
                     "dictionary", "fvSchemes", """
ddtSchemes { default Euler; }
gradSchemes { default Gauss linear; }
divSchemes { default none; div(phi,U) Gauss linear; }
laplacianSchemes { default Gauss linear corrected; }
interpolationSchemes { default linear; }
snGradSchemes { default corrected; }
""")

    _write_foam_dict(os.path.join(case_dir, "system", "fvSolution"),
                     "dictionary", "fvSolution", """
solvers
{
    p { solver PCG; preconditioner DIC; tolerance 1e-06; relTol 0.05; }
    pFinal { $p; relTol 0; }
    U { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-05; relTol 0; }
}
PISO { nCorrectors 2; nNonOrthogonalCorrectors 0; pRefCell 0; pRefValue 0; }
""")

    r = diameter / 2
    _write_foam_dict(os.path.join(case_dir, "system", "blockMeshDict"),
                     "dictionary", "blockMeshDict", f"""
scale   1;
vertices
(
    (0 0 0)
    ({length} 0 0)
    ({length} {r} 0)
    (0 {r} 0)
    (0 0 0.01)
    ({length} 0 0.01)
    ({length} {r} 0.01)
    (0 {r} 0.01)
);
blocks ( hex (0 1 2 3 4 5 6 7) ({nx} {ny} {nz}) simpleGrading (1 1 1) );
edges ();
boundary
(
    inlet {{ type patch; faces ((0 4 7 3)); }}
    outlet {{ type patch; faces ((2 6 5 1)); }}
    walls {{ type wall; faces ((3 7 6 2)); }}
    axis {{ type symmetryPlane; faces ((1 5 4 0)); }}
    frontAndBack {{ type empty; faces ((0 3 2 1) (4 5 6 7)); }}
);
""")

    _write_foam_dict(os.path.join(case_dir, "constant", "physicalProperties"),
                     "dictionary", "physicalProperties", f"nu [0 2 -1 0 0 0 0] {nu};\n")

    _write_foam_dict(os.path.join(case_dir, "0", "U"),
                     "volVectorField", "U", f"""
dimensions      [0 1 -1 0 0 0 0];
internalField   uniform (0 0 0);
boundaryField
{{
    inlet {{ type fixedValue; value uniform ({velocity_inlet} 0 0); }}
    outlet {{ type zeroGradient; }}
    walls {{ type noSlip; }}
    axis {{ type symmetryPlane; }}
    frontAndBack {{ type empty; }}
}}
""")

    _write_foam_dict(os.path.join(case_dir, "0", "p"),
                     "volScalarField", "p", """
dimensions      [0 2 -2 0 0 0 0];
internalField   uniform 0;
boundaryField
{
    inlet { type zeroGradient; }
    outlet { type fixedValue; value uniform 0; }
    walls { type zeroGradient; }
    axis { type symmetryPlane; }
    frontAndBack { type empty; }
}
""")


def _parse_residuals(log_text):
    """Parse OpenFOAM solver log for residuals."""
    residuals = {"Ux": [], "Uy": [], "p": []}
    iterations = []
    step = 0

    for line in log_text.split("\n"):
        if "Solving for Ux" in line:
            match = re.search(r"Final residual = ([0-9.e+-]+)", line)
            if match:
                residuals["Ux"].append(float(match.group(1)))
        elif "Solving for Uy" in line:
            match = re.search(r"Final residual = ([0-9.e+-]+)", line)
            if match:
                residuals["Uy"].append(float(match.group(1)))
        elif "Solving for p" in line:
            match = re.search(r"Final residual = ([0-9.e+-]+)", line)
            if match:
                residuals["p"].append(float(match.group(1)))
                step += 1
                iterations.append(step)

    return residuals, iterations


def _read_internal_field(filepath, n_cells_total):
    """Read an OpenFOAM internal field file and return numpy array."""
    try:
        with open(filepath) as f:
            content = f.read()

        # Find the internalField data block
        start = content.find("internalField")
        if start < 0:
            return None

        # Find opening paren after count
        paren_start = content.find("(", start)
        paren_end = content.find(")", paren_start)
        if paren_start < 0 or paren_end < 0:
            return None

        data_str = content[paren_start + 1:paren_end].strip()
        lines = data_str.strip().split("\n")

        values = []
        for line in lines:
            line = line.strip()
            if line.startswith("(") and line.endswith(")"):
                # Vector field
                parts = line[1:-1].split()
                values.append([float(x) for x in parts])
            elif line:
                try:
                    values.append(float(line))
                except ValueError:
                    continue

        return values
    except Exception:
        return None


@app.task(name="tools.openfoam_tool.run_openfoam", bind=True, soft_time_limit=600)
def run_openfoam(self, params, project="_default", label=None):
    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting OpenFOAM simulation"})

    sim_type = params.get("simulation_type", "cavity")
    solver = params.get("solver", "icoFoam")

    try:
        with tempfile.TemporaryDirectory() as case_dir:
            # Create directory structure
            os.makedirs(os.path.join(case_dir, "system"), exist_ok=True)
            os.makedirs(os.path.join(case_dir, "constant"), exist_ok=True)
            os.makedirs(os.path.join(case_dir, "0"), exist_ok=True)

            self.update_state(state="PROGRESS", meta={"progress": 0.1, "message": "Setting up case"})

            # Set up case based on type
            if sim_type == "cavity":
                _setup_cavity_case(case_dir, params)
            elif sim_type == "pipe_flow":
                _setup_pipe_flow_case(case_dir, params)
            else:
                raise ValueError(f"Unknown simulation_type: {sim_type}")

            self.update_state(state="PROGRESS", meta={"progress": 0.2, "message": "Generating mesh"})

            # Check for external mesh file
            mesh_file = params.get("mesh_file", None)
            if mesh_file and os.path.exists(mesh_file):
                # Use gmshToFoam for Gmsh mesh
                result = subprocess.run(
                    ["gmshToFoam", mesh_file],
                    capture_output=True, text=True, timeout=120,
                    cwd=case_dir
                )
                if result.returncode != 0:
                    raise RuntimeError(f"gmshToFoam failed: {result.stderr[:300]}")
            else:
                # Run blockMesh
                result = subprocess.run(
                    ["blockMesh"],
                    capture_output=True, text=True, timeout=120,
                    cwd=case_dir
                )
                if result.returncode != 0:
                    raise RuntimeError(f"blockMesh failed: {result.stderr[:300]}")

            self.update_state(state="PROGRESS", meta={"progress": 0.3, "message": f"Running {solver}"})

            # Run solver
            start_time = time.time()
            result = subprocess.run(
                [solver],
                capture_output=True, text=True, timeout=500,
                cwd=case_dir
            )
            execution_time = time.time() - start_time

            log_text = result.stdout + result.stderr

            if result.returncode != 0:
                raise RuntimeError(f"{solver} failed: {log_text[-500:]}")

            self.update_state(state="PROGRESS", meta={"progress": 0.7, "message": "Parsing results"})

            # Parse residuals
            residuals, iterations = _parse_residuals(log_text)

            # Find the latest time directory
            time_dirs = []
            for d in os.listdir(case_dir):
                try:
                    t = float(d)
                    if t > 0:
                        time_dirs.append((t, d))
                except ValueError:
                    continue
            time_dirs.sort()

            # Read final fields
            velocity_field = None
            pressure_field = None
            if time_dirs:
                last_dir = os.path.join(case_dir, time_dirs[-1][1])
                u_path = os.path.join(last_dir, "U")
                p_path = os.path.join(last_dir, "p")

                if os.path.exists(u_path):
                    velocity_field = _read_internal_field(u_path, 0)
                if os.path.exists(p_path):
                    pressure_field = _read_internal_field(p_path, 0)

            # Reshape to 2D grid for visualization
            n_cells = params.get("n_cells", [20, 20, 1])
            nx, ny = n_cells[0], n_cells[1]

            velocity_2d = None
            pressure_2d = None

            if velocity_field and len(velocity_field) == nx * ny:
                vel_arr = np.array(velocity_field)
                vel_mag = np.sqrt(vel_arr[:, 0]**2 + vel_arr[:, 1]**2)
                velocity_2d = vel_mag.reshape(ny, nx).tolist()

            if pressure_field and len(pressure_field) == nx * ny:
                pressure_2d = np.array(pressure_field).reshape(ny, nx).tolist()

            x_grid = np.linspace(0, 1, nx).tolist()
            y_grid = np.linspace(0, 1, ny).tolist()

            result_data = {
                "tool": "openfoam",
                "simulation_type": sim_type,
                "problem_type": "cfd",
                "solver": solver,
                "residuals": residuals,
                "iterations": iterations,
                "field_data": velocity_2d or pressure_2d,
                "pressure_field": pressure_2d,
                "x_grid": x_grid,
                "y_grid": y_grid,
                "execution_time_s": execution_time,
                "n_cells": n_cells,
                "n_time_steps": len(time_dirs),
            }

    except Exception as e:
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    _save_result(self.request.id, "openfoam", result_data, project, label)

    return result_data
