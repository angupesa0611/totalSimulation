import React from 'react';
import { InputField, SliderParam, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function FenicsParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const material = p.material || {};
  const updateMat = (key, val) => update('material', { ...material, [key]: val });

  const problemType = p.problem_type || 'heat';

  return (
    <>
      <DropdownSelect
        label="Problem Type"
        value={problemType}
        onChange={(v) => update('problem_type', v)}
        options={[
          { value: 'heat', label: 'Heat Conduction (Poisson)' },
          { value: 'diffusion', label: 'Diffusion' },
          { value: 'elasticity', label: 'Linear Elasticity' },
          { value: 'stokes', label: 'Stokes Flow' },
        ]}
      />

      <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
        Domain
      </div>
      <div style={{ display: 'flex', gap: 4 }}>
        <InputField label="Length X" value={p.length_x ?? 1.0} onChange={(v) => update('length_x', parseFloat(v))} type="number" step={0.1} />
        <InputField label="Length Y" value={p.length_y ?? 1.0} onChange={(v) => update('length_y', parseFloat(v))} type="number" step={0.1} />
      </div>

      <SliderParam label="Mesh Resolution" value={p.mesh_resolution ?? 32} onChange={(v) => update('mesh_resolution', v)} min={8} max={128} step={8} />
      <DropdownSelect label="Degree" value={p.degree ?? 1} onChange={(v) => update('degree', parseInt(v))} options={[1, 2, 3]} />

      <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
        Material Properties
      </div>

      {problemType === 'heat' || problemType === 'diffusion' ? (
        <>
          <InputField label="Conductivity" value={material.conductivity ?? 1.0} onChange={(v) => updateMat('conductivity', parseFloat(v))} type="number" step={0.1} />
          <InputField label="Source Term" value={p.source_term ?? 0.0} onChange={(v) => update('source_term', parseFloat(v))} type="number" step={0.1} />
        </>
      ) : problemType === 'elasticity' ? (
        <>
          <InputField label="Young's Modulus (E)" value={material.E ?? 1e5} onChange={(v) => updateMat('E', parseFloat(v))} type="number" step={1000} />
          <InputField label="Poisson Ratio (ν)" value={material.nu ?? 0.3} onChange={(v) => updateMat('nu', parseFloat(v))} type="number" step={0.01} />
          <InputField label="Density" value={material.density ?? 1.0} onChange={(v) => updateMat('density', parseFloat(v))} type="number" step={0.1} />
        </>
      ) : null}

      <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
        Boundary Conditions
      </div>
      <textarea
        value={p._bc_json || JSON.stringify(p.boundary_conditions || [
          { type: 'dirichlet', boundary: 'left', value: 100 },
          { type: 'dirichlet', boundary: 'right', value: 0 },
        ], null, 2)}
        onChange={(e) => {
          update('_bc_json', e.target.value);
          try {
            const parsed = JSON.parse(e.target.value);
            if (Array.isArray(parsed)) update('boundary_conditions', parsed);
          } catch { /* invalid JSON, keep raw text */ }
        }}
        rows={5}
        style={{
          width: '100%', background: theme.colors.bgTertiary,
          border: `1px solid ${theme.colors.border}`, borderRadius: 6,
          color: theme.colors.text, fontFamily: theme.fonts.mono,
          fontSize: 11, padding: 8, resize: 'vertical',
        }}
      />
    </>
  );
}
