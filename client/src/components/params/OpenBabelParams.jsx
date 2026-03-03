import React from 'react';
import { InputField, SliderParam, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function OpenBabelParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });
  const simType = p.simulation_type || 'convert';

  return (
    <>
      <DropdownSelect
        label="Operation"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'convert', label: 'Format Conversion' },
          { value: 'optimize_3d', label: '3D Optimization' },
          { value: 'protonate', label: 'Protonation (pH)' },
        ]}
      />

      <DropdownSelect
        label="Source Format"
        value={p.source_format || 'smi'}
        onChange={(v) => update('source_format', v)}
        options={[
          { value: 'smi', label: 'SMILES (.smi)' },
          { value: 'sdf', label: 'SDF (.sdf)' },
          { value: 'mol2', label: 'MOL2 (.mol2)' },
          { value: 'pdb', label: 'PDB (.pdb)' },
          { value: 'xyz', label: 'XYZ (.xyz)' },
          { value: 'inchi', label: 'InChI' },
          { value: 'cml', label: 'CML (.cml)' },
        ]}
      />

      <div style={{ marginBottom: 8 }}>
        <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
          Source Data
        </label>
        <textarea
          value={p.source_data || ''}
          onChange={(e) => update('source_data', e.target.value)}
          placeholder="e.g. CC(=O)Oc1ccccc1C(=O)O (aspirin SMILES)"
          rows={4}
          style={{
            width: '100%',
            background: theme.colors.bgTertiary,
            color: theme.colors.text,
            border: `1px solid ${theme.colors.border}`,
            borderRadius: 4,
            padding: 8,
            fontSize: 12,
            fontFamily: 'monospace',
            resize: 'vertical',
          }}
        />
      </div>

      {simType === 'convert' && (
        <DropdownSelect
          label="Target Format"
          value={p.target_format || 'sdf'}
          onChange={(v) => update('target_format', v)}
          options={[
            { value: 'sdf', label: 'SDF (.sdf)' },
            { value: 'mol2', label: 'MOL2 (.mol2)' },
            { value: 'pdb', label: 'PDB (.pdb)' },
            { value: 'xyz', label: 'XYZ (.xyz)' },
            { value: 'smi', label: 'SMILES (.smi)' },
            { value: 'inchi', label: 'InChI' },
            { value: 'can', label: 'Canonical SMILES' },
            { value: 'lmpdat', label: 'LAMMPS Data' },
            { value: 'gro', label: 'GROMACS (.gro)' },
            { value: 'gjf', label: 'Gaussian (.gjf)' },
          ]}
        />
      )}

      {simType === 'optimize_3d' && (
        <>
          <DropdownSelect
            label="Force Field"
            value={p.force_field || 'mmff94'}
            onChange={(v) => update('force_field', v)}
            options={[
              { value: 'mmff94', label: 'MMFF94 (organic molecules)' },
              { value: 'uff', label: 'UFF (universal)' },
              { value: 'gaff', label: 'GAFF (general amber)' },
            ]}
          />
          <SliderParam
            label="Optimization Steps"
            value={p.steps || 500}
            onChange={(v) => update('steps', v)}
            min={100}
            max={5000}
            step={100}
          />
        </>
      )}

      {simType === 'protonate' && (
        <InputField
          label="pH"
          value={p.ph ?? 7.4}
          onChange={(v) => update('ph', parseFloat(v))}
          type="number"
          step={0.1}
        />
      )}

      <div style={{ fontSize: 11, color: theme.colors.textSecondary, marginTop: 8, lineHeight: 1.5 }}>
        Open Babel supports 110+ molecular formats. Use format conversion to bridge
        between tools (RDKit, PySCF, LAMMPS, GROMACS, etc.).
      </div>
    </>
  );
}
