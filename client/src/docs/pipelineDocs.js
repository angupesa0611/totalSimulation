// Pipeline documentation data for all 11 named pipelines.

export const pipelineDocs = {
  quantum_to_organism: {
    label: "Quantum-to-Organism",
    summary: "7-step traverse from quantum mechanics to population genetics",
    steps: [
      { tool: "qutip", role: "Quantum state preparation — Rabi oscillation on a single qubit", duration: "~10s" },
      { tool: "pyscf", role: "Electronic structure — HF/STO-3G on H₂ molecule from quantum parameters", duration: "~30s" },
      { tool: "openmm", role: "Molecular dynamics — Langevin dynamics of small molecule at 300K", duration: "~2min" },
      { tool: "mdanalysis", role: "Trajectory analysis — RMSD computation from MD trajectory", duration: "~10s" },
      { tool: "basico", role: "Pathway modeling — Michaelis-Menten enzyme kinetics simulation", duration: "~5s" },
      { tool: "slim", role: "Population evolution — neutral drift of 500 individuals over 100 generations", duration: "~30s" },
      { tool: "tskit", role: "Tree sequence analysis — nucleotide diversity from SLiM output", duration: "~5s" },
    ],
    scientificContext: "This pipeline demonstrates the platform's full multi-scale capability: from quantum dynamics through molecular mechanics, biochemical pathways, and up to population genetics. Each step operates at a different spatial and temporal scale, connected by data transformations that bridge the scale gap.",
    recommendedParams: {
      qutip: { system_type: "qubit_rabi", qubit_rabi: { omega: 1.0, delta: 0.0, psi0: "ground", tmax: 25.0 } },
      openmm: { steps: 5000, report_interval: 50 },
      slim: { population_size: 500, n_generations: 100 },
    },
    expectedRuntime: "~5 minutes total",
  },

  mercury_precession: {
    label: "Mercury GR Precession",
    summary: "Mercury perihelion precession with REBOUNDx GR corrections",
    steps: [
      { tool: "rebound", role: "N-body integration with full post-Newtonian GR corrections (IAS15 integrator)", duration: "~30s" },
    ],
    scientificContext: "One of the classic tests of General Relativity: Mercury's perihelion precesses by 42.98 arcseconds per century due to GR effects beyond Newtonian gravity. This single-step pipeline uses REBOUNDx's gr_full correction to demonstrate this precession.",
    recommendedParams: {
      rebound: { gr_correction: "gr_full", integrator: "ias15", tmax: 62.83, n_outputs: 500 },
    },
    expectedRuntime: "~30 seconds",
  },

  qmmm_enzyme: {
    label: "QM/MM Enzyme Catalysis",
    summary: "Drug binding: ligand identification → QM/MM active site → trajectory analysis → pathway kinetics",
    steps: [
      { tool: "rdkit", role: "Ligand preparation — compute molecular descriptors from aspirin SMILES", duration: "~5s" },
      { tool: "qmmm", role: "QM/MM simulation — HF/STO-3G for active site with OpenMM MM surroundings", duration: "~2min" },
      { tool: "mdanalysis", role: "Trajectory analysis — RMSD of the bound complex", duration: "~10s" },
      { tool: "basico", role: "Kinetic modeling — enzyme kinetics of the catalytic reaction", duration: "~5s" },
    ],
    scientificContext: "Models enzyme catalysis from molecular to systems level: identify the drug molecule, compute quantum-accurate energies at the active site while treating the rest of the protein classically, analyze the resulting trajectory, and model the reaction kinetics.",
    recommendedParams: {
      rdkit: { simulation_type: "descriptors", smiles: "CC(=O)Oc1ccccc1C(=O)O" },
      qmmm: { qm_method: "hf", qm_basis: "sto-3g" },
    },
    expectedRuntime: "~3 minutes total",
  },

  evolution_structure: {
    label: "Evolution → Structure Feedback",
    summary: "Coalescent → forward sim → tree analysis",
    steps: [
      { tool: "msprime", role: "Coalescent history — generate genealogy for 50 samples over 100kb region", duration: "~5s" },
      { tool: "slim", role: "Forward evolution — nucleotide-level evolution of 500 individuals", duration: "~30s" },
      { tool: "tskit", role: "Diversity analysis — compute diversity statistics from tree sequence", duration: "~5s" },
    ],
    scientificContext: "Combines backward-time coalescent simulation (msprime) with forward-time evolution (SLiM) to model evolutionary dynamics across time scales. The tskit analysis step computes summary statistics from the combined genealogy.",
    recommendedParams: {
      msprime: { sample_size: 50, sequence_length: 100000, recombination_rate: 1e-8, mutation_rate: 1e-8 },
      slim: { simulation_type: "nucleotide_evolution", population_size: 500, n_generations: 200 },
    },
    expectedRuntime: "~1 minute total",
  },

  multiscale_tissue: {
    label: "Multiscale Tissue Modeling",
    summary: "FEniCS tissue stress → COPASI biochemical response",
    steps: [
      { tool: "fenics", role: "Tissue mechanics — solve elasticity PDE for tissue stress field", duration: "~30s" },
      { tool: "basico", role: "Biochemical response — enzyme kinetics driven by mechanical stress", duration: "~5s" },
    ],
    scientificContext: "Models mechanotransduction: how mechanical forces on tissue (computed with FEM) trigger biochemical signaling cascades. The FEniCS stress field informs the BasiCO reaction network parameters, demonstrating bidirectional multiscale coupling between continuum mechanics and systems biology.",
    recommendedParams: {
      fenics: { simulation_type: "elasticity" },
      basico: { model_type: "enzyme_kinetics" },
    },
    expectedRuntime: "~1 minute total",
  },

  drug_discovery: {
    label: "Drug Discovery",
    summary: "SMILES → quantum properties → MD binding → trajectory analysis → pathway impact",
    steps: [
      { tool: "rdkit", role: "Molecular properties — descriptors and 3D conformer from SMILES", duration: "~5s" },
      { tool: "pyscf", role: "Quantum chemistry — HF/STO-3G electronic energy and orbitals", duration: "~30s" },
      { tool: "openmm", role: "MD simulation — Langevin dynamics to sample binding conformations", duration: "~2min" },
      { tool: "mdanalysis", role: "Binding analysis — RMSD tracking of ligand position", duration: "~10s" },
      { tool: "basico", role: "Pathway modeling — impact on enzyme kinetics", duration: "~5s" },
    ],
    scientificContext: "A complete drug discovery workflow: start from a drug molecule's SMILES, compute its quantum properties, simulate its binding dynamics with MD, analyze the trajectory, and predict its impact on metabolic pathways. Each step adds a deeper level of analysis.",
    recommendedParams: {
      rdkit: { simulation_type: "descriptors", smiles: "CC(=O)Oc1ccccc1C(=O)O" },
      pyscf: { method: "hf", basis: "sto-3g" },
      openmm: { steps: 5000, report_interval: 50 },
    },
    expectedRuntime: "~4 minutes total",
  },

  materials_discovery: {
    label: "Materials Discovery",
    summary: "DFT properties → large-scale MD → trajectory analysis → continuum simulation",
    steps: [
      { tool: "qe", role: "DFT calculation — self-consistent field for material properties", duration: "~2min" },
      { tool: "lammps", role: "MD simulation — large-scale Lennard-Jones fluid dynamics", duration: "~1min" },
      { tool: "mdanalysis", role: "Trajectory analysis — RMSD and RDF from MD trajectory", duration: "~10s" },
      { tool: "fenics", role: "Continuum simulation — heat equation with material parameters", duration: "~30s" },
    ],
    scientificContext: "Bridges quantum-mechanical accuracy with macroscopic engineering: DFT computes atomic-level properties, LAMMPS scales up to thousands of atoms, MDAnalysis extracts statistics, and FEniCS models the continuum-scale behavior. This atomic-to-continuum pipeline is central to computational materials science.",
    recommendedParams: {
      qe: { simulation_type: "scf" },
      lammps: { simulation_type: "lj_fluid" },
      fenics: { simulation_type: "heat" },
    },
    expectedRuntime: "~5 minutes total",
  },

  reactive_multiphysics: {
    label: "Reactive Multiphysics",
    summary: "Symbolic rate expressions → detailed kinetics → reactive transport PDE on generated mesh",
    steps: [
      { tool: "sympy", role: "Symbolic rates — derive rate expression (k*A - k_r*B)", duration: "~5s" },
      { tool: "cantera", role: "Detailed kinetics — ignition delay with symbolic rate expression", duration: "~30s" },
      { tool: "gmsh", role: "Mesh generation — 3D box mesh for reactive transport domain", duration: "~10s" },
      { tool: "fenics", role: "Reactive transport — heat equation with Cantera source terms on Gmsh mesh", duration: "~1min" },
    ],
    scientificContext: "Demonstrates the symbolic-to-numerical pipeline: derive rate laws symbolically, validate them with detailed chemical kinetics, generate a computational mesh, and solve the reactive transport PDE. This pattern applies to combustion, catalysis, and environmental modeling.",
    recommendedParams: {
      sympy: { simulation_type: "solve", expression: "k*A - k_r*B", variable: "A" },
      cantera: { simulation_type: "ignition_delay" },
      gmsh: { mesh_type: "box_3d" },
      fenics: { simulation_type: "heat" },
    },
    expectedRuntime: "~2 minutes total",
  },

  math_verification: {
    label: "Mathematics Verification Loop",
    summary: "Symbolic computation → algebraic enrichment → formal proof verification",
    steps: [
      { tool: "sympy", role: "Symbolic computation — solve x² - 2 = 0", duration: "~5s" },
      { tool: "sagemath", role: "Algebraic analysis — Gröbner basis computation for polynomial system", duration: "~10s" },
      { tool: "lean4", role: "Formal verification — verify the mathematical result in Lean 4", duration: "~15s" },
    ],
    scientificContext: "Ensures mathematical correctness through three layers: SymPy computes symbolically, SageMath enriches with advanced algebra, and Lean 4 formally verifies the result. This verified computation pattern is crucial for mathematical research where correctness guarantees are needed.",
    recommendedParams: {
      sympy: { simulation_type: "solve", expression: "x**2 - 2", variable: "x" },
      sagemath: { simulation_type: "groebner_basis" },
      lean4: { simulation_type: "verify" },
    },
    expectedRuntime: "~30 seconds total",
  },

  classical_circuit: {
    label: "Classical Circuit Design",
    summary: "Symbolic analysis → numerical SPICE simulation → EM field verification",
    steps: [
      { tool: "lcapy", role: "Symbolic circuit — derive transfer function and SPICE netlist", duration: "~5s" },
      { tool: "pyspice", role: "SPICE simulation — transient analysis with ngspice backend", duration: "~10s" },
      { tool: "fenics", role: "EM field verification — heat equation approximation of EM effects", duration: "~30s" },
    ],
    scientificContext: "A circuit design workflow: analyze the circuit symbolically to understand frequency response, simulate numerically to verify time-domain behavior, and optionally solve for electromagnetic field effects. The Lcapy → PySpice coupling is the core of analog circuit design.",
    recommendedParams: {
      lcapy: { simulation_type: "transfer_function" },
      pyspice: { simulation_type: "transient" },
      fenics: { simulation_type: "heat" },
    },
    expectedRuntime: "~1 minute total",
  },

  quantum_chemistry_qc: {
    label: "QC on Quantum Computers",
    summary: "Molecular structure → Hamiltonian → qubit mapping → variational quantum optimization",
    steps: [
      { tool: "rdkit", role: "Molecular structure — generate water molecule geometry from SMILES", duration: "~5s" },
      { tool: "pyscf", role: "Hamiltonian — compute molecular integrals with HF/STO-3G", duration: "~30s" },
      { tool: "qiskit", role: "VQE (Qiskit) — map Hamiltonian to qubits and run variational solver", duration: "~1min" },
      { tool: "pennylane", role: "Optimization (PennyLane) — differentiable VQE with gradient-based optimizer", duration: "~1min" },
    ],
    scientificContext: "Bridges classical and quantum computing for chemistry: RDKit provides the molecular structure, PySCF computes the electronic Hamiltonian, Qiskit maps it to a quantum circuit, and PennyLane optimizes the variational parameters using automatic differentiation. This is the standard workflow for quantum chemistry on near-term quantum computers.",
    recommendedParams: {
      rdkit: { simulation_type: "descriptors", smiles: "O" },
      pyscf: { method: "hf", basis: "sto-3g" },
      qiskit: { simulation_type: "vqe" },
      pennylane: { simulation_type: "vqe" },
    },
    expectedRuntime: "~3 minutes total",
  },
};

// Helper: get all pipeline keys
export const allPipelineKeys = Object.keys(pipelineDocs);

// Helper: search pipelines
export function searchPipelines(query) {
  if (!query) return Object.entries(pipelineDocs).map(([key, doc]) => ({ key, ...doc }));
  const q = query.toLowerCase();
  return Object.entries(pipelineDocs)
    .filter(([key, doc]) =>
      key.includes(q) ||
      doc.label.toLowerCase().includes(q) ||
      doc.summary.toLowerCase().includes(q) ||
      doc.scientificContext.toLowerCase().includes(q) ||
      doc.steps.some(s => s.tool.includes(q) || s.role.toLowerCase().includes(q))
    )
    .map(([key, doc]) => ({ key, ...doc }));
}
