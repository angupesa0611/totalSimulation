import React from 'react';
import { InputField, SliderParam, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function NestParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'balanced_network';

  const bn = p.balanced_network || {};
  const updateBN = (key, val) => update('balanced_network', { ...bn, [key]: val });

  return (
    <>
      <DropdownSelect
        label="Simulation Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'balanced_network', label: 'Balanced Network (Brunel)' },
          { value: 'cortical_column', label: 'Cortical Column' },
          { value: 'synfire_chain', label: 'Synfire Chain' },
          { value: 'stdp_learning', label: 'STDP Learning' },
        ]}
      />

      <InputField label="Duration (ms)" value={p.duration_ms ?? 500} onChange={(v) => update('duration_ms', parseFloat(v))} type="number" step={50} />
      <InputField label="dt (ms)" value={p.dt_ms ?? 0.1} onChange={(v) => update('dt_ms', parseFloat(v))} type="number" step={0.01} />
      <SliderParam label="Record Neurons" value={p.record_n_neurons ?? 50} onChange={(v) => update('record_n_neurons', v)} min={10} max={200} step={10} />

      {simType === 'balanced_network' && (
        <>
          <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
            Balanced Network Parameters
          </div>
          <SliderParam label="Excitatory" value={bn.n_excitatory ?? 4000} onChange={(v) => updateBN('n_excitatory', v)} min={100} max={10000} step={100} />
          <SliderParam label="Inhibitory" value={bn.n_inhibitory ?? 1000} onChange={(v) => updateBN('n_inhibitory', v)} min={25} max={2500} step={25} />
          <DropdownSelect
            label="Neuron Model"
            value={bn.neuron_model || 'iaf_psc_alpha'}
            onChange={(v) => updateBN('neuron_model', v)}
            options={['iaf_psc_alpha', 'iaf_psc_exp', 'iaf_psc_delta']}
          />
          <InputField label="Connection Prob" value={bn.connection_probability ?? 0.1} onChange={(v) => updateBN('connection_probability', parseFloat(v))} type="number" step={0.01} />
          <InputField label="Weight Exc" value={bn.weight_exc ?? 0.1} onChange={(v) => updateBN('weight_exc', parseFloat(v))} type="number" step={0.01} />
          <InputField label="Inh Factor" value={bn.weight_inh_factor ?? -5.0} onChange={(v) => updateBN('weight_inh_factor', parseFloat(v))} type="number" step={0.5} />
          <InputField label="Delay (ms)" value={bn.delay_ms ?? 1.5} onChange={(v) => updateBN('delay_ms', parseFloat(v))} type="number" step={0.1} />
          <InputField label="External Rate (Hz)" value={bn.external_rate_hz ?? 8000} onChange={(v) => updateBN('external_rate_hz', parseFloat(v))} type="number" step={500} />
        </>
      )}

      <div style={{ fontSize: 11, color: '#f43f5e', marginTop: 8, padding: 8, background: '#f43f5e11', borderRadius: 4, border: '1px solid #f43f5e33' }}>
        Requires NEST container (--profile neuro). Large-scale neural simulation with internal thread pool.
      </div>
    </>
  );
}
