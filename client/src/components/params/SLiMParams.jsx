import React from 'react';
import { InputField, SliderParam, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function SLiMParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'neutral_evolution';

  return (
    <>
      <DropdownSelect
        label="Simulation Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'neutral_evolution', label: 'Neutral Evolution' },
          { value: 'selection', label: 'Selection' },
          { value: 'nucleotide_evolution', label: 'Nucleotide Evolution' },
          { value: 'spatial', label: 'Spatial (2D)' },
        ]}
      />

      <InputField label="Population Size" value={p.population_size ?? 500} onChange={(v) => update('population_size', parseInt(v))} type="number" step={100} />
      <SliderParam label="Generations" value={p.n_generations ?? 1000} onChange={(v) => update('n_generations', v)} min={100} max={10000} step={100} />
      <InputField label="Mutation Rate" value={p.mutation_rate ?? 1e-7} onChange={(v) => update('mutation_rate', parseFloat(v))} type="number" step={1e-8} />
      <InputField label="Recombination Rate" value={p.recombination_rate ?? 1e-8} onChange={(v) => update('recombination_rate', parseFloat(v))} type="number" step={1e-9} />
      <InputField label="Sequence Length (bp)" value={p.sequence_length ?? 100000} onChange={(v) => update('sequence_length', parseInt(v))} type="number" step={10000} />
      <SliderParam label="Samples (for stats)" value={p.n_samples ?? 50} onChange={(v) => update('n_samples', v)} min={10} max={200} step={10} />

      {simType === 'selection' && (
        <InputField label="Selection Coefficient" value={p.selection_coefficient ?? 0.01} onChange={(v) => update('selection_coefficient', parseFloat(v))} type="number" step={0.001} />
      )}

      <div style={{ fontSize: 11, color: '#84cc16', marginTop: 8, padding: 8, background: '#84cc1611', borderRadius: 4, border: '1px solid #84cc1633' }}>
        Forward-time Wright-Fisher simulation via SLiM (Eidos scripting). Records tree sequences for tskit-compatible analysis.
      </div>
    </>
  );
}
