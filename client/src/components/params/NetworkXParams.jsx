import React from 'react';
import { InputField, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function NetworkXParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'graph_analysis';

  const textareaStyle = {
    width: '100%', background: theme.colors.bgTertiary,
    border: `1px solid ${theme.colors.border}`, borderRadius: 4,
    color: theme.colors.text, padding: 8, fontSize: 12,
    fontFamily: theme.fonts.mono, resize: 'vertical',
  };

  return (
    <>
      <DropdownSelect
        label="Analysis Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'graph_analysis', label: 'Graph Analysis' },
          { value: 'shortest_path', label: 'Shortest Path' },
          { value: 'centrality', label: 'Centrality Measures' },
          { value: 'community_detection', label: 'Community Detection' },
          { value: 'max_flow', label: 'Maximum Flow' },
        ]}
      />

      <div style={{ marginTop: 8 }}>
        <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
          Nodes (JSON array of node IDs, or "karate_club")
        </label>
        <textarea
          value={p.nodes || JSON.stringify([0, 1, 2, 3, 4], null, 2)}
          onChange={(e) => update('nodes', e.target.value)}
          rows={3}
          style={textareaStyle}
        />
      </div>

      <div style={{ marginTop: 8 }}>
        <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
          Edges (JSON array of [source, target] or [source, target, weight])
        </label>
        <textarea
          value={p.edges || JSON.stringify([[0,1],[1,2],[2,3],[3,4],[4,0],[0,2]], null, 2)}
          onChange={(e) => update('edges', e.target.value)}
          rows={4}
          style={textareaStyle}
        />
      </div>

      <DropdownSelect
        label="Directed Graph"
        value={String(p.directed ?? false)}
        onChange={(v) => update('directed', v === 'true')}
        options={[
          { value: 'false', label: 'Undirected' },
          { value: 'true', label: 'Directed' },
        ]}
      />

      {simType === 'shortest_path' && (
        <>
          <InputField
            label="Source Node"
            value={p.source_node ?? 0}
            onChange={(v) => update('source_node', isNaN(Number(v)) ? v : Number(v))}
            placeholder="0"
          />
          <InputField
            label="Target Node"
            value={p.target_node ?? 4}
            onChange={(v) => update('target_node', isNaN(Number(v)) ? v : Number(v))}
            placeholder="4"
          />
          <DropdownSelect
            label="Algorithm"
            value={p.algorithm || 'dijkstra'}
            onChange={(v) => update('algorithm', v)}
            options={[
              { value: 'dijkstra', label: 'Dijkstra' },
              { value: 'bellman_ford', label: 'Bellman-Ford' },
              { value: 'astar', label: 'A*' },
            ]}
          />
        </>
      )}

      {simType === 'centrality' && (
        <DropdownSelect
          label="Centrality Metric"
          value={p.metric || 'degree'}
          onChange={(v) => update('metric', v)}
          options={[
            { value: 'degree', label: 'Degree' },
            { value: 'betweenness', label: 'Betweenness' },
            { value: 'closeness', label: 'Closeness' },
            { value: 'eigenvector', label: 'Eigenvector' },
            { value: 'pagerank', label: 'PageRank' },
          ]}
        />
      )}

      {simType === 'community_detection' && (
        <DropdownSelect
          label="Algorithm"
          value={p.algorithm || 'louvain'}
          onChange={(v) => update('algorithm', v)}
          options={[
            { value: 'louvain', label: 'Louvain' },
            { value: 'girvan_newman', label: 'Girvan-Newman' },
            { value: 'label_propagation', label: 'Label Propagation' },
          ]}
        />
      )}

      {simType === 'max_flow' && (
        <>
          <InputField
            label="Source Node"
            value={p.source_node ?? 0}
            onChange={(v) => update('source_node', isNaN(Number(v)) ? v : Number(v))}
            placeholder="0"
          />
          <InputField
            label="Sink Node"
            value={p.sink_node ?? 4}
            onChange={(v) => update('sink_node', isNaN(Number(v)) ? v : Number(v))}
            placeholder="4"
          />
        </>
      )}
    </>
  );
}
