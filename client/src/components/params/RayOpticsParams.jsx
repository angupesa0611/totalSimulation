import React from 'react';
import { InputField, SliderParam, DropdownSelect } from '../shared';

export default function RayOpticsParams({ params, onChange }) {
  const p = params || {};
  const simType = p.simulation_type || 'singlet_lens';
  const sub = p[simType] || {};

  const updateSub = (key, val) => {
    onChange({ ...p, [simType]: { ...sub, [key]: val } });
  };

  return (
    <>
      <DropdownSelect
        label="Simulation Type"
        value={simType}
        onChange={(v) => onChange({ ...p, simulation_type: v })}
        options={[
          { value: 'singlet_lens', label: 'Singlet Lens' },
          { value: 'doublet', label: 'Achromatic Doublet' },
          { value: 'spot_diagram', label: 'Spot Diagram' },
        ]}
      />
      <InputField label="Effective Focal Length (mm)" value={sub.efl ?? 100.0} onChange={(v) => updateSub('efl', v)} type="number" step={10} />
      <InputField label="f/Number" value={sub.f_number ?? 5.0} onChange={(v) => updateSub('f_number', v)} type="number" step={0.5} />
      <SliderParam label="Number of Rays" value={sub.n_rays ?? 21} onChange={(v) => updateSub('n_rays', v)} min={5} max={51} step={2} />
      {simType === 'singlet_lens' && (
        <>
          <InputField label="Wavelength (nm)" value={sub.wavelength ?? 587.56} onChange={(v) => updateSub('wavelength', v)} type="number" step={1} />
          <InputField label="R1 (mm)" value={sub.r1 ?? 90.0} onChange={(v) => updateSub('r1', v)} type="number" step={5} />
          <InputField label="R2 (mm)" value={sub.r2 ?? -90.0} onChange={(v) => updateSub('r2', v)} type="number" step={5} />
          <InputField label="Thickness (mm)" value={sub.thickness ?? 6.0} onChange={(v) => updateSub('thickness', v)} type="number" step={1} />
        </>
      )}
      {simType === 'spot_diagram' && (
        <>
          <SliderParam label="Ring Count" value={sub.n_rings ?? 6} onChange={(v) => updateSub('n_rings', v)} min={2} max={12} step={1} />
          <SliderParam label="Arm Count" value={sub.n_arms ?? 6} onChange={(v) => updateSub('n_arms', v)} min={4} max={12} step={1} />
        </>
      )}
    </>
  );
}
