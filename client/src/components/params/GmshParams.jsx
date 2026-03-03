import React from 'react';
import { InputField, DropdownSelect, SliderParam } from '../shared';
import theme from '../../theme.json';

export default function GmshParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'box_mesh';

  return (
    <>
      <DropdownSelect
        label="Geometry Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'box_mesh', label: 'Box Mesh' },
          { value: 'cylinder_mesh', label: 'Cylinder Mesh' },
          { value: 'sphere_mesh', label: 'Sphere Mesh' },
          { value: 'custom_geo', label: 'Custom .geo Script' },
        ]}
      />

      {simType === 'box_mesh' && (
        <>
          <InputField label="Length X" value={p.lx ?? 1.0} onChange={(v) => update('lx', parseFloat(v) || 1.0)} type="number" step={0.1} />
          <InputField label="Length Y" value={p.ly ?? 0.5} onChange={(v) => update('ly', parseFloat(v) || 0.5)} type="number" step={0.1} />
          <InputField label="Length Z" value={p.lz ?? 0.2} onChange={(v) => update('lz', parseFloat(v) || 0)} type="number" step={0.1} />
        </>
      )}

      {simType === 'cylinder_mesh' && (
        <>
          <InputField label="Radius" value={p.radius ?? 0.5} onChange={(v) => update('radius', parseFloat(v) || 0.5)} type="number" step={0.1} />
          <InputField label="Length" value={p.length ?? 2.0} onChange={(v) => update('length', parseFloat(v) || 2.0)} type="number" step={0.1} />
        </>
      )}

      {simType === 'sphere_mesh' && (
        <InputField label="Radius" value={p.radius ?? 1.0} onChange={(v) => update('radius', parseFloat(v) || 1.0)} type="number" step={0.1} />
      )}

      {simType === 'custom_geo' && (
        <div style={{ marginTop: 8 }}>
          <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
            Gmsh .geo Script
          </label>
          <textarea
            value={p.geo_script || ''}
            onChange={(e) => update('geo_script', e.target.value)}
            placeholder="Point(1) = {0, 0, 0, 0.1};&#10;..."
            rows={6}
            style={{
              width: '100%', background: theme.colors.bgTertiary,
              border: `1px solid ${theme.colors.border}`, borderRadius: 4,
              color: theme.colors.text, padding: 8, fontSize: 12,
              fontFamily: theme.fonts.mono, resize: 'vertical',
            }}
          />
        </div>
      )}

      <InputField
        label="Mesh Size"
        value={p.mesh_size ?? 0.1}
        onChange={(v) => update('mesh_size', parseFloat(v) || 0.1)}
        type="number"
        step={0.01}
      />

      <DropdownSelect
        label="Dimension"
        value={String(p.dimension ?? 3)}
        onChange={(v) => update('dimension', parseInt(v))}
        options={[
          { value: '2', label: '2D' },
          { value: '3', label: '3D' },
        ]}
      />

      <DropdownSelect
        label="Element Order"
        value={String(p.element_order ?? 1)}
        onChange={(v) => update('element_order', parseInt(v))}
        options={[
          { value: '1', label: 'Linear (P1)' },
          { value: '2', label: 'Quadratic (P2)' },
        ]}
      />

      <div style={{ fontSize: 11, color: '#a78bfa', marginTop: 8, padding: 8, background: '#a78bfa11', borderRadius: 4, border: '1px solid #a78bfa33' }}>
        Exports .msh mesh file for FEniCS pipeline coupling (Gmsh → FEniCS).
      </div>
    </>
  );
}
