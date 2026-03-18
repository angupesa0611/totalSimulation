import React from 'react';
import ThreeScene from './ThreeScene';
import PlotlyChart from './PlotlyChart';
import MolStarViewer from './MolStarViewer';
import ElectronicPlot from './ElectronicPlot';
import SAPTChart from './SAPTChart';
import AnalysisPlot from './AnalysisPlot';
import RigidBodyScene from './RigidBodyScene';
import FieldPlot from './FieldPlot';
import GeodesicPlot from './GeodesicPlot';
import SystemsBioPlot from './SystemsBioPlot';
import NeuralPlot from './NeuralPlot';
import EvolutionPlot from './EvolutionPlot';
import ChemPlot from './ChemPlot';
import KineticsPlot from './KineticsPlot';
import MaterialsPlot from './MaterialsPlot';
import SymbolicPlot from './SymbolicPlot';
import ProofView from './ProofView';
import MeshView from './MeshView';
import CircuitPlot from './CircuitPlot';
import QuantumCircuitPlot from './QuantumCircuitPlot';
import ImageView from './ImageView';
import VideoPlayer from './VideoPlayer';
import ControlPlot from './ControlPlot';
import OptimizationView from './OptimizationView';
import GraphView from './GraphView';
import RenderAnimationButton from '../components/RenderAnimationButton';
import theme from '../theme.json';

const visualizers = {
  rebound: ThreeScene,
  qutip: PlotlyChart,
  openmm: MolStarViewer,
  gromacs: MolStarViewer,
  namd: MolStarViewer,
  qmmm: MolStarViewer,
  pyscf: ElectronicPlot,
  psi4: SAPTChart,
  mdanalysis: AnalysisPlot,
  pybullet: RigidBodyScene,
  einsteinpy: GeodesicPlot,
  nrpy: GeodesicPlot,
  fenics: FieldPlot,
  elmer: FieldPlot,
  basico: SystemsBioPlot,
  tellurium: SystemsBioPlot,
  brian2: NeuralPlot,
  nest: NeuralPlot,
  msprime: EvolutionPlot,
  rdkit: ChemPlot,
  cantera: KineticsPlot,
  qe: MaterialsPlot,
  lammps: MaterialsPlot,
  sympy: SymbolicPlot,
  sagemath: SymbolicPlot,
  gmsh: MeshView,
  lean4: ProofView,
  gap: ProofView,
  lcapy: CircuitPlot,
  pyspice: CircuitPlot,
  qiskit: QuantumCircuitPlot,
  pennylane: QuantumCircuitPlot,
  matplotlib: ImageView,
  manim: VideoPlayer,
  control: ControlPlot,
  pyomo: OptimizationView,
  networkx: GraphView,
  phiflow: FieldPlot,
  openfoam: FieldPlot,
  dedalus: FieldPlot,
  su2: FieldPlot,
  firedrake: FieldPlot,
  vtk: ImageView,
  openbabel: ChemPlot,
  comsol: FieldPlot,
  alphafold: MolStarViewer,
  slim: EvolutionPlot,
  tskit: EvolutionPlot,
  simupop: EvolutionPlot,
  pyrosetta: MolStarViewer,
  einstein_toolkit: GeodesicPlot,
  rayoptics: PlotlyChart,
  lightpipes: FieldPlot,
  strawberryfields: PlotlyChart,
  meep: FieldPlot,
};

export default function VisualizerArea({ tool, result, jobId }) {
  if (!tool) {
    return (
      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'column',
        gap: 16,
        color: theme.colors.textSecondary,
      }}>
        <div style={{ fontSize: 48, opacity: 0.3 }}>~</div>
        <div style={{ fontSize: 16 }}>totalSimulation</div>
        <div style={{ fontSize: 13 }}>Select a tool from the sidebar to begin</div>
      </div>
    );
  }

  if (!result) {
    return (
      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: theme.colors.textSecondary,
        fontSize: 14,
      }}>
        Configure parameters and run a simulation to see results
      </div>
    );
  }

  const Component = visualizers[tool.key];
  if (!Component) {
    return <div style={{ color: theme.colors.textSecondary, padding: 24 }}>No visualizer for {tool.name}</div>;
  }

  return (
    <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
      <Component data={result} />
      {result && <RenderAnimationButton toolKey={tool.key} jobId={jobId} />}
    </div>
  );
}
