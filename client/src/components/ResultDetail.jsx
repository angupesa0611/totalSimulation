import React, { useState, useEffect } from 'react';
import { getResult, getResultFiles, getResultMetadata, deleteResult } from '../api/client';
import ExportButton from './ExportButton';
import VisualizerArea from '../visualizers/VisualizerArea';
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

function formatBytes(bytes) {
  if (bytes == null) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

const STATUS_COLORS = {
  SUCCESS: theme.colors.success,
  FAILURE: theme.colors.error,
  CANCELLED: theme.colors.warning,
  INTERRUPTED: theme.colors.warning,
};

export default function ResultDetail({ result, project, toolInfo, onRerun }) {
  const [metadata, setMetadata] = useState(null);
  const [files, setFiles] = useState([]);
  const [resultData, setResultData] = useState(null);
  const [viewingResult, setViewingResult] = useState(false);
  const [paramsExpanded, setParamsExpanded] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(false);

  useEffect(() => {
    if (!result?.job_id) return;
    setViewingResult(false);
    setResultData(null);

    getResultMetadata(result.job_id, project)
      .then(setMetadata)
      .catch(() => setMetadata(result));

    getResultFiles(result.job_id, project)
      .then(setFiles)
      .catch(() => setFiles([]));
  }, [result?.job_id, project]);

  const handleViewResult = async () => {
    if (!resultData) {
      const data = await getResult(result.job_id, project);
      setResultData(data);
    }
    setViewingResult(true);
  };

  const handleDelete = async () => {
    if (!deleteConfirm) {
      setDeleteConfirm(true);
      setTimeout(() => setDeleteConfirm(false), 3000);
      return;
    }
    await deleteResult(result.job_id, project);
    setDeleteConfirm(false);
  };

  const meta = metadata || result;
  const info = toolInfo?.[result.tool];
  const statusColor = STATUS_COLORS[meta.status] || theme.colors.textSecondary;

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Metadata header */}
      <div style={{
        padding: '12px 16px',
        borderBottom: `1px solid ${theme.colors.border}`,
        background: theme.colors.bgSecondary,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
          <span style={{ fontSize: 16, fontWeight: 700, color: theme.colors.text }}>
            {info?.name || result.tool?.toUpperCase()}
          </span>
          {meta.label && (
            <span style={{ fontSize: 13, color: theme.colors.textSecondary }}>
              — {meta.label}
            </span>
          )}
        </div>

        <div style={{ display: 'flex', gap: 16, fontSize: 11, color: theme.colors.textSecondary, flexWrap: 'wrap' }}>
          <span style={{ fontFamily: theme.fonts.mono }}>
            Job: {meta.job_id?.slice(0, 8)}
          </span>
          <span>{timeAgo(meta.timestamp)}</span>
          <span style={{ color: statusColor, fontWeight: 600 }}>
            {meta.status || 'SUCCESS'}
          </span>
          {meta.duration_s != null && (
            <span>Duration: {meta.duration_s.toFixed(1)}s</span>
          )}
          {meta.result_size_bytes != null && (
            <span>Size: {formatBytes(meta.result_size_bytes)}</span>
          )}
        </div>

        {meta.error && (
          <div style={{
            marginTop: 8, padding: '6px 10px', background: '#1a0a0a',
            borderRadius: 4, border: `1px solid ${theme.colors.error}`,
            fontSize: 11, color: theme.colors.error,
          }}>
            {meta.error}
          </div>
        )}

        {/* Action buttons */}
        <div style={{ display: 'flex', gap: 6, marginTop: 10 }}>
          <button
            onClick={handleViewResult}
            style={{
              padding: '5px 12px', background: theme.colors.accent,
              border: 'none', borderRadius: 4, color: '#fff',
              fontSize: 11, cursor: 'pointer',
            }}
          >
            {viewingResult ? 'Viewing' : 'View Result'}
          </button>

          {onRerun && (
            <button
              onClick={() => onRerun(result)}
              style={{
                padding: '5px 12px', background: theme.colors.bgTertiary,
                border: `1px solid ${theme.colors.border}`, borderRadius: 4,
                color: theme.colors.text, fontSize: 11, cursor: 'pointer',
              }}
            >
              Re-run
            </button>
          )}

          <ExportButton
            jobIds={[result.job_id]}
            title={`${info?.name || result.tool} Result`}
          />

          <button
            onClick={handleDelete}
            style={{
              padding: '5px 12px', background: 'transparent',
              border: `1px solid ${deleteConfirm ? theme.colors.error : theme.colors.border}`,
              borderRadius: 4,
              color: deleteConfirm ? theme.colors.error : theme.colors.textSecondary,
              fontSize: 11, cursor: 'pointer',
            }}
          >
            {deleteConfirm ? 'Confirm Delete' : 'Delete'}
          </button>
        </div>
      </div>

      {/* Visualizer / result view */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {viewingResult && resultData ? (
          <VisualizerArea
            tool={info || { key: result.tool, name: result.tool }}
            result={resultData}
            jobId={result.job_id}
          />
        ) : (
          <div style={{ padding: 16 }}>
            {/* Files section */}
            <div style={{ marginBottom: 16 }}>
              <h4 style={{
                fontSize: 12, fontWeight: 600, color: theme.colors.text,
                marginBottom: 8, margin: 0,
              }}>
                Files
              </h4>
              {files.length === 0 ? (
                <div style={{ fontSize: 11, color: theme.colors.textSecondary }}>No files</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {files.map(f => (
                    <a
                      key={f.name}
                      href={`/api/results/${result.job_id}/files/${f.name}?project=${project}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                        padding: '4px 8px', borderRadius: 3,
                        background: theme.colors.bgTertiary,
                        color: theme.colors.accent, fontSize: 11,
                        textDecoration: 'none',
                      }}
                    >
                      <span>{f.name}</span>
                      <span style={{ color: theme.colors.textSecondary, fontSize: 10 }}>
                        {formatBytes(f.size_bytes)}
                      </span>
                    </a>
                  ))}
                </div>
              )}
            </div>

            {/* Parameters section */}
            {meta.params_summary && (
              <div>
                <h4
                  style={{
                    fontSize: 12, fontWeight: 600, color: theme.colors.text,
                    marginBottom: 8, margin: 0, cursor: 'pointer',
                  }}
                  onClick={() => setParamsExpanded(!paramsExpanded)}
                >
                  Parameters {paramsExpanded ? '\u25B2' : '\u25BC'}
                </h4>
                {paramsExpanded && (
                  <pre style={{
                    padding: 10, background: theme.colors.bg,
                    borderRadius: 4, border: `1px solid ${theme.colors.border}`,
                    fontSize: 11, color: theme.colors.text,
                    overflow: 'auto', maxHeight: 300,
                    fontFamily: theme.fonts.mono,
                    whiteSpace: 'pre-wrap', wordBreak: 'break-all',
                  }}>
                    {meta.params_summary}
                  </pre>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
