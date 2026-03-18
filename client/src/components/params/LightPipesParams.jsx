import React from 'react';
import { InputField, SliderParam, DropdownSelect } from '../shared';

export default function LightPipesParams({ params, onChange }) {
  const p = params || {};
  const simType = p.simulation_type || 'double_slit';
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
          { value: 'double_slit', label: "Young's Double Slit" },
          { value: 'circular_aperture', label: 'Circular Aperture' },
          { value: 'lens_focus', label: 'Lens Focus' },
          { value: 'interferometer', label: 'Interferometer' },
        ]}
      />
      <InputField label="Wavelength (m)" value={sub.wavelength ?? 532e-9} onChange={(v) => updateSub('wavelength', v)} type="number" step={1e-9} />
      <InputField label="Grid Size (m)" value={sub.grid_size ?? 10e-3} onChange={(v) => updateSub('grid_size', v)} type="number" step={1e-3} />
      <SliderParam label="Grid Points" value={sub.grid_points ?? 512} onChange={(v) => updateSub('grid_points', v)} min={128} max={1024} step={128} />
      {simType === 'double_slit' && (
        <>
          <InputField label="Slit Width (m)" value={sub.slit_width ?? 0.1e-3} onChange={(v) => updateSub('slit_width', v)} type="number" step={0.01e-3} />
          <InputField label="Slit Separation (m)" value={sub.slit_separation ?? 0.2e-3} onChange={(v) => updateSub('slit_separation', v)} type="number" step={0.01e-3} />
          <InputField label="Propagation Distance (m)" value={sub.propagation_distance ?? 1.0} onChange={(v) => updateSub('propagation_distance', v)} type="number" step={0.1} />
        </>
      )}
      {simType === 'circular_aperture' && (
        <>
          <InputField label="Aperture Radius (m)" value={sub.aperture_radius ?? 0.5e-3} onChange={(v) => updateSub('aperture_radius', v)} type="number" step={0.1e-3} />
          <InputField label="Propagation Distance (m)" value={sub.propagation_distance ?? 2.0} onChange={(v) => updateSub('propagation_distance', v)} type="number" step={0.1} />
        </>
      )}
      {simType === 'lens_focus' && (
        <>
          <InputField label="Focal Length (m)" value={sub.focal_length ?? 0.5} onChange={(v) => updateSub('focal_length', v)} type="number" step={0.1} />
          <InputField label="Beam Radius (m)" value={sub.beam_radius ?? 2e-3} onChange={(v) => updateSub('beam_radius', v)} type="number" step={0.5e-3} />
        </>
      )}
      {simType === 'interferometer' && (
        <InputField label="Tilt Angle (rad)" value={sub.tilt_angle ?? 0.001} onChange={(v) => updateSub('tilt_angle', v)} type="number" step={0.0001} />
      )}
    </>
  );
}
