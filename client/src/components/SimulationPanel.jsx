import React from 'react';
import { InputField, SliderParam, DropdownSelect, RunButton, ProgressBar } from './shared';
import HelpButton from './shared/HelpButton';
import { ReboundParams, PyscfParams, Psi4Params, GromacsParams, NamdParams, QmmmParams, MdanalysisParams, PybulletParams, EinsteinpyParams, NrpyParams, FenicsParams, ElmerParams, BasicoParams, TelluriumParams, Brian2Params, NestParams, MsprimeParams, RDKitParams, CanteraParams, QeParams, LammpsParams, SymPyParams, GmshParams, LcapyParams, PennyLaneParams, SagemathParams, Lean4Params, GapParams, PySpiceParams, QiskitParams, MatplotlibParams, ControlParams, PyomoParams, NetworkXParams, PhiFlowParams, ManimParams, OpenFOAMParams, DedalusParams, SU2Params, FiredrakeParams, VTKParams, OpenBabelParams, COMSOLParams, AlphaFoldParams, SLiMParams, TskitParams, SimuPOPParams, PyRosettaParams, EinsteinToolkitParams } from './params';
import theme from '../theme.json';

function QutipParams({ params, onChange }) {
  const p = params || {};
  const sysType = p.system_type || 'qubit_rabi';
  const subParams = p[sysType] || {};

  const updateSub = (key, val) => {
    onChange({ ...p, [sysType]: { ...subParams, [key]: val } });
  };

  return (
    <>
      <DropdownSelect
        label="System Type"
        value={sysType}
        onChange={(v) => onChange({ ...p, system_type: v })}
        options={[
          { value: 'qubit_rabi', label: 'Qubit Rabi Oscillation' },
          { value: 'spin_chain', label: 'Spin Chain' },
          { value: 'jaynes_cummings', label: 'Jaynes-Cummings' },
        ]}
      />
      {sysType === 'qubit_rabi' && (
        <>
          <InputField label="Rabi Frequency (omega)" value={subParams.omega ?? 1.0} onChange={(v) => updateSub('omega', v)} type="number" step={0.1} />
          <InputField label="Detuning (delta)" value={subParams.delta ?? 0.0} onChange={(v) => updateSub('delta', v)} type="number" step={0.1} />
          <DropdownSelect label="Initial State" value={subParams.psi0 || 'ground'} onChange={(v) => updateSub('psi0', v)} options={['ground', 'excited', 'superposition']} />
          <InputField label="Max Time" value={subParams.tmax ?? 25.0} onChange={(v) => updateSub('tmax', v)} type="number" step={1} />
        </>
      )}
      {sysType === 'spin_chain' && (
        <>
          <SliderParam label="Number of Spins" value={subParams.n_spins ?? 4} onChange={(v) => updateSub('n_spins', v)} min={2} max={10} step={1} />
          <InputField label="Coupling J" value={subParams.J ?? 1.0} onChange={(v) => updateSub('J', v)} type="number" step={0.1} />
          <InputField label="Field B" value={subParams.B ?? 0.5} onChange={(v) => updateSub('B', v)} type="number" step={0.1} />
          <InputField label="Max Time" value={subParams.tmax ?? 20.0} onChange={(v) => updateSub('tmax', v)} type="number" step={1} />
          <InputField
            label="Initial State (e.g. 0,1,1,0)"
            value={subParams.initial_state || ''}
            onChange={(v) => updateSub('initial_state', v)}
            placeholder="0=up, 1=down per spin (comma-sep)"
          />
        </>
      )}
      {sysType === 'jaynes_cummings' && (
        <>
          <SliderParam label="Photon Cutoff" value={subParams.n_photons ?? 5} onChange={(v) => updateSub('n_photons', v)} min={2} max={20} step={1} />
          <InputField label="Atom Frequency (omega_a)" value={subParams.omega_a ?? 1.0} onChange={(v) => updateSub('omega_a', v)} type="number" step={0.1} />
          <InputField label="Cavity Frequency (omega_c)" value={subParams.omega_c ?? 1.0} onChange={(v) => updateSub('omega_c', v)} type="number" step={0.1} />
          <InputField label="Coupling g" value={subParams.g ?? 0.1} onChange={(v) => updateSub('g', v)} type="number" step={0.01} />
          <InputField label="Cavity Decay (kappa)" value={subParams.kappa ?? 0.05} onChange={(v) => updateSub('kappa', v)} type="number" step={0.01} />
          <InputField label="Atom Decay (gamma)" value={subParams.gamma ?? 0.01} onChange={(v) => updateSub('gamma', v)} type="number" step={0.01} />
          <InputField label="Max Time" value={subParams.tmax ?? 50.0} onChange={(v) => updateSub('tmax', v)} type="number" step={5} />
          <SliderParam label="Steps" value={subParams.n_steps ?? 500} onChange={(v) => updateSub('n_steps', v)} min={100} max={2000} step={100} />
        </>
      )}
    </>
  );
}

function OpenmmParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const handlePdbFile = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => update('pdb_content', ev.target.result);
    reader.readAsText(file);
  };

  return (
    <>
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginBottom: 4 }}>PDB Structure</div>
        <label style={{
          display: 'block', padding: '8px 12px', background: theme.colors.accent,
          borderRadius: 6, color: '#fff', fontSize: 12, textAlign: 'center',
          cursor: 'pointer', marginBottom: 6,
        }}>
          Upload .pdb file
          <input type="file" accept=".pdb" onChange={handlePdbFile} style={{ display: 'none' }} />
        </label>
        <textarea
          value={p.pdb_content || ''}
          onChange={(e) => update('pdb_content', e.target.value)}
          placeholder="Or paste PDB content here..."
          rows={4}
          style={{
            width: '100%', padding: 6, background: theme.colors.bgTertiary,
            border: `1px solid ${theme.colors.border}`, borderRadius: 4,
            color: theme.colors.text, fontSize: 11, fontFamily: "'JetBrains Mono', monospace",
            resize: 'vertical',
          }}
        />
        <div style={{ fontSize: 11, color: p.pdb_content ? theme.colors.success : theme.colors.warning, marginTop: 4 }}>
          {p.pdb_content ? `PDB loaded (${p.pdb_content.split('\n').length} lines)` : 'No PDB loaded — upload or paste a structure'}
        </div>
      </div>
      <DropdownSelect
        label="Integrator"
        value={p.integrator || 'langevin'}
        onChange={(v) => update('integrator', v)}
        options={['langevin', 'verlet', 'brownian']}
      />
      <InputField label="Temperature (K)" value={p.temperature ?? 300} onChange={(v) => update('temperature', v)} type="number" step={10} />
      <InputField label="Timestep (ps)" value={p.dt ?? 0.002} onChange={(v) => update('dt', v)} type="number" step={0.001} />
      <SliderParam label="Steps" value={p.steps ?? 10000} onChange={(v) => update('steps', v)} min={1000} max={100000} step={1000} />
      <SliderParam label="Report Interval" value={p.report_interval ?? 100} onChange={(v) => update('report_interval', v)} min={10} max={1000} step={10} />
    </>
  );
}

