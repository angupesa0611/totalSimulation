import React from 'react';
import { InputField, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function Psi4Params({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });
  const isSapt = (p.method || '').startsWith('sapt');

  return (
    <>
      <div style={{ marginBottom: 12 }}>
        <label style={{ display: 'block', fontSize: 12, color: theme.colors.textSecondary, marginBottom: 4 }}>
          Geometry {isSapt && '(use -- to separate fragments)'}
        </label>
        <textarea
          value={p.geometry || ''}
          onChange={(e) => update('geometry', e.target.value)}
          placeholder={isSapt
            ? "O  0.0  0.0  0.1\nH -0.8  0.0 -0.5\nH  0.8  0.0 -0.5\n--\nO  3.0  0.0  0.1\nH  2.2  0.0 -0.5\nH  3.8  0.0 -0.5"
            : "O  0.0  0.0  0.1\nH -0.8  0.0 -0.5\nH  0.8  0.0 -0.5"
          }
          rows={6}
          style={{
            width: '100%',
            background: theme.colors.bgTertiary,
            border: `1px solid ${theme.colors.border}`,
            borderRadius: 6,
            color: theme.colors.text,
            fontFamily: theme.fonts.mono,
            fontSize: 12,
            padding: 8,
            resize: 'vertical',
          }}
        />
      </div>

      <DropdownSelect
        label="Method"
        value={p.method || 'hf'}
        onChange={(v) => update('method', v)}
        options={[
          { value: 'hf', label: 'Hartree-Fock (HF)' },
          { value: 'mp2', label: 'MP2' },
          { value: 'ccsd', label: 'CCSD' },
          { value: 'ccsd(t)', label: 'CCSD(T)' },
          { value: 'sapt0', label: 'SAPT0' },
          { value: 'sapt2', label: 'SAPT2' },
        ]}
      />

      <DropdownSelect
        label="Basis Set"
        value={p.basis || 'cc-pvdz'}
        onChange={(v) => update('basis', v)}
        options={['sto-3g', '6-31g*', 'cc-pvdz', 'cc-pvtz', 'aug-cc-pvdz', 'jun-cc-pvdz']}
      />

      <InputField
        label="Charge"
        value={p.charge ?? 0}
        onChange={(v) => update('charge', parseInt(v) || 0)}
        type="number"
        step={1}
      />

      <InputField
        label="Multiplicity"
        value={p.multiplicity ?? 1}
        onChange={(v) => update('multiplicity', parseInt(v) || 1)}
        type="number"
        step={1}
        min={1}
      />

      {isSapt && (
        <div style={{
          fontSize: 11,
          color: '#06b6d4',
          marginTop: 8,
          padding: 10,
          background: theme.colors.bgTertiary,
          borderRadius: 6,
          border: '1px solid #06b6d433',
          lineHeight: 1.5,
        }}>
          SAPT decomposes interaction energy into electrostatics, exchange, induction, and dispersion.
          Requires two fragments separated by "--".
        </div>
      )}
    </>
  );
}
