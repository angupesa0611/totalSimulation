import React from 'react';

export default function RunButton({ onClick, disabled, loading, label = 'Run Simulation' }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      style={{
        width: '100%',
        padding: '12px 24px',
        background: disabled || loading ? '#2a2a3a' : '#6366f1',
        color: disabled || loading ? '#666' : '#fff',
        border: 'none',
        borderRadius: 8,
        fontSize: 14,
        fontWeight: 600,
        cursor: disabled || loading ? 'not-allowed' : 'pointer',
        transition: 'background 0.2s',
        marginTop: 8,
      }}
    >
      {loading ? 'Running...' : label}
    </button>
  );
}
