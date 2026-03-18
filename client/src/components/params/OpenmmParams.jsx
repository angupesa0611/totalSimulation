import React from 'react';
import { InputField, SliderParam, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function OpenmmParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const handlePdbFile = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => update('pdb_content', ev.target.result);
    reader.readAsText(file);
  };

  return (
    <>
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginBottom: 4 }}>PDB Structure</div>
        <label style={{
          display: 'block', padding: '8px 12px', background: theme.colors.accent,
          borderRadius: 6, color: '#fff', fontSize: 12, textAlign: 'center',
          cursor: 'pointer', marginBottom: 6,
        }}>
          Upload .pdb file
          <input type="file" accept=".pdb" onChange={handlePdbFile} style={{ display: 'none' }} />
        </label>
        <textarea
          value={p.pdb_content || ''}
          onChange={(e) => update('pdb_content', e.target.value)}
          placeholder="Or paste PDB content here..."
          rows={4}
          style={{
            width: '100%', padding: 6, background: theme.colors.bgTertiary,
            border: `1px solid ${theme.colors.border}`, borderRadius: 4,
            color: theme.colors.text, fontSize: 11, fontFamily: "'JetBrains Mono', monospace",
            resize: 'vertical',
          }}
        />
        <div style={{ fontSize: 11, color: p.pdb_content ? theme.colors.success : theme.colors.warning, marginTop: 4 }}>
          {p.pdb_content ? `PDB loaded (${p.pdb_content.split('\n').length} lines)` : 'No PDB loaded \u2014 upload or paste a structure'}
        </div>
      </div>
      <DropdownSelect
        label="Integrator"
        value={p.integrator || 'langevin'}
        onChange={(v) => update('integrator', v)}
        options={['langevin', 'verlet', 'brownian']}
      />
      <InputField label="Temperature (K)" value={p.temperature ?? 300} onChange={(v) => update('temperature', v)} type="number" step={10} />
      <InputField label="Timestep (ps)" value={p.dt ?? 0.002} onChange={(v) => update('dt', v)} type="number" step={0.001} />
      <SliderParam label="Steps" value={p.steps ?? 10000} onChange={(v) => update('steps', v)} min={1000} max={100000} step={1000} />
      <SliderParam label="Report Interval" value={p.report_interval ?? 100} onChange={(v) => update('report_interval', v)} min={10} max={1000} step={10} />
    </>
  );
}
