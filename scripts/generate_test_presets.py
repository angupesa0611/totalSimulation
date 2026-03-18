#!/usr/bin/env python3
"""Generate test preset JSON files for all pipelines and couplings.

Reads PIPELINES and COUPLINGS from config.py, maps each tool to sensible
default params from existing preset files, and writes:
  - shared/examples/pipeline_<key>.json   (12 files)
  - shared/examples/coupling_<key>.json   (~149 files, skipping deferred)
"""

import json
import os
import sys

# Navigate to project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
EXAMPLES_DIR = os.path.join(PROJECT_ROOT, "shared", "examples")

# Add orchestrator to path so we can import config
sys.path.insert(0, os.path.join(PROJECT_ROOT, "orchestrator"))

# We can't import config directly (needs redis etc), so we parse it manually.
# Instead, define the tool→default_params mapping from existing preset files.

def load_preset(filename):
    """Load a preset JSON file and return its params."""
    path = os.path.join(EXAMPLES_DIR, filename)
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        return data.get("params", {})
    return {}

# Map each tool to its best representative preset params
TOOL_DEFAULTS = {
    "rebound": load_preset("rebound_solar_system.json"),
    "qutip": load_preset("qutip_rabi.json"),
    "openmm": load_preset("openmm_alanine.json"),
    "pyscf": load_preset("pyscf_h2.json"),
    "mdanalysis": load_preset("mdanalysis_rmsd.json"),
    "psi4": load_preset("psi4_sapt_water_dimer.json"),
    "gromacs": load_preset("gromacs_lysozyme_vacuum.json"),
    "namd": load_preset("namd_ubiquitin.json"),
    "qmmm": load_preset("qmmm_enzyme_active_site.json"),
    "pybullet": load_preset("pybullet_collision.json"),
    "einsteinpy": load_preset("einsteinpy_schwarzschild.json"),
    "nrpy": load_preset("nrpy_bbh_merger.json"),
    "fenics": load_preset("fenics_heat_plate.json"),
    "elmer": load_preset("elmer_cantilever.json"),
    "basico": load_preset("basico_enzyme.json"),
    "tellurium": load_preset("tellurium_pathway.json"),
    "brian2": load_preset("brian2_lif.json"),
    "nest": load_preset("nest_brunel.json"),
    "msprime": load_preset("msprime_coalescent.json"),
    "rdkit": load_preset("rdkit_aspirin.json"),
    "cantera": load_preset("cantera_h2_ignition.json"),
    "qe": load_preset("qe_silicon.json"),
    "lammps": load_preset("lammps_lj.json"),
    "sympy": load_preset("sympy_quadratic.json"),
    "gmsh": load_preset("gmsh_box.json"),
    "lcapy": load_preset("lcapy_rc.json"),
    "pennylane": load_preset("pennylane_h2_vqe.json"),
    "sagemath": load_preset("sagemath_groebner.json"),
    "lean4": load_preset("lean4_nat_comm.json"),
    "gap": load_preset("gap_symmetric.json"),
    "pyspice": load_preset("pyspice_rlc.json"),
    "qiskit": load_preset("qiskit_bell.json"),
    "matplotlib": load_preset("matplotlib_sine.json"),
    "control": load_preset("control_rc_bode.json"),
    "pyomo": load_preset("pyomo_knapsack.json"),
    "networkx": load_preset("networkx_karate.json"),
    "phiflow": load_preset("phiflow_smoke.json"),
    "manim": load_preset("manim_bloch.json"),
    "openfoam": load_preset("openfoam_cavity.json"),
    "dedalus": load_preset("dedalus_rb.json"),
    "su2": load_preset("su2_naca_airfoil.json"),
    "firedrake": load_preset("firedrake_poisson.json"),
    "vtk": load_preset("vtk_isosurface.json"),
    "openbabel": load_preset("openbabel_aspirin_convert.json"),
    "slim": load_preset("slim_neutral.json"),
    "tskit": load_preset("tskit_diversity.json"),
    "simupop": load_preset("simupop_random_mating.json"),
    "einstein_toolkit": load_preset("etk_bbh.json"),
    "rayoptics": load_preset("rayoptics_singlet.json"),
    "lightpipes": load_preset("lightpipes_double_slit.json"),
    "strawberryfields": load_preset("strawberryfields_hom.json"),
    "meep": load_preset("meep_waveguide.json"),
    # Deferred tools — empty params (stubs)
    "comsol": {},
    "alphafold": {},
    "pyrosetta": {},
}

