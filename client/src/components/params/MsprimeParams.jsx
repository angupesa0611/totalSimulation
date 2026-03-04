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

      {simType === 'demographic_model' && (
        <div style={{ marginTop: 8 }}>
          <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
            Demographic Events (JSON)
          </label>
          <textarea
            value={typeof p.demographic_events === 'string' ? p.demographic_events : JSON.stringify(p.demographic_events || [
              { "type": "size_change", "time": 1000, "size": 500 },
              { "type": "recovery", "time": 2000, "size": 10000, "recovery_time": 500 }
            ], null, 2)}
            onChange={(e) => { try { update('demographic_events', JSON.parse(e.target.value)); } catch { update('demographic_events', e.target.value); } }}
            rows={6}
            style={{
              width: '100%', padding: 8, background: theme.colors.bgTertiary,
              border: `1px solid ${theme.colors.border}`, borderRadius: 6,
              color: theme.colors.text, fontFamily: "'JetBrains Mono', monospace", fontSize: 11, resize: 'vertical',
            }}
          />
        </div>
      )}

      <div style={{ fontSize: 11, color: '#84cc16', marginTop: 8, padding: 8, background: '#84cc1611', borderRadius: 4, border: '1px solid #84cc1633' }}>
        Backward-time coalescent simulation. Computes SFS, diversity (pi), and Tajima&apos;s D across genomic windows.
      </div>
    </>
  );
}
