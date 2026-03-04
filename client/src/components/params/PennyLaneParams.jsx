import React from 'react';
import { InputField, DropdownSelect, SliderParam } from '../shared';
import theme from '../../theme.json';

export default function PennyLaneParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'circuit_simulation';

  return (
    <>
      <DropdownSelect
        label="Simulation Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'circuit_simulation', label: 'Circuit Simulation' },
          { value: 'vqe', label: 'VQE' },
          { value: 'parameter_optimization', label: 'Parameter Optimization' },
        ]}
      />

      <InputField
        label="Qubits"
        value={p.n_qubits ?? 2}
        onChange={(v) => update('n_qubits', parseInt(v) || 2)}
        type="number"
        step={1}
      />

      {simType === 'circuit_simulation' && (
        <>
          <div style={{ marginTop: 8 }}>
            <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
              Gates (JSON array)
            </label>
            <textarea
              value={JSON.stringify(p.gates || [{"name":"h","wires":[0]},{"name":"cx","wires":[0,1]}], null, 1)}
              onChange={(e) => { try { update('gates', JSON.parse(e.target.value)); } catch {} }}
              rows={4}
              style={{
                width: '100%', background: theme.colors.bgTertiary,
                border: `1px solid ${theme.colors.border}`, borderRadius: 4,
                color: theme.colors.text, padding: 8, fontSize: 11,
                fontFamily: theme.fonts.mono, resize: 'vertical',
              }}
            />
          </div>
          <InputField
            label="Shots"
            value={p.n_shots ?? 1000}
            onChange={(v) => update('n_shots', parseInt(v) || 1000)}
            type="number"
          />
        </>
      )}

      {simType === 'vqe' && (
        <>
          <div style={{ marginTop: 8 }}>
            <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
              Hamiltonian (JSON [{'{'}coeff, pauli_string{'}'}])
            </label>
            <textarea
              value={JSON.stringify(p.hamiltonian || [{"coeff":-0.5,"pauli_string":"II"},{"coeff":0.5,"pauli_string":"ZZ"}], null, 1)}
              onChange={(e) => { try { update('hamiltonian', JSON.parse(e.target.value)); } catch {} }}
              rows={4}
              style={{
                width: '100%', background: theme.colors.bgTertiary,
                border: `1px solid ${theme.colors.border}`, borderRadius: 4,
                color: theme.colors.text, padding: 8, fontSize: 11,
                fontFamily: theme.fonts.mono, resize: 'vertical',
              }}
            />
          </div>
          <DropdownSelect
            label="Ansatz"
            value={p.ansatz || 'basic'}
            onChange={(v) => update('ansatz', v)}
            options={[
              { value: 'basic', label: 'Basic' },
              { value: 'hardware_efficient', label: 'Hardware Efficient' },
            ]}
          />
          <DropdownSelect
            label="Optimizer"
            value={p.optimizer || 'gradient_descent'}
            onChange={(v) => update('optimizer', v)}
            options={[
              { value: 'gradient_descent', label: 'Gradient Descent' },
              { value: 'adam', label: 'Adam' },
            ]}
          />
          <InputField
            label="Max Iterations"
            value={p.max_iterations ?? 100}
            onChange={(v) => update('max_iterations', parseInt(v) || 100)}
            type="number"
          />
          <InputField
            label="Step Size"
            value={p.step_size ?? 0.4}
            onChange={(v) => update('step_size', parseFloat(v) || 0.4)}
            type="number"
            step={0.05}
          />
        </>
      )}

      {simType === 'parameter_optimization' && (
        <>
          <DropdownSelect
            label="Ansatz"
            value={p.ansatz || 'basic'}
            onChange={(v) => update('ansatz', v)}
            options={[
              { value: 'basic', label: 'Basic' },
              { value: 'hardware_efficient', label: 'Hardware Efficient' },
            ]}
          />
          <InputField
            label="Max Iterations"
            value={p.max_iterations ?? 100}
            onChange={(v) => update('max_iterations', parseInt(v) || 100)}
            type="number"
          />
          <div style={{ marginTop: 8 }}>
            <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
              Target State (JSON array, e.g. [0.707, 0, 0, 0.707])
            </label>
            <textarea
              value={typeof p.target_state === 'string' ? p.target_state : JSON.stringify(p.target_state || null, null, 1)}
              onChange={(e) => { try { const v = JSON.parse(e.target.value); update('target_state', v); } catch { update('target_state', e.target.value); } }}
              rows={2}
              placeholder="Leave empty for default |+...+> state"
              style={{
                width: '100%', background: theme.colors.bgTertiary,
                border: `1px solid ${theme.colors.border}`, borderRadius: 4,
                color: theme.colors.text, padding: 8, fontSize: 11,
                fontFamily: "'JetBrains Mono', monospace", resize: 'vertical',
              }}
            />
          </div>
        </>
      )}

      <div style={{ fontSize: 11, color: '#2dd4bf', marginTop: 8, padding: 8, background: '#2dd4bf11', borderRadius: 4, border: '1px solid #2dd4bf33' }}>
        VQE exports gate sequences for Qiskit coupling (PennyLane → Qiskit).
      </div>
    </>
  );
}
