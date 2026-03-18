import React, { useState, useCallback, useEffect } from 'react';
import { getCouplings, getLayers, getPipelines, getPipeline, submitPipelineRender, submitDAGPipeline } from '../api/client';
import { usePipeline } from '../hooks/usePipeline';
import { InputField, DropdownSelect, RunButton, ProgressBar } from './shared';
import HelpButton from './shared/HelpButton';
import theme from '../theme.json';

const ACCENT = '#f472b6';

export default function PipelineBuilder({ onOpenDocs, initialPipeline, initialCoupling }) {
  const [steps, setSteps] = useState([{ tool: '', params: {}, param_map: {} }]);
  const [couplings, setCouplings] = useState({});
  const [tools, setTools] = useState([]);
  const [namedPipelines, setNamedPipelines] = useState({});
  const [loadingPipeline, setLoadingPipeline] = useState(null);
  const [renderingPipeline, setRenderingPipeline] = useState(false);
  const [pipelineRenderResult, setPipelineRenderResult] = useState(null);
  const [dagMode, setDagMode] = useState(false);
  const [dagSteps, setDagSteps] = useState([{ id: 'step_1', tool: '', params: {}, depends_on: [], param_map: {}, condition: '' }]);
  const [dagStatus, setDagStatus] = useState(null);
  const [dagError, setDagError] = useState(null);
  const [dagRunning, setDagRunning] = useState(false);
  const pipeline = usePipeline();

  useEffect(() => {
    getCouplings().then(setCouplings).catch(console.error);
    getPipelines().then(setNamedPipelines).catch(console.error);
    getLayers().then(layers => {
      const allTools = [];
      for (const layer of layers) {
        for (const tool of layer.tools) {
          allTools.push(tool);
        }
      }
      setTools(allTools);
    }).catch(console.error);
  }, []);

  // Pre-load a named pipeline when navigating from dashboard
  useEffect(() => {
    if (initialPipeline) {
      loadNamedPipeline(initialPipeline);
    }
  }, [initialPipeline]); // eslint-disable-line react-hooks/exhaustive-deps

  // Pre-populate a 2-step pipeline from a coupling
  useEffect(() => {
    if (initialCoupling && couplings[initialCoupling]) {
      const c = couplings[initialCoupling];
      setSteps([
        { tool: c.from, params: {}, param_map: {} },
        { tool: c.to, params: {}, param_map: c.default_param_map || {} },
      ]);
    }
  }, [initialCoupling, couplings]);

  const loadNamedPipeline = useCallback(async (key) => {
    setLoadingPipeline(key);
    try {
      const full = await getPipeline(key);
      setSteps(full.steps.map(s => ({
        tool: s.tool,
        params: s.params || {},
        param_map: s.param_map || {},
        label: s.label || '',
      })));
    } catch (err) {
      console.error('Failed to load pipeline:', err);
    }
    setLoadingPipeline(null);
  }, []);

  const addStep = useCallback(() => {
    setSteps(prev => [...prev, { tool: '', params: {}, param_map: {} }]);
  }, []);

  const removeStep = useCallback((idx) => {
    setSteps(prev => prev.filter((_, i) => i !== idx));
  }, []);

  const updateStep = useCallback((idx, field, value) => {
    setSteps(prev => prev.map((s, i) => i === idx ? { ...s, [field]: value } : s));
  }, []);

  const handleRun = useCallback(() => {
    const validSteps = steps.filter(s => s.tool);
    if (validSteps.length === 0) return;

    pipeline.run({
      steps: validSteps,
      label: 'Pipeline run',
    });
  }, [steps, pipeline]);

  // Find suggested couplings for current tool sequence
  const suggestedCouplings = [];
  for (const [key, coupling] of Object.entries(couplings)) {
    if (coupling.type === 'sequential') {
      suggestedCouplings.push({ key, ...coupling });
    }
  }

  const addDagStep = useCallback(() => {
    const nextId = `step_${dagSteps.length + 1}`;
    setDagSteps(prev => [...prev, { id: nextId, tool: '', params: {}, depends_on: [], param_map: {}, condition: '' }]);
  }, [dagSteps.length]);

  const removeDagStep = useCallback((idx) => {
    const removedId = dagSteps[idx]?.id;
    setDagSteps(prev => prev.filter((_, i) => i !== idx).map(s => ({
      ...s,
      depends_on: s.depends_on.filter(d => d !== removedId),
    })));
  }, [dagSteps]);

  const updateDagStep = useCallback((idx, field, value) => {
    setDagSteps(prev => prev.map((s, i) => i === idx ? { ...s, [field]: value } : s));
  }, []);

  const handleRunDag = useCallback(async () => {
    const validSteps = dagSteps.filter(s => s.tool);
    if (validSteps.length === 0) return;
    setDagRunning(true);
    setDagError(null);
    try {
      const res = await submitDAGPipeline({ steps: validSteps, label: 'DAG Pipeline' });
      setDagStatus(res);
    } catch (err) {
      setDagError(err.response?.data?.detail || err.message);
    }
    setDagRunning(false);
  }, [dagSteps]);

  const toolOptions = tools.map(t => ({ value: t.key, label: t.name }));

  return (
    <div style={{
      padding: 16,
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <h3 style={{ fontSize: 14, color: theme.colors.text, margin: 0 }}>
            Pipeline Builder
          </h3>
          {onOpenDocs && (
            <HelpButton
              onClick={() => onOpenDocs('pipelines', '')}
              title="Pipeline documentation"
            />
          )}
        </div>
        <div style={{ display: 'flex', gap: 2, background: theme.colors.bgTertiary, borderRadius: 4, padding: 2 }}>
          {['Sequential', 'DAG'].map(m => (
            <button
              key={m}
              onClick={() => setDagMode(m === 'DAG')}
              style={{
                padding: '3px 8px', fontSize: 10,
                background: (dagMode ? 'DAG' : 'Sequential') === m ? theme.colors.accent : 'transparent',
                color: (dagMode ? 'DAG' : 'Sequential') === m ? '#fff' : theme.colors.textSecondary,
                border: 'none', borderRadius: 3, cursor: 'pointer',
              }}
            >{m}</button>
          ))}
        </div>
      </div>

      {dagMode ? (
      /* ===== DAG MODE ===== */
      <>
        <div style={{ flex: 1, overflowY: 'auto', paddingRight: 4 }}>
          {dagSteps.map((step, idx) => (
            <div key={idx} style={{
              padding: 12, marginBottom: 8,
              background: theme.colors.bgTertiary, borderRadius: 8,
              border: `1px solid ${theme.colors.border}`,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <span style={{ fontSize: 11, color: theme.colors.accent, fontFamily: 'monospace' }}>
                  {step.id}
                </span>
                {dagSteps.length > 1 && (
                  <button onClick={() => removeDagStep(idx)} style={{
                    background: 'none', border: 'none', color: theme.colors.error,
                    fontSize: 11, cursor: 'pointer',
                  }}>Remove</button>
                )}
              </div>

              <div style={{ marginBottom: 6 }}>
                <label style={{ fontSize: 10, color: theme.colors.textSecondary }}>ID</label>
                <input
                  value={step.id}
                  onChange={e => updateDagStep(idx, 'id', e.target.value)}
                  style={{
                    width: '100%', padding: '3px 6px', fontSize: 11,
                    background: theme.colors.bg, color: theme.colors.text,
                    border: `1px solid ${theme.colors.border}`, borderRadius: 3,
                    boxSizing: 'border-box',
                  }}
                />
              </div>

              <DropdownSelect
                label="Tool"
                value={step.tool}
                onChange={(v) => updateDagStep(idx, 'tool', v)}
                options={[{ value: '', label: 'Select tool...' }, ...toolOptions]}
              />

              <div style={{ marginTop: 6 }}>
                <label style={{ fontSize: 10, color: theme.colors.textSecondary }}>Depends On</label>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 2 }}>
                  {dagSteps.filter((_, i) => i !== idx).map(other => (
                    <button
                      key={other.id}
                      onClick={() => {
                        const deps = step.depends_on.includes(other.id)
                          ? step.depends_on.filter(d => d !== other.id)
                          : [...step.depends_on, other.id];
                        updateDagStep(idx, 'depends_on', deps);
                      }}
                      style={{
                        padding: '2px 6px', fontSize: 9,
                        background: step.depends_on.includes(other.id) ? theme.colors.accent : theme.colors.bg,
                        color: step.depends_on.includes(other.id) ? '#fff' : theme.colors.textSecondary,
                        border: `1px solid ${step.depends_on.includes(other.id) ? theme.colors.accent : theme.colors.border}`,
                        borderRadius: 3, cursor: 'pointer',
                      }}
                    >{other.id}</button>
                  ))}
                </div>
              </div>

              <div style={{ marginTop: 6 }}>
                <label style={{ fontSize: 10, color: theme.colors.textSecondary }}>Condition (optional)</label>
                <input
                  placeholder="$step_id.status == 'SUCCESS'"
                  value={step.condition}
                  onChange={e => updateDagStep(idx, 'condition', e.target.value)}
                  style={{
                    width: '100%', padding: '3px 6px', fontSize: 10,
                    background: theme.colors.bg, color: theme.colors.text,
                    border: `1px solid ${theme.colors.border}`, borderRadius: 3,
                    fontFamily: 'monospace', boxSizing: 'border-box',
                  }}
                />
              </div>

              {/* Dependency arrows */}
              {step.depends_on.length > 0 && (
                <div style={{
                  marginTop: 4, padding: 4,
                  background: '#14b8a611', borderRadius: 3,
                  fontSize: 9, color: '#14b8a6', fontFamily: 'monospace',
                }}>
                  depends: {step.depends_on.join(', ')}
                </div>
              )}
            </div>
          ))}

          <button onClick={addDagStep} style={{
            width: '100%', padding: 8, background: 'transparent',
            border: `1px dashed ${theme.colors.border}`, borderRadius: 6,
            color: theme.colors.textSecondary, fontSize: 12, cursor: 'pointer',
          }}>+ Add Step</button>
        </div>

        <div style={{ marginTop: 12 }}>
          <RunButton
            onClick={handleRunDag}
            loading={dagRunning}
            disabled={dagRunning || !dagSteps.some(s => s.tool)}
            label="Run DAG Pipeline"
          />
          {dagError && (
            <div style={{ marginTop: 8, padding: 8, background: '#1a0a0a', borderRadius: 6, border: '1px solid #ef4444', fontSize: 11, color: '#ef4444' }}>
              {typeof dagError === 'string' ? dagError : JSON.stringify(dagError)}
            </div>
          )}
          {dagStatus && (
            <div style={{ marginTop: 8, padding: 8, background: '#0a1a0a', borderRadius: 6, border: '1px solid #22c55e', fontSize: 11, color: '#22c55e' }}>
              DAG Pipeline submitted: {dagStatus.pipeline_id?.slice(0, 8)}... ({dagStatus.total_steps} steps)
            </div>
          )}
        </div>
      </>
      ) : (
      /* ===== SEQUENTIAL MODE ===== */
      <>
      {/* Named Pipelines */}
      {Object.keys(namedPipelines).length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 11, color: theme.colors.textSecondary, marginBottom: 6 }}>
            Named Pipelines
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4, maxHeight: 200, overflowY: 'auto' }}>
            {Object.entries(namedPipelines).map(([key, p]) => (
              <div key={key} style={{ display: 'flex', gap: 4, alignItems: 'stretch' }}>
                <button
                  onClick={() => loadNamedPipeline(key)}
                  disabled={loadingPipeline === key}
                  style={{
                    flex: 1,
                    padding: '8px 10px',
                    background: theme.colors.bgTertiary,
                    border: `1px solid #14b8a633`,
                    borderLeft: `3px solid #14b8a6`,
                    borderRadius: 4,
                    color: theme.colors.text,
                    fontSize: 11,
                    cursor: 'pointer',
                    textAlign: 'left',
                  }}
                >
                  <div style={{ fontWeight: 600, marginBottom: 2 }}>
                    {p.label}
                    <span style={{
                      marginLeft: 6,
                      fontSize: 10,
                      color: '#14b8a6',
                      background: '#14b8a618',
                      padding: '1px 5px',
                      borderRadius: 3,
                    }}>
                      {p.n_steps} steps
                    </span>
                  </div>
                  <div style={{ fontSize: 10, color: theme.colors.textSecondary, lineHeight: 1.3 }}>
                    {p.description}
                  </div>
                </button>
                {onOpenDocs && (
                  <div style={{ display: 'flex', alignItems: 'center', paddingRight: 2 }}>
                    <HelpButton
                      onClick={() => onOpenDocs('pipelines', key)}
                      title={`Documentation for ${p.label}`}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick couplings */}
      {suggestedCouplings.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 11, color: theme.colors.textSecondary, marginBottom: 6 }}>
            Quick Pipelines
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {suggestedCouplings.map(c => (
              <button
                key={c.key}
                onClick={() => {
                  setSteps([
                    { tool: c.from, params: {}, param_map: {} },
                    { tool: c.to, params: {}, param_map: c.default_param_map || {} },
                  ]);
                }}
                style={{
                  padding: '4px 10px',
                  background: theme.colors.bgTertiary,
                  border: `1px solid ${theme.colors.border}`,
                  borderRadius: 4,
                  color: theme.colors.text,
                  fontSize: 11,
                  cursor: 'pointer',
                }}
              >
                {c.from} → {c.to}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Steps */}
      <div style={{ flex: 1, overflowY: 'auto', paddingRight: 4 }}>
        {steps.map((step, idx) => (
          <div key={idx}>
            {idx > 0 && (
              <div style={{
                display: 'flex',
                justifyContent: 'center',
                padding: '4px 0',
                color: theme.colors.textSecondary,
                fontSize: 16,
              }}>
                ↓
              </div>
            )}
            <div style={{
              padding: 12,
              background: theme.colors.bgTertiary,
              borderRadius: 8,
              border: `1px solid ${theme.colors.border}`,
              position: 'relative',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <span style={{ fontSize: 11, color: theme.colors.textSecondary }}>
                  Step {idx + 1}
                </span>
                {steps.length > 1 && (
                  <button
                    onClick={() => removeStep(idx)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: theme.colors.error,
                      fontSize: 12,
                      cursor: 'pointer',
                    }}
                  >
                    Remove
                  </button>
                )}
              </div>

              <DropdownSelect
                label="Tool"
                value={step.tool}
                onChange={(v) => updateStep(idx, 'tool', v)}
                options={[{ value: '', label: 'Select tool...' }, ...toolOptions]}
              />

              {idx > 0 && step.param_map && Object.keys(step.param_map).length > 0 && (
                <div style={{
                  marginTop: 8,
                  padding: 6,
                  background: '#14b8a611',
                  borderRadius: 4,
                  fontSize: 10,
                  color: '#14b8a6',
                  fontFamily: theme.fonts.mono,
                }}>
                  {Object.entries(step.param_map).map(([k, v]) => (
                    <div key={k}>{k}: {v}</div>
                  ))}
                </div>
              )}

              {/* Pipeline step status */}
              {pipeline.steps[idx] && (
                <div style={{ marginTop: 8 }}>
                  <div style={{
                    fontSize: 11,
                    color: pipeline.steps[idx].status === 'SUCCESS' ? theme.colors.success
                      : pipeline.steps[idx].status === 'FAILURE' ? theme.colors.error
                      : theme.colors.textSecondary,
                  }}>
                    {pipeline.steps[idx].status}
                    {pipeline.steps[idx].message && ` — ${pipeline.steps[idx].message}`}
                  </div>
                  {pipeline.steps[idx].status === 'RUNNING' && (
                    <ProgressBar
                      progress={pipeline.steps[idx].progress}
                      message={pipeline.steps[idx].message}
                      status="PROGRESS"
                    />
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        <button
          onClick={addStep}
          style={{
            width: '100%',
            padding: 8,
            marginTop: 8,
            background: 'transparent',
            border: `1px dashed ${theme.colors.border}`,
            borderRadius: 6,
            color: theme.colors.textSecondary,
            fontSize: 12,
            cursor: 'pointer',
          }}
        >
          + Add Step
        </button>
      </div>

      {/* Run */}
      <div style={{ marginTop: 12 }}>
        <RunButton
          onClick={handleRun}
          loading={pipeline.isRunning}
          disabled={pipeline.isRunning || !steps.some(s => s.tool)}
          label="Run Pipeline"
        />

        {pipeline.isRunning && (
          <ProgressBar
            progress={pipeline.progress}
            message={`Step ${pipeline.currentStep + 1}/${pipeline.totalSteps}`}
            status="PROGRESS"
          />
        )}

        {pipeline.isDone && (
          <div style={{ marginTop: 8 }}>
            <div style={{ padding: 10, background: '#0a1a0a', borderRadius: 6, border: '1px solid #22c55e', fontSize: 12, color: '#22c55e' }}>
              Pipeline complete
            </div>
            <button
              onClick={async () => {
                if (!pipeline.pipelineId) return;
                setRenderingPipeline(true);
                setPipelineRenderResult(null);
                try {
                  const res = await submitPipelineRender(pipeline.pipelineId, { quality: 'medium_quality' });
                  setPipelineRenderResult(res);
                } catch (err) {
                  setPipelineRenderResult({ error: err.response?.data?.detail || err.message });
                }
                setRenderingPipeline(false);
              }}
              disabled={renderingPipeline}
              style={{
                width: '100%', marginTop: 6, padding: '8px 0',
                background: renderingPipeline ? theme.colors.bgTertiary : ACCENT,
                border: 'none', borderRadius: 6,
                color: '#fff', fontSize: 12, fontWeight: 600,
                cursor: renderingPipeline ? 'default' : 'pointer',
                opacity: renderingPipeline ? 0.7 : 1,
              }}
            >
              {renderingPipeline ? 'Rendering...' : 'Render Pipeline Animation'}
            </button>
            {pipelineRenderResult && !pipelineRenderResult.error && (
              <div style={{ marginTop: 6, padding: 8, background: '#0a0a1a', borderRadius: 4, border: `1px solid ${ACCENT}`, fontSize: 11, color: ACCENT }}>
                {pipelineRenderResult.render_jobs?.length || 0} render job(s) submitted
              </div>
            )}
            {pipelineRenderResult?.error && (
              <div style={{ marginTop: 6, padding: 8, background: '#1a0a0a', borderRadius: 4, border: '1px solid #ef4444', fontSize: 11, color: '#ef4444' }}>
                {pipelineRenderResult.error}
              </div>
            )}
          </div>
        )}

        {pipeline.isFailed && (
          <div style={{ marginTop: 8, padding: 10, background: '#1a0a0a', borderRadius: 6, border: '1px solid #ef4444', fontSize: 12, color: '#ef4444' }}>
            {pipeline.error || 'Pipeline failed'}
          </div>
        )}
      </div>
      </>
      )}
    </div>
  );
}
