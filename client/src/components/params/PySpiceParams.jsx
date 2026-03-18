import React, { useState, useEffect } from 'react';
import { InputField, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function PySpiceParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });
  const [compText, setCompText] = useState(JSON.stringify(p.components || [], null, 1));

  useEffect(() => {
    setCompText(JSON.stringify(p.components || [], null, 1));
  }, [JSON.stringify(p.components)]);

  const simType = p.simulation_type || 'dc_operating_point';

  return (
    <>
      <DropdownSelect
        label="Analysis Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'dc_operating_point', label: 'DC Operating Point' },
          { value: 'ac_analysis', label: 'AC Analysis' },
          { value: 'transient_analysis', label: 'Transient Analysis' },
        ]}
      />

      <div style={{ marginTop: 8 }}>
        <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
          Components (JSON [{'{'}type, name, nodes, value{'}'}])
        </label>
        <textarea
          value={compText}
          onChange={(e) => {
            setCompText(e.target.value);
            try { update('components', JSON.parse(e.target.value)); } catch {}
          }}
          rows={6}
          style={{
            width: '100%', background: theme.colors.bgTertiary,
            border: `1px solid ${theme.colors.border}`, borderRadius: 4,
            color: theme.colors.text, padding: 8, fontSize: 11,
            fontFamily: theme.fonts.mono, resize: 'vertical',
          }}
        />
      </div>

      {simType === 'ac_analysis' && (
        <>
          <InputField
            label="Start Frequency (Hz)"
            value={p.f_start ?? 1}
            onChange={(v) => update('f_start', parseFloat(v) || 1)}
            type="number"
          />
          <InputField
            label="Stop Frequency (Hz)"
            value={p.f_stop ?? 1e6}
            onChange={(v) => update('f_stop', parseFloat(v) || 1e6)}
            type="number"
          />
          <InputField
            label="Points"
            value={p.n_points ?? 100}
            onChange={(v) => update('n_points', parseInt(v) || 100)}
            type="number"
          />
        </>
      )}

      {simType === 'transient_analysis' && (
        <>
          <InputField
            label="Step Time (s)"
            value={p.step_time ?? 1e-6}
            onChange={(v) => update('step_time', parseFloat(v) || 1e-6)}
            type="number"
            step={1e-7}
          />
          <InputField
            label="End Time (s)"
            value={p.end_time ?? 0.005}
            onChange={(v) => update('end_time', parseFloat(v) || 0.005)}
            type="number"
            step={0.001}
          />
        </>
      )}

    </>
  );
}
