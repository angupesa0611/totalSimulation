import React from 'react';

export default function SliderParam({ label, value, onChange, min = 0, max = 100, step = 1, disabled }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <label style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: '#8888a0', marginBottom: 4 }}>
        <span>{label}</span>
        <span style={{ color: '#e0e0e0', fontFamily: 'monospace' }}>{value}</span>
      </label>
      <input
        type="range"
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        min={min}
        max={max}
        step={step}
        disabled={disabled}
        style={{ width: '100%', accentColor: '#6366f1' }}
      />
    </div>
  );
}
