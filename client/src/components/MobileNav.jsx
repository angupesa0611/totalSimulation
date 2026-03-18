import React from 'react';
import theme from '../theme.json';

const TABS = [
  { key: 'dashboard', label: 'Home' },
  { key: 'sweep', label: 'Sweep' },
  { key: 'docs', label: 'Docs' },
];

export default function MobileNav({ view, detailType, onNavigate }) {
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
        const isActive = tab.key === 'dashboard'
          ? view === 'dashboard'
          : tab.key === 'sweep'
            ? view === 'detail' && detailType === 'sweep'
            : false;

        // Show back arrow on Home tab when in detail view
        const showBackArrow = tab.key === 'dashboard' && view === 'detail';

        return (
          <button
            key={tab.key}
            onClick={() => onNavigate(tab.key)}
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
            {showBackArrow ? '\u2190 Back' : tab.label}
          </button>
        );
      })}
    </nav>
  );
}
