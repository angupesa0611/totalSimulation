import React from 'react';
import { getToolsByLayer } from './toolDocs';
import theme from '../theme.json';

const LAYER_LABELS = {
  astrophysics: "Astrophysics",
  quantum: "Quantum Mechanics",
  molecular: "Molecular Dynamics",
  electronic: "Electronic Structure",
  analysis: "Analysis",
  multiscale: "Multiscale",
  mechanics: "Classical Mechanics",
  continuum: "Continuum Mechanics",
  relativity: "General Relativity",
  "systems-biology": "Systems Biology",
  neuroscience: "Neuroscience",
  evolution: "Population Genetics",
  chemistry: "Chemistry",
  materials: "Materials Science",
  mathematics: "Mathematics",
  circuits: "Circuits",
  visualization: "Visualization",
  "fluid-dynamics": "Fluid Dynamics",
  engineering: "Engineering",
  optics: "Optics & Photonics",
};

export default function DocsToolList({ searchQuery, onSelectTool }) {
  const groups = getToolsByLayer();
  const q = searchQuery?.toLowerCase() || '';

  return (
    <div>
      {Object.entries(groups).map(([layer, tools]) => {
        const filtered = q
          ? tools.filter(t =>
              t.key.includes(q) ||
              t.name.toLowerCase().includes(q) ||
              t.summary.toLowerCase().includes(q) ||
              t.description.toLowerCase().includes(q) ||
              layer.includes(q)
            )
          : tools;

        if (filtered.length === 0) return null;

        const color = theme.colors.layers[layer] || theme.colors.accent;

        return (
          <div key={layer} style={{ marginBottom: 16 }}>
            <div style={{
              fontSize: 11,
              fontWeight: 600,
              color,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              marginBottom: 6,
              padding: '4px 0',
              borderBottom: `1px solid ${color}33`,
            }}>
              {LAYER_LABELS[layer] || layer}
            </div>

            {filtered.map(tool => (
              <button
                key={tool.key}
                onClick={() => onSelectTool(tool.key)}
                style={{
                  display: 'block',
                  width: '100%',
                  padding: '8px 10px',
                  marginBottom: 4,
                  background: theme.colors.bgTertiary,
                  border: `1px solid ${theme.colors.border}`,
                  borderLeft: `3px solid ${color}`,
                  borderRadius: 4,
                  cursor: 'pointer',
                  textAlign: 'left',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ fontSize: 13, fontWeight: 600, color: theme.colors.text }}>
                    {tool.name}
                  </span>
                  <span style={{
                    fontSize: 9,
                    color,
                    background: `${color}18`,
                    padding: '1px 5px',
                    borderRadius: 3,
                    border: `1px solid ${color}33`,
                  }}>
                    {LAYER_LABELS[layer] || layer}
                  </span>
                </div>
                <div style={{
                  fontSize: 11,
                  color: theme.colors.textSecondary,
                  marginTop: 3,
                  lineHeight: 1.3,
                }}>
                  {tool.summary}
                </div>
              </button>
            ))}
          </div>
        );
      })}
    </div>
  );
}
