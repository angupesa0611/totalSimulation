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

      <div style={{ marginTop: 8 }}>
        <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
          Or: Inline Trajectory Data (JSON)
        </label>
        <textarea
          value={typeof p.trajectory_data === 'string' ? p.trajectory_data : (p.trajectory_data ? JSON.stringify(p.trajectory_data, null, 1) : '')}
          onChange={(e) => { if (!e.target.value.trim()) { update('trajectory_data', null); return; } try { update('trajectory_data', JSON.parse(e.target.value)); } catch { update('trajectory_data', e.target.value); } }}
          placeholder='{"frames": [[[x,y,z],...]], "n_atoms": N}'
          rows={3}
          style={{
            width: '100%', padding: 6, background: theme.colors.bgTertiary,
            border: `1px solid ${theme.colors.border}`, borderRadius: 4,
            color: theme.colors.text, fontSize: 11, fontFamily: "'JetBrains Mono', monospace",
            resize: 'vertical',
          }}
        />
      </div>

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
