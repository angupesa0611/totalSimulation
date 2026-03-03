import React from 'react';
import theme from '../../theme.json';

export default function PyRosettaParams() {
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
        DEFERRED — Academic License Required
      </div>
      <p style={{ fontSize: 12, color: theme.colors.textSecondary, margin: '0 0 12px', lineHeight: 1.5 }}>
        PyRosetta requires an academic license obtained from PyRosetta.org.
        Use the open-source alternatives below for structural biology tasks.
      </p>
      <div style={{ fontSize: 12, color: theme.colors.text, lineHeight: 1.8 }}>
        <div><strong>Capabilities</strong> (when enabled):</div>
        <div style={{ paddingLeft: 8 }}>Ab initio folding, homology modeling, ligand docking, protein design</div>
      </div>
      <div style={{ fontSize: 12, color: theme.colors.text, lineHeight: 1.8, marginTop: 8 }}>
        <div><strong>OpenMM</strong> — Energy minimization and MD refinement</div>
        <div><strong>AlphaFold</strong> — Deep learning structure prediction (also deferred)</div>
      </div>
    </div>
  );
}
