import React from 'react';
import { pipelineDocs } from './pipelineDocs';
import theme from '../theme.json';

export default function DocsPipelineList({ searchQuery, onSelectPipeline }) {
  const q = searchQuery?.toLowerCase() || '';

  const filtered = q
    ? Object.entries(pipelineDocs)
        .filter(([key, doc]) =>
          key.includes(q) ||
          doc.label.toLowerCase().includes(q) ||
          doc.summary.toLowerCase().includes(q) ||
          doc.scientificContext.toLowerCase().includes(q) ||
          doc.steps.some(s => s.tool.includes(q) || s.role.toLowerCase().includes(q))
        )
    : Object.entries(pipelineDocs);

  if (filtered.length === 0) {
    return (
      <div style={{ padding: 16, color: theme.colors.textSecondary, fontSize: 12 }}>
        No pipelines match "{searchQuery}"
      </div>
    );
  }

  return (
    <div>
      <div style={{ fontSize: 11, color: theme.colors.textSecondary, marginBottom: 12 }}>
        {Object.keys(pipelineDocs).length} named pipelines — multi-step scientific workflows
      </div>

      {filtered.map(([key, doc]) => (
        <button
          key={key}
          onClick={() => onSelectPipeline(key)}
          style={{
            display: 'block',
            width: '100%',
            padding: '12px 14px',
            marginBottom: 8,
            background: theme.colors.bgTertiary,
            border: `1px solid ${theme.colors.border}`,
            borderLeft: `3px solid #14b8a6`,
            borderRadius: 6,
            cursor: 'pointer',
            textAlign: 'left',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
            <span style={{ fontSize: 14, fontWeight: 600, color: theme.colors.text }}>
              {doc.label}
            </span>
            <span style={{
              fontSize: 10, color: '#14b8a6', background: '#14b8a618',
              padding: '2px 6px', borderRadius: 3, border: '1px solid #14b8a633',
            }}>
              {doc.steps.length} step{doc.steps.length !== 1 ? 's' : ''}
            </span>
          </div>
          <div style={{ fontSize: 11, color: theme.colors.textSecondary, lineHeight: 1.3, marginBottom: 6 }}>
            {doc.summary}
          </div>
          <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
            {doc.steps.map((step, i) => (
              <React.Fragment key={i}>
                {i > 0 && <span style={{ fontSize: 10, color: theme.colors.textSecondary }}>→</span>}
                <span style={{
                  fontSize: 9, padding: '1px 5px',
                  background: theme.colors.bg, borderRadius: 3,
                  border: `1px solid ${theme.colors.border}`,
                  color: theme.colors.text, fontFamily: theme.fonts.mono,
                }}>
                  {step.tool}
                </span>
              </React.Fragment>
            ))}
          </div>
          {doc.expectedRuntime && (
            <div style={{ fontSize: 10, color: theme.colors.textSecondary, marginTop: 6 }}>
              {doc.expectedRuntime}
            </div>
          )}
        </button>
      ))}
    </div>
  );
}
