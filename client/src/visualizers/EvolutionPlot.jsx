import React, { useMemo, useState } from 'react';
import Plot from 'react-plotly.js';

const ACCENT = '#84cc16';
const COLORS = ['#84cc16', '#a3e635', '#bef264', '#d9f99d', '#65a30d', '#4d7c0f', '#365314'];

export default function EvolutionPlot({ data }) {
  const [tab, setTab] = useState('sfs');

  if (!data) {
    return <div style={{ color: '#8888a0', padding: 24 }}>No evolution data to display</div>;
  }

  const tabs = useMemo(() => {
    const t = [];
    if (data.allele_frequencies) t.push('sfs');
    if (data.windowed_diversity) t.push('diversity');
    if (data.windowed_tajimas_d) t.push('tajimas_d');
    if (data.population_sizes) t.push('demography');
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

      {tab === 'sfs' && data.allele_frequencies && (
        <div style={{ flex: 1 }}>
          <Plot
            data={[{
              x: data.allele_frequencies.bins,
              y: data.allele_frequencies.counts,
              type: 'bar',
              marker: { color: ACCENT, line: { color: '#65a30d', width: 0.5 } },
              name: 'Site Frequency Spectrum',
            }]}
            layout={{
              ...darkLayout,
              title: { text: 'Site Frequency Spectrum (SFS)', font: { size: 14 } },
              xaxis: { ...darkLayout.xaxis, title: 'Derived Allele Count' },
              yaxis: { ...darkLayout.yaxis, title: 'Number of Sites' },
              bargap: 0.05,
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {tab === 'diversity' && data.windowed_diversity && (
        <div style={{ flex: 1 }}>
          <Plot
            data={[{
              x: data.windowed_diversity.positions,
              y: data.windowed_diversity.pi,
              type: 'scatter',
              mode: 'lines+markers',
              name: 'Nucleotide Diversity (pi)',
              line: { color: ACCENT, width: 2 },
              marker: { size: 4, color: ACCENT },
            }]}
            layout={{
              ...darkLayout,
              title: { text: 'Windowed Nucleotide Diversity', font: { size: 14 } },
              xaxis: { ...darkLayout.xaxis, title: 'Genomic Position (bp)' },
              yaxis: { ...darkLayout.yaxis, title: 'pi' },
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {tab === 'tajimas_d' && data.windowed_tajimas_d && (
        <div style={{ flex: 1 }}>
          <Plot
            data={[
              {
                x: data.windowed_tajimas_d.positions,
                y: data.windowed_tajimas_d.D,
                type: 'scatter',
                mode: 'lines+markers',
                name: "Tajima's D",
                line: { color: '#a3e635', width: 2 },
                marker: { size: 4, color: '#a3e635' },
              },
              {
                x: [data.windowed_tajimas_d.positions[0], data.windowed_tajimas_d.positions[data.windowed_tajimas_d.positions.length - 1]],
                y: [0, 0],
                type: 'scatter',
                mode: 'lines',
                name: 'Neutral (D=0)',
                line: { color: '#8888a0', width: 1, dash: 'dash' },
              },
            ]}
            layout={{
              ...darkLayout,
              title: { text: "Windowed Tajima's D", font: { size: 14 } },
              xaxis: { ...darkLayout.xaxis, title: 'Genomic Position (bp)' },
              yaxis: { ...darkLayout.yaxis, title: "Tajima's D" },
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {tab === 'demography' && data.population_sizes && (
        <div style={{ flex: 1 }}>
          <Plot
            data={[{
              x: data.population_sizes.map(p => p.time),
              y: data.population_sizes.map(p => p.size),
              type: 'scatter',
              mode: 'lines+markers',
              name: 'Population Size',
              line: { color: ACCENT, width: 2, shape: 'hv' },
              marker: { size: 6, color: ACCENT },
            }]}
            layout={{
              ...darkLayout,
              title: { text: 'Demographic History', font: { size: 14 } },
              xaxis: { ...darkLayout.xaxis, title: 'Time (generations ago)', autorange: 'reversed' },
              yaxis: { ...darkLayout.yaxis, title: 'Population Size (Ne)', type: 'log' },
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {tab === 'info' && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace" }}>
          <h4 style={{ color: ACCENT, marginBottom: 12 }}>Simulation Info</h4>
          <div>Simulation Type: {data.simulation_type}</div>
          <div>Samples: {data.n_samples}</div>
          <div>Sequence Length: {data.sequence_length?.toLocaleString()} bp</div>
          <div>Trees: {data.n_trees}</div>
          <div>Mutations: {data.n_mutations}</div>
          <div>Mean TMRCA: {data.mean_tmrca?.toFixed(2)}</div>
          <div>Population Size: {data.population_size?.toLocaleString()}</div>
          {data.selection_coefficient !== undefined && (
            <div>Selection Coefficient: {data.selection_coefficient}</div>
          )}
          {data.sweep_position !== undefined && (
            <div>Sweep Position: {data.sweep_position?.toLocaleString()} bp</div>
          )}
        </div>
      )}
    </div>
  );
}
