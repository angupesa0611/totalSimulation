import React from 'react';
import { InputField, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function GapParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'group_properties';

  return (
    <>
      <DropdownSelect
        label="Computation Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'group_properties', label: 'Group Properties' },
          { value: 'character_table', label: 'Character Table' },
          { value: 'representation', label: 'Representations' },
          { value: 'space_group', label: 'Space Group' },
          { value: 'stabilizer_codes', label: 'Stabilizer Codes (QEC)' },
        ]}
      />

      {simType !== 'space_group' && (
        <>
          <DropdownSelect
            label="Group Type"
            value={p.group_type || 'symmetric'}
            onChange={(v) => update('group_type', v)}
            options={[
              { value: 'symmetric', label: 'Symmetric Sₙ' },
              { value: 'alternating', label: 'Alternating Aₙ' },
              { value: 'cyclic', label: 'Cyclic Cₙ' },
              { value: 'dihedral', label: 'Dihedral Dₙ' },
            ]}
          />
          <InputField
            label="n (order parameter)"
            value={p.n ?? 5}
            onChange={(v) => update('n', parseInt(v) || 5)}
            type="number"
          />
        </>
      )}

      {simType === 'group_properties' && (
        <DropdownSelect
          label="Compute"
          value={p.compute || 'order'}
          onChange={(v) => update('compute', v)}
          options={[
            { value: 'order', label: 'Order' },
            { value: 'elements', label: 'Elements' },
            { value: 'center', label: 'Center' },
            { value: 'conjugacy_classes', label: 'Conjugacy Classes' },
          ]}
        />
      )}

      {simType === 'space_group' && (
        <InputField
          label="Space Group Number (1-230)"
          value={p.space_group_number ?? 1}
          onChange={(v) => update('space_group_number', parseInt(v) || 1)}
          type="number"
        />
      )}

      {simType === 'stabilizer_codes' && (
        <DropdownSelect
          label="Code Type"
          value={p.code_type || 'steane'}
          onChange={(v) => update('code_type', v)}
          options={[
            { value: 'steane', label: 'Steane [[7,1,3]]' },
            { value: 'shor', label: 'Shor [[9,1,3]]' },
            { value: 'five_qubit', label: 'Five-qubit [[5,1,3]]' },
            { value: 'custom', label: 'Custom generators' },
          ]}
        />
      )}

    </>
  );
}