# ---- PIPELINES ----
# Extracted from config.py PIPELINES dict
PIPELINES = {
    "quantum_to_organism": {
        "label": "Quantum-to-Organism",
        "description": "Full scale traverse: quantum → electronic → molecular → analysis → systems biology → population genetics",
        "steps": [
            {"tool": "qutip", "params": {"system_type": "qubit_rabi", "qubit_rabi": {"omega": 1.0, "delta": 0.0, "psi0": "ground", "tmax": 25.0}}, "label": "Quantum dynamics"},
            {"tool": "pyscf", "params": {"method": "hf", "basis": "sto-3g", "atom_coords": "H 0 0 0; H 0 0 0.74"}, "label": "Electronic structure"},
            {"tool": "openmm", "params": {"integrator": "langevin", "temperature": 300, "steps": 5000, "report_interval": 50}, "label": "Molecular dynamics"},
            {"tool": "mdanalysis", "params": {"analysis_type": "rmsd"}, "label": "Trajectory analysis"},
            {"tool": "basico", "params": {"model_type": "enzyme_kinetics"}, "label": "Pathway modeling"},
            {"tool": "slim", "params": {"simulation_type": "neutral_evolution", "population_size": 500, "n_generations": 100, "sequence_length": 10000}, "label": "Population evolution"},
            {"tool": "tskit", "params": {"simulation_type": "diversity"}, "label": "Tree sequence analysis"},
        ],
    },
    "mercury_precession": {
        "label": "Mercury GR Precession",
        "description": "Mercury perihelion precession with REBOUNDx GR corrections",
        "steps": [
            {"tool": "rebound", "params": {"gr_correction": "gr_full", "integrator": "ias15", "tmax": 62.83, "n_outputs": 500}, "label": "N-body with GR"},
        ],
    },
    "qmmm_enzyme": {
        "label": "QM/MM Enzyme Catalysis",
        "description": "Drug binding: ligand identification → QM/MM active site → trajectory analysis → pathway kinetics",
        "steps": [
            {"tool": "rdkit", "params": {"simulation_type": "descriptors", "smiles": "CC(=O)Oc1ccccc1C(=O)O"}, "label": "Ligand preparation"},
            {"tool": "qmmm", "params": {"qm_method": "hf", "qm_basis": "sto-3g"}, "label": "QM/MM simulation"},
            {"tool": "mdanalysis", "params": {"analysis_type": "rmsd"}, "label": "Trajectory analysis"},
            {"tool": "basico", "params": {"model_type": "enzyme_kinetics"}, "label": "Kinetic modeling"},
        ],
    },
    "evolution_structure": {
        "label": "Evolution → Structure Feedback",
        "description": "Coalescent → forward sim → tree analysis",
        "steps": [
            {"tool": "msprime", "params": {"simulation_type": "coalescent", "sample_size": 50, "sequence_length": 100000, "recombination_rate": 1e-8, "mutation_rate": 1e-8}, "label": "Coalescent history"},
            {"tool": "slim", "params": {"simulation_type": "nucleotide_evolution", "population_size": 500, "n_generations": 200, "sequence_length": 10000}, "label": "Forward evolution"},
            {"tool": "tskit", "params": {"simulation_type": "diversity"}, "label": "Diversity analysis"},
        ],
    },
    "multiscale_tissue": {
        "label": "Multiscale Tissue Modeling",
        "description": "FEniCS tissue stress → COPASI biochemical response",
        "steps": [
            {"tool": "fenics", "params": {"simulation_type": "elasticity"}, "label": "Tissue mechanics"},
            {"tool": "basico", "params": {"model_type": "enzyme_kinetics"}, "label": "Biochemical response"},
        ],
    },
    "drug_discovery": {
        "label": "Drug Discovery",
        "description": "SMILES → quantum properties → MD binding → trajectory analysis → pathway impact",
        "steps": [
            {"tool": "rdkit", "params": {"simulation_type": "descriptors", "smiles": "CC(=O)Oc1ccccc1C(=O)O"}, "label": "Molecular properties"},
            {"tool": "pyscf", "params": {"method": "hf", "basis": "sto-3g"}, "label": "Quantum chemistry"},
            {"tool": "openmm", "params": {"integrator": "langevin", "temperature": 300, "steps": 5000, "report_interval": 50}, "label": "MD simulation"},
            {"tool": "mdanalysis", "params": {"analysis_type": "rmsd"}, "label": "Binding analysis"},
            {"tool": "basico", "params": {"model_type": "enzyme_kinetics"}, "label": "Pathway modeling"},
        ],
    },
    "materials_discovery": {
        "label": "Materials Discovery",
        "description": "DFT → large-scale MD → trajectory analysis → continuum simulation",
        "steps": [
            {"tool": "qe", "params": {"simulation_type": "scf"}, "label": "DFT calculation"},
            {"tool": "lammps", "params": {"simulation_type": "lj_fluid"}, "label": "MD simulation"},
            {"tool": "mdanalysis", "params": {"analysis_type": "rmsd"}, "label": "Trajectory analysis"},
            {"tool": "fenics", "params": {"simulation_type": "heat"}, "label": "Continuum simulation"},
        ],
    },
    "reactive_multiphysics": {
        "label": "Reactive Multiphysics",
        "description": "Symbolic rate expressions → detailed kinetics → reactive transport PDE",
        "steps": [
            {"tool": "sympy", "params": {"simulation_type": "solve", "expression": "k*A - k_r*B", "variable": "A"}, "label": "Symbolic rates"},
            {"tool": "cantera", "params": {"simulation_type": "ignition_delay"}, "label": "Detailed kinetics"},
            {"tool": "gmsh", "params": {"mesh_type": "box_3d"}, "label": "Mesh generation"},
            {"tool": "fenics", "params": {"simulation_type": "heat"}, "label": "Reactive transport"},
        ],
    },
    "math_verification": {
        "label": "Mathematics Verification Loop",
        "description": "Symbolic computation → algebraic enrichment → formal proof verification",
        "steps": [
            {"tool": "sympy", "params": {"simulation_type": "solve", "expression": "x**2 - 2", "variable": "x"}, "label": "Symbolic computation"},
            {"tool": "sagemath", "params": {"simulation_type": "groebner_basis"}, "label": "Algebraic analysis"},
            {"tool": "lean4", "params": {"simulation_type": "verify"}, "label": "Formal verification"},
        ],
    },
    "classical_circuit": {
        "label": "Classical Circuit Design",
        "description": "Symbolic analysis → numerical SPICE simulation → EM field verification",
        "steps": [
            {"tool": "lcapy", "params": {"simulation_type": "transfer_function"}, "label": "Symbolic circuit"},
            {"tool": "pyspice", "params": {"simulation_type": "transient"}, "label": "SPICE simulation"},
            {"tool": "fenics", "params": {"simulation_type": "heat"}, "label": "EM field verification"},
        ],
    },
    "quantum_chemistry_qc": {
        "label": "QC on Quantum Computers",
        "description": "Molecular structure → Hamiltonian → qubit mapping → variational optimization",
        "steps": [
            {"tool": "rdkit", "params": {"simulation_type": "descriptors", "smiles": "O"}, "label": "Molecular structure"},
            {"tool": "pyscf", "params": {"method": "hf", "basis": "sto-3g"}, "label": "Hamiltonian"},
            {"tool": "qiskit", "params": {"simulation_type": "vqe"}, "label": "VQE (Qiskit)"},
            {"tool": "pennylane", "params": {"simulation_type": "vqe"}, "label": "Optimization (PennyLane)"},
        ],
    },
    "photonic_design": {
        "label": "Photonic Device Design",
        "description": "End-to-end photonic design: ray optics → wave propagation → FDTD → publication plot",
        "steps": [
            {"tool": "rayoptics", "params": {"simulation_type": "singlet_lens", "singlet_lens": {"efl": 100.0, "f_number": 5.0}}, "label": "Lens layout"},
            {"tool": "lightpipes", "params": {"simulation_type": "lens_focus", "lens_focus": {"focal_length": 0.1, "beam_radius": 2e-3}}, "label": "Wave propagation"},
            {"tool": "meep", "params": {"simulation_type": "waveguide_bend"}, "label": "FDTD verification"},
            {"tool": "matplotlib", "params": {"plot_type": "heatmap"}, "label": "Publication plot"},
        ],
    },
}

