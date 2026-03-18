import React from 'react';
import { RunButton, ProgressBar } from './shared';
import HelpButton from './shared/HelpButton';
import { PARAM_COMPONENTS } from './params/paramComponents';
import theme from '../theme.json';

export default function SimulationPanel({ tool, params, onParamsChange, onRun, simulation, onOpenDocs, style }) {
  const ParamComponent = tool ? PARAM_COMPONENTS[tool.key] : null;

  if (!tool) {
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
        Select a tool or preset to begin
      </div>
    );
  }

  return (
    <div style={{
      width: 320,
      background: theme.colors.bgSecondary,
      borderRight: `1px solid ${theme.colors.border}`,
      padding: 16,
      overflowY: 'auto',
      flexShrink: 0,
      ...style,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, margin: 0 }}>{tool.name}</h3>
        {onOpenDocs && (
          <HelpButton
            onClick={() => onOpenDocs('tools', tool.key)}
            title={`Documentation for ${tool.name}`}
          />
        )}
      </div>
      <p style={{ fontSize: 12, color: theme.colors.textSecondary, marginBottom: 16 }}>{tool.description}</p>

      {ParamComponent && (
        <ParamComponent params={params} onChange={onParamsChange} />
      )}

      <RunButton
        onClick={() => onRun({ tool: tool.key, params })}
        loading={simulation.isRunning}
        disabled={simulation.isRunning}
      />

      {simulation.isRunning && (
        <>
          {simulation.isStartingWorker && !simulation.jobId && (
            <div style={{
              marginTop: 8, padding: '6px 10px', background: '#1a1a0a',
              borderRadius: 6, border: '1px solid #f59e0b',
              fontSize: 11, color: '#f59e0b', textAlign: 'center',
            }}>
              Starting worker container...
            </div>
          )}
          <ProgressBar
            progress={simulation.progress}
            message={simulation.message}
            status={simulation.status}
            isStartingWorker={simulation.isStartingWorker && !simulation.jobId}
          />
          <button
            onClick={() => simulation.cancel()}
            style={{
              marginTop: 8,
              width: '100%',
              padding: '6px 0',
              background: 'transparent',
              border: `1px solid ${theme.colors.warning}`,
              borderRadius: 6,
              color: theme.colors.warning,
              fontSize: 12,
              cursor: 'pointer',
            }}
          >
            Cancel
          </button>
        </>
      )}

      {simulation.isCancelled && (
        <div style={{ marginTop: 12, padding: 12, background: '#1a1a0a', borderRadius: 8, border: `1px solid ${theme.colors.warning}`, fontSize: 12, color: theme.colors.warning }}>
          Simulation cancelled
        </div>
      )}

      {simulation.isFailed && !simulation.isCancelled && (
        <div style={{ marginTop: 12, padding: 12, background: '#1a0a0a', borderRadius: 8, border: '1px solid #ef4444', fontSize: 12, color: '#ef4444' }}>
          {simulation.error || simulation.message || 'Simulation failed'}
        </div>
      )}

      {simulation.isDone && (
        <div style={{ marginTop: 12, padding: 12, background: '#0a1a0a', borderRadius: 8, border: '1px solid #22c55e', fontSize: 12, color: '#22c55e' }}>
          Simulation complete
        </div>
      )}
    </div>
  );
}
