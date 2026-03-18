import React, { useState, useCallback, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import SimulationPanel from './components/SimulationPanel';
import PipelineBuilder from './components/PipelineBuilder';
import PipelinePanel from './components/PipelinePanel';
import SweepPanel from './components/SweepPanel';
import ResultsBrowser from './components/ResultsBrowser';
import ResultDetail from './components/ResultDetail';
import ExportButton from './components/ExportButton';
import DocsPanel from './components/DocsPanel';
import ProjectSelector from './components/ProjectSelector';
import LoginPage from './components/LoginPage';
import MobileNav from './components/MobileNav';
import VisualizerArea from './visualizers/VisualizerArea';
import { useSimulation } from './hooks/useSimulation';
import { useProjects } from './hooks/useProjects';
import { useAuth } from './hooks/useAuth';
import { useBreakpoint } from './hooks/useBreakpoint';
import { setAuthCallbacks } from './api/client';
import theme from './theme.json';

const toolInfo = {
  rebound: { key: 'rebound', name: 'REBOUND', description: 'N-body gravitational dynamics simulator' },
  qutip: { key: 'qutip', name: 'QuTiP', description: 'Quantum dynamics simulator' },
  openmm: { key: 'openmm', name: 'OpenMM', description: 'GPU-accelerated molecular dynamics' },
  pyscf: { key: 'pyscf', name: 'PySCF', description: 'Electronic structure calculations (HF, DFT, MP2, CCSD)' },
  mdanalysis: { key: 'mdanalysis', name: 'MDAnalysis', description: 'Trajectory analysis and post-processing' },
  psi4: { key: 'psi4', name: 'Psi4', description: 'Ab initio quantum chemistry with SAPT' },
  gromacs: { key: 'gromacs', name: 'GROMACS', description: 'High-performance molecular dynamics' },
  namd: { key: 'namd', name: 'NAMD', description: 'Scalable molecular dynamics' },
  qmmm: { key: 'qmmm', name: 'QM/MM', description: 'Hybrid QM/MM via ASH (PySCF + OpenMM)' },
  pybullet: { key: 'pybullet', name: 'PyBullet', description: 'Rigid body dynamics, collisions, and robotics' },
  einsteinpy: { key: 'einsteinpy', name: 'EinsteinPy', description: 'Geodesics and spacetime metrics in GR' },
  nrpy: { key: 'nrpy', name: 'NRPy+', description: 'Numerical relativity — BBH, gravitational waves, neutron stars' },
  fenics: { key: 'fenics', name: 'FEniCS', description: 'Finite element method — heat, elasticity, Stokes' },
  elmer: { key: 'elmer', name: 'Elmer', description: 'Multiphysics FEM — structural, thermal, coupled' },
  basico: { key: 'basico', name: 'BasiCO', description: 'Biochemical reaction networks (COPASI)' },
  tellurium: { key: 'tellurium', name: 'Tellurium', description: 'SBML/Antimony pathway models' },
  brian2: { key: 'brian2', name: 'Brian2', description: 'Spiking neural networks' },
  nest: { key: 'nest', name: 'NEST', description: 'Large-scale neural simulation' },
  msprime: { key: 'msprime', name: 'msprime', description: 'Coalescent population genetics' },
  rdkit: { key: 'rdkit', name: 'RDKit', description: 'Cheminformatics — SMILES, descriptors, fingerprints, conformers' },
  cantera: { key: 'cantera', name: 'Cantera', description: 'Chemical kinetics — combustion, ignition, flame speed' },
  qe: { key: 'qe', name: 'Quantum ESPRESSO', description: 'Materials DFT — SCF, bands, DOS, relaxation' },
  lammps: { key: 'lammps', name: 'LAMMPS', description: 'Materials MD — LJ fluids, metals, polymer melts' },
  sympy: { key: 'sympy', name: 'SymPy', description: 'Symbolic math — calculus, equation solving, code generation' },
  gmsh: { key: 'gmsh', name: 'Gmsh', description: 'Mesh generation — 2D/3D FEM meshes, CAD geometry' },
  lcapy: { key: 'lcapy', name: 'Lcapy', description: 'Symbolic circuits — transfer functions, pole-zero analysis' },
  pennylane: { key: 'pennylane', name: 'PennyLane', description: 'Differentiable quantum computing — VQE, QNN' },
  sagemath: { key: 'sagemath', name: 'SageMath', description: 'Comprehensive math — algebra, number theory, geometry' },
  lean4: { key: 'lean4', name: 'Lean 4', description: 'Formal verification — theorem proving, proofs' },
  gap: { key: 'gap', name: 'GAP', description: 'Group theory — permutation groups, character tables' },
  pyspice: { key: 'pyspice', name: 'PySpice', description: 'Circuit simulation — DC/AC/transient via ngspice' },
  qiskit: { key: 'qiskit', name: 'Qiskit', description: 'Quantum computing — circuits, Aer simulation, VQE' },
  matplotlib: { key: 'matplotlib', name: 'Matplotlib', description: 'Publication-quality plots — line, scatter, histogram, heatmap, contour, bar' },
  control: { key: 'control', name: 'python-control', description: 'Control systems — Bode, Nyquist, root locus, step response' },
  pyomo: { key: 'pyomo', name: 'Pyomo', description: 'LP, MILP, NLP with GLPK/HiGHS/CBC/IPOPT solvers' },
  networkx: { key: 'networkx', name: 'NetworkX', description: 'Graph theory — shortest paths, centrality, community detection' },
  phiflow: { key: 'phiflow', name: 'PhiFlow', description: 'Differentiable physics — smoke, fluid, diffusion, wave (NumPy/JAX)' },
  manim: { key: 'manim', name: 'Manim', description: 'Mathematical animation — equations, graphs, geometry → MP4/GIF' },
  openfoam: { key: 'openfoam', name: 'OpenFOAM', description: 'CFD — lid-driven cavity, pipe flow, external flow' },
  dedalus: { key: 'dedalus', name: 'Dedalus', description: 'Spectral PDE solver — Rayleigh-Bénard, diffusion, waves' },
  su2: { key: 'su2', name: 'SU2', description: 'Compressible CFD — Euler, RANS, transonic airfoil flow' },
  firedrake: { key: 'firedrake', name: 'Firedrake', description: 'FEM — Poisson, Stokes, elasticity, advection-diffusion (PETSc)' },
  vtk: { key: 'vtk', name: 'VTK', description: 'Scientific visualization — field render, isosurface, streamlines' },
  openbabel: { key: 'openbabel', name: 'Open Babel', description: 'Universal chemical format converter — 110+ formats, 3D optimization' },
  comsol: { key: 'comsol', name: 'COMSOL', description: 'Multiphysics FEM (DEFERRED — license required)' },
  alphafold: { key: 'alphafold', name: 'AlphaFold', description: 'Protein structure prediction (DEFERRED — storage required)' },
  slim: { key: 'slim', name: 'SLiM', description: 'Forward-time evolutionary simulation — neutral, selection, nucleotide, spatial' },
  tskit: { key: 'tskit', name: 'tskit', description: 'Tree sequence analysis — diversity, Fst, recapitation' },
  simupop: { key: 'simupop', name: 'simuPOP', description: 'Forward-time population genetics — mating, migration, selection' },
  pyrosetta: { key: 'pyrosetta', name: 'PyRosetta', description: 'Protein modeling and design (DEFERRED — license required)' },
  einstein_toolkit: { key: 'einstein_toolkit', name: 'Einstein Toolkit', description: 'Full numerical relativity — BBH inspiral, neutron stars, dynamical spacetimes' },
  rayoptics: { key: 'rayoptics', name: 'RayOptics', description: 'Geometrical ray tracing — singlet/doublet lenses, spot diagrams' },
  lightpipes: { key: 'lightpipes', name: 'LightPipes', description: 'Physical wave optics — diffraction, interference, beam propagation' },
  strawberryfields: { key: 'strawberryfields', name: 'Strawberry Fields', description: 'Quantum photonics — squeezed states, HOM effect, boson sampling' },
  meep: { key: 'meep', name: 'Meep', description: 'FDTD electromagnetic simulation — waveguides, resonators, photonic crystals' },
};

export default function App() {
  // Navigation: dashboard or detail view
  const [view, setView] = useState('dashboard'); // 'dashboard' | 'detail'
  const [detailType, setDetailType] = useState(null); // 'tool' | 'pipeline' | 'coupling' | 'sweep' | 'result-detail'
  const [detailTarget, setDetailTarget] = useState(null); // context object for the detail view

  const [selectedTool, setSelectedTool] = useState(null);
  const [params, setParams] = useState({});
  const [docsOpen, setDocsOpen] = useState(false);
  const [docsFilter, setDocsFilter] = useState({ tab: 'tools', filter: '' });
  const [selectedResult, setSelectedResult] = useState(null);
  const simulation = useSimulation();
  const projectsHook = useProjects();
  const auth = useAuth();
  const { isMobile } = useBreakpoint();

  // Wire auth callbacks into axios interceptors
  useEffect(() => {
    setAuthCallbacks(() => auth.token, () => auth.logout());
  }, [auth.token, auth.logout]);

  const handleOpenDocs = useCallback((tab, filter) => {
    setDocsFilter({ tab: tab || 'tools', filter: filter || '' });
    setDocsOpen(true);
  }, []);

  // Keyboard shortcut: ? toggles DocsPanel
  useEffect(() => {
    const handler = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;
      if (e.key === '?') {
        setDocsOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  // --- Navigation functions ---

  const navigateToDashboard = useCallback(() => {
    setView('dashboard');
    setDetailType(null);
    setDetailTarget(null);
  }, []);

  const navigateToTool = useCallback((tool) => {
    setSelectedTool(tool);
    setParams({});
    setSelectedResult(null);
    simulation.reset();
    setView('detail');
    setDetailType('tool');
    setDetailTarget(tool);
  }, [simulation]);

  const navigateToPreset = useCallback((presetData) => {
    const toolKey = presetData.tool;
    const info = toolInfo[toolKey];
    if (info) {
      setSelectedTool(info);
      setParams(presetData.params || {});
      setSelectedResult(null);
      simulation.reset();
      setView('detail');
      setDetailType('tool');
      setDetailTarget(info);
    }
  }, [simulation]);

  const navigateToPipeline = useCallback((key, pipeline) => {
    setSelectedResult(null);
    setView('detail');
    setDetailType('pipeline');
    setDetailTarget({ key, ...pipeline });
  }, []);

  const navigateToCoupling = useCallback((key, coupling) => {
    setSelectedResult(null);
    setView('detail');
    setDetailType('coupling');
    setDetailTarget({ key, ...coupling });
  }, []);

  const navigateToSweep = useCallback(() => {
    setSelectedResult(null);
    setView('detail');
    setDetailType('sweep');
    setDetailTarget(null);
  }, []);

  const navigateToResultDetail = useCallback((result) => {
    setSelectedResult(result);
    setView('detail');
    setDetailType('result-detail');
    setDetailTarget(result);
  }, []);

  const handleRun = useCallback((request) => {
    simulation.run({ ...request, project: projectsHook.activeProject });
  }, [simulation, projectsHook.activeProject]);

  const handleRerun = useCallback((result) => {
    const info = toolInfo[result.tool];
    if (info) {
      setSelectedTool(info);
      setParams(result.params || {});
      setSelectedResult(null);
      setView('detail');
      setDetailType('tool');
      setDetailTarget(info);
    }
  }, []);

  // Derive a display name for the detail header
  const detailName = detailType === 'tool' ? detailTarget?.name
    : detailType === 'pipeline' ? detailTarget?.label
    : detailType === 'coupling' ? `${detailTarget?.from} → ${detailTarget?.to}`
    : detailType === 'sweep' ? 'Parameter Sweep'
    : detailType === 'result-detail' ? (detailTarget?.tool || 'Result')
    : '';

  // Auth loading state
  if (auth.loading) {
    return (
      <div style={{
        width: '100vw', height: '100vh', background: theme.colors.bg,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: theme.colors.textSecondary, fontSize: 14,
      }}>
        Loading...
      </div>
    );
  }

  // Auth gate
  if (auth.needsLogin) {
    return <LoginPage onLogin={auth.setToken} />;
  }

  const isDetail = view === 'detail';

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      width: '100vw',
      height: '100vh',
      background: theme.colors.bg,
    }}>
      {/* Header */}
      <header style={{
        height: 48,
        background: theme.colors.bgSecondary,
        borderBottom: `1px solid ${theme.colors.border}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 20px',
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {/* Back button when in detail view */}
          {isDetail && (
            <button
              onClick={navigateToDashboard}
              style={{
                background: 'none', border: 'none', color: theme.colors.text,
                fontSize: 18, cursor: 'pointer', padding: '0 4px',
              }}
              title="Back to dashboard"
            >
              {'\u2190'}
            </button>
          )}
          <span
            onClick={isDetail ? navigateToDashboard : undefined}
            style={{
              fontSize: isMobile ? 14 : 18,
              fontWeight: 700,
              color: theme.colors.text,
              cursor: isDetail ? 'pointer' : 'default',
            }}
          >
            totalSimulation
          </span>
          {!isMobile && (
            <span style={{
              fontSize: 12,
              color: '#14b8a6',
              background: '#14b8a618',
              padding: '2px 8px',
              borderRadius: 4,
              border: '1px solid #14b8a633',
            }}>
              Phase 16
            </span>
          )}
          {/* Detail context name */}
          {isDetail && detailName && !isMobile && (
            <>
              <span style={{ color: theme.colors.textSecondary, fontSize: 14 }}>/</span>
              <span style={{ fontSize: 14, color: theme.colors.textSecondary }}>
                {detailName}
              </span>
            </>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: isMobile ? 6 : 12 }}>
          {/* Project selector */}
          <ProjectSelector
            projects={projectsHook.projects}
            activeProject={projectsHook.activeProject}
            onSelect={projectsHook.setActiveProject}
            onCreate={projectsHook.createProject}
            compact={isMobile}
          />

          {/* Docs button */}
          {!isMobile && (
            <button
              onClick={() => handleOpenDocs('tools', '')}
              style={{
                padding: '4px 12px',
                background: docsOpen ? theme.colors.accent : theme.colors.bgTertiary,
                border: `1px solid ${docsOpen ? theme.colors.accent : theme.colors.border}`,
                borderRadius: 4,
                color: docsOpen ? '#fff' : theme.colors.textSecondary,
                fontSize: 11,
                cursor: 'pointer',
              }}
            >
              Docs
            </button>
          )}

          {!isMobile && simulation.jobId && (
            <span style={{ fontSize: 11, color: theme.colors.textSecondary, fontFamily: 'monospace' }}>
              Job: {simulation.jobId.slice(0, 8)}...
            </span>
          )}

          {auth.authRequired && (
            <button
              onClick={auth.logout}
              style={{
                padding: '4px 10px',
                background: 'transparent',
                border: `1px solid ${theme.colors.border}`,
                borderRadius: 4,
                color: theme.colors.textSecondary,
                fontSize: 11,
                cursor: 'pointer',
              }}
            >
              Logout
            </button>
          )}
        </div>
      </header>

      {/* Main content */}
      <div style={{
        display: 'flex',
        flexDirection: isMobile ? 'column' : 'row',
        flex: 1,
        overflow: 'hidden',
        paddingBottom: isMobile ? 56 : 0,
      }}>
        {view === 'dashboard' ? (
          /* ===== DASHBOARD VIEW ===== */
          <Dashboard
            onSelectTool={navigateToTool}
            onLoadPreset={navigateToPreset}
            onSelectPipeline={navigateToPipeline}
            onSelectCoupling={navigateToCoupling}
            onSelectSweep={navigateToSweep}
            onSelectResult={navigateToResultDetail}
            project={projectsHook.activeProject}
            isMobile={isMobile}
          />
        ) : (
          /* ===== DETAIL VIEW ===== */
          <>
            {/* Left panel */}
            {detailType === 'tool' ? (
              <SimulationPanel
                tool={selectedTool}
                params={params}
                onParamsChange={setParams}
                onRun={handleRun}
                simulation={simulation}
                onOpenDocs={handleOpenDocs}
                style={isMobile ? { width: '100%', maxHeight: '40vh', flexShrink: 0 } : undefined}
              />
            ) : detailType === 'pipeline' ? (
              <PipelinePanel
                pipeline={detailTarget}
                onOpenDocs={handleOpenDocs}
                isMobile={isMobile}
                style={isMobile ? { width: '100%', maxHeight: '40vh', flexShrink: 0 } : undefined}
              />
            ) : detailType === 'coupling' ? (
              <div style={{
                width: isMobile ? '100%' : 320,
                maxHeight: isMobile ? '40vh' : undefined,
                background: theme.colors.bgSecondary,
                borderRight: isMobile ? 'none' : `1px solid ${theme.colors.border}`,
                borderBottom: isMobile ? `1px solid ${theme.colors.border}` : 'none',
                flexShrink: 0,
                overflow: 'hidden',
              }}>
                <PipelineBuilder
                  onOpenDocs={handleOpenDocs}
                  initialCoupling={detailTarget?.key}
                />
              </div>
            ) : detailType === 'sweep' ? (
              <div style={{
                width: isMobile ? '100%' : 320,
                maxHeight: isMobile ? '40vh' : undefined,
                background: theme.colors.bgSecondary,
                borderRight: isMobile ? 'none' : `1px solid ${theme.colors.border}`,
                borderBottom: isMobile ? `1px solid ${theme.colors.border}` : 'none',
                flexShrink: 0,
                overflow: 'hidden',
              }}>
                <SweepPanel />
              </div>
            ) : detailType === 'result-detail' ? (
              <ResultsBrowser
                project={projectsHook.activeProject}
                onSelectResult={(r) => { setSelectedResult(r); setDetailTarget(r); }}
                selectedResult={selectedResult}
                style={isMobile ? { width: '100%', maxHeight: '40vh', flexShrink: 0 } : undefined}
              />
            ) : null}

            {/* Right area: visualizer or result detail */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              {detailType === 'result-detail' && selectedResult ? (
                <ResultDetail
                  result={selectedResult}
                  project={projectsHook.activeProject}
                  toolInfo={toolInfo}
                  onRerun={handleRerun}
                />
              ) : (
                <>
                  {simulation.jobId && simulation.isDone && (
                    <div style={{
                      display: 'flex', justifyContent: 'flex-end', padding: '6px 12px',
                      borderBottom: `1px solid ${theme.colors.border}`,
                      background: theme.colors.bgSecondary,
                    }}>
                      <ExportButton
                        jobIds={simulation.jobId ? [simulation.jobId] : []}
                        title={selectedTool ? `${selectedTool.name} Results` : 'Results'}
                      />
                    </div>
                  )}
                  <VisualizerArea
                    tool={selectedTool}
                    result={simulation.result}
                    jobId={simulation.jobId}
                  />
                </>
              )}
            </div>
          </>
        )}
      </div>

      {/* Mobile bottom navigation */}
      {isMobile && (
        <MobileNav
          view={view}
          detailType={detailType}
          onNavigate={(target) => {
            if (target === 'dashboard') navigateToDashboard();
            else if (target === 'sweep') navigateToSweep();
            else if (target === 'docs') handleOpenDocs('tools', '');
          }}
        />
      )}

      <DocsPanel
        isOpen={docsOpen}
        onClose={() => setDocsOpen(false)}
        initialTab={docsFilter.tab}
        initialFilter={docsFilter.filter}
      />
    </div>
  );
}
