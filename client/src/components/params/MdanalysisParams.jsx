import React from 'react';
import { InputField, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function MdanalysisParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  return (
    <>
      <DropdownSelect
        label="Analysis Type"
        value={p.analysis_type || 'rmsd'}
        onChange={(v) => update('analysis_type', v)}
        options={[
          { value: 'rmsd', label: 'RMSD' },
          { value: 'rmsf', label: 'RMSF' },
          { value: 'rg', label: 'Radius of Gyration' },
          { value: 'contacts', label: 'Contact Map' },
          { value: 'ramachandran', label: 'Ramachandran' },
          { value: 'hbonds', label: 'Hydrogen Bonds' },
        ]}
      />

      <InputField
        label="Source Job ID"
        value={p.source_job_id || ''}
        onChange={(v) => update('source_job_id', v)}
        type="text"
        placeholder="Paste job ID from a previous MD run"
      />

      {(p.analysis_type === 'contacts' || p.analysis_type === 'hbonds') && (
        <InputField
          label="Distance Cutoff (Å)"
          value={p.cutoff ?? (p.analysis_type === 'hbonds' ? 3.5 : 5.0)}
          onChange={(v) => update('cutoff', parseFloat(v) || 5.0)}
          type="number"
          step={0.5}
          min={1}
          max={20}
        />
      )}

      <div style={{
        fontSize: 11,
        color: theme.colors.textSecondary,
        marginTop: 12,
        padding: 10,
        background: theme.colors.bgTertiary,
        borderRadius: 6,
        lineHeight: 1.5,
      }}>
        Analyzes trajectory data from a previous MD simulation.
        Enter the job ID from an OpenMM, GROMACS, or NAMD run.
      </div>
    </>
  );
}
