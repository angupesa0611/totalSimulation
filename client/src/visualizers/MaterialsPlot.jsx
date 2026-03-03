import React, { useMemo, useState } from 'react';
import Plot from 'react-plotly.js';

const ACCENT = '#d946ef';
const COLORS = ['#d946ef', '#e879f9', '#f0abfc', '#f5d0fe', '#c026d3', '#a21caf', '#86198f', '#701a75'];

export default function MaterialsPlot({ data }) {
  const [tab, setTab] = useState('main');

  if (!data) {
    return <div style={{ color: '#8888a0', padding: 24 }}>No data to display</div>;
  }

  const tabs = useMemo(() => {
    const t = [];
    // QE tabs
    if (data.bands) t.push('bands');
    if (data.energies_eV && data.dos_states_per_eV) t.push('dos');
    // LAMMPS tabs
    if (data.thermo && data.thermo.step?.length > 0) t.push('thermo');
    if (data.rdf && data.rdf.r?.length > 0) t.push('rdf');
    if (data.msd && data.msd.time?.length > 0) t.push('msd');
    // Shared
    if (data.total_energy_Ry !== undefined || data.thermo) t.push('energy');
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

  // Band structure traces
  const bandTraces = useMemo(() => {
    if (!data.bands) return [];
    return Object.entries(data.bands).map(([idx, energies], i) => ({
      x: Array.from({ length: energies.length }, (_, k) => k),
      y: energies,
      type: 'scatter',
      mode: 'lines',
      name: `Band ${idx}`,
      line: { color: i === 0 ? ACCENT : COLORS[i % COLORS.length], width: 1.5 },
      showlegend: false,
    }));
  }, [data]);

  // Thermo traces
  const thermoTraces = useMemo(() => {
    if (!data.thermo || !data.thermo.step?.length) return [];
    return [
      { name: 'Temperature', y: data.thermo.temp, color: '#ef4444', yaxis: 'y' },
      { name: 'PE', y: data.thermo.pe, color: ACCENT, yaxis: 'y2' },
      { name: 'KE', y: data.thermo.ke, color: '#22c55e', yaxis: 'y2' },
    ].filter(t => t.y?.length > 0).map(t => ({
      x: data.thermo.step,
      y: t.y,
      type: 'scatter',
      mode: 'lines',
      name: t.name,
      line: { color: t.color, width: 2 },
      yaxis: t.yaxis,
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
          >{t.replace('_', ' ')}</button>
        ))}
      </div>

      {activeTab === 'bands' && bandTraces.length > 0 && (
        <div style={{ flex: 1 }}>
          <Plot
            data={bandTraces}
            layout={{
              ...darkLayout,
              title: { text: `Band Structure${data.band_gap_eV !== undefined ? ` (gap: ${data.band_gap_eV.toFixed(2)} eV)` : ''}`, font: { size: 14 } },
              xaxis: { ...darkLayout.xaxis, title: 'k-point index' },
              yaxis: { ...darkLayout.yaxis, title: 'Energy (eV)' },
              shapes: data.fermi_energy_eV !== undefined ? [{
                type: 'line', x0: 0, x1: 1, xref: 'paper',
                y0: data.fermi_energy_eV, y1: data.fermi_energy_eV,
                line: { color: '#ef4444', width: 1, dash: 'dash' },
              }] : [],
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {activeTab === 'dos' && data.energies_eV && (
        <div style={{ flex: 1 }}>
          <Plot
            data={[{
              x: data.energies_eV,
              y: data.dos_states_per_eV,
              type: 'scatter',
              mode: 'lines',
              fill: 'tozeroy',
              name: 'DOS',
              line: { color: ACCENT, width: 2 },
              fillcolor: `${ACCENT}33`,
            }]}
            layout={{
              ...darkLayout,
              title: { text: 'Density of States', font: { size: 14 } },
              xaxis: { ...darkLayout.xaxis, title: 'Energy (eV)' },
              yaxis: { ...darkLayout.yaxis, title: 'DOS (states/eV)' },
              shapes: data.fermi_energy_eV !== undefined ? [{
                type: 'line', y0: 0, y1: 1, yref: 'paper',
                x0: data.fermi_energy_eV, x1: data.fermi_energy_eV,
                line: { color: '#ef4444', width: 1, dash: 'dash' },
              }] : [],
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {activeTab === 'thermo' && thermoTraces.length > 0 && (
        <div style={{ flex: 1 }}>
          <Plot
            data={thermoTraces}
            layout={{
              ...darkLayout,
              title: { text: 'Thermodynamic Properties', font: { size: 14 } },
              xaxis: { ...darkLayout.xaxis, title: 'Timestep' },
              yaxis: { ...darkLayout.yaxis, title: 'Temperature' },
              yaxis2: {
                title: 'Energy',
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

      {activeTab === 'rdf' && data.rdf?.r?.length > 0 && (
        <div style={{ flex: 1 }}>
          <Plot
            data={[{
              x: data.rdf.r,
              y: data.rdf.g_r,
              type: 'scatter',
              mode: 'lines',
              name: 'g(r)',
              line: { color: ACCENT, width: 2 },
              fill: 'tozeroy',
              fillcolor: `${ACCENT}22`,
            }]}
            layout={{
              ...darkLayout,
              title: { text: 'Radial Distribution Function', font: { size: 14 } },
              xaxis: { ...darkLayout.xaxis, title: 'r (σ)' },
              yaxis: { ...darkLayout.yaxis, title: 'g(r)' },
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {activeTab === 'msd' && data.msd?.time?.length > 0 && (
        <div style={{ flex: 1 }}>
          <Plot
            data={[{
              x: data.msd.time,
              y: data.msd.msd,
              type: 'scatter',
              mode: 'lines',
              name: 'MSD',
              line: { color: '#22c55e', width: 2 },
            }]}
            layout={{
              ...darkLayout,
              title: { text: 'Mean Square Displacement', font: { size: 14 } },
              xaxis: { ...darkLayout.xaxis, title: 'Time' },
              yaxis: { ...darkLayout.yaxis, title: 'MSD (σ²)' },
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {activeTab === 'energy' && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace", overflowY: 'auto', flex: 1 }}>
          <h4 style={{ color: ACCENT, marginBottom: 16 }}>Energy Summary</h4>
          {data.total_energy_Ry !== undefined && (
            <>
              <div>Total Energy: {data.total_energy_Ry.toFixed(6)} Ry</div>
              <div>Total Energy: {(data.total_energy_Ry * 13.6057).toFixed(4)} eV</div>
            </>
          )}
          {data.n_iterations !== undefined && <div>SCF Iterations: {data.n_iterations}</div>}
          {data.fermi_energy_eV !== undefined && <div>Fermi Energy: {data.fermi_energy_eV.toFixed(4)} eV</div>}
          {data.band_gap_eV !== undefined && <div>Band Gap: {data.band_gap_eV.toFixed(4)} eV</div>}
          {data.total_force !== undefined && <div>Total Force: {data.total_force.toFixed(6)}</div>}
          {data.n_atoms !== undefined && <div>Atoms: {data.n_atoms}</div>}
          {data.final_temperature !== undefined && <div>Final Temperature: {data.final_temperature.toFixed(2)}</div>}
          {data.solve_time !== undefined && <div>Solve Time: {data.solve_time.toFixed(1)} s</div>}
        </div>
      )}

      {activeTab === 'info' && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace" }}>
          <h4 style={{ color: ACCENT, marginBottom: 12 }}>Simulation Info</h4>
          <div>Tool: {data.tool}</div>
          <div>Type: {data.simulation_type}</div>
          {data.n_atoms !== undefined && <div>Atoms: {data.n_atoms}</div>}
          {data.solve_time !== undefined && <div>Solve Time: {data.solve_time.toFixed(1)} s</div>}
          {data.trajectory_job_id && (
            <div style={{ marginTop: 8, color: ACCENT }}>Trajectory available for MDAnalysis coupling</div>
          )}
        </div>
      )}
    </div>
  );
}
