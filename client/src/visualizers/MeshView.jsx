import React, { useMemo, useState } from 'react';
import Plot from 'react-plotly.js';

const ACCENT = '#a78bfa';

export default function MeshView({ data }) {
  const [tab, setTab] = useState('mesh_3d');

  if (!data) {
    return <div style={{ color: '#8888a0', padding: 24 }}>No data to display</div>;
  }

  const tabs = ['mesh_3d', 'stats', 'info'];
  const activeTab = tabs.includes(tab) ? tab : tabs[0];

  const nodeTrace = useMemo(() => {
    if (!data.nodes || data.nodes.length === 0) return null;

    const x = data.nodes.map(n => n.x);
    const y = data.nodes.map(n => n.y);
    const z = data.nodes.map(n => n.z);

    return { x, y, z };
  }, [data]);

  const wireframeTraces = useMemo(() => {
    if (!data.elements || data.elements.length === 0 || !data.nodes) return [];

    const nodeMap = {};
    data.nodes.forEach(n => { nodeMap[n.id] = n; });

    const traces = [];
    const maxEdges = 2000;
    let edgeCount = 0;

    for (const elem of data.elements) {
      if (edgeCount >= maxEdges) break;
      const nodeIds = elem.node_ids;
      for (let i = 0; i < nodeIds.length && edgeCount < maxEdges; i++) {
        const n1 = nodeMap[nodeIds[i]];
        const n2 = nodeMap[nodeIds[(i + 1) % nodeIds.length]];
        if (n1 && n2) {
          traces.push({
            x: [n1.x, n2.x, null],
            y: [n1.y, n2.y, null],
            z: [n1.z, n2.z, null],
          });
          edgeCount++;
        }
      }
    }

    // Merge into single trace
    const x = [], y = [], z = [];
    traces.forEach(t => { x.push(...t.x); y.push(...t.y); z.push(...t.z); });
    return [{ x, y, z }];
  }, [data]);

  const darkLayout = {
    paper_bgcolor: '#0a0a0f',
    plot_bgcolor: '#12121a',
    font: { color: '#e0e0e0', family: "'Inter', sans-serif" },
  };

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

      {activeTab === 'mesh_3d' && (
        <div style={{ flex: 1 }}>
          <Plot
            data={[
              ...(nodeTrace ? [{
                x: nodeTrace.x,
                y: nodeTrace.y,
                z: nodeTrace.z,
                type: 'scatter3d',
                mode: 'markers',
                marker: { size: 2, color: ACCENT, opacity: 0.6 },
                name: 'Nodes',
              }] : []),
              ...wireframeTraces.map(wf => ({
                x: wf.x,
                y: wf.y,
                z: wf.z,
                type: 'scatter3d',
                mode: 'lines',
                line: { color: '#4a4a6a', width: 1 },
                name: 'Wireframe',
                showlegend: false,
              })),
            ]}
            layout={{
              ...darkLayout,
              title: { text: `${data.simulation_type} — ${data.n_nodes} nodes, ${data.n_elements} elements`, font: { size: 14 } },
              scene: {
                xaxis: { gridcolor: '#2a2a3a', title: 'X' },
                yaxis: { gridcolor: '#2a2a3a', title: 'Y' },
                zaxis: { gridcolor: '#2a2a3a', title: 'Z' },
                bgcolor: '#0a0a0f',
                aspectmode: 'data',
              },
              margin: { t: 50, r: 10, b: 10, l: 10 },
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {activeTab === 'stats' && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace", overflowY: 'auto', flex: 1 }}>
          <h4 style={{ color: ACCENT, marginBottom: 16 }}>Mesh Statistics</h4>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <tbody>
              {[
                ['Nodes', data.n_nodes],
                ['Elements', data.n_elements],
                ['Dimension', data.dimension],
                ['Element Type', data.element_type],
                ['Domain Min', data.bounds?.min?.join(', ')],
                ['Domain Max', data.bounds?.max?.join(', ')],
                ['Min Quality', data.mesh_quality?.min_quality?.toFixed(4)],
                ['Avg Quality', data.mesh_quality?.avg_quality?.toFixed(4)],
              ].filter(([, v]) => v !== undefined).map(([label, value]) => (
                <tr key={label} style={{ borderBottom: '1px solid #2a2a3a' }}>
                  <td style={{ padding: '8px 12px', color: '#8888a0' }}>{label}</td>
                  <td style={{ padding: '8px 12px', color: '#e0e0e0', fontWeight: 600 }}>{value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'info' && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace" }}>
          <h4 style={{ color: ACCENT, marginBottom: 12 }}>Gmsh Info</h4>
          <div>Tool: {data.tool}</div>
          <div>Type: {data.simulation_type}</div>
          <div>Nodes: {data.n_nodes}</div>
          <div>Elements: {data.n_elements}</div>
          {data.mesh_file_path && (
            <div style={{ marginTop: 8, color: ACCENT }}>Mesh file exported for FEniCS coupling</div>
          )}
        </div>
      )}
    </div>
  );
}
