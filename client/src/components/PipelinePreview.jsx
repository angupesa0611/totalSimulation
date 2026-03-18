import React, { useState, useEffect, useCallback, useRef } from 'react';
import { pipelineDocs } from '../docs/pipelineDocs';
import { getWorkerStatus, startWorker } from '../api/client';
import theme from '../theme.json';

const teal = '#14b8a6';

function SpinnerDot({ size = 7 }) {
  return (
    <span style={{
      width: size,
      height: size,
      borderRadius: '50%',
      border: '2px solid rgba(255,255,255,0.15)',
      borderTopColor: teal,
      animation: 'pipelinepreview-spin 0.8s linear infinite',
      flexShrink: 0,
      display: 'inline-block',
    }} />
  );
}

function StatusDot({ color, size = 7 }) {
  if (color === 'spinner') return <SpinnerDot size={size} />;
  return (
    <span style={{
      width: size,
      height: size,
      borderRadius: '50%',
      background: color,
      boxShadow: color === theme.colors.success ? `0 0 6px ${theme.colors.success}60` : 'none',
      flexShrink: 0,
    }} />
  );
}

function Divider() {
  return <div style={{ height: 1, background: 'rgba(255,255,255,0.06)', margin: '16px 0' }} />;
}

function SectionLabel({ children }) {
  return (
    <div style={{
      fontSize: 10,
      fontWeight: 600,
      color: 'rgba(255,255,255,0.35)',
      textTransform: 'uppercase',
      letterSpacing: '0.08em',
      marginBottom: 8,
    }}>
      {children}
    </div>
  );
}

// Per-tool status dot color
function toolStatusColor(s) {
  switch (s) {
    case 'ready': return theme.colors.success;
    case 'stopped': return 'rgba(255,255,255,0.25)';
    case 'not_found': return theme.colors.warning;
    case 'checking': return 'spinner';
    case 'starting': return 'spinner';
    case 'building': return 'spinner';
    case 'error': return theme.colors.error;
    default: return 'rgba(255,255,255,0.25)';
  }
}

// Derive aggregate status from per-tool statuses
function deriveAggregate(toolStatuses) {
  const vals = Object.values(toolStatuses);
  if (vals.length === 0) return 'checking';
  if (vals.some(s => s === 'checking')) return 'checking';
  if (vals.some(s => s === 'building')) return 'building';
  if (vals.some(s => s === 'starting')) return 'starting';
  if (vals.some(s => s === 'error')) return 'error';
  if (vals.some(s => s === 'not_found')) return 'needs_build';
  if (vals.every(s => s === 'ready')) return 'all_ready';
  if (vals.some(s => s === 'stopped')) return 'some_stopped';
  return 'all_ready';
}

