import React from 'react';
import { InputField, SliderParam, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function Brian2Params({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'lif';

  const lif = p.lif || {};
  const updateLif = (key, val) => update('lif', { ...lif, [key]: val });

  const hh = p.hodgkin_huxley || {};
  const updateHH = (key, val) => update('hodgkin_huxley', { ...hh, [key]: val });

  const iz = p.izhikevich || {};
  const updateIz = (key, val) => update('izhikevich', { ...iz, [key]: val });

  return (
    <>
      <DropdownSelect
        label="Simulation Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'lif', label: 'Leaky Integrate-and-Fire' },
          { value: 'hodgkin_huxley', label: 'Hodgkin-Huxley' },
          { value: 'izhikevich', label: 'Izhikevich' },
          { value: 'custom_equations', label: 'Custom Equations' },
        ]}
      />

      <SliderParam label="Neurons" value={p.n_neurons ?? 100} onChange={(v) => update('n_neurons', v)} min={1} max={5000} step={10} />
      <InputField label="Duration (ms)" value={p.duration_ms ?? 500} onChange={(v) => update('duration_ms', parseFloat(v))} type="number" step={50} />
      <InputField label="dt (ms)" value={p.dt_ms ?? 0.1} onChange={(v) => update('dt_ms', parseFloat(v))} type="number" step={0.01} />

      {simType === 'lif' && (
        <>
          <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
            LIF Parameters
          </div>
          <InputField label="tau_m (ms)" value={lif.tau_m ?? 10} onChange={(v) => updateLif('tau_m', parseFloat(v))} type="number" step={1} />
          <InputField label="V_rest (mV)" value={lif.v_rest ?? -65} onChange={(v) => updateLif('v_rest', parseFloat(v))} type="number" step={1} />
          <InputField label="V_threshold (mV)" value={lif.v_threshold ?? -50} onChange={(v) => updateLif('v_threshold', parseFloat(v))} type="number" step={1} />
          <InputField label="V_reset (mV)" value={lif.v_reset ?? -65} onChange={(v) => updateLif('v_reset', parseFloat(v))} type="number" step={1} />
          <InputField label="Refractory (ms)" value={lif.tau_refrac ?? 2} onChange={(v) => updateLif('tau_refrac', parseFloat(v))} type="number" step={0.5} />
          <InputField label="Input Rate (Hz)" value={lif.input_rate_hz ?? 15} onChange={(v) => updateLif('input_rate_hz', parseFloat(v))} type="number" step={1} />
          <InputField label="Weight (mV)" value={lif.weight ?? 1.5} onChange={(v) => updateLif('weight', parseFloat(v))} type="number" step={0.1} />
        </>
      )}

      {simType === 'hodgkin_huxley' && (
        <>
          <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
            Hodgkin-Huxley Parameters
          </div>
          <InputField label="I_ext (nA)" value={hh.I_ext ?? 10} onChange={(v) => updateHH('I_ext', parseFloat(v))} type="number" step={1} />
          <InputField label="g_Na (mS/cm²)" value={hh.g_Na ?? 120} onChange={(v) => updateHH('g_Na', parseFloat(v))} type="number" step={10} />
          <InputField label="g_K (mS/cm²)" value={hh.g_K ?? 36} onChange={(v) => updateHH('g_K', parseFloat(v))} type="number" step={1} />
          <InputField label="g_L (mS/cm²)" value={hh.g_L ?? 0.3} onChange={(v) => updateHH('g_L', parseFloat(v))} type="number" step={0.1} />
        </>
      )}

      {simType === 'izhikevich' && (
        <>
          <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
            Izhikevich Parameters
          </div>
          <DropdownSelect
            label="Neuron Type"
            value={iz.neuron_type || 'RS'}
            onChange={(v) => updateIz('neuron_type', v)}
            options={[
              { value: 'RS', label: 'Regular Spiking' },
              { value: 'IB', label: 'Intrinsically Bursting' },
              { value: 'CH', label: 'Chattering' },
              { value: 'FS', label: 'Fast Spiking' },
              { value: 'LTS', label: 'Low-Threshold Spiking' },
            ]}
          />
          <InputField label="I_ext (mV)" value={iz.I_ext ?? 10} onChange={(v) => updateIz('I_ext', parseFloat(v))} type="number" step={1} />
        </>
      )}

      {simType === 'custom_equations' && (
        <>
          <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
            Custom Brian2 Equations
          </div>
          <textarea
            value={p.equations || 'dv/dt = -v / (10*ms) : volt'}
            onChange={(e) => update('equations', e.target.value)}
            style={{
              width: '100%', height: 60, padding: 8,
              background: theme.colors.bgTertiary, color: theme.colors.text,
              border: `1px solid ${theme.colors.border}`, borderRadius: 6,
              fontFamily: theme.fonts.mono, fontSize: 11, resize: 'vertical',
            }}
          />
          <InputField label="Threshold" value={p.threshold || 'v > -50*mV'} onChange={(v) => update('threshold', v)} />
          <InputField label="Reset" value={p.reset || 'v = -65*mV'} onChange={(v) => update('reset', v)} />
        </>
      )}

      <div style={{ fontSize: 11, color: '#f43f5e', marginTop: 8, padding: 8, background: '#f43f5e11', borderRadius: 4, border: '1px solid #f43f5e33' }}>
        Spiking neural network simulator. Can receive input current from BasiCO pipeline.
      </div>
    </>
  );
}
