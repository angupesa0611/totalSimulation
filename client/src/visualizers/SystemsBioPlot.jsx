import React, { useMemo, useState } from 'react';
import Plot from 'react-plotly.js';

const ACCENT = '#10b981';
const COLORS = ['#10b981', '#34d399', '#6ee7b7', '#a7f3d0', '#059669', '#047857', '#065f46', '#064e3b'];

export default function SystemsBioPlot({ data }) {
  const [tab, setTab] = useState('timecourse');

  if (!data) {
    return <div style={{ color: '#8888a0', padding: 24 }}>No data to display</div>;
  }

  const simType = data.simulation_type || 'ode_timecourse';

  const tabs = useMemo(() => {
    const t = [];
    if (data.times && data.species) t.push('timecourse');
    if (data.steady_state_values) t.push('steady_state');
    if (data.scan_values && data.scan_results) t.push('scan');
    if (data.flux_control_coefficients || data.concentration_control_coefficients) t.push('mca');
    if (data.sensitivities) t.push('sensitivity');
    t.push('info');
    return t;
  }, [data]);

  const timecourseTraces = useMemo(() => {
    if (!data.times || !data.species) return [];
    return Object.entries(data.species).map(([name, values], i) => ({
      x: data.times,
      y: values,
      type: 'scatter',
      mode: 'lines',
      name,
      line: { color: COLORS[i % COLORS.length], width: 2 },
    }));
  }, [data]);

  const scanTraces = useMemo(() => {
    if (!data.scan_values || !data.scan_results) return [];
    const speciesNames = Object.keys(data.scan_results[0] || {});
    return speciesNames.map((name, i) => ({
      x: data.scan_values,
      y: data.scan_results.map(r => r[name]),
      type: 'scatter',
      mode: 'lines+markers',
      name,
      line: { color: COLORS[i % COLORS.length], width: 2 },
      marker: { size: 4 },
    }));
  }, [data]);

  const darkLayout = {
    paper_bgcolor: '#0a0a0f',
    plot_bgcolor: '#12121a',
    font: { color: '#e0e0e0', family: "'Inter', sans-serif" },
    margin: { t: 40, r: 30, b: 50, l: 60 },
    xaxis: { gridcolor: '#2a2a3a', zerolinecolor: '#2a2a3a' },
    yaxis: { gridcolor: '#2a2a3a', zerolinecolor: '#2a2a3a' },
    legend: { bgcolor: 'transparent', font: { color: '#8888a0' } },
  };

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Tab bar */}
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
          >{t.replace('_', ' ')}</button>
        ))}
      </div>

      {tab === 'timecourse' && timecourseTraces.length > 0 && (
        <div style={{ flex: 1 }}>
          <Plot
            data={timecourseTraces}
            layout={{
              ...darkLayout,
              title: { text: `${data.tool === 'basico' ? 'BasiCO' : 'Tellurium'} — Species Timecourse`, font: { size: 14 } },
              xaxis: { ...darkLayout.xaxis, title: 'Time' },
              yaxis: { ...darkLayout.yaxis, title: 'Concentration' },
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {tab === 'steady_state' && data.steady_state_values && (
        <div style={{ flex: 1 }}>
          <Plot
            data={[{
              x: Object.keys(data.steady_state_values),
              y: Object.values(data.steady_state_values),
              type: 'bar',
              marker: { color: ACCENT },
            }]}
            layout={{
              ...darkLayout,
              title: { text: 'Steady State Concentrations', font: { size: 14 } },
              xaxis: { ...darkLayout.xaxis, title: 'Species' },
              yaxis: { ...darkLayout.yaxis, title: 'Concentration' },
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {tab === 'scan' && scanTraces.length > 0 && (
        <div style={{ flex: 1 }}>
          <Plot
            data={scanTraces}
            layout={{
              ...darkLayout,
              title: { text: `Parameter Scan: ${data.scan_parameter}`, font: { size: 14 } },
              xaxis: { ...darkLayout.xaxis, title: data.scan_parameter },
              yaxis: { ...darkLayout.yaxis, title: 'Steady-State Concentration' },
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {tab === 'mca' && (
        <div style={{ flex: 1 }}>
          {data.flux_control_coefficients?.data && (
            <Plot
              data={[{
                z: data.flux_control_coefficients.data,
                x: data.flux_control_coefficients.cols,
                y: data.flux_control_coefficients.rows,
                type: 'heatmap',
                colorscale: [[0, '#064e3b'], [0.5, '#0a0a0f'], [1, '#10b981']],
                colorbar: { title: { text: 'FCC', font: { color: '#e0e0e0' } }, tickfont: { color: '#8888a0' } },
              }]}
              layout={{
                ...darkLayout,
                title: { text: 'Flux Control Coefficients', font: { size: 14 } },
              }}
              style={{ width: '100%', height: '100%' }}
              useResizeHandler
              config={{ responsive: true }}
            />
          )}
        </div>
      )}

      {tab === 'sensitivity' && data.sensitivities && (
        <div style={{ flex: 1, padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace", overflowY: 'auto' }}>
          <h4 style={{ color: ACCENT, marginBottom: 12 }}>Sensitivity Analysis</h4>
          {Object.entries(data.sensitivities).map(([param, species]) => (
            <div key={param} style={{ marginBottom: 12 }}>
              <div style={{ fontWeight: 600 }}>{param}</div>
              {Object.entries(species).map(([sp, val]) => (
                <div key={sp} style={{ paddingLeft: 16, color: '#8888a0' }}>
                  {sp}: {typeof val === 'number' ? val.toFixed(4) : val}
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      {tab === 'info' && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace" }}>
          <h4 style={{ color: ACCENT, marginBottom: 12 }}>Simulation Info</h4>
          <div>Tool: {data.tool}</div>
          <div>Type: {data.simulation_type}</div>
          {data.n_species !== undefined && <div>Species: {data.n_species}</div>}
          {data.duration !== undefined && <div>Duration: {data.duration}</div>}
          {data.method && <div>Method: {data.method}</div>}
          {data.sbml_export && <div style={{ marginTop: 8, color: '#10b981' }}>SBML export available for pipeline coupling</div>}
        </div>
      )}
    </div>
  );
}
