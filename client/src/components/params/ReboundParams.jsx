import React, { useState } from 'react';
import { InputField, DropdownSelect, SliderParam } from '../shared';
import theme from '../../theme.json';

const COORD_MODE = { KEP: 'keplerian', CART: 'cartesian' };

function ParticleCard({ particle, index, total, names, onUpdate, onRemove }) {
  const [expanded, setExpanded] = useState(false);
  const isFirst = index === 0;
  const mode = particle._mode || (particle.a != null ? COORD_MODE.KEP : COORD_MODE.CART);

  const set = (key, val) => onUpdate(index, { ...particle, [key]: val });

  const setMode = (newMode) => {
    const base = { name: particle.name, m: particle.m, _mode: newMode };
    if (newMode === COORD_MODE.KEP) {
      onUpdate(index, { ...base, a: 1.0, e: 0.0, primary: 0 });
    } else {
      onUpdate(index, { ...base, x: 0, y: 0, z: 0, vx: 0, vy: 0, vz: 0 });
    }
  };

  const cardStyle = {
    background: theme.colors.bgTertiary,
    border: `1px solid ${theme.colors.border}`,
    borderRadius: 8,
    padding: 10,
    marginBottom: 8,
  };

  const rowStyle = { display: 'flex', gap: 8, alignItems: 'flex-end' };
  const miniLabel = { fontSize: 11, color: theme.colors.textSecondary, marginBottom: 2 };
  const miniInput = {
    width: '100%',
    padding: '5px 8px',
    background: theme.colors.bg,
    border: `1px solid ${theme.colors.border}`,
    borderRadius: 4,
    color: theme.colors.text,
    fontSize: 13,
    outline: 'none',
  };

  const MiniField = ({ label, value, onChange, step, style: extraStyle }) => (
    <div style={{ flex: 1, marginBottom: 6, ...extraStyle }}>
      <div style={miniLabel}>{label}</div>
      <input
        type="number"
        value={value ?? ''}
        onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
        step={step || 'any'}
        style={miniInput}
      />
    </div>
  );

  const NameField = ({ value, onChange }) => (
    <div style={{ flex: 2, marginBottom: 6 }}>
      <div style={miniLabel}>Name</div>
      <input
        type="text"
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        style={miniInput}
        placeholder={`Body ${index + 1}`}
      />
    </div>
  );

  return (
    <div style={cardStyle}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
        <span style={{ fontSize: 12, fontWeight: 600, color: theme.colors.text }}>
          {particle.name || `Body ${index + 1}`}
          {isFirst && <span style={{ color: theme.colors.textSecondary, fontWeight: 400 }}> (central)</span>}
        </span>
        {total > 1 && (
          <button
            onClick={() => onRemove(index)}
            style={{
              background: 'none', border: 'none', color: theme.colors.error,
              cursor: 'pointer', fontSize: 16, padding: '0 4px', lineHeight: 1,
            }}
            title="Remove body"
          >x</button>
        )}
      </div>

      <div style={rowStyle}>
        <NameField value={particle.name} onChange={(v) => set('name', v)} />
        <MiniField label="Mass (M_sun)" value={particle.m} onChange={(v) => set('m', v)} step={0.001} />
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 6 }}>
        <div style={{ flex: 1 }}>
          <div style={miniLabel}>Coordinates</div>
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            style={{ ...miniInput, cursor: 'pointer' }}
          >
            {!isFirst && <option value={COORD_MODE.KEP}>Keplerian</option>}
            <option value={COORD_MODE.CART}>Cartesian</option>
          </select>
        </div>
        {!isFirst && mode === COORD_MODE.KEP && (
          <div style={{ flex: 1 }}>
            <div style={miniLabel}>Primary (index)</div>
            <select
              value={particle.primary ?? 0}
              onChange={(e) => set('primary', parseInt(e.target.value))}
              style={{ ...miniInput, cursor: 'pointer' }}
            >
              {names.slice(0, index).map((n, i) => (
                <option key={i} value={i}>{i}: {n}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      {mode === COORD_MODE.KEP && !isFirst && (
        <>
          <div style={rowStyle}>
            <MiniField label="a (AU)" value={particle.a} onChange={(v) => set('a', v)} step={0.01} />
            <MiniField label="e" value={particle.e} onChange={(v) => set('e', v)} step={0.01} />
          </div>
          <div
            onClick={() => setExpanded(!expanded)}
            style={{ fontSize: 11, color: theme.colors.accent, cursor: 'pointer', marginBottom: expanded ? 6 : 0, userSelect: 'none' }}
          >
            {expanded ? '- Hide' : '+ More'} orbital elements
          </div>
          {expanded && (
            <>
              <div style={rowStyle}>
                <MiniField label="inc (rad)" value={particle.inc} onChange={(v) => set('inc', v)} step={0.01} />
                <MiniField label="omega (rad)" value={particle.omega} onChange={(v) => set('omega', v)} step={0.01} />
              </div>
              <div style={rowStyle}>
                <MiniField label="Omega (rad)" value={particle.Omega} onChange={(v) => set('Omega', v)} step={0.01} />
                <MiniField label="f (rad)" value={particle.f} onChange={(v) => set('f', v)} step={0.01} />
              </div>
            </>
          )}
        </>
      )}

      {mode === COORD_MODE.CART && (
        <>
          <div style={rowStyle}>
            <MiniField label="x (AU)" value={particle.x} onChange={(v) => set('x', v)} />
            <MiniField label="y (AU)" value={particle.y} onChange={(v) => set('y', v)} />
            <MiniField label="z (AU)" value={particle.z} onChange={(v) => set('z', v)} />
          </div>
          <div style={rowStyle}>
            <MiniField label="vx (AU/yr)" value={particle.vx} onChange={(v) => set('vx', v)} />
            <MiniField label="vy (AU/yr)" value={particle.vy} onChange={(v) => set('vy', v)} />
            <MiniField label="vz (AU/yr)" value={particle.vz} onChange={(v) => set('vz', v)} />
          </div>
        </>
      )}
    </div>
  );
}

export default function ReboundParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const particles = p.particles || [];
  const names = particles.map((pt, i) => pt.name || `Body ${i + 1}`);

  const extraForces = p.extra_forces || [];
  const toggleForce = (force) => {
    const next = extraForces.includes(force)
      ? extraForces.filter(f => f !== force)
      : [...extraForces, force];
    update('extra_forces', next);
  };

  const updateParticle = (idx, particle) => {
    const next = [...particles];
    next[idx] = particle;
    update('particles', next);
  };

  const removeParticle = (idx) => {
    update('particles', particles.filter((_, i) => i !== idx));
  };

  const addParticle = () => {
    const newP = particles.length === 0
      ? { name: 'Star', m: 1.0, x: 0, y: 0, z: 0, vx: 0, vy: 0, vz: 0, _mode: COORD_MODE.CART }
      : { name: '', m: 1e-6, a: 1.0, e: 0.0, primary: 0, _mode: COORD_MODE.KEP };
    update('particles', [...particles, newP]);
  };

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <div style={{ fontSize: 12, color: theme.colors.textSecondary }}>
          Particles ({particles.length} {particles.length === 1 ? 'body' : 'bodies'})
        </div>
        <button
          onClick={addParticle}
          style={{
            background: theme.colors.accent,
            border: 'none',
            borderRadius: 4,
            color: '#fff',
            fontSize: 11,
            padding: '4px 10px',
            cursor: 'pointer',
          }}
        >+ Add Body</button>
      </div>

      {particles.map((pt, i) => (
        <ParticleCard
          key={i}
          particle={pt}
          index={i}
          total={particles.length}
          names={names}
          onUpdate={updateParticle}
          onRemove={removeParticle}
        />
      ))}

      {particles.length === 0 && (
        <div style={{
          padding: 16, textAlign: 'center', fontSize: 12,
          color: theme.colors.warning, background: '#1a1a0a',
          borderRadius: 8, border: `1px solid ${theme.colors.warning}33`,
          marginBottom: 12,
        }}>
          Add at least one body to run a simulation
        </div>
      )}

      <DropdownSelect
        label="Integrator"
        value={p.integrator || 'whfast'}
        onChange={(v) => update('integrator', v)}
        options={['ias15', 'whfast', 'mercurius', 'leapfrog']}
      />
      <InputField label="Max Time (yr)" value={p.tmax || 62.83} onChange={(v) => update('tmax', v)} type="number" step={1} />
      <SliderParam label="Output Frames" value={p.n_outputs || 500} onChange={(v) => update('n_outputs', v)} min={50} max={2000} step={50} />
      <InputField label="Timestep (yr)" value={p.dt || 0.01} onChange={(v) => update('dt', v)} type="number" step={0.001} />

      <DropdownSelect
        label="GR Correction (REBOUNDx)"
        value={p.gr_correction || 'none'}
        onChange={(v) => update('gr_correction', v)}
        options={[
          { value: 'none', label: 'None' },
          { value: 'gr', label: 'Post-Newtonian (1PN)' },
          { value: 'gr_full', label: 'Full PN (most accurate)' },
          { value: 'gr_potential', label: 'Potential-only (fast)' },
        ]}
      />

      <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
        Extra Forces (REBOUNDx)
      </div>
      {[
        { key: 'radiation_pressure', label: 'Radiation Pressure' },
        { key: 'tides_constant_time_lag', label: 'Tidal Forces' },
      ].map(f => (
        <label key={f.key} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: theme.colors.text, cursor: 'pointer', marginBottom: 4 }}>
          <input type="checkbox" checked={extraForces.includes(f.key)} onChange={() => toggleForce(f.key)} />
          {f.label}
        </label>
      ))}
    </>
  );
}
