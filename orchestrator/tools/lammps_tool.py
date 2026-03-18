"""LAMMPS — classical molecular dynamics simulations.

Simulation types:
  - lj_fluid: Lennard-Jones fluid simulation
  - eam_metal: EAM metal simulation (with LJ fallback)
  - polymer_melt: Bead-spring polymer melt model
  - custom_script: Run arbitrary LAMMPS input scripts
"""

import os
import tempfile
import time
from typing import Any

import numpy as np
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result


def _downsample(data_list, max_points=5000):
    """Downsample a list to max_points evenly spaced entries."""
    if len(data_list) <= max_points:
        return data_list
    indices = np.linspace(0, len(data_list) - 1, max_points, dtype=int)
    return [data_list[i] for i in indices]


def _run_lj_fluid(lmp, params):
    """Lennard-Jones fluid simulation."""
    p = params.get("lj_fluid", {})
    n_atoms = p.get("n_atoms", 500)
    temperature = p.get("temperature", 1.0)
    density = p.get("density", 0.8)
    timestep = p.get("timestep", 0.005)
    n_steps = min(p.get("n_steps", 10000), 50000)
    dump_interval = p.get("dump_interval", 100)

    vol = n_atoms / density
    box_length = vol ** (1.0 / 3.0)
    half = box_length / 2.0

    lmp.command("units lj")
    lmp.command("atom_style atomic")
    lmp.command("boundary p p p")
    lmp.command(f"region box block {-half} {half} {-half} {half} {-half} {half}")
    lmp.command(f"create_box 1 box")
    lmp.command(f"create_atoms 1 random {n_atoms} 12345 box")
    lmp.command("mass 1 1.0")
    lmp.command("pair_style lj/cut 2.5")
    lmp.command("pair_coeff 1 1 1.0 1.0 2.5")
    lmp.command("neighbor 0.3 bin")
    lmp.command("neigh_modify every 1 delay 0 check yes")

    lmp.command("minimize 1e-4 1e-6 1000 10000")
    lmp.command(f"velocity all create {temperature} 87287 dist gaussian")
    lmp.command(f"timestep {timestep}")
    lmp.command("fix nve_fix all nve")
    lmp.command(f"fix temp_fix all langevin {temperature} {temperature} 0.5 48279")
    lmp.command(f"thermo {dump_interval}")
    lmp.command("thermo_style custom step temp pe ke press")

    lmp.command("compute rdf_compute all rdf 100")
    lmp.command(f"fix rdf_fix all ave/time {dump_interval} 1 {dump_interval} c_rdf_compute[*] file rdf.dat mode vector")

    lmp.command("compute msd_compute all msd")
    lmp.command(f"fix msd_fix all ave/time {dump_interval} 1 {dump_interval} c_msd_compute[4] file msd.dat")

    lmp.command(f"run {n_steps}")
    return n_atoms, temperature


