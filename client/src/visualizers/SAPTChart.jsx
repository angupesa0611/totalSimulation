import React, { useMemo, useState } from 'react';
import Plot from 'react-plotly.js';
import ElectronicPlot from './ElectronicPlot';
import theme from '../theme.json';

export default function SAPTChart({ data }) {
  if (!data) {
    return <div style={{ color: theme.colors.textSecondary, padding: 24 }}>No Psi4 data</div>;
  }

  // If not SAPT, fall back to ElectronicPlot
  if (!data.is_sapt) {
    return <ElectronicPlot data={data} />;
  }

  const sapt = data.sapt || {};

  const barTrace = useMemo(() => {
    const components = ['electrostatics', 'exchange', 'induction', 'dispersion'];
    const labels = ['Electrostatics', 'Exchange', 'Induction', 'Dispersion'];
    const colors = ['#6366f1', '#ef4444', '#f59e0b', '#22c55e'];

    const values = components.map(c => (sapt[c] || 0) * 627.509);  // Ha → kcal/mol

    return [{
      type: 'bar',
      x: labels,
      y: values,
      marker: {
        color: colors,
      },
      hovertemplate: '%{x}<br>%{y:.3f} kcal/mol<extra></extra>',
    }];
  }, [sapt]);

  const totalKcal = (sapt.interaction_energy || 0) * 627.509;

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{
        padding: '8px 16px',
        borderBottom: `1px solid ${theme.colors.border}`,
        display: 'flex',
        alignItems: 'center',
        gap: 12,
      }}>
        <span style={{ fontSize: 13, color: theme.colors.text, fontWeight: 500 }}>
          SAPT Energy Decomposition
        </span>
        <span style={{
          fontSize: 12,
          color: totalKcal < 0 ? '#22c55e' : '#ef4444',
          fontFamily: theme.fonts.mono,
        }}>
          Total: {totalKcal.toFixed(3)} kcal/mol
        </span>
      </div>

      <div style={{ flex: 1 }}>
        <Plot
          data={barTrace}
          layout={{
            title: {
              text: `${data.method?.toUpperCase()}/${data.basis} SAPT Decomposition`,
              font: { color: theme.colors.text, size: 16 },
            },
            xaxis: {
              color: theme.colors.textSecondary,
              gridcolor: theme.colors.border,
            },
            yaxis: {
              title: 'Energy (kcal/mol)',
              color: theme.colors.textSecondary,
              gridcolor: theme.colors.border,
              zeroline: true,
              zerolinecolor: theme.colors.border,
              zerolinewidth: 2,
            },
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: theme.colors.text },
            margin: { t: 50, r: 30, b: 50, l: 80 },
            autosize: true,
            shapes: [{
              type: 'line',
              x0: -0.5,
              x1: 3.5,
              y0: totalKcal,
              y1: totalKcal,
              line: {
                color: '#e0e0e0',
                width: 2,
                dash: 'dash',
              },
            }],
            annotations: [{
              text: `Net: ${totalKcal.toFixed(3)} kcal/mol`,
              x: 3.5,
              y: totalKcal,
              xanchor: 'right',
              showarrow: false,
              font: { size: 11, color: theme.colors.textSecondary },
            }],
          }}
          config={{ responsive: true, displaylogo: false }}
          style={{ width: '100%', height: '100%' }}
          useResizeHandler
        />
      </div>
    </div>
  );
}
