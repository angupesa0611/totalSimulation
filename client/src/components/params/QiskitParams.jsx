import React from 'react';
import { InputField, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function QiskitParams({ params, onChange }) {
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
          { value: 'transpilation', label: 'Transpilation' },
          { value: 'stabilizer_codes', label: 'Stabilizer Codes (QEC)' },
        ]}
      />

      <InputField
        label="Qubits"
        value={p.n_qubits ?? 2}
        onChange={(v) => update('n_qubits', parseInt(v) || 2)}
        type="number"
        step={1}
      />

      {(simType === 'circuit_simulation' || simType === 'transpilation') && (
        <div style={{ marginTop: 8 }}>
          <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
            Gates (JSON array)
          </label>
          <textarea
            value={JSON.stringify(p.gates || [{"name":"h","qubits":[0]},{"name":"cx","qubits":[0,1]}], null, 1)}
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
      )}

      {simType === 'circuit_simulation' && (
        <>
          <InputField
            label="Shots"
            value={p.n_shots ?? 1024}
            onChange={(v) => update('n_shots', parseInt(v) || 1024)}
            type="number"
          />
          <DropdownSelect
            label="Backend"
            value={p.backend || 'qasm'}
            onChange={(v) => update('backend', v)}
            options={[
              { value: 'qasm', label: 'QASM (Measurement)' },
              { value: 'statevector', label: 'Statevector (Exact)' },
            ]}
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
            value={p.ansatz || 'hardware_efficient'}
            onChange={(v) => update('ansatz', v)}
            options={[
              { value: 'hardware_efficient', label: 'Hardware Efficient' },
              { value: 'uccsd', label: 'UCCSD' },
            ]}
          />
          <DropdownSelect
            label="Optimizer"
            value={p.optimizer || 'cobyla'}
            onChange={(v) => update('optimizer', v)}
            options={[
              { value: 'cobyla', label: 'COBYLA' },
              { value: 'spsa', label: 'SPSA' },
            ]}
          />
          <InputField
            label="Max Iterations"
            value={p.max_iterations ?? 100}
            onChange={(v) => update('max_iterations', parseInt(v) || 100)}
            type="number"
          />
        </>
      )}

      {simType === 'transpilation' && (
        <DropdownSelect
          label="Optimization Level"
          value={String(p.optimization_level ?? 1)}
          onChange={(v) => update('optimization_level', parseInt(v))}
          options={[
            { value: '0', label: 'Level 0 (No optimization)' },
            { value: '1', label: 'Level 1 (Light)' },
            { value: '2', label: 'Level 2 (Medium)' },
            { value: '3', label: 'Level 3 (Heavy)' },
          ]}
        />
      )}

      {simType === 'stabilizer_codes' && (
        <>
          <div style={{ marginTop: 8 }}>
            <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
              Generators (JSON array of Pauli strings)
            </label>
            <textarea
              value={JSON.stringify(p.generators || ["IIIXXXX", "IXXIIXX", "XIXIXIX", "IIIZZZZ", "IZZIIZZ", "ZIZIZIZ"], null, 1)}
              onChange={(e) => { try { update('generators', JSON.parse(e.target.value)); } catch {} }}
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
            value={p.n_shots ?? 1024}
            onChange={(v) => update('n_shots', parseInt(v) || 1024)}
            type="number"
          />
        </>
      )}

    </>
  );
}
