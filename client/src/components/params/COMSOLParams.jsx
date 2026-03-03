import React from 'react';
import theme from '../../theme.json';

export default function COMSOLParams() {
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
        DEFERRED — License Required
      </div>
      <p style={{ fontSize: 12, color: theme.colors.textSecondary, margin: '0 0 12px', lineHeight: 1.5 }}>
        COMSOL requires a commercial license that is not currently available.
        Use the open-source alternatives below for equivalent functionality.
      </p>
      <div style={{ fontSize: 12, color: theme.colors.text, lineHeight: 1.8 }}>
        <div><strong>FEniCS</strong> — Custom PDE research (variational form)</div>
        <div><strong>Elmer</strong> — Built-in multiphysics (thermal-structural, EM)</div>
        <div><strong>Firedrake</strong> — High-performance FEM with PETSc backend</div>
      </div>
    </div>
  );
}
