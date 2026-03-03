import React from 'react';
import { InputField, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function ControlParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'transfer_function';

  const hasTF = ['transfer_function', 'bode_plot', 'nyquist_plot', 'root_locus', 'step_response'].includes(simType);
  const hasOmega = ['bode_plot', 'nyquist_plot'].includes(simType);

  const textareaStyle = {
    width: '100%', background: theme.colors.bgTertiary,
    border: `1px solid ${theme.colors.border}`, borderRadius: 4,
    color: theme.colors.text, padding: 8, fontSize: 12,
    fontFamily: theme.fonts.mono, resize: 'vertical',
  };

  return (
    <>
      <DropdownSelect
        label="Analysis Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'transfer_function', label: 'Transfer Function' },
          { value: 'state_space', label: 'State Space' },
          { value: 'bode_plot', label: 'Bode Plot' },
          { value: 'nyquist_plot', label: 'Nyquist Plot' },
          { value: 'root_locus', label: 'Root Locus' },
          { value: 'step_response', label: 'Step Response' },
        ]}
      />

      {hasTF && (
        <>
          <InputField
            label="Numerator (comma-separated)"
            value={
              Array.isArray(p.numerator)
                ? p.numerator.join(',')
                : (p.numerator || '1')
            }
            onChange={(v) => update('numerator', v.split(',').map(Number))}
            placeholder="1"
          />
          <InputField
            label="Denominator (comma-separated)"
            value={
              Array.isArray(p.denominator)
                ? p.denominator.join(',')
                : (p.denominator || '1,1')
            }
            onChange={(v) => update('denominator', v.split(',').map(Number))}
            placeholder="1,1"
          />
        </>
      )}

      {hasOmega && (
        <>
          <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
            Omega Range (rad/s)
          </div>
          <div style={{ display: 'flex', gap: 4 }}>
            <InputField
              label="Min"
              value={p.omega_min ?? 0.01}
              onChange={(v) => update('omega_min', parseFloat(v) || 0.01)}
              type="number"
              step={0.01}
            />
            <InputField
              label="Max"
              value={p.omega_max ?? 100}
              onChange={(v) => update('omega_max', parseFloat(v) || 100)}
              type="number"
              step={1}
            />
          </div>
        </>
      )}

      {simType === 'root_locus' && (
        <>
          <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
            K Range
          </div>
          <div style={{ display: 'flex', gap: 4 }}>
            <InputField
              label="K Min"
              value={p.k_min ?? 0}
              onChange={(v) => update('k_min', parseFloat(v))}
              type="number"
              step={0.1}
            />
            <InputField
              label="K Max"
              value={p.k_max ?? 10}
              onChange={(v) => update('k_max', parseFloat(v))}
              type="number"
              step={0.1}
            />
          </div>
        </>
      )}

      {simType === 'step_response' && (
        <InputField
          label="Final Time (s)"
          value={p.t_final ?? 10}
          onChange={(v) => update('t_final', parseFloat(v) || 10)}
          type="number"
          step={0.5}
        />
      )}

      {simType === 'state_space' && (
        <>
          <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
            State Space Matrices (JSON 2D arrays)
          </div>
          <div style={{ marginTop: 8 }}>
            <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
              A Matrix
            </label>
            <textarea
              value={p.A_matrix || JSON.stringify([[-1, 0], [0, -2]], null, 2)}
              onChange={(e) => { try { update('A_matrix', JSON.parse(e.target.value)); } catch { update('A_matrix', e.target.value); } }}
              rows={3}
              style={textareaStyle}
            />
          </div>
          <div style={{ marginTop: 8 }}>
            <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
              B Matrix
            </label>
            <textarea
              value={p.B_matrix || JSON.stringify([[1], [0]], null, 2)}
              onChange={(e) => { try { update('B_matrix', JSON.parse(e.target.value)); } catch { update('B_matrix', e.target.value); } }}
              rows={3}
              style={textareaStyle}
            />
          </div>
          <div style={{ marginTop: 8 }}>
            <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
              C Matrix
            </label>
            <textarea
              value={p.C_matrix || JSON.stringify([[1, 0]], null, 2)}
              onChange={(e) => { try { update('C_matrix', JSON.parse(e.target.value)); } catch { update('C_matrix', e.target.value); } }}
              rows={2}
              style={textareaStyle}
            />
          </div>
          <div style={{ marginTop: 8 }}>
            <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
              D Matrix
            </label>
            <textarea
              value={p.D_matrix || JSON.stringify([[0]], null, 2)}
              onChange={(e) => { try { update('D_matrix', JSON.parse(e.target.value)); } catch { update('D_matrix', e.target.value); } }}
              rows={2}
              style={textareaStyle}
            />
          </div>
        </>
      )}
    </>
  );
}
