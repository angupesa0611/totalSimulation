import React, { useMemo, useState } from 'react';
import Plot from 'react-plotly.js';

const ACCENT = '#fb923c';
const COMMUNITY_COLORS = ['#6366f1', '#22c55e', '#ef4444', '#f59e0b', '#06b6d4', '#ec4899', '#a855f7', '#14b8a6', '#84cc16', '#d946ef'];

export default function GraphView({ data }) {
  const [tab, setTab] = useState('graph');

  if (!data) {
    return <div style={{ color: '#8888a0', padding: 24 }}>No data to display</div>;
  }

  const darkLayout = {
    paper_bgcolor: '#0a0a0f',
    plot_bgcolor: '#12121a',
    font: { color: '#e0e0e0', family: "'Inter', sans-serif" },
    margin: { t: 40, r: 30, b: 50, l: 60 },
    xaxis: { gridcolor: '#2a2a3a', zerolinecolor: '#2a2a3a', showgrid: false, zeroline: false, showticklabels: false },
    yaxis: { gridcolor: '#2a2a3a', zerolinecolor: '#2a2a3a', showgrid: false, zeroline: false, showticklabels: false, scaleanchor: 'x' },
    legend: { bgcolor: 'transparent', font: { color: '#8888a0' } },
    showlegend: false,
  };

  const tabs = useMemo(() => {
    const t = ['graph'];
    if (data.simulation_type === 'shortest_path' && data.path) t.push('path');
    t.push('metrics');
    t.push('info');
    return t;
  }, [data]);

  // Build node colors based on communities or centrality
  const nodeColors = useMemo(() => {
    if (!data.layout) return {};
    const colors = {};

    if (data.communities) {
      data.communities.forEach((community, ci) => {
        community.forEach(node => {
          colors[String(node)] = COMMUNITY_COLORS[ci % COMMUNITY_COLORS.length];
        });
      });
    } else if (data.scores) {
      const values = Object.values(data.scores);
      const maxVal = Math.max(...values);
      const minVal = Math.min(...values);
      const range = maxVal - minVal || 1;
      Object.entries(data.scores).forEach(([node, score]) => {
        const t = (score - minVal) / range;
        colors[node] = `rgb(${Math.round(255 * t)}, ${Math.round(100 + 100 * (1 - t))}, ${Math.round(100)})`;
      });
    }
    return colors;
  }, [data]);

  // Build edge and node traces
  const graphTraces = useMemo(() => {
    if (!data.layout || !data.edges) return [];
    const traces = [];

    // Edge traces
    const edgeX = [];
    const edgeY = [];
    data.edges.forEach(([u, v]) => {
      const posU = data.layout[String(u)];
      const posV = data.layout[String(v)];
      if (posU && posV) {
        edgeX.push(posU[0], posV[0], null);
        edgeY.push(posU[1], posV[1], null);
      }
    });

    traces.push({
      x: edgeX, y: edgeY,
      type: 'scatter', mode: 'lines',
      line: { color: '#2a2a3a', width: 1 },
      hoverinfo: 'none',
    });

    // Node traces
    const nodeX = [];
    const nodeY = [];
    const nodeText = [];
    const nodeColor = [];
    const nodes = data.nodes || Object.keys(data.layout);

    nodes.forEach(n => {
      const pos = data.layout[String(n)];
      if (pos) {
        nodeX.push(pos[0]);
        nodeY.push(pos[1]);
        nodeText.push(String(n));
        nodeColor.push(nodeColors[String(n)] || ACCENT);
      }
    });

    traces.push({
      x: nodeX, y: nodeY,
      type: 'scatter', mode: 'markers+text',
      marker: { size: 10, color: nodeColor, line: { width: 1, color: '#0a0a0f' } },
      text: nodeText, textposition: 'top center',
      textfont: { size: 9, color: '#8888a0' },
    });

    return traces;
  }, [data, nodeColors]);

  // Path highlight trace
  const pathTrace = useMemo(() => {
    if (!data.path || !data.layout) return null;
    const pathX = [];
    const pathY = [];
    data.path.forEach(n => {
      const pos = data.layout[String(n)];
      if (pos) {
        pathX.push(pos[0]);
        pathY.push(pos[1]);
      }
    });
    return {
      x: pathX, y: pathY,
      type: 'scatter', mode: 'lines+markers',
      line: { color: '#ef4444', width: 3 },
      marker: { size: 12, color: '#ef4444' },
      name: 'Shortest Path',
    };
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

      {activeTab === 'graph' && graphTraces.length > 0 && (
        <div style={{ flex: 1 }}>
          <Plot
            data={graphTraces}
            layout={{
              ...darkLayout,
              title: {
                text: data.simulation_type === 'community_detection'
                  ? `Communities (${data.n_communities} found, Q=${data.modularity?.toFixed(3)})`
                  : data.simulation_type === 'centrality'
                    ? `${data.metric} Centrality`
                    : 'Graph',
                font: { size: 14 },
              },
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {activeTab === 'path' && pathTrace && (
        <div style={{ flex: 1 }}>
          <Plot
            data={[...graphTraces, pathTrace]}
            layout={{
              ...darkLayout,
              title: { text: `Shortest Path: ${data.path?.join(' → ')} (length: ${data.path_length?.toFixed(2)})`, font: { size: 14 } },
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {activeTab === 'metrics' && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace" }}>
          <h4 style={{ color: ACCENT, marginBottom: 12 }}>Graph Metrics</h4>
          {data.n_nodes !== undefined && <div>Nodes: {data.n_nodes}</div>}
          {data.n_edges !== undefined && <div>Edges: {data.n_edges}</div>}
          {data.density !== undefined && <div>Density: {data.density?.toFixed(4)}</div>}
          {data.diameter !== undefined && data.diameter !== null && <div>Diameter: {data.diameter}</div>}
          {data.avg_clustering !== undefined && <div>Avg Clustering: {data.avg_clustering?.toFixed(4)}</div>}
          {data.is_connected !== undefined && <div>Connected: {data.is_connected ? 'Yes' : 'No'}</div>}
          {data.components !== undefined && <div>Components: {data.components}</div>}
          {data.modularity !== undefined && <div>Modularity: {data.modularity?.toFixed(4)}</div>}
          {data.max_flow_value !== undefined && <div>Max Flow: {data.max_flow_value}</div>}
          {data.path_length !== undefined && <div>Path Length: {data.path_length?.toFixed(2)}</div>}

          {data.top_nodes && (
            <div style={{ marginTop: 12 }}>
              <div style={{ color: ACCENT, marginBottom: 4 }}>Top Nodes ({data.metric}):</div>
              {data.top_nodes.map((n, i) => (
                <div key={i}>{n}: {data.scores?.[n]?.toFixed(4)}</div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'info' && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace" }}>
          <h4 style={{ color: ACCENT, marginBottom: 12 }}>NetworkX Info</h4>
          <div>Tool: {data.tool}</div>
          <div>Type: {data.simulation_type}</div>
          {data.algorithm && <div>Algorithm: {data.algorithm}</div>}
          {data.metric && <div>Metric: {data.metric}</div>}
        </div>
      )}
    </div>
  );
}