# ---- COUPLINGS ----
# Extracted from config.py — all coupling keys with from/to/param_map
COUPLINGS = {
    "openmm_to_mdanalysis": {"from": "openmm", "to": "mdanalysis", "description": "Analyze OpenMM trajectory with MDAnalysis", "param_map": {"source_job_id": "$prev.job_id"}},
    "gromacs_to_mdanalysis": {"from": "gromacs", "to": "mdanalysis", "description": "Analyze GROMACS trajectory with MDAnalysis", "param_map": {"source_job_id": "$prev.job_id"}},
    "namd_to_mdanalysis": {"from": "namd", "to": "mdanalysis", "description": "Analyze NAMD trajectory with MDAnalysis", "param_map": {"source_job_id": "$prev.job_id"}},
    "qutip_to_pyscf": {"from": "qutip", "to": "pyscf", "description": "QuTiP state → PySCF electronic structure", "param_map": {}},
    "qmmm_concurrent": {"from": "pyscf", "to": "openmm", "description": "QM/MM: PySCF active site + OpenMM surroundings", "param_map": {}},
    "fenics_to_elmer": {"from": "fenics", "to": "elmer", "description": "FEniCS thermal → Elmer structural coupling", "param_map": {"temperature_field": "$prev.result.field_data"}},
    "pybullet_to_fenics": {"from": "pybullet", "to": "fenics", "description": "PyBullet contact forces → FEniCS stress", "param_map": {"source_forces": "$prev.result.collisions"}},
    "tellurium_to_copasi": {"from": "tellurium", "to": "basico", "description": "Tellurium SBML → BasiCO parameter estimation", "param_map": {"sbml_string": "$prev.result.sbml_export", "model_source": "sbml"}},
    "copasi_to_brian2": {"from": "basico", "to": "brian2", "description": "BasiCO concentrations → Brian2 input current", "param_map": {"input_current_timeseries": "$prev.result"}},
    "rdkit_to_pyscf": {"from": "rdkit", "to": "pyscf", "description": "RDKit SMILES → PySCF electronic structure", "param_map": {"atom_coords": "$prev.result.atom_coords_pyscf"}},
    "lammps_to_mdanalysis": {"from": "lammps", "to": "mdanalysis", "description": "LAMMPS trajectory → MDAnalysis", "param_map": {"source_job_id": "$prev.result.trajectory_job_id"}},
    "sympy_to_fenics": {"from": "sympy", "to": "fenics", "description": "SymPy symbolic PDE → FEniCS weak form", "param_map": {"ufl_code": "$prev.result.ufl_code"}},
    "gmsh_to_fenics": {"from": "gmsh", "to": "fenics", "description": "Gmsh mesh → FEniCS mesh import", "param_map": {"mesh_file": "$prev.result.mesh_file_path"}},
    "lcapy_to_pyspice": {"from": "lcapy", "to": "pyspice", "description": "Symbolic circuit → SPICE simulation", "param_map": {"netlist": "$prev.result.spice_netlist"}},
    "qiskit_to_qutip": {"from": "qiskit", "to": "qutip", "description": "Qiskit OpenQASM → QuTiP-QIP circuit", "param_map": {"qasm_str": "$prev.result.qasm_str"}},
    "qiskit_to_pyscf": {"from": "qiskit", "to": "pyscf", "description": "Qiskit Nature → molecular VQE Hamiltonian", "param_map": {"atom_coords": "$prev.result.molecular_geometry"}},
    "pennylane_to_qiskit": {"from": "pennylane", "to": "qiskit", "description": "PennyLane → Qiskit backend execution", "param_map": {"gates": "$prev.result.gate_sequence"}},
    "gmsh_to_openfoam": {"from": "gmsh", "to": "openfoam", "description": "Gmsh mesh → OpenFOAM mesh", "param_map": {"mesh_file": "$prev.result.mesh_file_path"}},
    "sympy_to_manim": {"from": "sympy", "to": "manim", "description": "SymPy expression → Manim animation", "param_map": {"expressions": "$prev.result.latex"}},
    "sympy_to_pyomo": {"from": "sympy", "to": "pyomo", "description": "Symbolic expressions → Pyomo optimization", "param_map": {"objective": {"expression": "$prev.result.expression"}}},
    "rebound_to_manim": {"from": "rebound", "to": "manim", "description": "REBOUND trajectories → animated orbital vis", "param_map": {"trajectories": "$prev.result.trajectories"}},
    "fenics_to_matplotlib": {"from": "fenics", "to": "matplotlib", "description": "FEniCS fields → Matplotlib plot", "param_map": {"z_data": "$prev.result.field_data"}},
    "lcapy_to_control": {"from": "lcapy", "to": "control", "description": "Lcapy transfer function → Bode/Nyquist", "param_map": {"numerator": "$prev.result.transfer_numerator", "denominator": "$prev.result.transfer_denominator"}},
    "networkx_to_manim": {"from": "networkx", "to": "manim", "description": "NetworkX graph → animated graph vis", "param_map": {"nodes": "$prev.result.nodes", "edges": "$prev.result.edges"}},
    "phiflow_to_matplotlib": {"from": "phiflow", "to": "matplotlib", "description": "PhiFlow fields → Matplotlib plot", "param_map": {"z_data": "$prev.result.field_data"}},
    "qutip_to_manim": {"from": "qutip", "to": "manim", "description": "QuTiP Bloch vector → Manim 3D Bloch sphere", "param_map": {"simulation_type": "bloch_sphere"}},
    "sagemath_to_sympy": {"from": "sagemath", "to": "sympy", "description": "SageMath → SymPy expression", "param_map": {"expression": "$prev.result.result"}},
    "sympy_to_sagemath": {"from": "sympy", "to": "sagemath", "description": "SymPy → SageMath computation", "param_map": {"polynomials": "$prev.result.result"}},
    "gap_to_qiskit": {"from": "gap", "to": "qiskit", "description": "GAP stabilizers → Qiskit syndrome circuits", "param_map": {"simulation_type": "stabilizer_codes", "generators": "$prev.result.generators"}},
    "gmsh_to_su2": {"from": "gmsh", "to": "su2", "description": "Gmsh mesh → SU2 mesh", "param_map": {"mesh_file": "$prev.result.mesh_file_path"}},
    "gmsh_to_firedrake": {"from": "gmsh", "to": "firedrake", "description": "Gmsh mesh → Firedrake mesh", "param_map": {"mesh_file": "$prev.result.mesh_file_path"}},
    "openfoam_to_vtk": {"from": "openfoam", "to": "vtk", "description": "OpenFOAM fields → VTK visualization", "param_map": {"field_data": "$prev.result.field_data"}},
    "fenics_to_vtk": {"from": "fenics", "to": "vtk", "description": "FEniCS fields → VTK rendering", "param_map": {"field_data": "$prev.result.field_data"}},
    "dedalus_to_vtk": {"from": "dedalus", "to": "vtk", "description": "Dedalus spectral → VTK field vis", "param_map": {"field_data": "$prev.result.field_data"}},
    "phiflow_to_vtk": {"from": "phiflow", "to": "vtk", "description": "PhiFlow fields → VTK rendering", "param_map": {"field_data": "$prev.result.field_data"}},
    "qutip_to_psi4": {"from": "qutip", "to": "psi4", "description": "QuTiP quantum state → Psi4 electronic structure", "param_map": {}},
    "pybullet_to_elmer": {"from": "pybullet", "to": "elmer", "description": "PyBullet contact forces → Elmer FEM", "param_map": {"contact_forces": "$prev.result.collisions"}},
    "fenics_to_pyspice": {"from": "fenics", "to": "pyspice", "description": "FEniCS EM field → PySpice parasitic extraction", "param_map": {"field_data": "$prev.result.field_data"}},
    "elmer_to_pyspice": {"from": "elmer", "to": "pyspice", "description": "Elmer EM/thermal → PySpice circuit params", "param_map": {"field_data": "$prev.result.field_data"}},
    "openmm_to_basico": {"from": "openmm", "to": "basico", "description": "OpenMM binding energies → BasiCO rates", "param_map": {"binding_energy": "$prev.result.potential_energy"}},
    "openmm_to_tellurium": {"from": "openmm", "to": "tellurium", "description": "OpenMM structural data → Tellurium pathway", "param_map": {"structural_data": "$prev.result"}},
    "fenics_to_basico": {"from": "fenics", "to": "basico", "description": "FEniCS diffusion → BasiCO spatial reaction-diffusion", "param_map": {"diffusion_field": "$prev.result.field_data"}},
    "fenics_to_tellurium": {"from": "fenics", "to": "tellurium", "description": "FEniCS continuum → Tellurium boundary conditions", "param_map": {"boundary_data": "$prev.result.field_data"}},
    "rdkit_to_psi4": {"from": "rdkit", "to": "psi4", "description": "RDKit conformer → Psi4 quantum chemistry", "param_map": {"geometry": "$prev.result.atom_coords_xyz"}},
    "rdkit_to_openmm": {"from": "rdkit", "to": "openmm", "description": "RDKit structure → OpenMM MD", "param_map": {"pdb_content": "$prev.result.pdb_block"}},
    "rdkit_to_mdanalysis": {"from": "rdkit", "to": "mdanalysis", "description": "RDKit conformer ensemble → MDAnalysis", "param_map": {"structure_data": "$prev.result"}},
    "cantera_to_fenics": {"from": "cantera", "to": "fenics", "description": "Cantera flame → FEniCS reactive flow", "param_map": {"source_term": "$prev.result.heat_release_rate"}},
    "cantera_to_basico": {"from": "cantera", "to": "basico", "description": "Cantera kinetics → BasiCO network", "param_map": {"species_concentrations": "$prev.result.species"}},
    "cantera_to_tellurium": {"from": "cantera", "to": "tellurium", "description": "Cantera species → Tellurium pathway", "param_map": {"species_data": "$prev.result.species"}},
    "cantera_to_elmer": {"from": "cantera", "to": "elmer", "description": "Cantera thermal → Elmer FEM", "param_map": {"temperature_profile": "$prev.result.temperature"}},
    "qe_to_lammps": {"from": "qe", "to": "lammps", "description": "QE DFT potential → LAMMPS MD", "param_map": {"potential_data": "$prev.result"}},
    "qe_to_cantera": {"from": "qe", "to": "cantera", "description": "QE surface energies → Cantera catalysis", "param_map": {"surface_energies": "$prev.result.total_energy"}},
    "cantera_to_lammps": {"from": "cantera", "to": "lammps", "description": "Cantera reactive → LAMMPS ReaxFF", "param_map": {"species_data": "$prev.result.species"}},
    "rdkit_to_cantera": {"from": "rdkit", "to": "cantera", "description": "RDKit molecular properties → Cantera thermo", "param_map": {"smiles": "$prev.result.smiles"}},
    "rdkit_to_lammps": {"from": "rdkit", "to": "lammps", "description": "RDKit conformer → LAMMPS system", "param_map": {"coordinates": "$prev.result.conformer_coordinates"}},
    "sympy_to_cantera": {"from": "sympy", "to": "cantera", "description": "Symbolic rate expressions → Cantera mechanisms", "param_map": {"rate_expression": "$prev.result.expression"}},
    "sympy_to_qutip": {"from": "sympy", "to": "qutip", "description": "Symbolic Hamiltonian → QuTiP dynamics", "param_map": {"hamiltonian_expr": "$prev.result.expression"}},
    "sympy_to_einsteinpy": {"from": "sympy", "to": "einsteinpy", "description": "Metric tensor → EinsteinPy geodesics", "param_map": {"metric_expr": "$prev.result.expression"}},
    "sagemath_to_gap": {"from": "sagemath", "to": "gap", "description": "SageMath group → GAP group theory", "param_map": {"group_data": "$prev.result.result"}},
    "gap_to_sagemath": {"from": "gap", "to": "sagemath", "description": "GAP group → SageMath algebra", "param_map": {"group_data": "$prev.result"}},
    "sagemath_to_einsteinpy": {"from": "sagemath", "to": "einsteinpy", "description": "Differential geometry → EinsteinPy spacetime", "param_map": {"metric_data": "$prev.result.result"}},
    "gmsh_to_elmer": {"from": "gmsh", "to": "elmer", "description": "Gmsh mesh → Elmer FEM", "param_map": {"mesh_file": "$prev.result.mesh_file_path"}},
    "lcapy_to_sympy": {"from": "lcapy", "to": "sympy", "description": "Lcapy circuit expression → SymPy analysis", "param_map": {"expression": "$prev.result.transfer_function_str"}},
    "pennylane_to_qutip": {"from": "pennylane", "to": "qutip", "description": "PennyLane circuit → QuTiP open system", "param_map": {"gate_sequence": "$prev.result.gate_sequence"}},
    "pennylane_to_pyscf": {"from": "pennylane", "to": "pyscf", "description": "PennyLane VQE → PySCF electronic structure", "param_map": {"geometry": "$prev.result.molecular_geometry"}},
    "sympy_to_pyspice": {"from": "sympy", "to": "pyspice", "description": "Symbolic circuit → PySpice numerical", "param_map": {"circuit_expr": "$prev.result.expression"}},
    "sympy_to_qiskit": {"from": "sympy", "to": "qiskit", "description": "Symbolic Hamiltonian → Qiskit circuit", "param_map": {"hamiltonian_expr": "$prev.result.expression"}},
    "rdkit_to_qiskit": {"from": "rdkit", "to": "qiskit", "description": "Molecular data → Qiskit Nature VQE", "param_map": {"smiles": "$prev.result.smiles"}},
    "rdkit_to_openbabel": {"from": "rdkit", "to": "openbabel", "description": "RDKit → Open Babel format conversion", "param_map": {"source_data": "$prev.result.smiles", "source_format": "smi"}},
    "openbabel_to_rdkit": {"from": "openbabel", "to": "rdkit", "description": "Open Babel → RDKit descriptors", "param_map": {"smiles": "$prev.result.output_data"}},
    "openbabel_to_pyscf": {"from": "openbabel", "to": "pyscf", "description": "Open Babel XYZ → PySCF", "param_map": {"geometry": "$prev.result.output_xyz"}},
    "openbabel_to_psi4": {"from": "openbabel", "to": "psi4", "description": "Open Babel geometry → Psi4", "param_map": {"geometry": "$prev.result.output_xyz"}},
    "openbabel_to_lammps": {"from": "openbabel", "to": "lammps", "description": "Open Babel → LAMMPS data", "param_map": {"molecule_data": "$prev.result.output_data"}},
    "openbabel_to_gromacs": {"from": "openbabel", "to": "gromacs", "description": "Open Babel → GROMACS topology", "param_map": {"molecule_data": "$prev.result.output_data"}},
    "openbabel_to_qe": {"from": "openbabel", "to": "qe", "description": "Open Babel geometry → QE input", "param_map": {"coordinates": "$prev.result.coordinates"}},
    "openbabel_to_openmm": {"from": "openbabel", "to": "openmm", "description": "Open Babel PDB → OpenMM MD", "param_map": {"pdb_content": "$prev.result.output_pdb"}},
    "openbabel_to_namd": {"from": "openbabel", "to": "namd", "description": "Open Babel PDB → NAMD MD", "param_map": {"pdb_content": "$prev.result.output_pdb"}},
    "mdanalysis_to_openbabel": {"from": "mdanalysis", "to": "openbabel", "description": "MDAnalysis frame → Open Babel convert", "param_map": {"source_data": "$prev.result.pdb_frame", "source_format": "pdb"}},
    "einsteinpy_to_rebound": {"from": "einsteinpy", "to": "rebound", "description": "EinsteinPy metric → REBOUND N-body + GR", "param_map": {"gr_correction": "gr_full", "M": "$prev.result.M"}},
    "slim_to_tskit": {"from": "slim", "to": "tskit", "description": "SLiM tree sequence → tskit analysis", "param_map": {"source_job_id": "$prev.job_id"}},
    "msprime_to_tskit": {"from": "msprime", "to": "tskit", "description": "msprime tree → tskit post-hoc analysis", "param_map": {"source_job_id": "$prev.job_id"}},
    "msprime_to_slim": {"from": "msprime", "to": "slim", "description": "msprime coalescent → SLiM forward sim", "param_map": {"demographic_data": "$prev.result"}},
    "slim_to_msprime": {"from": "slim", "to": "msprime", "description": "SLiM forward → msprime recapitation", "param_map": {"source_job_id": "$prev.job_id"}},
    "slim_to_simupop": {"from": "slim", "to": "simupop", "description": "SLiM population → simuPOP model", "param_map": {"population_size": "$prev.result.population_size"}},
    "simupop_to_msprime": {"from": "simupop", "to": "msprime", "description": "simuPOP pop size → msprime demographic model", "param_map": {"population_size": "$prev.result.population_size"}},
    "psi4_to_openmm_qmmm": {"from": "psi4", "to": "openmm", "description": "QM/MM: Psi4 QM + OpenMM MM", "param_map": {}},
    "gromacs_to_openmm": {"from": "gromacs", "to": "openmm", "description": "GROMACS topology → OpenMM System", "param_map": {"topology_data": "$prev.result"}},
    "einsteinpy_to_etk": {"from": "einsteinpy", "to": "einstein_toolkit", "description": "EinsteinPy metric → ETK initial data", "param_map": {"metric_data": "$prev.result"}},
    "etk_to_rebound": {"from": "einstein_toolkit", "to": "rebound", "description": "ETK strong-field → REBOUNDx forces", "param_map": {"gr_correction": "gr_full", "metric_data": "$prev.result"}},
    "psi4_to_qiskit": {"from": "psi4", "to": "qiskit", "description": "Qiskit Nature Psi4 driver", "param_map": {"molecular_data": "$prev.result"}},
    "psi4_to_pennylane": {"from": "psi4", "to": "pennylane", "description": "pennylane-psi4 plugin", "param_map": {"molecular_data": "$prev.result"}},
    "pyscf_to_cantera": {"from": "pyscf", "to": "cantera", "description": "QC barriers → rate constants (TST)", "param_map": {"activation_energy": "$prev.result.total_energy"}},
    "psi4_to_cantera": {"from": "psi4", "to": "cantera", "description": "Psi4 QC barriers → rate constants (TST)", "param_map": {"activation_energy": "$prev.result.total_energy"}},
    "pyscf_to_qe": {"from": "pyscf", "to": "qe", "description": "Molecular ↔ periodic DFT bridge", "param_map": {"molecular_data": "$prev.result"}},
    "psi4_to_qe": {"from": "psi4", "to": "qe", "description": "Molecular ↔ periodic DFT via Psi4", "param_map": {"molecular_data": "$prev.result"}},
    "openmm_to_lammps": {"from": "openmm", "to": "lammps", "description": "Force field conversion, bio+materials", "param_map": {"structure_data": "$prev.result"}},
    "gromacs_to_lammps": {"from": "gromacs", "to": "lammps", "description": "Trajectory interconversion via MDAnalysis", "param_map": {"trajectory_data": "$prev.result"}},
    "namd_to_lammps": {"from": "namd", "to": "lammps", "description": "NAMD → LAMMPS interconversion", "param_map": {"trajectory_data": "$prev.result"}},
    "openmm_to_qe": {"from": "openmm", "to": "qe", "description": "QE-derived force constants → OpenMM FF", "param_map": {"structure_data": "$prev.result"}},
    "gromacs_to_qe": {"from": "gromacs", "to": "qe", "description": "QE-derived params → GROMACS topology", "param_map": {"structure_data": "$prev.result"}},
    "lammps_to_elmer": {"from": "lammps", "to": "elmer", "description": "Atomic → continuum: elastic/thermal props", "param_map": {"material_properties": "$prev.result"}},
    "qe_to_fenics": {"from": "qe", "to": "fenics", "description": "DFT material properties → FEM continuum", "param_map": {"material_data": "$prev.result"}},
    "qe_to_elmer": {"from": "qe", "to": "elmer", "description": "DFT material → Elmer FEM continuum", "param_map": {"material_data": "$prev.result"}},
    "sympy_to_elmer": {"from": "sympy", "to": "elmer", "description": "Symbolic PDE → Elmer .sif input", "param_map": {"pde_expression": "$prev.result.expression"}},
    "basico_to_sympy": {"from": "basico", "to": "sympy", "description": "Systems biology ODEs → symbolic analysis", "param_map": {"expression": "$prev.result.ode_system"}},
    "tellurium_to_sympy": {"from": "tellurium", "to": "sympy", "description": "Tellurium ODEs → symbolic analysis", "param_map": {"expression": "$prev.result.ode_system"}},
    "qmmm_to_rdkit": {"from": "qmmm", "to": "rdkit", "description": "QM/MM ligand → RDKit analysis", "param_map": {"smiles": "$prev.result.ligand_smiles"}},
    "qmmm_to_openbabel": {"from": "qmmm", "to": "openbabel", "description": "QM/MM output → Open Babel convert", "param_map": {"source_data": "$prev.result.structure_data"}},
    "rdkit_to_qe": {"from": "rdkit", "to": "qe", "description": "SMILES → crystal structure prediction", "param_map": {"coordinates": "$prev.result.conformer_coordinates"}},
    "gmsh_to_lammps": {"from": "gmsh", "to": "lammps", "description": "FEM mesh for hybrid continuum-atomistic", "param_map": {"mesh_data": "$prev.result.mesh_file_path"}},
    "sagemath_to_elmer": {"from": "sagemath", "to": "elmer", "description": "Differential geometry → curved-space FEM", "param_map": {"geometry_data": "$prev.result.result"}},
    "qutip_to_qe": {"from": "qutip", "to": "qe", "description": "Defect qubits in solids (NV centers)", "param_map": {"qubit_data": "$prev.result"}},
    "qutip_to_sagemath": {"from": "qutip", "to": "sagemath", "description": "Lie algebra → quantum operators", "param_map": {"operator_data": "$prev.result"}},
    "qutip_to_gap": {"from": "qutip", "to": "gap", "description": "Group theory → symmetry quantum states", "param_map": {"symmetry_data": "$prev.result"}},
    "qutip_to_pyspice": {"from": "qutip", "to": "pyspice", "description": "Circuit QED: classical readout + quantum", "param_map": {"qubit_params": "$prev.result"}},
    "qutip_to_lcapy": {"from": "qutip", "to": "lcapy", "description": "Circuit QED: LC → quantum Hamiltonian", "param_map": {"circuit_params": "$prev.result"}},
    "sympy_to_pennylane": {"from": "sympy", "to": "pennylane", "description": "Symbolic Hamiltonians → parametric circuits", "param_map": {"hamiltonian_expr": "$prev.result.expression"}},
    "sympy_to_lean4": {"from": "sympy", "to": "lean4", "description": "SymPy → Lean 4 formal verification", "param_map": {"statement": "$prev.result.expression"}},
    "sagemath_to_lean4": {"from": "sagemath", "to": "lean4", "description": "SageMath → Lean 4 formal verification", "param_map": {"statement": "$prev.result.result"}},
    "sagemath_to_lcapy": {"from": "sagemath", "to": "lcapy", "description": "Advanced symbolic circuit via SymPy bridge", "param_map": {"expression": "$prev.result.result"}},
    "sagemath_to_qiskit": {"from": "sagemath", "to": "qiskit", "description": "Coding theory → stabilizer codes for QEC", "param_map": {"code_data": "$prev.result.result"}},
    "sagemath_to_pennylane": {"from": "sagemath", "to": "pennylane", "description": "Symmetry-aware quantum ML", "param_map": {"symmetry_data": "$prev.result.result"}},
    "lean4_to_gap": {"from": "lean4", "to": "gap", "description": "Verified computational algebra", "param_map": {"proof_data": "$prev.result"}},
    "gap_to_qe": {"from": "gap", "to": "qe", "description": "Crystallographic groups → Brillouin zone", "param_map": {"space_group": "$prev.result"}},
    "gap_to_pennylane": {"from": "gap", "to": "pennylane", "description": "Equivariant quantum circuits via symmetry", "param_map": {"group_data": "$prev.result"}},
    "qe_to_qiskit": {"from": "qe", "to": "qiskit", "description": "Periodic Hamiltonians → quantum simulation", "param_map": {"hamiltonian_data": "$prev.result"}},
    "qe_to_pennylane": {"from": "qe", "to": "pennylane", "description": "Quantum algorithms for periodic DFT", "param_map": {"material_data": "$prev.result"}},
    "pyspice_to_qiskit": {"from": "pyspice", "to": "qiskit", "description": "Classical + quantum circuit co-design", "param_map": {"circuit_data": "$prev.result"}},
    "pyspice_to_pennylane": {"from": "pyspice", "to": "pennylane", "description": "Classical + quantum circuit co-design", "param_map": {"circuit_data": "$prev.result"}},
    "lcapy_to_qiskit": {"from": "lcapy", "to": "qiskit", "description": "Symbolic circuit → transmon Hamiltonians", "param_map": {"circuit_params": "$prev.result"}},
    "lcapy_to_pennylane": {"from": "lcapy", "to": "pennylane", "description": "Symbolic circuit → differentiable quantum", "param_map": {"circuit_params": "$prev.result"}},
    "simupop_to_tskit": {"from": "simupop", "to": "tskit", "description": "Genotype matrix → tsinfer → tree sequence", "param_map": {"genotype_data": "$prev.result"}},
    "openbabel_to_cantera": {"from": "openbabel", "to": "cantera", "description": "Molecular geometry → transport properties", "param_map": {"molecule_data": "$prev.result"}},
    "rdkit_to_sympy": {"from": "rdkit", "to": "sympy", "description": "QSAR symbolic analysis of descriptors", "param_map": {"expression": "$prev.result.descriptors"}},
    "pennylane_to_lammps": {"from": "pennylane", "to": "lammps", "description": "Quantum neural network potentials for MD", "param_map": {"potential_data": "$prev.result"}},
    "lean4_to_sympy": {"from": "lean4", "to": "sympy", "description": "Verified symbolic computation", "param_map": {"expression": "$prev.result.proof_term"}},
    # Optics couplings
    "rayoptics_to_lightpipes": {"from": "rayoptics", "to": "lightpipes", "description": "Ray trace focus → wave propagation", "param_map": {"lens_focus.focal_length": "$prev.result.efl"}},
    "lightpipes_to_meep": {"from": "lightpipes", "to": "meep", "description": "Wave optics → FDTD source", "param_map": {"source_field": "$prev.result.intensity"}},
    "meep_to_vtk": {"from": "meep", "to": "vtk", "description": "FDTD field → VTK 3D vis", "param_map": {"field_data": "$prev.result.field_ez"}},
    "meep_to_matplotlib": {"from": "meep", "to": "matplotlib", "description": "FDTD fields → publication plots", "param_map": {"z_data": "$prev.result.field_ez"}},
    "lightpipes_to_matplotlib": {"from": "lightpipes", "to": "matplotlib", "description": "Diffraction pattern → publication plot", "param_map": {"z_data": "$prev.result.intensity"}},
    "strawberryfields_to_qutip": {"from": "strawberryfields", "to": "qutip", "description": "Photonic state → cavity QED", "param_map": {"initial_state_data": "$prev.result"}},
    "qutip_to_strawberryfields": {"from": "qutip", "to": "strawberryfields", "description": "Quantum state → photonic circuit", "param_map": {"state_data": "$prev.result"}},
    "strawberryfields_to_pennylane": {"from": "strawberryfields", "to": "pennylane", "description": "Photonic circuit → hybrid QML", "param_map": {"circuit_data": "$prev.result"}},
    "pennylane_to_strawberryfields": {"from": "pennylane", "to": "strawberryfields", "description": "Optimized QML → photonic circuit", "param_map": {"optimized_params": "$prev.result"}},
    "meep_to_fenics": {"from": "meep", "to": "fenics", "description": "EM field absorption → thermal FEM", "param_map": {"source_term": "$prev.result.field_ez"}},
    "sympy_to_rayoptics": {"from": "sympy", "to": "rayoptics", "description": "Symbolic lens equation → ray trace", "param_map": {"singlet_lens.efl": "$prev.result.expression"}},
    "sympy_to_lightpipes": {"from": "sympy", "to": "lightpipes", "description": "Symbolic diffraction → wave simulation", "param_map": {"double_slit.slit_separation": "$prev.result.expression"}},
    "gmsh_to_meep": {"from": "gmsh", "to": "meep", "description": "Gmsh mesh → FDTD domain", "param_map": {"mesh_file": "$prev.result.mesh_file_path"}},
}


