import React from 'react';
import { InputField, SliderParam, DropdownSelect } from '../shared';
import theme from '../../theme.json';

export default function MatplotlibParams({ params, onChange }) {
  const p = params || {};
  const update = (key, val) => onChange({ ...p, [key]: val });

  const simType = p.simulation_type || 'line_plot';

  const textareaStyle = {
    width: '100%', background: theme.colors.bgTertiary,
    border: `1px solid ${theme.colors.border}`, borderRadius: 4,
    color: theme.colors.text, padding: 8, fontSize: 12,
    fontFamily: theme.fonts.mono, resize: 'vertical',
  };

  return (
    <>
      <DropdownSelect
        label="Plot Type"
        value={simType}
        onChange={(v) => update('simulation_type', v)}
        options={[
          { value: 'line_plot', label: 'Line Plot' },
          { value: 'scatter_plot', label: 'Scatter Plot' },
          { value: 'histogram', label: 'Histogram' },
          { value: 'heatmap', label: 'Heatmap' },
          { value: 'contour_plot', label: 'Contour Plot' },
          { value: 'bar_chart', label: 'Bar Chart' },
        ]}
      />

      <InputField
        label="Title"
        value={p.title || ''}
        onChange={(v) => update('title', v)}
        placeholder="My Plot"
      />
      <InputField
        label="X Label"
        value={p.xlabel || ''}
        onChange={(v) => update('xlabel', v)}
        placeholder="x"
      />
      <InputField
        label="Y Label"
        value={p.ylabel || ''}
        onChange={(v) => update('ylabel', v)}
        placeholder="y"
      />

      <DropdownSelect
        label="Style"
        value={p.style || 'seaborn-v0_8-darkgrid'}
        onChange={(v) => update('style', v)}
        options={[
          { value: 'seaborn-v0_8-darkgrid', label: 'Seaborn Darkgrid' },
          { value: 'ggplot', label: 'ggplot' },
          { value: 'classic', label: 'Classic' },
          { value: 'dark_background', label: 'Dark Background' },
        ]}
      />

      <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 8, marginBottom: 4 }}>
        Figure Size
      </div>
      <div style={{ display: 'flex', gap: 4 }}>
        <InputField
          label="Width"
          value={p.figure_width ?? 10}
          onChange={(v) => update('figure_width', parseFloat(v) || 10)}
          type="number"
          step={1}
        />
        <InputField
          label="Height"
          value={p.figure_height ?? 6}
          onChange={(v) => update('figure_height', parseFloat(v) || 6)}
          type="number"
          step={1}
        />
      </div>

      <SliderParam
        label="DPI"
        value={p.dpi ?? 150}
        onChange={(v) => update('dpi', v)}
        min={50}
        max={300}
        step={10}
      />

      <DropdownSelect
        label="Output Format"
        value={p.output_format || 'png'}
        onChange={(v) => update('output_format', v)}
        options={[
          { value: 'png', label: 'PNG' },
          { value: 'svg', label: 'SVG' },
          { value: 'pdf', label: 'PDF' },
        ]}
      />

      {(simType === 'line_plot' || simType === 'scatter_plot') && (
        <div style={{ marginTop: 8 }}>
          <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
            Datasets (JSON array of {'{'}x, y, label{'}'})
          </label>
          <textarea
            value={p.datasets || JSON.stringify([{ x: [1,2,3,4,5], y: [2,4,1,3,5], label: 'Series 1' }], null, 2)}
            onChange={(e) => update('datasets', e.target.value)}
            rows={5}
            style={textareaStyle}
          />
        </div>
      )}

      {simType === 'histogram' && (
        <>
          <div style={{ marginTop: 8 }}>
            <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
              Data (JSON array of numbers)
            </label>
            <textarea
              value={p.data || JSON.stringify([1,2,2,3,3,3,4,4,5], null, 2)}
              onChange={(e) => update('data', e.target.value)}
              rows={3}
              style={textareaStyle}
            />
          </div>
          <SliderParam
            label="Bins"
            value={p.bins ?? 30}
            onChange={(v) => update('bins', v)}
            min={5}
            max={100}
            step={1}
          />
          <DropdownSelect
            label="Density"
            value={String(p.density ?? false)}
            onChange={(v) => update('density', v === 'true')}
            options={[
              { value: 'false', label: 'Count' },
              { value: 'true', label: 'Density (normalized)' },
            ]}
          />
        </>
      )}

      {(simType === 'heatmap' || simType === 'contour_plot') && (
        <DropdownSelect
          label="Colormap"
          value={p.colormap || 'viridis'}
          onChange={(v) => update('colormap', v)}
          options={[
            { value: 'viridis', label: 'Viridis' },
            { value: 'hot', label: 'Hot' },
            { value: 'coolwarm', label: 'Coolwarm' },
            { value: 'plasma', label: 'Plasma' },
            { value: 'inferno', label: 'Inferno' },
          ]}
        />
      )}

      {simType === 'bar_chart' && (
        <>
          <div style={{ marginTop: 8 }}>
            <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
              Categories (JSON array of strings)
            </label>
            <textarea
              value={p.categories || JSON.stringify(['A', 'B', 'C', 'D'], null, 2)}
              onChange={(e) => update('categories', e.target.value)}
              rows={2}
              style={textareaStyle}
            />
          </div>
          <div style={{ marginTop: 8 }}>
            <label style={{ fontSize: 12, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
              Values (JSON array of numbers)
            </label>
            <textarea
              value={p.values || JSON.stringify([10, 25, 15, 30], null, 2)}
              onChange={(e) => update('values', e.target.value)}
              rows={2}
              style={textareaStyle}
            />
          </div>
        </>
      )}
    </>
  );
}