export default function PipelinePreview({ pipeline, onGo, onClose, isMobile }) {
  const pipelineKey = pipeline?.key;
  const doc = pipelineDocs[pipelineKey] || null;
  const steps = doc?.steps || [];

  // unique tool keys in this pipeline
  const toolKeys = [...new Set(steps.map(s => s.tool))];

  const [toolStatuses, setToolStatuses] = useState(() => {
    const init = {};
    toolKeys.forEach(k => { init[k] = 'checking'; });
    return init;
  });
  const [buildProgress, setBuildProgress] = useState({ current: 0, total: 0 });
  const [errorMsg, setErrorMsg] = useState(null);
  const cancelledRef = useRef(false);

  // Check worker statuses on mount
  useEffect(() => {
    cancelledRef.current = false;
    const init = {};
    toolKeys.forEach(k => { init[k] = 'checking'; });
    setToolStatuses(init);
    setErrorMsg(null);

    getWorkerStatus()
      .then(workers => {
        if (cancelledRef.current) return;
        const updated = {};
        toolKeys.forEach(toolKey => {
          const match = workers.find(w => w.tool_key === toolKey);
          if (!match) {
            updated[toolKey] = 'ready'; // embedded
          } else if (match.status === 'running') {
            updated[toolKey] = 'ready';
          } else if (match.status === 'not_found') {
            updated[toolKey] = 'not_found';
          } else {
            updated[toolKey] = 'stopped';
          }
        });
        setToolStatuses(updated);
      })
      .catch(() => {
        if (!cancelledRef.current) {
          const err = {};
          toolKeys.forEach(k => { err[k] = 'error'; });
          setToolStatuses(err);
        }
      });

    return () => { cancelledRef.current = true; };
  }, [pipelineKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const aggregate = deriveAggregate(toolStatuses);

  // Build All: sequentially build containers that are not_found
  const handleBuildAll = useCallback(async () => {
    const toBuild = toolKeys.filter(k => toolStatuses[k] === 'not_found');
    if (toBuild.length === 0) return;
    setErrorMsg(null);
    setBuildProgress({ current: 0, total: toBuild.length });

    for (let i = 0; i < toBuild.length; i++) {
      if (cancelledRef.current) return;
      const k = toBuild[i];
      setToolStatuses(prev => ({ ...prev, [k]: 'building' }));
      setBuildProgress({ current: i + 1, total: toBuild.length });
      try {
        const result = await startWorker(k);
        if (cancelledRef.current) return;
        if (result.status === 'running' || result.status === 'embedded') {
          setToolStatuses(prev => ({ ...prev, [k]: 'ready' }));
        } else {
          setToolStatuses(prev => ({ ...prev, [k]: 'stopped' }));
        }
      } catch (err) {
        if (cancelledRef.current) return;
        setErrorMsg(`Failed to build ${k}: ${err.response?.data?.detail || err.message}`);
        setToolStatuses(prev => ({ ...prev, [k]: 'error' }));
        return; // stop on first error
      }
    }
    setBuildProgress({ current: 0, total: 0 });
  }, [toolKeys, toolStatuses]); // eslint-disable-line react-hooks/exhaustive-deps

  // Go: auto-start stopped containers, then navigate
  const handleGo = useCallback(async () => {
    const stopped = toolKeys.filter(k => toolStatuses[k] === 'stopped');
    if (stopped.length === 0) {
      onGo();
      return;
    }
    // Start stopped containers
    for (const k of stopped) {
      if (cancelledRef.current) return;
      setToolStatuses(prev => ({ ...prev, [k]: 'starting' }));
      try {
        const result = await startWorker(k);
        if (cancelledRef.current) return;
        if (result.status === 'running' || result.status === 'embedded') {
          setToolStatuses(prev => ({ ...prev, [k]: 'ready' }));
        } else {
          setToolStatuses(prev => ({ ...prev, [k]: 'error' }));
          setErrorMsg(`Failed to start ${k}`);
          return;
        }
      } catch (err) {
        if (cancelledRef.current) return;
        setErrorMsg(`Failed to start ${k}: ${err.response?.data?.detail || err.message}`);
        setToolStatuses(prev => ({ ...prev, [k]: 'error' }));
        return;
      }
    }
    onGo();
  }, [toolKeys, toolStatuses, onGo]); // eslint-disable-line react-hooks/exhaustive-deps

  // Close on Escape (blocked during busy states)
  const busy = aggregate === 'building' || aggregate === 'starting';
  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape' && !busy) onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose, busy]);

  // Status bar
  let statusLabel, statusColor;
  switch (aggregate) {
    case 'checking':
      statusLabel = 'Checking containers...'; statusColor = 'rgba(255,255,255,0.3)';
      break;
    case 'all_ready':
      statusLabel = 'All tools ready'; statusColor = 'rgba(255,255,255,0.4)';
      break;
    case 'some_stopped':
      statusLabel = 'Some containers stopped \u2014 will auto-start'; statusColor = 'rgba(255,255,255,0.4)';
      break;
    case 'needs_build':
      statusLabel = `${toolKeys.filter(k => toolStatuses[k] === 'not_found').length} container(s) need building`;
      statusColor = theme.colors.warning;
      break;
    case 'building':
      statusLabel = buildProgress.total > 0
        ? `Building container ${buildProgress.current}/${buildProgress.total}...`
        : 'Building...';
      statusColor = teal;
      break;
    case 'starting':
      statusLabel = 'Starting containers...'; statusColor = teal;
      break;
    case 'error':
      statusLabel = errorMsg || 'Something went wrong'; statusColor = theme.colors.error;
      break;
    default:
      statusLabel = ''; statusColor = 'rgba(255,255,255,0.3)';
  }

  // Button
  let buttonLabel, buttonDisabled, buttonOnClick;
  switch (aggregate) {
    case 'checking':
      buttonLabel = '\u2026'; buttonDisabled = true; buttonOnClick = null;
      break;
    case 'all_ready':
    case 'some_stopped':
      buttonLabel = 'Go'; buttonDisabled = false; buttonOnClick = handleGo;
      break;
    case 'needs_build':
      buttonLabel = 'Build All'; buttonDisabled = false; buttonOnClick = handleBuildAll;
      break;
    case 'building':
      buttonLabel = 'Building\u2026'; buttonDisabled = true; buttonOnClick = null;
      break;
    case 'starting':
      buttonLabel = 'Starting\u2026'; buttonDisabled = true; buttonOnClick = null;
      break;
    case 'error':
      buttonLabel = 'Unavailable'; buttonDisabled = true; buttonOnClick = null;
      break;
    default:
      buttonLabel = 'Go'; buttonDisabled = true; buttonOnClick = null;
  }

  return (
    <>
      <style>{`@keyframes pipelinepreview-spin { to { transform: rotate(360deg); } }`}</style>
      <div
        onClick={() => { if (!busy) onClose(); }}
        style={{
          position: 'fixed',
          inset: 0,
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'rgba(0,0,0,0.6)',
          backdropFilter: 'blur(4px)',
          WebkitBackdropFilter: 'blur(4px)',
          padding: isMobile ? 8 : 24,
        }}
      >
        <div
          onClick={e => e.stopPropagation()}
          style={{
            width: '100%',
            maxWidth: 680,
            maxHeight: '85vh',
            borderRadius: 16,
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.08)',
            boxShadow: '0 24px 80px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.04)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {/* Scrollable content */}
          <div style={{
            flex: 1,
            overflowY: 'auto',
            padding: isMobile ? '20px 16px 16px' : '28px 28px 20px',
          }}>
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, marginBottom: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                <h2 style={{
                  margin: 0,
                  fontSize: 22,
                  fontWeight: 700,
                  color: theme.colors.text,
                  letterSpacing: '-0.01em',
                }}>
                  {doc?.label || pipeline?.label || pipelineKey}
                </h2>
                <span style={{
                  fontSize: 10,
                  fontWeight: 600,
                  color: teal,
                  background: `${teal}18`,
                  padding: '3px 10px',
                  borderRadius: 9999,
                  border: `1px solid ${teal}30`,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}>
                  {steps.length} steps
                </span>
              </div>
              <button
                onClick={onClose}
                disabled={busy}
                style={{
                  background: 'rgba(255,255,255,0.06)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  borderRadius: 8,
                  color: 'rgba(255,255,255,0.5)',
                  cursor: busy ? 'not-allowed' : 'pointer',
                  fontSize: 16,
                  width: 32,
                  height: 32,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  transition: 'all 0.15s ease-out',
                  opacity: busy ? 0.4 : 1,
                }}
                onMouseEnter={e => { if (!busy) { e.currentTarget.style.background = 'rgba(255,255,255,0.1)'; e.currentTarget.style.color = 'rgba(255,255,255,0.8)'; } }}
                onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.06)'; e.currentTarget.style.color = 'rgba(255,255,255,0.5)'; }}
              >
                {'\u2715'}
              </button>
            </div>

            {/* Summary */}
            {doc?.summary && (
              <p style={{
                margin: '0 0 4px',
                fontSize: 14,
                fontWeight: 500,
                color: teal,
                lineHeight: 1.5,
              }}>
                {doc.summary}
              </p>
            )}

            {/* Scientific Context */}
            {doc?.scientificContext && (
              <>
                <Divider />
                <div style={{
                  background: `${teal}08`,
                  border: `1px solid ${teal}15`,
                  borderRadius: 10,
                  padding: '12px 14px',
                }}>
                  <SectionLabel>Scientific Context</SectionLabel>
                  <p style={{
                    margin: 0,
                    fontSize: 12,
                    color: 'rgba(255,255,255,0.55)',
                    lineHeight: 1.7,
                  }}>
                    {doc.scientificContext}
                  </p>
                </div>
              </>
            )}

            {/* Expected Runtime */}
            {doc?.expectedRuntime && (
              <div style={{
                marginTop: 12,
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}>
                <span style={{
                  fontSize: 10,
                  fontWeight: 600,
                  color: 'rgba(255,255,255,0.35)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                }}>
                  Expected Runtime
                </span>
                <span style={{
                  fontSize: 12,
                  color: 'rgba(255,255,255,0.6)',
                  fontFamily: theme.fonts.mono,
                }}>
                  {doc.expectedRuntime}
                </span>
              </div>
            )}

            {/* Steps */}
            <Divider />
            <SectionLabel>Pipeline Steps</SectionLabel>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {steps.map((step, i) => {
                const st = toolStatuses[step.tool] || 'checking';
                return (
                  <div key={i} style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 10,
                    padding: '10px 12px',
                    background: 'rgba(255,255,255,0.02)',
                    borderRadius: 10,
                    border: '1px solid rgba(255,255,255,0.04)',
                  }}>
                    {/* Step number */}
                    <span style={{
                      fontSize: 10,
                      fontWeight: 700,
                      color: teal,
                      background: `${teal}15`,
                      width: 22,
                      height: 22,
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                      marginTop: 1,
                    }}>
                      {i + 1}
                    </span>

                    {/* Content */}
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
                        <span style={{
                          fontSize: 12,
                          fontWeight: 600,
                          color: theme.colors.text,
                        }}>
                          {step.tool}
                        </span>
                        <span style={{
                          fontSize: 10,
                          color: 'rgba(255,255,255,0.3)',
                          fontFamily: theme.fonts.mono,
                        }}>
                          {step.duration}
                        </span>
                      </div>
                      <div style={{
                        fontSize: 11,
                        color: 'rgba(255,255,255,0.45)',
                        lineHeight: 1.5,
                      }}>
                        {step.role}
                      </div>
                    </div>

                    {/* Status dot */}
                    <div style={{ marginTop: 4, flexShrink: 0 }}>
                      <StatusDot color={toolStatusColor(st)} />
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Recommended params note */}
            {doc?.recommendedParams && Object.keys(doc.recommendedParams).length > 0 && (
              <>
                <Divider />
                <div style={{
                  padding: '10px 14px',
                  background: `${teal}06`,
                  border: `1px solid ${teal}12`,
                  borderRadius: 10,
                  fontSize: 12,
                  color: 'rgba(255,255,255,0.5)',
                  lineHeight: 1.6,
                }}>
                  Recommended parameters will be pre-filled for {Object.keys(doc.recommendedParams).length} tool(s). You can adjust them in the simulation panel.
                </div>
              </>
            )}
          </div>

          {/* Sticky bottom bar */}
          <div style={{
            padding: isMobile ? '12px 16px' : '14px 28px',
            borderTop: '1px solid rgba(255,255,255,0.06)',
            background: 'rgba(10,10,15,0.8)',
            backdropFilter: 'blur(12px)',
            WebkitBackdropFilter: 'blur(12px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 12,
          }}>
            {/* Status indicator */}
            <div style={{ fontSize: 11, color: statusColor, display: 'flex', alignItems: 'center', gap: 6, minWidth: 0 }}>
              <StatusDot color={
                aggregate === 'checking' || aggregate === 'building' || aggregate === 'starting'
                  ? 'spinner'
                  : aggregate === 'all_ready' ? theme.colors.success
                  : aggregate === 'needs_build' ? theme.colors.warning
                  : aggregate === 'error' ? theme.colors.error
                  : 'rgba(255,255,255,0.25)'
              } />
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {statusLabel}
              </span>
            </div>

            {/* Action button */}
            <button
              onClick={buttonOnClick}
              disabled={buttonDisabled}
              style={{
                padding: '9px 28px',
                background: buttonDisabled
                  ? 'rgba(255,255,255,0.08)'
                  : aggregate === 'needs_build' ? theme.colors.warning : teal,
                border: 'none',
                borderRadius: 10,
                color: buttonDisabled ? 'rgba(255,255,255,0.3)' : '#fff',
                fontSize: 13,
                fontWeight: 600,
                cursor: buttonDisabled ? 'not-allowed' : 'pointer',
                transition: 'all 0.15s ease-out',
                boxShadow: buttonDisabled ? 'none'
                  : `0 4px 14px ${aggregate === 'needs_build' ? theme.colors.warning : teal}40`,
                flexShrink: 0,
                letterSpacing: '0.01em',
              }}
              onMouseEnter={e => {
                if (!buttonDisabled) {
                  const c = aggregate === 'needs_build' ? theme.colors.warning : teal;
                  e.currentTarget.style.transform = 'translateY(-1px)';
                  e.currentTarget.style.boxShadow = `0 6px 20px ${c}50`;
                }
              }}
              onMouseLeave={e => {
                if (!buttonDisabled) {
                  const c = aggregate === 'needs_build' ? theme.colors.warning : teal;
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = `0 4px 14px ${c}40`;
                } else {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = 'none';
                }
              }}
            >
              {buttonLabel}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
