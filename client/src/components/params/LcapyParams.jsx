import React from 'react';
import { InputField, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function LcapyParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'dc_analysis';

  return (
    <>
      <DropdownSelect
        label="Analysis Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'dc_analysis', label: 'DC Analysis' },
          { value: 'ac_analysis', label: 'AC Analysis' },
          { value: 'transfer_function', label: 'Transfer Function' },
          { value: 'transient', label: 'Transient' },
        ]}
      />

      <div style={{ marginTop: 8 }}>
        <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
          Netlist (SPICE format)
        </label>
        <textarea
          value={p.netlist || ''}
          onChange={(e) => update('netlist', e.target.value)}
          placeholder="V1 1 0; R1 1 2 1k; C1 2 0 1u"
          rows={4}
          style={{
            width: '100%', background: theme.colors.bgTertiary,
            border: `1px solid ${theme.colors.border}`, borderRadius: 4,
            color: theme.colors.text, padding: 8, fontSize: 12,
            fontFamily: theme.fonts.mono, resize: 'vertical',
          }}
        />
      </div>

      {(simType === 'ac_analysis' || simType === 'transfer_function') && (
        <>
          <InputField
            label="Input Node"
            value={p.input_node || '1'}
            onChange={(v) => update('input_node', v)}
          />
          <InputField
            label="Output Node"
            value={p.output_node || '2'}
            onChange={(v) => update('output_node', v)}
          />
        </>
      )}

      {simType === 'ac_analysis' && (
        <>
          <InputField
            label="Min Frequency (Hz)"
            value={p.frequency_range?.[0] ?? 1}
            onChange={(v) => update('frequency_range', [parseFloat(v) || 1, p.frequency_range?.[1] ?? 1e6])}
            type="number"
          />
          <InputField
            label="Max Frequency (Hz)"
            value={p.frequency_range?.[1] ?? 1e6}
            onChange={(v) => update('frequency_range', [p.frequency_range?.[0] ?? 1, parseFloat(v) || 1e6])}
            type="number"
          />
        </>
      )}

      {simType === 'transient' && (
        <>
          <InputField
            label="Max Time (s)"
            value={p.t_max ?? 0.01}
            onChange={(v) => update('t_max', parseFloat(v) || 0.01)}
            type="number"
            step={0.001}
          />
          <InputField
            label="Points"
            value={p.n_points ?? 200}
            onChange={(v) => update('n_points', parseInt(v) || 200)}
            type="number"
          />
        </>
      )}

      <div style={{ fontSize: 11, color: '#2dd4bf', marginTop: 8, padding: 8, background: '#2dd4bf11', borderRadius: 4, border: '1px solid #2dd4bf33' }}>
        Exports SPICE netlist for PySpice pipeline coupling (Lcapy → PySpice).
      </div>
    </>
  );
}
