import React from 'react';
import { InputField, SliderParam, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function TelluriumParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'antimony_timecourse';

  return (
    <>
      <DropdownSelect
        label="Simulation Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'antimony_timecourse', label: 'Antimony Timecourse' },
          { value: 'sbml_timecourse', label: 'SBML Timecourse' },
          { value: 'steady_state', label: 'Steady State' },
          { value: 'parameter_scan', label: 'Parameter Scan' },
          { value: 'metabolic_control', label: 'Metabolic Control Analysis' },
        ]}
      />

      {simType !== 'sbml_timecourse' && (
        <>
          <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
            Antimony Model
          </div>
          <textarea
            value={p.antimony_model || 'model pathway\n  S1 -> S2; k1*S1;\n  S2 -> S3; k2*S2;\n  S3 -> ; k3*S3;\n  S1 = 10; S2 = 0; S3 = 0;\n  k1 = 0.1; k2 = 0.05; k3 = 0.02;\nend'}
            onChange={(e) => update('antimony_model', e.target.value)}
            style={{
              width: '100%', height: 120, padding: 8,
              background: theme.colors.bgTertiary, color: theme.colors.text,
              border: `1px solid ${theme.colors.border}`, borderRadius: 6,
              fontFamily: theme.fonts.mono, fontSize: 11, resize: 'vertical',
            }}
          />
        </>
      )}

      {simType === 'sbml_timecourse' && (
        <>
          <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
            SBML Model (XML)
          </div>
          <textarea
            value={p.sbml_model || ''}
            onChange={(e) => update('sbml_model', e.target.value)}
            placeholder="Paste SBML XML here..."
            style={{
              width: '100%', height: 120, padding: 8,
              background: theme.colors.bgTertiary, color: theme.colors.text,
              border: `1px solid ${theme.colors.border}`, borderRadius: 6,
              fontFamily: theme.fonts.mono, fontSize: 11, resize: 'vertical',
            }}
          />
        </>
      )}

      {(simType === 'antimony_timecourse' || simType === 'sbml_timecourse') && (
        <>
          <InputField label="Start Time" value={p.start_time ?? 0} onChange={(v) => update('start_time', parseFloat(v))} type="number" step={1} />
          <InputField label="End Time" value={p.end_time ?? 100} onChange={(v) => update('end_time', parseFloat(v))} type="number" step={10} />
          <SliderParam label="Points" value={p.n_points ?? 200} onChange={(v) => update('n_points', v)} min={50} max={1000} step={50} />
        </>
      )}

      {simType === 'parameter_scan' && (
        <>
          <InputField label="Scan Parameter" value={p.scan_parameter || ''} onChange={(v) => update('scan_parameter', v)} placeholder="e.g. k1" />
          <div style={{ display: 'flex', gap: 4 }}>
            <InputField label="Range Min" value={p.scan_range?.[0] ?? 0.01} onChange={(v) => update('scan_range', [parseFloat(v), p.scan_range?.[1] ?? 1.0])} type="number" step={0.01} />
            <InputField label="Range Max" value={p.scan_range?.[1] ?? 1.0} onChange={(v) => update('scan_range', [p.scan_range?.[0] ?? 0.01, parseFloat(v)])} type="number" step={0.1} />
          </div>
          <SliderParam label="Scan Points" value={p.scan_points ?? 20} onChange={(v) => update('scan_points', v)} min={5} max={100} step={5} />
        </>
      )}

      <div style={{ fontSize: 11, color: '#10b981', marginTop: 8, padding: 8, background: '#10b98111', borderRadius: 4, border: '1px solid #10b98133' }}>
        Exports SBML automatically for pipeline coupling to BasiCO.
      </div>
    </>
  );
}
