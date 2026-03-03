import React from 'react';
import { InputField, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function DedalusParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'rayleigh_benard';

  return (
    <>
      <DropdownSelect
        label="Problem Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'rayleigh_benard', label: 'Rayleigh-Bénard Convection' },
          { value: 'diffusion_1d', label: '1D Diffusion' },
          { value: 'wave_1d', label: '1D Wave Equation' },
        ]}
      />

      {simType === 'rayleigh_benard' && (
        <>
          <InputField
            label="Rayleigh Number"
            value={p.rayleigh ?? 1e6}
            onChange={(v) => update('rayleigh', parseFloat(v) || 1e6)}
            type="number"
            step={1e5}
          />
          <InputField
            label="Prandtl Number"
            value={p.prandtl ?? 1}
            onChange={(v) => update('prandtl', parseFloat(v) || 1)}
            type="number"
            step={0.1}
          />
          <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
            Resolution
          </div>
          <div style={{ display: 'flex', gap: 4 }}>
            <InputField
              label="Nx"
              value={p.nx ?? 64}
              onChange={(v) => update('nx', parseInt(v) || 64)}
              type="number"
              step={16}
            />
            <InputField
              label="Nz"
              value={p.nz ?? 32}
              onChange={(v) => update('nz', parseInt(v) || 32)}
              type="number"
              step={8}
            />
          </div>
          <InputField
            label="Aspect Ratio"
            value={p.aspect_ratio ?? 4}
            onChange={(v) => update('aspect_ratio', parseFloat(v) || 4)}
            type="number"
            step={0.5}
          />
          <InputField
            label="End Time"
            value={p.end_time ?? 30}
            onChange={(v) => update('end_time', parseFloat(v) || 30)}
            type="number"
            step={5}
          />
          <InputField
            label="Time Step (dt)"
            value={p.dt ?? 0.01}
            onChange={(v) => update('dt', parseFloat(v) || 0.01)}
            type="number"
            step={0.005}
          />
        </>
      )}

      {simType === 'diffusion_1d' && (
        <>
          <InputField
            label="Diffusivity"
            value={p.diffusivity ?? 1.0}
            onChange={(v) => update('diffusivity', parseFloat(v) || 1.0)}
            type="number"
            step={0.1}
          />
          <InputField
            label="Spectral Modes (N)"
            value={p.n_modes ?? 64}
            onChange={(v) => update('n_modes', parseInt(v) || 64)}
            type="number"
            step={16}
          />
          <InputField
            label="Domain Size"
            value={p.domain_size ?? 1.0}
            onChange={(v) => update('domain_size', parseFloat(v) || 1.0)}
            type="number"
            step={0.5}
          />
          <InputField
            label="End Time"
            value={p.end_time ?? 1.0}
            onChange={(v) => update('end_time', parseFloat(v) || 1.0)}
            type="number"
            step={0.1}
          />
          <DropdownSelect
            label="Initial Condition"
            value={p.initial_condition || 'gaussian'}
            onChange={(v) => update('initial_condition', v)}
            options={[
              { value: 'gaussian', label: 'Gaussian' },
              { value: 'step', label: 'Step Function' },
              { value: 'sinusoidal', label: 'Sinusoidal' },
            ]}
          />
        </>
      )}

      {simType === 'wave_1d' && (
        <>
          <InputField
            label="Wave Speed"
            value={p.wave_speed ?? 1.0}
            onChange={(v) => update('wave_speed', parseFloat(v) || 1.0)}
            type="number"
            step={0.1}
          />
          <InputField
            label="Spectral Modes (N)"
            value={p.n_modes ?? 64}
            onChange={(v) => update('n_modes', parseInt(v) || 64)}
            type="number"
            step={16}
          />
          <InputField
            label="Domain Size"
            value={p.domain_size ?? 1.0}
            onChange={(v) => update('domain_size', parseFloat(v) || 1.0)}
            type="number"
            step={0.5}
          />
          <InputField
            label="End Time"
            value={p.end_time ?? 2.0}
            onChange={(v) => update('end_time', parseFloat(v) || 2.0)}
            type="number"
            step={0.5}
          />
        </>
      )}
    </>
  );
}
