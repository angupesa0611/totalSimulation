import React from 'react';
import { InputField, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function PyscfParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  return (
    <>
      <div style={{ marginBottom: 12 }}>
        <label style={{ display: 'block', fontSize: 12, color: theme.colors.textSecondary, marginBottom: 4 }}>
          Atom Coordinates
        </label>
        <textarea
          value={p.atom_coords || ''}
          onChange={(e) => update('atom_coords', e.target.value)}
          placeholder="H 0 0 0; H 0 0 0.74"
          rows={4}
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
          { value: 'dft', label: 'Density Functional Theory (DFT)' },
          { value: 'mp2', label: 'MP2' },
          { value: 'ccsd', label: 'CCSD' },
        ]}
      />

      <DropdownSelect
        label="Basis Set"
        value={p.basis || 'sto-3g'}
        onChange={(v) => update('basis', v)}
        options={['sto-3g', '6-31g', '6-31g*', '6-311g**', 'cc-pvdz', 'cc-pvtz', 'aug-cc-pvdz']}
      />

      {p.method === 'dft' && (
        <DropdownSelect
          label="XC Functional"
          value={p.xc_functional || 'b3lyp'}
          onChange={(v) => update('xc_functional', v)}
          options={['b3lyp', 'pbe', 'pbe0', 'lda', 'm06-2x']}
        />
      )}

      <InputField
        label="Charge"
        value={p.charge ?? 0}
        onChange={(v) => update('charge', parseInt(v) || 0)}
        type="number"
        step={1}
      />

      <InputField
        label="Spin (2S)"
        value={p.spin ?? 0}
        onChange={(v) => update('spin', parseInt(v) || 0)}
        type="number"
        step={1}
        min={0}
      />
    </>
  );
}
