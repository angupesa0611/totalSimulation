import React, { useEffect, useState } from 'react';
import { getLayers, getPresets, getPresetParams } from '../api/client';
import theme from '../theme.json';

const layerColors = theme.colors.layers;

export default function LayerSelector({ onSelectTool, onLoadPreset, selectedTool, onClose }) {
  const [layers, setLayers] = useState([]);
  const [presets, setPresets] = useState([]);

  useEffect(() => {
    getLayers().then(setLayers).catch(console.error);
    getPresets().then(setPresets).catch(console.error);
  }, []);

  const handlePreset = async (preset) => {
    try {
      const params = await getPresetParams(preset.key);
      onLoadPreset(params);
    } catch (err) {
      console.error('Failed to load preset:', err);
    }
  };

  return (
    <div style={{
      width: 260,
      height: '100%',
      background: theme.colors.bgSecondary,
      borderRight: `1px solid ${theme.colors.border}`,
      padding: 16,
      overflowY: 'auto',
      flexShrink: 0,
      boxSizing: 'border-box',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2 style={{ fontSize: 14, color: theme.colors.textSecondary, margin: 0, textTransform: 'uppercase', letterSpacing: 1 }}>
          Simulation Layers
        </h2>
        {onClose && (
          <button
            onClick={onClose}
            style={{
              background: 'none', border: 'none', color: theme.colors.textSecondary,
              fontSize: 18, cursor: 'pointer', padding: '0 4px',
            }}
          >
            {'\u2715'}
          </button>
        )}
      </div>

      {layers.map((layer) => (
        <div key={layer.key} style={{ marginBottom: 20 }}>
          <div style={{
            fontSize: 12,
            fontWeight: 600,
            color: layerColors[layer.key] || theme.colors.accent,
            marginBottom: 8,
            display: 'flex',
            alignItems: 'center',
            gap: 6,
          }}>
            <span style={{
              width: 8, height: 8, borderRadius: '50%',
              background: layerColors[layer.key] || theme.colors.accent,
            }} />
            {layer.name}
          </div>

          {layer.tools.map((tool) => (
            <button
              key={tool.key}
              onClick={() => onSelectTool(tool)}
              style={{
                width: '100%',
                padding: '10px 12px',
                background: selectedTool?.key === tool.key ? theme.colors.bgTertiary : 'transparent',
                border: selectedTool?.key === tool.key
                  ? `1px solid ${layerColors[layer.key] || theme.colors.accent}`
                  : '1px solid transparent',
                borderRadius: 8,
                color: theme.colors.text,
                fontSize: 13,
                textAlign: 'left',
                cursor: 'pointer',
                marginBottom: 4,
                transition: 'all 0.15s',
              }}
            >
              <div style={{ fontWeight: 500 }}>{tool.name}</div>
              <div style={{ fontSize: 11, color: theme.colors.textSecondary, marginTop: 2 }}>
                {tool.description}
              </div>
            </button>
          ))}
        </div>
      ))}

      <div style={{ marginTop: 24, borderTop: `1px solid ${theme.colors.border}`, paddingTop: 16 }}>
        <h2 style={{ fontSize: 14, color: theme.colors.textSecondary, marginBottom: 12, textTransform: 'uppercase', letterSpacing: 1 }}>
          Presets
        </h2>
        {presets.map((preset) => (
          <button
            key={preset.key}
            onClick={() => handlePreset(preset)}
            style={{
              width: '100%',
              padding: '8px 12px',
              background: 'transparent',
              border: '1px solid transparent',
              borderRadius: 6,
              color: theme.colors.text,
              fontSize: 12,
              textAlign: 'left',
              cursor: 'pointer',
              marginBottom: 4,
            }}
          >
            <div style={{ fontWeight: 500 }}>{preset.label}</div>
            <div style={{ fontSize: 11, color: theme.colors.textSecondary }}>{preset.description}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
