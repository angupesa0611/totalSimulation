import React from 'react';
import { InputField, SliderParam, DropdownSelect } from '../shared';
import theme from '../../theme.json';

function ObjectEditor({ objects, onChange }) {
  const addObject = () => {
    const newObj = {
      name: `object_${objects.length}`,
      shape: 'sphere',
      mass: 1.0,
      position: [0, 0, 1],
      velocity: [0, 0, 0],
      radius: 0.3,
    };
    onChange([...objects, newObj]);
  };

  const updateObject = (idx, key, val) => {
    const updated = objects.map((o, i) => i === idx ? { ...o, [key]: val } : o);
    onChange(updated);
  };

  const removeObject = (idx) => {
    onChange(objects.filter((_, i) => i !== idx));
  };

  const parseVec = (str) => {
    const parts = str.split(',').map(s => parseFloat(s.trim()));
    return parts.length === 3 && parts.every(n => !isNaN(n)) ? parts : null;
  };

  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginBottom: 6 }}>
        Objects ({objects.length})
      </div>
      {objects.map((obj, idx) => (
        <div key={idx} style={{
          padding: 8, marginBottom: 6, background: theme.colors.bgTertiary,
          borderRadius: 6, border: `1px solid ${theme.colors.border}`,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
            <input
              value={obj.name || ''}
              onChange={(e) => updateObject(idx, 'name', e.target.value)}
              style={{ background: 'transparent', border: 'none', color: theme.colors.text, fontSize: 12, fontWeight: 600 }}
            />
            <button onClick={() => removeObject(idx)} style={{
              background: 'none', border: 'none', color: theme.colors.error, fontSize: 11, cursor: 'pointer',
            }}>x</button>
          </div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            <select
              value={obj.shape || 'sphere'}
              onChange={(e) => updateObject(idx, 'shape', e.target.value)}
              style={{ flex: 1, minWidth: 80, background: theme.colors.bg, border: `1px solid ${theme.colors.border}`, borderRadius: 4, color: theme.colors.text, fontSize: 11, padding: '2px 4px' }}
            >
              <option value="sphere">Sphere</option>
              <option value="box">Box</option>
              <option value="cylinder">Cylinder</option>
            </select>
            <input
              type="number" value={obj.mass ?? 1.0} step={0.1}
              onChange={(e) => updateObject(idx, 'mass', parseFloat(e.target.value) || 1.0)}
              style={{ width: 50, background: theme.colors.bg, border: `1px solid ${theme.colors.border}`, borderRadius: 4, color: theme.colors.text, fontSize: 11, padding: '2px 4px' }}
              title="Mass"
            />
          </div>
          {obj.shape === 'sphere' && (
            <div style={{ marginTop: 4 }}>
              <label style={{ fontSize: 10, color: theme.colors.textSecondary }}>Radius</label>
              <input type="number" value={obj.radius ?? 0.5} step={0.1}
                onChange={(e) => updateObject(idx, 'radius', parseFloat(e.target.value) || 0.5)}
                style={{ width: '100%', background: theme.colors.bg, border: `1px solid ${theme.colors.border}`, borderRadius: 4, color: theme.colors.text, fontSize: 11, padding: '2px 4px', fontFamily: theme.fonts.mono }}
              />
            </div>
          )}
          {obj.shape === 'box' && (
            <div style={{ marginTop: 4 }}>
              <label style={{ fontSize: 10, color: theme.colors.textSecondary }}>Half-Extents (x,y,z)</label>
              <input
                value={(obj.half_extents || [0.5,0.5,0.5]).join(', ')}
                onChange={(e) => { const v = parseVec(e.target.value); if (v) updateObject(idx, 'half_extents', v); }}
                style={{ width: '100%', background: theme.colors.bg, border: `1px solid ${theme.colors.border}`, borderRadius: 4, color: theme.colors.text, fontSize: 11, padding: '2px 4px', fontFamily: theme.fonts.mono }}
              />
            </div>
          )}
          {obj.shape === 'cylinder' && (
            <div style={{ display: 'flex', gap: 4, marginTop: 4 }}>
              <div style={{ flex: 1 }}>
                <label style={{ fontSize: 10, color: theme.colors.textSecondary }}>Radius</label>
                <input type="number" value={obj.radius ?? 0.5} step={0.1}
                  onChange={(e) => updateObject(idx, 'radius', parseFloat(e.target.value) || 0.5)}
                  style={{ width: '100%', background: theme.colors.bg, border: `1px solid ${theme.colors.border}`, borderRadius: 4, color: theme.colors.text, fontSize: 11, padding: '2px 4px' }}
                />
              </div>
              <div style={{ flex: 1 }}>
                <label style={{ fontSize: 10, color: theme.colors.textSecondary }}>Height</label>
                <input type="number" value={obj.height ?? 1.0} step={0.1}
                  onChange={(e) => updateObject(idx, 'height', parseFloat(e.target.value) || 1.0)}
                  style={{ width: '100%', background: theme.colors.bg, border: `1px solid ${theme.colors.border}`, borderRadius: 4, color: theme.colors.text, fontSize: 11, padding: '2px 4px' }}
                />
              </div>
            </div>
          )}
          <div style={{ marginTop: 4 }}>
            <label style={{ fontSize: 10, color: theme.colors.textSecondary }}>Pos (x,y,z)</label>
            <input
              value={(obj.position || [0,0,1]).join(', ')}
              onChange={(e) => { const v = parseVec(e.target.value); if (v) updateObject(idx, 'position', v); }}
              style={{ width: '100%', background: theme.colors.bg, border: `1px solid ${theme.colors.border}`, borderRadius: 4, color: theme.colors.text, fontSize: 11, padding: '2px 4px', fontFamily: theme.fonts.mono }}
            />
          </div>
          <div style={{ marginTop: 4 }}>
            <label style={{ fontSize: 10, color: theme.colors.textSecondary }}>Vel (x,y,z)</label>
            <input
              value={(obj.velocity || [0,0,0]).join(', ')}
              onChange={(e) => { const v = parseVec(e.target.value); if (v) updateObject(idx, 'velocity', v); }}
              style={{ width: '100%', background: theme.colors.bg, border: `1px solid ${theme.colors.border}`, borderRadius: 4, color: theme.colors.text, fontSize: 11, padding: '2px 4px', fontFamily: theme.fonts.mono }}
            />
          </div>
        </div>
      ))}
      <button onClick={addObject} style={{
        width: '100%', padding: 6, background: 'transparent',
        border: `1px dashed ${theme.colors.border}`, borderRadius: 4,
        color: theme.colors.textSecondary, fontSize: 11, cursor: 'pointer',
      }}>+ Add Object</button>
    </div>
  );
}

