import json
import os
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


@app.task(name="tools.fenics_tool.run_fenics", bind=True)
def run_fenics(self, params: dict, project: str = "_default",
               label: str | None = None) -> dict:
    from mpi4py import MPI
    import dolfinx
    import dolfinx.fem
    import dolfinx.mesh
    import ufl
    from dolfinx.fem.petsc import LinearProblem

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Setting up FEniCS problem"})

    problem_type = params.get("problem_type", "heat")
    if problem_type not in ("heat", "diffusion", "stokes", "elasticity"):
        raise ValueError(f"Unknown problem_type: {problem_type}")

    # Domain parameters
    nx = params.get("mesh_resolution", 32)
    ny = params.get("mesh_resolution_y", nx)
    lx = params.get("length_x", 1.0)
    ly = params.get("length_y", 1.0)
    degree = params.get("degree", 1)

    # Material properties
    material = params.get("material", {})
    conductivity = material.get("conductivity", 1.0)
    E_modulus = material.get("E", 1e5)
    nu_poisson = material.get("nu", 0.3)

    # Boundary conditions
    bc_specs = params.get("boundary_conditions", [])
    source_value = params.get("source_term", 0.0)

    start_time = time.time()

    self.update_state(state="PROGRESS", meta={"progress": 0.1, "message": "Creating mesh"})

    # Create mesh
    mesh = dolfinx.mesh.create_rectangle(
        MPI.COMM_WORLD,
        [np.array([0.0, 0.0]), np.array([lx, ly])],
        [nx, ny],
        dolfinx.mesh.CellType.triangle,
    )

    if problem_type in ("heat", "diffusion"):
        result = _solve_heat(mesh, params, conductivity, source_value, degree, bc_specs, self)
    elif problem_type == "elasticity":
        result = _solve_elasticity(mesh, params, E_modulus, nu_poisson, degree, bc_specs, self)
    elif problem_type == "stokes":
        result = _solve_stokes(mesh, params, degree, bc_specs, self)

    solve_time = time.time() - start_time

    # Extract field data on a regular grid for visualization
    self.update_state(state="PROGRESS", meta={"progress": 0.8, "message": "Extracting field data"})

    result["tool"] = "fenics"
    result["problem_type"] = problem_type
    result["solve_time"] = solve_time
    result["mesh_info"] = {
        "n_cells": mesh.topology.index_map(mesh.topology.dim).size_local,
        "n_vertices": mesh.topology.index_map(0).size_local,
        "domain": [lx, ly],
        "resolution": [nx, ny],
    }

    self.update_state(state="PROGRESS", meta={"progress": 0.95, "message": "Saving results"})
    _save_result(self.request.id, "fenics", result, project, label)

    return result


def _extract_field_2d(mesh, uh, nx_out=50, ny_out=50):
    """Extract solution values on a regular grid for visualization."""
    import dolfinx

    # Get mesh bounding box
    coords = mesh.geometry.x
    x_min, x_max = float(coords[:, 0].min()), float(coords[:, 0].max())
    y_min, y_max = float(coords[:, 1].min()), float(coords[:, 1].max())

    # Create regular grid
    x_grid = np.linspace(x_min, x_max, nx_out)
    y_grid = np.linspace(y_min, y_max, ny_out)

    # Build evaluation points
    field_data = np.zeros((ny_out, nx_out))
    points = np.zeros((nx_out * ny_out, 3))
    idx = 0
    for j in range(ny_out):
        for i in range(nx_out):
            points[idx] = [x_grid[i], y_grid[j], 0.0]
            idx += 1

    # Use DOLFINx geometry to find cells and evaluate
    bb_tree = dolfinx.geometry.bb_tree(mesh, mesh.topology.dim)
    cell_candidates = dolfinx.geometry.compute_collisions_points(bb_tree, points)
    colliding_cells = dolfinx.geometry.compute_colliding_cells(mesh, cell_candidates, points)

    for i in range(len(points)):
        cells = colliding_cells.links(i)
        if len(cells) > 0:
            val = uh.eval(points[i], cells[0])
            row = i // nx_out
            col = i % nx_out
            field_data[row, col] = float(val[0]) if len(val) > 0 else 0.0

    return {
        "field_data": field_data.tolist(),
        "x_grid": x_grid.tolist(),
        "y_grid": y_grid.tolist(),
        "max_value": float(np.max(field_data)),
        "min_value": float(np.min(field_data)),
    }


