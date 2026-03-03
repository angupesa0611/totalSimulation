import React from 'react';
import { InputField, SliderParam, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function EinsteinToolkitParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'bbh_inspiral';

  return (
    <>
      <DropdownSelect
        label="Simulation Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'bbh_inspiral', label: 'Binary Black Hole Inspiral' },
          { value: 'neutron_star', label: 'Neutron Star (TOV)' },
          { value: 'gravitational_waves', label: 'GW Post-Processing' },
        ]}
      />

      <DropdownSelect
        label="Resolution"
        value={p.resolution || 'low'}
        onChange={(v) => update('resolution', v)}
        options={[
          { value: 'low', label: 'Low (dx=2.0M)' },
          { value: 'medium', label: 'Medium (dx=1.0M)' },
          { value: 'high', label: 'High (dx=0.5M)' },
        ]}
      />

      {simType === 'bbh_inspiral' && (
        <>
          <SliderParam label="Mass Ratio (q = m2/m1)" value={p.mass_ratio ?? 1.0} onChange={(v) => update('mass_ratio', v)} min={0.1} max={10} step={0.1} />
          <InputField label="Initial Separation (M)" value={p.initial_separation ?? 10.0} onChange={(v) => update('initial_separation', parseFloat(v))} type="number" step={1} />
          <InputField label="Evolution Time (M)" value={p.evolution_time ?? 50.0} onChange={(v) => update('evolution_time', parseFloat(v))} type="number" step={10} />
          <InputField label="Extraction Radius (M)" value={p.extraction_radius ?? 50.0} onChange={(v) => update('extraction_radius', parseFloat(v))} type="number" step={5} />
        </>
      )}

      {simType === 'neutron_star' && (
        <>
          <InputField label="Central Density (code units)" value={p.central_density ?? 1.28e-3} onChange={(v) => update('central_density', parseFloat(v))} type="number" step={1e-4} />
          <InputField label="EOS Gamma" value={p.eos_gamma ?? 2.0} onChange={(v) => update('eos_gamma', parseFloat(v))} type="number" step={0.1} />
          <InputField label="Evolution Time (M)" value={p.evolution_time ?? 50.0} onChange={(v) => update('evolution_time', parseFloat(v))} type="number" step={10} />
        </>
      )}

      {simType === 'gravitational_waves' && (
        <>
          <SliderParam label="Mass Ratio" value={p.mass_ratio ?? 1.0} onChange={(v) => update('mass_ratio', v)} min={0.1} max={10} step={0.1} />
          <InputField label="Total Mass (solar masses)" value={p.total_mass_solar ?? 60.0} onChange={(v) => update('total_mass_solar', parseFloat(v))} type="number" step={5} />
          <SliderParam label="Output Points" value={p.n_points ?? 500} onChange={(v) => update('n_points', v)} min={100} max={2000} step={100} />
        </>
      )}

      <div style={{
        fontSize: 11,
        color: '#f59e0b',
        marginTop: 12,
        padding: 8,
        background: '#f59e0b11',
        borderRadius: 4,
        border: '1px solid #f59e0b33',
      }}>
        Heavy computation — may take several minutes at medium/high resolution
      </div>

      <div style={{ fontSize: 11, color: theme.colors.textSecondary, marginTop: 8, padding: 8, background: theme.colors.bgTertiary, borderRadius: 4 }}>
        {simType === 'bbh_inspiral'
          ? 'Solves the full Einstein equations for binary black hole inspiral using Cactus + McLachlan (BSSNOK). Extracts Weyl scalar ψ₄ and computes GW strain.'
          : simType === 'neutron_star'
          ? 'Evolves a TOV neutron star with polytropic EOS to test stability. Monitors central lapse and density oscillations.'
          : 'Generates an approximate inspiral-merger-ringdown GW waveform from mass parameters (post-processing mode).'}
      </div>
    </>
  );
}
