import React, { useMemo, useState } from 'react';
import Plot from 'react-plotly.js';

const ACCENT = '#0ea5e9';

export default function ChemPlot({ data }) {
  const [tab, setTab] = useState('main');

  if (!data) {
    return <div style={{ color: '#8888a0', padding: 24 }}>No data to display</div>;
  }

  const simType = data.simulation_type || 'descriptors';

  const tabs = useMemo(() => {
    const t = [];
    if (simType === 'descriptors') t.push('descriptors');
    if (simType === 'conformer_3d' && data.conformers) t.push('conformer');
    if (simType === 'fingerprint') t.push('fingerprint');
    if (simType === 'similarity' && data.similarity_scores) t.push('similarity');
    t.push('info');
    return t;
  }, [data, simType]);

  const darkLayout = {
    paper_bgcolor: '#0a0a0f',
    plot_bgcolor: '#12121a',
    font: { color: '#e0e0e0', family: "'Inter', sans-serif" },
    margin: { t: 40, r: 30, b: 50, l: 60 },
    xaxis: { gridcolor: '#2a2a3a', zerolinecolor: '#2a2a3a' },
    yaxis: { gridcolor: '#2a2a3a', zerolinecolor: '#2a2a3a' },
    legend: { bgcolor: 'transparent', font: { color: '#8888a0' } },
  };

  // Parse 3D coordinates from atom_coords_pyscf for conformer visualization
  const conformerTrace = useMemo(() => {
    if (simType !== 'conformer_3d' || !data.conformers || !data.conformers[0]) return null;

    const bestConf = data.conformers[0];
    const coords = bestConf.atom_coords_pyscf;
    if (!coords) return null;

    const atoms = coords.split(';').map(a => a.trim().split(/\s+/));
    const x = [], y = [], z = [], text = [];
    const colors = [];
    const colorMap = { H: '#ffffff', C: '#909090', N: '#3050F8', O: '#FF0D0D', S: '#FFFF30', F: '#90E050', Cl: '#1FF01F', Br: '#A62929' };

    atoms.forEach(parts => {
      if (parts.length >= 4) {
        const symbol = parts[0];
        x.push(parseFloat(parts[1]));
        y.push(parseFloat(parts[2]));
        z.push(parseFloat(parts[3]));
        text.push(symbol);
        colors.push(colorMap[symbol] || ACCENT);
      }
    });

    return { x, y, z, text, colors };
  }, [data, simType]);

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

      {activeTab === 'descriptors' && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace", overflowY: 'auto', flex: 1 }}>
          <h4 style={{ color: ACCENT, marginBottom: 16 }}>Molecular Descriptors — {data.smiles}</h4>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <tbody>
              {[
                ['Formula', data.formula],
                ['Molecular Weight', data.molecular_weight?.toFixed(2) + ' Da'],
                ['LogP', data.logp?.toFixed(2)],
                ['H-Bond Donors', data.hbd],
                ['H-Bond Acceptors', data.hba],
                ['TPSA', data.tpsa?.toFixed(1) + ' Å²'],
                ['Rotatable Bonds', data.rotatable_bonds],
                ['Ring Count', data.ring_count],
              ].map(([label, value]) => (
                <tr key={label} style={{ borderBottom: '1px solid #2a2a3a' }}>
                  <td style={{ padding: '8px 12px', color: '#8888a0' }}>{label}</td>
                  <td style={{ padding: '8px 12px', color: '#e0e0e0', fontWeight: 600 }}>{value}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {data.atom_coords_pyscf && (
            <div style={{ marginTop: 16, color: ACCENT, fontSize: 11 }}>
              PySCF coordinates available for pipeline coupling
            </div>
          )}
        </div>
      )}

      {activeTab === 'conformer' && conformerTrace && (
        <div style={{ flex: 1 }}>
          <Plot
            data={[{
              x: conformerTrace.x,
              y: conformerTrace.y,
              z: conformerTrace.z,
              text: conformerTrace.text,
              type: 'scatter3d',
              mode: 'markers+text',
              marker: { size: 8, color: conformerTrace.colors, opacity: 0.9 },
              textposition: 'top center',
              textfont: { size: 10, color: '#8888a0' },
            }]}
            layout={{
              ...darkLayout,
              title: { text: `3D Conformer — ${data.smiles} (E=${data.conformers[0].energy?.toFixed(2)} kcal/mol)`, font: { size: 14 } },
              scene: {
                xaxis: { gridcolor: '#2a2a3a', title: 'X (Å)' },
                yaxis: { gridcolor: '#2a2a3a', title: 'Y (Å)' },
                zaxis: { gridcolor: '#2a2a3a', title: 'Z (Å)' },
                bgcolor: '#0a0a0f',
              },
              margin: { t: 50, r: 10, b: 10, l: 10 },
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {activeTab === 'fingerprint' && (
        <div style={{ flex: 1 }}>
          <Plot
            data={[{
              x: [data.fingerprint_type || 'morgan'],
              y: [data.density || 0],
              type: 'bar',
              marker: { color: ACCENT },
              text: [`${(data.density * 100).toFixed(1)}%`],
              textposition: 'auto',
            }]}
            layout={{
              ...darkLayout,
              title: { text: `${data.fingerprint_type?.toUpperCase()} Fingerprint — ${data.smiles}`, font: { size: 14 } },
              xaxis: { ...darkLayout.xaxis, title: 'Fingerprint Type' },
              yaxis: { ...darkLayout.yaxis, title: 'Bit Density', range: [0, 1] },
              annotations: [{
                text: `${data.bits_on?.length || 0} / ${data.n_bits || 0} bits ON`,
                xref: 'paper', yref: 'paper', x: 0.5, y: -0.15,
                showarrow: false, font: { color: '#8888a0', size: 12 },
              }],
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {activeTab === 'similarity' && data.similarity_scores && (
        <div style={{ flex: 1 }}>
          <Plot
            data={[{
              x: data.targets || [],
              y: data.similarity_scores,
              type: 'bar',
              marker: {
                color: data.similarity_scores.map(s => {
                  if (s > 0.7) return '#22c55e';
                  if (s > 0.4) return '#f59e0b';
                  return '#ef4444';
                }),
              },
              text: data.similarity_scores.map(s => s.toFixed(3)),
              textposition: 'auto',
            }]}
            layout={{
              ...darkLayout,
              title: { text: `Tanimoto Similarity to ${data.query}`, font: { size: 14 } },
              xaxis: { ...darkLayout.xaxis, title: 'Target SMILES', tickangle: -45 },
              yaxis: { ...darkLayout.yaxis, title: 'Similarity', range: [0, 1] },
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {activeTab === 'info' && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace" }}>
          <h4 style={{ color: ACCENT, marginBottom: 12 }}>RDKit Analysis Info</h4>
          <div>Tool: {data.tool}</div>
          <div>Type: {data.simulation_type}</div>
          <div>SMILES: {data.smiles}</div>
          {data.n_conformers !== undefined && <div>Conformers: {data.n_conformers}</div>}
          {data.atom_coords_pyscf && (
            <div style={{ marginTop: 8, color: ACCENT }}>PySCF coordinates ready for pipeline coupling</div>
          )}
        </div>
      )}
    </div>
  );
}
