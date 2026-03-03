import React, { useMemo, useState } from 'react';
import Plot from 'react-plotly.js';

const COLORSCALES = {
  heat: 'Hot',
  diffusion: 'YlGnBu',
  elasticity: 'Viridis',
  stokes: 'Blues',
  structural: 'Viridis',
  thermal: 'Hot',
  thermal_structural: 'RdYlBu',
  smoke: 'Greys',
  fluid: 'Blues',
  convection: 'RdBu',
  wave: 'RdYlBu',
  cfd: 'Jet',
};

export default function FieldPlot({ data }) {
  const [tab, setTab] = useState('field');

  if (!data || !data.field_data) {
    return <div style={{ color: '#8888a0', padding: 24 }}>No field data to display</div>;
  }

  const problemType = data.problem_type || 'heat';
  const colorscale = COLORSCALES[problemType] || 'Viridis';

  const fieldLabelMap = {
    heat: 'Temperature', diffusion: 'Concentration', thermal: 'Temperature',
    stokes: 'Velocity', smoke: 'Density', fluid: 'Velocity',
    convection: 'Temperature', wave: 'Amplitude', cfd: 'Velocity',
  };
  const fieldLabel = fieldLabelMap[problemType] || 'Field Value';

  const plotData = useMemo(() => {
    if (tab === 'field') {
      return [{
        z: data.field_data,
        x: data.x_grid,
        y: data.y_grid,
        type: 'heatmap',
        colorscale: colorscale,
        colorbar: {
          title: { text: fieldLabel, font: { color: '#e0e0e0', size: 12 } },
          tickfont: { color: '#8888a0' },
        },
      }];
    }
    return [];
  }, [data, tab, colorscale, fieldLabel]);

  const layout = useMemo(() => ({
    paper_bgcolor: '#0a0a0f',
    plot_bgcolor: '#12121a',
    font: { color: '#e0e0e0', family: "'Inter', sans-serif" },
    margin: { t: 40, r: 80, b: 50, l: 60 },
    xaxis: {
      title: 'x',
      gridcolor: '#2a2a3a',
      zerolinecolor: '#2a2a3a',
    },
    yaxis: {
      title: 'y',
      gridcolor: '#2a2a3a',
      zerolinecolor: '#2a2a3a',
      scaleanchor: 'x',
    },
    title: {
      text: `${(data.tool || 'Field').charAt(0).toUpperCase() + (data.tool || 'field').slice(1)} — ${fieldLabel} Field`,
      font: { size: 14 },
    },
  }), [data, fieldLabel]);

  const tabs = ['field', 'stats'];
  if (data.mesh_info) tabs.splice(1, 0, 'mesh');

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
              padding: '4px 12px', background: tab === t ? '#6366f1' : 'transparent',
              border: 'none', borderRadius: 4,
              color: tab === t ? '#fff' : '#8888a0',
              fontSize: 11, cursor: 'pointer', textTransform: 'capitalize',
            }}
          >{t}</button>
        ))}
      </div>

      {tab === 'field' && (
        <div style={{ flex: 1 }}>
          <Plot
            data={plotData}
            layout={layout}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {tab === 'mesh' && data.mesh_info && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace" }}>
          <h4 style={{ color: '#6366f1', marginBottom: 12 }}>Mesh Information</h4>
          {data.mesh_info.n_cells && <div>Cells: {data.mesh_info.n_cells}</div>}
          {data.mesh_info.n_vertices && <div>Vertices: {data.mesh_info.n_vertices}</div>}
          {data.mesh_info.domain && <div>Domain: {data.mesh_info.domain.join(' x ')}</div>}
          {data.mesh_info.resolution && <div>Resolution: {data.mesh_info.resolution.join(' x ')}</div>}
          {data.mesh_info.divisions && <div>Divisions: {data.mesh_info.divisions.join(' x ')}</div>}
          {data.n_dofs && <div>Degrees of Freedom: {data.n_dofs}</div>}
          {data.n_elements && <div>Elements: {data.n_elements}</div>}
        </div>
      )}

      {tab === 'stats' && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace" }}>
          <h4 style={{ color: '#6366f1', marginBottom: 12 }}>Solution Statistics</h4>
          <div>Problem Type: {data.problem_type}</div>
          <div>Min Value: {data.min_value?.toExponential(4)}</div>
          <div>Max Value: {data.max_value?.toExponential(4)}</div>
          {data.max_displacement !== undefined && <div>Max Displacement: {data.max_displacement?.toExponential(4)}</div>}
          {data.solve_time !== undefined && <div>Solve Time: {data.solve_time?.toFixed(3)}s</div>}
          {data.n_dofs && <div>DOFs: {data.n_dofs}</div>}
          {data.tool && <div>Solver: {data.tool}</div>}
        </div>
      )}
    </div>
  );
}
