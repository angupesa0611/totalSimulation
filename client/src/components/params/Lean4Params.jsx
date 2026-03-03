import React from 'react';
import { InputField, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function Lean4Params({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'verify_statement';

  return (
    <>
      <DropdownSelect
        label="Verification Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'verify_statement', label: 'Verify Statement' },
          { value: 'check_proof', label: 'Check Proof' },
          { value: 'type_check', label: 'Type Check' },
        ]}
      />

      <div style={{ marginTop: 8 }}>
        <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
          Lean 4 Code
        </label>
        <textarea
          value={p.lean_code || ''}
          onChange={(e) => update('lean_code', e.target.value)}
          placeholder="theorem add_comm (n m : Nat) : n + m = m + n := Nat.add_comm n m"
          rows={8}
          style={{
            width: '100%', background: theme.colors.bgTertiary,
            border: `1px solid ${theme.colors.border}`, borderRadius: 4,
            color: theme.colors.text, padding: 8, fontSize: 12,
            fontFamily: theme.fonts.mono, resize: 'vertical',
          }}
        />
      </div>

      {simType === 'verify_statement' && (
        <InputField
          label="Theorem Name"
          value={p.theorem_name || ''}
          onChange={(v) => update('theorem_name', v)}
          placeholder="add_comm"
        />
      )}

      <InputField
        label="Timeout (s)"
        value={p.timeout_s ?? 60}
        onChange={(v) => update('timeout_s', parseInt(v) || 60)}
        type="number"
      />

      <div style={{ fontSize: 11, color: '#a78bfa', marginTop: 8, padding: 8, background: '#a78bfa11', borderRadius: 4, border: '1px solid #a78bfa33' }}>
        Requires <code>mathematics</code> Docker profile. Uses Lean 4 stable toolchain (no Mathlib).
      </div>
    </>
  );
}
