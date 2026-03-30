from typing import Any
import numpy as np
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result


class CanteraTool(SimulationTool):
    name = "Cantera"
    key = "cantera"
    layer = "chemistry"

    SIMULATION_TYPES = {"ignition_delay", "reactor_timecourse", "flame_speed", "equilibrium"}

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type", "ignition_delay")
        if sim_type not in self.SIMULATION_TYPES:
            raise ValueError(f"Unknown simulation_type: {sim_type}. Supported: {self.SIMULATION_TYPES}")

        params.setdefault("simulation_type", sim_type)
        params.setdefault("mechanism", "gri30.yaml")
        params.setdefault("temperature_K", 1000.0)
        params.setdefault("pressure_atm", 1.0)
        params.setdefault("composition", "H2:2,O2:1,N2:3.76")
        params.setdefault("end_time_s", 0.001)
        params.setdefault("n_points", 200)
        params.setdefault("width_m", 0.03)
        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        params = self.validate_params(params)
        sim_type = params["simulation_type"]

        if sim_type == "ignition_delay":
            return self._run_ignition_delay(params)
        elif sim_type == "reactor_timecourse":
            return self._run_reactor_timecourse(params)
        elif sim_type == "flame_speed":
            return self._run_flame_speed(params)
        elif sim_type == "equilibrium":
            return self._run_equilibrium(params)

    def _run_ignition_delay(self, params):
        import cantera as ct

        gas = ct.Solution(params["mechanism"])
        gas.TPX = (
            params["temperature_K"],
            params["pressure_atm"] * ct.one_atm,
            params["composition"],
        )

        reactor = ct.IdealGasReactor(gas)
        sim = ct.ReactorNet([reactor])

        end_time = params["end_time_s"]
        n_points = params["n_points"]
        dt = end_time / n_points

        times = []
        temperatures = []
        pressures = []
        species_data = {}

        # Track species of interest (top 10 by mole fraction)
        initial_x = gas.X
        top_species_idx = np.argsort(initial_x)[-10:]
        top_species_names = [gas.species_name(i) for i in top_species_idx]

        for name in top_species_names:
            species_data[name] = []

        t = 0.0
        while t < end_time:
            t += dt
            sim.advance(t)
            times.append(t * 1000.0)  # convert to ms
            temperatures.append(float(reactor.T))
            pressures.append(float(reactor.thermo.P / ct.one_atm))

            for name in top_species_names:
                idx = gas.species_index(name)
                species_data[name].append(float(reactor.thermo.X[idx]))

        # Detect ignition delay via max dT/dt
        temps = np.array(temperatures)
        time_arr = np.array(times)
        if len(temps) > 2:
            dTdt = np.gradient(temps, time_arr)
            ignition_idx = int(np.argmax(dTdt))
            ignition_delay_ms = float(time_arr[ignition_idx])
        else:
            ignition_delay_ms = 0.0

        return {
            "tool": "cantera",
            "simulation_type": "ignition_delay",
            "mechanism": params["mechanism"],
            "ignition_delay_ms": ignition_delay_ms,
            "times_ms": times,
            "temperatures_K": temperatures,
            "pressures_atm": pressures,
            "species": species_data,
        }

    def _run_reactor_timecourse(self, params):
        import cantera as ct

        gas = ct.Solution(params["mechanism"])
        gas.TPX = (
            params["temperature_K"],
            params["pressure_atm"] * ct.one_atm,
            params["composition"],
        )

        reactor = ct.IdealGasReactor(gas)
        sim = ct.ReactorNet([reactor])

        end_time = params["end_time_s"]
        n_points = params["n_points"]
        dt = end_time / n_points

        times = []
        temperatures = []
        pressures = []
        species_data = {}

        initial_x = gas.X
        top_species_idx = np.argsort(initial_x)[-10:]
        top_species_names = [gas.species_name(i) for i in top_species_idx]

        for name in top_species_names:
            species_data[name] = []

        t = 0.0
        while t < end_time:
            t += dt
            sim.advance(t)
            times.append(t * 1000.0)
            temperatures.append(float(reactor.T))
            pressures.append(float(reactor.thermo.P / ct.one_atm))

            for name in top_species_names:
                idx = gas.species_index(name)
                species_data[name].append(float(reactor.thermo.X[idx]))

        return {
            "tool": "cantera",
            "simulation_type": "reactor_timecourse",
            "mechanism": params["mechanism"],
            "times_ms": times,
            "temperatures_K": temperatures,
            "pressures_atm": pressures,
            "species": species_data,
        }

    def _run_flame_speed(self, params):
        import cantera as ct

        gas = ct.Solution(params["mechanism"])
        gas.TPX = (
            params["temperature_K"],
            params["pressure_atm"] * ct.one_atm,
            params["composition"],
        )

        width = params.get("width_m", 0.03)
        flame = ct.FreeFlame(gas, width=width)
        flame.set_refine_criteria(ratio=3, slope=0.1, curve=0.1)
        flame.solve(loglevel=0, auto=True)

        flame_speed_cm_s = float(flame.velocity[0] * 100.0)

        # Temperature profile
        positions = flame.grid.tolist()
        temp_profile = flame.T.tolist()

        # Species profiles (top species)
        initial_x = gas.X
        top_species_idx = np.argsort(initial_x)[-6:]
        top_species_names = [gas.species_name(i) for i in top_species_idx]

        species_profiles = {}
        for name in top_species_names:
            idx = gas.species_index(name)
            species_profiles[name] = {
                "positions_m": positions,
                "values": flame.X[idx].tolist(),
            }

        return {
            "tool": "cantera",
            "simulation_type": "flame_speed",
            "mechanism": params["mechanism"],
            "flame_speed_cm_s": flame_speed_cm_s,
            "temperature_profile": {
                "positions_m": positions,
                "T_K": temp_profile,
            },
            "species_profiles": species_profiles,
        }

    def _run_equilibrium(self, params):
        import cantera as ct

        gas = ct.Solution(params["mechanism"])
        gas.TPX = (
            params["temperature_K"],
            params["pressure_atm"] * ct.one_atm,
            params["composition"],
        )

        gas.equilibrate("HP")

        # Get equilibrium species (filter to those with significant mole fractions)
        species_eq = {}
        for i in range(gas.n_species):
            if gas.X[i] > 1e-10:
                species_eq[gas.species_name(i)] = float(gas.X[i])

        return {
            "tool": "cantera",
            "simulation_type": "equilibrium",
            "mechanism": params["mechanism"],
            "T_eq_K": float(gas.T),
            "P_eq_atm": float(gas.P / ct.one_atm),
            "species_eq": species_eq,
        }

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "ignition_delay",
            "mechanism": "gri30.yaml",
            "temperature_K": 1200.0,
            "pressure_atm": 1.0,
            "composition": "H2:2,O2:1,N2:3.76",
            "end_time_s": 0.001,
            "n_points": 200,
        }


@celery_app.task(name="tools.cantera_tool.run_cantera", bind=True)
def run_cantera(self, params: dict, project: str = "_default",
                label: str | None = None) -> dict:
    tool = CanteraTool()

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting Cantera simulation"})

    try:
        sim_type = params.get("simulation_type", "ignition_delay")
        self.update_state(state="PROGRESS", meta={"progress": 0.1, "message": f"Running {sim_type}"})
        result = tool.run(params)
    except Exception as e:
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    save_result(self.request.id, "cantera", result, project, label)

    return result
