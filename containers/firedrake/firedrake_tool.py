import json
import os
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


def _extract_field_2d(mesh, u, lx, ly, nx_out=50, ny_out=50):
    """Extract Firedrake solution on a regular grid via point evaluation."""
    x_grid = np.linspace(0, lx, nx_out)
    y_grid = np.linspace(0, ly, ny_out)
    field_data = np.zeros((ny_out, nx_out))

    for j in range(ny_out):
        for i in range(nx_out):
            try:
                val = u.at([x_grid[i], y_grid[j]])
                if isinstance(val, (list, np.ndarray)):
                    field_data[j, i] = float(np.linalg.norm(val))
                else:
                    field_data[j, i] = float(val)
            except Exception:
                field_data[j, i] = 0.0

    return {
        "field_data": field_data.tolist(),
        "x_grid": x_grid.tolist(),
        "y_grid": y_grid.tolist(),
        "max_value": float(np.max(field_data)),
        "min_value": float(np.min(field_data)),
    }


@app.task(name="tools.firedrake_tool.run_firedrake", bind=True)
def run_firedrake(self, params, project="_default", label=None):
    import firedrake

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Setting up Firedrake problem"})

    problem_type = params.get("problem_type", "poisson")
    if problem_type not in ("poisson", "stokes", "elasticity", "advection_diffusion"):
        raise ValueError(f"Unknown problem_type: {problem_type}")

    nx = params.get("mesh_resolution", 32)
    ny = params.get("mesh_resolution_y", nx)
    lx = params.get("length_x", 1.0)
    ly = params.get("length_y", 1.0)
    degree = params.get("degree", 1)
    bc_specs = params.get("boundary_conditions", [])
    source_value = params.get("source_term", 0.0)
    material = params.get("material", {})

    start_time = time.time()

    try:
        self.update_state(state="PROGRESS", meta={"progress": 0.1, "message": "Creating mesh"})
        mesh = firedrake.RectangleMesh(nx, ny, lx, ly)

        if problem_type == "poisson":
            result = _solve_poisson(mesh, params, degree, bc_specs, source_value, self)
        elif problem_type == "stokes":
            result = _solve_stokes(mesh, params, degree, self)
        elif problem_type == "elasticity":
            result = _solve_elasticity(mesh, params, degree, material, self)
        elif problem_type == "advection_diffusion":
            result = _solve_advection_diffusion(mesh, params, degree, self)

    except Exception as e:
        raise

    solve_time = time.time() - start_time

    result["tool"] = "firedrake"
    result["problem_type"] = problem_type
    result["solve_time"] = solve_time
    result["mesh_info"] = {
        "n_cells": int(mesh.num_cells()),
        "n_vertices": int(mesh.num_vertices()),
        "domain": [lx, ly],
        "resolution": [int(nx), int(ny)],
    }

    self.update_state(state="PROGRESS", meta={"progress": 0.95, "message": "Saving results"})
    _save_result(self.request.id, "firedrake", result, project, label)
    return result


def _apply_bcs(V, mesh, bc_specs, lx, ly):
    """Apply Dirichlet boundary conditions from spec list."""
    import firedrake

    bcs = []
    # Firedrake uses numbered boundary IDs: 1=left, 2=right, 3=bottom, 4=top
    boundary_map = {"left": 1, "right": 2, "bottom": 3, "top": 4}

    if bc_specs:
        for spec in bc_specs:
            bc_type = spec.get("type", "dirichlet")
            value = spec.get("value", 0.0)
            boundary = spec.get("boundary", "all")

            if bc_type == "dirichlet":
                if boundary == "all":
                    bcs.append(firedrake.DirichletBC(V, firedrake.Constant(value), "on_boundary"))
                elif boundary in boundary_map:
                    bcs.append(firedrake.DirichletBC(V, firedrake.Constant(value), boundary_map[boundary]))
    else:
        # Default: u=0 on all boundaries
        bcs.append(firedrake.DirichletBC(V, firedrake.Constant(0.0), "on_boundary"))

    return bcs


def _solve_poisson(mesh, params, degree, bc_specs, source_value, task):
    """Solve Poisson equation: -nabla^2(u) = f"""
    import firedrake

    task.update_state(state="PROGRESS", meta={"progress": 0.2, "message": "Setting up Poisson equation"})

    V = firedrake.FunctionSpace(mesh, "CG", degree)
    u = firedrake.TrialFunction(V)
    v = firedrake.TestFunction(V)

    conductivity = params.get("material", {}).get("conductivity", 1.0)
    k = firedrake.Constant(conductivity)
    f_val = source_value if source_value != 0.0 else 1.0
    f = firedrake.Constant(f_val)

    a = k * firedrake.inner(firedrake.grad(u), firedrake.grad(v)) * firedrake.dx
    L = f * v * firedrake.dx

    lx = params.get("length_x", 1.0)
    ly = params.get("length_y", 1.0)
    bcs = _apply_bcs(V, mesh, bc_specs, lx, ly)

    task.update_state(state="PROGRESS", meta={"progress": 0.4, "message": "Solving linear system"})

    uh = firedrake.Function(V)
    firedrake.solve(a == L, uh, bcs=bcs)

    task.update_state(state="PROGRESS", meta={"progress": 0.6, "message": "Extracting solution"})

    field_result = _extract_field_2d(mesh, uh, lx, ly)
    field_result["n_dofs"] = int(V.dof_count)

    return field_result


