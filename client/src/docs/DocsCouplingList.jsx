import React, { useState } from 'react';
import { couplingDocs } from './couplingDocs';
import theme from '../theme.json';

export default function DocsCouplingList({ searchQuery, onSelectCoupling }) {
  const [expandedCat, setExpandedCat] = useState(null);
  const q = searchQuery?.toLowerCase() || '';

  const filtered = q
    ? couplingDocs.categories.filter(cat =>
        cat.label.toLowerCase().includes(q) ||
        cat.description.toLowerCase().includes(q) ||
        cat.tools.some(t => t.includes(q)) ||
        (cat.target && cat.target.includes(q))
      )
    : couplingDocs.categories;

  if (filtered.length === 0) {
    return (
      <div style={{ padding: 16, color: theme.colors.textSecondary, fontSize: 12 }}>
        No couplings match "{searchQuery}"
      </div>
    );
  }

  return (
    <div>
      <div style={{ fontSize: 11, color: theme.colors.textSecondary, marginBottom: 12 }}>
        {couplingDocs.categories.length} coupling categories covering 100+ individual connections
      </div>

      {filtered.map(cat => {
        const isExpanded = expandedCat === cat.id || q;
        return (
          <div key={cat.id} style={{ marginBottom: 8 }}>
            <button
              onClick={() => setExpandedCat(expandedCat === cat.id ? null : cat.id)}
              style={{
                display: 'block',
                width: '100%',
                padding: '10px 12px',
                background: theme.colors.bgTertiary,
                border: `1px solid ${theme.colors.border}`,
                borderRadius: 6,
                cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: theme.colors.text }}>
                  {cat.label}
                </span>
                <span style={{ fontSize: 10, color: theme.colors.textSecondary }}>
                  {cat.examples.length} coupling{cat.examples.length !== 1 ? 's' : ''}
                  {cat.deferred && ' (deferred)'}
                </span>
              </div>
              <div style={{
                fontSize: 11, color: theme.colors.textSecondary,
                marginTop: 4, lineHeight: 1.4,
              }}>
                {cat.description}
              </div>
            </button>

            {isExpanded && (
              <div style={{
                padding: '8px 12px',
                background: theme.colors.bg,
                borderLeft: `2px solid ${theme.colors.accent}`,
                marginLeft: 8,
                marginTop: 4,
                borderRadius: '0 4px 4px 0',
              }}>
                <div style={{ fontSize: 11, color: theme.colors.textSecondary, marginBottom: 6 }}>
                  <strong style={{ color: theme.colors.text }}>Data flow:</strong> {cat.dataFlow}
                </div>
                <div style={{ fontSize: 11, color: theme.colors.textSecondary, marginBottom: 6 }}>
                  <strong style={{ color: theme.colors.text }}>Source tools:</strong>{' '}
                  {cat.tools.join(', ')}
                  {cat.target && <> → <strong>{cat.target}</strong></>}
                </div>
                <div style={{ fontSize: 10, color: theme.colors.textSecondary, marginBottom: 4 }}>
                  Individual couplings:
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                  {cat.examples.map(ex => {
                    const hasDetail = !!couplingDocs.details[ex];
                    return (
                      <button
                        key={ex}
                        onClick={(e) => {
                          e.stopPropagation();
                          if (hasDetail) onSelectCoupling(ex);
                        }}
                        style={{
                          padding: '3px 8px',
                          fontSize: 10,
                          background: hasDetail ? `${theme.colors.accent}18` : theme.colors.bgTertiary,
                          border: `1px solid ${hasDetail ? theme.colors.accent + '33' : theme.colors.border}`,
                          borderRadius: 3,
                          color: hasDetail ? theme.colors.accent : theme.colors.textSecondary,
                          cursor: hasDetail ? 'pointer' : 'default',
                          fontFamily: theme.fonts.mono,
                        }}
                      >
                        {ex.replace(/_to_/g, ' → ').replace(/_/g, ' ')}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
