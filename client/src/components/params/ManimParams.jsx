import React from 'react';
import { InputField, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function ManimParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'equation_animation';

  const textareaStyle = {
    width: '100%', background: theme.colors.bgTertiary,
    border: `1px solid ${theme.colors.border}`, borderRadius: 4,
    color: theme.colors.text, padding: 8, fontSize: 12,
    fontFamily: theme.fonts.mono, resize: 'vertical',
  };

  return (
    <>
      <DropdownSelect
        label="Scene Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'equation_animation', label: 'Equation Animation' },
          { value: 'graph_animation', label: 'Graph Animation' },
          { value: 'geometry_animation', label: 'Geometry Animation' },
          { value: 'function_plot', label: 'Function Plot' },
          { value: 'bloch_sphere', label: 'Bloch Sphere (3D)' },
          { value: 'custom_scene', label: 'Custom Scene' },
        ]}
      />

      <DropdownSelect
        label="Quality"
        value={p.quality || 'medium_quality'}
        onChange={(v) => update('quality', v)}
        options={[
          { value: 'low_quality', label: 'Low (480p, fast)' },
          { value: 'medium_quality', label: 'Medium (720p)' },
          { value: 'high_quality', label: 'High (1080p)' },
        ]}
      />

      <DropdownSelect
        label="Output Format"
        value={p.format || 'mp4'}
        onChange={(v) => update('format', v)}
        options={[
          { value: 'mp4', label: 'MP4 (video)' },
          { value: 'gif', label: 'GIF (animated)' },
        ]}
      />

      {simType === 'equation_animation' && (
        <>
          <div style={{ marginTop: 8 }}>
            <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
              Expressions (one LaTeX per line)
            </label>
            <textarea
              value={
                Array.isArray(p.expressions)
                  ? p.expressions.join('\n')
                  : (p.expressions || 'E = mc^2\n\\int_0^\\infty e^{-x} dx = 1')
              }
              onChange={(e) => update('expressions', e.target.value.split('\n').filter(s => s.trim()))}
              rows={4}
              style={textareaStyle}
            />
          </div>
          <DropdownSelect
            label="Animation Type"
            value={p.animation_type || 'write'}
            onChange={(v) => update('animation_type', v)}
            options={[
              { value: 'write', label: 'Write (draw stroke by stroke)' },
              { value: 'transform', label: 'Transform (morph between)' },
              { value: 'fade', label: 'Fade In' },
            ]}
          />
        </>
      )}

      {simType === 'function_plot' && (
        <>
          <div style={{ marginTop: 8 }}>
            <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
              Functions (one per line, e.g. "np.sin(x)")
            </label>
            <textarea
              value={
                Array.isArray(p.functions)
                  ? p.functions.join('\n')
                  : (p.functions || 'np.sin(x)\nnp.cos(x)')
              }
              onChange={(e) => update('functions', e.target.value.split('\n').filter(s => s.trim()))}
              rows={3}
              style={textareaStyle}
            />
          </div>
          <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
            X Range
          </div>
          <div style={{ display: 'flex', gap: 4 }}>
            <InputField
              label="Min"
              value={p.x_min ?? -4}
              onChange={(v) => update('x_min', parseFloat(v))}
              type="number"
              step={0.5}
            />
            <InputField
              label="Max"
              value={p.x_max ?? 4}
              onChange={(v) => update('x_max', parseFloat(v))}
              type="number"
              step={0.5}
            />
          </div>
        </>
      )}

      {simType === 'bloch_sphere' && (
        <div style={{ marginTop: 8 }}>
          <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
            Trajectory (JSON arrays for x, y, z)
          </label>
          <textarea
            value={p.trajectory_json || JSON.stringify({
              x: [0, 0.3, 0.6, 0.8, 1.0, 0.8, 0.6, 0.3, 0],
              y: [0, 0.3, 0.6, 0.8, 0.6, 0.3, 0, -0.3, 0],
              z: [1, 0.9, 0.6, 0.2, 0, -0.2, -0.6, -0.9, -1],
            }, null, 2)}
            onChange={(e) => {
              update('trajectory_json', e.target.value);
              try {
                const d = JSON.parse(e.target.value);
                update('trajectory_x', d.x || []);
                update('trajectory_y', d.y || []);
                update('trajectory_z', d.z || []);
              } catch {}
            }}
            rows={6}
            style={textareaStyle}
          />
          <div style={{ fontSize: 11, color: '#a78bfa', marginTop: 4 }}>
            Use QuTiP → Manim coupling to auto-populate from Bloch vector output.
          </div>
        </div>
      )}

      {simType === 'custom_scene' && (
        <div style={{ marginTop: 8 }}>
          <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
            Scene Code (Python, inherits from Scene)
          </label>
          <textarea
            value={p.scene_code || `def construct(self):\n    circle = Circle()\n    self.play(Create(circle))\n    self.wait(1)`}
            onChange={(e) => update('scene_code', e.target.value)}
            rows={10}
            style={{ ...textareaStyle, fontSize: 11 }}
          />
        </div>
      )}
    </>
  );
}
