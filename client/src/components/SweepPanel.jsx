import React, { useState, useEffect } from 'react';
import { useSweep } from '../hooks/useSweep';
import { getLayers } from '../api/client';
import theme from '../theme.json';

const defaultAxis = () => ({
  param: '',
  mode: 'values', // 'values' or 'range'
  valuesStr: '',
  rangeMin: 0,
  rangeMax: 1,
  rangeSteps: 5,
  log_scale: false,
});

export default function SweepPanel() {
  const sweep = useSweep();
  const [tools, setTools] = useState([]);
  const [selectedTool, setSelectedTool] = useState('');
  const [method, setMethod] = useState('grid');
  const [nSamples, setNSamples] = useState(10);
  const [axes, setAxes] = useState([defaultAxis()]);
  const [label, setLabel] = useState('');

  useEffect(() => {
    getLayers().then(layers => {
      const allTools = layers.flatMap(l => l.tools || []);
      setTools(allTools);
    }).catch(() => {});
  }, []);

  const updateAxis = (index, field, value) => {
    setAxes(prev => prev.map((ax, i) =>
      i === index ? { ...ax, [field]: value } : ax
    ));
  };

  const addAxis = () => {
    if (axes.length < 3) setAxes(prev => [...prev, defaultAxis()]);
  };

  const removeAxis = (index) => {
    setAxes(prev => prev.filter((_, i) => i !== index));
  };

  const handleRun = () => {
    const sweepAxes = axes.map(ax => {
      const axis = { param: ax.param };
      if (ax.mode === 'values') {
        try {
          axis.values = JSON.parse(`[${ax.valuesStr}]`);
        } catch { axis.values = []; }
      } else {
        axis.range = { min: Number(ax.rangeMin), max: Number(ax.rangeMax), steps: Number(ax.rangeSteps) };
        axis.log_scale = ax.log_scale;
      }
      return axis;
    });

    sweep.run({
      tool: selectedTool,
      base_params: {},
      axes: sweepAxes,
      method,
      n_samples: method !== 'grid' ? nSamples : undefined,
      label: label || undefined,
    });
  };

  const cellStyle = {
    padding: '4px 8px',
    fontSize: 11,
    borderBottom: `1px solid ${theme.colors.border}`,
    color: theme.colors.text,
  };

  return (
    <div style={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
    }}>
      <div style={{
        padding: '12px 16px',
        borderBottom: `1px solid ${theme.colors.border}`,
      }}>
        <h3 style={{ margin: 0, fontSize: 14, color: theme.colors.text }}>Parameter Sweep</h3>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
        {/* Tool selector */}
        <label style={{ fontSize: 11, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
          Tool
        </label>
        <select
          value={selectedTool}
          onChange={e => setSelectedTool(e.target.value)}
          style={{
            width: '100%', padding: '6px 8px', fontSize: 12,
            background: theme.colors.bgTertiary, color: theme.colors.text,
            border: `1px solid ${theme.colors.border}`, borderRadius: 4,
            marginBottom: 12,
          }}
        >
          <option value="">Select tool...</option>
          {tools.map(t => (
            <option key={t.key} value={t.key}>{t.name}</option>
          ))}
        </select>

        {/* Method selector */}
        <label style={{ fontSize: 11, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
          Sampling Method
        </label>
        <div style={{ display: 'flex', gap: 4, marginBottom: 12 }}>
          {['grid', 'random', 'lhs'].map(m => (
            <button
              key={m}
              onClick={() => setMethod(m)}
              style={{
                flex: 1, padding: '4px 8px', fontSize: 11,
                background: method === m ? theme.colors.accent : theme.colors.bgTertiary,
                color: method === m ? '#fff' : theme.colors.textSecondary,
                border: `1px solid ${method === m ? theme.colors.accent : theme.colors.border}`,
                borderRadius: 4, cursor: 'pointer', textTransform: 'uppercase',
              }}
            >
              {m === 'lhs' ? 'LHS' : m}
            </button>
          ))}
        </div>

        {method !== 'grid' && (
          <div style={{ marginBottom: 12 }}>
            <label style={{ fontSize: 11, color: theme.colors.textSecondary }}>Samples</label>
            <input
              type="number" value={nSamples} min={1} max={100}
              onChange={e => setNSamples(parseInt(e.target.value) || 10)}
              style={{
                width: '100%', padding: '4px 8px', fontSize: 12,
                background: theme.colors.bgTertiary, color: theme.colors.text,
                border: `1px solid ${theme.colors.border}`, borderRadius: 4,
              }}
            />
          </div>
        )}

        {/* Axes */}
        <div style={{ marginBottom: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <label style={{ fontSize: 11, color: theme.colors.textSecondary }}>Sweep Axes</label>
            {axes.length < 3 && (
              <button onClick={addAxis} style={{
                fontSize: 10, padding: '2px 8px', background: theme.colors.bgTertiary,
                color: theme.colors.accent, border: `1px solid ${theme.colors.border}`,
                borderRadius: 4, cursor: 'pointer',
              }}>+ Axis</button>
            )}
          </div>

          {axes.map((ax, i) => (
            <div key={i} style={{
              background: theme.colors.bgTertiary, borderRadius: 6, padding: 10,
              marginBottom: 8, border: `1px solid ${theme.colors.border}`,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <span style={{ fontSize: 11, color: theme.colors.accent }}>Axis {i + 1}</span>
                {axes.length > 1 && (
                  <button onClick={() => removeAxis(i)} style={{
                    fontSize: 10, padding: '1px 6px', background: 'transparent',
                    color: '#ef4444', border: 'none', cursor: 'pointer',
                  }}>Remove</button>
                )}
              </div>

              <input
                placeholder="Parameter path (e.g. dt, integrator.dt)"
                value={ax.param}
                onChange={e => updateAxis(i, 'param', e.target.value)}
                style={{
                  width: '100%', padding: '4px 8px', fontSize: 11,
                  background: theme.colors.bg, color: theme.colors.text,
                  border: `1px solid ${theme.colors.border}`, borderRadius: 4,
                  marginBottom: 6, boxSizing: 'border-box',
                }}
              />

              <div style={{ display: 'flex', gap: 4, marginBottom: 6 }}>
                {['values', 'range'].map(m => (
                  <button
                    key={m}
                    onClick={() => updateAxis(i, 'mode', m)}
                    style={{
                      flex: 1, padding: '3px', fontSize: 10,
                      background: ax.mode === m ? theme.colors.accent : 'transparent',
                      color: ax.mode === m ? '#fff' : theme.colors.textSecondary,
                      border: `1px solid ${ax.mode === m ? theme.colors.accent : theme.colors.border}`,
                      borderRadius: 3, cursor: 'pointer', textTransform: 'capitalize',
                    }}
                  >{m}</button>
                ))}
              </div>

              {ax.mode === 'values' ? (
                <input
                  placeholder="0.1, 0.5, 1.0, 2.0"
                  value={ax.valuesStr}
                  onChange={e => updateAxis(i, 'valuesStr', e.target.value)}
                  style={{
                    width: '100%', padding: '4px 8px', fontSize: 11,
                    background: theme.colors.bg, color: theme.colors.text,
                    border: `1px solid ${theme.colors.border}`, borderRadius: 4,
                    boxSizing: 'border-box',
                  }}
                />
              ) : (
                <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                  {[['Min', 'rangeMin'], ['Max', 'rangeMax'], ['Steps', 'rangeSteps']].map(([lbl, key]) => (
                    <div key={key} style={{ flex: 1, minWidth: 60 }}>
                      <label style={{ fontSize: 9, color: theme.colors.textSecondary }}>{lbl}</label>
                      <input
                        type="number" value={ax[key]}
                        onChange={e => updateAxis(i, key, e.target.value)}
                        style={{
                          width: '100%', padding: '3px 6px', fontSize: 11,
                          background: theme.colors.bg, color: theme.colors.text,
                          border: `1px solid ${theme.colors.border}`, borderRadius: 3,
                          boxSizing: 'border-box',
                        }}
                      />
                    </div>
                  ))}
                  <label style={{ fontSize: 10, color: theme.colors.textSecondary, display: 'flex', alignItems: 'center', gap: 4, marginTop: 4 }}>
                    <input type="checkbox" checked={ax.log_scale} onChange={e => updateAxis(i, 'log_scale', e.target.checked)} />
                    Log scale
                  </label>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Label */}
        <input
          placeholder="Label (optional)"
          value={label}
          onChange={e => setLabel(e.target.value)}
          style={{
            width: '100%', padding: '4px 8px', fontSize: 12,
            background: theme.colors.bgTertiary, color: theme.colors.text,
            border: `1px solid ${theme.colors.border}`, borderRadius: 4,
            marginBottom: 12, boxSizing: 'border-box',
          }}
        />

        {/* Run button */}
        <button
          onClick={handleRun}
          disabled={!selectedTool || axes.every(a => !a.param) || sweep.isRunning}
          style={{
            width: '100%', padding: '8px', fontSize: 13, fontWeight: 600,
            background: sweep.isRunning ? theme.colors.bgTertiary : theme.colors.accent,
            color: '#fff', border: 'none', borderRadius: 6,
            cursor: sweep.isRunning ? 'default' : 'pointer',
            opacity: (!selectedTool || sweep.isRunning) ? 0.5 : 1,
          }}
        >
          {sweep.isRunning ? 'Running Sweep...' : 'Run Sweep'}
        </button>

        {sweep.error && (
          <div style={{ marginTop: 8, padding: 8, background: '#ef444420', borderRadius: 4, fontSize: 11, color: '#ef4444' }}>
            {typeof sweep.error === 'string' ? sweep.error : JSON.stringify(sweep.error)}
          </div>
        )}

        {/* Progress */}
        {sweep.sweepId && (
          <div style={{ marginTop: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: theme.colors.textSecondary, marginBottom: 4 }}>
              <span>Progress</span>
              <span>{sweep.completedRuns}/{sweep.totalRuns} complete{sweep.failedRuns > 0 ? `, ${sweep.failedRuns} failed` : ''}</span>
            </div>
            <div style={{ height: 6, background: theme.colors.bgTertiary, borderRadius: 3, overflow: 'hidden' }}>
              <div style={{
                height: '100%', borderRadius: 3,
                width: `${sweep.progress * 100}%`,
                background: sweep.failedRuns > 0 ? '#f59e0b' : theme.colors.accent,
                transition: 'width 0.3s ease',
              }} />
            </div>

            {/* Run status badges */}
            {sweep.status && (
              <div style={{
                marginTop: 8, padding: 6,
                background: theme.colors.bgTertiary, borderRadius: 4,
                fontSize: 10, color: theme.colors.textSecondary,
              }}>
                Status: <span style={{
                  color: sweep.status === 'SUCCESS' ? '#22c55e' :
                         sweep.status === 'PARTIAL' ? '#f59e0b' :
                         sweep.status === 'FAILURE' ? '#ef4444' : theme.colors.accent,
                  fontWeight: 600,
                }}>{sweep.status}</span>
              </div>
            )}

            {/* Results table */}
            {sweep.isDone && sweep.runs.length > 0 && (
              <div style={{ marginTop: 12, overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 10 }}>
                  <thead>
                    <tr>
                      <th style={cellStyle}>#</th>
                      <th style={cellStyle}>Status</th>
                      <th style={cellStyle}>Params</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sweep.runs.slice(0, 20).map((run, i) => (
                      <tr key={i}>
                        <td style={cellStyle}>{run.run_index + 1}</td>
                        <td style={{
                          ...cellStyle,
                          color: run.status === 'SUCCESS' ? '#22c55e' :
                                 run.status === 'FAILURE' ? '#ef4444' : theme.colors.textSecondary,
                        }}>{run.status}</td>
                        <td style={{ ...cellStyle, fontFamily: 'monospace', fontSize: 9 }}>
                          {JSON.stringify(run.params).slice(0, 80)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {sweep.runs.length > 20 && (
                  <div style={{ fontSize: 10, color: theme.colors.textSecondary, textAlign: 'center', marginTop: 4 }}>
                    Showing 20 of {sweep.runs.length} runs
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
