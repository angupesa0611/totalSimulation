import json
import math
import os
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


def _generate_naca_mesh(naca_digits="0012", n_points=129, far_field=10.0):
    """Generate a simple NACA airfoil mesh in SU2 native format."""
    # Parse 4-digit NACA
    m = int(naca_digits[0]) / 100.0
    p_camber = int(naca_digits[1]) / 10.0
    t = int(naca_digits[2:]) / 100.0

    # Generate airfoil surface points
    beta = np.linspace(0, math.pi, n_points)
    x_c = 0.5 * (1 - np.cos(beta))

    # Thickness distribution
    yt = 5 * t * (0.2969 * np.sqrt(x_c) - 0.1260 * x_c
                  - 0.3516 * x_c**2 + 0.2843 * x_c**3 - 0.1015 * x_c**4)

    # Camber line
    yc = np.zeros_like(x_c)
    if m > 0 and p_camber > 0:
        mask1 = x_c <= p_camber
        mask2 = x_c > p_camber
        yc[mask1] = (m / p_camber**2) * (2 * p_camber * x_c[mask1] - x_c[mask1]**2)
        yc[mask2] = (m / (1 - p_camber)**2) * ((1 - 2 * p_camber) + 2 * p_camber * x_c[mask2] - x_c[mask2]**2)

    x_upper = x_c
    y_upper = yc + yt
    x_lower = x_c
    y_lower = yc - yt

    # Build structured C-mesh points
    n_far = 33
    r_vals = np.linspace(1.0, far_field, n_far)

    all_x = []
    all_y = []

    # Airfoil surface points (upper then lower, excluding duplicate TE)
    surface_x = np.concatenate([x_upper, x_lower[-2:0:-1]])
    surface_y = np.concatenate([y_upper, y_lower[-2:0:-1]])
    n_surface = len(surface_x)

    for r in r_vals:
        for i in range(n_surface):
            angle = math.atan2(surface_y[i], surface_x[i] - 0.5) if r > 1.0 else 0
            all_x.append(surface_x[i] + (r - 1) * math.cos(angle) * (r - 1) / far_field)
            all_y.append(surface_y[i] + (r - 1) * math.sin(angle) * max(0.1, (r - 1) / far_field))

    n_points_total = len(all_x)
    n_elems = (n_surface - 1) * (n_far - 1)

    # Write SU2 mesh
    lines = [f"% NACA {naca_digits} airfoil mesh", f"NDIME= 2"]
    lines.append(f"NPOIN= {n_points_total}")
    for i in range(n_points_total):
        lines.append(f"  {all_x[i]:.10e}  {all_y[i]:.10e}  {i}")

    lines.append(f"NELEM= {n_elems}")
    elem_idx = 0
    for j in range(n_far - 1):
        for i in range(n_surface - 1):
            n0 = j * n_surface + i
            n1 = j * n_surface + i + 1
            n2 = (j + 1) * n_surface + i + 1
            n3 = (j + 1) * n_surface + i
            lines.append(f"9  {n0}  {n1}  {n2}  {n3}  {elem_idx}")
            elem_idx += 1

    # Markers
    lines.append("NMARK= 2")
    lines.append("MARKER_TAG= airfoil")
    lines.append(f"MARKER_ELEMS= {n_surface - 1}")
    for i in range(n_surface - 1):
        lines.append(f"3  {i}  {i + 1}")

    far_start = (n_far - 1) * n_surface
    lines.append("MARKER_TAG= farfield")
    lines.append(f"MARKER_ELEMS= {n_surface - 1}")
    for i in range(n_surface - 1):
        lines.append(f"3  {far_start + i}  {far_start + i + 1}")

    return "\n".join(lines)


