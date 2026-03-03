import React from 'react';
import { InputField, SliderParam, DropdownSelect } from '../shared';

export default function CanteraParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'ignition_delay';

  return (
    <>
      <DropdownSelect
        label="Simulation Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'ignition_delay', label: 'Ignition Delay' },
          { value: 'reactor_timecourse', label: 'Reactor Time Course' },
          { value: 'flame_speed', label: 'Flame Speed' },
          { value: 'equilibrium', label: 'Equilibrium' },
        ]}
      />

      <DropdownSelect
        label="Mechanism"
        value={p.mechanism || 'gri30.yaml'}
        onChange={(v) => update('mechanism', v)}
        options={[
          { value: 'gri30.yaml', label: 'GRI-Mech 3.0 (CH4/H2)' },
          { value: 'h2o2.yaml', label: 'H2/O2 (simple)' },
        ]}
      />

      <InputField
        label="Temperature (K)"
        value={p.temperature_K ?? 1200}
        onChange={(v) => update('temperature_K', parseFloat(v))}
        type="number"
        step={50}
      />

      <InputField
        label="Pressure (atm)"
        value={p.pressure_atm ?? 1.0}
        onChange={(v) => update('pressure_atm', parseFloat(v))}
        type="number"
        step={0.5}
      />

      <InputField
        label="Composition"
        value={p.composition || 'H2:2,O2:1,N2:3.76'}
        onChange={(v) => update('composition', v)}
        placeholder="H2:2,O2:1,N2:3.76"
      />

      {(simType === 'ignition_delay' || simType === 'reactor_timecourse') && (
        <>
          <InputField
            label="End Time (s)"
            value={p.end_time_s ?? 0.001}
            onChange={(v) => update('end_time_s', parseFloat(v))}
            type="number"
            step={0.0001}
          />
          <SliderParam
            label="Output Points"
            value={p.n_points ?? 200}
            onChange={(v) => update('n_points', v)}
            min={50}
            max={1000}
            step={50}
          />
        </>
      )}

      {simType === 'flame_speed' && (
        <InputField
          label="Domain Width (m)"
          value={p.width_m ?? 0.03}
          onChange={(v) => update('width_m', parseFloat(v))}
          type="number"
          step={0.005}
        />
      )}
    </>
  );
}
