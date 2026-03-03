// Tool documentation data for all 51 tools in the platform.
// Each entry follows a consistent schema: name, layer, summary, description,
// capabilities, whenToUse, alternatives, params, outputs, examples, references, license, limitations.

export const toolDocs = {
  // ═══════════════════════════════════════════
  // ASTROPHYSICS
  // ═══════════════════════════════════════════
  rebound: {
    name: "REBOUND",
    layer: "astrophysics",
    summary: "N-body gravitational dynamics simulator",
    description:
      "REBOUND is a multi-purpose N-body integrator for collisional and collisionless dynamics. It supports symplectic (WHFast, leapfrog), high-accuracy (IAS15), and hybrid (Mercurius) integrators. REBOUNDx provides additional forces including general relativistic corrections, radiation pressure, and tidal forces.",
    capabilities: [
      "Symplectic integration (WHFast) for long-term stability",
      "High-accuracy IAS15 integrator (15th order, adaptive)",
      "Hybrid Mercurius integrator for close encounters",
      "REBOUNDx post-Newtonian GR corrections (1PN, full PN, potential-only)",
      "Radiation pressure and tidal force modeling",
      "Arbitrary N-body initial conditions",
    ],
    whenToUse:
      "Use REBOUND for gravitational N-body problems: planetary orbits, asteroid dynamics, stellar clusters, ring systems. Choose WHFast for long integrations, IAS15 for close encounters or high precision, Mercurius for mixed scenarios.",
    alternatives:
      "For relativistic corrections beyond post-Newtonian, combine with EinsteinPy or NRPy+. For non-gravitational particle dynamics, consider PyBullet or LAMMPS.",
    params: {
      integrator: {
        type: "select",
        description: "Integration algorithm",
        options: {
          ias15: "15th-order adaptive (highest accuracy, slower)",
          whfast: "Symplectic Wisdom-Holman (fast, long-term stable)",
          mercurius: "Hybrid WHFast + IAS15 for close encounters",
          leapfrog: "2nd-order symplectic (simplest)",
        },
      },
      tmax: { type: "number", unit: "years (2π = 1 year)", description: "Total simulation time" },
      n_outputs: { type: "number", description: "Number of output snapshots", range: "50–2000" },
      dt: { type: "number", unit: "years", description: "Fixed timestep (WHFast/leapfrog) or initial guess (IAS15)" },
      gr_correction: {
        type: "select",
        description: "General relativistic correction via REBOUNDx",
        options: {
          none: "No GR corrections",
          gr: "Post-Newtonian 1PN (standard)",
          gr_full: "Full post-Newtonian (most accurate)",
          gr_potential: "Potential-only (fast approximation)",
        },
      },
      extra_forces: {
        type: "multiselect",
        description: "Additional REBOUNDx forces",
        options: {
          radiation_pressure: "Solar radiation pressure on small bodies",
          tides_constant_time_lag: "Tidal forces with constant time lag model",
        },
      },
      particles: { type: "json", description: "Array of particle objects with mass, position, velocity" },
    },
    outputs: {
      positions: "3D positions per body per frame (x, y, z arrays)",
      velocities: "3D velocities per body per frame",
      energies: "Total, kinetic, and potential energy per frame",
      times: "Time array for each output frame",
    },
    examples: ["Inner Solar System preset", "Mercury precession with GR corrections"],
    references: [
      { label: "REBOUND documentation", url: "https://rebound.readthedocs.io" },
      { label: "REBOUNDx additional forces", url: "https://reboundx.readthedocs.io" },
    ],
    license: "GPL-3.0",
    limitations: [
      "No relativistic effects without REBOUNDx",
      "CPU-only (no GPU acceleration)",
      "Post-Newtonian corrections are approximate beyond strong-field regime",
    ],
  },

  // ═══════════════════════════════════════════
  // QUANTUM MECHANICS
  // ═══════════════════════════════════════════
  qutip: {
    name: "QuTiP",
    layer: "quantum",
    summary: "Quantum dynamics simulator",
    description:
      "QuTiP (Quantum Toolbox in Python) solves the dynamics of open quantum systems using master equations, Monte Carlo, and Floquet methods. It handles qubits, spin chains, cavity QED, and open quantum systems with Lindblad decoherence.",
    capabilities: [
      "Schrödinger and master equation solvers (mesolve, sesolve)",
      "Monte Carlo wave function method (mcsolve)",
      "Bloch sphere visualization",
      "Spin chain Hamiltonians (Heisenberg, Ising)",
      "Jaynes-Cummings and Rabi models",
      "Lindblad decoherence and collapse operators",
    ],
    whenToUse:
      "Use QuTiP for quantum dynamics: qubit evolution, spin systems, cavity QED, open quantum systems. It excels at small-to-medium Hilbert spaces (up to ~15 qubits equivalent).",
    alternatives:
      "For quantum computing circuits, use Qiskit or PennyLane. For electronic structure of molecules, use PySCF or Psi4.",
    params: {
      system_type: {
        type: "select",
        description: "Type of quantum system to simulate",
        options: {
          qubit_rabi: "Single qubit Rabi oscillation",
          spin_chain: "Heisenberg spin chain",
          jaynes_cummings: "Jaynes-Cummings atom-cavity model",
        },
      },
      "qubit_rabi.omega": { type: "number", unit: "GHz", description: "Rabi frequency" },
      "qubit_rabi.delta": { type: "number", unit: "GHz", description: "Detuning from resonance" },
      "qubit_rabi.psi0": { type: "select", description: "Initial state", options: { ground: "|0⟩", excited: "|1⟩", superposition: "(|0⟩+|1⟩)/√2" } },
      "qubit_rabi.tmax": { type: "number", unit: "ns", description: "Evolution time" },
      "spin_chain.n_spins": { type: "number", description: "Number of spins in chain", range: "2–10" },
      "spin_chain.J": { type: "number", description: "Exchange coupling constant" },
      "spin_chain.B": { type: "number", description: "External magnetic field" },
      "jaynes_cummings.n_photons": { type: "number", description: "Photon number cutoff", range: "2–20" },
      "jaynes_cummings.g": { type: "number", description: "Atom-cavity coupling strength" },
      "jaynes_cummings.kappa": { type: "number", description: "Cavity decay rate" },
    },
    outputs: {
      expectation_values: "Time-dependent expectation values of observables",
      bloch: "Bloch sphere coordinates (x, y, z) for qubit states",
      states: "Full quantum state at each time step (density matrix or state vector)",
    },
    examples: ["Rabi Oscillation preset", "Spin chain dynamics"],
    references: [
      { label: "QuTiP documentation", url: "https://qutip.org/docs/latest/" },
    ],
    license: "BSD-3-Clause",
    limitations: [
      "Limited to small-to-medium Hilbert spaces (~2^15 states)",
      "Not designed for molecular electronic structure",
      "CPU-only",
    ],
  },

  pennylane: {
    name: "PennyLane",
    layer: "quantum",
    summary: "Differentiable quantum computing — VQE, QNN",
    description:
      "PennyLane is a cross-platform library for differentiable programming of quantum computers. It provides automatic differentiation of quantum circuits, variational quantum eigensolver (VQE), quantum neural networks, and interfaces to multiple quantum backends.",
    capabilities: [
      "Variational Quantum Eigensolver (VQE) for molecular ground states",
      "Quantum Neural Networks (QNN) with trainable parameters",
      "Automatic differentiation of quantum circuits (parameter-shift rule)",
      "Multiple backends: default.qubit, qiskit.aer, lightning.qubit",
      "Molecular Hamiltonian construction from geometry",
    ],
    whenToUse:
      "Use PennyLane for variational quantum algorithms, quantum machine learning, or when you need differentiable quantum circuits. Ideal for VQE molecular energy calculations and hybrid quantum-classical optimization.",
    alternatives:
      "For pure circuit simulation without gradients, use Qiskit. For non-variational quantum dynamics, use QuTiP.",
    params: {
      simulation_type: {
        type: "select",
        description: "Type of quantum computation",
        options: {
          vqe: "Variational Quantum Eigensolver — molecular ground state energy",
          qnn: "Quantum Neural Network — parametric circuit training",
          circuit: "Custom quantum circuit execution",
        },
      },
      n_qubits: { type: "number", description: "Number of qubits", range: "2–20" },
      n_layers: { type: "number", description: "Number of variational layers" },
      max_iterations: { type: "number", description: "Optimizer iterations for VQE/QNN" },
    },
    outputs: {
      energy: "Ground state energy (VQE)",
      parameters: "Optimized circuit parameters",
      convergence: "Energy vs iteration history",
      circuit: "Circuit diagram and gate sequence",
    },
    examples: ["H₂ VQE preset"],
    references: [
      { label: "PennyLane documentation", url: "https://pennylane.ai/qml/" },
    ],
    license: "Apache-2.0",
    limitations: [
      "Limited to ~20 qubits on classical simulators",
      "VQE convergence depends heavily on ansatz choice",
      "No noise models by default (use qiskit.aer backend for noise)",
    ],
  },

  qiskit: {
    name: "Qiskit",
    layer: "circuits",
    summary: "Quantum computing — circuits, Aer simulation, VQE",
    description:
      "Qiskit is IBM's open-source quantum computing framework. It provides tools for building quantum circuits, simulating them on classical hardware (Aer), and running on real IBM quantum devices. Includes Qiskit Nature for molecular simulation.",
    capabilities: [
      "Quantum circuit construction and visualization",
      "Aer high-performance simulator (statevector, QASM, density matrix)",
      "VQE with Qiskit Nature for molecular Hamiltonians",
      "Quantum error correction codes (stabilizer circuits)",
      "Bell state preparation and measurement",
      "OpenQASM 2.0/3.0 circuit export",
    ],
    whenToUse:
      "Use Qiskit for quantum circuit simulation, quantum algorithms (VQE, QAOA, Grover), and quantum error correction. Best when you need circuit-level control or IBM Q device compatibility.",
    alternatives:
      "For differentiable circuits, use PennyLane. For open quantum system dynamics (not circuits), use QuTiP.",
    params: {
      simulation_type: {
        type: "select",
        description: "Type of quantum simulation",
        options: {
          bell_state: "Bell state preparation and measurement",
          vqe: "Variational Quantum Eigensolver for molecules",
          custom_circuit: "Custom circuit from gate sequence",
          stabilizer_codes: "Quantum error correction stabilizer codes",
        },
      },
      n_qubits: { type: "number", description: "Number of qubits", range: "1–30" },
      shots: { type: "number", description: "Number of measurement shots", range: "100–10000" },
    },
    outputs: {
      counts: "Measurement outcome counts (bitstring histogram)",
      statevector: "Full quantum state vector",
      energy: "Ground state energy (VQE)",
      circuit_diagram: "ASCII or LaTeX circuit diagram",
      qasm_str: "OpenQASM 2.0 export",
    },
    examples: ["Bell State preset", "H₂ VQE"],
    references: [
      { label: "Qiskit documentation", url: "https://docs.quantum.ibm.com/" },
    ],
    license: "Apache-2.0",
    limitations: [
      "Classical simulation limited to ~30 qubits (Aer)",
      "No native gradient computation (use PennyLane for that)",
      "VQE for molecules requires Qiskit Nature addon",
    ],
  },

  // ═══════════════════════════════════════════
  // MOLECULAR DYNAMICS
  // ═══════════════════════════════════════════
  openmm: {
    name: "OpenMM",
    layer: "molecular",
    summary: "GPU-accelerated molecular dynamics",
    description:
      "OpenMM is a high-performance molecular dynamics toolkit with GPU acceleration. It supports standard biomolecular force fields (AMBER, CHARMM, OPLS), Langevin/Verlet/Brownian integrators, and can simulate proteins, nucleic acids, and small molecules.",
    capabilities: [
      "GPU-accelerated MD via CUDA/OpenCL",
      "Langevin, Verlet, and Brownian integrators",
      "AMBER, CHARMM, and OPLS force fields",
      "PDB structure input",
      "Implicit and explicit solvent models",
      "Energy minimization",
    ],
    whenToUse:
      "Use OpenMM for biomolecular MD simulations: protein dynamics, ligand binding, conformational sampling. Ideal when GPU acceleration is needed for large systems.",
    alternatives:
      "For materials science MD, use LAMMPS. For high-throughput MD, use GROMACS. For very large biological systems, use NAMD.",
    params: {
      integrator: {
        type: "select",
        description: "Integration method",
        options: {
          langevin: "Langevin dynamics (thermostat built-in)",
          verlet: "Velocity Verlet (NVE ensemble)",
          brownian: "Brownian dynamics (overdamped limit)",
        },
      },
      temperature: { type: "number", unit: "K", description: "Simulation temperature" },
      dt: { type: "number", unit: "ps", description: "Integration timestep" },
      steps: { type: "number", description: "Number of MD steps", range: "1000–100000" },
      report_interval: { type: "number", description: "Frames between trajectory outputs" },
      pdb_content: { type: "text", description: "PDB structure (loaded from preset or pipeline)" },
    },
    outputs: {
      positions: "Atomic positions per frame (trajectory)",
      energies: "Potential, kinetic, and total energy per frame",
      pdb_block: "Final structure as PDB text",
      temperature: "Instantaneous temperature per frame",
    },
    examples: ["Alanine Dipeptide preset", "QM/MM Alanine preset"],
    references: [
      { label: "OpenMM documentation", url: "http://docs.openmm.org/" },
    ],
    license: "MIT",
    limitations: [
      "Requires PDB input structure",
      "GPU container needed for acceleration (separate worker)",
      "Limited reactive chemistry (no bond breaking/forming)",
    ],
  },

  gromacs: {
    name: "GROMACS",
    layer: "molecular",
    summary: "High-performance molecular dynamics",
    description:
      "GROMACS is one of the fastest molecular dynamics packages, optimized for biomolecular simulations. It supports extensive force fields, free energy calculations, and advanced sampling methods.",
    capabilities: [
      "Highly optimized MD engine (SIMD, GPU)",
      "AMBER, CHARMM, OPLS-AA, GROMOS force fields",
      "Free energy perturbation",
      "Enhanced sampling (replica exchange, metadynamics)",
      "Trajectory analysis tools",
    ],
    whenToUse:
      "Use GROMACS for large-scale biomolecular MD when maximum performance is critical. Excellent for membrane simulations, protein-ligand systems, and free energy calculations.",
    alternatives:
      "For simpler setup, use OpenMM. For materials science, use LAMMPS.",
    params: {
      simulation_type: {
        type: "select",
        description: "Type of GROMACS simulation",
        options: {
          md: "Standard molecular dynamics",
          em: "Energy minimization",
          nvt: "NVT equilibration",
          npt: "NPT equilibration",
        },
      },
      integrator: { type: "select", description: "Integration algorithm", options: { md: "Leap-frog", "md-vv": "Velocity Verlet", steep: "Steepest descent (minimization)" } },
      dt: { type: "number", unit: "ps", description: "Timestep" },
      nsteps: { type: "number", description: "Number of integration steps" },
      temperature: { type: "number", unit: "K", description: "Reference temperature" },
    },
    outputs: {
      trajectory: "Molecular trajectory frames",
      energies: "System energies over time",
      structure: "Final structure",
    },
    examples: ["Lysozyme in water preset"],
    references: [
      { label: "GROMACS documentation", url: "https://manual.gromacs.org/" },
    ],
    license: "LGPL-2.1",
    limitations: [
      "Complex input file setup (topology, parameters)",
      "Requires pre-built topology files",
      "Less flexible scripting than OpenMM",
    ],
  },

  namd: {
    name: "NAMD",
    layer: "molecular",
    summary: "Scalable molecular dynamics",
    description:
      "NAMD is a parallel molecular dynamics code for large biomolecular systems. It uses the CHARMM force field and excels at scaling across many CPU cores for very large systems (millions of atoms).",
    capabilities: [
      "Excellent parallel scaling on HPC clusters",
      "CHARMM force field support",
      "Steered MD and free energy methods",
      "Constant pressure/temperature ensembles",
      "Enhanced sampling (ABF, metadynamics)",
    ],
    whenToUse:
      "Use NAMD for very large biomolecular systems (millions of atoms) where parallel scaling is critical. Also excellent for steered MD and free energy calculations.",
    alternatives:
      "For GPU-accelerated MD, use OpenMM. For high-throughput smaller systems, use GROMACS.",
    params: {
      simulation_type: { type: "select", description: "Simulation type", options: { md: "Standard MD", minimize: "Energy minimization" } },
      temperature: { type: "number", unit: "K", description: "Simulation temperature" },
      timestep: { type: "number", unit: "fs", description: "Integration timestep" },
      num_steps: { type: "number", description: "Number of simulation steps" },
    },
    outputs: {
      trajectory: "DCD trajectory file",
      energies: "Energy log over time",
      structure: "Final PDB coordinates",
    },
    examples: [],
    references: [
      { label: "NAMD documentation", url: "https://www.ks.uiuc.edu/Research/namd/" },
    ],
    license: "Free for non-commercial use",
    limitations: [
      "CHARMM force field primarily",
      "Complex configuration file syntax",
      "CPU-focused (less GPU optimization than OpenMM)",
    ],
  },

  // ═══════════════════════════════════════════
  // ELECTRONIC STRUCTURE
  // ═══════════════════════════════════════════
  pyscf: {
    name: "PySCF",
    layer: "electronic",
    summary: "Electronic structure calculations (HF, DFT, MP2, CCSD)",
    description:
      "PySCF is a Python-based electronic structure package supporting Hartree-Fock, DFT, MP2, CCSD, and other post-HF methods. It handles molecular and periodic systems with Gaussian basis sets.",
    capabilities: [
      "Restricted/Unrestricted Hartree-Fock (RHF/UHF)",
      "Density Functional Theory (DFT) with many functionals",
      "MP2 and CCSD post-Hartree-Fock methods",
      "Multiple basis sets (STO-3G, 6-31G, cc-pVDZ, etc.)",
      "Molecular orbital visualization",
      "Periodic boundary conditions (pbc module)",
    ],
    whenToUse:
      "Use PySCF for quantum chemistry calculations on molecules: ground state energies, orbital analysis, electron correlation. Ideal for small-to-medium molecules (up to ~50 atoms with HF/DFT).",
    alternatives:
      "For SAPT interaction energies, use Psi4. For periodic solid-state DFT, use Quantum ESPRESSO.",
    params: {
      method: {
        type: "select",
        description: "Electronic structure method",
        options: { hf: "Hartree-Fock", dft: "Density Functional Theory", mp2: "MP2 perturbation theory", ccsd: "Coupled Cluster Singles and Doubles" },
      },
      basis: {
        type: "select",
        description: "Basis set",
        options: { "sto-3g": "Minimal (fast, qualitative)", "6-31g": "Split-valence (good balance)", "cc-pvdz": "Correlation-consistent (accurate)", "cc-pvtz": "Triple-zeta (high accuracy)" },
      },
      atom_coords: { type: "text", description: "Atomic coordinates (e.g., 'H 0 0 0; H 0 0 0.74')" },
      charge: { type: "number", description: "Molecular charge" },
      spin: { type: "number", description: "Spin multiplicity (2S)" },
    },
    outputs: {
      total_energy: "Total electronic energy (Hartree)",
      orbital_energies: "Molecular orbital energies",
      dipole_moment: "Electric dipole moment",
      pdb_block: "Optimized structure as PDB (if geometry optimization)",
      molecular_geometry: "Geometry string for downstream tools",
    },
    examples: ["H₂ Hartree-Fock preset"],
    references: [
      { label: "PySCF documentation", url: "https://pyscf.org/user.html" },
    ],
    license: "Apache-2.0",
    limitations: [
      "CPU-only (no GPU acceleration)",
      "CCSD scales as O(N^6) — limited to small molecules",
      "No analytical gradients for all methods",
    ],
  },

  psi4: {
    name: "Psi4",
    layer: "electronic",
    summary: "Ab initio quantum chemistry with SAPT",
    description:
      "Psi4 is a quantum chemistry package specializing in symmetry-adapted perturbation theory (SAPT) for intermolecular interactions, alongside standard HF, DFT, MP2, and coupled cluster methods.",
    capabilities: [
      "SAPT for non-covalent interaction analysis",
      "HF, DFT, MP2, CCSD(T) methods",
      "Geometry optimization",
      "Frequency analysis and thermochemistry",
      "Basis set superposition error (BSSE) corrections",
    ],
    whenToUse:
      "Use Psi4 for intermolecular interaction energies (SAPT), benchmark-quality quantum chemistry, and when you need decomposed interaction energy components (electrostatic, induction, dispersion, exchange).",
    alternatives:
      "For routine molecular calculations, PySCF is more lightweight. For solid-state, use Quantum ESPRESSO.",
    params: {
      method: {
        type: "select",
        description: "Computation method",
        options: { sapt0: "SAPT0 interaction energy", hf: "Hartree-Fock", mp2: "MP2", "ccsd(t)": "Gold-standard coupled cluster" },
      },
      basis: { type: "select", description: "Basis set", options: { "jun-cc-pvdz": "SAPT-optimized", "cc-pvdz": "Correlation-consistent DZ", "cc-pvtz": "Correlation-consistent TZ" } },
      geometry: { type: "text", description: "Molecular geometry in XYZ or Z-matrix format" },
    },
    outputs: {
      total_energy: "Total interaction or molecular energy",
      sapt_components: "Electrostatic, exchange, induction, dispersion (SAPT only)",
      optimized_geometry: "Optimized molecular coordinates",
    },
    examples: ["Water dimer SAPT preset"],
    references: [
      { label: "Psi4 documentation", url: "https://psicode.org/psi4manual/master/" },
    ],
    license: "LGPL-3.0",
    limitations: [
      "SAPT limited to dimer interactions",
      "High-level methods very computationally expensive",
      "CPU-only",
    ],
  },

  // ═══════════════════════════════════════════
  // ANALYSIS
  // ═══════════════════════════════════════════
  mdanalysis: {
    name: "MDAnalysis",
    layer: "analysis",
    summary: "Trajectory analysis and post-processing",
    description:
      "MDAnalysis is a Python library for analyzing molecular dynamics trajectories. It reads trajectories from OpenMM, GROMACS, NAMD, LAMMPS, and computes structural properties like RMSD, RMSF, hydrogen bonds, and contact maps.",
    capabilities: [
      "RMSD and RMSF calculations",
      "Hydrogen bond analysis",
      "Radial distribution functions (RDF)",
      "Contact map analysis",
      "Distance and angle measurements",
      "Reads DCD, XTC, TRR, PDB, and many other formats",
    ],
    whenToUse:
      "Use MDAnalysis after running any MD simulation (OpenMM, GROMACS, NAMD, LAMMPS) to analyze the trajectory. Essential for extracting quantitative structural and dynamic information from simulations.",
    alternatives:
      "MDTraj is a lighter alternative. For visualization-focused analysis, use VMD.",
    params: {
      analysis_type: {
        type: "select",
        description: "Type of trajectory analysis",
        options: { rmsd: "Root mean square deviation", rmsf: "Root mean square fluctuation", contacts: "Contact map analysis", distances: "Distance measurements", hbonds: "Hydrogen bond analysis" },
      },
      source_job_id: { type: "text", description: "Job ID of the MD simulation to analyze (auto-set in pipelines)" },
      selection: { type: "text", description: "MDAnalysis atom selection string (e.g., 'protein and name CA')" },
    },
    outputs: {
      rmsd: "RMSD vs time plot data",
      rmsf: "Per-residue RMSF values",
      contacts: "Contact map matrix",
      distances: "Distance time series",
    },
    examples: ["Alanine RMSD analysis"],
    references: [
      { label: "MDAnalysis documentation", url: "https://docs.mdanalysis.org/" },
    ],
    license: "GPL-2.0+",
    limitations: [
      "Analysis only — does not run simulations",
      "Requires trajectory data from a prior MD run",
      "Large trajectories can be memory-intensive",
    ],
  },

  // ═══════════════════════════════════════════
  // MULTISCALE
  // ═══════════════════════════════════════════
  qmmm: {
    name: "QM/MM",
    layer: "multiscale",
    summary: "Hybrid QM/MM via ASH (PySCF + OpenMM)",
    description:
      "QM/MM combines quantum mechanical (QM) treatment of an active site with molecular mechanical (MM) treatment of the surroundings. This implementation uses ASH to couple PySCF (QM region) with OpenMM (MM region).",
    capabilities: [
      "QM/MM energy and gradient calculations",
      "PySCF HF/DFT for QM region",
      "OpenMM force fields for MM region",
      "Electrostatic embedding",
      "Active site selection by residue/atom",
    ],
    whenToUse:
      "Use QM/MM for enzyme catalysis, drug binding, or any system where a small region needs quantum accuracy while the bulk environment is treated classically.",
    alternatives:
      "For pure QM, use PySCF. For pure MD, use OpenMM. For semi-empirical QM on larger regions, consider PM7 in Open Babel.",
    params: {
      qm_method: { type: "select", description: "QM method for active site", options: { hf: "Hartree-Fock", dft: "DFT (B3LYP)" } },
      qm_basis: { type: "select", description: "QM basis set", options: { "sto-3g": "Minimal", "6-31g": "Split-valence", "cc-pvdz": "Correlation-consistent" } },
      qm_selection: { type: "text", description: "Atom selection for QM region" },
    },
    outputs: {
      qmmm_energy: "Total QM/MM energy",
      qm_energy: "QM region energy",
      mm_energy: "MM region energy",
      structure: "Final optimized structure",
    },
    examples: ["QM/MM Alanine preset"],
    references: [
      { label: "ASH documentation", url: "https://ash.readthedocs.io/" },
    ],
    license: "LGPL-3.0",
    limitations: [
      "QM region should be small (< 100 atoms)",
      "Boundary treatment requires careful atom selection",
      "No QM/MM MD yet (single-point or optimization only)",
    ],
  },

  // ═══════════════════════════════════════════
  // CLASSICAL MECHANICS
  // ═══════════════════════════════════════════
  pybullet: {
    name: "PyBullet",
    layer: "mechanics",
    summary: "Rigid body dynamics, collisions, and robotics",
    description:
      "PyBullet is a physics engine for rigid body dynamics, collision detection, and robotics simulation. It supports articulated bodies, constraints, contact forces, and URDF/SDF robot models.",
    capabilities: [
      "Rigid body collision detection",
      "Articulated body dynamics (joints, constraints)",
      "URDF/SDF robot model loading",
      "Contact force computation",
      "Gravity and external force application",
    ],
    whenToUse:
      "Use PyBullet for macroscopic rigid body simulations: collisions, robotics, mechanical systems. Not for molecular or atomic-scale dynamics.",
    alternatives:
      "For finite element analysis of deformable bodies, use FEniCS. For fluid-structure interaction, combine with OpenFOAM.",
    params: {
      simulation_type: { type: "select", description: "Type of simulation", options: { collision: "Rigid body collision", articulated: "Articulated robot dynamics" } },
      gravity: { type: "number", unit: "m/s²", description: "Gravitational acceleration" },
      timestep: { type: "number", unit: "s", description: "Physics timestep" },
      duration: { type: "number", unit: "s", description: "Total simulation time" },
    },
    outputs: {
      positions: "Object positions over time",
      collisions: "Contact points and forces",
      joint_angles: "Joint angle time series (articulated bodies)",
    },
    examples: ["Sphere collision preset"],
    references: [
      { label: "PyBullet documentation", url: "https://pybullet.org/" },
    ],
    license: "Zlib",
    limitations: [
      "Rigid bodies only (no deformation)",
      "Limited to macroscopic scale",
      "No fluid dynamics",
    ],
  },

  // ═══════════════════════════════════════════
  // CONTINUUM MECHANICS
  // ═══════════════════════════════════════════
  fenics: {
    name: "FEniCS",
    layer: "continuum",
    summary: "Finite element method — heat, elasticity, Stokes",
    description:
      "FEniCS (via DOLFINx) is an automated finite element framework for solving PDEs. It uses the Unified Form Language (UFL) to express variational problems in near-mathematical notation, then auto-generates efficient C code.",
    capabilities: [
      "Heat equation (diffusion)",
      "Linear elasticity",
      "Stokes and Navier-Stokes flow",
      "Custom PDEs via UFL",
      "Adaptive mesh refinement",
      "Parallel computing with MPI",
    ],
    whenToUse:
      "Use FEniCS for PDE-based continuum simulations: heat transfer, structural mechanics, fluid flow. Its UFL interface makes it ideal for custom PDE formulations.",
    alternatives:
      "For multiphysics coupling, use Elmer. For spectral methods, use Dedalus. For CFD, use OpenFOAM.",
    params: {
      simulation_type: {
        type: "select",
        description: "Type of FEM simulation",
        options: { heat: "Heat equation (diffusion)", elasticity: "Linear elasticity", stokes: "Stokes flow", poisson: "Poisson equation" },
      },
      mesh_type: { type: "select", description: "Mesh type", options: { unit_square: "Unit square (2D)", unit_cube: "Unit cube (3D)", custom: "Custom mesh (from Gmsh)" } },
      resolution: { type: "number", description: "Mesh resolution (elements per side)" },
    },
    outputs: {
      field_data: "Solution field values on mesh nodes",
      x_grid: "X coordinates of mesh nodes",
      y_grid: "Y coordinates of mesh nodes",
      mesh_info: "Mesh statistics (elements, vertices, DOFs)",
    },
    examples: ["Heated Plate preset", "Cantilever Beam preset"],
    references: [
      { label: "FEniCS documentation", url: "https://fenicsproject.org/documentation/" },
    ],
    license: "LGPL-3.0",
    limitations: [
      "Primarily for linear and weakly nonlinear PDEs",
      "Complex geometries require Gmsh mesh import",
      "No built-in contact mechanics",
    ],
  },

  elmer: {
    name: "Elmer",
    layer: "continuum",
    summary: "Multiphysics FEM — structural, thermal, coupled",
    description:
      "Elmer is a multiphysics FEM solver supporting structural mechanics, heat transfer, electromagnetics, fluid dynamics, and coupled multi-field problems. It uses the SIF (Solver Input File) format for problem definition.",
    capabilities: [
      "Linear and nonlinear elasticity",
      "Heat conduction and convection",
      "Electromagnetics (Maxwell equations)",
      "Fluid-structure interaction",
      "Coupled thermal-structural analysis",
    ],
    whenToUse:
      "Use Elmer when you need multiphysics coupling (e.g., thermal-structural, fluid-structure). It handles problems that require simultaneous solution of multiple physics domains.",
    alternatives:
      "For simpler single-physics PDE, use FEniCS. For CFD-specific problems, use OpenFOAM.",
    params: {
      simulation_type: { type: "select", description: "Simulation type", options: { structural: "Structural mechanics", thermal: "Heat transfer", coupled: "Thermal-structural coupling" } },
      mesh_source: { type: "select", description: "Mesh source", options: { built_in: "Built-in mesh", gmsh: "Import from Gmsh" } },
    },
    outputs: {
      field_data: "Solution field values",
      stress: "Stress tensor components (structural)",
      temperature: "Temperature field (thermal)",
    },
    examples: ["Thermal-structural coupling preset"],
    references: [
      { label: "Elmer documentation", url: "https://www.elmerfem.org/documentation/" },
    ],
    license: "GPL-2.0",
    limitations: [
      "Complex SIF file syntax",
      "Less automated than FEniCS",
      "Parallel scaling limited for very large problems",
    ],
  },

  firedrake: {
    name: "Firedrake",
    layer: "continuum",
    summary: "FEM — Poisson, Stokes, elasticity, advection-diffusion (PETSc)",
    description:
      "Firedrake is a FEM framework built on PETSc, using UFL for problem specification (similar to FEniCS). It features automated code generation, composable solvers, and excellent parallel scaling.",
    capabilities: [
      "Poisson, Stokes, Navier-Stokes solvers",
      "Linear elasticity",
      "Advection-diffusion",
      "Composable solver chains via PETSc",
      "Mesh import from Gmsh",
      "High-order elements",
    ],
    whenToUse:
      "Use Firedrake when you need advanced PETSc solver options, composable preconditioners, or specific solver strategies not available in FEniCS.",
    alternatives:
      "FEniCS is similar and often simpler to set up. For multiphysics, use Elmer.",
    params: {
      simulation_type: { type: "select", description: "Problem type", options: { poisson: "Poisson equation", stokes: "Stokes flow", elasticity: "Linear elasticity", advection_diffusion: "Advection-diffusion" } },
      mesh_source: { type: "select", description: "Mesh source", options: { built_in: "Built-in mesh", gmsh: "Gmsh import" } },
    },
    outputs: {
      field_data: "Solution field values on mesh",
      x_grid: "X coordinates",
      y_grid: "Y coordinates",
    },
    examples: [],
    references: [
      { label: "Firedrake documentation", url: "https://www.firedrakeproject.org/documentation.html" },
    ],
    license: "LGPL-3.0",
    limitations: [
      "Requires PETSc backend",
      "Steeper learning curve for advanced solver configuration",
      "Less community documentation than FEniCS",
    ],
  },

  // ═══════════════════════════════════════════
  // GENERAL RELATIVITY
  // ═══════════════════════════════════════════
  einsteinpy: {
    name: "EinsteinPy",
    layer: "relativity",
    summary: "Geodesics and spacetime metrics in GR",
    description:
      "EinsteinPy computes geodesics, Christoffel symbols, and tensor operations in curved spacetimes. It supports Schwarzschild, Kerr, and custom metrics for studying relativistic orbital dynamics.",
    capabilities: [
      "Schwarzschild and Kerr geodesic integration",
      "Christoffel symbol computation",
      "Metric tensor manipulation",
      "Timelike and null geodesics",
      "Perihelion precession calculation",
    ],
    whenToUse:
      "Use EinsteinPy for analytical/semi-analytical GR problems: geodesics around black holes, light bending, orbital precession. Good for single-body problems in known metrics.",
    alternatives:
      "For numerical relativity (BBH mergers, gravitational waves), use NRPy+ or Einstein Toolkit. For N-body with GR corrections, use REBOUND with REBOUNDx.",
    params: {
      metric: { type: "select", description: "Spacetime metric", options: { schwarzschild: "Schwarzschild (non-rotating)", kerr: "Kerr (rotating)", custom: "Custom metric tensor" } },
      M: { type: "number", unit: "solar masses", description: "Central mass" },
      a: { type: "number", description: "Kerr spin parameter (0 to 1)" },
      initial_position: { type: "json", description: "Initial position [r, θ, φ]" },
      initial_velocity: { type: "json", description: "Initial velocity components" },
    },
    outputs: {
      geodesic: "Geodesic trajectory in coordinate space",
      proper_time: "Proper time along the geodesic",
      christoffels: "Christoffel symbols (if requested)",
    },
    examples: ["Schwarzschild Orbit preset"],
    references: [
      { label: "EinsteinPy documentation", url: "https://docs.einsteinpy.org/" },
    ],
    license: "MIT",
    limitations: [
      "Semi-analytical — not for dynamical spacetimes",
      "Limited to test-particle motion in fixed backgrounds",
      "No gravitational wave extraction",
    ],
  },

  nrpy: {
    name: "NRPy+",
    layer: "relativity",
    summary: "Numerical relativity — BBH, gravitational waves, neutron stars",
    description:
      "NRPy+ generates highly optimized C code for numerical relativity simulations. It handles the BSSN formulation of Einstein's equations, initial data construction (TwoPunctures), and gravitational wave extraction.",
    capabilities: [
      "BSSN formulation of Einstein equations",
      "Binary black hole initial data (TwoPunctures)",
      "Gravitational wave extraction (Weyl scalar Ψ₄)",
      "AMR (adaptive mesh refinement) grid setup",
      "Automated C code generation from SymPy",
    ],
    whenToUse:
      "Use NRPy+ for strong-field numerical relativity: BBH mergers, neutron star collisions, gravitational wave template generation. It generates efficient C code from symbolic expressions.",
    alternatives:
      "For production NR runs, use Einstein Toolkit (Cactus). For weak-field GR, use EinsteinPy.",
    params: {
      simulation_type: { type: "select", description: "NR scenario", options: { bbh: "Binary black hole merger", single_bh: "Single black hole (gauge wave test)", neutron_star: "Neutron star collapse" } },
      resolution: { type: "number", description: "Grid resolution parameter" },
      mass_ratio: { type: "number", description: "Mass ratio q = m₁/m₂" },
    },
    outputs: {
      waveform: "Gravitational wave strain h+ and h×",
      trajectories: "BH puncture trajectories",
      constraints: "Hamiltonian and momentum constraint violations",
    },
    examples: ["BBH Merger preset"],
    references: [
      { label: "NRPy+ documentation", url: "https://nrpytutorial.readthedocs.io/" },
    ],
    license: "BSD-2-Clause",
    limitations: [
      "Computationally very expensive",
      "Low-resolution runs only on this platform",
      "Requires significant physics background to interpret results",
    ],
  },

  einstein_toolkit: {
    name: "Einstein Toolkit",
    layer: "relativity",
    summary: "Full numerical relativity — BBH inspiral, neutron stars, dynamical spacetimes",
    description:
      "The Einstein Toolkit (Cactus + McLachlan) is the community standard for numerical relativity. It solves Einstein's equations using the BSSN formulation with Carpet AMR and provides thorns for matter, gauge conditions, and wave extraction.",
    capabilities: [
      "Full BSSN evolution with McLachlan",
      "Carpet AMR (adaptive mesh refinement)",
      "TwoPunctures initial data",
      "Weyl scalar extraction (Ψ₄)",
      "Matter evolution (GRHydro for neutron stars)",
    ],
    whenToUse:
      "Use Einstein Toolkit for production numerical relativity: binary black hole inspiral, neutron star mergers, gravitational wave astronomy. Most physically complete NR framework.",
    alternatives:
      "For quick NR code generation, use NRPy+. For geodesics in fixed backgrounds, use EinsteinPy.",
    params: {
      simulation_type: { type: "select", description: "Scenario", options: { bbh: "Binary black hole inspiral", single_bh: "Single puncture (gauge wave)", ns_collapse: "Neutron star collapse" } },
      resolution: { type: "select", description: "Grid resolution", options: { low: "Low (fast, ~5 min)", medium: "Medium (~30 min)", high: "High (~2 hours)" } },
    },
    outputs: {
      waveform: "Gravitational wave strain",
      trajectories: "Puncture trajectories",
      constraints: "Constraint violation monitors",
    },
    examples: ["ETK BBH Inspiral preset"],
    references: [
      { label: "Einstein Toolkit", url: "https://einsteintoolkit.org/" },
    ],
    license: "Mixed open-source (GPL/LGPL/BSD per thorn)",
    limitations: [
      "Very computationally expensive (even low-res takes minutes)",
      "Complex thorn parameter file setup",
      "Requires HPC-class resources for production runs",
    ],
  },

  // ═══════════════════════════════════════════
  // SYSTEMS BIOLOGY
  // ═══════════════════════════════════════════
  basico: {
    name: "BasiCO",
    layer: "systems-biology",
    summary: "Biochemical reaction networks (COPASI)",
    description:
      "BasiCO is a Python wrapper for COPASI, a biochemical network simulator. It supports ODE time-course, stochastic simulation (Gillespie), steady-state analysis, parameter estimation, and sensitivity analysis.",
    capabilities: [
      "ODE time-course simulation (deterministic)",
      "Stochastic simulation (Gillespie algorithm)",
      "Steady-state analysis",
      "Parameter estimation",
      "Sensitivity analysis",
      "SBML model import/export",
    ],
    whenToUse:
      "Use BasiCO for biochemical reaction network modeling: enzyme kinetics, metabolic pathways, gene regulatory networks. Ideal when you need COPASI's mature ODE/stochastic solvers from Python.",
    alternatives:
      "For Antimony/SBML-first workflows, use Tellurium. For spatial reaction-diffusion, combine with FEniCS.",
    params: {
      model_type: {
        type: "select",
        description: "Predefined model type",
        options: { enzyme_kinetics: "Michaelis-Menten enzyme kinetics", linear_pathway: "Linear metabolic pathway", custom: "Custom reactions/species" },
      },
      simulation_type: {
        type: "select",
        description: "Simulation method",
        options: { ode_timecourse: "ODE time-course", stochastic_timecourse: "Stochastic (Gillespie)", steady_state: "Steady-state", parameter_estimation: "Parameter estimation", sensitivity: "Sensitivity analysis" },
      },
      duration: { type: "number", unit: "seconds", description: "Simulation duration" },
      steps: { type: "number", description: "Number of output time points" },
      reactions: { type: "json", description: "Custom reaction definitions (JSON)" },
      species: { type: "json", description: "Initial species concentrations (JSON)" },
    },
    outputs: {
      timecourse: "Species concentrations over time",
      steady_state: "Steady-state concentrations",
      sensitivities: "Parameter sensitivity coefficients",
      sbml_export: "SBML model export string",
    },
    examples: ["Enzyme Kinetics preset", "Linear Pathway preset"],
    references: [
      { label: "BasiCO documentation", url: "https://basico.readthedocs.io/" },
      { label: "COPASI", url: "https://copasi.org/" },
    ],
    license: "Artistic-2.0",
    limitations: [
      "No spatial modeling (well-mixed assumption)",
      "Limited to ODE or discrete stochastic (no spatial PDEs)",
      "Custom models require COPASI-compatible reaction format",
    ],
  },

  tellurium: {
    name: "Tellurium",
    layer: "systems-biology",
    summary: "SBML/Antimony pathway models",
    description:
      "Tellurium is a systems biology modeling environment based on the Antimony language and libRoadRunner. It provides a human-readable syntax for defining reaction networks and fast ODE simulation.",
    capabilities: [
      "Antimony language for model definition",
      "SBML import/export",
      "Fast ODE simulation (libRoadRunner)",
      "Steady-state and stability analysis",
      "Bifurcation analysis",
    ],
    whenToUse:
      "Use Tellurium when you want to write models in Antimony syntax (more readable than SBML XML) or need fast repeated simulations via libRoadRunner.",
    alternatives:
      "For COPASI-specific features (parameter estimation, sensitivity), use BasiCO.",
    params: {
      model_source: { type: "select", description: "Model input format", options: { antimony: "Antimony text", sbml: "SBML XML" } },
      antimony_model: { type: "text", description: "Antimony model definition" },
      duration: { type: "number", unit: "seconds", description: "Simulation duration" },
      steps: { type: "number", description: "Number of output points" },
    },
    outputs: {
      timecourse: "Species concentrations over time",
      steady_state: "Steady-state values",
      sbml_export: "SBML export for downstream tools",
      ode_system: "ODE system equations (for symbolic analysis)",
    },
    examples: ["Simple pathway preset"],
    references: [
      { label: "Tellurium documentation", url: "https://tellurium.readthedocs.io/" },
    ],
    license: "Apache-2.0",
    limitations: [
      "Well-mixed only (no spatial modeling)",
      "Limited stochastic simulation options",
      "Antimony syntax has learning curve",
    ],
  },

  // ═══════════════════════════════════════════
  // NEUROSCIENCE
  // ═══════════════════════════════════════════
  brian2: {
    name: "Brian2",
    layer: "neuroscience",
    summary: "Spiking neural networks",
    description:
      "Brian2 is a simulator for spiking neural networks. It uses equation-based model definitions, supporting Leaky Integrate-and-Fire (LIF), Hodgkin-Huxley, and custom neuron models with synaptic plasticity.",
    capabilities: [
      "LIF (Leaky Integrate-and-Fire) neurons",
      "Hodgkin-Huxley neurons",
      "Exponential/adaptive exponential IF",
      "STDP and other plasticity rules",
      "Network construction from neuron groups and synapses",
    ],
    whenToUse:
      "Use Brian2 for detailed spiking neural network simulations: cortical microcircuits, plasticity studies, neural coding. Best for networks up to ~10,000 neurons.",
    alternatives:
      "For larger networks (millions of neurons), use NEST. For rate-based neural models, use a systems biology tool.",
    params: {
      neuron_model: { type: "select", description: "Neuron model", options: { lif: "Leaky Integrate-and-Fire", hh: "Hodgkin-Huxley", adex: "Adaptive Exponential IF" } },
      n_neurons: { type: "number", description: "Number of neurons" },
      connection_prob: { type: "number", description: "Connection probability (0–1)" },
      duration: { type: "number", unit: "ms", description: "Simulation duration" },
    },
    outputs: {
      spike_times: "Spike raster data (neuron ID, time)",
      membrane_potential: "Membrane potential traces",
      firing_rates: "Population firing rates over time",
    },
    examples: ["LIF Network preset"],
    references: [
      { label: "Brian2 documentation", url: "https://brian2.readthedocs.io/" },
    ],
    license: "CeCILL-2.1",
    limitations: [
      "Performance limited for very large networks (> 100k neurons)",
      "CPU-only (no GPU acceleration)",
      "No built-in morphological neuron models",
    ],
  },

  nest: {
    name: "NEST",
    layer: "neuroscience",
    summary: "Large-scale neural simulation",
    description:
      "NEST is designed for large-scale simulation of spiking neural networks. It efficiently handles networks with millions of neurons on distributed computing clusters, used for cortical network models.",
    capabilities: [
      "Efficient simulation of millions of neurons",
      "Built-in neuron models (LIF, Izhikevich, MAT2)",
      "STDP and other synapse models",
      "Random and structured connectivity",
      "Parallel execution (MPI + threads)",
    ],
    whenToUse:
      "Use NEST for large-scale neural network simulations: cortical column models, thalamocortical circuits, full brain region models. Scales to millions of neurons.",
    alternatives:
      "For smaller, more flexible networks with custom equations, use Brian2.",
    params: {
      network_model: { type: "select", description: "Network model", options: { brunel: "Brunel balanced network", random: "Random network", custom: "Custom connectivity" } },
      n_neurons: { type: "number", description: "Number of neurons", range: "100–1000000" },
      duration: { type: "number", unit: "ms", description: "Simulation duration" },
    },
    outputs: {
      spike_times: "Spike raster data",
      firing_rates: "Population firing rates",
      membrane_potential: "Sampled membrane potential traces",
    },
    examples: ["Brunel Network preset"],
    references: [
      { label: "NEST documentation", url: "https://nest-simulator.readthedocs.io/" },
    ],
    license: "GPL-2.0",
    limitations: [
      "Less flexible for custom neuron equations than Brian2",
      "Setup can be verbose for complex networks",
      "Visualization must be done externally",
    ],
  },

  // ═══════════════════════════════════════════
  // EVOLUTION / POPULATION GENETICS
  // ═══════════════════════════════════════════
  msprime: {
    name: "msprime",
    layer: "evolution",
    summary: "Coalescent population genetics",
    description:
      "msprime is a population genetics simulator implementing the coalescent with recombination. It efficiently generates tree sequences representing the genealogical history of a sample, with support for complex demographic models.",
    capabilities: [
      "Coalescent simulation with recombination",
      "Complex demographic models (population splits, migration)",
      "Mutation overlay on tree sequences",
      "Tree sequence output (tskit-compatible)",
      "Efficient memory usage for large samples",
    ],
    whenToUse:
      "Use msprime for backward-in-time population genetics: generating genealogies under neutral models, complex demography, or as initial conditions for forward-time simulations (SLiM recapitation).",
    alternatives:
      "For forward-time simulation with selection, use SLiM. For individual-based population models, use simuPOP.",
    params: {
      simulation_type: { type: "select", description: "Simulation type", options: { coalescent: "Standard coalescent", demography: "Demographic model" } },
      sample_size: { type: "number", description: "Number of sampled genomes" },
      sequence_length: { type: "number", unit: "bp", description: "Sequence length in base pairs" },
      recombination_rate: { type: "number", unit: "per bp per gen", description: "Recombination rate" },
      mutation_rate: { type: "number", unit: "per bp per gen", description: "Mutation rate" },
    },
    outputs: {
      tree_sequence: "tskit tree sequence object",
      diversity: "Nucleotide diversity statistics",
      num_trees: "Number of marginal trees",
      num_mutations: "Total mutations in the tree sequence",
    },
    examples: ["Neutral Coalescent preset"],
    references: [
      { label: "msprime documentation", url: "https://tskit.dev/msprime/docs/stable/" },
    ],
    license: "GPL-3.0",
    limitations: [
      "No natural selection (neutral models only)",
      "Backward-in-time only (no forward simulation)",
      "Demographic model specification can be complex",
    ],
  },

  slim: {
    name: "SLiM",
    layer: "evolution",
    summary: "Forward-time evolutionary simulation — neutral, selection, nucleotide, spatial",
    description:
      "SLiM is a forward-time, individual-based evolutionary simulator. It supports natural selection, complex life cycles, spatial structure, nucleotide-level evolution, and tree sequence recording.",
    capabilities: [
      "Neutral and selected evolution",
      "Nucleotide-level sequence evolution",
      "Spatial structure and continuous-space models",
      "Complex life cycles (non-Wright-Fisher)",
      "Tree sequence recording for efficient analysis",
      "Custom SLiM scripts via Eidos language",
    ],
    whenToUse:
      "Use SLiM for forward-time evolution: natural selection, adaptation, spatial dynamics, complex genetic architectures. Combine with msprime for recapitation.",
    alternatives:
      "For neutral coalescent models, use msprime (much faster). For individual-based genetics without spatial, use simuPOP.",
    params: {
      simulation_type: { type: "select", description: "Evolution scenario", options: { neutral_evolution: "Neutral drift", directional_selection: "Directional selection", nucleotide_evolution: "Nucleotide-level evolution", spatial: "Spatial population" } },
      population_size: { type: "number", description: "Number of individuals" },
      n_generations: { type: "number", description: "Number of generations to simulate" },
      sequence_length: { type: "number", unit: "bp", description: "Genome length" },
      mutation_rate: { type: "number", description: "Per-base mutation rate" },
    },
    outputs: {
      tree_sequence: "Tree sequence (tskit-compatible)",
      allele_frequencies: "Allele frequency trajectories",
      fixations: "Fixed mutations",
      population_size: "Population size over time",
    },
    examples: ["SLiM Neutral Evolution preset"],
    references: [
      { label: "SLiM documentation", url: "https://messerlab.org/slim/" },
    ],
    license: "GPL-3.0",
    limitations: [
      "Forward-time is slower than coalescent for neutral models",
      "Memory usage scales with population size",
      "Complex models require Eidos scripting knowledge",
    ],
  },

  tskit: {
    name: "tskit",
    layer: "evolution",
    summary: "Tree sequence analysis — diversity, Fst, recapitation",
    description:
      "tskit (tree sequence toolkit) provides analysis methods for tree sequences produced by msprime and SLiM. It computes population genetic statistics, performs recapitation, and visualizes genealogies.",
    capabilities: [
      "Nucleotide diversity (π) and divergence",
      "Fst between populations",
      "Recapitation of SLiM tree sequences",
      "Tree visualization and traversal",
      "Efficient storage and analysis of large genealogies",
    ],
    whenToUse:
      "Use tskit after msprime or SLiM simulations to analyze tree sequences. Essential for computing population genetic summary statistics.",
    alternatives:
      "For per-site statistics, use scikit-allel. tskit is generally the most efficient choice for tree sequence data.",
    params: {
      simulation_type: { type: "select", description: "Analysis type", options: { diversity: "Nucleotide diversity", fst: "Fst between populations", recapitate: "Recapitate SLiM output" } },
      source_job_id: { type: "text", description: "Job ID of msprime/SLiM simulation to analyze" },
    },
    outputs: {
      diversity: "Nucleotide diversity statistics",
      fst: "Pairwise Fst values",
      tree_stats: "Summary statistics of the tree sequence",
    },
    examples: ["tskit Diversity Analysis preset"],
    references: [
      { label: "tskit documentation", url: "https://tskit.dev/tskit/docs/stable/" },
    ],
    license: "MIT",
    limitations: [
      "Analysis only — does not generate simulations",
      "Requires tree sequence input from msprime or SLiM",
      "Some statistics require mutations (not just topology)",
    ],
  },

  simupop: {
    name: "simuPOP",
    layer: "evolution",
    summary: "Forward-time population genetics — mating, migration, selection",
    description:
      "simuPOP is a general-purpose forward-time population genetics simulator. It focuses on individual-based modeling with detailed mating schemes, migration patterns, and selection models.",
    capabilities: [
      "Random and assortative mating",
      "Migration between demes",
      "Natural selection (directional, balancing, frequency-dependent)",
      "Mutation models (finite sites, infinite sites)",
      "Demographic events (bottlenecks, expansions)",
    ],
    whenToUse:
      "Use simuPOP for forward-time population genetics focusing on mating patterns, migration, and demographic events. Good for modeling complex breeding programs or structured populations.",
    alternatives:
      "For tree sequence recording (more efficient analysis), use SLiM. For neutral coalescent, use msprime.",
    params: {
      population_size: { type: "number", description: "Initial population size" },
      n_generations: { type: "number", description: "Number of generations" },
      mating_scheme: { type: "select", description: "Mating scheme", options: { random: "Random mating", monogamy: "Monogamous pairs", polygyny: "Polygynous mating" } },
      migration_rate: { type: "number", description: "Migration rate between demes" },
    },
    outputs: {
      allele_frequencies: "Allele frequency trajectories",
      population_size: "Population size over generations",
      genotype_data: "Genotype matrix for downstream analysis",
    },
    examples: [],
    references: [
      { label: "simuPOP documentation", url: "https://bopeng.github.io/simuPOP/" },
    ],
    license: "GPL-2.0",
    limitations: [
      "No tree sequence recording (less efficient than SLiM for large simulations)",
      "Python 3 support via specific builds",
      "Documentation can be sparse for advanced features",
    ],
  },

  // ═══════════════════════════════════════════
  // CHEMISTRY
  // ═══════════════════════════════════════════
  rdkit: {
    name: "RDKit",
    layer: "chemistry",
    summary: "Cheminformatics — SMILES, descriptors, fingerprints, conformers",
    description:
      "RDKit is a comprehensive cheminformatics toolkit. It parses SMILES strings, generates 3D conformers, computes molecular descriptors and fingerprints, and provides structure visualization.",
    capabilities: [
      "SMILES/SMARTS parsing and manipulation",
      "3D conformer generation (ETKDG)",
      "Molecular descriptor calculation (200+ descriptors)",
      "Morgan/ECFP and MACCS fingerprints",
      "Molecular similarity and substructure search",
      "PDB/SDF/MOL2 file generation",
    ],
    whenToUse:
      "Use RDKit as the entry point for chemistry workflows: convert SMILES to 3D structures, compute molecular properties, or prepare inputs for quantum chemistry (PySCF, Psi4) and MD (OpenMM, LAMMPS) tools.",
    alternatives:
      "For format conversion, also consider Open Babel. For drug-like property filtering, RDKit is the standard.",
    params: {
      simulation_type: { type: "select", description: "Computation type", options: { descriptors: "Molecular descriptors", fingerprints: "Morgan fingerprints", conformer: "3D conformer generation", similarity: "Molecular similarity search" } },
      smiles: { type: "text", description: "SMILES string of the molecule (e.g., 'CC(=O)Oc1ccccc1C(=O)O' for aspirin)" },
    },
    outputs: {
      descriptors: "Molecular weight, LogP, TPSA, HBD, HBA, rotatable bonds, etc.",
      fingerprints: "Morgan fingerprint bit vector",
      conformer_coordinates: "3D coordinates of generated conformer",
      pdb_block: "PDB format structure",
      atom_coords_pyscf: "Atom coordinates formatted for PySCF input",
      sdf_block: "SDF format structure",
      smiles: "Canonical SMILES",
      molecular_weight: "Molecular weight",
      elements: "List of element symbols",
    },
    examples: ["Aspirin Descriptors preset"],
    references: [
      { label: "RDKit documentation", url: "https://www.rdkit.org/docs/" },
    ],
    license: "BSD-3-Clause",
    limitations: [
      "No quantum chemistry (use PySCF/Psi4 downstream)",
      "Conformer generation is approximate (force-field based)",
      "Limited to small organic molecules",
    ],
  },

  cantera: {
    name: "Cantera",
    layer: "chemistry",
    summary: "Chemical kinetics — combustion, ignition, flame speed",
    description:
      "Cantera is a suite of tools for chemical kinetics, thermodynamics, and transport. It supports homogeneous reactors, flame simulations, ignition delay calculations, and equilibrium computations using detailed reaction mechanisms.",
    capabilities: [
      "Ignition delay calculation",
      "Reactor time-course simulation",
      "Laminar flame speed computation",
      "Chemical equilibrium",
      "GRI-Mech 3.0 and H₂/O₂ mechanisms",
      "Species transport properties",
    ],
    whenToUse:
      "Use Cantera for combustion chemistry, atmospheric chemistry, or any chemical kinetics problem involving gas-phase reactions. Ideal for ignition delay, flame speed, and reactor modeling.",
    alternatives:
      "For biochemical kinetics, use BasiCO. For surface chemistry on materials, combine with Quantum ESPRESSO.",
    params: {
      simulation_type: { type: "select", description: "Simulation type", options: { ignition_delay: "Ignition delay", reactor_timecourse: "Reactor time-course", flame_speed: "Laminar flame speed", equilibrium: "Chemical equilibrium" } },
      mechanism: { type: "select", description: "Reaction mechanism", options: { "gri30.yaml": "GRI-Mech 3.0 (natural gas)", "h2o2.yaml": "H₂/O₂ (hydrogen)" } },
      temperature: { type: "number", unit: "K", description: "Initial temperature" },
      pressure: { type: "number", unit: "atm", description: "Initial pressure" },
      composition: { type: "text", description: "Species composition (e.g., 'H2:2, O2:1, AR:0.5')" },
    },
    outputs: {
      temperature: "Temperature vs time profile",
      species: "Species concentration profiles",
      ignition_delay: "Ignition delay time (if applicable)",
      flame_speed: "Laminar flame speed (if applicable)",
      heat_release_rate: "Heat release rate profile",
    },
    examples: ["Hydrogen Ignition preset"],
    references: [
      { label: "Cantera documentation", url: "https://cantera.org/documentation/" },
    ],
    license: "BSD-3-Clause",
    limitations: [
      "0D/1D only (no multi-dimensional CFD)",
      "Requires mechanism files for specific chemistry",
      "Limited to gas-phase (no liquid-phase kinetics)",
    ],
  },

  openbabel: {
    name: "Open Babel",
    layer: "chemistry",
    summary: "Universal chemical format converter — 110+ formats, 3D optimization",
    description:
      "Open Babel is a universal chemical toolbox for converting between 110+ molecular file formats, performing 3D structure generation and optimization, and computing basic molecular properties.",
    capabilities: [
      "Format conversion (SMILES, PDB, SDF, MOL2, XYZ, CIF, etc.)",
      "3D coordinate generation and optimization",
      "Force field optimization (MMFF94, UFF, Ghemical)",
      "Molecular property calculation",
      "Substructure search (SMARTS)",
    ],
    whenToUse:
      "Use Open Babel as a format bridge between tools: convert SMILES to PDB for OpenMM, XYZ for PySCF, or SDF for RDKit. Also useful for quick 3D structure optimization.",
    alternatives:
      "RDKit handles many of the same conversions with more cheminformatics features.",
    params: {
      conversion_type: { type: "select", description: "Operation type", options: { convert: "Format conversion", optimize: "3D optimization", generate: "3D coordinate generation" } },
      source_format: { type: "select", description: "Input format", options: { smi: "SMILES", pdb: "PDB", sdf: "SDF", xyz: "XYZ" } },
      target_format: { type: "select", description: "Output format", options: { pdb: "PDB", sdf: "SDF", xyz: "XYZ", mol2: "MOL2" } },
      source_data: { type: "text", description: "Input molecular data" },
    },
    outputs: {
      output_data: "Converted molecular data in target format",
      output_pdb: "PDB format output (if target is PDB)",
      output_xyz: "XYZ coordinate output",
      coordinates: "Atomic coordinates",
      elements: "Element list",
    },
    examples: [],
    references: [
      { label: "Open Babel documentation", url: "https://openbabel.org/docs/" },
    ],
    license: "GPL-2.0",
    limitations: [
      "No electronic structure calculations",
      "Force field optimization is approximate",
      "Some format conversions may lose information",
    ],
  },

  // ═══════════════════════════════════════════
  // MATERIALS SCIENCE
  // ═══════════════════════════════════════════
  qe: {
    name: "Quantum ESPRESSO",
    layer: "materials",
    summary: "Materials DFT — SCF, bands, DOS, relaxation",
    description:
      "Quantum ESPRESSO is a suite of codes for electronic structure calculations and materials modeling using plane-wave basis sets and pseudopotentials. It handles metals, semiconductors, insulators, and surfaces.",
    capabilities: [
      "Self-consistent field (SCF) calculations",
      "Band structure computation",
      "Density of states (DOS)",
      "Structural relaxation (ionic positions and cell)",
      "Phonon calculations (DFPT)",
      "Pseudopotential-based DFT (PBE, LDA)",
    ],
    whenToUse:
      "Use Quantum ESPRESSO for solid-state materials: band gaps, crystal structures, surface properties, phonons. Standard choice for periodic DFT with plane waves.",
    alternatives:
      "For molecular quantum chemistry, use PySCF. For classical materials MD, use LAMMPS.",
    params: {
      simulation_type: { type: "select", description: "Calculation type", options: { scf: "Self-consistent field", bands: "Band structure", dos: "Density of states", relax: "Structural relaxation" } },
      crystal_system: { type: "text", description: "Crystal structure definition" },
      ecutwfc: { type: "number", unit: "Ry", description: "Plane-wave cutoff energy" },
      k_points: { type: "text", description: "K-point grid (e.g., '4 4 4')" },
    },
    outputs: {
      total_energy: "Total DFT energy",
      band_structure: "Electronic band energies vs k-points",
      dos: "Density of states",
      forces: "Atomic forces (for relaxation)",
    },
    examples: ["Silicon SCF preset"],
    references: [
      { label: "Quantum ESPRESSO", url: "https://www.quantum-espresso.org/documentation/" },
    ],
    license: "GPL-2.0",
    limitations: [
      "Requires pseudopotential files for each element",
      "Plane-wave basis demands high cutoff for hard elements",
      "DFT limitations (band gap underestimation)",
    ],
  },

  lammps: {
    name: "LAMMPS",
    layer: "materials",
    summary: "Materials MD — LJ fluids, metals, polymer melts",
    description:
      "LAMMPS (Large-scale Atomic/Molecular Massively Parallel Simulator) is a molecular dynamics engine for materials science. It supports a vast range of potentials: Lennard-Jones, EAM for metals, ReaxFF for reactive systems, and coarse-grained models.",
    capabilities: [
      "Lennard-Jones fluids",
      "EAM potentials for metals",
      "ReaxFF reactive force fields",
      "Polymer and soft matter simulations",
      "Non-equilibrium MD (NEMD)",
      "Massive parallel scaling",
    ],
    whenToUse:
      "Use LAMMPS for materials science MD: metals, ceramics, polymers, fluids. Choose over OpenMM when working with non-biological materials or custom potentials.",
    alternatives:
      "For biomolecular MD, use OpenMM or GROMACS. For DFT-level accuracy, use Quantum ESPRESSO.",
    params: {
      simulation_type: { type: "select", description: "Simulation type", options: { lj_fluid: "Lennard-Jones fluid", eam_metal: "EAM metallic system", polymer: "Polymer melt" } },
      temperature: { type: "number", unit: "K", description: "Simulation temperature" },
      n_atoms: { type: "number", description: "Number of atoms" },
      timestep: { type: "number", unit: "fs", description: "Timestep" },
      n_steps: { type: "number", description: "Number of simulation steps" },
    },
    outputs: {
      positions: "Atomic positions over time",
      energies: "System energy components",
      rdf: "Radial distribution function",
      msd: "Mean square displacement",
      trajectory_job_id: "Job ID for trajectory analysis",
    },
    examples: ["LJ Fluid preset"],
    references: [
      { label: "LAMMPS documentation", url: "https://docs.lammps.org/" },
    ],
    license: "GPL-2.0",
    limitations: [
      "Force field accuracy limited by potential choice",
      "Complex input script syntax",
      "No electronic structure (classical only)",
    ],
  },

  // ═══════════════════════════════════════════
  // MATHEMATICS
  // ═══════════════════════════════════════════
  sympy: {
    name: "SymPy",
    layer: "mathematics",
    summary: "Symbolic math — calculus, equation solving, code generation",
    description:
      "SymPy is a Python library for symbolic mathematics. It handles algebraic expressions, calculus, equation solving, linear algebra, and can generate LaTeX, C, and Fortran code from symbolic expressions.",
    capabilities: [
      "Algebraic simplification and expansion",
      "Symbolic differentiation and integration",
      "Equation solving (algebraic and differential)",
      "Matrix operations and eigenvalue problems",
      "LaTeX output for publication",
      "Code generation (C, Fortran, UFL for FEniCS)",
    ],
    whenToUse:
      "Use SymPy for any symbolic computation: deriving equations, solving ODEs symbolically, generating code from mathematical expressions. Great as a pipeline starting point for generating FEniCS UFL or Cantera rate expressions.",
    alternatives:
      "For advanced algebra/number theory, use SageMath. For formal verification of proofs, use Lean 4.",
    params: {
      simulation_type: { type: "select", description: "Computation type", options: { solve: "Equation solving", simplify: "Expression simplification", integrate: "Symbolic integration", diff: "Symbolic differentiation", ode: "ODE solving" } },
      expression: { type: "text", description: "Symbolic expression (e.g., 'x**2 - 2')" },
      variable: { type: "text", description: "Variable to solve for / differentiate w.r.t." },
    },
    outputs: {
      result: "Symbolic result (solution, simplified expression, etc.)",
      latex: "LaTeX representation",
      expression: "String representation for downstream tools",
      ufl_code: "UFL code for FEniCS (if PDE conversion)",
    },
    examples: ["Quadratic Solve preset"],
    references: [
      { label: "SymPy documentation", url: "https://docs.sympy.org/" },
    ],
    license: "BSD-3-Clause",
    limitations: [
      "Not for numerical computation (use NumPy/SciPy)",
      "Complex expressions can be slow to simplify",
      "Limited support for some special functions",
    ],
  },

  sagemath: {
    name: "SageMath",
    layer: "mathematics",
    summary: "Comprehensive math — algebra, number theory, geometry",
    description:
      "SageMath is a comprehensive mathematics system unifying many open-source packages (GAP, PARI, Singular, etc.) under a common Python interface. It covers algebra, number theory, combinatorics, algebraic geometry, and more.",
    capabilities: [
      "Polynomial algebra and Gröbner bases",
      "Number theory (prime factorization, modular arithmetic)",
      "Combinatorics and graph theory",
      "Algebraic geometry",
      "Differential geometry and manifolds",
    ],
    whenToUse:
      "Use SageMath for advanced mathematics beyond SymPy: Gröbner bases, number theory, algebraic geometry, combinatorics. Also good as a bridge to GAP for group theory.",
    alternatives:
      "For basic symbolic math, SymPy is lighter. For group theory specifically, use GAP directly.",
    params: {
      simulation_type: { type: "select", description: "Computation type", options: { groebner_basis: "Gröbner basis computation", factorize: "Polynomial factorization", number_theory: "Number theory operations" } },
      polynomials: { type: "text", description: "Input polynomials or expressions" },
    },
    outputs: {
      result: "Computation result",
      latex: "LaTeX representation",
    },
    examples: ["Polynomial Gröbner preset"],
    references: [
      { label: "SageMath documentation", url: "https://doc.sagemath.org/" },
    ],
    license: "GPL-2.0+",
    limitations: [
      "Large installation footprint",
      "Some operations can be slow for very large inputs",
      "Python 2/3 compatibility historically complex (now Python 3)",
    ],
  },

  lean4: {
    name: "Lean 4",
    layer: "mathematics",
    summary: "Formal verification — theorem proving, proofs",
    description:
      "Lean 4 is a theorem prover and programming language for formal mathematical verification. It can verify proofs of mathematical theorems, ensuring correctness at the highest possible standard.",
    capabilities: [
      "Interactive theorem proving",
      "Tactic-based proof construction",
      "Mathlib library of formalized mathematics",
      "Dependent type theory",
      "Proof term extraction",
    ],
    whenToUse:
      "Use Lean 4 at the end of a mathematics pipeline to formally verify results computed by SymPy or SageMath. Ensures mathematical correctness beyond numerical or symbolic checks.",
    alternatives:
      "For symbolic computation (not verification), use SymPy. For group-theoretic computations, use GAP.",
    params: {
      simulation_type: { type: "select", description: "Verification type", options: { verify: "Verify a mathematical statement", check: "Type-check a Lean expression" } },
      statement: { type: "text", description: "Mathematical statement or Lean expression to verify" },
    },
    outputs: {
      verified: "Whether the statement was verified (boolean)",
      proof_term: "Extracted proof term",
      messages: "Lean diagnostic messages",
    },
    examples: [],
    references: [
      { label: "Lean 4 documentation", url: "https://lean-lang.org/lean4/doc/" },
    ],
    license: "Apache-2.0",
    limitations: [
      "Requires formalized statement (not natural language)",
      "Mathlib coverage is growing but not complete",
      "Proof construction can require significant expertise",
    ],
  },

  gap: {
    name: "GAP",
    layer: "mathematics",
    summary: "Group theory — permutation groups, character tables",
    description:
      "GAP (Groups, Algorithms, Programming) is a system for computational discrete algebra, particularly group theory. It handles permutation groups, matrix groups, character tables, and combinatorial structures.",
    capabilities: [
      "Permutation and matrix group operations",
      "Character table computation",
      "Subgroup lattice analysis",
      "Coset enumeration",
      "Stabilizer code generators for quantum error correction",
    ],
    whenToUse:
      "Use GAP for group theory computations: symmetry analysis, character tables, permutation group operations. Also useful for generating stabilizer codes for quantum error correction (Qiskit coupling).",
    alternatives:
      "SageMath includes GAP as a backend. For basic group operations, SageMath's interface may be simpler.",
    params: {
      simulation_type: { type: "select", description: "Computation type", options: { character_table: "Character table", subgroup_lattice: "Subgroup lattice", permutation: "Permutation group operations" } },
      group_data: { type: "text", description: "Group specification (e.g., generators)" },
    },
    outputs: {
      result: "Computation result",
      character_table: "Character table (if requested)",
      generators: "Group generators",
    },
    examples: [],
    references: [
      { label: "GAP documentation", url: "https://www.gap-system.org/Manuals/doc/ref/chap0.html" },
    ],
    license: "GPL-2.0",
    limitations: [
      "Specialized for discrete algebra (not continuous math)",
      "Large groups can exhaust memory",
      "GAP language differs from Python syntax",
    ],
  },

  pyomo: {
    name: "Pyomo",
    layer: "mathematics",
    summary: "LP, MILP, NLP with GLPK/HiGHS/CBC/IPOPT solvers",
    description:
      "Pyomo is a Python-based optimization modeling language. It formulates and solves linear programs (LP), mixed-integer programs (MILP), nonlinear programs (NLP), and stochastic programs using open-source solvers.",
    capabilities: [
      "Linear programming (LP) with GLPK/HiGHS",
      "Mixed-integer linear programming (MILP) with CBC",
      "Nonlinear programming (NLP) with IPOPT",
      "Constraint programming",
      "Multi-objective optimization",
    ],
    whenToUse:
      "Use Pyomo for optimization problems: resource allocation, scheduling, network design, parameter optimization. Can receive objective functions from SymPy symbolic expressions.",
    alternatives:
      "For small optimization problems, scipy.optimize may suffice. For pure LP, GLPK directly is simpler.",
    params: {
      problem_type: { type: "select", description: "Problem type", options: { lp: "Linear program", milp: "Mixed-integer LP", nlp: "Nonlinear program" } },
      solver: { type: "select", description: "Solver", options: { glpk: "GLPK (LP)", highs: "HiGHS (LP/MILP)", cbc: "CBC (MILP)", ipopt: "IPOPT (NLP)" } },
      objective: { type: "json", description: "Objective function definition" },
      constraints: { type: "json", description: "Constraint definitions" },
    },
    outputs: {
      optimal_value: "Optimal objective function value",
      solution: "Variable values at optimum",
      status: "Solver status (optimal, infeasible, unbounded)",
      solver_time: "Solution time",
    },
    examples: [],
    references: [
      { label: "Pyomo documentation", url: "https://www.pyomo.org/documentation" },
    ],
    license: "BSD-3-Clause",
    limitations: [
      "NLP may find local optima (not guaranteed global)",
      "Solver availability depends on container installation",
      "Large models can be slow to build and solve",
    ],
  },

  networkx: {
    name: "NetworkX",
    layer: "mathematics",
    summary: "Graph theory — shortest paths, centrality, community detection",
    description:
      "NetworkX is a Python library for creating, manipulating, and studying complex networks and graphs. It implements standard graph algorithms for path finding, centrality, clustering, and community detection.",
    capabilities: [
      "Shortest path algorithms (Dijkstra, BFS, A*)",
      "Centrality measures (degree, betweenness, eigenvector)",
      "Community detection (Louvain, Girvan-Newman)",
      "Random graph generation (Erdős-Rényi, Barabási-Albert)",
      "Graph isomorphism testing",
    ],
    whenToUse:
      "Use NetworkX for graph and network analysis: social networks, citation networks, molecular graphs, transportation networks. Good for small-to-medium graphs (up to ~100k nodes).",
    alternatives:
      "For very large graphs (millions of nodes), use igraph or graph-tool.",
    params: {
      graph_type: { type: "select", description: "Graph generation/analysis", options: { erdos_renyi: "Erdős-Rényi random graph", barabasi_albert: "Barabási-Albert scale-free", watts_strogatz: "Watts-Strogatz small-world", custom: "Custom graph" } },
      n_nodes: { type: "number", description: "Number of nodes" },
      algorithm: { type: "select", description: "Analysis algorithm", options: { shortest_path: "Shortest path", centrality: "Centrality measures", community: "Community detection" } },
    },
    outputs: {
      nodes: "Node list with attributes",
      edges: "Edge list with weights",
      centrality: "Centrality values per node",
      communities: "Community assignments",
      paths: "Computed shortest paths",
    },
    examples: [],
    references: [
      { label: "NetworkX documentation", url: "https://networkx.org/documentation/" },
    ],
    license: "BSD-3-Clause",
    limitations: [
      "Not optimized for very large graphs (> 100k nodes)",
      "No GPU acceleration",
      "Pure Python (slower than C-based alternatives)",
    ],
  },

  // ═══════════════════════════════════════════
  // CIRCUITS
  // ═══════════════════════════════════════════
  lcapy: {
    name: "Lcapy",
    layer: "circuits",
    summary: "Symbolic circuits — transfer functions, pole-zero analysis",
    description:
      "Lcapy is a symbolic linear circuit analysis package. It computes transfer functions, impedances, pole-zero plots, and SPICE netlists from symbolic circuit descriptions using SymPy as the backend.",
    capabilities: [
      "Transfer function derivation",
      "Impedance and admittance computation",
      "Pole-zero analysis",
      "SPICE netlist generation",
      "Bode plot data (symbolic)",
    ],
    whenToUse:
      "Use Lcapy as the starting point for circuit analysis: derive transfer functions symbolically, then send to PySpice for numerical simulation or python-control for control analysis.",
    alternatives:
      "For numerical circuit simulation directly, use PySpice. For control systems analysis, use python-control.",
    params: {
      simulation_type: { type: "select", description: "Analysis type", options: { transfer_function: "Transfer function derivation", impedance: "Input/output impedance", pole_zero: "Pole-zero analysis" } },
      circuit: { type: "text", description: "Circuit netlist description" },
    },
    outputs: {
      transfer_function_str: "Transfer function as symbolic string",
      transfer_numerator: "Numerator polynomial coefficients",
      transfer_denominator: "Denominator polynomial coefficients",
      poles: "Pole locations in s-plane",
      zeros: "Zero locations in s-plane",
      spice_netlist: "SPICE-compatible netlist",
    },
    examples: ["RC Lowpass preset"],
    references: [
      { label: "Lcapy documentation", url: "https://lcapy.readthedocs.io/" },
    ],
    license: "LGPL-2.1",
    limitations: [
      "Linear circuits only",
      "Symbolic analysis can be slow for large circuits",
      "No transient simulation (use PySpice for that)",
    ],
  },

  pyspice: {
    name: "PySpice",
    layer: "circuits",
    summary: "Circuit simulation — DC/AC/transient via ngspice",
    description:
      "PySpice is a Python interface to ngspice for numerical circuit simulation. It supports DC operating point, AC frequency sweep, and transient time-domain analysis of analog and mixed-signal circuits.",
    capabilities: [
      "DC operating point analysis",
      "AC frequency sweep (Bode plots)",
      "Transient time-domain simulation",
      "SPICE netlist import from Lcapy",
      "Parametric sweeps",
    ],
    whenToUse:
      "Use PySpice for numerical circuit simulation: verify symbolic results from Lcapy, simulate nonlinear circuits, or compute time-domain responses. Standard SPICE-compatible analysis.",
    alternatives:
      "For symbolic analysis, use Lcapy. For control system analysis (Bode/Nyquist), use python-control.",
    params: {
      simulation_type: { type: "select", description: "Analysis type", options: { dc: "DC operating point", ac: "AC frequency sweep", transient: "Transient simulation" } },
      netlist: { type: "text", description: "SPICE netlist (can be auto-generated from Lcapy)" },
      duration: { type: "number", unit: "s", description: "Transient simulation duration" },
      freq_start: { type: "number", unit: "Hz", description: "AC sweep start frequency" },
      freq_stop: { type: "number", unit: "Hz", description: "AC sweep stop frequency" },
    },
    outputs: {
      voltages: "Node voltages over time/frequency",
      currents: "Branch currents",
      frequency_response: "Magnitude and phase vs frequency",
    },
    examples: ["RLC Transient preset"],
    references: [
      { label: "PySpice documentation", url: "https://pyspice.fabrice-salvaire.fr/" },
    ],
    license: "GPL-3.0",
    limitations: [
      "Requires ngspice backend",
      "No RF/microwave simulation",
      "Limited semiconductor device models compared to commercial SPICE",
    ],
  },

  control: {
    name: "python-control",
    layer: "engineering",
    summary: "Control systems — Bode, Nyquist, root locus, step response",
    description:
      "python-control implements control systems analysis and design in Python. It provides transfer function manipulation, frequency response (Bode, Nyquist), root locus, state-space models, and time-domain simulation.",
    capabilities: [
      "Transfer function and state-space models",
      "Bode and Nyquist plots",
      "Root locus analysis",
      "Step and impulse response",
      "PID controller design",
      "Gain and phase margins",
    ],
    whenToUse:
      "Use python-control for control systems engineering: stability analysis, controller design, frequency response. Receives transfer functions from Lcapy or manually specified systems.",
    alternatives:
      "MATLAB Control System Toolbox is the commercial equivalent. For circuit-level analysis, use PySpice.",
    params: {
      simulation_type: { type: "select", description: "Analysis type", options: { bode: "Bode plot", nyquist: "Nyquist plot", root_locus: "Root locus", step: "Step response", impulse: "Impulse response" } },
      numerator: { type: "json", description: "Transfer function numerator coefficients" },
      denominator: { type: "json", description: "Transfer function denominator coefficients" },
    },
    outputs: {
      bode_data: "Magnitude and phase vs frequency",
      step_response: "Step response time series",
      poles: "Closed-loop poles",
      margins: "Gain and phase margins",
    },
    examples: [],
    references: [
      { label: "python-control documentation", url: "https://python-control.readthedocs.io/" },
    ],
    license: "BSD-3-Clause",
    limitations: [
      "SISO analysis primarily (MIMO support limited)",
      "No nonlinear system analysis",
      "No real-time hardware interface",
    ],
  },

  // ═══════════════════════════════════════════
  // VISUALIZATION
  // ═══════════════════════════════════════════
  matplotlib: {
    name: "Matplotlib",
    layer: "visualization",
    summary: "Publication-quality plots — line, scatter, histogram, heatmap, contour, bar",
    description:
      "Matplotlib is the standard Python plotting library. It produces publication-quality figures: line plots, scatter plots, histograms, contour maps, heatmaps, bar charts, and more.",
    capabilities: [
      "Line, scatter, and bar plots",
      "Histograms and density plots",
      "Contour and filled contour plots",
      "Heatmaps (imshow, pcolormesh)",
      "3D surface plots",
      "LaTeX-rendered labels and annotations",
    ],
    whenToUse:
      "Use Matplotlib for publication-quality static plots of simulation results. Receives field data from FEniCS, PhiFlow, or any numerical simulation and creates customizable figures.",
    alternatives:
      "For animated visualizations, use Manim. For 3D scientific rendering, use VTK. For interactive web plots, Plotly is built into the visualizer.",
    params: {
      plot_type: { type: "select", description: "Plot type", options: { line: "Line plot", scatter: "Scatter plot", histogram: "Histogram", heatmap: "Heatmap", contour: "Contour plot", bar: "Bar chart" } },
      x_data: { type: "json", description: "X-axis data (or auto-generated from pipeline)" },
      y_data: { type: "json", description: "Y-axis data" },
      z_data: { type: "json", description: "Z-axis data (heatmap/contour)" },
      title: { type: "text", description: "Plot title" },
      xlabel: { type: "text", description: "X-axis label" },
      ylabel: { type: "text", description: "Y-axis label" },
    },
    outputs: {
      image: "PNG image of the plot",
      svg: "SVG vector image",
    },
    examples: ["Sine Plot preset"],
    references: [
      { label: "Matplotlib documentation", url: "https://matplotlib.org/stable/contents.html" },
    ],
    license: "PSF-based",
    limitations: [
      "Static images only (no interactivity)",
      "Not real-time visualization",
      "Large datasets may be slow to render",
    ],
  },

  manim: {
    name: "Manim",
    layer: "visualization",
    summary: "Mathematical animation — equations, graphs, geometry → MP4/GIF",
    description:
      "Manim (Mathematical Animation Engine) creates precise mathematical animations. It renders equations, geometric transformations, graph animations, and explanatory videos as MP4 or GIF.",
    capabilities: [
      "LaTeX equation animation",
      "Geometric transformation animations",
      "Graph and tree traversal visualization",
      "3D scene rendering",
      "Bloch sphere animation (via QuTiP coupling)",
      "Orbital trajectory animation (via REBOUND coupling)",
    ],
    whenToUse:
      "Use Manim to create animated explanations of simulation results: animated equations from SymPy, orbital visualizations from REBOUND, graph traversals from NetworkX, or Bloch sphere animations from QuTiP.",
    alternatives:
      "For static plots, use Matplotlib. For interactive 3D, use VTK.",
    params: {
      simulation_type: { type: "select", description: "Animation type", options: { equation: "LaTeX equation animation", graph_anim: "Graph animation", bloch_sphere: "Bloch sphere trajectory", geometry: "Geometric animation" } },
      expressions: { type: "json", description: "LaTeX expressions to animate" },
      output_format: { type: "select", description: "Output format", options: { mp4: "MP4 video", gif: "Animated GIF" } },
    },
    outputs: {
      video: "MP4 or GIF animation file",
      frames: "Individual frame images",
    },
    examples: ["Pythagorean Animation preset"],
    references: [
      { label: "Manim Community docs", url: "https://docs.manim.community/" },
    ],
    license: "MIT",
    limitations: [
      "Rendering can be slow for complex scenes",
      "Video output only (not interactive)",
      "Requires LaTeX installation for equation rendering",
    ],
  },

  vtk: {
    name: "VTK",
    layer: "visualization",
    summary: "Scientific visualization — field render, isosurface, streamlines",
    description:
      "VTK (Visualization Toolkit) provides advanced 3D scientific visualization. It renders volumetric data, isosurfaces, streamlines, and field data from FEM simulations, CFD results, and medical imaging.",
    capabilities: [
      "Volume rendering",
      "Isosurface extraction",
      "Streamline visualization",
      "Vector field (glyph) rendering",
      "Mesh visualization",
    ],
    whenToUse:
      "Use VTK for 3D scientific visualization of simulation results: fluid velocity fields from OpenFOAM, temperature fields from FEniCS, or any volumetric data. Produces high-quality rendered images.",
    alternatives:
      "For 2D plots, use Matplotlib. For animated math, use Manim. For interactive 3D in-browser, MolStar is available for molecular data.",
    params: {
      render_type: { type: "select", description: "Rendering mode", options: { field: "Scalar field rendering", isosurface: "Isosurface extraction", streamlines: "Streamline visualization", mesh: "Mesh wireframe" } },
      field_data: { type: "json", description: "Scalar/vector field data" },
      x_grid: { type: "json", description: "X coordinates" },
      y_grid: { type: "json", description: "Y coordinates" },
    },
    outputs: {
      image: "Rendered PNG image",
    },
    examples: [],
    references: [
      { label: "VTK documentation", url: "https://vtk.org/documentation/" },
    ],
    license: "BSD-3-Clause",
    limitations: [
      "Static image output (not interactive in web UI)",
      "Requires off-screen rendering on server",
      "Large datasets can be memory-intensive",
    ],
  },

  // ═══════════════════════════════════════════
  // FLUID DYNAMICS
  // ═══════════════════════════════════════════
  openfoam: {
    name: "OpenFOAM",
    layer: "fluid-dynamics",
    summary: "CFD — lid-driven cavity, pipe flow, external flow",
    description:
      "OpenFOAM is an open-source CFD toolbox for solving incompressible and compressible fluid flow problems. It includes pre-built solvers for many flow configurations and turbulence models.",
    capabilities: [
      "Incompressible flow (icoFoam, simpleFoam)",
      "Compressible flow (rhoSimpleFoam)",
      "Turbulence modeling (k-epsilon, k-omega SST)",
      "Mesh generation (blockMesh, snappyHexMesh)",
      "Post-processing (ParaView integration)",
    ],
    whenToUse:
      "Use OpenFOAM for engineering CFD: lid-driven cavity, pipe flow, external aerodynamics. Standard open-source choice for production CFD with complex geometries.",
    alternatives:
      "For spectral methods, use Dedalus. For compressible/transonic, use SU2. For differentiable physics, use PhiFlow.",
    params: {
      case_type: { type: "select", description: "Flow case", options: { lid_cavity: "Lid-driven cavity", pipe_flow: "Pipe flow", external: "External flow around body" } },
      reynolds: { type: "number", description: "Reynolds number" },
      solver: { type: "select", description: "Solver", options: { icoFoam: "Incompressible transient", simpleFoam: "Incompressible steady-state", pisoFoam: "Incompressible PISO" } },
      end_time: { type: "number", unit: "s", description: "Simulation end time" },
    },
    outputs: {
      field_data: "Velocity and pressure field data",
      x_grid: "X coordinates",
      y_grid: "Y coordinates",
      residuals: "Solver convergence residuals",
    },
    examples: ["Lid-Driven Cavity preset"],
    references: [
      { label: "OpenFOAM documentation", url: "https://www.openfoam.com/documentation/" },
    ],
    license: "GPL-3.0",
    limitations: [
      "Complex case setup (dictionaries, mesh generation)",
      "No built-in GUI (command-line only)",
      "Mesh quality critical for convergence",
    ],
  },

  dedalus: {
    name: "Dedalus",
    layer: "fluid-dynamics",
    summary: "Spectral PDE solver — Rayleigh-Bénard, diffusion, waves",
    description:
      "Dedalus is a spectral PDE solver for fluid dynamics and related problems. It uses Fourier and Chebyshev spectral methods, achieving high accuracy for smooth problems on simple geometries.",
    capabilities: [
      "Rayleigh-Bénard convection",
      "Diffusion equation",
      "Wave equation",
      "Custom PDE systems",
      "Spectral accuracy (exponential convergence for smooth solutions)",
    ],
    whenToUse:
      "Use Dedalus for spectral-accuracy PDE solutions: convection, turbulence, waves on periodic or bounded domains. Best for problems where high accuracy on simple geometries is needed.",
    alternatives:
      "For complex geometries, use FEniCS. For engineering CFD, use OpenFOAM.",
    params: {
      simulation_type: { type: "select", description: "Problem type", options: { rayleigh_benard: "Rayleigh-Bénard convection", diffusion: "Diffusion equation", wave: "Wave equation" } },
      rayleigh: { type: "number", description: "Rayleigh number (convection)" },
      resolution: { type: "number", description: "Spectral resolution (modes)" },
      end_time: { type: "number", description: "Simulation end time" },
    },
    outputs: {
      field_data: "Solution field values",
      x_grid: "X coordinates",
      y_grid: "Y coordinates",
    },
    examples: ["Rayleigh-Bénard preset"],
    references: [
      { label: "Dedalus documentation", url: "https://dedalus-project.readthedocs.io/" },
    ],
    license: "GPL-3.0",
    limitations: [
      "Simple geometries only (rectangles, cylinders, spheres)",
      "Not suitable for complex engineering geometries",
      "Resolution limited by available memory",
    ],
  },

  su2: {
    name: "SU2",
    layer: "fluid-dynamics",
    summary: "Compressible CFD — Euler, RANS, transonic airfoil flow",
    description:
      "SU2 is an open-source CFD code designed for compressible flow, adjoint optimization, and multiphysics. It handles Euler and RANS equations for external aerodynamics, including transonic and supersonic flows.",
    capabilities: [
      "Euler equations (inviscid compressible flow)",
      "RANS turbulence modeling",
      "Adjoint-based design optimization",
      "Mesh deformation",
      "Transonic and supersonic flows",
    ],
    whenToUse:
      "Use SU2 for compressible aerodynamics: transonic airfoil analysis, supersonic flow, and design optimization. Complements OpenFOAM for compressible regimes.",
    alternatives:
      "For incompressible flow, use OpenFOAM. For spectral accuracy, use Dedalus.",
    params: {
      simulation_type: { type: "select", description: "Flow type", options: { euler: "Euler (inviscid)", rans: "RANS (turbulent)" } },
      mach: { type: "number", description: "Freestream Mach number" },
      angle_of_attack: { type: "number", unit: "degrees", description: "Angle of attack" },
      mesh_file: { type: "text", description: "Mesh file path (from Gmsh)" },
    },
    outputs: {
      field_data: "Pressure, velocity, density fields",
      lift_coefficient: "Cl",
      drag_coefficient: "Cd",
      residuals: "Convergence history",
    },
    examples: ["NACA Airfoil preset"],
    references: [
      { label: "SU2 documentation", url: "https://su2code.github.io/" },
    ],
    license: "LGPL-2.1",
    limitations: [
      "Less mature than OpenFOAM for some cases",
      "Requires structured or unstructured mesh input",
      "RANS turbulence modeling has inherent limitations",
    ],
  },

  phiflow: {
    name: "PhiFlow",
    layer: "fluid-dynamics",
    summary: "Differentiable physics — smoke, fluid, diffusion, wave (NumPy/JAX)",
    description:
      "PhiFlow is a differentiable physics simulation framework. It solves fluid dynamics, diffusion, and wave equations with automatic differentiation support, enabling gradient-based optimization of physics simulations.",
    capabilities: [
      "Smoke and fluid simulation",
      "Diffusion equation",
      "Wave equation",
      "Differentiable simulation (JAX backend)",
      "Automatic differentiation through physics",
    ],
    whenToUse:
      "Use PhiFlow for differentiable physics simulations: when you need gradients through the simulation for optimization or machine learning. Also good for quick fluid/diffusion simulations.",
    alternatives:
      "For production CFD, use OpenFOAM. For spectral accuracy, use Dedalus.",
    params: {
      simulation_type: { type: "select", description: "Physics type", options: { smoke: "Smoke simulation", fluid: "Fluid flow", diffusion: "Diffusion equation", wave: "Wave equation" } },
      resolution: { type: "number", description: "Grid resolution" },
      steps: { type: "number", description: "Number of time steps" },
      backend: { type: "select", description: "Compute backend", options: { numpy: "NumPy (CPU)", jax: "JAX (differentiable)" } },
    },
    outputs: {
      field_data: "Velocity/density/temperature field data",
      x_grid: "X coordinates",
      y_grid: "Y coordinates",
    },
    examples: [],
    references: [
      { label: "PhiFlow documentation", url: "https://tum-pbs.github.io/PhiFlow/" },
    ],
    license: "MIT",
    limitations: [
      "Lower accuracy than spectral or FEM methods",
      "Regular grid only (no unstructured meshes)",
      "JAX backend required for differentiation",
    ],
  },

  // ═══════════════════════════════════════════
  // ENGINEERING / MESH
  // ═══════════════════════════════════════════
  gmsh: {
    name: "Gmsh",
    layer: "engineering",
    summary: "Mesh generation — 2D/3D FEM meshes, CAD geometry",
    description:
      "Gmsh is an open-source mesh generator for 2D and 3D finite element meshes. It handles CAD geometry import, structured and unstructured meshing, and exports to formats compatible with FEniCS, Elmer, OpenFOAM, and SU2.",
    capabilities: [
      "2D triangle and quad meshing",
      "3D tetrahedral and hexahedral meshing",
      "CAD geometry import (STEP, IGES)",
      "Mesh refinement and optimization",
      "Export to MSH, VTK, STL formats",
    ],
    whenToUse:
      "Use Gmsh as the mesh generation step before any FEM/CFD simulation. It creates meshes consumed by FEniCS, Elmer, Firedrake, OpenFOAM, and SU2.",
    alternatives:
      "For simple built-in meshes, FEniCS and Firedrake have their own mesh generators.",
    params: {
      mesh_type: { type: "select", description: "Mesh type", options: { box_2d: "2D rectangular domain", box_3d: "3D box domain", circle: "2D circular domain", sphere: "3D sphere" } },
      resolution: { type: "number", description: "Characteristic mesh size" },
      algorithm: { type: "select", description: "Meshing algorithm", options: { auto: "Automatic", delaunay: "Delaunay", frontal: "Frontal" } },
    },
    outputs: {
      mesh_file_path: "Path to generated .msh file",
      n_elements: "Number of mesh elements",
      n_nodes: "Number of mesh nodes",
      mesh_info: "Mesh quality statistics",
    },
    examples: [],
    references: [
      { label: "Gmsh documentation", url: "https://gmsh.info/doc/texinfo/gmsh.html" },
    ],
    license: "GPL-2.0+",
    limitations: [
      "Complex CAD geometries may need manual cleanup",
      "Mesh quality depends on input geometry",
      "Large 3D meshes can be slow to generate",
    ],
  },

  // ═══════════════════════════════════════════
  // DEFERRED TOOLS
  // ═══════════════════════════════════════════
  comsol: {
    name: "COMSOL",
    layer: "engineering",
    summary: "Multiphysics FEM (DEFERRED — license required)",
    description:
      "COMSOL Multiphysics is a commercial FEM solver for coupled multiphysics problems. This tool is deferred pending license acquisition. Coupling stubs exist for future integration with PySpice, Cantera, Gmsh, LAMMPS, QE, and SymPy.",
    capabilities: [
      "Multiphysics coupling (thermal-structural-EM-fluid)",
      "Extensive material library",
      "Parametric sweeps and optimization",
    ],
    whenToUse:
      "COMSOL is not yet available on this platform. Use FEniCS or Elmer for similar FEM capabilities.",
    alternatives:
      "FEniCS for custom PDE, Elmer for multiphysics coupling.",
    params: {},
    outputs: {},
    examples: [],
    references: [
      { label: "COMSOL website", url: "https://www.comsol.com/" },
    ],
    license: "Commercial (not available)",
    limitations: ["DEFERRED — requires commercial license", "Not currently operational on this platform"],
  },

  alphafold: {
    name: "AlphaFold",
    layer: "molecular",
    summary: "Protein structure prediction (DEFERRED — storage required)",
    description:
      "AlphaFold predicts protein 3D structures from amino acid sequences with near-experimental accuracy. This tool is deferred pending storage provisioning for the large model weights and databases.",
    capabilities: [
      "Protein structure prediction from sequence",
      "Confidence (pLDDT) scoring per residue",
      "Multiple sequence alignment (MSA) search",
    ],
    whenToUse:
      "AlphaFold is not yet available on this platform. For protein structure manipulation, use PyRosetta (also deferred) or prepare structures manually.",
    alternatives:
      "ESMFold (lighter model), or manual PDB structure download.",
    params: {},
    outputs: {},
    examples: [],
    references: [
      { label: "AlphaFold", url: "https://alphafold.ebi.ac.uk/" },
    ],
    license: "Apache-2.0",
    limitations: ["DEFERRED — requires ~2TB storage for databases", "Not currently operational on this platform"],
  },

  pyrosetta: {
    name: "PyRosetta",
    layer: "molecular",
    summary: "Protein modeling and design (DEFERRED — license required)",
    description:
      "PyRosetta provides Python bindings to the Rosetta molecular modeling suite for protein design, docking, and structure prediction. Deferred pending academic license.",
    capabilities: [
      "Protein design (fixed backbone, flexible backbone)",
      "Protein-ligand docking",
      "Structure refinement (relax)",
      "Scoring functions (REF2015, etc.)",
    ],
    whenToUse:
      "PyRosetta is not yet available on this platform. For MD-based protein refinement, use OpenMM.",
    alternatives:
      "OpenMM for MD refinement, RDKit for small molecule work.",
    params: {},
    outputs: {},
    examples: [],
    references: [
      { label: "PyRosetta", url: "https://www.pyrosetta.org/" },
    ],
    license: "Academic license required",
    limitations: ["DEFERRED — requires academic license", "Not currently operational on this platform"],
  },
};

// Helper: get all tool keys
export const allToolKeys = Object.keys(toolDocs);

// Helper: get tools grouped by layer
export function getToolsByLayer() {
  const groups = {};
  for (const [key, doc] of Object.entries(toolDocs)) {
    const layer = doc.layer;
    if (!groups[layer]) groups[layer] = [];
    groups[layer].push({ key, ...doc });
  }
  return groups;
}

// Helper: search tools by query
export function searchTools(query) {
  if (!query) return Object.entries(toolDocs).map(([key, doc]) => ({ key, ...doc }));
  const q = query.toLowerCase();
  return Object.entries(toolDocs)
    .filter(([key, doc]) =>
      key.includes(q) ||
      doc.name.toLowerCase().includes(q) ||
      doc.summary.toLowerCase().includes(q) ||
      doc.description.toLowerCase().includes(q) ||
      doc.layer.toLowerCase().includes(q)
    )
    .map(([key, doc]) => ({ key, ...doc }));
}
