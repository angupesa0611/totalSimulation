import React from 'react';
import { InputField, SliderParam, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function SU2Params({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'inviscid_airfoil';

  return (
    <>
      <DropdownSelect
        label="Simulation Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'inviscid_airfoil', label: 'Inviscid Airfoil' },
          { value: 'euler_flow', label: 'Euler Flow' },
          { value: 'rans', label: 'RANS (Turbulent)' },
          { value: 'nozzle_flow', label: 'Nozzle Flow' },
        ]}
      />

      <InputField
        label="Mach Number"
        value={p.mach_number ?? 0.8}
        onChange={(v) => update('mach_number', parseFloat(v) || 0.8)}
        type="number"
        step={0.05}
      />

      <InputField
        label="Angle of Attack (deg)"
        value={p.angle_of_attack ?? 1.25}
        onChange={(v) => update('angle_of_attack', parseFloat(v) || 0.0)}
        type="number"
        step={0.25}
      />

      {simType === 'rans' && (
        <InputField
          label="Reynolds Number"
          value={p.reynolds_number ?? 6500000}
          onChange={(v) => update('reynolds_number', parseFloat(v) || 6.5e6)}
          type="number"
        />
      )}

      <DropdownSelect
        label="Mesh"
        value={p.mesh || 'naca_0012'}
        onChange={(v) => update('mesh', v)}
        options={[
          { value: 'naca_0012', label: 'NACA 0012' },
          { value: 'naca_2412', label: 'NACA 2412' },
          { value: 'naca_4412', label: 'NACA 4412' },
          { value: 'naca_0006', label: 'NACA 0006 (thin)' },
        ]}
      />

      <SliderParam
        label="Iterations"
        value={p.n_iterations ?? 250}
        onChange={(v) => update('n_iterations', v)}
        min={50}
        max={2000}
        step={50}
      />

      <div style={{ fontSize: 11, color: '#f59e0b', marginTop: 8, padding: 8, background: '#f59e0b11', borderRadius: 4, border: '1px solid #f59e0b33' }}>
        Requires <code>fluids</code> Docker profile. Compressible/transonic CFD (complements OpenFOAM).
      </div>
    </>
  );
}