def generate_pipeline_preset(key, pipeline):
    """Generate a pipeline test preset JSON file."""
    filename = f"pipeline_{key}.json"
    filepath = os.path.join(EXAMPLES_DIR, filename)

    preset = {
        "pipeline": key,
        "label": pipeline["label"],
        "description": pipeline["description"],
        "steps": pipeline["steps"],
    }

    with open(filepath, "w") as f:
        json.dump(preset, f, indent=2)

    return filename


def generate_coupling_preset(key, coupling):
    """Generate a coupling test preset as a 2-step pipeline JSON file."""
    filename = f"coupling_{key}.json"
    filepath = os.path.join(EXAMPLES_DIR, filename)

    from_tool = coupling["from"]
    to_tool = coupling["to"]

    # Get default params for both tools
    from_params = TOOL_DEFAULTS.get(from_tool, {})
    to_params = TOOL_DEFAULTS.get(to_tool, {})

    steps = [
        {
            "tool": from_tool,
            "params": from_params,
            "label": f"Step 1: {from_tool}",
        },
        {
            "tool": to_tool,
            "params": to_params,
            "param_map": coupling.get("param_map", {}),
            "label": f"Step 2: {to_tool}",
        },
    ]

    preset = {
        "coupling": key,
        "label": coupling["description"],
        "from": from_tool,
        "to": to_tool,
        "steps": steps,
    }

    with open(filepath, "w") as f:
        json.dump(preset, f, indent=2)

    return filename


def main():
    os.makedirs(EXAMPLES_DIR, exist_ok=True)

    print("=== Generating Pipeline Presets ===")
    pipeline_count = 0
    for key, pipeline in PIPELINES.items():
        fn = generate_pipeline_preset(key, pipeline)
        pipeline_count += 1
        print(f"  [{pipeline_count}] {fn}")

    print(f"\n  Total pipeline presets: {pipeline_count}")

    print("\n=== Generating Coupling Presets ===")
    coupling_count = 0
    for key, coupling in COUPLINGS.items():
        fn = generate_coupling_preset(key, coupling)
        coupling_count += 1
        print(f"  [{coupling_count}] {fn}")

    print(f"\n  Total coupling presets: {coupling_count}")
    print(f"\n  Grand total: {pipeline_count + coupling_count} preset files generated")


if __name__ == "__main__":
    main()
