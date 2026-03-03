import React from 'react';
import { InputField, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function PyomoParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'linear_program';

  const textareaStyle = {
    width: '100%', background: theme.colors.bgTertiary,
    border: `1px solid ${theme.colors.border}`, borderRadius: 4,
    color: theme.colors.text, padding: 8, fontSize: 12,
    fontFamily: theme.fonts.mono, resize: 'vertical',
  };

  return (
    <>
      <DropdownSelect
        label="Problem Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'linear_program', label: 'Linear Program (LP)' },
          { value: 'mixed_integer', label: 'Mixed-Integer (MIP)' },
          { value: 'nonlinear', label: 'Nonlinear (NLP)' },
        ]}
      />

      <div style={{ marginTop: 8 }}>
        <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
          Variables (JSON array of {'{'}name, lower, upper, domain{'}'})
        </label>
        <textarea
          value={p.variables || JSON.stringify([
            { name: 'x', lower: 0, upper: null, domain: 'NonNegativeReals' },
            { name: 'y', lower: 0, upper: null, domain: 'NonNegativeReals' },
          ], null, 2)}
          onChange={(e) => { try { update('variables', JSON.parse(e.target.value)); } catch { update('variables', e.target.value); } }}
          rows={5}
          style={textareaStyle}
        />
      </div>

      <InputField
        label="Objective Expression"
        value={p.objective || ''}
        onChange={(v) => update('objective', v)}
        placeholder="2*x + 3*y"
      />

      <DropdownSelect
        label="Objective Sense"
        value={p.sense || 'minimize'}
        onChange={(v) => update('sense', v)}
        options={[
          { value: 'minimize', label: 'Minimize' },
          { value: 'maximize', label: 'Maximize' },
        ]}
      />

      <div style={{ marginTop: 8 }}>
        <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
          Constraints (JSON array of {'{'}name, expression{'}'})
        </label>
        <textarea
          value={p.constraints || JSON.stringify([
            { name: 'c1', expression: 'x + y <= 10' },
            { name: 'c2', expression: 'x - y >= 0' },
          ], null, 2)}
          onChange={(e) => { try { update('constraints', JSON.parse(e.target.value)); } catch { update('constraints', e.target.value); } }}
          rows={5}
          style={textareaStyle}
        />
      </div>

      <DropdownSelect
        label="Solver"
        value={p.solver || 'glpk'}
        onChange={(v) => update('solver', v)}
        options={[
          { value: 'glpk', label: 'GLPK' },
          { value: 'highs', label: 'HiGHS (LP/MILP, fast)' },
          { value: 'cbc', label: 'CBC (LP/MILP)' },
          { value: 'ipopt', label: 'IPOPT (NLP)' },
        ]}
      />
    </>
  );
}
