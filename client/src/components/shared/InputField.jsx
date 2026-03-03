import React from 'react';

export default function InputField({ label, value, onChange, type = 'text', step, min, max, placeholder, disabled }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <label style={{ display: 'block', fontSize: 12, color: '#8888a0', marginBottom: 4 }}>
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(type === 'number' ? parseFloat(e.target.value) : e.target.value)}
        step={step}
        min={min}
        max={max}
        placeholder={placeholder}
        disabled={disabled}
        style={{
          width: '100%',
          padding: '8px 12px',
          background: '#1a1a28',
          border: '1px solid #2a2a3a',
          borderRadius: 6,
          color: '#e0e0e0',
          fontSize: 14,
          outline: 'none',
        }}
      />
    </div>
  );
}
