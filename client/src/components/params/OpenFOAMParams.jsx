import React from 'react';
import { InputField, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function OpenFOAMParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'cavity';

  return (
    <>
      <DropdownSelect
        label="Case Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'cavity', label: 'Lid-Driven Cavity' },
          { value: 'pipe_flow', label: 'Pipe Flow' },
        ]}
      />

      <DropdownSelect
        label="Solver"
        value={p.solver || 'icoFoam'}
        onChange={(v) => update('solver', v)}
        options={[
          { value: 'icoFoam', label: 'icoFoam (incompressible, transient)' },
          { value: 'simpleFoam', label: 'simpleFoam (steady-state)' },
          { value: 'pisoFoam', label: 'pisoFoam (transient PISO)' },
        ]}
      />

      <DropdownSelect
        label="Turbulence Model"
        value={p.turbulence_model || 'laminar'}
        onChange={(v) => update('turbulence_model', v)}
        options={[
          { value: 'laminar', label: 'Laminar' },
          { value: 'kEpsilon', label: 'k-Epsilon' },
          { value: 'kOmegaSST', label: 'k-Omega SST' },
        ]}
      />

      {simType === 'cavity' && (
        <>
          <InputField
            label="Reynolds Number"
            value={p.re ?? 100}
            onChange={(v) => update('re', parseFloat(v) || 100)}
            type="number"
            step={50}
          />
          <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
            Mesh Cells
          </div>
          <div style={{ display: 'flex', gap: 4 }}>
            <InputField
              label="Nx"
              value={p.nx ?? 20}
              onChange={(v) => update('nx', parseInt(v) || 20)}
              type="number"
              step={5}
            />
            <InputField
              label="Ny"
              value={p.ny ?? 20}
              onChange={(v) => update('ny', parseInt(v) || 20)}
              type="number"
              step={5}
            />
            <InputField
              label="Nz"
              value={p.nz ?? 1}
              onChange={(v) => update('nz', parseInt(v) || 1)}
              type="number"
              step={1}
            />
          </div>
          <InputField
            label="End Time (s)"
            value={p.end_time ?? 0.5}
            onChange={(v) => update('end_time', parseFloat(v) || 0.5)}
            type="number"
            step={0.1}
          />
          <InputField
            label="Write Interval (s)"
            value={p.write_interval ?? 0.1}
            onChange={(v) => update('write_interval', parseFloat(v) || 0.1)}
            type="number"
            step={0.05}
          />
        </>
      )}

      {simType === 'pipe_flow' && (
        <>
          <InputField
            label="Diameter (m)"
            value={p.diameter ?? 0.1}
            onChange={(v) => update('diameter', parseFloat(v) || 0.1)}
            type="number"
            step={0.01}
          />
          <InputField
            label="Length (m)"
            value={p.length ?? 1.0}
            onChange={(v) => update('length', parseFloat(v) || 1.0)}
            type="number"
            step={0.1}
          />
          <InputField
            label="Inlet Velocity (m/s)"
            value={p.velocity_inlet ?? 1.0}
            onChange={(v) => update('velocity_inlet', parseFloat(v) || 1.0)}
            type="number"
            step={0.1}
          />
          <InputField
            label="Mesh Cells"
            value={p.n_cells ?? 1000}
            onChange={(v) => update('n_cells', parseInt(v) || 1000)}
            type="number"
            step={100}
          />
          <InputField
            label="End Time (s)"
            value={p.end_time ?? 1.0}
            onChange={(v) => update('end_time', parseFloat(v) || 1.0)}
            type="number"
            step={0.1}
          />
        </>
      )}
    </>
  );
}
