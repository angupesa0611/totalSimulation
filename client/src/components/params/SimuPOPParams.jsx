import React from 'react';
import { InputField, SliderParam, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function SimuPOPParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'random_mating';

  return (
    <>
      <DropdownSelect
        label="Simulation Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'random_mating', label: 'Random Mating' },
          { value: 'migration', label: 'Island Migration' },
          { value: 'selection_drift', label: 'Selection + Drift' },
        ]}
      />

      <InputField label="Population Size" value={p.population_size ?? 1000} onChange={(v) => update('population_size', parseInt(v))} type="number" step={100} />
      <SliderParam label="Generations" value={p.n_generations ?? 200} onChange={(v) => update('n_generations', v)} min={10} max={5000} step={10} />
      <SliderParam label="Loci" value={p.n_loci ?? 1} onChange={(v) => update('n_loci', v)} min={1} max={20} step={1} />
      <InputField label="Initial Frequency" value={p.initial_freq ?? 0.5} onChange={(v) => update('initial_freq', parseFloat(v))} type="number" step={0.05} min={0} max={1} />

      {simType === 'migration' && (
        <>
          <SliderParam label="Populations" value={p.n_populations ?? 3} onChange={(v) => update('n_populations', v)} min={2} max={10} step={1} />
          <InputField label="Migration Rate" value={p.migration_rate ?? 0.01} onChange={(v) => update('migration_rate', parseFloat(v))} type="number" step={0.005} />
        </>
      )}

      {simType === 'selection_drift' && (
        <>
          <InputField label="Fitness AA" value={(p.fitness || {}).AA ?? 1.0} onChange={(v) => update('fitness', { ...(p.fitness || {}), AA: parseFloat(v) })} type="number" step={0.01} />
          <InputField label="Fitness Aa" value={(p.fitness || {}).Aa ?? 1.0} onChange={(v) => update('fitness', { ...(p.fitness || {}), Aa: parseFloat(v) })} type="number" step={0.01} />
          <InputField label="Fitness aa" value={(p.fitness || {}).aa ?? 0.9} onChange={(v) => update('fitness', { ...(p.fitness || {}), aa: parseFloat(v) })} type="number" step={0.01} />
        </>
      )}

      <div style={{ fontSize: 11, color: '#84cc16', marginTop: 8, padding: 8, background: '#84cc1611', borderRadius: 4, border: '1px solid #84cc1633' }}>
        Forward-time individual-based population genetics. Tracks allele frequency trajectories with configurable mating, migration, and selection schemes.
      </div>
    </>
  );
}
