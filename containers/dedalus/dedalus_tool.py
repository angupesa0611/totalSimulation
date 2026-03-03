import json
import os
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


def _downsample(field, max_size=64):
    """Downsample array for JSON serialization."""
    if field.ndim == 1:
        if field.shape[0] <= max_size:
            return field
        step = max(1, field.shape[0] // max_size)
        return field[::step]
    if field.shape[0] <= max_size and field.shape[1] <= max_size:
        return field
    step_y = max(1, field.shape[0] // max_size)
    step_x = max(1, field.shape[1] // max_size)
    return field[::step_y, ::step_x]


def _run_rayleigh_benard(params):
    """Rayleigh-Benard convection using Dedalus 3."""
    import dedalus.public as d3

    Ra = params.get("rayleigh", 1e6)
    Pr = params.get("prandtl", 1)
    nx, nz = params.get("resolution", [128, 64])
    aspect = params.get("aspect_ratio", 2)
    end_time = params.get("end_time", 1.0)
    dt = params.get("dt", 1e-3)

    Lx = aspect
    Lz = 1

    # Bases
    coords = d3.CartesianCoordinates('x', 'z')
    dist = d3.Distributor(coords, dtype=np.float64)
    xbasis = d3.RealFourier(coords['x'], size=nx, bounds=(0, Lx), dealias=3/2)
    zbasis = d3.ChebyshevT(coords['z'], size=nz, bounds=(0, Lz), dealias=3/2)

    # Fields
    p = dist.Field(name='p', bases=(xbasis, zbasis))
    b = dist.Field(name='b', bases=(xbasis, zbasis))
    u = dist.VectorField(coords, name='u', bases=(xbasis, zbasis))
    tau_p = dist.Field(name='tau_p')
    tau_b1 = dist.Field(name='tau_b1', bases=xbasis)
    tau_b2 = dist.Field(name='tau_b2', bases=xbasis)
    tau_u1 = dist.VectorField(coords, name='tau_u1', bases=xbasis)
    tau_u2 = dist.VectorField(coords, name='tau_u2', bases=xbasis)

    # Substitutions
    kappa = (Ra * Pr)**(-1/2)
    nu_val = (Ra / Pr)**(-1/2)
    x, z = dist.local_grids(xbasis, zbasis)
    ex, ez = coords.unit_vector_fields(dist)
    lift_basis = zbasis.derivative_basis(1)
    lift = lambda A: d3.Lift(A, lift_basis, -1)

    # Problem
    problem = d3.IVP([p, b, u, tau_p, tau_b1, tau_b2, tau_u1, tau_u2], namespace=locals())
    problem.add_equation("trace(grad(u)) + tau_p = 0")
    problem.add_equation("dt(b) - kappa*div(grad(b)) + lift(tau_b1) + lift(tau_b2) = - u@grad(b)")
    problem.add_equation("dt(u) - nu_val*div(grad(u)) + grad(p) - b*ez + lift(tau_u1) + lift(tau_u2) = - u@grad(u)")
    problem.add_equation("b(z=0) = 1")
    problem.add_equation("b(z=Lz) = 0")
    problem.add_equation("u(z=0) = 0")
    problem.add_equation("u(z=Lz) = 0")
    problem.add_equation("integ(p) = 0")

    # Solver
    solver = problem.build_solver(d3.RK222)
    solver.stop_sim_time = end_time

    # Initial conditions — small perturbation
    b['g'] = 1 - z + 0.1 * np.sin(2 * np.pi * x / Lx) * np.sin(np.pi * z / Lz) * np.random.randn(*b['g'].shape) * 0.01

    snapshots = []
    energy_times = []
    energy_values = []
    snapshot_interval = max(1, int(end_time / dt / 10))
    step = 0

    while solver.proceed:
        solver.step(dt)
        step += 1

        # Track energy
        if step % 10 == 0:
            ke = float(np.sum(u['g']**2))
            energy_times.append(float(solver.sim_time))
            energy_values.append(ke)

        if step % snapshot_interval == 0:
            b_data = _downsample(b['g'])
            snapshots.append({"time": float(solver.sim_time), "field_data": b_data.tolist()})

    # Final field
    final_b = _downsample(b['g'])
    x_grid = np.linspace(0, Lx, final_b.shape[0]).tolist()
    z_grid = np.linspace(0, Lz, final_b.shape[1]).tolist()

    # Nusselt number approximation
    b_top = b['g'][:, -1]
    nusselt = float(1 + np.mean(np.abs(np.gradient(b_top))))

    return {
        "tool": "dedalus",
        "simulation_type": "rayleigh_benard",
        "problem_type": "convection",
        "field_data": final_b.tolist(),
        "x_grid": x_grid,
        "y_grid": z_grid,
        "snapshots": snapshots,
        "energy_timeseries": {"times": energy_times, "energy": energy_values},
        "nusselt_number": nusselt,
        "rayleigh": Ra,
        "prandtl": Pr,
        "resolution": [nx, nz],
        "total_time": float(solver.sim_time),
    }


def _run_diffusion_1d(params):
    """1D diffusion equation using Dedalus 3."""
    import dedalus.public as d3

    diffusivity = params.get("diffusivity", 0.1)
    n_modes = params.get("n_modes", 64)
    domain_size = params.get("domain_size", 2 * np.pi)
    end_time = params.get("end_time", 1.0)
    init_cond = params.get("initial_condition", "gaussian")

    coords = d3.CartesianCoordinates('x')
    dist = d3.Distributor(coords, dtype=np.float64)
    xbasis = d3.RealFourier(coords['x'], size=n_modes, bounds=(0, domain_size), dealias=3/2)

    u = dist.Field(name='u', bases=xbasis)
    x = dist.local_grids(xbasis)[0]

    problem = d3.IVP([u], namespace=locals())
    problem.add_equation("dt(u) - diffusivity*dx(dx(u)) = 0")

    solver = problem.build_solver(d3.RK222)
    solver.stop_sim_time = end_time

    # Initial condition
    if init_cond == "gaussian":
        u['g'] = np.exp(-((x - domain_size / 2)**2) / (0.1 * domain_size)**2)
    elif init_cond == "sine":
        u['g'] = np.sin(2 * np.pi * x / domain_size)
    elif init_cond == "step":
        u['g'] = np.where(x < domain_size / 2, 1.0, 0.0)

    dt = params.get("dt", 0.001)
    snapshots = []
    energy_times = []
    energy_values = []
    step = 0
    snapshot_interval = max(1, int(end_time / dt / 10))

    while solver.proceed:
        solver.step(dt)
        step += 1

        if step % 10 == 0:
            energy_times.append(float(solver.sim_time))
            energy_values.append(float(np.sum(u['g']**2)))

        if step % snapshot_interval == 0:
            snapshots.append({"time": float(solver.sim_time), "field_data": u['g'].tolist()})

    x_grid = np.linspace(0, domain_size, len(u['g'])).tolist()

    return {
        "tool": "dedalus",
        "simulation_type": "diffusion_1d",
        "problem_type": "diffusion",
        "field_data": u['g'].tolist(),
        "x_grid": x_grid,
        "y_grid": [],
        "snapshots": snapshots,
        "energy_timeseries": {"times": energy_times, "energy": energy_values},
        "spectral_coefficients": np.abs(u['c']).tolist(),
        "total_time": float(solver.sim_time),
    }


def _run_wave_1d(params):
    """1D wave equation using Dedalus 3."""
    import dedalus.public as d3

    wave_speed = params.get("wave_speed", 1.0)
    n_modes = params.get("n_modes", 64)
    domain_size = params.get("domain_size", 2 * np.pi)
    end_time = params.get("end_time", 2.0)

    coords = d3.CartesianCoordinates('x')
    dist = d3.Distributor(coords, dtype=np.float64)
    xbasis = d3.RealFourier(coords['x'], size=n_modes, bounds=(0, domain_size), dealias=3/2)

    u = dist.Field(name='u', bases=xbasis)
    v = dist.Field(name='v', bases=xbasis)  # du/dt
    c2 = wave_speed**2
    x = dist.local_grids(xbasis)[0]

    problem = d3.IVP([u, v], namespace=locals())
    problem.add_equation("dt(u) - v = 0")
    problem.add_equation("dt(v) - c2*dx(dx(u)) = 0")

    solver = problem.build_solver(d3.RK222)
    solver.stop_sim_time = end_time

    # Gaussian initial displacement, zero velocity
    u['g'] = np.exp(-((x - domain_size / 2)**2) / (0.05 * domain_size)**2)
    v['g'] = 0

    dt = params.get("dt", 0.001)
    snapshots = []
    energy_times = []
    energy_values = []
    step = 0
    snapshot_interval = max(1, int(end_time / dt / 10))

    while solver.proceed:
        solver.step(dt)
        step += 1

        if step % 10 == 0:
            energy = float(np.sum(u['g']**2 + v['g']**2))
            energy_times.append(float(solver.sim_time))
            energy_values.append(energy)

        if step % snapshot_interval == 0:
            snapshots.append({"time": float(solver.sim_time), "field_data": u['g'].tolist()})

    x_grid = np.linspace(0, domain_size, len(u['g'])).tolist()

    return {
        "tool": "dedalus",
        "simulation_type": "wave_1d",
        "problem_type": "wave",
        "field_data": u['g'].tolist(),
        "x_grid": x_grid,
        "y_grid": [],
        "snapshots": snapshots,
        "energy_timeseries": {"times": energy_times, "energy": energy_values},
        "spectral_coefficients": np.abs(u['c']).tolist(),
        "total_time": float(solver.sim_time),
    }


@app.task(name="tools.dedalus_tool.run_dedalus", bind=True, soft_time_limit=600)
def run_dedalus(self, params, project="_default", label=None):
    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting Dedalus simulation"})

    sim_type = params.get("simulation_type", "rayleigh_benard")

    try:
        self.update_state(state="PROGRESS", meta={"progress": 0.1, "message": f"Running {sim_type}"})

        if sim_type == "rayleigh_benard":
            result = _run_rayleigh_benard(params)
        elif sim_type == "diffusion_1d":
            result = _run_diffusion_1d(params)
        elif sim_type == "wave_1d":
            result = _run_wave_1d(params)
        else:
            raise ValueError(f"Unknown simulation_type: {sim_type}")

    except Exception as e:
        self.update_state(state="FAILURE", meta={"message": str(e)})
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    _save_result(self.request.id, "dedalus", result, project, label)

    return result
