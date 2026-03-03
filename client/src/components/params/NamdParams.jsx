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
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
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

export default function NamdParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  return (
    <>
      <FileUpload
        label="PDB File (.pdb)"
        accept=".pdb"
        value={p.pdb_content}
        onChange={(v) => update('pdb_content', v)}
      />

      <FileUpload
        label="PSF File (.psf)"
        accept=".psf"
        value={p.psf_content}
        onChange={(v) => update('psf_content', v)}
      />

      <div style={{ marginBottom: 12 }}>
        <label style={{ display: 'block', fontSize: 12, color: theme.colors.textSecondary, marginBottom: 4 }}>
          NAMD Configuration
        </label>
        <textarea
          value={p.namd_conf || ''}
          onChange={(e) => update('namd_conf', e.target.value)}
          placeholder="# NAMD config\nstructure input.psf\ncoordinates input.pdb\n..."
          rows={6}
          style={{
            width: '100%',
            background: theme.colors.bgTertiary,
            border: `1px solid ${theme.colors.border}`,
            borderRadius: 6,
            color: theme.colors.text,
            fontFamily: theme.fonts.mono,
            fontSize: 11,
            padding: 8,
            resize: 'vertical',
          }}
        />
      </div>

      <div style={{
        fontSize: 11,
        color: theme.colors.textSecondary,
        marginTop: 8,
        padding: 10,
        background: theme.colors.bgTertiary,
        borderRadius: 6,
        lineHeight: 1.5,
      }}>
        Upload PDB (coordinates) and PSF (structure) files,
        then provide the NAMD configuration.
      </div>
    </>
  );
}
