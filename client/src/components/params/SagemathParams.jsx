import React from 'react';
import { InputField, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function SagemathParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'polynomial_algebra';

  return (
    <>
      <DropdownSelect
        label="Computation Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'polynomial_algebra', label: 'Polynomial Algebra' },
          { value: 'number_theory', label: 'Number Theory' },
          { value: 'combinatorics', label: 'Combinatorics' },
          { value: 'differential_geometry', label: 'Differential Geometry' },
          { value: 'coding_theory', label: 'Coding Theory' },
        ]}
      />

      {simType === 'polynomial_algebra' && (
        <>
          <div style={{ marginTop: 8 }}>
            <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
              Polynomials (one per line)
            </label>
            <textarea
              value={(p.polynomials || []).join('\n')}
              onChange={(e) => update('polynomials', e.target.value.split('\n').filter(s => s.trim()))}
              placeholder="x^2 + y^2 - 1&#10;x - y"
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
            label="Ring"
            value={p.ring || 'QQ'}
            onChange={(v) => update('ring', v)}
            options={[
              { value: 'QQ', label: 'Rationals (QQ)' },
              { value: 'ZZ', label: 'Integers (ZZ)' },
              { value: 'GF(2)', label: 'GF(2)' },
              { value: 'GF(7)', label: 'GF(7)' },
            ]}
          />
          <DropdownSelect
            label="Operation"
            value={p.operation || 'groebner'}
            onChange={(v) => update('operation', v)}
            options={[
              { value: 'groebner', label: 'Gröbner Basis' },
              { value: 'factor', label: 'Factor' },
              { value: 'gcd', label: 'GCD' },
              { value: 'resultant', label: 'Resultant' },
            ]}
          />
        </>
      )}

      {simType === 'number_theory' && (
        <>
          <InputField
            label="Number"
            value={p.number ?? 60}
            onChange={(v) => update('number', parseInt(v) || 60)}
            type="number"
          />
          <DropdownSelect
            label="Operation"
            value={p.operation || 'factor'}
            onChange={(v) => update('operation', v)}
            options={[
              { value: 'factor', label: 'Factorization' },
              { value: 'primality', label: 'Primality Test' },
              { value: 'euler_phi', label: 'Euler Phi' },
              { value: 'continued_fraction', label: 'Continued Fraction' },
            ]}
          />
        </>
      )}

      {simType === 'combinatorics' && (
        <>
          <InputField label="n" value={p.n ?? 5} onChange={(v) => update('n', parseInt(v) || 5)} type="number" />
          <InputField label="k" value={p.k ?? 3} onChange={(v) => update('k', parseInt(v) || 3)} type="number" />
          <DropdownSelect
            label="Operation"
            value={p.operation || 'partitions'}
            onChange={(v) => update('operation', v)}
            options={[
              { value: 'partitions', label: 'Partitions' },
              { value: 'permutations', label: 'Permutations' },
              { value: 'graphs', label: 'Graphs' },
              { value: 'lattice', label: 'Binomial Coefficients' },
            ]}
          />
        </>
      )}

      {simType === 'differential_geometry' && (
        <>
          <InputField
            label="Manifold Dimension"
            value={p.manifold_dim ?? 2}
            onChange={(v) => update('manifold_dim', parseInt(v) || 2)}
            type="number"
          />
          <DropdownSelect
            label="Compute"
            value={p.compute || 'christoffel'}
            onChange={(v) => update('compute', v)}
            options={[
              { value: 'christoffel', label: 'Christoffel Symbols' },
              { value: 'riemann', label: 'Riemann Tensor' },
              { value: 'ricci', label: 'Ricci Tensor' },
              { value: 'scalar_curvature', label: 'Scalar Curvature' },
            ]}
          />
        </>
      )}

      {simType === 'coding_theory' && (
        <>
          <DropdownSelect
            label="Code Type"
            value={p.code_type || 'linear'}
            onChange={(v) => update('code_type', v)}
            options={[
              { value: 'linear', label: 'Linear Code' },
              { value: 'bch', label: 'BCH Code' },
              { value: 'reed_solomon', label: 'Reed-Solomon' },
            ]}
          />
          <InputField label="n (length)" value={p.n ?? 7} onChange={(v) => update('n', parseInt(v) || 7)} type="number" />
          <InputField label="k (dimension)" value={p.k ?? 4} onChange={(v) => update('k', parseInt(v) || 4)} type="number" />
          <InputField label="Field Size" value={p.field_size ?? 2} onChange={(v) => update('field_size', parseInt(v) || 2)} type="number" />
        </>
      )}

      <div style={{ fontSize: 11, color: '#a78bfa', marginTop: 8, padding: 8, background: '#a78bfa11', borderRadius: 4, border: '1px solid #a78bfa33' }}>
        Requires <code>mathematics</code> Docker profile. Run with: <code>--profile mathematics</code>
      </div>
    </>
  );
}
