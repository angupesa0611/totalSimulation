import React from 'react';
import { InputField, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function VTKParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'field_render';

  const textareaStyle = {
    width: '100%', background: theme.colors.bgTertiary,
    border: `1px solid ${theme.colors.border}`, borderRadius: 4,
    color: theme.colors.text, padding: 8, fontSize: 12,
    fontFamily: theme.fonts.mono, resize: 'vertical',
  };

  return (
    <>
      <DropdownSelect
        label="Visualization Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'field_render', label: 'Field Render (2D heatmap)' },
          { value: 'isosurface', label: 'Isosurface (3D contour)' },
          { value: 'streamlines', label: 'Streamlines (vector field)' },
          { value: 'volume_render', label: 'Volume Render (3D)' },
        ]}
      />

      <DropdownSelect
        label="Colormap"
        value={p.colormap || 'viridis'}
        onChange={(v) => update('colormap', v)}
        options={[
          { value: 'viridis', label: 'Viridis' },
          { value: 'plasma', label: 'Plasma' },
          { value: 'inferno', label: 'Inferno' },
          { value: 'coolwarm', label: 'Cool-Warm' },
          { value: 'jet', label: 'Jet' },
          { value: 'hot', label: 'Hot' },
        ]}
      />

      <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
        Window Size
      </div>
      <div style={{ display: 'flex', gap: 4 }}>
        <InputField
          label="Width"
          value={p.window_width ?? 800}
          onChange={(v) => update('window_size', [parseInt(v) || 800, (p.window_size || [800, 600])[1]])}
          type="number"
          step={100}
        />
        <InputField
          label="Height"
          value={p.window_height ?? 600}
          onChange={(v) => update('window_size', [(p.window_size || [800, 600])[0], parseInt(v) || 600])}
          type="number"
          step={100}
        />
      </div>

      {simType === 'isosurface' && (
        <div style={{ marginTop: 8 }}>
          <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
            Iso-values (JSON array)
          </label>
          <textarea
            value={JSON.stringify(p.iso_values || [0.25, 0.5, 0.75], null, 1)}
            onChange={(e) => { try { update('iso_values', JSON.parse(e.target.value)); } catch {} }}
            rows={2}
            style={textareaStyle}
          />
        </div>
      )}

      {simType === 'streamlines' && (
        <div style={{ marginTop: 8 }}>
          <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
            Seed Points (JSON [[x,y], ...], empty for auto)
          </label>
          <textarea
            value={JSON.stringify(p.seed_points || [], null, 1)}
            onChange={(e) => { try { update('seed_points', JSON.parse(e.target.value)); } catch {} }}
            rows={2}
            style={textareaStyle}
          />
        </div>
      )}

      <div style={{ marginTop: 8 }}>
        <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
          Field Data (JSON 2D/3D array, or use tool coupling)
        </label>
        <textarea
          value={typeof p.field_data === 'string' ? p.field_data : (p.field_data ? 'Loaded from coupling' : 'No data')}
          onChange={(e) => { try { update('field_data', JSON.parse(e.target.value)); } catch {} }}
          rows={3}
          style={textareaStyle}
          placeholder="Use a coupling (FEniCS → VTK, PhiFlow → VTK) to populate"
        />
      </div>

      <div style={{ fontSize: 11, color: '#818cf8', marginTop: 8, padding: 8, background: '#818cf811', borderRadius: 4, border: '1px solid #818cf833' }}>
        Server-side rendering via OSMesa. Chain from FEniCS/OpenFOAM/PhiFlow/Dedalus for field data.
      </div>
    </>
  );
}