const PARAM_COMPONENTS = {
  rebound: ReboundParams,
  qutip: QutipParams,
  openmm: OpenmmParams,
  pyscf: PyscfParams,
  mdanalysis: MdanalysisParams,
  psi4: Psi4Params,
  gromacs: GromacsParams,
  namd: NamdParams,
  qmmm: QmmmParams,
  pybullet: PybulletParams,
  einsteinpy: EinsteinpyParams,
  nrpy: NrpyParams,
  fenics: FenicsParams,
  elmer: ElmerParams,
  basico: BasicoParams,
  tellurium: TelluriumParams,
  brian2: Brian2Params,
  nest: NestParams,
  msprime: MsprimeParams,
  rdkit: RDKitParams,
  cantera: CanteraParams,
  qe: QeParams,
  lammps: LammpsParams,
  sympy: SymPyParams,
  gmsh: GmshParams,
  lcapy: LcapyParams,
  pennylane: PennyLaneParams,
  sagemath: SagemathParams,
  lean4: Lean4Params,
  gap: GapParams,
  pyspice: PySpiceParams,
  qiskit: QiskitParams,
  matplotlib: MatplotlibParams,
  control: ControlParams,
  pyomo: PyomoParams,
  networkx: NetworkXParams,
  phiflow: PhiFlowParams,
  manim: ManimParams,
  openfoam: OpenFOAMParams,
  dedalus: DedalusParams,
  su2: SU2Params,
  firedrake: FiredrakeParams,
  vtk: VTKParams,
  openbabel: OpenBabelParams,
  comsol: COMSOLParams,
  alphafold: AlphaFoldParams,
  slim: SLiMParams,
  tskit: TskitParams,
  simupop: SimuPOPParams,
  pyrosetta: PyRosettaParams,
  einstein_toolkit: EinsteinToolkitParams,
};

export default function SimulationPanel({ tool, params, onParamsChange, onRun, simulation, onOpenDocs, style }) {
  const ParamComponent = tool ? PARAM_COMPONENTS[tool.key] : null;

  if (!tool) {
    return (
      <div style={{
        width: 320,
        background: theme.colors.bgSecondary,
        borderRight: `1px solid ${theme.colors.border}`,
        padding: 24,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: theme.colors.textSecondary,
        fontSize: 14,
        flexShrink: 0,
        ...style,
      }}>
        Select a tool or preset to begin
      </div>
    );
  }

  return (
    <div style={{
      width: 320,
      background: theme.colors.bgSecondary,
      borderRight: `1px solid ${theme.colors.border}`,
      padding: 16,
      overflowY: 'auto',
      flexShrink: 0,
      ...style,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, margin: 0 }}>{tool.name}</h3>
        {onOpenDocs && (
          <HelpButton
            onClick={() => onOpenDocs('tools', tool.key)}
            title={`Documentation for ${tool.name}`}
          />
        )}
      </div>
      <p style={{ fontSize: 12, color: theme.colors.textSecondary, marginBottom: 16 }}>{tool.description}</p>

      {ParamComponent && (
        <ParamComponent params={params} onChange={onParamsChange} />
      )}

      <RunButton
        onClick={() => onRun({ tool: tool.key, params })}
        loading={simulation.isRunning}
        disabled={simulation.isRunning}
      />

      {simulation.isRunning && (
        <>
          <ProgressBar
            progress={simulation.progress}
            message={simulation.message}
            status={simulation.status}
          />
          <button
            onClick={() => simulation.cancel()}
            style={{
              marginTop: 8,
              width: '100%',
              padding: '6px 0',
              background: 'transparent',
              border: `1px solid ${theme.colors.warning}`,
              borderRadius: 6,
              color: theme.colors.warning,
              fontSize: 12,
              cursor: 'pointer',
            }}
          >
            Cancel
          </button>
        </>
      )}

      {simulation.isCancelled && (
        <div style={{ marginTop: 12, padding: 12, background: '#1a1a0a', borderRadius: 8, border: `1px solid ${theme.colors.warning}`, fontSize: 12, color: theme.colors.warning }}>
          Simulation cancelled
        </div>
      )}

      {simulation.isFailed && !simulation.isCancelled && (
        <div style={{ marginTop: 12, padding: 12, background: '#1a0a0a', borderRadius: 8, border: '1px solid #ef4444', fontSize: 12, color: '#ef4444' }}>
          {simulation.error || simulation.message || 'Simulation failed'}
        </div>
      )}

      {simulation.isDone && (
        <div style={{ marginTop: 12, padding: 12, background: '#0a1a0a', borderRadius: 8, border: '1px solid #22c55e', fontSize: 12, color: '#22c55e' }}>
          Simulation complete
        </div>
      )}
    </div>
  );
}
