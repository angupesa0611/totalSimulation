import React from 'react';
import { InputField, SliderParam, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function MsprimeParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'coalescent';

  return (
    <>
      <DropdownSelect
        label="Simulation Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'coalescent', label: 'Neutral Coalescent' },
          { value: 'demographic_model', label: 'Demographic Model' },
          { value: 'selective_sweep', label: 'Selective Sweep' },
          { value: 'recombination', label: 'Recombination Hotspots' },
        ]}
      />

      <SliderParam label="Samples" value={p.n_samples ?? 50} onChange={(v) => update('n_samples', v)} min={2} max={500} step={10} />
      <InputField label="Sequence Length (bp)" value={p.sequence_length ?? 100000} onChange={(v) => update('sequence_length', parseInt(v))} type="number" step={10000} />
      <InputField label="Mutation Rate" value={p.mutation_rate ?? 1e-8} onChange={(v) => update('mutation_rate', parseFloat(v))} type="number" step={1e-9} />
      <InputField label="Recombination Rate" value={p.recombination_rate ?? 1e-8} onChange={(v) => update('recombination_rate', parseFloat(v))} type="number" step={1e-9} />
      <InputField label="Population Size (Ne)" value={p.population_size ?? 10000} onChange={(v) => update('population_size', parseInt(v))} type="number" step={1000} />
      <InputField label="Random Seed" value={p.random_seed ?? 42} onChange={(v) => update('random_seed', parseInt(v))} type="number" step={1} />
      <SliderParam label="Windows" value={p.n_windows ?? 20} onChange={(v) => update('n_windows', v)} min={5} max={100} step={5} />

      {simType === 'selective_sweep' && (
        <>
          <InputField label="Selection Coefficient" value={p.selection_coefficient ?? 0.01} onChange={(v) => update('selection_coefficient', parseFloat(v))} type="number" step={0.001} />
          <InputField label="Sweep Position (bp)" value={p.sweep_position ?? 50000} onChange={(v) => update('sweep_position', parseInt(v))} type="number" step={1000} />
        </>
      )}

      <div style={{ fontSize: 11, color: '#84cc16', marginTop: 8, padding: 8, background: '#84cc1611', borderRadius: 4, border: '1px solid #84cc1633' }}>
        Backward-time coalescent simulation. Computes SFS, diversity (pi), and Tajima&apos;s D across genomic windows.
      </div>
    </>
  );
}
