import React, { useState, useEffect, useCallback } from 'react';
import { RunButton, ProgressBar } from './shared';
import HelpButton from './shared/HelpButton';
import { PARAM_COMPONENTS } from './params/paramComponents';
import { pipelineDocs } from '../docs/pipelineDocs';
import { usePipeline } from '../hooks/usePipeline';
import theme from '../theme.json';

const teal = '#14b8a6';

function StepHeader({ index, toolKey, expanded, onToggle, status }) {
  const [hovered, setHovered] = useState(false);
  // Status dot color for pipeline progress
  let dotColor = 'rgba(255,255,255,0.2)';
  if (status === 'SUCCESS') dotColor = theme.colors.success;
  else if (status === 'RUNNING') dotColor = teal;
  else if (status === 'FAILURE') dotColor = theme.colors.error;

  return (
    <button
      onClick={onToggle}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        width: '100%',
        background: hovered ? 'rgba(255,255,255,0.04)' : 'transparent',
        border: 'none',
        borderBottom: '1px solid rgba(255,255,255,0.04)',
        cursor: 'pointer',
        padding: '10px 12px',
        textAlign: 'left',
        transition: 'background 0.15s ease-out',
      }}
    >
      <span style={{
        fontSize: 8,
        color: 'rgba(255,255,255,0.3)',
        transition: 'transform 0.15s ease-out',
        transform: expanded ? 'rotate(0deg)' : 'rotate(-90deg)',
        display: 'inline-block',
      }}>
        {'\u25BC'}
      </span>
      <span style={{
        width: 7,
        height: 7,
        borderRadius: '50%',
        background: dotColor,
        boxShadow: status === 'RUNNING' ? `0 0 6px ${teal}80` : 'none',
        flexShrink: 0,
      }} />
      <span style={{
        fontSize: 10,
        fontWeight: 700,
        color: teal,
        background: `${teal}15`,
        width: 18,
        height: 18,
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
      }}>
        {index + 1}
      </span>
      <span style={{
        fontSize: 12,
        fontWeight: 600,
        color: theme.colors.text,
        flex: 1,
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
      }}>
        {toolKey}
      </span>
    </button>
  );
}

