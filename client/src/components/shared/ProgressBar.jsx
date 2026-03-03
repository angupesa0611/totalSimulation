import React from 'react';

export default function ProgressBar({ progress = 0, message = '', status = '' }) {
  const pct = Math.round(progress * 100);
  const barColor = status === 'FAILURE' ? '#ef4444' : status === 'SUCCESS' ? '#22c55e' : '#6366f1';

  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: '#8888a0', marginBottom: 4 }}>
        <span>{message || status}</span>
        <span>{pct}%</span>
      </div>
      <div style={{ width: '100%', height: 6, background: '#1a1a28', borderRadius: 3, overflow: 'hidden' }}>
        <div
          style={{
            width: `${pct}%`,
            height: '100%',
            background: barColor,
            borderRadius: 3,
            transition: 'width 0.3s ease',
          }}
        />
      </div>
    </div>
  );
}
