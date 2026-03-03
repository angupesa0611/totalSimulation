import React, { useCallback } from 'react';
import { InputField, DropdownSelect, SliderParam } from '../shared';
import theme from '../../theme.json';

export default function QmmmParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const handlePdbFile = useCallback((e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => update('pdb_content', ev.target.result);
    reader.readAsText(file);
  }, [p, onChange]);

  // Parse qm_region string like "0-4" or "0,1,2,3,4" into array
  const qmRegionStr = Array.isArray(p.qm_region)
    ? p.qm_region.join(', ')
    : (p.qm_region || '');

  const handleQmRegion = (val) => {
    // Support "0-4" range notation and "0,1,2,3" comma notation
    const parts = val.split(/[,\s]+/).filter(Boolean);
    const indices = [];
    for (const part of parts) {
      if (part.includes('-')) {
        const [start, end] = part.split('-').map(Number);
        if (!isNaN(start) && !isNaN(end)) {
          for (let i = start; i <= end; i++) indices.push(i);
        }
      } else {
        const n = parseInt(part);
        if (!isNaN(n)) indices.push(n);
      }
    }
    update('qm_region', indices.length > 0 ? indices : val);
  };

  return (
    <>
      {/* PDB Upload */}
      <div style={{ marginBottom: 12 }}>
        <label style={{ display: 'block', fontSize: 12, color: theme.colors.textSecondary, marginBottom: 4 }}>
          PDB Structure
        </label>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <label style={{
            padding: '6px 12px',
            background: theme.colors.bgTertiary,
            border: `1px solid ${theme.colors.border}`,
            borderRadius: 6,
            color: theme.colors.text,
            fontSize: 12,
            cursor: 'pointer',
          }}>
            Choose PDB
            <input type="file" accept=".pdb" onChange={handlePdbFile} style={{ display: 'none' }} />
          </label>
          <span style={{ fontSize: 11, color: p.pdb_content ? theme.colors.success : theme.colors.textSecondary }}>
            {p.pdb_content ? `${p.pdb_content.split('\n').length} lines` : 'No file'}
          </span>
        </div>
      </div>

      {/* QM Region */}
      <div style={{ marginBottom: 12 }}>
        <label style={{ display: 'block', fontSize: 12, color: theme.colors.textSecondary, marginBottom: 4 }}>
          QM Region (atom indices)
        </label>
        <input
          type="text"
          value={qmRegionStr}
          onChange={(e) => handleQmRegion(e.target.value)}
          placeholder="0-4 or 0, 1, 2, 3, 4"
          style={{
            width: '100%',
            padding: 8,
            background: theme.colors.bgTertiary,
            border: `1px solid ${theme.colors.border}`,
            borderRadius: 6,
            color: theme.colors.text,
            fontFamily: theme.fonts.mono,
            fontSize: 12,
          }}
        />
        <div style={{ fontSize: 10, color: theme.colors.textSecondary, marginTop: 2 }}>
          Use "0-4" for range or "0, 1, 2, 3" for explicit indices (0-indexed)
        </div>
      </div>

      <DropdownSelect
        label="QM Method"
        value={p.qm_method || 'hf'}
        onChange={(v) => update('qm_method', v)}
        options={[
          { value: 'hf', label: 'Hartree-Fock (HF)' },
          { value: 'b3lyp', label: 'DFT B3LYP' },
          { value: 'pbe', label: 'DFT PBE' },
          { value: 'pbe0', label: 'DFT PBE0' },
        ]}
      />

      <DropdownSelect
        label="QM Basis Set"
        value={p.qm_basis || 'sto-3g'}
        onChange={(v) => update('qm_basis', v)}
        options={['sto-3g', '6-31g', '6-31g*', 'cc-pvdz']}
      />

      <DropdownSelect
        label="MM Forcefield"
        value={p.forcefield || 'AMBER'}
        onChange={(v) => update('forcefield', v)}
        options={['AMBER', 'CHARMM']}
      />

      <DropdownSelect
        label="Task Type"
        value={p.task_type || 'optimization'}
        onChange={(v) => update('task_type', v)}
        options={[
          { value: 'optimization', label: 'Geometry Optimization' },
          { value: 'md', label: 'Molecular Dynamics' },
        ]}
      />

      <SliderParam
        label="Steps"
        value={p.steps ?? 50}
        onChange={(v) => update('steps', v)}
        min={10}
        max={500}
        step={10}
      />

      {p.task_type === 'md' && (
        <InputField
          label="Temperature (K)"
          value={p.temperature ?? 300}
          onChange={(v) => update('temperature', parseFloat(v) || 300)}
          type="number"
          step={10}
        />
      )}

      <InputField
        label="QM Charge"
        value={p.charge ?? 0}
        onChange={(v) => update('charge', parseInt(v) || 0)}
        type="number"
        step={1}
      />

      <div style={{
        fontSize: 11,
        marginTop: 12,
        padding: 10,
        background: '#14b8a611',
        border: '1px solid #14b8a633',
        borderRadius: 6,
        color: '#14b8a6',
        lineHeight: 1.5,
      }}>
        QM/MM: PySCF computes the QM region with electrostatic embedding
        from MM point charges. OpenMM handles the MM surroundings.
      </div>
    </>
  );
}
