import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { toolDocs } from '../docs/toolDocs';
import { getWorkerStatus, startWorker } from '../api/client';
import theme from '../theme.json';

const layerColors = theme.colors.layers;

const TYPE_COLORS = {
  select: '#6366f1',
  multiselect: '#6366f1',
  number: '#14b8a6',
  json: '#f59e0b',
  text: '#8888a0',
};

// Status flow:
//   checking → ready | stopped | not_found | error
//   stopped  → (click Go) → starting → ready → auto-navigate
//   not_found → (click Build) → building → ready → user clicks Go → navigate
//   ready → (click Go) → navigate immediately

function TypeBadge({ type }) {
  const color = TYPE_COLORS[type] || TYPE_COLORS.text;
  return (
    <span style={{
      fontSize: 10,
      fontWeight: 600,
      color,
      background: `${color}18`,
      border: `1px solid ${color}30`,
      padding: '1px 8px',
      borderRadius: 9999,
      textTransform: 'uppercase',
      letterSpacing: '0.04em',
      flexShrink: 0,
    }}>
      {type}
    </span>
  );
}

function LayerPill({ layer }) {
  const color = layerColors[layer] || theme.colors.accent;
  return (
    <span style={{
      fontSize: 10,
      fontWeight: 600,
      color,
      background: `${color}15`,
      border: `1px solid ${color}30`,
      padding: '3px 10px',
      borderRadius: 9999,
      textTransform: 'uppercase',
      letterSpacing: '0.05em',
    }}>
      {layer}
    </span>
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

function PresetMiniCard({ preset, onClick, disabled }) {
  const [hovered, setHovered] = useState(false);
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        padding: '10px 14px',
        background: hovered && !disabled ? 'rgba(99,102,241,0.1)' : 'rgba(99,102,241,0.04)',
        border: `1px solid ${hovered && !disabled ? 'rgba(99,102,241,0.3)' : 'rgba(99,102,241,0.12)'}`,
        borderRadius: 10,
        color: theme.colors.text,
        textAlign: 'left',
        cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'all 0.15s ease-out',
        width: '100%',
        opacity: disabled ? 0.5 : 1,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
        <span style={{
          fontSize: 9,
          color: theme.colors.accent,
          background: 'rgba(99,102,241,0.15)',
          padding: '1px 6px',
          borderRadius: 9999,
          fontWeight: 600,
          letterSpacing: '0.04em',
          textTransform: 'uppercase',
        }}>
          Preset
        </span>
        <span style={{ fontSize: 12, fontWeight: 600 }}>{preset.label}</span>
      </div>
      {preset.description && (
        <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', lineHeight: 1.5 }}>
          {preset.description}
        </div>
      )}
    </button>
  );
}

function SpinnerDot() {
  return (
    <span style={{
      width: 7,
      height: 7,
      borderRadius: '50%',
      border: '2px solid rgba(255,255,255,0.15)',
      borderTopColor: theme.colors.accent,
      animation: 'toolpreview-spin 0.8s linear infinite',
      flexShrink: 0,
      display: 'inline-block',
    }} />
  );
}

export default function ToolPreview({ tool, presets, onGo, onGoWithPreset, onClose, isMobile }) {
  const [status, setStatus] = useState('checking');
  const [isEmbedded, setIsEmbedded] = useState(false);
  const [limitsOpen, setLimitsOpen] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  // pendingAction: when starting a stopped container via Go, auto-navigate on ready
  const [pendingAction, setPendingAction] = useState(null);
  const cancelledRef = useRef(false);

  const doc = toolDocs[tool.key] || null;

  const toolPresets = useMemo(() => {
    return presets.filter(p => p.tool === tool.key);
  }, [presets, tool.key]);

  // Check initial worker status
  useEffect(() => {
    cancelledRef.current = false;
    setStatus('checking');
    setIsEmbedded(false);
    setErrorMsg(null);

    getWorkerStatus()
      .then(workers => {
        if (cancelledRef.current) return;
        const match = workers.find(w => w.tool_key === tool.key);
        if (!match) {
          setIsEmbedded(true);
          setStatus('ready');
        } else if (match.status === 'running') {
          setStatus('ready');
        } else if (match.status === 'not_found') {
          setStatus('not_found');
        } else {
          // exited, created, etc. = stopped
          setStatus('stopped');
        }
      })
      .catch(() => {
        if (!cancelledRef.current) setStatus('error');
      });

    return () => { cancelledRef.current = true; };
  }, [tool.key]);

  // Auto-navigate when ready + pending action
  useEffect(() => {
    if (status === 'ready' && pendingAction) {
      const action = pendingAction;
      setPendingAction(null);
      if (action.type === 'go') onGo();
      else onGoWithPreset(action.preset);
    }
  }, [status, pendingAction, onGo, onGoWithPreset]);

  // Go button: for ready and stopped states
  const handleGo = useCallback(async (action) => {
    if (status === 'ready') {
      if (action.type === 'go') onGo();
      else onGoWithPreset(action.preset);
      return;
    }
    if (status === 'stopped') {
      setPendingAction(action);
      setStatus('starting');
      try {
        const result = await startWorker(tool.key);
        if (cancelledRef.current) return;
        if (result.status === 'embedded' || result.status === 'running') {
          setStatus('ready'); // triggers auto-navigate via useEffect
        } else {
          setStatus('error');
          setPendingAction(null);
        }
      } catch (err) {
        if (cancelledRef.current) return;
        setErrorMsg(err.response?.data?.detail || 'Failed to start');
        setStatus('error');
        setPendingAction(null);
      }
    }
  }, [status, tool.key, onGo, onGoWithPreset]);

  // Build button: for not_found state. Builds + creates + starts, then shows Go.
  const handleBuild = useCallback(async () => {
    setStatus('building');
    setErrorMsg(null);
    try {
      const result = await startWorker(tool.key);
      if (cancelledRef.current) return;
      if (result.status === 'running' || result.status === 'embedded') {
        setStatus('ready'); // no pending action — user clicks Go next
      } else {
        setStatus('error');
      }
    } catch (err) {
      if (cancelledRef.current) return;
      setErrorMsg(err.response?.data?.detail || 'Build failed');
      setStatus('not_found');
    }
  }, [tool.key]);

  // Close on Escape (blocked during starting/building)
  useEffect(() => {
    const busy = status === 'starting' || status === 'building';
    const handler = (e) => { if (e.key === 'Escape' && !busy) onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose, status]);

  const busy = status === 'starting' || status === 'building';
  const params = doc?.params ? Object.entries(doc.params) : [];
  const outputs = doc?.outputs ? Object.entries(doc.outputs) : [];
  const layerColor = layerColors[doc?.layer || tool.layer] || theme.colors.accent;

  // Status bar
  let statusDot, statusLabel, statusColor;
  switch (status) {
    case 'checking':
      statusDot = 'spinner'; statusLabel = 'Checking status...'; statusColor = 'rgba(255,255,255,0.3)';
      break;
    case 'ready':
      statusDot = theme.colors.success;
      statusLabel = isEmbedded ? 'Embedded \u2014 always ready' : 'Container running';
      statusColor = 'rgba(255,255,255,0.4)';
      break;
    case 'stopped':
      statusDot = 'rgba(255,255,255,0.25)';
      statusLabel = 'Container stopped \u2014 starts in ~30-60s';
      statusColor = 'rgba(255,255,255,0.4)';
      break;
    case 'not_found':
      statusDot = theme.colors.warning;
      statusLabel = 'Container not built';
      statusColor = theme.colors.warning;
      break;
    case 'starting':
      statusDot = 'spinner'; statusLabel = 'Starting container...'; statusColor = theme.colors.accent;
      break;
    case 'building':
      statusDot = 'spinner'; statusLabel = 'Building container \u2014 this may take a while...'; statusColor = theme.colors.accent;
      break;
    case 'error':
      statusDot = theme.colors.error;
      statusLabel = errorMsg || 'Something went wrong';
      statusColor = theme.colors.error;
      break;
    default:
      statusDot = 'rgba(255,255,255,0.25)'; statusLabel = ''; statusColor = 'rgba(255,255,255,0.3)';
  }

  // Button
  let buttonLabel, buttonDisabled, buttonOnClick;
  switch (status) {
    case 'checking':
      buttonLabel = '\u2026'; buttonDisabled = true; buttonOnClick = null;
      break;
    case 'ready':
    case 'stopped':
      buttonLabel = 'Go'; buttonDisabled = false;
      buttonOnClick = () => handleGo({ type: 'go' });
      break;
    case 'not_found':
      buttonLabel = 'Build'; buttonDisabled = false;
      buttonOnClick = handleBuild;
      break;
    case 'starting':
      buttonLabel = 'Starting\u2026'; buttonDisabled = true; buttonOnClick = null;
      break;
    case 'building':
      buttonLabel = 'Building\u2026'; buttonDisabled = true; buttonOnClick = null;
      break;
    case 'error':
      buttonLabel = 'Unavailable'; buttonDisabled = true; buttonOnClick = null;
      break;
    default:
      buttonLabel = 'Go'; buttonDisabled = true; buttonOnClick = null;
  }

  const presetsDisabled = busy || status === 'checking' || status === 'error';

  return (
    <>
      <style>{`@keyframes toolpreview-spin { to { transform: rotate(360deg); } }`}</style>
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
            maxWidth: 640,
            maxHeight: '80vh',
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
                  {doc?.name || tool.name}
                </h2>
                <LayerPill layer={doc?.layer || tool.layer || ''} />
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
                color: layerColor,
                lineHeight: 1.5,
              }}>
                {doc.summary}
              </p>
            )}

            {/* Description */}
            {doc?.description && (
              <p style={{
                margin: '0 0 0',
                fontSize: 13,
                color: 'rgba(255,255,255,0.6)',
                lineHeight: 1.7,
              }}>
                {doc.description}
              </p>
            )}

            {/* When to Use */}
            {doc?.whenToUse && (
              <>
                <Divider />
                <div style={{
                  background: 'rgba(99,102,241,0.05)',
                  border: '1px solid rgba(99,102,241,0.12)',
                  borderRadius: 10,
                  padding: '12px 14px',
                }}>
                  <SectionLabel>When to Use</SectionLabel>
                  <p style={{
                    margin: 0,
                    fontSize: 12,
                    color: 'rgba(255,255,255,0.55)',
                    lineHeight: 1.7,
                  }}>
                    {doc.whenToUse}
                  </p>
                </div>
              </>
            )}

            {/* Capabilities */}
            {doc?.capabilities?.length > 0 && (
              <>
                <Divider />
                <SectionLabel>Capabilities</SectionLabel>
                <ul style={{
                  margin: 0,
                  padding: '0 0 0 18px',
                  listStyle: 'none',
                }}>
                  {doc.capabilities.map((cap, i) => (
                    <li key={i} style={{
                      fontSize: 12,
                      color: 'rgba(255,255,255,0.55)',
                      lineHeight: 1.7,
                      position: 'relative',
                      paddingLeft: 0,
                    }}>
                      <span style={{
                        position: 'absolute',
                        left: -14,
                        color: layerColor,
                        fontSize: 8,
                        top: 5,
                      }}>{'\u25CF'}</span>
                      {cap}
                    </li>
                  ))}
                </ul>
              </>
            )}

            {/* Parameters */}
            {params.length > 0 && (
              <>
                <Divider />
                <SectionLabel>Parameters</SectionLabel>
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 6,
                }}>
                  {params.map(([name, param]) => (
                    <div key={name} style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: 8,
                      padding: '6px 10px',
                      background: 'rgba(255,255,255,0.02)',
                      borderRadius: 8,
                      border: '1px solid rgba(255,255,255,0.04)',
                    }}>
                      <code style={{
                        fontSize: 11,
                        fontWeight: 600,
                        color: theme.colors.text,
                        fontFamily: theme.fonts.mono,
                        flexShrink: 0,
                        marginTop: 1,
                      }}>
                        {name}
                      </code>
                      <TypeBadge type={param.type} />
                      <span style={{
                        fontSize: 11,
                        color: 'rgba(255,255,255,0.45)',
                        lineHeight: 1.5,
                      }}>
                        {param.description}
                        {param.unit && <span style={{ color: 'rgba(255,255,255,0.3)' }}> ({param.unit})</span>}
                        {param.range && <span style={{ color: 'rgba(255,255,255,0.3)' }}> [{param.range}]</span>}
                      </span>
                    </div>
                  ))}
                </div>
              </>
            )}

            {/* Expected Outputs */}
            {outputs.length > 0 && (
              <>
                <Divider />
                <SectionLabel>Expected Outputs</SectionLabel>
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 4,
                }}>
                  {outputs.map(([key, desc]) => (
                    <div key={key} style={{
                      display: 'flex',
                      gap: 8,
                      fontSize: 12,
                      lineHeight: 1.6,
                      padding: '3px 0',
                    }}>
                      <code style={{
                        fontFamily: theme.fonts.mono,
                        fontWeight: 600,
                        color: theme.colors.text,
                        fontSize: 11,
                        flexShrink: 0,
                      }}>
                        {key}
                      </code>
                      <span style={{ color: 'rgba(255,255,255,0.45)' }}>{desc}</span>
                    </div>
                  ))}
                </div>
              </>
            )}

            {/* Presets */}
            {toolPresets.length > 0 && (
              <>
                <Divider />
                <SectionLabel>Presets</SectionLabel>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {toolPresets.map(preset => (
                    <PresetMiniCard
                      key={preset.key}
                      preset={preset}
                      disabled={presetsDisabled}
                      onClick={() => handleGo({ type: 'preset', preset })}
                    />
                  ))}
                </div>
              </>
            )}

            {/* Limitations (collapsible) */}
            {doc?.limitations?.length > 0 && (
              <>
                <Divider />
                <button
                  onClick={() => setLimitsOpen(p => !p)}
                  style={{
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    padding: 0,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    color: 'rgba(255,255,255,0.35)',
                    fontSize: 10,
                    fontWeight: 600,
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                  }}
                >
                  <span style={{
                    fontSize: 8,
                    transition: 'transform 0.15s ease-out',
                    transform: limitsOpen ? 'rotate(0deg)' : 'rotate(-90deg)',
                    display: 'inline-block',
                  }}>
                    {'\u25BC'}
                  </span>
                  Limitations
                </button>
                {limitsOpen && (
                  <ul style={{
                    margin: '8px 0 0',
                    padding: '0 0 0 18px',
                    listStyle: 'none',
                  }}>
                    {doc.limitations.map((lim, i) => (
                      <li key={i} style={{
                        fontSize: 12,
                        color: 'rgba(255,255,255,0.4)',
                        lineHeight: 1.7,
                        position: 'relative',
                      }}>
                        <span style={{
                          position: 'absolute',
                          left: -14,
                          color: 'rgba(255,255,255,0.2)',
                          fontSize: 8,
                          top: 5,
                        }}>{'\u25CF'}</span>
                        {lim}
                      </li>
                    ))}
                  </ul>
                )}
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
              {statusDot === 'spinner' ? (
                <SpinnerDot />
              ) : (
                <span style={{
                  width: 7,
                  height: 7,
                  borderRadius: '50%',
                  background: statusDot,
                  boxShadow: statusDot === theme.colors.success ? `0 0 6px ${theme.colors.success}60` : 'none',
                  flexShrink: 0,
                }} />
              )}
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
                  : status === 'not_found' ? theme.colors.warning : layerColor,
                border: 'none',
                borderRadius: 10,
                color: buttonDisabled ? 'rgba(255,255,255,0.3)' : '#fff',
                fontSize: 13,
                fontWeight: 600,
                cursor: buttonDisabled ? 'not-allowed' : 'pointer',
                transition: 'all 0.15s ease-out',
                boxShadow: buttonDisabled ? 'none'
                  : `0 4px 14px ${status === 'not_found' ? theme.colors.warning : layerColor}40`,
                flexShrink: 0,
                letterSpacing: '0.01em',
              }}
              onMouseEnter={e => {
                if (!buttonDisabled) {
                  const c = status === 'not_found' ? theme.colors.warning : layerColor;
                  e.currentTarget.style.transform = 'translateY(-1px)';
                  e.currentTarget.style.boxShadow = `0 6px 20px ${c}50`;
                }
              }}
              onMouseLeave={e => {
                if (!buttonDisabled) {
                  const c = status === 'not_found' ? theme.colors.warning : layerColor;
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
