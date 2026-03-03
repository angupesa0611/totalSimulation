import React from 'react';
import theme from '../theme.json';

const TABS = [
  { key: 'layers', label: 'Layers' },
  { key: 'tool', label: 'Tool' },
  { key: 'pipeline', label: 'Pipeline' },
  { key: 'sweep', label: 'Sweep' },
  { key: 'results', label: 'Results' },
];

export default function MobileNav({ mode, onModeChange, onToggleSidebar }) {
  return (
    <nav style={{
      position: 'fixed',
      bottom: 0,
      left: 0,
      right: 0,
      height: 56,
      background: theme.colors.bgSecondary,
      borderTop: `1px solid ${theme.colors.border}`,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-around',
      zIndex: 1000,
    }}>
      {TABS.map(tab => {
        const isActive = tab.key === 'layers' ? false : mode === tab.key;
        return (
          <button
            key={tab.key}
            onClick={() => {
              if (tab.key === 'layers') {
                onToggleSidebar();
              } else {
                onModeChange(tab.key);
              }
            }}
            style={{
              flex: 1,
              height: '100%',
              background: 'transparent',
              border: 'none',
              color: isActive ? theme.colors.accent : theme.colors.textSecondary,
              fontSize: 11,
              fontWeight: isActive ? 600 : 400,
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 2,
              borderTop: isActive ? `2px solid ${theme.colors.accent}` : '2px solid transparent',
            }}
          >
            {tab.label}
          </button>
        );
      })}
    </nav>
  );
}
