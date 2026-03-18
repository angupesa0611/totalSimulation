import React from 'react';
import { InputField, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function QeParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'scf';
  const kPoints = p.k_points || [4, 4, 4];

  const updateKPoint = (idx, val) => {
    const newK = [...kPoints];
    newK[idx] = parseInt(val) || 1;
    update('k_points', newK);
  };

  return (
    <>
      <DropdownSelect
        label="Calculation"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'scf', label: 'SCF (Self-Consistent Field)' },
          { value: 'bands', label: 'Band Structure' },
          { value: 'dos', label: 'Density of States' },
          { value: 'relax', label: 'Geometry Optimization' },
        ]}
      />

      <div style={{ marginTop: 8 }}>
        <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
          Crystal Structure (JSON)
        </label>
        <textarea
          value={typeof p.structure === 'object' ? JSON.stringify(p.structure, null, 2) : (p.structure || '')}
          onChange={(e) => {
            try {
              const parsed = JSON.parse(e.target.value);
              update('structure', parsed);
            } catch {
              // Keep raw text while user is editing
              update('structure', e.target.value);
            }
          }}
          placeholder='{"cell": [[0,2.715,2.715],[2.715,0,2.715],[2.715,2.715,0]], "positions": [{"symbol": "Si", "coords": [0,0,0]}], "is_fractional": true}'
          rows={6}
          style={{
            width: '100%',
            background: theme.colors.bgTertiary,
            border: `1px solid ${theme.colors.border}`,
            borderRadius: 4,
            color: theme.colors.text,
            padding: 8,
            fontSize: 11,
            fontFamily: theme.fonts.mono,
            resize: 'vertical',
          }}
        />
      </div>

      <InputField
        label="Wavefunction Cutoff (Ry)"
        value={p.ecutwfc ?? 30}
        onChange={(v) => update('ecutwfc', parseFloat(v))}
        type="number"
        step={5}
      />

      <InputField
        label="Charge Density Cutoff (Ry)"
        value={p.ecutrho ?? 240}
        onChange={(v) => update('ecutrho', parseFloat(v))}
        type="number"
        step={10}
      />

      <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
        K-Points Grid
      </div>
      <div style={{ display: 'flex', gap: 4 }}>
        <InputField label="kx" value={kPoints[0]} onChange={(v) => updateKPoint(0, v)} type="number" step={1} />
        <InputField label="ky" value={kPoints[1]} onChange={(v) => updateKPoint(1, v)} type="number" step={1} />
        <InputField label="kz" value={kPoints[2]} onChange={(v) => updateKPoint(2, v)} type="number" step={1} />
      </div>

    </>
  );
}
