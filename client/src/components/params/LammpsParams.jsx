import React from 'react';
import { InputField, SliderParam, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function LammpsParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'lj_fluid';

  const subParams = p[simType] || {};
  const updateSub = (key, val) => {
    onChange({ ...p, [simType]: { ...subParams, [key]: val } });
  };

  return (
    <>
      <DropdownSelect
        label="Simulation Type"
        value={simType}
        onChange={(v) => onChange({ ...p, simulation_type: v })}
        options={[
          { value: 'lj_fluid', label: 'Lennard-Jones Fluid' },
          { value: 'eam_metal', label: 'EAM Metal' },
          { value: 'polymer_melt', label: 'Polymer Melt' },
          { value: 'custom_script', label: 'Custom Script' },
        ]}
      />

      {simType === 'lj_fluid' && (
        <>
          <SliderParam label="Atoms" value={subParams.n_atoms ?? 500} onChange={(v) => updateSub('n_atoms', v)} min={100} max={5000} step={100} />
          <InputField label="Temperature (LJ)" value={subParams.temperature ?? 1.0} onChange={(v) => updateSub('temperature', parseFloat(v))} type="number" step={0.1} />
          <InputField label="Density (LJ)" value={subParams.density ?? 0.8} onChange={(v) => updateSub('density', parseFloat(v))} type="number" step={0.1} />
          <InputField label="Timestep" value={subParams.timestep ?? 0.005} onChange={(v) => updateSub('timestep', parseFloat(v))} type="number" step={0.001} />
          <SliderParam label="Steps" value={subParams.n_steps ?? 10000} onChange={(v) => updateSub('n_steps', v)} min={1000} max={50000} step={1000} />
          <SliderParam label="Dump Interval" value={subParams.dump_interval ?? 100} onChange={(v) => updateSub('dump_interval', v)} min={10} max={1000} step={10} />
        </>
      )}

      {simType === 'eam_metal' && (
        <>
          <DropdownSelect label="Element" value={subParams.element || 'Cu'} onChange={(v) => updateSub('element', v)} options={['Cu', 'Al', 'Fe', 'Ni', 'Au']} />
          <DropdownSelect label="Lattice" value={subParams.lattice_type || 'fcc'} onChange={(v) => updateSub('lattice_type', v)} options={['fcc', 'bcc', 'hcp']} />
          <InputField label="Lattice Constant (Å)" value={subParams.lattice_constant ?? 3.615} onChange={(v) => updateSub('lattice_constant', parseFloat(v))} type="number" step={0.01} />
          <InputField label="Temperature (K)" value={subParams.temperature ?? 300} onChange={(v) => updateSub('temperature', parseFloat(v))} type="number" step={50} />
          <SliderParam label="Steps" value={subParams.n_steps ?? 10000} onChange={(v) => updateSub('n_steps', v)} min={1000} max={50000} step={1000} />
        </>
      )}

      {simType === 'polymer_melt' && (
        <>
          <SliderParam label="Chains" value={subParams.n_chains ?? 10} onChange={(v) => updateSub('n_chains', v)} min={1} max={50} step={1} />
          <SliderParam label="Chain Length" value={subParams.chain_length ?? 20} onChange={(v) => updateSub('chain_length', v)} min={5} max={100} step={5} />
          <InputField label="Temperature (LJ)" value={subParams.temperature ?? 1.0} onChange={(v) => updateSub('temperature', parseFloat(v))} type="number" step={0.1} />
          <SliderParam label="Steps" value={subParams.n_steps ?? 10000} onChange={(v) => updateSub('n_steps', v)} min={1000} max={50000} step={1000} />
        </>
      )}

      {simType === 'custom_script' && (
        <div style={{ marginTop: 8 }}>
          <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
            LAMMPS Input Script
          </label>
          <textarea
            value={p.lammps_script || ''}
            onChange={(e) => update('lammps_script', e.target.value)}
            placeholder="units lj&#10;atom_style atomic&#10;..."
            rows={8}
            style={{
              width: '100%',
              background: theme.colors.bgTertiary,
              border: `1px solid ${theme.colors.border}`,
              borderRadius: 4,
              color: theme.colors.text,
              padding: 8,
              fontSize: 11,
              fontFamily: theme.fonts.mono,
              resize: 'vertical',
            }}
          />
        </div>
      )}

    </>
  );
}
