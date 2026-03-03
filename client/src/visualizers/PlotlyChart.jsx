import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';
import theme from '../theme.json';

const COLORS = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899', '#8b5cf6', '#14b8a6'];

export default function PlotlyChart({ data }) {
  const traces = useMemo(() => {
    if (!data || !data.expect || !data.times) return [];

    return Object.entries(data.expect).map(([key, values], i) => ({
      x: data.times,
      y: values,
      type: 'scatter',
      mode: 'lines',
      name: key,
      line: { color: COLORS[i % COLORS.length], width: 2 },
    }));
  }, [data]);

  if (!traces.length) {
    return <div style={{ color: '#8888a0', padding: 24 }}>No quantum data to display</div>;
  }

  const systemLabel = data.system_type === 'qubit_rabi' ? 'Rabi Oscillation'
    : data.system_type === 'spin_chain' ? 'Spin Chain'
    : data.system_type === 'jaynes_cummings' ? 'Jaynes-Cummings'
    : 'Quantum Simulation';

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <Plot
        data={traces}
        layout={{
          title: { text: systemLabel, font: { color: theme.colors.text, size: 16 } },
          xaxis: {
            title: 'Time',
            color: theme.colors.textSecondary,
            gridcolor: theme.colors.border,
            zerolinecolor: theme.colors.border,
          },
          yaxis: {
            title: 'Expectation Value',
            color: theme.colors.textSecondary,
            gridcolor: theme.colors.border,
            zerolinecolor: theme.colors.border,
          },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          font: { color: theme.colors.text, family: theme.fonts.sans },
          legend: { font: { color: theme.colors.text } },
          margin: { t: 50, r: 30, b: 50, l: 60 },
          autosize: true,
        }}
        config={{ responsive: true, displayModeBar: true, displaylogo: false }}
        style={{ width: '100%', height: '100%' }}
        useResizeHandler
      />
    </div>
  );
}
