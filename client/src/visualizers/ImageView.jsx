import React, { useState } from 'react';

const ACCENT = '#f472b6';

export default function ImageView({ data }) {
  const [tab, setTab] = useState('image');

  if (!data || !data.image_base64) {
    return <div style={{ color: '#8888a0', padding: 24 }}>No image data to display</div>;
  }

  const mimeType = data.image_format === 'svg' ? 'svg+xml' : data.image_format || 'png';
  const dataUrl = `data:image/${mimeType};base64,${data.image_base64}`;

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = dataUrl;
    link.download = `plot.${data.image_format || 'png'}`;
    link.click();
  };

  const tabs = ['image', 'info'];

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{
        display: 'flex', gap: 2, padding: '8px 16px',
        background: '#12121a', borderBottom: '1px solid #2a2a3a',
        alignItems: 'center',
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
        <div style={{ flex: 1 }} />
        <button
          onClick={handleDownload}
          style={{
            padding: '4px 12px', background: '#1a1a28', border: `1px solid ${ACCENT}`,
            borderRadius: 4, color: ACCENT, fontSize: 11, cursor: 'pointer',
          }}
        >Download</button>
      </div>

      {tab === 'image' && (
        <div style={{
          flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
          padding: 16, overflow: 'auto', background: '#0a0a0f',
        }}>
          <img
            src={dataUrl}
            alt="Matplotlib plot"
            style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
          />
        </div>
      )}

      {tab === 'info' && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace" }}>
          <h4 style={{ color: ACCENT, marginBottom: 12 }}>Plot Information</h4>
          <div>Tool: {data.tool}</div>
          <div>Type: {data.simulation_type}</div>
          <div>Format: {data.image_format}</div>
          <div>Figure Size: {data.figure_size?.join(' x ')} inches</div>
          <div>DPI: {data.dpi}</div>
        </div>
      )}
    </div>
  );
}
