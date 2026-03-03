import React from 'react';
import { couplingDocs } from './couplingDocs';
import { toolDocs } from './toolDocs';
import theme from '../theme.json';

const TIER_COLORS = {
  core: theme.colors.success,
  extension: theme.colors.accent,
  research: theme.colors.warning,
};

export default function DocsCouplingPage({ couplingKey, onBack }) {
  const detail = couplingDocs.details[couplingKey];
  if (!detail) {
    return (
      <div style={{ padding: 16 }}>
        <button onClick={onBack} style={{
          background: 'none', border: 'none', color: theme.colors.accent,
          fontSize: 12, cursor: 'pointer', padding: '4px 0', marginBottom: 12,
        }}>← Back to couplings</button>
        <div style={{ color: theme.colors.error, fontSize: 12 }}>
          No detailed documentation for: {couplingKey}
        </div>
      </div>
    );
  }

  const fromTool = toolDocs[detail.from];
  const toTool = toolDocs[detail.to];
  const fromColor = fromTool ? theme.colors.layers[fromTool.layer] || theme.colors.accent : theme.colors.accent;
  const toColor = toTool ? theme.colors.layers[toTool.layer] || theme.colors.accent : theme.colors.accent;
  const tierColor = TIER_COLORS[detail.tier] || theme.colors.textSecondary;

  return (
    <div>
      <button onClick={onBack} style={{
        background: 'none', border: 'none', color: theme.colors.accent,
        fontSize: 12, cursor: 'pointer', padding: '4px 0', marginBottom: 12,
      }}>← Back to couplings</button>

      {/* Header with arrow */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10,
        marginBottom: 16, padding: '12px 14px',
        background: theme.colors.bgTertiary, borderRadius: 8,
        border: `1px solid ${theme.colors.border}`,
      }}>
        <span style={{
          fontSize: 14, fontWeight: 700, color: fromColor,
        }}>
          {fromTool?.name || detail.from}
        </span>
        <span style={{ fontSize: 16, color: theme.colors.textSecondary }}>→</span>
        <span style={{
          fontSize: 14, fontWeight: 700, color: toColor,
        }}>
          {toTool?.name || detail.to}
        </span>
        <span style={{
          fontSize: 9, padding: '2px 6px', borderRadius: 3,
          background: `${tierColor}18`, color: tierColor,
          border: `1px solid ${tierColor}33`, marginLeft: 'auto',
        }}>
          {detail.tier}
        </span>
      </div>

      {/* Type */}
      <div style={{ marginBottom: 12 }}>
        <span style={{ fontSize: 10, color: theme.colors.textSecondary }}>Type: </span>
        <span style={{ fontSize: 11, color: theme.colors.text }}>
          {detail.type === 'sequential' ? 'Sequential (output → input)' : 'Concurrent (parallel execution)'}
        </span>
      </div>

      {/* Description */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: theme.colors.text, marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
          Description
        </div>
        <div style={{ fontSize: 12, color: theme.colors.text, lineHeight: 1.6 }}>
          {detail.description}
        </div>
      </div>

      {/* Parameter Map */}
      {detail.paramMap && Object.keys(detail.paramMap).length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: theme.colors.text, marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Parameter Mapping
          </div>
          <div style={{
            padding: 10, background: theme.colors.bg, borderRadius: 6,
            border: `1px solid ${theme.colors.border}`, fontFamily: theme.fonts.mono, fontSize: 11,
          }}>
            {Object.entries(detail.paramMap).map(([k, v]) => (
              <div key={k} style={{ color: theme.colors.text, marginBottom: 2 }}>
                <span style={{ color: theme.colors.accent }}>{k}</span>
                <span style={{ color: theme.colors.textSecondary }}>{' ← '}</span>
                <span style={{ color: theme.colors.success }}>{v}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Worked Example */}
      {detail.workedExample && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: theme.colors.text, marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Worked Example
          </div>
          <div style={{
            padding: 12, background: `${theme.colors.accent}08`, borderRadius: 6,
            border: `1px solid ${theme.colors.accent}22`,
            fontSize: 12, color: theme.colors.text, lineHeight: 1.7,
          }}>
            {detail.workedExample}
          </div>
        </div>
      )}

      {/* Related couplings in same category */}
      {(() => {
        const parentCat = couplingDocs.categories.find(cat =>
          cat.examples.includes(couplingKey)
        );
        if (!parentCat) return null;
        const related = parentCat.examples.filter(k => k !== couplingKey);
        if (related.length === 0) return null;
        return (
          <div>
            <div style={{ fontSize: 12, fontWeight: 600, color: theme.colors.text, marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Related Couplings
            </div>
            <div style={{ fontSize: 11, color: theme.colors.textSecondary, marginBottom: 4 }}>
              In category: {parentCat.label}
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
              {related.map(k => (
                <span key={k} style={{
                  padding: '3px 8px', fontSize: 10,
                  background: theme.colors.bgTertiary, borderRadius: 3,
                  border: `1px solid ${theme.colors.border}`,
                  color: theme.colors.textSecondary, fontFamily: theme.fonts.mono,
                }}>
                  {k.replace(/_to_/g, ' → ')}
                </span>
              ))}
            </div>
          </div>
        );
      })()}
    </div>
  );
}
