import React, { useMemo, useState } from 'react';
import Plot from 'react-plotly.js';

const ACCENT = '#f43f5e';
const COLORS = ['#f43f5e', '#fb7185', '#fda4af', '#fecdd3', '#e11d48', '#be123c', '#9f1239'];

export default function NeuralPlot({ data }) {
  const [tab, setTab] = useState('raster');

  if (!data) {
    return <div style={{ color: '#8888a0', padding: 24 }}>No neural data to display</div>;
  }

  const tabs = ['raster', 'voltage', 'rates', 'info'];

  const rasterTrace = useMemo(() => {
    if (!data.spike_trains?.times_ms || !data.spike_trains?.neuron_ids) return [];

    const times = data.spike_trains.times_ms;
    const ids = data.spike_trains.neuron_ids;

    // Use scattergl for large datasets
    const useGL = times.length > 10000;

    return [{
      x: times,
      y: ids,
      type: useGL ? 'scattergl' : 'scatter',
      mode: 'markers',
      marker: {
        size: 1.5,
        color: ACCENT,
        opacity: 0.7,
      },
      name: 'Spikes',
    }];
  }, [data]);

  const voltageTraces = useMemo(() => {
    if (!data.voltage_traces?.times_ms || !data.voltage_traces?.neurons) return [];

    const times = data.voltage_traces.times_ms;
    return Object.entries(data.voltage_traces.neurons).map(([id, values], i) => ({
      x: times,
      y: values,
      type: 'scatter',
      mode: 'lines',
      name: `Neuron ${id}`,
      line: { color: COLORS[i % COLORS.length], width: 1 },
    }));
  }, [data]);

  const rateTrace = useMemo(() => {
    if (!data.firing_rates?.per_neuron) return [];

    const rates = data.firing_rates.per_neuron;
    // Histogram of firing rates
    return [{
      x: rates,
      type: 'histogram',
      nbinsx: 30,
      marker: { color: ACCENT, line: { color: '#e11d48', width: 0.5 } },
      name: 'Firing Rate Distribution',
    }];
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
          >{t}</button>
        ))}
      </div>

      {tab === 'raster' && rasterTrace.length > 0 && (
        <div style={{ flex: 1 }}>
          <Plot
            data={rasterTrace}
            layout={{
              ...darkLayout,
              title: { text: `${data.tool === 'brian2' ? 'Brian2' : 'NEST'} — Spike Raster`, font: { size: 14 } },
              xaxis: { ...darkLayout.xaxis, title: 'Time (ms)' },
              yaxis: { ...darkLayout.yaxis, title: 'Neuron ID' },
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {tab === 'raster' && rasterTrace.length === 0 && (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#8888a0' }}>
          No spikes recorded
        </div>
      )}

      {tab === 'voltage' && (
        <div style={{ flex: 1 }}>
          {voltageTraces.length > 0 ? (
            <Plot
              data={voltageTraces}
              layout={{
                ...darkLayout,
                title: { text: 'Membrane Voltage Traces', font: { size: 14 } },
                xaxis: { ...darkLayout.xaxis, title: 'Time (ms)' },
                yaxis: { ...darkLayout.yaxis, title: 'V (mV)' },
              }}
              style={{ width: '100%', height: '100%' }}
              useResizeHandler
              config={{ responsive: true }}
            />
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#8888a0' }}>
              No voltage traces recorded
            </div>
          )}
        </div>
      )}

      {tab === 'rates' && (
        <div style={{ flex: 1 }}>
          {rateTrace.length > 0 ? (
            <Plot
              data={rateTrace}
              layout={{
                ...darkLayout,
                title: { text: 'Firing Rate Distribution', font: { size: 14 } },
                xaxis: { ...darkLayout.xaxis, title: 'Firing Rate (Hz)' },
                yaxis: { ...darkLayout.yaxis, title: 'Count' },
                bargap: 0.05,
              }}
              style={{ width: '100%', height: '100%' }}
              useResizeHandler
              config={{ responsive: true }}
            />
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#8888a0' }}>
              No firing rate data
            </div>
          )}
        </div>
      )}

      {tab === 'info' && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace" }}>
          <h4 style={{ color: ACCENT, marginBottom: 12 }}>Simulation Info</h4>
          <div>Tool: {data.tool}</div>
          <div>Type: {data.simulation_type}</div>
          <div>Neurons: {data.n_neurons}</div>
          <div>Total Spikes: {data.n_spikes}</div>
          <div>Duration: {data.duration_ms} ms</div>
          {data.firing_rates?.mean_hz !== undefined && (
            <div>Mean Firing Rate: {data.firing_rates.mean_hz.toFixed(2)} Hz</div>
          )}
        </div>
      )}
    </div>
  );
}