def _run_eam_metal(lmp, params):
    """EAM metal simulation."""
    p = params.get("eam_metal", {})
    element = p.get("element", "Cu")
    lattice_type = p.get("lattice_type", "fcc")
    lattice_constant = p.get("lattice_constant", 3.615)
    supercell = p.get("supercell", [4, 4, 4])
    temperature = p.get("temperature", 300.0)
    n_steps = min(p.get("n_steps", 10000), 50000)
    dump_interval = max(n_steps // 100, 10)

    lmp.command("units metal")
    lmp.command("atom_style atomic")
    lmp.command("boundary p p p")
    lmp.command(f"lattice {lattice_type} {lattice_constant}")
    lmp.command(f"region box block 0 {supercell[0]} 0 {supercell[1]} 0 {supercell[2]}")
    lmp.command("create_box 1 box")
    lmp.command("create_atoms 1 box")
    lmp.command("mass 1 63.546")

    lmp.command("pair_style lj/cut 5.0")
    lmp.command(f"pair_coeff 1 1 0.167 2.338 5.0")
    lmp.command("neighbor 2.0 bin")
    lmp.command("neigh_modify every 1 delay 0 check yes")

    lmp.command(f"velocity all create {temperature} 87287 dist gaussian")
    lmp.command("timestep 0.001")
    lmp.command("fix npt_fix all npt temp {t} {t} 0.1 iso 0.0 0.0 1.0".format(t=temperature))
    lmp.command(f"thermo {dump_interval}")
    lmp.command("thermo_style custom step temp pe ke press")

    lmp.command("compute rdf_compute all rdf 100")
    lmp.command(f"fix rdf_fix all ave/time {dump_interval} 1 {dump_interval} c_rdf_compute[*] file rdf.dat mode vector")

    lmp.command("compute msd_compute all msd")
    lmp.command(f"fix msd_fix all ave/time {dump_interval} 1 {dump_interval} c_msd_compute[4] file msd.dat")

    lmp.command(f"run {n_steps}")
    n_atoms = int(lmp.get_natoms())
    return n_atoms, temperature


def _run_polymer_melt(lmp, params):
    """Polymer melt simulation using simple bead-spring model."""
    p = params.get("polymer_melt", {})
    n_chains = p.get("n_chains", 10)
    chain_length = p.get("chain_length", 20)
    temperature = p.get("temperature", 1.0)
    n_steps = min(p.get("n_steps", 10000), 50000)

    n_atoms = n_chains * chain_length
    density = 0.85
    vol = n_atoms / density
    box_length = vol ** (1.0 / 3.0)
    half = box_length / 2.0
    dump_interval = max(n_steps // 100, 10)

    lmp.command("units lj")
    lmp.command("atom_style molecular")
    lmp.command("boundary p p p")
    lmp.command(f"region box block {-half} {half} {-half} {half} {-half} {half}")
    lmp.command("create_box 1 box bond/types 1 extra/bond/per/atom 2")
    lmp.command(f"create_atoms 1 random {n_atoms} 12345 box")
    lmp.command("mass 1 1.0")

    lmp.command("pair_style lj/cut 2.5")
    lmp.command("pair_coeff 1 1 1.0 1.0 2.5")
    lmp.command("bond_style fene")
    lmp.command("bond_coeff 1 30.0 1.5 1.0 1.0")
    lmp.command("special_bonds fene")
    lmp.command("neighbor 0.4 bin")

    for chain in range(n_chains):
        start = chain * chain_length + 1
        for i in range(chain_length - 1):
            lmp.command(f"create_bonds single/bond 1 {start + i} {start + i + 1}")

    lmp.command("minimize 1e-4 1e-6 1000 10000")
    lmp.command(f"velocity all create {temperature} 87287 dist gaussian")
    lmp.command("timestep 0.005")
    lmp.command("fix nve_fix all nve")
    lmp.command(f"fix temp_fix all langevin {temperature} {temperature} 1.0 48279")
    lmp.command(f"thermo {dump_interval}")
    lmp.command("thermo_style custom step temp pe ke press")

    lmp.command("compute msd_compute all msd")
    lmp.command(f"fix msd_fix all ave/time {dump_interval} 1 {dump_interval} c_msd_compute[4] file msd.dat")

    lmp.command(f"run {n_steps}")
    return n_atoms, temperature


def _run_custom_script(lmp, params):
    """Run a custom LAMMPS script."""
    script = params.get("lammps_script", "")
    if not script.strip():
        raise ValueError("lammps_script is required for custom_script simulation type")

    for line in script.strip().split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            lmp.command(line)

    n_atoms = int(lmp.get_natoms())
    return n_atoms, 0.0


def _parse_thermo_log(log_path):
    """Parse LAMMPS thermo output from log file."""
    thermo = {"step": [], "temp": [], "pe": [], "ke": [], "press": []}

    if not os.path.exists(log_path):
        return thermo

    with open(log_path) as f:
        in_thermo = False
        for line in f:
            line = line.strip()
            if line.startswith("Step"):
                in_thermo = True
                continue
            if in_thermo:
                if line.startswith("Loop") or not line:
                    in_thermo = False
                    continue
                parts = line.split()
                if len(parts) >= 5:
                    try:
                        thermo["step"].append(int(parts[0]))
                        thermo["temp"].append(float(parts[1]))
                        thermo["pe"].append(float(parts[2]))
                        thermo["ke"].append(float(parts[3]))
                        thermo["press"].append(float(parts[4]))
                    except (ValueError, IndexError):
                        continue

    return thermo


def _parse_rdf_file(rdf_path):
    """Parse RDF output file."""
    r = []
    g_r = []

    if not os.path.exists(rdf_path):
        return r, g_r

    with open(rdf_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            parts = line.split()
            if len(parts) >= 3:
                try:
                    r.append(float(parts[1]))
                    g_r.append(float(parts[2]))
                except (ValueError, IndexError):
                    continue

    return r, g_r


def _parse_msd_file(msd_path):
    """Parse MSD output file."""
    time_vals = []
    msd_vals = []

    if not os.path.exists(msd_path):
        return time_vals, msd_vals

    with open(msd_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                try:
                    time_vals.append(float(parts[0]))
                    msd_vals.append(float(parts[1]))
                except (ValueError, IndexError):
                    continue

    return time_vals, msd_vals


class LAMMPSTool(SimulationTool):
    name = "LAMMPS"
    key = "lammps"
    layer = "materials-science"

    SIMULATION_TYPES = {"lj_fluid", "eam_metal", "polymer_melt", "custom_script"}

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type", "lj_fluid")
        if sim_type not in self.SIMULATION_TYPES:
            raise ValueError(f"Unknown simulation_type: {sim_type}. Supported: {self.SIMULATION_TYPES}")
        params.setdefault("simulation_type", sim_type)
        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        params = self.validate_params(params)
        sim_type = params["simulation_type"]
        start_time = time.time()

        with tempfile.TemporaryDirectory() as tmpdir:
            orig_dir = os.getcwd()
            os.chdir(tmpdir)

            try:
                from lammps import lammps

                log_path = os.path.join(tmpdir, "log.lammps")
                lmp = lammps(cmdargs=["-log", log_path, "-screen", "none"])

                if sim_type == "lj_fluid":
                    n_atoms, temperature = _run_lj_fluid(lmp, params)
                elif sim_type == "eam_metal":
                    n_atoms, temperature = _run_eam_metal(lmp, params)
                elif sim_type == "polymer_melt":
                    n_atoms, temperature = _run_polymer_melt(lmp, params)
                elif sim_type == "custom_script":
                    n_atoms, temperature = _run_custom_script(lmp, params)

                final_temp = float(lmp.get_thermo("temp"))
                lmp.close()

                thermo = _parse_thermo_log(log_path)
                rdf_r, rdf_g = _parse_rdf_file(os.path.join(tmpdir, "rdf.dat"))
                msd_t, msd_v = _parse_msd_file(os.path.join(tmpdir, "msd.dat"))

                for key in thermo:
                    thermo[key] = _downsample(thermo[key])

                solve_time = time.time() - start_time

                result = {
                    "tool": "lammps",
                    "simulation_type": sim_type,
                    "thermo": thermo,
                    "rdf": {"r": rdf_r, "g_r": rdf_g},
                    "msd": {"time": msd_t, "msd": msd_v},
                    "n_atoms": n_atoms,
                    "final_temperature": final_temp,
                    "solve_time": solve_time,
                }

            finally:
                os.chdir(orig_dir)

        return result

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "lj_fluid",
            "lj_fluid": {
                "n_atoms": 500,
                "temperature": 1.0,
                "density": 0.8,
                "timestep": 0.005,
                "n_steps": 10000,
                "dump_interval": 100,
            },
        }


@celery_app.task(name="tools.lammps_tool.run_lammps", bind=True)
def run_lammps(self, params: dict, project: str = "_default",
               label: str | None = None) -> dict:
    tool = LAMMPSTool()

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Setting up LAMMPS"})

    try:
        sim_type = params.get("simulation_type", "lj_fluid")
        self.update_state(state="PROGRESS", meta={"progress": 0.1, "message": f"Running {sim_type}"})
        result = tool.run(params)
    except Exception as e:
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.95, "message": "Saving results"})
    save_result(self.request.id, "lammps", result, project, label)

    return result