export default function PipelinePanel({ pipeline, onOpenDocs, isMobile, style }) {
  const pipelineKey = pipeline?.key;
  const doc = pipelineDocs[pipelineKey] || null;
  const steps = doc?.steps || [];

  const pipelineHook = usePipeline();

  // Per-step params, initialized from recommendedParams
  const [stepParams, setStepParams] = useState({});
  // Track which steps are expanded (first step expanded by default)
  const [expanded, setExpanded] = useState({});

  // Initialize params and expanded state on pipeline change
  useEffect(() => {
    if (!doc) return;
    const initial = {};
    const exp = {};
    steps.forEach((step, i) => {
      initial[step.tool] = doc.recommendedParams?.[step.tool]
        ? { ...doc.recommendedParams[step.tool] }
        : {};
      exp[i] = i === 0; // expand first step by default
    });
    setStepParams(initial);
    setExpanded(exp);
    pipelineHook.reset();
  }, [pipelineKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const toggleStep = useCallback((index) => {
    setExpanded(prev => ({ ...prev, [index]: !prev[index] }));
  }, []);

  const updateStepParams = useCallback((toolKey, newParams) => {
    setStepParams(prev => ({ ...prev, [toolKey]: newParams }));
  }, []);

  const handleRun = useCallback(() => {
    if (!doc) return;
    const request = {
      steps: steps.map(step => ({
        tool: step.tool,
        params: stepParams[step.tool] || {},
        param_map: {},
      })),
      label: doc.label,
    };
    pipelineHook.run(request);
  }, [doc, steps, stepParams, pipelineHook]);

  // No doc found
  if (!doc) {
    return (
      <div style={{
        width: 320,
        background: theme.colors.bgSecondary,
        borderRight: `1px solid ${theme.colors.border}`,
        padding: 24,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: theme.colors.textSecondary,
        fontSize: 14,
        flexShrink: 0,
        ...style,
      }}>
        Pipeline not found
      </div>
    );
  }

  // Get step status from pipeline hook
  const getStepStatus = (index) => {
    const hookStep = pipelineHook.steps[index];
    return hookStep?.status || null;
  };

  return (
    <div style={{
      width: 320,
      background: theme.colors.bgSecondary,
      borderRight: `1px solid ${theme.colors.border}`,
      display: 'flex',
      flexDirection: 'column',
      flexShrink: 0,
      overflow: 'hidden',
      ...style,
    }}>
      {/* Header */}
      <div style={{
        padding: '14px 16px 12px',
        borderBottom: `1px solid ${theme.colors.border}`,
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, margin: 0, color: theme.colors.text }}>
            {doc.label}
          </h3>
          <span style={{
            fontSize: 10,
            fontWeight: 600,
            color: teal,
            background: `${teal}18`,
            padding: '2px 8px',
            borderRadius: 9999,
            border: `1px solid ${teal}25`,
          }}>
            {steps.length} steps
          </span>
          {onOpenDocs && (
            <HelpButton
              onClick={() => onOpenDocs('pipelines', pipelineKey)}
              title={`Documentation for ${doc.label}`}
            />
          )}
        </div>
        <p style={{ fontSize: 11, color: theme.colors.textSecondary, margin: 0, lineHeight: 1.5 }}>
          {doc.summary}
        </p>
      </div>

      {/* Steps with param forms */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {steps.map((step, i) => {
          const ParamComponent = PARAM_COMPONENTS[step.tool] || null;
          const isExpanded = expanded[i];
          const stepStatus = getStepStatus(i);

          return (
            <div key={`${step.tool}-${i}`}>
              <StepHeader
                index={i}
                toolKey={step.tool}
                expanded={isExpanded}
                onToggle={() => toggleStep(i)}
                status={stepStatus}
              />
              {isExpanded && (
                <div style={{
                  padding: '12px 14px',
                  borderBottom: '1px solid rgba(255,255,255,0.04)',
                  background: 'rgba(255,255,255,0.015)',
                }}>
                  {ParamComponent ? (
                    <ParamComponent
                      params={stepParams[step.tool] || {}}
                      onChange={(p) => updateStepParams(step.tool, p)}
                    />
                  ) : (
                    <div style={{
                      fontSize: 11,
                      color: theme.colors.textSecondary,
                      padding: '8px 0',
                    }}>
                      No configurable parameters
                    </div>
                  )}
                  {/* Step role description */}
                  <div style={{
                    marginTop: 8,
                    fontSize: 10,
                    color: 'rgba(255,255,255,0.35)',
                    lineHeight: 1.5,
                    fontStyle: 'italic',
                  }}>
                    {step.role}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Bottom controls */}
      <div style={{
        padding: '12px 14px',
        borderTop: `1px solid ${theme.colors.border}`,
        flexShrink: 0,
      }}>
        <RunButton
          onClick={handleRun}
          loading={pipelineHook.isRunning}
          disabled={pipelineHook.isRunning}
          label="Run Pipeline"
        />

        {/* Pipeline progress */}
        {pipelineHook.isRunning && (
          <div style={{ marginTop: 8 }}>
            <ProgressBar
              progress={pipelineHook.progress}
              message={`Step ${pipelineHook.currentStep + 1}/${pipelineHook.totalSteps}`}
              status={pipelineHook.status}
            />
            {/* Per-step mini status */}
            <div style={{ marginTop: 6, display: 'flex', gap: 3 }}>
              {pipelineHook.steps.map((s, i) => (
                <div key={i} style={{
                  flex: 1,
                  height: 3,
                  borderRadius: 2,
                  background: s.status === 'SUCCESS' ? theme.colors.success
                    : s.status === 'RUNNING' ? teal
                    : s.status === 'FAILURE' ? theme.colors.error
                    : 'rgba(255,255,255,0.08)',
                  transition: 'background 0.3s ease-out',
                }} />
              ))}
            </div>
          </div>
        )}

        {pipelineHook.isDone && (
          <div style={{
            marginTop: 8,
            padding: 10,
            background: '#0a1a0a',
            borderRadius: 8,
            border: '1px solid #22c55e',
            fontSize: 12,
            color: '#22c55e',
            textAlign: 'center',
          }}>
            Pipeline complete
          </div>
        )}

        {pipelineHook.isFailed && (
          <div style={{
            marginTop: 8,
            padding: 10,
            background: '#1a0a0a',
            borderRadius: 8,
            border: '1px solid #ef4444',
            fontSize: 12,
            color: '#ef4444',
            textAlign: 'center',
          }}>
            {pipelineHook.error || 'Pipeline failed'}
          </div>
        )}
      </div>
    </div>
  );
}
