import React from 'react';
import { InputField, SliderParam, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function NrpyParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'gw_strain';

  return (
    <>
      <DropdownSelect
        label="Simulation Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'brill_lindquist', label: 'Brill-Lindquist (2-BH Initial Data)' },
          { value: 'gw_strain', label: 'Gravitational Wave Strain' },
          { value: 'tov_star', label: 'TOV Neutron Star' },
        ]}
      />

      {simType === 'brill_lindquist' && (
        <>
          <SliderParam label="Mass Ratio (q = m2/m1)" value={p.mass_ratio ?? 1.0} onChange={(v) => update('mass_ratio', v)} min={0.1} max={10} step={0.1} />
          <InputField label="Separation (M)" value={p.separation ?? 10.0} onChange={(v) => update('separation', parseFloat(v))} type="number" step={1} />
          <SliderParam label="Grid Points" value={p.grid_points ?? 200} onChange={(v) => update('grid_points', v)} min={50} max={500} step={50} />
        </>
      )}

      {simType === 'gw_strain' && (
        <>
          <InputField label="Total Mass (solar masses)" value={p.total_mass_solar ?? 60.0} onChange={(v) => update('total_mass_solar', parseFloat(v))} type="number" step={5} />
          <SliderParam label="Mass Ratio" value={p.mass_ratio ?? 1.0} onChange={(v) => update('mass_ratio', v)} min={0.1} max={10} step={0.1} />
          <SliderParam label="Spin 1" value={p.spin1 ?? 0.0} onChange={(v) => update('spin1', v)} min={-0.998} max={0.998} step={0.01} />
          <SliderParam label="Spin 2" value={p.spin2 ?? 0.0} onChange={(v) => update('spin2', v)} min={-0.998} max={0.998} step={0.01} />
          <SliderParam label="Points" value={p.grid_points ?? 500} onChange={(v) => update('grid_points', v)} min={100} max={2000} step={100} />
        </>
      )}

      {simType === 'tov_star' && (
        <>
          <InputField label="Central Density (kg/m³)" value={p.central_density ?? 5e17} onChange={(v) => update('central_density', parseFloat(v))} type="number" step={1e16} />
          <SliderParam label="Grid Points" value={p.grid_points ?? 200} onChange={(v) => update('grid_points', v)} min={50} max={1000} step={50} />
        </>
      )}

      {simType !== 'tov_star' && (
        <div style={{ fontSize: 11, color: theme.colors.textSecondary, marginTop: 8, padding: 8, background: theme.colors.bgTertiary, borderRadius: 4 }}>
          {simType === 'brill_lindquist'
            ? 'Computes the conformal factor for two momentarily stationary black holes (Brill-Lindquist initial data).'
            : 'Generates approximate gravitational wave strain for a binary black hole inspiral-merger-ringdown.'}
        </div>
      )}
    </>
  );
}
