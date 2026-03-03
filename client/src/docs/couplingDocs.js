// Coupling documentation data — groups 100+ couplings into ~20 categories
// with representative examples and detailed entries for key couplings.

export const couplingDocs = {
  categories: [
    {
      id: "trajectory-analysis",
      label: "Trajectory → Analysis",
      description: "MD simulation trajectories analyzed with MDAnalysis for structural properties (RMSD, RMSF, contacts, H-bonds).",
      tools: ["openmm", "gromacs", "namd", "lammps"],
      target: "mdanalysis",
      dataFlow: "Trajectory frames → RMSD, RMSF, contacts, distances, hydrogen bonds",
      examples: ["openmm_to_mdanalysis", "gromacs_to_mdanalysis", "namd_to_mdanalysis", "lammps_to_mdanalysis"],
    },
    {
      id: "quantum-electronic",
      label: "Quantum → Electronic Structure",
      description: "Quantum dynamics results initialize electronic structure calculations for molecular orbital and energy analysis.",
      tools: ["qutip"],
      target: "pyscf",
      dataFlow: "Quantum state/parameters → molecular Hamiltonian → HF/DFT/MP2 energies",
      examples: ["qutip_to_pyscf", "qutip_to_psi4"],
    },
    {
      id: "cheminformatics-qc",
      label: "Cheminformatics → Quantum Chemistry",
      description: "RDKit or Open Babel generate 3D molecular structures that feed into PySCF or Psi4 for electronic structure calculations.",
      tools: ["rdkit", "openbabel"],
      target: "pyscf",
      dataFlow: "SMILES → 3D conformer → atom coordinates → HF/DFT/SAPT energies",
      examples: ["rdkit_to_pyscf", "rdkit_to_psi4", "openbabel_to_pyscf", "openbabel_to_psi4"],
    },
    {
      id: "cheminformatics-md",
      label: "Cheminformatics → Molecular Dynamics",
      description: "Molecular structures from RDKit or Open Babel used as starting configurations for MD simulations.",
      tools: ["rdkit", "openbabel"],
      target: "openmm",
      dataFlow: "SMILES → PDB/SDF structure → MD simulation with force fields",
      examples: ["rdkit_to_openmm", "openbabel_to_openmm", "openbabel_to_namd", "openbabel_to_gromacs"],
    },
    {
      id: "mesh-fem",
      label: "Mesh → FEM/CFD Solvers",
      description: "Gmsh generates finite element meshes consumed by FEniCS, Elmer, Firedrake, OpenFOAM, or SU2.",
      tools: ["gmsh"],
      target: "fenics",
      dataFlow: "Geometry definition → mesh (.msh) → FEM/CFD solver input",
      examples: ["gmsh_to_fenics", "gmsh_to_elmer", "gmsh_to_firedrake", "gmsh_to_openfoam", "gmsh_to_su2"],
    },
    {
      id: "fem-visualization",
      label: "FEM/CFD → Visualization",
      description: "Simulation field data (temperature, velocity, pressure) rendered as publication-quality plots or 3D visualizations.",
      tools: ["fenics", "openfoam", "dedalus", "phiflow"],
      target: "matplotlib",
      dataFlow: "Solution fields → contour/heatmap plots or 3D VTK renderings",
      examples: ["fenics_to_matplotlib", "fenics_to_vtk", "openfoam_to_vtk", "dedalus_to_vtk", "phiflow_to_matplotlib", "phiflow_to_vtk"],
    },
    {
      id: "symbolic-circuits",
      label: "Symbolic → Circuit Simulation",
      description: "Lcapy derives symbolic transfer functions and SPICE netlists, which PySpice simulates numerically.",
      tools: ["lcapy"],
      target: "pyspice",
      dataFlow: "Symbolic circuit → transfer function → SPICE netlist → DC/AC/transient simulation",
      examples: ["lcapy_to_pyspice", "lcapy_to_sympy", "lcapy_to_control"],
    },
    {
      id: "symbolic-fem",
      label: "Symbolic → FEM",
      description: "SymPy symbolic PDEs converted to FEniCS UFL weak forms or Elmer SIF input for numerical solution.",
      tools: ["sympy"],
      target: "fenics",
      dataFlow: "Symbolic PDE expression → UFL code / SIF parameters → FEM solution",
      examples: ["sympy_to_fenics", "sympy_to_elmer"],
    },
    {
      id: "symbolic-animation",
      label: "Symbolic → Animation",
      description: "Symbolic expressions, orbits, or graphs animated using Manim for educational or presentation purposes.",
      tools: ["sympy", "rebound", "qutip", "networkx"],
      target: "manim",
      dataFlow: "Symbolic/numerical results → Manim scene → MP4/GIF animation",
      examples: ["sympy_to_manim", "rebound_to_manim", "qutip_to_manim", "networkx_to_manim"],
    },
    {
      id: "evolution-pipeline",
      label: "Population Genetics Pipeline",
      description: "Coalescent (msprime) and forward-time (SLiM, simuPOP) simulations output tree sequences analyzed by tskit.",
      tools: ["msprime", "slim", "simupop"],
      target: "tskit",
      dataFlow: "Genealogical history → tree sequence → diversity, Fst, recapitation",
      examples: ["slim_to_tskit", "msprime_to_tskit", "slim_to_msprime", "msprime_to_slim", "slim_to_simupop", "simupop_to_tskit", "simupop_to_msprime"],
    },
    {
      id: "sysbio-coupling",
      label: "Systems Biology Coupling",
      description: "BasiCO and Tellurium exchange SBML models and couple with upstream MD binding data or downstream neural models.",
      tools: ["basico", "tellurium", "openmm"],
      target: "basico",
      dataFlow: "SBML models, binding energies → pathway simulation → concentration time-series",
      examples: ["tellurium_to_copasi", "copasi_to_brian2", "openmm_to_basico", "openmm_to_tellurium", "fenics_to_basico", "fenics_to_tellurium"],
    },
    {
      id: "gr-coupling",
      label: "General Relativity Pipeline",
      description: "EinsteinPy analytical metrics feed into REBOUND N-body (GR corrections) or Einstein Toolkit (full NR validation).",
      tools: ["einsteinpy", "einstein_toolkit"],
      target: "rebound",
      dataFlow: "Analytical metric → GR corrections / initial data → N-body or NR evolution",
      examples: ["einsteinpy_to_rebound", "einsteinpy_to_etk", "etk_to_rebound"],
    },
    {
      id: "kinetics-multiphysics",
      label: "Chemical Kinetics → Multiphysics",
      description: "Cantera reaction kinetics feed into FEM solvers for reactive transport, or into systems biology for pathway modeling.",
      tools: ["cantera"],
      target: "fenics",
      dataFlow: "Reaction rates, heat release → FEM source terms / pathway parameters",
      examples: ["cantera_to_fenics", "cantera_to_basico", "cantera_to_tellurium", "cantera_to_elmer", "cantera_to_lammps"],
    },
    {
      id: "materials-multiscale",
      label: "Materials Multiscale",
      description: "Quantum ESPRESSO DFT properties feed into LAMMPS MD or FEM solvers for atomic-to-continuum bridging.",
      tools: ["qe"],
      target: "lammps",
      dataFlow: "DFT energies/forces → fitted potentials → large-scale MD → continuum properties",
      examples: ["qe_to_lammps", "qe_to_fenics", "qe_to_elmer", "qe_to_cantera", "lammps_to_mdanalysis", "lammps_to_elmer"],
    },
    {
      id: "quantum-computing",
      label: "Quantum Computing Interop",
      description: "Connections between quantum computing frameworks (Qiskit, PennyLane, QuTiP) and quantum chemistry codes.",
      tools: ["qiskit", "pennylane", "qutip", "pyscf", "psi4"],
      target: "qiskit",
      dataFlow: "Molecular Hamiltonians ↔ quantum circuits ↔ VQE optimization",
      examples: ["qiskit_to_qutip", "qiskit_to_pyscf", "pennylane_to_qiskit", "pennylane_to_qutip", "pennylane_to_pyscf", "psi4_to_qiskit", "psi4_to_pennylane"],
    },
    {
      id: "math-verification",
      label: "Mathematics Verification",
      description: "SymPy and SageMath computations formally verified by Lean 4, or enriched through GAP group theory.",
      tools: ["sympy", "sagemath", "lean4", "gap"],
      target: "lean4",
      dataFlow: "Symbolic result → formal statement → proof verification",
      examples: ["sympy_to_lean4", "sagemath_to_lean4", "sagemath_to_gap", "gap_to_sagemath", "lean4_to_gap", "lean4_to_sympy"],
    },
    {
      id: "format-conversion",
      label: "Format Conversion",
      description: "Open Babel converts between 110+ molecular formats, bridging tools that use different structure representations.",
      tools: ["rdkit", "openbabel", "mdanalysis"],
      target: "openbabel",
      dataFlow: "SMILES/PDB/SDF → Open Babel → target format (XYZ, MOL2, PDB, etc.)",
      examples: ["rdkit_to_openbabel", "openbabel_to_rdkit", "mdanalysis_to_openbabel", "openbabel_to_lammps", "openbabel_to_qe"],
    },
    {
      id: "circuit-qed",
      label: "Circuit QED / Quantum Hardware",
      description: "Research frontier: symbolic circuit parameters inform quantum Hamiltonians for superconducting qubit design.",
      tools: ["lcapy", "pyspice", "qutip", "qiskit", "pennylane"],
      target: "qutip",
      dataFlow: "LC parameters → transmon Hamiltonian → quantum circuit / readout design",
      examples: ["qutip_to_pyspice", "qutip_to_lcapy", "lcapy_to_qiskit", "lcapy_to_pennylane", "pyspice_to_qiskit", "pyspice_to_pennylane"],
    },
    {
      id: "optimization",
      label: "Symbolic → Optimization",
      description: "SymPy symbolic objectives and constraints feed into Pyomo for mathematical optimization.",
      tools: ["sympy"],
      target: "pyomo",
      dataFlow: "Symbolic expression → objective function / constraints → LP/MILP/NLP solution",
      examples: ["sympy_to_pyomo"],
    },
    {
      id: "deferred-bio",
      label: "Deferred Bio-Structure",
      description: "Future couplings for AlphaFold and PyRosetta protein structure prediction and design (not yet available).",
      tools: ["alphafold", "pyrosetta", "slim", "rdkit", "openbabel"],
      target: "openmm",
      dataFlow: "Sequence → predicted structure → MD refinement → design iteration",
      examples: ["alphafold_to_openmm", "alphafold_to_pyrosetta", "slim_to_alphafold", "rdkit_to_pyrosetta", "pyrosetta_to_openmm", "pyrosetta_to_basico"],
      deferred: true,
    },
  ],

  // Detailed documentation for key couplings
  details: {
    openmm_to_mdanalysis: {
      from: "openmm", to: "mdanalysis", type: "sequential",
      description: "Run molecular dynamics in OpenMM, then analyze the trajectory with MDAnalysis for RMSD, RMSF, contacts, and hydrogen bonds.",
      paramMap: { source_job_id: "$prev.job_id" },
      tier: "core",
      workedExample: "1. Run alanine dipeptide in OpenMM (10,000 steps, Langevin integrator, 300K). 2. MDAnalysis loads the trajectory via source_job_id. 3. Compute RMSD relative to first frame → plot backbone deviation over time.",
    },
    rdkit_to_pyscf: {
      from: "rdkit", to: "pyscf", type: "sequential",
      description: "Convert a SMILES string to a 3D conformer with RDKit, then compute electronic structure with PySCF (HF, DFT, MP2, or CCSD).",
      paramMap: { atom_coords: "$prev.result.atom_coords_pyscf" },
      tier: "core",
      workedExample: "1. Input aspirin SMILES: CC(=O)Oc1ccccc1C(=O)O. 2. RDKit generates 3D conformer via ETKDG. 3. PySCF reads atom_coords_pyscf and computes HF/STO-3G energy.",
    },
    gmsh_to_fenics: {
      from: "gmsh", to: "fenics", type: "sequential",
      description: "Generate a finite element mesh with Gmsh and import it into FEniCS for PDE solving (heat, elasticity, Stokes).",
      paramMap: { mesh_file: "$prev.result.mesh_file_path" },
      tier: "core",
      workedExample: "1. Gmsh creates a 2D box mesh with 0.1 element size. 2. FEniCS imports the .msh file via dolfinx.io. 3. Solve Poisson equation on the custom mesh.",
    },
    lcapy_to_pyspice: {
      from: "lcapy", to: "pyspice", type: "sequential",
      description: "Derive a symbolic transfer function and SPICE netlist with Lcapy, then simulate numerically with PySpice (DC/AC/transient).",
      paramMap: { netlist: "$prev.result.spice_netlist" },
      tier: "core",
      workedExample: "1. Lcapy analyzes an RC lowpass circuit symbolically. 2. Exports SPICE netlist. 3. PySpice runs AC sweep to generate Bode plot.",
    },
    slim_to_tskit: {
      from: "slim", to: "tskit", type: "sequential",
      description: "Run forward-time evolution in SLiM with tree sequence recording, then analyze diversity and Fst with tskit.",
      paramMap: { source_job_id: "$prev.job_id" },
      tier: "core",
      workedExample: "1. SLiM simulates neutral evolution (500 individuals, 100 generations). 2. tskit loads the tree sequence. 3. Compute nucleotide diversity (π) and plot site frequency spectrum.",
    },
    qutip_to_pyscf: {
      from: "qutip", to: "pyscf", type: "sequential",
      description: "Simulate quantum dynamics with QuTiP and use the resulting state to initialize PySCF electronic structure calculations.",
      paramMap: {},
      tier: "extension",
      workedExample: "1. QuTiP simulates Rabi oscillation on a qubit. 2. PySCF computes HF energy for H₂ molecule. 3. Compare quantum state evolution with electronic ground state.",
    },
    cantera_to_fenics: {
      from: "cantera", to: "fenics", type: "sequential",
      description: "Compute chemical kinetics (ignition, flame) with Cantera, then use heat release rates as source terms in FEniCS reactive transport PDE.",
      paramMap: { source_term: "$prev.result.heat_release_rate" },
      tier: "extension",
      workedExample: "1. Cantera computes H₂/O₂ ignition delay. 2. Heat release rate profile exported. 3. FEniCS solves heat equation with Cantera source term.",
    },
    qe_to_lammps: {
      from: "qe", to: "lammps", type: "sequential",
      description: "Compute DFT properties of a material with Quantum ESPRESSO, then use the results to parameterize LAMMPS MD simulations.",
      paramMap: { potential_data: "$prev.result" },
      tier: "core",
      workedExample: "1. QE computes silicon SCF energy and forces. 2. Results used to fit or validate LAMMPS potential parameters. 3. LAMMPS runs large-scale MD of the material.",
    },
    einsteinpy_to_rebound: {
      from: "einsteinpy", to: "rebound", type: "sequential",
      description: "Compute spacetime metric parameters with EinsteinPy, then use them for REBOUND N-body simulation with GR corrections via REBOUNDx.",
      paramMap: { gr_correction: "gr_full", M: "$prev.result.M" },
      tier: "extension",
      workedExample: "1. EinsteinPy computes Schwarzschild geodesic around a solar-mass BH. 2. REBOUND uses the central mass for full post-Newtonian GR corrections. 3. Compare geodesic with N-body orbit.",
    },
    sympy_to_manim: {
      from: "sympy", to: "manim", type: "sequential",
      description: "Derive symbolic expressions with SymPy and animate them with Manim for educational presentations.",
      paramMap: { expressions: "$prev.result.latex" },
      tier: "extension",
      workedExample: "1. SymPy solves x² - 2 = 0 → x = ±√2. 2. Manim animates the LaTeX equation and solution steps. 3. Output MP4 showing step-by-step derivation.",
    },
  },
};

// Helper: search couplings
export function searchCouplings(query) {
  if (!query) return couplingDocs.categories;
  const q = query.toLowerCase();
  return couplingDocs.categories.filter(cat =>
    cat.label.toLowerCase().includes(q) ||
    cat.description.toLowerCase().includes(q) ||
    cat.tools.some(t => t.includes(q)) ||
    (cat.target && cat.target.includes(q))
  );
}

// Helper: get coupling detail by key
export function getCouplingDetail(key) {
  return couplingDocs.details[key] || null;
}