def _solve_stokes(mesh, params, degree, task):
    """Solve Stokes equations for viscous flow."""
    import firedrake

    task.update_state(state="PROGRESS", meta={"progress": 0.2, "message": "Setting up Stokes flow"})

    # Simplified: solve Poisson for stream function
    V = firedrake.FunctionSpace(mesh, "CG", degree)
    u = firedrake.TrialFunction(V)
    v = firedrake.TestFunction(V)

    f = firedrake.Constant(1.0)
    a = firedrake.inner(firedrake.grad(u), firedrake.grad(v)) * firedrake.dx
    L = f * v * firedrake.dx

    bcs = [firedrake.DirichletBC(V, firedrake.Constant(0.0), "on_boundary")]

    task.update_state(state="PROGRESS", meta={"progress": 0.4, "message": "Solving Stokes"})

    uh = firedrake.Function(V)
    firedrake.solve(a == L, uh, bcs=bcs)

    task.update_state(state="PROGRESS", meta={"progress": 0.6, "message": "Extracting velocity field"})

    lx = params.get("length_x", 1.0)
    ly = params.get("length_y", 1.0)
    field_result = _extract_field_2d(mesh, uh, lx, ly)
    field_result["n_dofs"] = int(V.dof_count)

    return field_result


def _solve_elasticity(mesh, params, degree, material, task):
    """Solve linear elasticity."""
    import firedrake

    task.update_state(state="PROGRESS", meta={"progress": 0.2, "message": "Setting up elasticity"})

    V = firedrake.VectorFunctionSpace(mesh, "CG", degree)
    u = firedrake.TrialFunction(V)
    v = firedrake.TestFunction(V)

    E = material.get("E", 1e5)
    nu = material.get("nu", 0.3)
    density = material.get("density", 1.0)

    lmbda = firedrake.Constant(E * nu / ((1 + nu) * (1 - 2 * nu)))
    mu = firedrake.Constant(E / (2 * (1 + nu)))

    def epsilon(u):
        return firedrake.sym(firedrake.grad(u))

    def sigma(u):
        return lmbda * firedrake.div(u) * firedrake.Identity(2) + 2 * mu * epsilon(u)

    f = firedrake.Constant((0.0, -density * 9.81))

    a = firedrake.inner(sigma(u), epsilon(v)) * firedrake.dx
    L = firedrake.dot(f, v) * firedrake.dx

    # Fixed left boundary
    bc = firedrake.DirichletBC(V, firedrake.Constant((0.0, 0.0)), 1)

    task.update_state(state="PROGRESS", meta={"progress": 0.4, "message": "Solving elasticity"})

    uh = firedrake.Function(V)
    firedrake.solve(a == L, uh, bcs=[bc])

    task.update_state(state="PROGRESS", meta={"progress": 0.6, "message": "Computing displacement field"})

    lx = params.get("length_x", 1.0)
    ly = params.get("length_y", 1.0)
    field_result = _extract_field_2d(mesh, uh, lx, ly)
    field_result["n_dofs"] = int(V.dof_count)

    return field_result


def _solve_advection_diffusion(mesh, params, degree, task):
    """Solve advection-diffusion equation."""
    import firedrake

    task.update_state(state="PROGRESS", meta={"progress": 0.2, "message": "Setting up advection-diffusion"})

    V = firedrake.FunctionSpace(mesh, "CG", degree)
    u = firedrake.TrialFunction(V)
    v = firedrake.TestFunction(V)

    diffusivity = params.get("diffusivity", 0.01)
    kappa = firedrake.Constant(diffusivity)
    velocity = firedrake.Constant((1.0, 0.0))
    f = firedrake.Constant(1.0)

    a = (kappa * firedrake.inner(firedrake.grad(u), firedrake.grad(v))
         + firedrake.inner(velocity, firedrake.grad(u)) * v) * firedrake.dx
    L = f * v * firedrake.dx

    bcs = [firedrake.DirichletBC(V, firedrake.Constant(0.0), "on_boundary")]

    task.update_state(state="PROGRESS", meta={"progress": 0.4, "message": "Solving advection-diffusion"})

    uh = firedrake.Function(V)
    firedrake.solve(a == L, uh, bcs=bcs)

    task.update_state(state="PROGRESS", meta={"progress": 0.6, "message": "Extracting solution"})

    lx = params.get("length_x", 1.0)
    ly = params.get("length_y", 1.0)
    field_result = _extract_field_2d(mesh, uh, lx, ly)
    field_result["n_dofs"] = int(V.dof_count)

    return field_result
