import React from 'react';
import { InputField, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function SymPyParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'symbolic_solve';

  return (
    <>
      <DropdownSelect
        label="Computation Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'symbolic_solve', label: 'Symbolic Solve' },
          { value: 'calculus', label: 'Calculus' },
          { value: 'matrix_algebra', label: 'Matrix Algebra' },
          { value: 'ode_solve', label: 'ODE Solve' },
          { value: 'code_generation', label: 'Code Generation' },
        ]}
      />

      {simType === 'symbolic_solve' && (
        <>
          <div style={{ marginTop: 8 }}>
            <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
              Equations (one per line)
            </label>
            <textarea
              value={(p.equations || []).join('\n')}
              onChange={(e) => update('equations', e.target.value.split('\n').filter(s => s.trim()))}
              placeholder="x**2 - 5*x + 6"
              rows={3}
              style={{
                width: '100%', background: theme.colors.bgTertiary,
                border: `1px solid ${theme.colors.border}`, borderRadius: 4,
                color: theme.colors.text, padding: 8, fontSize: 12,
                fontFamily: theme.fonts.mono, resize: 'vertical',
              }}
            />
          </div>
          <InputField
            label="Solve For"
            value={(p.solve_for || ['x']).join(', ')}
            onChange={(v) => update('solve_for', v.split(',').map(s => s.trim()).filter(Boolean))}
            placeholder="x"
          />
        </>
      )}

      {simType === 'calculus' && (
        <>
          <InputField
            label="Expression"
            value={p.expression || ''}
            onChange={(v) => update('expression', v)}
            placeholder="x**2 + sin(x)"
          />
          <DropdownSelect
            label="Operation"
            value={p.operation || 'differentiate'}
            onChange={(v) => update('operation', v)}
            options={[
              { value: 'differentiate', label: 'Differentiate' },
              { value: 'integrate', label: 'Integrate' },
              { value: 'limit', label: 'Limit' },
              { value: 'series', label: 'Series Expansion' },
            ]}
          />
          <InputField
            label="With Respect To"
            value={p.respect_to || 'x'}
            onChange={(v) => update('respect_to', v)}
          />
          {p.operation === 'series' && (
            <InputField
              label="Order"
              value={p.order ?? 6}
              onChange={(v) => update('order', parseInt(v) || 6)}
              type="number"
            />
          )}
        </>
      )}

      {simType === 'matrix_algebra' && (
        <>
          <div style={{ marginTop: 8 }}>
            <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
              Matrix (JSON 2D array)
            </label>
            <textarea
              value={JSON.stringify(p.matrix || [[1,0],[0,1]])}
              onChange={(e) => { try { update('matrix', JSON.parse(e.target.value)); } catch {} }}
              rows={3}
              style={{
                width: '100%', background: theme.colors.bgTertiary,
                border: `1px solid ${theme.colors.border}`, borderRadius: 4,
                color: theme.colors.text, padding: 8, fontSize: 12,
                fontFamily: theme.fonts.mono, resize: 'vertical',
              }}
            />
          </div>
          <DropdownSelect
            label="Operation"
            value={p.operation || 'eigenvalues'}
            onChange={(v) => update('operation', v)}
            options={[
              { value: 'eigenvalues', label: 'Eigenvalues' },
              { value: 'determinant', label: 'Determinant' },
              { value: 'inverse', label: 'Inverse' },
              { value: 'decomposition', label: 'LU Decomposition' },
            ]}
          />
        </>
      )}

      {simType === 'ode_solve' && (
        <>
          <InputField
            label="ODE"
            value={p.ode || ''}
            onChange={(v) => update('ode', v)}
            placeholder="f(x).diff(x) - f(x)"
          />
          <InputField
            label="Function Name"
            value={p.function || 'f'}
            onChange={(v) => update('function', v)}
          />
          <InputField
            label="Variable"
            value={p.variable || 'x'}
            onChange={(v) => update('variable', v)}
          />
        </>
      )}

      {simType === 'code_generation' && (
        <>
          <InputField
            label="Expression"
            value={p.expression || ''}
            onChange={(v) => update('expression', v)}
            placeholder="x**2 + y**2"
          />
          <DropdownSelect
            label="Target Language"
            value={p.target_language || 'python'}
            onChange={(v) => update('target_language', v)}
            options={[
              { value: 'python', label: 'Python' },
              { value: 'c', label: 'C' },
              { value: 'fortran', label: 'Fortran' },
            ]}
          />
        </>
      )}

      <InputField
        label="Variables"
        value={(p.variables || ['x']).join(', ')}
        onChange={(v) => update('variables', v.split(',').map(s => s.trim()).filter(Boolean))}
        placeholder="x, y"
      />

      <div style={{ fontSize: 11, color: '#a78bfa', marginTop: 8, padding: 8, background: '#a78bfa11', borderRadius: 4, border: '1px solid #a78bfa33' }}>
        Code generation mode exports UFL code for FEniCS pipeline coupling (SymPy → FEniCS).
      </div>
    </>
  );
}
