import React from 'react';
import { toolDocs } from './toolDocs';
import theme from '../theme.json';

const LAYER_LABELS = {
  astrophysics: "Astrophysics", quantum: "Quantum Mechanics", molecular: "Molecular Dynamics",
  electronic: "Electronic Structure", analysis: "Analysis", multiscale: "Multiscale",
  mechanics: "Classical Mechanics", continuum: "Continuum Mechanics", relativity: "General Relativity",
  "systems-biology": "Systems Biology", neuroscience: "Neuroscience", evolution: "Population Genetics",
  chemistry: "Chemistry", materials: "Materials Science", mathematics: "Mathematics",
  circuits: "Circuits", visualization: "Visualization", "fluid-dynamics": "Fluid Dynamics",
  engineering: "Engineering",
  optics: "Optics & Photonics",
};

function Section({ title, children }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{
        fontSize: 12,
        fontWeight: 600,
        color: theme.colors.text,
        marginBottom: 6,
        textTransform: 'uppercase',
        letterSpacing: '0.04em',
      }}>
        {title}
      </div>
      {children}
    </div>
  );
}

export default function DocsToolPage({ toolKey, onBack }) {
  const doc = toolDocs[toolKey];
  if (!doc) return <div style={{ padding: 16, color: theme.colors.error }}>Tool not found: {toolKey}</div>;

  const color = theme.colors.layers[doc.layer] || theme.colors.accent;

  return (
    <div>
      {/* Back button */}
      <button
        onClick={onBack}
        style={{
          background: 'none', border: 'none', color: theme.colors.accent,
          fontSize: 12, cursor: 'pointer', padding: '4px 0', marginBottom: 12,
        }}
      >
        ← Back to tools
      </button>

      {/* Header */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
          <span style={{ fontSize: 18, fontWeight: 700, color: theme.colors.text }}>{doc.name}</span>
          <span style={{
            fontSize: 10, color, background: `${color}18`, padding: '2px 8px',
            borderRadius: 4, border: `1px solid ${color}33`,
          }}>
            {LAYER_LABELS[doc.layer] || doc.layer}
          </span>
        </div>
        <div style={{ fontSize: 13, color: theme.colors.textSecondary, lineHeight: 1.4 }}>
          {doc.summary}
        </div>
      </div>

      {/* Description */}
      <Section title="Description">
        <div style={{ fontSize: 12, color: theme.colors.text, lineHeight: 1.6 }}>
          {doc.description}
        </div>
      </Section>

      {/* Capabilities */}
      {doc.capabilities && doc.capabilities.length > 0 && (
        <Section title="Capabilities">
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: theme.colors.text, lineHeight: 1.8 }}>
            {doc.capabilities.map((c, i) => <li key={i}>{c}</li>)}
          </ul>
        </Section>
      )}

      {/* When to Use */}
      {doc.whenToUse && (
        <Section title="When to Use">
          <div style={{ fontSize: 12, color: theme.colors.text, lineHeight: 1.6 }}>
            {doc.whenToUse}
          </div>
        </Section>
      )}

      {/* Alternatives */}
      {doc.alternatives && (
        <Section title="Alternatives">
          <div style={{ fontSize: 12, color: theme.colors.textSecondary, lineHeight: 1.6, fontStyle: 'italic' }}>
            {doc.alternatives}
          </div>
        </Section>
      )}

      {/* Parameters Table */}
      {doc.params && Object.keys(doc.params).length > 0 && (
        <Section title="Parameters">
          <div style={{ fontSize: 11 }}>
            {Object.entries(doc.params).map(([name, param]) => (
              <div key={name} style={{
                padding: '8px 10px',
                marginBottom: 4,
                background: theme.colors.bgTertiary,
                borderRadius: 4,
                border: `1px solid ${theme.colors.border}`,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                  <code style={{
                    fontSize: 11, fontWeight: 600, color: theme.colors.accent,
                    fontFamily: theme.fonts.mono,
                  }}>
                    {name}
                  </code>
                  <span style={{
                    fontSize: 9, color: theme.colors.textSecondary,
                    background: theme.colors.bg, padding: '1px 5px', borderRadius: 3,
                  }}>
                    {param.type}
                  </span>
                  {param.unit && (
                    <span style={{ fontSize: 9, color: theme.colors.warning }}>
                      {param.unit}
                    </span>
                  )}
                </div>
                <div style={{ fontSize: 11, color: theme.colors.text, lineHeight: 1.4 }}>
                  {param.description}
                </div>
                {param.range && (
                  <div style={{ fontSize: 10, color: theme.colors.textSecondary, marginTop: 2 }}>
                    Range: {param.range}
                  </div>
                )}
                {param.options && typeof param.options === 'object' && (
                  <div style={{ marginTop: 4 }}>
                    {Object.entries(param.options).map(([val, desc]) => (
                      <div key={val} style={{ fontSize: 10, color: theme.colors.textSecondary, marginLeft: 8, lineHeight: 1.5 }}>
                        <code style={{ color: theme.colors.accent, fontFamily: theme.fonts.mono }}>{val}</code>
                        {' — '}{desc}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Outputs */}
      {doc.outputs && Object.keys(doc.outputs).length > 0 && (
        <Section title="Outputs">
          <div style={{ fontSize: 11 }}>
            {Object.entries(doc.outputs).map(([name, desc]) => (
              <div key={name} style={{
                display: 'flex', gap: 8, padding: '4px 0',
                borderBottom: `1px solid ${theme.colors.border}22`,
              }}>
                <code style={{
                  fontSize: 11, color: theme.colors.success, fontFamily: theme.fonts.mono,
                  minWidth: 100, flexShrink: 0,
                }}>
                  {name}
                </code>
                <span style={{ color: theme.colors.text }}>{desc}</span>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Examples */}
      {doc.examples && doc.examples.length > 0 && (
        <Section title="Examples">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {doc.examples.map((ex, i) => (
              <span key={i} style={{
                fontSize: 11, padding: '3px 8px',
                background: theme.colors.bgTertiary, borderRadius: 4,
                border: `1px solid ${theme.colors.border}`,
                color: theme.colors.text,
              }}>
                {ex}
              </span>
            ))}
          </div>
        </Section>
      )}

      {/* References */}
      {doc.references && doc.references.length > 0 && (
        <Section title="References">
          {doc.references.map((ref, i) => (
            <a
              key={i}
              href={ref.url}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'block', fontSize: 11, color: theme.colors.accent,
                textDecoration: 'none', marginBottom: 4,
              }}
            >
              {ref.label} ↗
            </a>
          ))}
        </Section>
      )}

      {/* License + Limitations */}
      <div style={{ display: 'flex', gap: 16, marginTop: 8 }}>
        {doc.license && (
          <div>
            <span style={{ fontSize: 10, color: theme.colors.textSecondary }}>License: </span>
            <span style={{ fontSize: 10, color: theme.colors.text }}>{doc.license}</span>
          </div>
        )}
      </div>

      {doc.limitations && doc.limitations.length > 0 && (
        <Section title="Limitations">
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 11, color: theme.colors.warning, lineHeight: 1.8 }}>
            {doc.limitations.map((l, i) => <li key={i}>{l}</li>)}
          </ul>
        </Section>
      )}
    </div>
  );
}
