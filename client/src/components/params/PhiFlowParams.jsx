import React from 'react';
import { InputField, SliderParam, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function PhiFlowParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'smoke_simulation';

  return (
    <>
      <DropdownSelect
        label="Simulation Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'smoke_simulation', label: 'Smoke Simulation' },
          { value: 'fluid_2d', label: '2D Fluid' },
          { value: 'diffusion', label: 'Diffusion' },
          { value: 'wave_equation', label: 'Wave Equation' },
        ]}
      />

      <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
        Grid Resolution
      </div>
      <div style={{ display: 'flex', gap: 4 }}>
        <InputField
          label="Nx"
          value={p.nx ?? 64}
          onChange={(v) => update('nx', parseInt(v) || 64)}
          type="number"
          step={8}
        />
        <InputField
          label="Ny"
          value={p.ny ?? 64}
          onChange={(v) => update('ny', parseInt(v) || 64)}
          type="number"
          step={8}
        />
      </div>

      <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
        Domain Size
      </div>
      <div style={{ display: 'flex', gap: 4 }}>
        <InputField
          label="Lx"
          value={p.lx ?? 1.0}
          onChange={(v) => update('lx', parseFloat(v) || 1.0)}
          type="number"
          step={0.1}
        />
        <InputField
          label="Ly"
          value={p.ly ?? 1.0}
          onChange={(v) => update('ly', parseFloat(v) || 1.0)}
          type="number"
          step={0.1}
        />
      </div>

      <InputField
        label="Time Step (dt)"
        value={p.dt ?? 0.1}
        onChange={(v) => update('dt', parseFloat(v) || 0.1)}
        type="number"
        step={0.01}
      />

      <SliderParam
        label="Steps"
        value={p.n_steps ?? 100}
        onChange={(v) => update('n_steps', v)}
        min={10}
        max={1000}
        step={10}
      />

      <DropdownSelect
        label="Backend"
        value={p.backend || 'numpy'}
        onChange={(v) => update('backend', v)}
        options={[
          { value: 'numpy', label: 'NumPy (CPU)' },
          { value: 'jax', label: 'JAX (CPU, faster)' },
        ]}
      />

      {simType === 'smoke_simulation' && (
        <>
          <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
            Inflow Position
          </div>
          <div style={{ display: 'flex', gap: 4 }}>
            <InputField
              label="X"
              value={p.inflow_x ?? 0.5}
              onChange={(v) => update('inflow_x', parseFloat(v))}
              type="number"
              step={0.05}
            />
            <InputField
              label="Y"
              value={p.inflow_y ?? 0.1}
              onChange={(v) => update('inflow_y', parseFloat(v))}
              type="number"
              step={0.05}
            />
          </div>
          <InputField
            label="Inflow Radius"
            value={p.inflow_radius ?? 0.05}
            onChange={(v) => update('inflow_radius', parseFloat(v) || 0.05)}
            type="number"
            step={0.01}
          />
          <InputField
            label="Buoyancy"
            value={p.buoyancy ?? 0.5}
            onChange={(v) => update('buoyancy', parseFloat(v))}
            type="number"
            step={0.1}
          />
        </>
      )}

      {simType === 'fluid_2d' && (
        <>
          <InputField
            label="Viscosity"
            value={p.viscosity ?? 0.001}
            onChange={(v) => update('viscosity', parseFloat(v) || 0.001)}
            type="number"
            step={0.001}
          />
          <DropdownSelect
            label="Initial Velocity"
            value={p.initial_velocity || 'zero'}
            onChange={(v) => update('initial_velocity', v)}
            options={[
              { value: 'zero', label: 'Zero' },
              { value: 'uniform_x', label: 'Uniform (X direction)' },
              { value: 'vortex', label: 'Vortex' },
              { value: 'random', label: 'Random' },
            ]}
          />
        </>
      )}

      {simType === 'diffusion' && (
        <>
          <InputField
            label="Diffusivity"
            value={p.diffusivity ?? 0.1}
            onChange={(v) => update('diffusivity', parseFloat(v) || 0.1)}
            type="number"
            step={0.01}
          />
          <DropdownSelect
            label="Initial Condition"
            value={p.initial_condition || 'gaussian'}
            onChange={(v) => update('initial_condition', v)}
            options={[
              { value: 'gaussian', label: 'Gaussian' },
              { value: 'step', label: 'Step Function' },
              { value: 'sinusoidal', label: 'Sinusoidal' },
              { value: 'random', label: 'Random' },
            ]}
          />
        </>
      )}

      {simType === 'wave_equation' && (
        <>
          <InputField
            label="Wave Speed"
            value={p.wave_speed ?? 1.0}
            onChange={(v) => update('wave_speed', parseFloat(v) || 1.0)}
            type="number"
            step={0.1}
          />
          <DropdownSelect
            label="Initial Condition"
            value={p.initial_condition || 'gaussian'}
            onChange={(v) => update('initial_condition', v)}
            options={[
              { value: 'gaussian', label: 'Gaussian Pulse' },
              { value: 'sinusoidal', label: 'Sinusoidal' },
              { value: 'plane_wave', label: 'Plane Wave' },
            ]}
          />
        </>
      )}
    </>
  );
}
