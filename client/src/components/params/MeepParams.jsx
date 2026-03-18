import React from 'react';
import { InputField, SliderParam, DropdownSelect } from '../shared';

export default function MeepParams({ params, onChange }) {
  const p = params || {};
  const simType = p.simulation_type || 'waveguide_bend';
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
          { value: 'waveguide_bend', label: 'Waveguide 90° Bend' },
          { value: 'ring_resonator', label: 'Ring Resonator' },
          { value: 'photonic_crystal', label: 'Photonic Crystal' },
          { value: 'dipole_radiation', label: 'Dipole Radiation' },
        ]}
      />
      <SliderParam label="Resolution (px/unit)" value={sub.resolution ?? 30} onChange={(v) => updateSub('resolution', v)} min={10} max={80} step={5} />
      <InputField label="Wavelength (µm)" value={sub.wavelength ?? 1.55} onChange={(v) => updateSub('wavelength', v)} type="number" step={0.01} />
      <InputField label="Core Index" value={sub.n_core ?? 3.4} onChange={(v) => updateSub('n_core', v)} type="number" step={0.1} />
      <InputField label="Waveguide Width" value={sub.waveguide_width ?? 1.0} onChange={(v) => updateSub('waveguide_width', v)} type="number" step={0.1} />
      <SliderParam label="Run Time" value={sub.run_time ?? 200} onChange={(v) => updateSub('run_time', v)} min={50} max={1000} step={50} />
      {simType === 'ring_resonator' && (
        <>
          <InputField label="Ring Radius" value={sub.ring_radius ?? 5.0} onChange={(v) => updateSub('ring_radius', v)} type="number" step={0.5} />
          <InputField label="Gap" value={sub.gap ?? 0.1} onChange={(v) => updateSub('gap', v)} type="number" step={0.05} />
        </>
      )}
      {simType === 'photonic_crystal' && (
        <>
          <InputField label="Rod Radius" value={sub.rod_radius ?? 0.2} onChange={(v) => updateSub('rod_radius', v)} type="number" step={0.05} />
          <InputField label="Lattice Constant" value={sub.lattice_constant ?? 1.0} onChange={(v) => updateSub('lattice_constant', v)} type="number" step={0.1} />
          <SliderParam label="Nx (rods)" value={sub.nx ?? 7} onChange={(v) => updateSub('nx', v)} min={3} max={15} step={2} />
          <SliderParam label="Ny (rods)" value={sub.ny ?? 7} onChange={(v) => updateSub('ny', v)} min={3} max={15} step={2} />
        </>
      )}
    </>
  );
}
