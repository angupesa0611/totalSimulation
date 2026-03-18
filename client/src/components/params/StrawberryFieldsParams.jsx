import React from 'react';
import { InputField, SliderParam, DropdownSelect } from '../shared';

export default function StrawberryFieldsParams({ params, onChange }) {
  const p = params || {};
  const simType = p.simulation_type || 'hong_ou_mandel';
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
          { value: 'squeezed_state', label: 'Squeezed State' },
          { value: 'hong_ou_mandel', label: 'Hong-Ou-Mandel Effect' },
          { value: 'boson_sampling', label: 'Boson Sampling' },
          { value: 'gaussian_state', label: 'Gaussian State' },
        ]}
      />
      {simType === 'squeezed_state' && (
        <>
          <InputField label="Squeezing Parameter (r)" value={sub.squeezing_param ?? 0.5} onChange={(v) => updateSub('squeezing_param', v)} type="number" step={0.1} />
          <InputField label="Phase (φ)" value={sub.phase ?? 0.0} onChange={(v) => updateSub('phase', v)} type="number" step={0.1} />
          <SliderParam label="Cutoff Dimension" value={sub.cutoff_dim ?? 20} onChange={(v) => updateSub('cutoff_dim', v)} min={5} max={50} step={5} />
          <SliderParam label="Shots" value={sub.n_shots ?? 1000} onChange={(v) => updateSub('n_shots', v)} min={100} max={5000} step={100} />
        </>
      )}
      {simType === 'hong_ou_mandel' && (
        <>
          <InputField label="Beam Splitter Angle (rad)" value={sub.beam_splitter_angle ?? 0.7854} onChange={(v) => updateSub('beam_splitter_angle', v)} type="number" step={0.01} />
          <SliderParam label="Cutoff Dimension" value={sub.cutoff_dim ?? 10} onChange={(v) => updateSub('cutoff_dim', v)} min={5} max={30} step={1} />
          <SliderParam label="Shots" value={sub.n_shots ?? 1000} onChange={(v) => updateSub('n_shots', v)} min={100} max={5000} step={100} />
        </>
      )}
      {simType === 'boson_sampling' && (
        <>
          <SliderParam label="Modes" value={sub.n_modes ?? 4} onChange={(v) => updateSub('n_modes', v)} min={2} max={8} step={1} />
          <SliderParam label="Photons" value={sub.n_photons ?? 2} onChange={(v) => updateSub('n_photons', v)} min={1} max={4} step={1} />
          <SliderParam label="Cutoff Dimension" value={sub.cutoff_dim ?? 7} onChange={(v) => updateSub('cutoff_dim', v)} min={4} max={15} step={1} />
          <SliderParam label="Shots" value={sub.n_shots ?? 500} onChange={(v) => updateSub('n_shots', v)} min={100} max={2000} step={100} />
        </>
      )}
      {simType === 'gaussian_state' && (
        <>
          <SliderParam label="Modes" value={sub.n_modes ?? 2} onChange={(v) => updateSub('n_modes', v)} min={1} max={4} step={1} />
          <InputField label="Squeezing (r)" value={sub.squeezing_param ?? 0.5} onChange={(v) => updateSub('squeezing_param', v)} type="number" step={0.1} />
          <InputField label="Displacement (α)" value={sub.displacement ?? 1.0} onChange={(v) => updateSub('displacement', v)} type="number" step={0.1} />
        </>
      )}
    </>
  );
}
