import React from 'react';
import { InputField, SliderParam, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function FiredrakeParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const problemType = p.problem_type || 'poisson';

  const textareaStyle = {
    width: '100%', background: theme.colors.bgTertiary,
    border: `1px solid ${theme.colors.border}`, borderRadius: 4,
    color: theme.colors.text, padding: 8, fontSize: 12,
    fontFamily: theme.fonts.mono, resize: 'vertical',
  };

  return (
    <>
      <DropdownSelect
        label="Problem Type"
        value={problemType}
        onChange={(v) => update('problem_type', v)}
        options={[
          { value: 'poisson', label: 'Poisson (Heat)' },
          { value: 'stokes', label: 'Stokes Flow' },
          { value: 'elasticity', label: 'Elasticity' },
          { value: 'advection_diffusion', label: 'Advection-Diffusion' },
        ]}
      />

      <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
        Domain
      </div>
      <div style={{ display: 'flex', gap: 4 }}>
        <InputField
          label="Length X"
          value={p.length_x ?? 1.0}
          onChange={(v) => update('length_x', parseFloat(v) || 1.0)}
          type="number"
          step={0.1}
        />
        <InputField
          label="Length Y"
          value={p.length_y ?? 1.0}
          onChange={(v) => update('length_y', parseFloat(v) || 1.0)}
          type="number"
          step={0.1}
        />
      </div>

      <SliderParam
        label="Mesh Resolution"
        value={p.mesh_resolution ?? 32}
        onChange={(v) => update('mesh_resolution', v)}
        min={8}
        max={128}
        step={8}
      />

      <SliderParam
        label="Polynomial Degree"
        value={p.degree ?? 1}
        onChange={(v) => update('degree', v)}
        min={1}
        max={3}
        step={1}
      />

      {(problemType === 'poisson' || problemType === 'advection_diffusion') && (
        <>
          <InputField
            label={problemType === 'advection_diffusion' ? 'Diffusivity' : 'Conductivity'}
            value={problemType === 'advection_diffusion' ? (p.diffusivity ?? 0.01) : (p.material?.conductivity ?? 1.0)}
            onChange={(v) => {
              if (problemType === 'advection_diffusion') {
                update('diffusivity', parseFloat(v) || 0.01);
              } else {
                update('material', { ...(p.material || {}), conductivity: parseFloat(v) || 1.0 });
              }
            }}
            type="number"
            step={0.1}
          />
          {problemType === 'poisson' && (
            <InputField
              label="Source Term"
              value={p.source_term ?? 1.0}
              onChange={(v) => update('source_term', parseFloat(v))}
              type="number"
              step={0.1}
            />
          )}
        </>
      )}

      {problemType === 'elasticity' && (
        <>
          <InputField
            label="Young's Modulus (E)"
            value={p.material?.E ?? 100000}
            onChange={(v) => update('material', { ...(p.material || {}), E: parseFloat(v) || 1e5 })}
            type="number"
          />
          <InputField
            label="Poisson Ratio (v)"
            value={p.material?.nu ?? 0.3}
            onChange={(v) => update('material', { ...(p.material || {}), nu: parseFloat(v) || 0.3 })}
            type="number"
            step={0.05}
          />
        </>
      )}

      <div style={{ marginTop: 8 }}>
        <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
          Boundary Conditions (JSON)
        </label>
        <textarea
          value={JSON.stringify(p.boundary_conditions || [
            { type: 'dirichlet', boundary: 'left', value: 100 },
            { type: 'dirichlet', boundary: 'right', value: 0 },
          ], null, 2)}
          onChange={(e) => { try { update('boundary_conditions', JSON.parse(e.target.value)); } catch {} }}
          rows={4}
          style={textareaStyle}
        />
      </div>

      <div style={{ fontSize: 11, color: '#14b8a6', marginTop: 8, padding: 8, background: '#14b8a611', borderRadius: 4, border: '1px solid #14b8a633' }}>
        Requires <code>continuum</code> Docker profile. Uses Firedrake FEM with PETSc backend.
      </div>
    </>
  );
}
