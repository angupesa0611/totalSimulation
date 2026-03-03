import React from 'react';
import theme from '../../theme.json';

export default function AlphaFoldParams() {
  return (
    <div style={{
      padding: 16,
      background: '#1a0f0a',
      borderRadius: 8,
      border: '1px solid #f59e0b33',
    }}>
      <div style={{
        fontSize: 13,
        fontWeight: 600,
        color: '#f59e0b',
        marginBottom: 8,
        display: 'flex',
        alignItems: 'center',
        gap: 8,
      }}>
        DEFERRED — Storage Required
      </div>
      <p style={{ fontSize: 12, color: theme.colors.textSecondary, margin: '0 0 12px', lineHeight: 1.5 }}>
        AlphaFold requires ~500 GB for the reduced database (2.2 TB full).
        ColabFold MMseqs2 (~100 GB) will be evaluated when storage is available.
      </p>
      <div style={{ fontSize: 12, color: theme.colors.text, lineHeight: 1.8 }}>
        <div><strong>PyRosetta</strong> — Ab initio folding, docking, protein design (Phase 10)</div>
        <div><strong>OpenMM</strong> — Energy minimization and MD refinement</div>
      </div>
    </div>
  );
}
