import React from 'react';
import { pipelineDocs } from './pipelineDocs';
import { toolDocs } from './toolDocs';
import theme from '../theme.json';

export default function DocsPipelinePage({ pipelineKey, onBack, onOpenToolDocs }) {
  const doc = pipelineDocs[pipelineKey];
  if (!doc) {
    return (
      <div style={{ padding: 16 }}>
        <button onClick={onBack} style={{
          background: 'none', border: 'none', color: theme.colors.accent,
          fontSize: 12, cursor: 'pointer', padding: '4px 0', marginBottom: 12,
        }}>← Back to pipelines</button>
        <div style={{ color: theme.colors.error, fontSize: 12 }}>
          Pipeline not found: {pipelineKey}
        </div>
      </div>
    );
  }

  return (
    <div>
      <button onClick={onBack} style={{
        background: 'none', border: 'none', color: theme.colors.accent,
        fontSize: 12, cursor: 'pointer', padding: '4px 0', marginBottom: 12,
      }}>← Back to pipelines</button>

      {/* Header */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
          <span style={{ fontSize: 18, fontWeight: 700, color: theme.colors.text }}>
            {doc.label}
          </span>
          <span style={{
            fontSize: 10, color: '#14b8a6', background: '#14b8a618',
            padding: '2px 8px', borderRadius: 4, border: '1px solid #14b8a633',
          }}>
            {doc.steps.length} steps
          </span>
        </div>
        <div style={{ fontSize: 13, color: theme.colors.textSecondary, lineHeight: 1.4 }}>
          {doc.summary}
        </div>
        {doc.expectedRuntime && (
          <div style={{ fontSize: 11, color: theme.colors.textSecondary, marginTop: 4 }}>
            Expected runtime: {doc.expectedRuntime}
          </div>
        )}
      </div>

      {/* Step-by-step flow */}
      <div style={{ marginBottom: 16 }}>
        <div style={{
          fontSize: 12, fontWeight: 600, color: theme.colors.text, marginBottom: 8,
          textTransform: 'uppercase', letterSpacing: '0.04em',
        }}>
          Pipeline Steps
        </div>

        {doc.steps.map((step, i) => {
          const toolDoc = toolDocs[step.tool];
          const color = toolDoc ? theme.colors.layers[toolDoc.layer] || theme.colors.accent : theme.colors.accent;

          return (
            <React.Fragment key={i}>
              {i > 0 && (
                <div style={{
                  display: 'flex', justifyContent: 'center', padding: '4px 0',
                  color: theme.colors.textSecondary, fontSize: 18,
                }}>↓</div>
              )}
              <div style={{
                padding: '10px 12px',
                background: theme.colors.bgTertiary,
                borderRadius: 6,
                border: `1px solid ${theme.colors.border}`,
                borderLeft: `3px solid ${color}`,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{
                      fontSize: 10, color: theme.colors.textSecondary,
                      background: theme.colors.bg, padding: '1px 5px',
                      borderRadius: 3, fontFamily: theme.fonts.mono,
                    }}>
                      {i + 1}
                    </span>
                    <button
                      onClick={() => onOpenToolDocs && onOpenToolDocs(step.tool)}
                      style={{
                        background: 'none', border: 'none', cursor: 'pointer',
                        fontSize: 13, fontWeight: 600, color,
                        textDecoration: 'underline', textDecorationColor: `${color}44`,
                        padding: 0,
                      }}
                    >
                      {toolDoc?.name || step.tool}
                    </button>
                  </div>
                  <span style={{ fontSize: 10, color: theme.colors.textSecondary }}>
                    {step.duration}
                  </span>
                </div>
                <div style={{ fontSize: 11, color: theme.colors.text, lineHeight: 1.4 }}>
                  {step.role}
                </div>
              </div>
            </React.Fragment>
          );
        })}
      </div>

      {/* Scientific Context */}
      {doc.scientificContext && (
        <div style={{ marginBottom: 16 }}>
          <div style={{
            fontSize: 12, fontWeight: 600, color: theme.colors.text, marginBottom: 6,
            textTransform: 'uppercase', letterSpacing: '0.04em',
          }}>
            Scientific Context
          </div>
          <div style={{
            fontSize: 12, color: theme.colors.text, lineHeight: 1.7,
            padding: 12, background: `${theme.colors.accent}08`,
            borderRadius: 6, border: `1px solid ${theme.colors.accent}22`,
          }}>
            {doc.scientificContext}
          </div>
        </div>
      )}

      {/* Recommended Parameters */}
      {doc.recommendedParams && Object.keys(doc.recommendedParams).length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div style={{
            fontSize: 12, fontWeight: 600, color: theme.colors.text, marginBottom: 6,
            textTransform: 'uppercase', letterSpacing: '0.04em',
          }}>
            Recommended Parameters
          </div>
          <div style={{
            padding: 10, background: theme.colors.bg, borderRadius: 6,
            border: `1px solid ${theme.colors.border}`,
            fontFamily: theme.fonts.mono, fontSize: 10,
          }}>
            {Object.entries(doc.recommendedParams).map(([tool, params]) => (
              <div key={tool} style={{ marginBottom: 6 }}>
                <div style={{ color: theme.colors.accent, fontWeight: 600, marginBottom: 2 }}>
                  {tool}:
                </div>
                {Object.entries(params).map(([k, v]) => (
                  <div key={k} style={{ color: theme.colors.text, marginLeft: 12 }}>
                    {k}: <span style={{ color: theme.colors.success }}>
                      {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                    </span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
