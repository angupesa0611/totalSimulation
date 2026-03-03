import React, { useState } from 'react';

const ACCENT = '#fb923c';

export default function OptimizationView({ data }) {
  const [tab, setTab] = useState('solution');

  if (!data) {
    return <div style={{ color: '#8888a0', padding: 24 }}>No data to display</div>;
  }

  const tabs = ['solution', 'constraints', 'summary'];

  const statusColor = data.status === 'optimal' ? '#22c55e' :
    data.status === 'infeasible' ? '#ef4444' : '#f59e0b';

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{
        display: 'flex', gap: 2, padding: '8px 16px',
        background: '#12121a', borderBottom: '1px solid #2a2a3a',
      }}>
        {tabs.map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              padding: '4px 12px', background: tab === t ? ACCENT : 'transparent',
              border: 'none', borderRadius: 4,
              color: tab === t ? '#fff' : '#8888a0',
              fontSize: 11, cursor: 'pointer', textTransform: 'capitalize',
            }}
          >{t}</button>
        ))}
      </div>

      {tab === 'solution' && data.variable_values && (
        <div style={{ flex: 1, padding: 24, overflow: 'auto' }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20,
          }}>
            <span style={{
              padding: '4px 12px', borderRadius: 4, fontSize: 12, fontWeight: 600,
              background: `${statusColor}18`, color: statusColor, border: `1px solid ${statusColor}33`,
            }}>{data.status?.toUpperCase()}</span>
            {data.optimal_value !== null && (
              <span style={{ color: '#e0e0e0', fontSize: 14 }}>
                Optimal Value: <strong style={{ color: ACCENT }}>{data.optimal_value?.toFixed(4)}</strong>
              </span>
            )}
          </div>

          <table style={{
            width: '100%', borderCollapse: 'collapse', fontSize: 13,
            fontFamily: "'JetBrains Mono', monospace",
          }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left', padding: '8px 12px', borderBottom: '1px solid #2a2a3a', color: ACCENT }}>Variable</th>
                <th style={{ textAlign: 'right', padding: '8px 12px', borderBottom: '1px solid #2a2a3a', color: ACCENT }}>Value</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.variable_values).map(([name, value]) => (
                <tr key={name}>
                  <td style={{ padding: '8px 12px', borderBottom: '1px solid #1a1a28', color: '#e0e0e0' }}>{name}</td>
                  <td style={{ padding: '8px 12px', borderBottom: '1px solid #1a1a28', color: '#e0e0e0', textAlign: 'right' }}>
                    {value !== null ? value.toFixed(4) : 'N/A'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'constraints' && (
        <div style={{ flex: 1, padding: 24, overflow: 'auto' }}>
          {data.constraint_slacks && Object.keys(data.constraint_slacks).length > 0 ? (
            <table style={{
              width: '100%', borderCollapse: 'collapse', fontSize: 13,
              fontFamily: "'JetBrains Mono', monospace",
            }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left', padding: '8px 12px', borderBottom: '1px solid #2a2a3a', color: ACCENT }}>Constraint</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px', borderBottom: '1px solid #2a2a3a', color: ACCENT }}>Slack</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(data.constraint_slacks).map(([name, slack]) => (
                  <tr key={name}>
                    <td style={{ padding: '8px 12px', borderBottom: '1px solid #1a1a28', color: '#e0e0e0' }}>{name}</td>
                    <td style={{ padding: '8px 12px', borderBottom: '1px solid #1a1a28', color: '#e0e0e0', textAlign: 'right' }}>
                      {slack !== null ? slack.toFixed(4) : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div style={{ color: '#8888a0' }}>No constraint slack data available</div>
          )}
        </div>
      )}

      {tab === 'summary' && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace" }}>
          <h4 style={{ color: ACCENT, marginBottom: 12 }}>Optimization Summary</h4>
          <div>Tool: {data.tool}</div>
          <div>Type: {data.simulation_type}</div>
          <div>Status: <span style={{ color: statusColor }}>{data.status}</span></div>
          <div>Solver: {data.solver}</div>
          {data.optimal_value !== null && <div>Optimal Value: {data.optimal_value?.toFixed(6)}</div>}
          {data.solver_time_s !== undefined && <div>Solver Time: {data.solver_time_s?.toFixed(4)} s</div>}
          {data.variable_values && <div>Variables: {Object.keys(data.variable_values).length}</div>}
        </div>
      )}
    </div>
  );
}
