import React from 'react';
import theme from '../../theme.json';

export default function HelpButton({ onClick, title }) {
  return (
    <button
      onClick={onClick}
      title={title || 'Open documentation'}
      style={{
        width: 20,
        height: 20,
        borderRadius: '50%',
        border: `1px solid ${theme.colors.accent}`,
        background: 'transparent',
        color: theme.colors.accent,
        fontSize: 11,
        fontWeight: 700,
        cursor: 'pointer',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 0,
        lineHeight: 1,
        flexShrink: 0,
        transition: 'box-shadow 0.15s',
      }}
      onMouseEnter={e => e.target.style.boxShadow = `0 0 6px ${theme.colors.accent}66`}
      onMouseLeave={e => e.target.style.boxShadow = 'none'}
    >
      ?
    </button>
  );
}
