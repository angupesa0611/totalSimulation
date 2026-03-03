import React, { useMemo, useState } from 'react';
import Plot from 'react-plotly.js';
import theme from '../theme.json';

export default function AnalysisPlot({ data }) {
  if (!data) {
    return <div style={{ color: theme.colors.textSecondary, padding: 24 }}>No analysis data</div>;
  }

  const analysisType = data.analysis_type || 'rmsd';

  const plotProps = useMemo(() => {
    switch (analysisType) {
      case 'rmsd':
        return {
          traces: [{
            x: data.times,
            y: data.rmsd,
            type: 'scatter',
            mode: 'lines',
            name: 'RMSD',
            line: { color: '#ec4899', width: 2 },
          }],
          title: 'RMSD vs Frame',
          yaxis: 'RMSD (Å)',
          annotations: data.mean_rmsd != null ? [{
            text: `Mean: ${data.mean_rmsd.toFixed(3)} Å`,
            xref: 'paper', yref: 'paper',
            x: 1, y: 1.08, showarrow: false,
            font: { size: 11, color: theme.colors.textSecondary },
          }] : [],
        };

      case 'rmsf':
        return {
          traces: [{
            x: data.atom_indices,
            y: data.rmsf,
            type: 'bar',
            name: 'RMSF',
            marker: { color: '#ec4899' },
          }],
          title: 'RMSF per Atom',
          yaxis: 'RMSF (Å)',
          xaxis: 'Atom Index',
          annotations: [],
        };

      case 'rg':
        return {
          traces: [{
            x: data.times,
            y: data.rg,
            type: 'scatter',
            mode: 'lines',
            name: 'Rg',
            line: { color: '#14b8a6', width: 2 },
          }],
          title: 'Radius of Gyration vs Frame',
          yaxis: 'Rg (Å)',
          annotations: data.mean_rg != null ? [{
            text: `Mean: ${data.mean_rg.toFixed(3)} Å`,
            xref: 'paper', yref: 'paper',
            x: 1, y: 1.08, showarrow: false,
            font: { size: 11, color: theme.colors.textSecondary },
          }] : [],
        };

      case 'contacts':
        return {
          traces: [{
            z: data.contact_map,
            type: 'heatmap',
            colorscale: [[0, '#0a0a0f'], [1, '#ec4899']],
            showscale: false,
          }],
          title: 'Contact Map (Last Frame)',
          yaxis: 'Atom',
          xaxis: 'Atom',
          annotations: [],
        };

      case 'ramachandran':
        return {
          traces: [{
            x: data.phi,
            y: data.psi,
            type: 'scatter',
            mode: 'markers',
            name: 'Dihedrals',
            marker: { color: '#6366f1', size: 4, opacity: 0.6 },
          }],
          title: 'Ramachandran Plot',
          yaxis: 'Psi (°)',
          xaxis: 'Phi (°)',
          annotations: [],
        };

      case 'hbonds':
        return {
          traces: [{
            x: data.times,
            y: data.hbond_count,
            type: 'scatter',
            mode: 'lines',
            name: 'H-bonds',
            line: { color: '#f59e0b', width: 2 },
          }],
          title: 'Hydrogen Bond Count vs Frame',
          yaxis: 'H-bond Count',
          annotations: data.mean_hbonds != null ? [{
            text: `Mean: ${data.mean_hbonds.toFixed(1)}`,
            xref: 'paper', yref: 'paper',
            x: 1, y: 1.08, showarrow: false,
            font: { size: 11, color: theme.colors.textSecondary },
          }] : [],
        };

      default:
        return { traces: [], title: 'Analysis', yaxis: '', annotations: [] };
    }
  }, [data, analysisType]);

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '8px 16px', borderBottom: `1px solid ${theme.colors.border}`, display: 'flex', alignItems: 'center', gap: 12 }}>
        <span style={{ fontSize: 13, color: theme.colors.text, fontWeight: 500 }}>
          {analysisType.toUpperCase()} Analysis
        </span>
        <span style={{ fontSize: 11, color: theme.colors.textSecondary }}>
          {data.n_frames} frames, {data.n_atoms} atoms
        </span>
        {data.source_job_id && (
          <span style={{ fontSize: 10, color: theme.colors.textSecondary, fontFamily: theme.fonts.mono }}>
            Source: {data.source_job_id.slice(0, 8)}...
          </span>
        )}
      </div>

      <div style={{ flex: 1 }}>
        <Plot
          data={plotProps.traces}
          layout={{
            title: { text: plotProps.title, font: { color: theme.colors.text, size: 16 } },
            xaxis: {
              title: plotProps.xaxis || 'Frame',
              color: theme.colors.textSecondary,
              gridcolor: theme.colors.border,
            },
            yaxis: {
              title: plotProps.yaxis,
              color: theme.colors.textSecondary,
              gridcolor: theme.colors.border,
            },
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: theme.colors.text },
            margin: { t: 50, r: 30, b: 50, l: 70 },
            autosize: true,
            annotations: plotProps.annotations,
          }}
          config={{ responsive: true, displaylogo: false }}
          style={{ width: '100%', height: '100%' }}
          useResizeHandler
        />
      </div>
    </div>
  );
}