export default function PybulletParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  return (
    <>
      <DropdownSelect
        label="Simulation Type"
        value={p.simulation_type || 'collision'}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'free_fall', label: 'Free Fall' },
          { value: 'collision', label: 'Collision' },
          { value: 'pendulum', label: 'Pendulum' },
          { value: 'projectile', label: 'Projectile' },
        ]}
      />
      <InputField label="Gravity (m/s²)" value={p.gravity ?? -9.81} onChange={(v) => update('gravity', parseFloat(v))} type="number" step={0.1} />
      <InputField label="Duration (s)" value={p.duration ?? 5.0} onChange={(v) => update('duration', parseFloat(v))} type="number" step={0.5} />
      <InputField label="Timestep (s)" value={p.timestep ?? (1/240)} onChange={(v) => update('timestep', parseFloat(v))} type="number" step={0.001} />
      <SliderParam label="Restitution" value={p.restitution ?? 0.9} onChange={(v) => update('restitution', v)} min={0} max={1} step={0.05} />
      <SliderParam label="Friction" value={p.friction ?? 0.5} onChange={(v) => update('friction', v)} min={0} max={2} step={0.1} />

      {p.simulation_type === 'pendulum' ? (
        <>
          <InputField label="Pendulum Length" value={p.pendulum_length ?? 1.0} onChange={(v) => update('pendulum_length', parseFloat(v))} type="number" step={0.1} />
          <InputField label="Initial Angle (rad)" value={p.initial_angle ?? 0.785} onChange={(v) => update('initial_angle', parseFloat(v))} type="number" step={0.1} />
          <InputField label="Bob Mass" value={p.bob_mass ?? 1.0} onChange={(v) => update('bob_mass', parseFloat(v))} type="number" step={0.1} />
        </>
      ) : (
        <ObjectEditor
          objects={p.objects || []}
          onChange={(objs) => update('objects', objs)}
        />
      )}
    </>
  );
}
