import React from 'react';
import { InputField, SliderParam, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function EinsteinpyParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'schwarzschild_geodesic';
  const pos = p.initial_position || [40.0, Math.PI / 2, 0.0];
  const vel = p.initial_velocity || [0.0, 0.0, 0.002];

  const updatePos = (idx, val) => {
    const newPos = [...pos];
    newPos[idx] = parseFloat(val) || 0;
    update('initial_position', newPos);
  };

  const updateVel = (idx, val) => {
    const newVel = [...vel];
    newVel[idx] = parseFloat(val) || 0;
    update('initial_velocity', newVel);
  };

  return (
    <>
      <DropdownSelect
        label="Simulation Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'schwarzschild_geodesic', label: 'Schwarzschild Geodesic' },
          { value: 'kerr_geodesic', label: 'Kerr Geodesic' },
          { value: 'precession', label: 'Perihelion Precession' },
        ]}
      />

      <InputField label="Black Hole Mass (M)" value={p.M ?? 1e6} onChange={(v) => update('M', parseFloat(v))} type="number" step={1e5} />

      {simType === 'kerr_geodesic' && (
        <SliderParam label="Spin Parameter (a)" value={p.a ?? 0.0} onChange={(v) => update('a', v)} min={0} max={0.998} step={0.01} />
      )}

      <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
        Initial Position (r, θ, φ)
      </div>
      <div style={{ display: 'flex', gap: 4 }}>
        <InputField label="r" value={pos[0]} onChange={(v) => updatePos(0, v)} type="number" step={1} />
        <InputField label="θ" value={pos[1]} onChange={(v) => updatePos(1, v)} type="number" step={0.1} />
        <InputField label="φ" value={pos[2]} onChange={(v) => updatePos(2, v)} type="number" step={0.1} />
      </div>

      <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
        Initial Velocity (v_r, v_θ, v_φ)
      </div>
      <div style={{ display: 'flex', gap: 4 }}>
        <InputField label="v_r" value={vel[0]} onChange={(v) => updateVel(0, v)} type="number" step={0.001} />
        <InputField label="v_θ" value={vel[1]} onChange={(v) => updateVel(1, v)} type="number" step={0.001} />
        <InputField label="v_φ" value={vel[2]} onChange={(v) => updateVel(2, v)} type="number" step={0.001} />
      </div>

      <InputField label="Max Proper Time" value={p.max_time ?? 5000} onChange={(v) => update('max_time', parseFloat(v))} type="number" step={100} />
      <SliderParam label="Integration Steps" value={p.n_steps ?? 1000} onChange={(v) => update('n_steps', v)} min={100} max={5000} step={100} />
    </>
  );
}
