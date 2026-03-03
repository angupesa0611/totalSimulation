import React, { useState, useEffect } from 'react';
import { getResult } from '../api/client';
import theme from '../theme.json';

/**
 * Side-by-side or overlay comparison of multiple simulation results.
 * Shows parameter diffs and overlays numeric data on Plotly traces.
 */
export default function ComparisonView({ jobIds }) {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState('table'); // 'table' or 'overlay'

  useEffect(() => {
    if (!jobIds || jobIds.length === 0) {
      setResults([]);
      return;
    }

    setLoading(true);
    Promise.all(jobIds.map(id => getResult(id).catch(() => null)))
      .then(data => setResults(data.filter(Boolean)))
      .finally(() => setLoading(false));
  }, [jobIds]);

  if (!jobIds || jobIds.length === 0) return null;

  // Flatten a result into dot-path key-value pairs for comparison
  const flatten = (obj, prefix = '') => {
    const out = {};
    for (const [k, v] of Object.entries(obj || {})) {
      const key = prefix ? `${prefix}.${k}` : k;
      if (v && typeof v === 'object' && !Array.isArray(v)) {
        Object.assign(out, flatten(v, key));
      } else if (typeof v === 'number' || typeof v === 'string' || typeof v === 'boolean') {
        out[key] = v;
      } else if (Array.isArray(v) && v.length <= 5) {
        out[key] = JSON.stringify(v);
      } else if (Array.isArray(v)) {
        out[key] = `[${v.length} items]`;
      }
    }
    return out;
  };

  // Get all unique keys across results
  const allFlat = results.map(r => flatten(r));
  const allKeys = [...new Set(allFlat.flatMap(f => Object.keys(f)))].sort();

  // Find keys where values differ
  const diffKeys = allKeys.filter(key => {
    const values = allFlat.map(f => f[key]);
    return new Set(values.map(v => JSON.stringify(v))).size > 1;
  });

  return (
    <div style={{
      background: theme.colors.bgSecondary,
      borderRadius: 8,
      border: `1px solid ${theme.colors.border}`,
      overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '8px 12px',
        borderBottom: `1px solid ${theme.colors.border}`,
      }}>
        <span style={{ fontSize: 12, fontWeight: 600, color: theme.colors.text }}>
          Comparison ({results.length} results)
        </span>
        <div style={{ display: 'flex', gap: 4 }}>
          {['table', 'overlay'].map(m => (
            <button
              key={m}
              onClick={() => setViewMode(m)}
              style={{
                padding: '3px 8px', fontSize: 10,
                background: viewMode === m ? theme.colors.accent : 'transparent',
                color: viewMode === m ? '#fff' : theme.colors.textSecondary,
                border: `1px solid ${viewMode === m ? theme.colors.accent : theme.colors.border}`,
                borderRadius: 3, cursor: 'pointer', textTransform: 'capitalize',
              }}
            >{m}</button>
          ))}
        </div>
      </div>

      {loading ? (
        <div style={{ padding: 20, textAlign: 'center', fontSize: 12, color: theme.colors.textSecondary }}>
          Loading results...
        </div>
      ) : (
        <div style={{ maxHeight: 400, overflow: 'auto', padding: 8 }}>
          {viewMode === 'table' ? (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={{
                    padding: '4px 8px', fontSize: 10, textAlign: 'left',
                    color: theme.colors.textSecondary,
                    borderBottom: `1px solid ${theme.colors.border}`,
                    position: 'sticky', top: 0,
                    background: theme.colors.bgSecondary,
                  }}>Field</th>
                  {results.map((_, i) => (
                    <th key={i} style={{
                      padding: '4px 8px', fontSize: 10, textAlign: 'left',
                      color: theme.colors.accent,
                      borderBottom: `1px solid ${theme.colors.border}`,
                      position: 'sticky', top: 0,
                      background: theme.colors.bgSecondary,
                    }}>Result {i + 1}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(diffKeys.length > 0 ? diffKeys : allKeys.slice(0, 50)).map(key => (
                  <tr key={key}>
                    <td style={{
                      padding: '3px 8px', fontSize: 10, fontFamily: 'monospace',
                      color: diffKeys.includes(key) ? '#f59e0b' : theme.colors.textSecondary,
                      borderBottom: `1px solid ${theme.colors.border}`,
                      whiteSpace: 'nowrap',
                    }}>{key}</td>
                    {allFlat.map((flat, i) => (
                      <td key={i} style={{
                        padding: '3px 8px', fontSize: 10,
                        color: theme.colors.text,
                        borderBottom: `1px solid ${theme.colors.border}`,
                        fontFamily: typeof flat[key] === 'number' ? 'monospace' : 'inherit',
                      }}>
                        {flat[key] !== undefined
                          ? typeof flat[key] === 'number'
                            ? Number(flat[key]).toPrecision(6)
                            : String(flat[key]).slice(0, 40)
                          : '—'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div style={{ padding: 12, fontSize: 11, color: theme.colors.textSecondary }}>
              {/* Overlay mode: show numeric arrays side by side */}
              {allKeys.filter(k => {
                return allFlat.some(f => {
                  const v = f[k];
                  return typeof v === 'number';
                });
              }).slice(0, 10).map(key => (
                <div key={key} style={{ marginBottom: 8 }}>
                  <div style={{ fontSize: 10, fontFamily: 'monospace', color: theme.colors.accent, marginBottom: 2 }}>
                    {key}
                  </div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    {allFlat.map((flat, i) => (
                      <span key={i} style={{
                        padding: '2px 6px',
                        background: theme.colors.bgTertiary,
                        borderRadius: 3,
                        fontSize: 11,
                        fontFamily: 'monospace',
                        color: ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444'][i % 4],
                      }}>
                        {flat[key] !== undefined ? Number(flat[key]).toPrecision(6) : '—'}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
              {diffKeys.length === 0 && (
                <div style={{ textAlign: 'center', color: theme.colors.textSecondary }}>
                  No numeric differences found between results
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
