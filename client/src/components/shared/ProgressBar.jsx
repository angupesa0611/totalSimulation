import React from 'react';

export default function ProgressBar({ progress = 0, message = '', status = '', isStartingWorker = false }) {
  const pct = Math.round(progress * 100);
  const barColor = isStartingWorker ? '#f59e0b'
    : status === 'FAILURE' ? '#ef4444'
    : status === 'SUCCESS' ? '#22c55e'
    : '#6366f1';

  const displayMessage = isStartingWorker ? 'Starting worker container...' : (message || status);

  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: isStartingWorker ? '#f59e0b' : '#8888a0', marginBottom: 4 }}>
        <span>{displayMessage}</span>
        <span>{isStartingWorker ? '' : `${pct}%`}</span>
      </div>
      <div style={{ width: '100%', height: 6, background: '#1a1a28', borderRadius: 3, overflow: 'hidden' }}>
        <div
          style={{
            width: isStartingWorker ? '100%' : `${pct}%`,
            height: '100%',
            background: barColor,
            borderRadius: 3,
            transition: 'width 0.3s ease',
            ...(isStartingWorker ? { animation: 'pulse 1.5s ease-in-out infinite', opacity: 0.7 } : {}),
          }}
        />
      </div>
      {isStartingWorker && (
        <style>{`@keyframes pulse { 0%, 100% { opacity: 0.4; } 50% { opacity: 0.9; } }`}</style>
      )}
    </div>
  );
}