def _generate_config(sim_type, params):
    """Generate SU2 .cfg configuration file content."""
    mach = params.get("mach_number", 0.8)
    aoa = params.get("angle_of_attack", 1.25)
    reynolds = params.get("reynolds_number", 6.5e6)
    n_iter = params.get("n_iterations", 250)

    cfg = [
        f"% SU2 config for {sim_type}",
        f"MATH_PROBLEM= DIRECT",
    ]

    if sim_type == "euler_flow":
        cfg += [
            "SOLVER= EULER",
            "CONV_NUM_METHOD_FLOW= JST",
        ]
    elif sim_type == "rans":
        cfg += [
            "SOLVER= RANS",
            "KIND_TURB_MODEL= SA",
            "CONV_NUM_METHOD_FLOW= JST",
            f"REYNOLDS_NUMBER= {reynolds}",
        ]
    elif sim_type == "inviscid_airfoil":
        cfg += [
            "SOLVER= EULER",
            "CONV_NUM_METHOD_FLOW= ROE",
        ]
    elif sim_type == "nozzle_flow":
        cfg += [
            "SOLVER= EULER",
            "CONV_NUM_METHOD_FLOW= ROE",
        ]
    else:
        cfg += [
            "SOLVER= EULER",
            "CONV_NUM_METHOD_FLOW= JST",
        ]

    cfg += [
        f"MACH_NUMBER= {mach}",
        f"AOA= {aoa}",
        "SIDESLIP_ANGLE= 0.0",
        "FREESTREAM_TEMPERATURE= 288.15",
        "FREESTREAM_PRESSURE= 101325.0",
        f"REF_ORIGIN_MOMENT_X= 0.25",
        f"REF_ORIGIN_MOMENT_Y= 0.00",
        f"REF_ORIGIN_MOMENT_Z= 0.00",
        "REF_LENGTH= 1.0",
        "REF_AREA= 1.0",
        "",
        "MARKER_EULER= ( airfoil )",
        "MARKER_FAR= ( farfield )",
        "MARKER_MONITORING= ( airfoil )",
        "",
        f"NUM_METHOD_GRAD= GREEN_GAUSS",
        "CFL_NUMBER= 10.0",
        "CFL_ADAPT= NO",
        "",
        f"ITER= {n_iter}",
        "CONV_RESIDUAL_MINVAL= -12",
        "",
        "MESH_FILENAME= mesh.su2",
        "MESH_FORMAT= SU2",
        "OUTPUT_FILES= RESTART, PARAVIEW",
        "CONV_FILENAME= history",
        "VOLUME_FILENAME= flow",
        "SURFACE_FILENAME= surface_flow",
        "TABULAR_FORMAT= CSV",
        "OUTPUT_WRT_FREQ= 50",
        "",
        "SCREEN_OUTPUT= INNER_ITER, RMS_DENSITY, LIFT, DRAG",
    ]

    return "\n".join(cfg)


def _parse_history_csv(history_path):
    """Parse SU2 convergence history CSV."""
    iterations = []
    rms_density = []
    cl_values = []
    cd_values = []

    if not os.path.exists(history_path):
        return iterations, rms_density, cl_values, cd_values

    with open(history_path) as f:
        header = None
        for line in f:
            line = line.strip()
            if not line:
                continue
            if header is None:
                header = [h.strip().strip('"') for h in line.split(",")]
                continue
            parts = line.split(",")
            try:
                row = {h: parts[i].strip().strip('"') for i, h in enumerate(header) if i < len(parts)}
                it = int(row.get("Inner_Iter", row.get("Iteration", "0")))
                iterations.append(it)
                rms_density.append(float(row.get("rms[Rho]", row.get("RMS_Density", "0"))))
                cl_values.append(float(row.get("CL", row.get("Lift", "0"))))
                cd_values.append(float(row.get("CD", row.get("Drag", "0"))))
            except (ValueError, KeyError):
                continue

    return iterations, rms_density, cl_values, cd_values


