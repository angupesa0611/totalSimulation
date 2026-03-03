import React, { useMemo, useState } from 'react';
import Plot from 'react-plotly.js';

const ACCENT = '#fb923c';
const COLORS = ['#fb923c', '#f59e0b', '#22c55e', '#6366f1', '#ef4444', '#06b6d4'];

export default function ControlPlot({ data }) {
  const [tab, setTab] = useState('main');

  if (!data) {
    return <div style={{ color: '#8888a0', padding: 24 }}>No data to display</div>;
  }

  const simType = data.simulation_type;

  const darkLayout = {
    paper_bgcolor: '#0a0a0f',
    plot_bgcolor: '#12121a',
    font: { color: '#e0e0e0', family: "'Inter', sans-serif" },
    margin: { t: 40, r: 30, b: 50, l: 60 },
    xaxis: { gridcolor: '#2a2a3a', zerolinecolor: '#2a2a3a' },
    yaxis: { gridcolor: '#2a2a3a', zerolinecolor: '#2a2a3a' },
    legend: { bgcolor: 'transparent', font: { color: '#8888a0' } },
  };

  const tabs = useMemo(() => {
    const t = ['main'];
    if (simType === 'bode_plot') t[0] = 'magnitude';
    if (simType === 'bode_plot') t.push('phase');
    t.push('info');
    return t;
  }, [simType]);

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
          >{t}</button>
        ))}
      </div>

      {/* Bode Plot - Magnitude */}
      {(activeTab === 'magnitude' || (activeTab === 'main' && simType === 'bode_plot')) && data.magnitude_dB && (
        <div style={{ flex: 1 }}>
          <Plot
            data={[{
              x: data.frequencies_rad,
              y: data.magnitude_dB,
              type: 'scatter',
              mode: 'lines',
              name: 'Magnitude',
              line: { color: ACCENT, width: 2 },
            }]}
            layout={{
              ...darkLayout,
              title: { text: 'Bode Plot — Magnitude', font: { size: 14 } },
              xaxis: { ...darkLayout.xaxis, title: 'Frequency (rad/s)', type: 'log' },
              yaxis: { ...darkLayout.yaxis, title: 'Magnitude (dB)' },
              annotations: data.gain_margin_dB ? [{
                text: `GM: ${data.gain_margin_dB?.toFixed(1)} dB | PM: ${data.phase_margin_deg?.toFixed(1)}°`,
                xref: 'paper', yref: 'paper', x: 0.02, y: 0.98,
                showarrow: false, font: { color: ACCENT, size: 11 },
                bgcolor: '#1a1a28', borderpad: 4,
              }] : [],
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {/* Bode Plot - Phase */}
      {activeTab === 'phase' && data.phase_deg && (
        <div style={{ flex: 1 }}>
          <Plot
            data={[{
              x: data.frequencies_rad,
              y: data.phase_deg,
              type: 'scatter',
              mode: 'lines',
              name: 'Phase',
              line: { color: '#22c55e', width: 2 },
            }]}
            layout={{
              ...darkLayout,
              title: { text: 'Bode Plot — Phase', font: { size: 14 } },
              xaxis: { ...darkLayout.xaxis, title: 'Frequency (rad/s)', type: 'log' },
              yaxis: { ...darkLayout.yaxis, title: 'Phase (degrees)' },
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {/* Nyquist Plot */}
      {activeTab === 'main' && simType === 'nyquist_plot' && data.real && (
        <div style={{ flex: 1 }}>
          <Plot
            data={[
              {
                x: data.real,
                y: data.imag,
                type: 'scatter',
                mode: 'lines',
                name: 'Nyquist',
                line: { color: ACCENT, width: 2 },
              },
              {
                x: Array.from({length: 101}, (_, i) => Math.cos(i * 2 * Math.PI / 100)),
                y: Array.from({length: 101}, (_, i) => Math.sin(i * 2 * Math.PI / 100)),
                type: 'scatter',
                mode: 'lines',
                name: 'Unit Circle',
                line: { color: '#2a2a3a', width: 1, dash: 'dash' },
              },
            ]}
            layout={{
              ...darkLayout,
              title: { text: `Nyquist Plot — ${data.is_stable ? 'Stable' : 'Unstable'}`, font: { size: 14 } },
              xaxis: { ...darkLayout.xaxis, title: 'Real', scaleanchor: 'y' },
              yaxis: { ...darkLayout.yaxis, title: 'Imaginary' },
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {/* Root Locus */}
      {activeTab === 'main' && simType === 'root_locus' && data.roots_real && (
        <div style={{ flex: 1 }}>
          <Plot
            data={data.roots_real[0]?.map((_, colIdx) => ({
              x: data.roots_real.map(row => row[colIdx]),
              y: data.roots_imag.map(row => row[colIdx]),
              type: 'scatter',
              mode: 'markers',
              marker: { size: 3, color: COLORS[colIdx % COLORS.length] },
              name: `Branch ${colIdx + 1}`,
            })) || []}
            layout={{
              ...darkLayout,
              title: { text: 'Root Locus', font: { size: 14 } },
              xaxis: { ...darkLayout.xaxis, title: 'Real Axis' },
              yaxis: { ...darkLayout.yaxis, title: 'Imaginary Axis' },
              showlegend: false,
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {/* Step Response */}
      {activeTab === 'main' && simType === 'step_response' && data.times && (
        <div style={{ flex: 1 }}>
          <Plot
            data={[{
              x: data.times,
              y: data.response,
              type: 'scatter',
              mode: 'lines',
              name: 'Response',
              line: { color: ACCENT, width: 2 },
            }]}
            layout={{
              ...darkLayout,
              title: { text: 'Step Response', font: { size: 14 } },
              xaxis: { ...darkLayout.xaxis, title: 'Time (s)' },
              yaxis: { ...darkLayout.yaxis, title: 'Amplitude' },
              annotations: [
                data.settling_time && {
                  text: `Ts: ${data.settling_time?.toFixed(3)}s`,
                  xref: 'paper', yref: 'paper', x: 0.98, y: 0.98,
                  showarrow: false, font: { color: '#22c55e', size: 11 },
                  bgcolor: '#1a1a28', borderpad: 4, xanchor: 'right',
                },
                data.overshoot_pct !== undefined && {
                  text: `OS: ${data.overshoot_pct?.toFixed(1)}%`,
                  xref: 'paper', yref: 'paper', x: 0.98, y: 0.90,
                  showarrow: false, font: { color: '#f59e0b', size: 11 },
                  bgcolor: '#1a1a28', borderpad: 4, xanchor: 'right',
                },
              ].filter(Boolean),
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {/* Transfer Function / State Space Info */}
      {activeTab === 'main' && (simType === 'transfer_function' || simType === 'state_space') && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace" }}>
          <h4 style={{ color: ACCENT, marginBottom: 12 }}>System Analysis</h4>
          <div>Stable: {data.is_stable ? 'Yes' : 'No'}</div>
          {data.dc_gain !== undefined && <div>DC Gain: {data.dc_gain?.toFixed(4)}</div>}
          <div style={{ marginTop: 8 }}>Poles: {data.poles_real?.map((r, i) =>
            `${r.toFixed(4)}${data.poles_imag[i] ? ` + ${data.poles_imag[i].toFixed(4)}j` : ''}`
          ).join(', ')}</div>
          {data.zeros_real?.length > 0 && <div>Zeros: {data.zeros_real?.map((r, i) =>
            `${r.toFixed(4)}${data.zeros_imag?.[i] ? ` + ${data.zeros_imag[i].toFixed(4)}j` : ''}`
          ).join(', ')}</div>}
          {data.n_states && <div>States: {data.n_states}, Inputs: {data.n_inputs}, Outputs: {data.n_outputs}</div>}
        </div>
      )}

      {/* Info tab */}
      {activeTab === 'info' && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace" }}>
          <h4 style={{ color: ACCENT, marginBottom: 12 }}>Control Systems Info</h4>
          <div>Tool: {data.tool}</div>
          <div>Type: {data.simulation_type}</div>
          {data.gain_margin_dB && <div>Gain Margin: {data.gain_margin_dB?.toFixed(2)} dB</div>}
          {data.phase_margin_deg && <div>Phase Margin: {data.phase_margin_deg?.toFixed(2)}°</div>}
          {data.crossover_freq && <div>Crossover Frequency: {data.crossover_freq?.toFixed(4)} rad/s</div>}
          {data.settling_time && <div>Settling Time: {data.settling_time?.toFixed(4)} s</div>}
          {data.overshoot_pct !== undefined && <div>Overshoot: {data.overshoot_pct?.toFixed(2)}%</div>}
          {data.rise_time && <div>Rise Time: {data.rise_time?.toFixed(4)} s</div>}
          {data.steady_state !== undefined && <div>Steady State: {data.steady_state?.toFixed(4)}</div>}
        </div>
      )}
    </div>
  );
}
