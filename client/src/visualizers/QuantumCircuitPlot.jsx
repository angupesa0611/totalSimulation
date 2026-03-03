import React, { useMemo, useState } from 'react';
import Plot from 'react-plotly.js';

const ACCENT = '#2dd4bf';

export default function QuantumCircuitPlot({ data }) {
  const [tab, setTab] = useState('main');

  if (!data) {
    return <div style={{ color: '#8888a0', padding: 24 }}>No data to display</div>;
  }

  const simType = data.simulation_type || 'circuit_simulation';

  const tabs = useMemo(() => {
    const t = [];
    if (data.counts || data.measurement_counts) t.push('histogram');
    if (data.probabilities?.length > 0) t.push('statevector');
    if (data.convergence) t.push('convergence');
    if (simType === 'transpilation') t.push('transpile');
    t.push('circuit_info');
    return t;
  }, [data, simType]);

  const darkLayout = {
    paper_bgcolor: '#0a0a0f',
    plot_bgcolor: '#12121a',
    font: { color: '#e0e0e0', family: "'Inter', sans-serif" },
    margin: { t: 40, r: 30, b: 50, l: 60 },
    xaxis: { gridcolor: '#2a2a3a', zerolinecolor: '#2a2a3a' },
    yaxis: { gridcolor: '#2a2a3a', zerolinecolor: '#2a2a3a' },
    legend: { bgcolor: 'transparent', font: { color: '#8888a0' } },
  };

  const activeTab = tabs.includes(tab) ? tab : tabs[0];

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
              padding: '4px 12px', background: activeTab === t ? ACCENT : 'transparent',
              border: 'none', borderRadius: 4,
              color: activeTab === t ? '#fff' : '#8888a0',
              fontSize: 11, cursor: 'pointer', textTransform: 'capitalize',
            }}
          >{t.replace('_', ' ')}</button>
        ))}
      </div>

      {activeTab === 'histogram' && (
        <div style={{ flex: 1 }}>
          {(() => {
            const counts = data.counts || data.measurement_counts || {};
            const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
            const labels = sorted.map(e => e[0]);
            const values = sorted.map(e => e[1]);

            return (
              <Plot
                data={[{
                  x: labels,
                  y: values,
                  type: 'bar',
                  marker: {
                    color: labels.map((_, i) => {
                      const hue = (i * 360 / labels.length) % 360;
                      return `hsl(${hue}, 70%, 60%)`;
                    }),
                  },
                  text: values.map(v => String(v)),
                  textposition: 'auto',
                }]}
                layout={{
                  ...darkLayout,
                  title: { text: 'Measurement Counts', font: { size: 14 } },
                  xaxis: { ...darkLayout.xaxis, title: 'Bitstring', tickangle: -45 },
                  yaxis: { ...darkLayout.yaxis, title: 'Counts' },
                }}
                style={{ width: '100%', height: '100%' }}
                useResizeHandler
                config={{ responsive: true }}
              />
            );
          })()}
        </div>
      )}

      {activeTab === 'statevector' && data.probabilities?.length > 0 && (
        <div style={{ flex: 1 }}>
          {(() => {
            const nQubits = data.n_qubits || Math.log2(data.probabilities.length);
            const labels = data.probabilities.map((_, i) =>
              `|${i.toString(2).padStart(nQubits, '0')}⟩`
            );

            return (
              <Plot
                data={[{
                  x: labels,
                  y: data.probabilities,
                  type: 'bar',
                  marker: { color: ACCENT },
                  text: data.probabilities.map(p => p.toFixed(4)),
                  textposition: 'auto',
                }]}
                layout={{
                  ...darkLayout,
                  title: { text: 'State Probabilities', font: { size: 14 } },
                  xaxis: { ...darkLayout.xaxis, title: 'Basis State', tickangle: -45 },
                  yaxis: { ...darkLayout.yaxis, title: 'Probability', range: [0, 1] },
                }}
                style={{ width: '100%', height: '100%' }}
                useResizeHandler
                config={{ responsive: true }}
              />
            );
          })()}
        </div>
      )}

      {activeTab === 'convergence' && data.convergence && (
        <div style={{ flex: 1 }}>
          <Plot
            data={[{
              x: data.convergence.iterations,
              y: data.convergence.energies || data.convergence.costs,
              type: 'scatter',
              mode: 'lines',
              line: { color: ACCENT, width: 2 },
              name: data.convergence.energies ? 'Energy' : 'Cost',
            }]}
            layout={{
              ...darkLayout,
              title: { text: `VQE Convergence — E = ${data.ground_state_energy?.toFixed(6) || data.fidelity?.toFixed(6) || 'N/A'}`, font: { size: 14 } },
              xaxis: { ...darkLayout.xaxis, title: 'Iteration' },
              yaxis: { ...darkLayout.yaxis, title: data.convergence.energies ? 'Energy (Ha)' : 'Cost' },
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {activeTab === 'transpile' && simType === 'transpilation' && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace", overflowY: 'auto', flex: 1 }}>
          <h4 style={{ color: ACCENT, marginBottom: 16 }}>Transpilation Results</h4>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <tbody>
              {[
                ['Original Depth', data.original_depth],
                ['Optimized Depth', data.optimized_depth],
                ['Original Gates', data.original_gates],
                ['Optimized Gates', data.optimized_gates],
                ['Reduction', data.original_depth > 0 ? `${((1 - data.optimized_depth / data.original_depth) * 100).toFixed(1)}%` : 'N/A'],
              ].map(([label, value]) => (
                <tr key={label} style={{ borderBottom: '1px solid #2a2a3a' }}>
                  <td style={{ padding: '8px 12px', color: '#8888a0' }}>{label}</td>
                  <td style={{ padding: '8px 12px', color: '#e0e0e0', fontWeight: 600 }}>{value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'circuit_info' && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace", overflowY: 'auto', flex: 1 }}>
          <h4 style={{ color: ACCENT, marginBottom: 12 }}>Circuit Info</h4>
          <div>Tool: {data.tool}</div>
          <div>Type: {data.simulation_type}</div>
          <div>Qubits: {data.n_qubits}</div>
          {data.depth !== undefined && <div>Circuit Depth: {data.depth}</div>}
          {data.n_gates !== undefined && <div>Gate Count: {data.n_gates}</div>}
          {data.ground_state_energy !== undefined && (
            <div style={{ marginTop: 8, color: ACCENT }}>
              Ground State Energy: {data.ground_state_energy.toFixed(6)} Ha
            </div>
          )}
          {data.fidelity !== undefined && (
            <div style={{ marginTop: 8, color: ACCENT }}>
              Fidelity: {data.fidelity.toFixed(6)}
            </div>
          )}
          {data.qasm_str && (
            <>
              <h4 style={{ color: ACCENT, marginTop: 16, marginBottom: 8 }}>OpenQASM</h4>
              <pre style={{
                background: '#1a1a28', padding: 12, borderRadius: 4,
                fontSize: 11, overflowX: 'auto', maxHeight: 200, overflowY: 'auto',
              }}>{data.qasm_str}</pre>
            </>
          )}
        </div>
      )}
    </div>
  );
}
