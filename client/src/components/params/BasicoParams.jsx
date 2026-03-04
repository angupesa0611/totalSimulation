import React, { useState } from 'react';
import { InputField, SliderParam, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function BasicoParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'ode_timecourse';

  const [reactionsText, setReactionsText] = useState(
    p.reactions ? JSON.stringify(p.reactions, null, 2) : JSON.stringify([
      { "name": "binding", "scheme": "S + E -> ES" },
      { "name": "unbinding", "scheme": "ES -> S + E" },
      { "name": "catalysis", "scheme": "ES -> P + E" }
    ], null, 2)
  );

  const [speciesText, setSpeciesText] = useState(
    p.species ? JSON.stringify(p.species, null, 2) : JSON.stringify([
      { "name": "S", "initial_concentration": 10.0 },
      { "name": "E", "initial_concentration": 1.0 },
      { "name": "ES", "initial_concentration": 0.0 },
      { "name": "P", "initial_concentration": 0.0 }
    ], null, 2)
  );

  const handleReactionsChange = (text) => {
    setReactionsText(text);
    try {
      const parsed = JSON.parse(text);
      update('reactions', parsed);
    } catch { /* ignore parse errors while typing */ }
  };

  const handleSpeciesChange = (text) => {
    setSpeciesText(text);
    try {
      const parsed = JSON.parse(text);
      update('species', parsed);
    } catch { /* ignore parse errors while typing */ }
  };

  const modelSource = p.model_source || 'reactions';

  const [paramsText, setParamsText] = useState(
    p.parameters ? JSON.stringify(p.parameters, null, 2) : JSON.stringify([
      { "name": "binding.k1", "value": 0.1 },
      { "name": "unbinding.k1", "value": 0.01 },
      { "name": "catalysis.k1", "value": 0.05 }
    ], null, 2)
  );

  const handleParamsChange = (text) => {
    setParamsText(text);
    try { update('parameters', JSON.parse(text)); } catch {}
  };

  return (
    <>
      <DropdownSelect
        label="Simulation Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'ode_timecourse', label: 'ODE Timecourse' },
          { value: 'stochastic_timecourse', label: 'Stochastic Timecourse' },
          { value: 'steady_state', label: 'Steady State' },
          { value: 'parameter_estimation', label: 'Parameter Estimation' },
          { value: 'sensitivity', label: 'Sensitivity Analysis' },
        ]}
      />

      <DropdownSelect
        label="Method"
        value={p.method || 'deterministic'}
        onChange={(v) => update('method', v)}
        options={['deterministic', 'stochastic', 'hybrid']}
      />

      <DropdownSelect
        label="Model Source"
        value={modelSource}
        onChange={(v) => update('model_source', v)}
        options={[
          { value: 'reactions', label: 'Reactions + Species' },
          { value: 'sbml', label: 'SBML (XML)' },
        ]}
      />

      {modelSource === 'reactions' && (
        <>
          <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
            Reactions (JSON)
          </div>
          <textarea
            value={reactionsText}
            onChange={(e) => handleReactionsChange(e.target.value)}
            style={{
              width: '100%', height: 100, padding: 8,
              background: theme.colors.bgTertiary, color: theme.colors.text,
              border: `1px solid ${theme.colors.border}`, borderRadius: 6,
              fontFamily: theme.fonts.mono, fontSize: 11, resize: 'vertical',
            }}
          />

          <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
            Species (JSON)
          </div>
          <textarea
            value={speciesText}
            onChange={(e) => handleSpeciesChange(e.target.value)}
            style={{
              width: '100%', height: 80, padding: 8,
              background: theme.colors.bgTertiary, color: theme.colors.text,
              border: `1px solid ${theme.colors.border}`, borderRadius: 6,
              fontFamily: theme.fonts.mono, fontSize: 11, resize: 'vertical',
            }}
          />

          <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
            Kinetic Parameters (JSON)
          </div>
          <textarea
            value={paramsText}
            onChange={(e) => handleParamsChange(e.target.value)}
            style={{
              width: '100%', height: 80, padding: 8,
              background: theme.colors.bgTertiary, color: theme.colors.text,
              border: `1px solid ${theme.colors.border}`, borderRadius: 6,
              fontFamily: theme.fonts.mono, fontSize: 11, resize: 'vertical',
            }}
          />
        </>
      )}

      {modelSource === 'sbml' && (
        <div style={{ marginTop: 8 }}>
          <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginBottom: 4 }}>
            SBML Model (XML)
          </div>
          <textarea
            value={p.sbml_string || ''}
            onChange={(e) => update('sbml_string', e.target.value)}
            placeholder="Paste SBML XML content here..."
            style={{
              width: '100%', height: 120, padding: 8,
              background: theme.colors.bgTertiary, color: theme.colors.text,
              border: `1px solid ${theme.colors.border}`, borderRadius: 6,
              fontFamily: theme.fonts.mono, fontSize: 11, resize: 'vertical',
            }}
          />
        </div>
      )}

      {(simType === 'ode_timecourse' || simType === 'stochastic_timecourse' || simType === 'sensitivity') && (
        <>
          <InputField label="Duration" value={p.duration ?? 200} onChange={(v) => update('duration', parseFloat(v))} type="number" step={10} />
          <SliderParam label="Steps" value={p.n_steps ?? 200} onChange={(v) => update('n_steps', v)} min={50} max={1000} step={50} />
        </>
      )}

      <div style={{ fontSize: 11, color: '#10b981', marginTop: 8, padding: 8, background: '#10b98111', borderRadius: 4, border: '1px solid #10b98133' }}>
        COPASI-powered biochemical kinetics. Output can be piped to Brian2 for neuro coupling.
      </div>
    </>
  );
}