@app.task(name="tools.su2_tool.run_su2", bind=True, soft_time_limit=600)
def run_su2(self, params, project="_default", label=None):
    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting SU2 CFD simulation"})

    sim_type = params.get("simulation_type", "inviscid_airfoil")
    if sim_type not in ("euler_flow", "rans", "inviscid_airfoil", "nozzle_flow"):
        raise ValueError(f"Unknown simulation_type: {sim_type}")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate mesh
            self.update_state(state="PROGRESS", meta={"progress": 0.1, "message": "Generating mesh"})
            mesh_preset = params.get("mesh", "naca_0012")
            if mesh_preset.startswith("naca_"):
                naca_digits = mesh_preset.replace("naca_", "")
                if len(naca_digits) != 4 or not naca_digits.isdigit():
                    naca_digits = "0012"
                mesh_content = _generate_naca_mesh(naca_digits)
            else:
                mesh_content = _generate_naca_mesh("0012")

            mesh_path = os.path.join(tmpdir, "mesh.su2")
            with open(mesh_path, "w") as f:
                f.write(mesh_content)

            # Generate config
            self.update_state(state="PROGRESS", meta={"progress": 0.2, "message": "Writing configuration"})
            cfg_content = _generate_config(sim_type, params)
            cfg_path = os.path.join(tmpdir, "config.cfg")
            with open(cfg_path, "w") as f:
                f.write(cfg_content)

            # Run SU2
            self.update_state(state="PROGRESS", meta={"progress": 0.3, "message": "Running SU2_CFD solver"})
            start = time.time()
            proc = subprocess.run(
                ["SU2_CFD", "config.cfg"],
                capture_output=True,
                text=True,
                timeout=550,
                cwd=tmpdir,
            )
            solve_time = time.time() - start

            if proc.returncode != 0:
                # Try to extract useful error
                stderr = proc.stderr[:500] if proc.stderr else ""
                stdout_tail = proc.stdout[-500:] if proc.stdout else ""
                raise RuntimeError(f"SU2_CFD failed (rc={proc.returncode}): {stderr or stdout_tail}")

            self.update_state(state="PROGRESS", meta={"progress": 0.7, "message": "Parsing results"})

            # Parse convergence history
            history_path = os.path.join(tmpdir, "history.csv")
            iterations, rms_density, cl_values, cd_values = _parse_history_csv(history_path)

            # Final Cl, Cd
            cl = cl_values[-1] if cl_values else 0.0
            cd = cd_values[-1] if cd_values else 0.0

            # Build field data from surface if available
            field_data = []
            x_grid = []
            y_grid = []
            cp_distribution = []

            surface_path = os.path.join(tmpdir, "surface_flow.csv")
            if os.path.exists(surface_path):
                with open(surface_path) as f:
                    header = None
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        if header is None:
                            header = [h.strip().strip('"') for h in line.split(",")]
                            continue
                        parts = line.split(",")
                        try:
                            row = {h: float(parts[i].strip().strip('"'))
                                   for i, h in enumerate(header) if i < len(parts)}
                            x_grid.append(row.get("x", 0.0))
                            y_grid.append(row.get("y", 0.0))
                            cp = row.get("Pressure_Coefficient", row.get("Cp", 0.0))
                            cp_distribution.append(cp)
                        except (ValueError, KeyError):
                            continue

            # Build 2D field data (pressure) from volume output if available
            flow_path = os.path.join(tmpdir, "flow.csv")
            if os.path.exists(flow_path):
                fx, fy, fp = [], [], []
                with open(flow_path) as f:
                    header = None
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        if header is None:
                            header = [h.strip().strip('"') for h in line.split(",")]
                            continue
                        parts = line.split(",")
                        try:
                            row = {h: float(parts[i].strip().strip('"'))
                                   for i, h in enumerate(header) if i < len(parts)}
                            fx.append(row.get("x", 0.0))
                            fy.append(row.get("y", 0.0))
                            fp.append(row.get("Pressure", row.get("Mach", 0.0)))
                        except (ValueError, KeyError):
                            continue

                if fx:
                    # Interpolate onto a regular grid for FieldPlot
                    from scipy.interpolate import griddata
                    nx_out, ny_out = 64, 64
                    xi = np.linspace(min(fx), max(fx), nx_out)
                    yi = np.linspace(min(fy), max(fy), ny_out)
                    xi_grid, yi_grid = np.meshgrid(xi, yi)
                    zi = griddata(
                        np.column_stack([fx, fy]), fp,
                        (xi_grid, yi_grid), method="linear", fill_value=0.0,
                    )
                    field_data = zi.tolist()
                    x_grid = xi.tolist()
                    y_grid = yi.tolist()

            result_data = {
                "tool": "su2",
                "simulation_type": sim_type,
                "problem_type": "cfd",
                "cl": cl,
                "cd": cd,
                "cp_distribution": cp_distribution,
                "field_data": field_data,
                "x_grid": x_grid,
                "y_grid": y_grid,
                "convergence_history": {
                    "iterations": iterations,
                    "rms_density": rms_density,
                    "cl": cl_values,
                    "cd": cd_values,
                },
                "mach_number": params.get("mach_number", 0.8),
                "angle_of_attack": params.get("angle_of_attack", 1.25),
                "solve_time": solve_time,
                "n_iterations": len(iterations),
            }

    except Exception as e:
        self.update_state(state="FAILURE", meta={"message": str(e)})
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    _save_result(self.request.id, "su2", result_data, project, label)
    return result_data
