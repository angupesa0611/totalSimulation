import React from 'react';
import { InputField, SliderParam, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function ElmerParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const material = p.material || {};
  const updateMat = (key, val) => update('material', { ...material, [key]: val });

  const problemType = p.problem_type || 'structural';

  return (
    <>
      <DropdownSelect
        label="Problem Type"
        value={problemType}
        onChange={(v) => update('problem_type', v)}
        options={[
          { value: 'structural', label: 'Structural (Elasticity)' },
          { value: 'thermal', label: 'Thermal (Heat Conduction)' },
          { value: 'thermal_structural', label: 'Thermal-Structural (Coupled)' },
        ]}
      />

      <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
        Geometry
      </div>
      <div style={{ display: 'flex', gap: 4 }}>
        <InputField label="Length X" value={p.length_x ?? 1.0} onChange={(v) => update('length_x', parseFloat(v))} type="number" step={0.1} />
        <InputField label="Length Y" value={p.length_y ?? 0.1} onChange={(v) => update('length_y', parseFloat(v))} type="number" step={0.01} />
      </div>
      <div style={{ display: 'flex', gap: 4 }}>
        <SliderParam label="Mesh X" value={p.mesh_divisions_x ?? 20} onChange={(v) => update('mesh_divisions_x', v)} min={5} max={100} step={5} />
        <SliderParam label="Mesh Y" value={p.mesh_divisions_y ?? 10} onChange={(v) => update('mesh_divisions_y', v)} min={5} max={50} step={5} />
      </div>

      <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
        Material Properties
      </div>

      {(problemType === 'structural' || problemType === 'thermal_structural') && (
        <>
          <InputField label="Young's Modulus (Pa)" value={material.youngs_modulus ?? 2e11} onChange={(v) => updateMat('youngs_modulus', parseFloat(v))} type="number" step={1e9} />
          <InputField label="Poisson Ratio" value={material.poisson_ratio ?? 0.3} onChange={(v) => updateMat('poisson_ratio', parseFloat(v))} type="number" step={0.01} />
        </>
      )}

      {(problemType === 'thermal' || problemType === 'thermal_structural') && (
        <InputField label="Conductivity (W/m·K)" value={material.conductivity ?? 50.0} onChange={(v) => updateMat('conductivity', parseFloat(v))} type="number" step={1} />
      )}

      {problemType === 'thermal_structural' && (
        <InputField label="Thermal Expansion (1/K)" value={material.expansion_coeff ?? 1.2e-5} onChange={(v) => updateMat('expansion_coeff', parseFloat(v))} type="number" step={1e-6} />
      )}

      <InputField label="Density (kg/m³)" value={material.density ?? 7800} onChange={(v) => updateMat('density', parseFloat(v))} type="number" step={100} />

      {problemType === 'thermal_structural' && (
        <div style={{ fontSize: 11, color: '#14b8a6', marginTop: 8, padding: 8, background: '#14b8a611', borderRadius: 4, border: '1px solid #14b8a633' }}>
          Coupled analysis: solves heat equation first, then uses the temperature field as thermal load for structural deformation. Use in a pipeline with FEniCS for cross-solver coupling.
        </div>
      )}
    </>
  );
}