def _solve_heat(mesh, params, conductivity, source_value, degree, bc_specs, task):
    """Solve Poisson/heat equation: -k*nabla^2(u) = f"""
    import dolfinx.fem
    import ufl
    from dolfinx.fem.petsc import LinearProblem
    from petsc4py import PETSc

    task.update_state(state="PROGRESS", meta={"progress": 0.2, "message": "Setting up heat equation"})

    V = dolfinx.fem.functionspace(mesh, ("Lagrange", degree))

    # Source term
    f = dolfinx.fem.Constant(mesh, PETSc.ScalarType(source_value))
    k = dolfinx.fem.Constant(mesh, PETSc.ScalarType(conductivity))

    # Trial and test functions
    u = ufl.TrialFunction(V)
    v = ufl.TestFunction(V)

    # Bilinear and linear forms
    a = k * ufl.inner(ufl.grad(u), ufl.grad(v)) * ufl.dx
    L = f * v * ufl.dx

    # Boundary conditions
    bcs = []
    tdim = mesh.topology.dim
    fdim = tdim - 1
    mesh.topology.create_connectivity(fdim, tdim)

    if bc_specs:
        for bc_spec in bc_specs:
            bc_type = bc_spec.get("type", "dirichlet")
            bc_value = bc_spec.get("value", 0.0)
            bc_boundary = bc_spec.get("boundary", "all")

            if bc_type == "dirichlet":
                if bc_boundary == "left":
                    facets = dolfinx.mesh.locate_entities_boundary(
                        mesh, fdim, lambda x: np.isclose(x[0], 0.0))
                elif bc_boundary == "right":
                    coords_local = mesh.geometry.x
                    x_max = float(coords_local[:, 0].max())
                    facets = dolfinx.mesh.locate_entities_boundary(
                        mesh, fdim, lambda x, xm=x_max: np.isclose(x[0], xm))
                elif bc_boundary == "bottom":
                    facets = dolfinx.mesh.locate_entities_boundary(
                        mesh, fdim, lambda x: np.isclose(x[1], 0.0))
                elif bc_boundary == "top":
                    coords_local = mesh.geometry.x
                    y_max = float(coords_local[:, 1].max())
                    facets = dolfinx.mesh.locate_entities_boundary(
                        mesh, fdim, lambda x, ym=y_max: np.isclose(x[1], ym))
                else:
                    facets = dolfinx.mesh.locate_entities_boundary(
                        mesh, fdim, lambda x: np.full(x.shape[1], True))

                dofs = dolfinx.fem.locate_dofs_topological(V, fdim, facets)
                bc = dolfinx.fem.dirichletbc(
                    PETSc.ScalarType(bc_value), dofs, V)
                bcs.append(bc)
    else:
        # Default: u=0 on all boundaries, source=1
        facets = dolfinx.mesh.locate_entities_boundary(
            mesh, fdim, lambda x: np.full(x.shape[1], True))
        dofs = dolfinx.fem.locate_dofs_topological(V, fdim, facets)
        bc = dolfinx.fem.dirichletbc(PETSc.ScalarType(0.0), dofs, V)
        bcs.append(bc)
        if source_value == 0.0:
            f = dolfinx.fem.Constant(mesh, PETSc.ScalarType(1.0))
            L = f * v * ufl.dx

    task.update_state(state="PROGRESS", meta={"progress": 0.4, "message": "Solving linear system"})

    problem = LinearProblem(a, L, bcs=bcs)
    uh = problem.solve()

    task.update_state(state="PROGRESS", meta={"progress": 0.6, "message": "Extracting solution"})

    n_dofs = V.dofmap.index_map.size_local
    field_result = _extract_field_2d(mesh, uh)
    field_result["n_dofs"] = n_dofs

    return field_result


