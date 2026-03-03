import React from 'react';
import { InputField, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function RDKitParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'descriptors';

  return (
    <>
      <DropdownSelect
        label="Analysis Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'descriptors', label: 'Molecular Descriptors' },
          { value: 'conformer_3d', label: '3D Conformer Generation' },
          { value: 'fingerprint', label: 'Molecular Fingerprint' },
          { value: 'similarity', label: 'Similarity Search' },
        ]}
      />

      <InputField
        label="SMILES"
        value={p.smiles || ''}
        onChange={(v) => update('smiles', v)}
        placeholder="CC(=O)Oc1ccccc1C(=O)O"
      />

      {simType === 'conformer_3d' && (
        <>
          <InputField
            label="Number of Conformers"
            value={p.n_conformers ?? 1}
            onChange={(v) => update('n_conformers', parseInt(v) || 1)}
            type="number"
            step={1}
          />
          <DropdownSelect
            label="Optimize (MMFF94)"
            value={p.optimize_conformer !== false ? 'true' : 'false'}
            onChange={(v) => update('optimize_conformer', v === 'true')}
            options={[
              { value: 'true', label: 'Yes' },
              { value: 'false', label: 'No' },
            ]}
          />
        </>
      )}

      {simType === 'fingerprint' && (
        <>
          <DropdownSelect
            label="Fingerprint Type"
            value={p.fingerprint_type || 'morgan'}
            onChange={(v) => update('fingerprint_type', v)}
            options={[
              { value: 'morgan', label: 'Morgan (ECFP)' },
              { value: 'rdkit', label: 'RDKit Topological' },
              { value: 'maccs', label: 'MACCS Keys' },
            ]}
          />
          {(p.fingerprint_type || 'morgan') === 'morgan' && (
            <InputField
              label="Radius"
              value={p.fingerprint_radius ?? 2}
              onChange={(v) => update('fingerprint_radius', parseInt(v) || 2)}
              type="number"
              step={1}
            />
          )}
        </>
      )}

      {simType === 'similarity' && (
        <div style={{ marginTop: 8 }}>
          <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
            Target SMILES (one per line)
          </label>
          <textarea
            value={(p.smiles_list || []).join('\n')}
            onChange={(e) => update('smiles_list', e.target.value.split('\n').filter(s => s.trim()))}
            placeholder="CCO&#10;CC(=O)O&#10;c1ccccc1"
            rows={4}
            style={{
              width: '100%',
              background: theme.colors.bgTertiary,
              border: `1px solid ${theme.colors.border}`,
              borderRadius: 4,
              color: theme.colors.text,
              padding: 8,
              fontSize: 12,
              fontFamily: theme.fonts.mono,
              resize: 'vertical',
            }}
          />
        </div>
      )}

      <div style={{ fontSize: 11, color: '#0ea5e9', marginTop: 8, padding: 8, background: '#0ea5e911', borderRadius: 4, border: '1px solid #0ea5e933' }}>
        All analysis types export PySCF-compatible coordinates for pipeline coupling (RDKit → PySCF).
      </div>
    </>
  );
}
