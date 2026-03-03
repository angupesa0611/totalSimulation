import React, { useMemo, useState } from 'react';
import Plot from 'react-plotly.js';

const ACCENT = '#0ea5e9';
const COLORS = ['#0ea5e9', '#38bdf8', '#7dd3fc', '#bae6fd', '#0284c7', '#0369a1', '#075985', '#0c4a6e'];

export default function KineticsPlot({ data }) {
  const [tab, setTab] = useState('temperature');

  if (!data) {
    return <div style={{ color: '#8888a0', padding: 24 }}>No data to display</div>;
  }

  const simType = data.simulation_type || 'ignition_delay';

  const tabs = useMemo(() => {
    const t = [];
    if (data.temperatures_K) t.push('temperature');
    if (data.pressures_atm) t.push('pressure');
    if (data.species) t.push('species');
    if (data.temperature_profile) t.push('flame');
    if (data.species_eq) t.push('equilibrium');
    t.push('info');
    return t;
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

  const ignitionShapes = useMemo(() => {
    if (simType !== 'ignition_delay' || !data.ignition_delay_ms) return [];
    return [{
      type: 'line',
      x0: data.ignition_delay_ms,
      x1: data.ignition_delay_ms,
      y0: 0, y1: 1, yref: 'paper',
      line: { color: '#ef4444', width: 2, dash: 'dash' },
    }];
  }, [data, simType]);

  const ignitionAnnotations = useMemo(() => {
    if (simType !== 'ignition_delay' || !data.ignition_delay_ms) return [];
    return [{
      x: data.ignition_delay_ms,
      y: 1, yref: 'paper',
      text: `τ_ign = ${data.ignition_delay_ms.toFixed(4)} ms`,
      showarrow: true, arrowhead: 2, arrowcolor: '#ef4444',
      font: { color: '#ef4444', size: 11 },
      bgcolor: '#1a0a0a',
    }];
  }, [data, simType]);

  const speciesTraces = useMemo(() => {
    if (!data.species || !data.times_ms) return [];
    return Object.entries(data.species).map(([name, values], i) => ({
      x: data.times_ms,
      y: values,
      type: 'scatter',
      mode: 'lines',
      name,
      line: { color: COLORS[i % COLORS.length], width: 2 },
    }));
  }, [data]);

  const flameSpeciesTraces = useMemo(() => {
    if (!data.species_profiles) return [];
    return Object.entries(data.species_profiles).map(([name, profile], i) => ({
      x: profile.positions_m,
      y: profile.values,
      type: 'scatter',
      mode: 'lines',
      name,
      line: { color: COLORS[i % COLORS.length], width: 2 },
      yaxis: 'y2',
    }));
  }, [data]);

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

      {activeTab === 'temperature' && data.temperatures_K && (
        <div style={{ flex: 1 }}>
          <Plot
            data={[{
              x: data.times_ms,
              y: data.temperatures_K,
              type: 'scatter',
              mode: 'lines',
              name: 'Temperature',
              line: { color: ACCENT, width: 2 },
            }]}
            layout={{
              ...darkLayout,
              title: { text: `Temperature Profile — ${data.mechanism || 'GRI-Mech'}`, font: { size: 14 } },
              xaxis: { ...darkLayout.xaxis, title: 'Time (ms)' },
              yaxis: { ...darkLayout.yaxis, title: 'Temperature (K)' },
              shapes: ignitionShapes,
              annotations: ignitionAnnotations,
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {activeTab === 'pressure' && data.pressures_atm && (
        <div style={{ flex: 1 }}>
          <Plot
            data={[{
              x: data.times_ms,
              y: data.pressures_atm,
              type: 'scatter',
              mode: 'lines',
              name: 'Pressure',
              line: { color: '#f59e0b', width: 2 },
            }]}
            layout={{
              ...darkLayout,
              title: { text: 'Pressure Profile', font: { size: 14 } },
              xaxis: { ...darkLayout.xaxis, title: 'Time (ms)' },
              yaxis: { ...darkLayout.yaxis, title: 'Pressure (atm)' },
              shapes: ignitionShapes,
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {activeTab === 'species' && speciesTraces.length > 0 && (
        <div style={{ flex: 1 }}>
          <Plot
            data={speciesTraces}
            layout={{
              ...darkLayout,
              title: { text: 'Species Mole Fractions', font: { size: 14 } },
              xaxis: { ...darkLayout.xaxis, title: 'Time (ms)' },
              yaxis: { ...darkLayout.yaxis, title: 'Mole Fraction', type: 'log' },
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {activeTab === 'flame' && data.temperature_profile && (
        <div style={{ flex: 1 }}>
          <Plot
            data={[
              {
                x: data.temperature_profile.positions_m,
                y: data.temperature_profile.T_K,
                type: 'scatter',
                mode: 'lines',
                name: 'Temperature',
                line: { color: '#ef4444', width: 2 },
              },
              ...flameSpeciesTraces,
            ]}
            layout={{
              ...darkLayout,
              title: { text: `Flame Structure — S_L = ${data.flame_speed_cm_s?.toFixed(2)} cm/s`, font: { size: 14 } },
              xaxis: { ...darkLayout.xaxis, title: 'Position (m)' },
              yaxis: { ...darkLayout.yaxis, title: 'Temperature (K)' },
              yaxis2: {
                title: 'Mole Fraction',
                overlaying: 'y',
                side: 'right',
                gridcolor: '#2a2a3a',
              },
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {activeTab === 'equilibrium' && data.species_eq && (
        <div style={{ flex: 1 }}>
          <Plot
            data={[{
              x: Object.keys(data.species_eq),
              y: Object.values(data.species_eq),
              type: 'bar',
              marker: { color: ACCENT },
            }]}
            layout={{
              ...darkLayout,
              title: { text: `Equilibrium — T=${data.T_eq_K?.toFixed(0)} K, P=${data.P_eq_atm?.toFixed(2)} atm`, font: { size: 14 } },
              xaxis: { ...darkLayout.xaxis, title: 'Species', tickangle: -45 },
              yaxis: { ...darkLayout.yaxis, title: 'Mole Fraction', type: 'log' },
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {activeTab === 'info' && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace" }}>
          <h4 style={{ color: ACCENT, marginBottom: 12 }}>Cantera Simulation Info</h4>
          <div>Tool: {data.tool}</div>
          <div>Type: {data.simulation_type}</div>
          <div>Mechanism: {data.mechanism}</div>
          {data.ignition_delay_ms !== undefined && <div>Ignition Delay: {data.ignition_delay_ms.toFixed(4)} ms</div>}
          {data.flame_speed_cm_s !== undefined && <div>Flame Speed: {data.flame_speed_cm_s.toFixed(2)} cm/s</div>}
          {data.T_eq_K !== undefined && <div>Equilibrium T: {data.T_eq_K.toFixed(1)} K</div>}
        </div>
      )}
    </div>
  );
}
