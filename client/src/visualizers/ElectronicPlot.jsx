import React, { useMemo, useState } from 'react';
import Plot from 'react-plotly.js';
import theme from '../theme.json';

export default function ElectronicPlot({ data }) {
  const [activeTab, setActiveTab] = useState('orbitals');

  if (!data) {
    return <div style={{ color: theme.colors.textSecondary, padding: 24 }}>No electronic structure data</div>;
  }

  const orbitalTrace = useMemo(() => {
    if (!data.orbital_energies) return [];
    const energies = Array.isArray(data.orbital_energies[0])
      ? data.orbital_energies[0]  // UHF: take alpha
      : data.orbital_energies;
    const occ = Array.isArray(data.mo_occ?.[0])
      ? data.mo_occ[0]
      : (data.mo_occ || []);

    return [{
      type: 'bar',
      x: energies.map((_, i) => `MO ${i + 1}`),
      y: energies,
      marker: {
        color: energies.map((_, i) => (occ[i] > 0 ? '#6366f1' : '#ef4444')),
      },
      hovertemplate: '%{x}<br>Energy: %{y:.4f} Ha<extra></extra>',
    }];
  }, [data]);

  const chargeTrace = useMemo(() => {
    if (!data.mulliken_charges || !data.atom_labels) return [];
    return [{
      type: 'bar',
      x: data.atom_labels.map((l, i) => `${l}${i + 1}`),
      y: data.mulliken_charges,
      marker: {
        color: data.mulliken_charges.map(c => c >= 0 ? '#22c55e' : '#ef4444'),
      },
      hovertemplate: '%{x}<br>Charge: %{y:.4f}<extra></extra>',
    }];
  }, [data]);

  const tabs = ['orbitals', 'charges', 'info'];

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', gap: 4, padding: '8px 16px', borderBottom: `1px solid ${theme.colors.border}` }}>
        {tabs.map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '6px 16px',
              background: activeTab === tab ? theme.colors.bgTertiary : 'transparent',
              border: activeTab === tab ? `1px solid #06b6d4` : '1px solid transparent',
              borderRadius: 6,
              color: activeTab === tab ? theme.colors.text : theme.colors.textSecondary,
              fontSize: 13,
              cursor: 'pointer',
              textTransform: 'capitalize',
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      <div style={{ flex: 1, overflow: 'auto' }}>
        {activeTab === 'orbitals' && orbitalTrace.length > 0 && (
          <Plot
            data={orbitalTrace}
            layout={{
              title: { text: 'Molecular Orbital Energies', font: { color: theme.colors.text, size: 16 } },
              xaxis: { title: 'Orbital', color: theme.colors.textSecondary, gridcolor: theme.colors.border },
              yaxis: { title: 'Energy (Hartree)', color: theme.colors.textSecondary, gridcolor: theme.colors.border },
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
              font: { color: theme.colors.text },
              margin: { t: 50, r: 30, b: 80, l: 70 },
              autosize: true,
              annotations: [{
                text: 'Blue = occupied, Red = virtual',
                xref: 'paper', yref: 'paper',
                x: 1, y: 1.08, showarrow: false,
                font: { size: 11, color: theme.colors.textSecondary },
              }],
            }}
            config={{ responsive: true, displaylogo: false }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
          />
        )}

        {activeTab === 'charges' && chargeTrace.length > 0 && (
          <Plot
            data={chargeTrace}
            layout={{
              title: { text: 'Mulliken Charges', font: { color: theme.colors.text, size: 16 } },
              xaxis: { title: 'Atom', color: theme.colors.textSecondary, gridcolor: theme.colors.border },
              yaxis: { title: 'Charge (e)', color: theme.colors.textSecondary, gridcolor: theme.colors.border },
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
              font: { color: theme.colors.text },
              margin: { t: 50, r: 30, b: 50, l: 70 },
              autosize: true,
            }}
            config={{ responsive: true, displaylogo: false }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
          />
        )}

        {activeTab === 'info' && (
          <div style={{ padding: 24 }}>
            <h3 style={{ fontSize: 16, marginBottom: 16, color: theme.colors.text }}>Calculation Info</h3>
            <InfoRow label="Method" value={data.method?.toUpperCase()} />
            <InfoRow label="Basis Set" value={data.basis} />
            {data.xc_functional && <InfoRow label="XC Functional" value={data.xc_functional} />}
            <InfoRow label="Total Energy" value={`${data.total_energy?.toFixed(6)} Ha`} />
            <InfoRow label="Atoms" value={data.n_atoms} />
            <InfoRow label="Electrons" value={data.n_electrons} />
            <InfoRow label="Charge" value={data.charge} />
            <InfoRow label="Spin" value={data.spin} />
            {data.dipole_moment?.length > 0 && (
              <InfoRow
                label="Dipole (Debye)"
                value={`(${data.dipole_moment.map(d => d.toFixed(3)).join(', ')})`}
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function InfoRow({ label, value }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: `1px solid ${theme.colors.border}` }}>
      <span style={{ color: theme.colors.textSecondary, fontSize: 13 }}>{label}</span>
      <span style={{ color: theme.colors.text, fontSize: 13, fontFamily: theme.fonts.mono }}>{value ?? '—'}</span>
    </div>
  );
}