def _solve_elasticity(mesh, params, E, nu, degree, bc_specs, task):
    """Solve linear elasticity: div(sigma) = f"""
    import dolfinx.fem
    import ufl
    from dolfinx.fem.petsc import LinearProblem
    from petsc4py import PETSc

    task.update_state(state="PROGRESS", meta={"progress": 0.2, "message": "Setting up elasticity"})

    V = dolfinx.fem.functionspace(mesh, ("Lagrange", degree, (mesh.geometry.dim,)))

    # Lame parameters
    lmbda = E * nu / ((1 + nu) * (1 - 2 * nu))
    mu = E / (2 * (1 + nu))

    def epsilon(u):
        return ufl.sym(ufl.grad(u))

    def sigma(u):
        return lmbda * ufl.nabla_div(u) * ufl.Identity(len(u)) + 2 * mu * epsilon(u)

    u = ufl.TrialFunction(V)
    v = ufl.TestFunction(V)

    # Body force (gravity-like)
    density = params.get("material", {}).get("density", 1.0)
    f = dolfinx.fem.Constant(mesh, PETSc.ScalarType((0.0, -density * 9.81)))

    a = ufl.inner(sigma(u), epsilon(v)) * ufl.dx
    L = ufl.dot(f, v) * ufl.dx

    # Fixed left boundary by default
    tdim = mesh.topology.dim
    fdim = tdim - 1
    mesh.topology.create_connectivity(fdim, tdim)
    facets = dolfinx.mesh.locate_entities_boundary(
        mesh, fdim, lambda x: np.isclose(x[0], 0.0))
    dofs = dolfinx.fem.locate_dofs_topological(V, fdim, facets)
    bc = dolfinx.fem.dirichletbc(
        np.zeros(mesh.geometry.dim, dtype=PETSc.ScalarType), dofs, V)

    task.update_state(state="PROGRESS", meta={"progress": 0.4, "message": "Solving elasticity"})

    problem = LinearProblem(a, L, bcs=[bc])
    uh = problem.solve()

    task.update_state(state="PROGRESS", meta={"progress": 0.6, "message": "Computing displacement field"})

    # Extract displacement magnitude on regular grid
    n_dofs = V.dofmap.index_map.size_local
    coords = mesh.geometry.x
    x_min, x_max = float(coords[:, 0].min()), float(coords[:, 0].max())
    y_min, y_max = float(coords[:, 1].min()), float(coords[:, 1].max())

    nx_out, ny_out = 50, 50
    x_grid = np.linspace(x_min, x_max, nx_out)
    y_grid = np.linspace(y_min, y_max, ny_out)

    import dolfinx.geometry
    bb_tree = dolfinx.geometry.bb_tree(mesh, mesh.topology.dim)
    field_data = np.zeros((ny_out, nx_out))
    points = np.zeros((nx_out * ny_out, 3))
    idx = 0
    for j in range(ny_out):
        for i in range(nx_out):
            points[idx] = [x_grid[i], y_grid[j], 0.0]
            idx += 1

    cell_candidates = dolfinx.geometry.compute_collisions_points(bb_tree, points)
    colliding_cells = dolfinx.geometry.compute_colliding_cells(mesh, cell_candidates, points)

    for i in range(len(points)):
        cells = colliding_cells.links(i)
        if len(cells) > 0:
            val = uh.eval(points[i], cells[0])
            row = i // nx_out
            col = i % nx_out
            disp_mag = np.sqrt(val[0]**2 + val[1]**2) if len(val) >= 2 else 0.0
            field_data[row, col] = float(disp_mag)

    max_disp = float(np.max(field_data))

    return {
        "field_data": field_data.tolist(),
        "x_grid": x_grid.tolist(),
        "y_grid": y_grid.tolist(),
        "max_value": max_disp,
        "min_value": float(np.min(field_data)),
        "max_displacement": max_disp,
        "n_dofs": n_dofs,
    }


def _solve_stokes(mesh, params, degree, bc_specs, task):
    """Solve simplified Stokes flow as Poisson for velocity magnitude."""
    import dolfinx.fem
    import ufl
    from dolfinx.fem.petsc import LinearProblem
    from petsc4py import PETSc

    task.update_state(state="PROGRESS", meta={"progress": 0.2, "message": "Setting up Stokes flow"})

    V = dolfinx.fem.functionspace(mesh, ("Lagrange", degree))
    u = ufl.TrialFunction(V)
    v = ufl.TestFunction(V)
    f = dolfinx.fem.Constant(mesh, PETSc.ScalarType(1.0))

    a = ufl.inner(ufl.grad(u), ufl.grad(v)) * ufl.dx
    L = f * v * ufl.dx

    tdim = mesh.topology.dim
    fdim = tdim - 1
    mesh.topology.create_connectivity(fdim, tdim)
    facets = dolfinx.mesh.locate_entities_boundary(
        mesh, fdim, lambda x: np.full(x.shape[1], True))
    dofs = dolfinx.fem.locate_dofs_topological(V, fdim, facets)
    bc = dolfinx.fem.dirichletbc(PETSc.ScalarType(0.0), dofs, V)

    task.update_state(state="PROGRESS", meta={"progress": 0.4, "message": "Solving Stokes"})

    problem = LinearProblem(a, L, bcs=[bc])
    uh = problem.solve()

    task.update_state(state="PROGRESS", meta={"progress": 0.6, "message": "Extracting velocity field"})

    n_dofs = V.dofmap.index_map.size_local
    field_result = _extract_field_2d(mesh, uh)
    field_result["n_dofs"] = n_dofs

    return field_result
