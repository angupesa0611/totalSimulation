import React from 'react';
import { InputField, SliderParam, DropdownSelect } from '../shared';

export default function QutipParams({ params, onChange }) {
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
