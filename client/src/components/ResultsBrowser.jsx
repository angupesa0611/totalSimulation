import React, { useState } from 'react';
import { useResults } from '../hooks/useResults';
import theme from '../theme.json';

function timeAgo(timestamp) {
  if (!timestamp) return '';
  const diff = Date.now() - new Date(timestamp).getTime();
  const seconds = Math.floor(diff / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

const STATUS_ICONS = {
  SUCCESS: { symbol: '\u2713', color: theme.colors.success },
  FAILURE: { symbol: '\u2717', color: theme.colors.error },
  CANCELLED: { symbol: '\u25CB', color: theme.colors.warning },
  INTERRUPTED: { symbol: '\u26A0', color: theme.colors.warning },
  RUNNING: { symbol: '\u25CF', color: theme.colors.accent },
  PENDING: { symbol: '\u25CB', color: theme.colors.textSecondary },
};

function StatusIcon({ status }) {
  const info = STATUS_ICONS[status] || STATUS_ICONS.SUCCESS;
  return (
    <span style={{ color: info.color, fontSize: 14, fontWeight: 700, width: 18, textAlign: 'center' }}>
      {info.symbol}
    </span>
  );
}

export default function ResultsBrowser({ project, onSelectResult, selectedResult, style }) {
  const { results, total, loading, filters, setFilters, page, setPage, pageCount, deleteResult, refresh } = useResults(project);
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  const handleDelete = async (jobId, e) => {
    e.stopPropagation();
    if (deleteConfirm === jobId) {
      await deleteResult(jobId);
      setDeleteConfirm(null);
    } else {
      setDeleteConfirm(jobId);
      setTimeout(() => setDeleteConfirm(null), 3000);
    }
  };

  return (
    <div style={{
      width: 320,
      background: theme.colors.bgSecondary,
      borderRight: `1px solid ${theme.colors.border}`,
      flexShrink: 0,
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      ...style,
    }}>
      {/* Header */}
      <div style={{
        padding: '12px 16px 8px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, margin: 0, color: theme.colors.text }}>
          Results
        </h3>
        <button
          onClick={refresh}
          style={{
            background: 'none', border: 'none', color: theme.colors.textSecondary,
            cursor: 'pointer', fontSize: 14, padding: '2px 6px',
          }}
          title="Refresh"
        >
          {'\u21BB'}
        </button>
      </div>

      {/* Search */}
      <div style={{ padding: '0 12px 8px' }}>
        <input
          type="text"
          value={filters.q}
          onChange={e => setFilters(f => ({ ...f, q: e.target.value }))}
          placeholder="Search results..."
          style={{
            width: '100%',
            padding: '6px 10px',
            background: theme.colors.bg,
            border: `1px solid ${theme.colors.border}`,
            borderRadius: 4,
            color: theme.colors.text,
            fontSize: 12,
            outline: 'none',
            boxSizing: 'border-box',
          }}
        />
      </div>

      {/* Filters row */}
      <div style={{ padding: '0 12px 8px', display: 'flex', gap: 6 }}>
        <select
          value={filters.tool || ''}
          onChange={e => setFilters(f => ({ ...f, tool: e.target.value || null }))}
          style={{
            flex: 1, padding: '4px 6px', background: theme.colors.bg,
            border: `1px solid ${theme.colors.border}`, borderRadius: 3,
            color: theme.colors.text, fontSize: 10,
          }}
        >
          <option value="">All Tools</option>
          {[...new Set(results.map(r => r.tool))].sort().map(t => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>

        <select
          value={filters.status || ''}
          onChange={e => setFilters(f => ({ ...f, status: e.target.value || null }))}
          style={{
            flex: 1, padding: '4px 6px', background: theme.colors.bg,
            border: `1px solid ${theme.colors.border}`, borderRadius: 3,
            color: theme.colors.text, fontSize: 10,
          }}
        >
          <option value="">All Status</option>
          <option value="SUCCESS">Success</option>
          <option value="FAILURE">Failure</option>
          <option value="CANCELLED">Cancelled</option>
          <option value="INTERRUPTED">Interrupted</option>
        </select>

        <select
          value={filters.sort}
          onChange={e => setFilters(f => ({ ...f, sort: e.target.value }))}
          style={{
            flex: 1, padding: '4px 6px', background: theme.colors.bg,
            border: `1px solid ${theme.colors.border}`, borderRadius: 3,
            color: theme.colors.text, fontSize: 10,
          }}
        >
          <option value="newest">Newest</option>
          <option value="oldest">Oldest</option>
          <option value="tool">By Tool</option>
        </select>
      </div>

      {/* Divider */}
      <div style={{ height: 1, background: theme.colors.border }} />

      {/* Results list */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {loading && results.length === 0 ? (
          <div style={{ padding: 24, textAlign: 'center', color: theme.colors.textSecondary, fontSize: 12 }}>
            Loading...
          </div>
        ) : results.length === 0 ? (
          <div style={{ padding: 24, textAlign: 'center', color: theme.colors.textSecondary, fontSize: 12 }}>
            No results found
          </div>
        ) : (
          results.map(r => (
            <div
              key={r.job_id}
              onClick={() => onSelectResult(r)}
              style={{
                padding: '10px 12px',
                borderBottom: `1px solid ${theme.colors.border}`,
                cursor: 'pointer',
                background: selectedResult?.job_id === r.job_id
                  ? theme.colors.accent + '18'
                  : 'transparent',
                display: 'flex',
                alignItems: 'flex-start',
                gap: 8,
                transition: 'background 0.1s',
              }}
              onMouseEnter={e => {
                if (selectedResult?.job_id !== r.job_id)
                  e.currentTarget.style.background = theme.colors.bgTertiary;
              }}
              onMouseLeave={e => {
                if (selectedResult?.job_id !== r.job_id)
                  e.currentTarget.style.background = 'transparent';
              }}
            >
              <StatusIcon status={r.status || 'SUCCESS'} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8,
                }}>
                  <span style={{
                    fontSize: 12, fontWeight: 600, color: theme.colors.text,
                    textTransform: 'uppercase',
                  }}>
                    {r.tool}
                  </span>
                  <span style={{ fontSize: 10, color: theme.colors.textSecondary, flexShrink: 0 }}>
                    {timeAgo(r.timestamp)}
                  </span>
                </div>
                <div style={{
                  fontSize: 11, color: theme.colors.textSecondary, marginTop: 2,
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                }}>
                  {r.label || r.job_id?.slice(0, 12)}
                </div>
                {r.duration_s != null && (
                  <span style={{ fontSize: 10, color: theme.colors.textSecondary }}>
                    {r.duration_s.toFixed(1)}s
                  </span>
                )}
              </div>

              {/* Delete button */}
              <button
                onClick={(e) => handleDelete(r.job_id, e)}
                style={{
                  background: 'none', border: 'none',
                  color: deleteConfirm === r.job_id ? theme.colors.error : theme.colors.textSecondary,
                  cursor: 'pointer', fontSize: 11, padding: '2px 4px',
                  flexShrink: 0, opacity: 0.6,
                }}
                title={deleteConfirm === r.job_id ? 'Click again to confirm' : 'Delete result'}
              >
                {deleteConfirm === r.job_id ? 'Confirm?' : '\u2715'}
              </button>
            </div>
          ))
        )}
      </div>

      {/* Pagination */}
      {total > 0 && (
        <div style={{
          padding: '8px 12px',
          borderTop: `1px solid ${theme.colors.border}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: 11,
          color: theme.colors.textSecondary,
        }}>
          <span>
            {page * 20 + 1}-{Math.min((page + 1) * 20, total)} of {total}
          </span>
          <div style={{ display: 'flex', gap: 4 }}>
            <button
              onClick={() => setPage(p => Math.max(0, p - 1))}
              disabled={page === 0}
              style={{
                background: theme.colors.bgTertiary, border: 'none', borderRadius: 3,
                color: page === 0 ? theme.colors.border : theme.colors.text,
                cursor: page === 0 ? 'default' : 'pointer', padding: '2px 8px', fontSize: 11,
              }}
            >
              {'<'}
            </button>
            <button
              onClick={() => setPage(p => Math.min(pageCount - 1, p + 1))}
              disabled={page >= pageCount - 1}
              style={{
                background: theme.colors.bgTertiary, border: 'none', borderRadius: 3,
                color: page >= pageCount - 1 ? theme.colors.border : theme.colors.text,
                cursor: page >= pageCount - 1 ? 'default' : 'pointer', padding: '2px 8px', fontSize: 11,
              }}
            >
              {'>'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
