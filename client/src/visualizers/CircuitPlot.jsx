import React, { useMemo, useState } from 'react';
import Plot from 'react-plotly.js';

const ACCENT = '#2dd4bf';

export default function CircuitPlot({ data }) {
  const [tab, setTab] = useState('main');

  if (!data) {
    return <div style={{ color: '#8888a0', padding: 24 }}>No data to display</div>;
  }

  const simType = data.simulation_type || 'dc_analysis';

  const tabs = useMemo(() => {
    const t = [];
    if (simType === 'dc_analysis' || simType === 'dc_operating_point') t.push('dc');
    if (simType === 'ac_analysis') t.push('bode');
    if (simType === 'transient' || simType === 'transient_analysis') t.push('waveform');
    if (simType === 'transfer_function') t.push('transfer');
    t.push('info');
    return t;
  }, [simType]);

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
          >{t}</button>
        ))}
      </div>

      {activeTab === 'dc' && (
        <div style={{ flex: 1 }}>
          {(() => {
            const nodeV = data.node_voltages || {};
            const names = Object.keys(nodeV);
            const values = names.map(n => {
              const v = nodeV[n];
              return typeof v === 'number' ? v : parseFloat(v) || 0;
            });

            if (names.length === 0) {
              return (
                <div style={{ padding: 24, color: '#e0e0e0', fontFamily: "'JetBrains Mono', monospace" }}>
                  <h4 style={{ color: ACCENT, marginBottom: 12 }}>DC Analysis</h4>
                  {data.latex && Object.entries(data.latex).map(([k, v]) => (
                    <div key={k} style={{ marginBottom: 4 }}>{k}: {v}</div>
                  ))}
                </div>
              );
            }

            return (
              <Plot
                data={[{
                  x: names,
                  y: values,
                  type: 'bar',
                  marker: { color: ACCENT },
                  text: values.map(v => `${v.toFixed(3)} V`),
                  textposition: 'auto',
                }]}
                layout={{
                  ...darkLayout,
                  title: { text: 'DC Node Voltages', font: { size: 14 } },
                  xaxis: { ...darkLayout.xaxis, title: 'Node' },
                  yaxis: { ...darkLayout.yaxis, title: 'Voltage (V)' },
                }}
                style={{ width: '100%', height: '100%' }}
                useResizeHandler
                config={{ responsive: true }}
              />
            );
          })()}
        </div>
      )}

      {activeTab === 'bode' && (
        <div style={{ flex: 1 }}>
          {(() => {
            const freq = data.frequencies_Hz || [];
            // Handle both dict and list formats for magnitude
            let magData, phaseData;
            if (typeof data.magnitude_dB === 'object' && !Array.isArray(data.magnitude_dB)) {
              // PySpice dict format
              const firstKey = Object.keys(data.magnitude_dB)[0];
              magData = data.magnitude_dB[firstKey] || [];
              phaseData = (data.phase_deg || {})[firstKey] || [];
            } else {
              magData = data.magnitude_dB || [];
              phaseData = data.phase_deg || [];
            }

            return (
              <Plot
                data={[
                  {
                    x: freq, y: magData,
                    type: 'scatter', mode: 'lines',
                    line: { color: ACCENT, width: 2 },
                    name: 'Magnitude',
                    yaxis: 'y',
                  },
                  {
                    x: freq, y: phaseData,
                    type: 'scatter', mode: 'lines',
                    line: { color: '#f59e0b', width: 2, dash: 'dash' },
                    name: 'Phase',
                    yaxis: 'y2',
                  },
                ]}
                layout={{
                  ...darkLayout,
                  title: { text: 'Bode Plot', font: { size: 14 } },
                  xaxis: { ...darkLayout.xaxis, title: 'Frequency (Hz)', type: 'log' },
                  yaxis: { ...darkLayout.yaxis, title: 'Magnitude (dB)', side: 'left' },
                  yaxis2: {
                    title: 'Phase (°)', overlaying: 'y', side: 'right',
                    gridcolor: '#2a2a3a', zerolinecolor: '#2a2a3a',
                    titlefont: { color: '#f59e0b' }, tickfont: { color: '#f59e0b' },
                  },
                }}
                style={{ width: '100%', height: '100%' }}
                useResizeHandler
                config={{ responsive: true }}
              />
            );
          })()}
        </div>
      )}

      {activeTab === 'waveform' && (
        <div style={{ flex: 1 }}>
          {(() => {
            const times = data.times_s || [];
            const traces = [];

            // Plot voltages
            const voltages = data.voltages || {};
            Object.entries(voltages).forEach(([name, values]) => {
              traces.push({
                x: times, y: values,
                type: 'scatter', mode: 'lines',
                name: `V(${name})`,
                line: { width: 2 },
              });
            });

            // Plot currents
            const currents = data.currents || {};
            Object.entries(currents).forEach(([name, values]) => {
              traces.push({
                x: times, y: values,
                type: 'scatter', mode: 'lines',
                name: `I(${name})`,
                line: { width: 2, dash: 'dash' },
              });
            });

            return (
              <Plot
                data={traces}
                layout={{
                  ...darkLayout,
                  title: { text: 'Transient Waveforms', font: { size: 14 } },
                  xaxis: { ...darkLayout.xaxis, title: 'Time (s)' },
                  yaxis: { ...darkLayout.yaxis, title: 'Value' },
                }}
                style={{ width: '100%', height: '100%' }}
                useResizeHandler
                config={{ responsive: true }}
              />
            );
          })()}
        </div>
      )}

      {activeTab === 'transfer' && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace", overflowY: 'auto', flex: 1 }}>
          <h4 style={{ color: ACCENT, marginBottom: 16 }}>Transfer Function</h4>
          <div style={{ marginBottom: 12 }}>
            <span style={{ color: '#8888a0' }}>H(s) = </span>
            <span style={{ color: '#fff', fontSize: 14 }}>{data.transfer_expr}</span>
          </div>
          {data.transfer_latex && (
            <div style={{ color: ACCENT, fontSize: 12, marginBottom: 16 }}>
              LaTeX: {data.transfer_latex}
            </div>
          )}
          {data.dc_gain !== null && data.dc_gain !== undefined && (
            <div style={{ marginBottom: 8 }}>DC Gain: {data.dc_gain}</div>
          )}
          {data.poles?.length > 0 && (
            <div style={{ marginBottom: 8 }}>
              <span style={{ color: '#ef4444' }}>Poles: </span>{data.poles.join(', ')}
            </div>
          )}
          {data.zeros?.length > 0 && (
            <div style={{ marginBottom: 8 }}>
              <span style={{ color: '#22c55e' }}>Zeros: </span>{data.zeros.join(', ')}
            </div>
          )}
        </div>
      )}

      {activeTab === 'info' && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace" }}>
          <h4 style={{ color: ACCENT, marginBottom: 12 }}>Circuit Info</h4>
          <div>Tool: {data.tool}</div>
          <div>Type: {data.simulation_type}</div>
          {data.spice_netlist && (
            <div style={{ marginTop: 8, color: ACCENT }}>SPICE netlist available for coupling</div>
          )}
        </div>
      )}
    </div>
  );
}
