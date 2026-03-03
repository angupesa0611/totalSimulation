import React, { useCallback } from 'react';
import theme from '../../theme.json';

function FileUpload({ label, accept, value, onChange }) {
  const handleFile = useCallback((e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => onChange(ev.target.result);
    reader.readAsText(file);
  }, [onChange]);

  return (
    <div style={{ marginBottom: 12 }}>
      <label style={{ display: 'block', fontSize: 12, color: theme.colors.textSecondary, marginBottom: 4 }}>
        {label}
      </label>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
      }}>
        <label style={{
          padding: '6px 12px',
          background: theme.colors.bgTertiary,
          border: `1px solid ${theme.colors.border}`,
          borderRadius: 6,
          color: theme.colors.text,
          fontSize: 12,
          cursor: 'pointer',
        }}>
          Choose File
          <input type="file" accept={accept} onChange={handleFile} style={{ display: 'none' }} />
        </label>
        <span style={{ fontSize: 11, color: value ? theme.colors.success : theme.colors.textSecondary }}>
          {value ? `${value.split('\n').length} lines loaded` : 'No file'}
        </span>
      </div>
    </div>
  );
}

export default function GromacsParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  return (
    <>
      <FileUpload
        label="Coordinate File (.gro)"
        accept=".gro"
        value={p.gro_content}
        onChange={(v) => update('gro_content', v)}
      />

      <FileUpload
        label="Topology File (.top)"
        accept=".top,.itp"
        value={p.top_content}
        onChange={(v) => update('top_content', v)}
      />

      <FileUpload
        label="Run Parameters (.mdp)"
        accept=".mdp"
        value={p.mdp_content}
        onChange={(v) => update('mdp_content', v)}
      />

      <div style={{
        fontSize: 11,
        color: theme.colors.textSecondary,
        marginTop: 8,
        padding: 10,
        background: theme.colors.bgTertiary,
        borderRadius: 6,
        lineHeight: 1.5,
      }}>
        Upload GROMACS input files. The .gro file provides coordinates,
        .top defines the topology, and .mdp sets simulation parameters.
      </div>
    </>
  );
}
