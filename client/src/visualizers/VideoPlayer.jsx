import React, { useState } from 'react';

const ACCENT = '#f472b6';

export default function VideoPlayer({ data }) {
  const [tab, setTab] = useState('video');

  if (!data || !data.video_url) {
    return <div style={{ color: '#8888a0', padding: 24 }}>No video data to display</div>;
  }

  const tabs = ['video', 'info'];

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
        <a
          href={data.video_url}
          download={data.video_filename}
          style={{
            padding: '4px 12px', background: '#1a1a28', border: `1px solid ${ACCENT}`,
            borderRadius: 4, color: ACCENT, fontSize: 11, cursor: 'pointer',
            textDecoration: 'none',
          }}
        >Download</a>
      </div>

      {tab === 'video' && (
        <div style={{
          flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
          padding: 16, background: '#0a0a0f',
        }}>
          <video
            src={data.video_url}
            controls
            autoPlay
            loop
            style={{ maxWidth: '100%', maxHeight: '100%', borderRadius: 8 }}
          />
        </div>
      )}

      {tab === 'info' && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace" }}>
          <h4 style={{ color: ACCENT, marginBottom: 12 }}>Animation Information</h4>
          <div>Tool: {data.tool}</div>
          <div>Type: {data.simulation_type}</div>
          <div>Format: {data.format}</div>
          <div>Quality: {data.quality}</div>
          <div>File: {data.video_filename}</div>
          {data.file_size_bytes && <div>Size: {(data.file_size_bytes / 1024 / 1024).toFixed(2)} MB</div>}
        </div>
      )}
    </div>
  );
}
