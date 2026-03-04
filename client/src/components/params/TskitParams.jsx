import React from 'react';
import { InputField, SliderParam, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function TskitParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'diversity';

  return (
    <>
      <DropdownSelect
        label="Analysis Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'tree_analysis', label: 'Tree Analysis' },
          { value: 'diversity', label: 'Diversity (pi + Tajima\'s D)' },
          { value: 'fst', label: 'Fst (Population Differentiation)' },
          { value: 'recapitate', label: 'Recapitate (pyslim)' },
        ]}
      />

      <InputField label="Source Job ID" value={p.source_job_id ?? ''} onChange={(v) => update('source_job_id', v)} type="text" placeholder="Enter a previous SLiM/msprime job ID" />
      <SliderParam label="Windows" value={p.n_windows ?? 20} onChange={(v) => update('n_windows', v)} min={5} max={100} step={5} />

      {simType === 'fst' && (
        <div style={{ marginTop: 8 }}>
          <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
            Sample Sets (JSON array of arrays, e.g. [[0,1,2],[3,4,5]])
          </label>
          <textarea
            value={typeof p.sample_sets === 'string' ? p.sample_sets : JSON.stringify(p.sample_sets || [[0,1,2,3,4],[5,6,7,8,9]], null, 1)}
            onChange={(e) => { try { update('sample_sets', JSON.parse(e.target.value)); } catch { update('sample_sets', e.target.value); } }}
            rows={3}
            style={{
              width: '100%', padding: 8, background: theme.colors.bgTertiary,
              border: `1px solid ${theme.colors.border}`, borderRadius: 6,
              color: theme.colors.text, fontFamily: "'JetBrains Mono', monospace", fontSize: 11, resize: 'vertical',
            }}
          />
        </div>
      )}

      {simType === 'recapitate' && (
        <>
          <InputField label="Ancestral Ne" value={p.population_size ?? 10000} onChange={(v) => update('population_size', parseInt(v))} type="number" step={1000} />
          <InputField label="Recombination Rate" value={p.recombination_rate ?? 1e-8} onChange={(v) => update('recombination_rate', parseFloat(v))} type="number" step={1e-9} />
          <InputField label="Mutation Rate" value={p.mutation_rate ?? 1e-8} onChange={(v) => update('mutation_rate', parseFloat(v))} type="number" step={1e-9} />
        </>
      )}

      <div style={{ fontSize: 11, color: '#84cc16', marginTop: 8, padding: 8, background: '#84cc1611', borderRadius: 4, border: '1px solid #84cc1633' }}>
        Post-hoc analysis of tree sequences from SLiM or msprime. Computes diversity, Fst, and SFS across genomic windows. Recapitate adds coalescent history to SLiM output.
      </div>
    </>
  );
}
