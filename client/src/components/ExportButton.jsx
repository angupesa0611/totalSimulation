import React, { useState } from 'react';
import { submitExport, downloadExport } from '../api/client';
import theme from '../theme.json';

const formats = [
  { key: 'csv', label: 'CSV', icon: ',' },
  { key: 'json', label: 'JSON', icon: '{}' },
  { key: 'latex', label: 'LaTeX', icon: 'Tx' },
  { key: 'pdf', label: 'PDF', icon: 'Pd' },
];

export default function ExportButton({ jobIds, title }) {
  const [open, setOpen] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState(null);

  if (!jobIds || jobIds.length === 0) return null;

  const handleExport = async (format) => {
    setExporting(true);
    setError(null);
    try {
      const response = await submitExport({
        job_ids: jobIds,
        format,
        title: title || 'Simulation Results',
      });
      downloadExport(response.export_id);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setExporting(false);
      setOpen(false);
    }
  };

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <button
        onClick={() => setOpen(!open)}
        disabled={exporting}
        style={{
          padding: '6px 12px',
          fontSize: 11,
          background: theme.colors.bgTertiary,
          color: theme.colors.text,
          border: `1px solid ${theme.colors.border}`,
          borderRadius: 4,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: 6,
        }}
      >
        {exporting ? 'Exporting...' : 'Export'}
        <span style={{ fontSize: 9 }}>{open ? '\u25B2' : '\u25BC'}</span>
      </button>

      {open && (
        <div style={{
          position: 'absolute',
          top: '100%',
          right: 0,
          marginTop: 4,
          background: theme.colors.bgSecondary,
          border: `1px solid ${theme.colors.border}`,
          borderRadius: 6,
          boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
          zIndex: 100,
          minWidth: 140,
          overflow: 'hidden',
        }}>
          {formats.map(f => (
            <button
              key={f.key}
              onClick={() => handleExport(f.key)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                width: '100%',
                padding: '8px 12px',
                background: 'transparent',
                color: theme.colors.text,
                border: 'none',
                borderBottom: `1px solid ${theme.colors.border}`,
                cursor: 'pointer',
                fontSize: 12,
                textAlign: 'left',
              }}
              onMouseEnter={e => e.target.style.background = theme.colors.bgTertiary}
              onMouseLeave={e => e.target.style.background = 'transparent'}
            >
              <span style={{
                fontSize: 9,
                fontWeight: 700,
                color: theme.colors.accent,
                fontFamily: 'monospace',
                width: 20,
                textAlign: 'center',
              }}>{f.icon}</span>
              {f.label}
            </button>
          ))}
        </div>
      )}

      {error && (
        <div style={{
          position: 'absolute',
          top: '100%',
          right: 0,
          marginTop: 4,
          padding: '6px 10px',
          background: '#ef444420',
          border: '1px solid #ef444440',
          borderRadius: 4,
          fontSize: 10,
          color: '#ef4444',
          whiteSpace: 'nowrap',
        }}>
          {typeof error === 'string' ? error : 'Export failed'}
        </div>
      )}
    </div>
  );
}
