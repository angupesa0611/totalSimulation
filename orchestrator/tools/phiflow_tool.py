from typing import Any
import numpy as np
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result


class PhiFlowTool(SimulationTool):
    name = "PhiFlow"
    key = "phiflow"
    layer = "fluid-dynamics"

    SIMULATION_TYPES = {"smoke_simulation", "fluid_2d", "diffusion", "wave_equation"}

    BACKENDS = {"numpy", "jax"}

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type", "smoke_simulation")
        if sim_type not in self.SIMULATION_TYPES:
            raise ValueError(f"Unknown simulation_type: {sim_type}. Supported: {self.SIMULATION_TYPES}")

        backend = params.get("backend", "numpy")
        if backend not in self.BACKENDS:
            raise ValueError(f"Unknown backend: {backend}. Available: {self.BACKENDS}")

        params.setdefault("simulation_type", sim_type)
        params.setdefault("backend", backend)
        params.setdefault("dt", 0.01)
        params.setdefault("n_steps", 100)

        # Normalize split resolution fields from frontend
        if "nx" in params or "ny" in params:
            params["resolution"] = [
                params.pop("ny", 64),
                params.pop("nx", 64),
            ]
        params.setdefault("resolution", [64, 64])

        # Normalize split domain size fields from frontend
        if "lx" in params or "ly" in params:
            params["domain_size"] = [
                params.pop("ly", 1.0),
                params.pop("lx", 1.0),
            ]
        params.setdefault("domain_size", [1.0, 1.0])

        # Normalize split inflow position fields from frontend
        if "inflow_x" in params or "inflow_y" in params:
            params["inflow_position"] = [
                params.pop("inflow_x", 0.5),
                params.pop("inflow_y", 0.1),
            ]

        return params

    def _select_backend(self, backend):
        """Activate the PhiFlow backend before simulation."""
        if backend == "jax":
            from phi import jax as phi_jax  # noqa: F401 — activates JAX backend
        # numpy is the default — no activation needed

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        params = self.validate_params(params)
        self._select_backend(params.get("backend", "numpy"))
        sim_type = params["simulation_type"]

        if sim_type == "smoke_simulation":
            return self._run_smoke(params)
        elif sim_type == "fluid_2d":
            return self._run_fluid_2d(params)
        elif sim_type == "diffusion":
            return self._run_diffusion(params)
        elif sim_type == "wave_equation":
            return self._run_wave(params)

    def _downsample(self, field, max_size=64):
        """Downsample a 2D array to max_size x max_size for JSON serialization."""
        if field.shape[0] <= max_size and field.shape[1] <= max_size:
            return field
        step_y = max(1, field.shape[0] // max_size)
        step_x = max(1, field.shape[1] // max_size)
        return field[::step_y, ::step_x]

    def _run_smoke(self, params):
        from phi.flow import CenteredGrid, StaggeredGrid, Box, extrapolation, advect, diffuse
        from phi import math

        res_y, res_x = params["resolution"]
        ly, lx = params["domain_size"]
        dt = params["dt"]
        n_steps = params["n_steps"]
        inflow_pos = params.get("inflow_position", [0.5, 0.1])
        inflow_radius = params.get("inflow_radius", 0.05)
        buoyancy = params.get("buoyancy", 1.0)

        # Initialize density and velocity fields
        density = CenteredGrid(0, extrapolation.BOUNDARY, x=res_x, y=res_y,
                               bounds=Box(x=lx, y=ly))
        velocity = StaggeredGrid(0, extrapolation.ZERO, x=res_x, y=res_y,
                                 bounds=Box(x=lx, y=ly))

        # Inflow mask
        inflow = CenteredGrid(
            lambda x: math.exp(-0.5 * ((x[0] - inflow_pos[0])**2 + (x[1] - inflow_pos[1])**2) / inflow_radius**2),
            extrapolation.BOUNDARY, x=res_x, y=res_y,
            bounds=Box(x=lx, y=ly)
        )

        snapshots = []
        energy_steps = []
        energy_values = []
        snapshot_interval = max(1, n_steps // 10)

        for step in range(n_steps):
            density = advect.mac_cormack(density, velocity, dt)
            density += dt * inflow

            # Buoyancy force
            buoyancy_force = (density * (0, buoyancy)).at(velocity)
            velocity += dt * buoyancy_force

            velocity = diffuse.explicit(velocity, 0.1, dt)
            velocity, _ = velocity.with_extrapolation(extrapolation.ZERO), None

            # Track energy
            vel_np = velocity.staggered_tensor().numpy(velocity.staggered_tensor().shape)
            energy = float(np.sum(vel_np**2)) if vel_np.size > 0 else 0.0
            energy_steps.append(step)
            energy_values.append(energy)

            if step % snapshot_interval == 0 or step == n_steps - 1:
                d_np = density.values.numpy(density.values.shape)
                d_ds = self._downsample(d_np)
                snapshots.append({"step": step, "field_data": d_ds.tolist()})

        # Final field
        final_density = density.values.numpy(density.values.shape)
        final_ds = self._downsample(final_density)

        x_grid = np.linspace(0, lx, final_ds.shape[1]).tolist()
        y_grid = np.linspace(0, ly, final_ds.shape[0]).tolist()

        return {
            "tool": "phiflow",
            "simulation_type": "smoke_simulation",
            "problem_type": "smoke",
            "field_data": final_ds.tolist(),
            "x_grid": x_grid,
            "y_grid": y_grid,
            "snapshots": snapshots,
            "domain_size": params["domain_size"],
            "resolution": params["resolution"],
            "total_time": float(n_steps * dt),
            "energy_timeseries": {"steps": energy_steps, "energy": energy_values},
        }

    def _run_fluid_2d(self, params):
        from phi.flow import CenteredGrid, StaggeredGrid, Box, extrapolation, advect, diffuse, fluid
        from phi import math

        res_y, res_x = params["resolution"]
        ly, lx = params["domain_size"]
        dt = params["dt"]
        n_steps = params["n_steps"]
        viscosity = params.get("viscosity", 0.01)
        init_vel = params.get("initial_velocity", "vortex")

        # Initialize velocity
        if init_vel == "vortex":
            def vortex_fn(x):
                cx, cy = lx / 2, ly / 2
                dx_v = x[0] - cx
                dy_v = x[1] - cy
                r = math.sqrt(dx_v**2 + dy_v**2) + 1e-6
                strength = math.exp(-r**2 / (0.1 * lx)**2)
                return math.stack([-dy_v * strength / r, dx_v * strength / r], dim='vector')
            velocity = StaggeredGrid(vortex_fn, extrapolation.ZERO, x=res_x, y=res_y,
                                     bounds=Box(x=lx, y=ly))
        else:
            velocity = StaggeredGrid(0, extrapolation.ZERO, x=res_x, y=res_y,
                                     bounds=Box(x=lx, y=ly))

        snapshots = []
        energy_steps = []
        energy_values = []
        snapshot_interval = max(1, n_steps // 10)

        for step in range(n_steps):
            velocity = advect.semi_lagrangian(velocity, velocity, dt)
            velocity = diffuse.explicit(velocity, viscosity, dt)
            velocity, pressure = fluid.make_incompressible(velocity)

            vel_np = velocity.staggered_tensor().numpy(velocity.staggered_tensor().shape)
            energy = float(np.sum(vel_np**2)) if vel_np.size > 0 else 0.0
            energy_steps.append(step)
            energy_values.append(energy)

            if step % snapshot_interval == 0 or step == n_steps - 1:
                # Store velocity magnitude as field data
                vel_centered = velocity.at_centers()
                vel_mag = math.sqrt(math.sum(vel_centered.values**2, dim='vector'))
                mag_np = vel_mag.numpy(vel_mag.shape)
                snapshots.append({"step": step, "field_data": self._downsample(mag_np).tolist()})

        # Final velocity magnitude
        vel_centered = velocity.at_centers()
        vel_mag = math.sqrt(math.sum(vel_centered.values**2, dim='vector'))
        final_mag = vel_mag.numpy(vel_mag.shape)
        final_ds = self._downsample(final_mag)

        x_grid = np.linspace(0, lx, final_ds.shape[1]).tolist()
        y_grid = np.linspace(0, ly, final_ds.shape[0]).tolist()

        return {
            "tool": "phiflow",
            "simulation_type": "fluid_2d",
            "problem_type": "fluid",
            "field_data": final_ds.tolist(),
            "x_grid": x_grid,
            "y_grid": y_grid,
            "snapshots": snapshots,
            "domain_size": params["domain_size"],
            "resolution": params["resolution"],
            "total_time": float(n_steps * dt),
            "energy_timeseries": {"steps": energy_steps, "energy": energy_values},
        }

    def _run_diffusion(self, params):
        from phi.flow import CenteredGrid, Box, extrapolation, diffuse
        from phi import math

        res_y, res_x = params["resolution"]
        ly, lx = params["domain_size"]
        dt = params["dt"]
        n_steps = params["n_steps"]
        diffusivity = params.get("diffusivity", 0.1)
        init_cond = params.get("initial_condition", "gaussian")

        if init_cond == "gaussian":
            field = CenteredGrid(
                lambda x: math.exp(-((x[0] - lx/2)**2 + (x[1] - ly/2)**2) / (0.05 * lx)**2),
                extrapolation.ZERO, x=res_x, y=res_y, bounds=Box(x=lx, y=ly))
        elif init_cond == "step":
            field = CenteredGrid(
                lambda x: math.cast(x[0] < lx/2, float),
                extrapolation.ZERO, x=res_x, y=res_y, bounds=Box(x=lx, y=ly))
        else:
            field = CenteredGrid(
                lambda x: math.random_normal(x.shape),
                extrapolation.ZERO, x=res_x, y=res_y, bounds=Box(x=lx, y=ly))

        snapshots = []
        energy_steps = []
        energy_values = []
        snapshot_interval = max(1, n_steps // 10)

        for step in range(n_steps):
            field = diffuse.explicit(field, diffusivity, dt)

            f_np = field.values.numpy(field.values.shape)
            energy = float(np.sum(f_np**2))
            energy_steps.append(step)
            energy_values.append(energy)

            if step % snapshot_interval == 0 or step == n_steps - 1:
                snapshots.append({"step": step, "field_data": self._downsample(f_np).tolist()})

        final_field = field.values.numpy(field.values.shape)
        final_ds = self._downsample(final_field)
        x_grid = np.linspace(0, lx, final_ds.shape[1]).tolist()
        y_grid = np.linspace(0, ly, final_ds.shape[0]).tolist()

        return {
            "tool": "phiflow",
            "simulation_type": "diffusion",
            "problem_type": "diffusion",
            "field_data": final_ds.tolist(),
            "x_grid": x_grid,
            "y_grid": y_grid,
            "snapshots": snapshots,
            "domain_size": params["domain_size"],
            "resolution": params["resolution"],
            "total_time": float(n_steps * dt),
            "energy_timeseries": {"steps": energy_steps, "energy": energy_values},
        }

    def _run_wave(self, params):
        from phi.flow import CenteredGrid, Box, extrapolation
        from phi import math as phi_math

        res_y, res_x = params["resolution"]
        ly, lx = params["domain_size"]
        dt = params["dt"]
        n_steps = params["n_steps"]
        wave_speed = params.get("wave_speed", 1.0)
        init_cond = params.get("initial_condition", "gaussian")

        # Initial displacement via PhiFlow CenteredGrid
        if init_cond == "gaussian":
            u = CenteredGrid(
                lambda x: phi_math.exp(-((x[0] - lx / 2) ** 2 + (x[1] - ly / 2) ** 2) / (0.05 * lx) ** 2),
                extrapolation.ZERO, x=res_x, y=res_y, bounds=Box(x=lx, y=ly),
            )
        elif init_cond == "standing":
            u = CenteredGrid(
                lambda x: phi_math.sin(2 * 3.141592653589793 * x[0] / lx) * phi_math.sin(2 * 3.141592653589793 * x[1] / ly),
                extrapolation.ZERO, x=res_x, y=res_y, bounds=Box(x=lx, y=ly),
            )
        else:
            u = CenteredGrid(
                lambda x: phi_math.exp(-((x[0] - lx / 2) ** 2 + (x[1] - ly / 2) ** 2) / (0.05 * lx) ** 2),
                extrapolation.ZERO, x=res_x, y=res_y, bounds=Box(x=lx, y=ly),
            )

        # Leapfrog: u_prev = u at t=0 (zero initial velocity)
        u_prev = u

        c2_dt2 = wave_speed ** 2 * dt ** 2

        snapshots = []
        energy_steps = []
        energy_values = []
        snapshot_interval = max(1, n_steps // 10)

        for step in range(n_steps):
            # Wave equation leapfrog: u_new = 2*u - u_prev + c^2*dt^2*laplacian(u)
            lap = u.laplace(None)
            u_new = 2 * u - u_prev + c2_dt2 * lap
            u_prev = u
            u = u_new

            u_np = u.values.numpy(u.values.shape)
            energy = float(np.sum(u_np ** 2))
            energy_steps.append(step)
            energy_values.append(energy)

            if step % snapshot_interval == 0 or step == n_steps - 1:
                snapshots.append({"step": step, "field_data": self._downsample(u_np).tolist()})

        final_np = u.values.numpy(u.values.shape)
        final_ds = self._downsample(final_np)
        x_grid = np.linspace(0, lx, final_ds.shape[1]).tolist()
        y_grid = np.linspace(0, ly, final_ds.shape[0]).tolist()

        return {
            "tool": "phiflow",
            "simulation_type": "wave_equation",
            "problem_type": "wave",
            "field_data": final_ds.tolist(),
            "x_grid": x_grid,
            "y_grid": y_grid,
            "snapshots": snapshots,
            "domain_size": params["domain_size"],
            "resolution": params["resolution"],
            "total_time": float(n_steps * dt),
            "energy_timeseries": {"steps": energy_steps, "energy": energy_values},
        }

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "smoke_simulation",
            "resolution": [64, 64],
            "domain_size": [1.0, 1.0],
            "dt": 0.01,
            "n_steps": 200,
            "inflow_position": [0.5, 0.1],
            "inflow_radius": 0.05,
            "buoyancy": 1.0,
        }


@celery_app.task(name="tools.phiflow_tool.run_phiflow", bind=True)
def run_phiflow(self, params: dict, project: str = "_default",
                label: str | None = None) -> dict:
    tool = PhiFlowTool()

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting PhiFlow simulation"})

    try:
        sim_type = params.get("simulation_type", "smoke_simulation")
        self.update_state(state="PROGRESS", meta={"progress": 0.1, "message": f"Running {sim_type}"})
        result = tool.run(params)
    except Exception as e:
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    save_result(self.request.id, "phiflow", result, project, label)

    return result
