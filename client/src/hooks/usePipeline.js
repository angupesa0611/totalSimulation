import { useState, useCallback, useEffect, useRef } from 'react';
import { submitPipeline } from '../api/client';

/**
 * Hook for managing pipeline submission and multi-step WebSocket tracking.
 */
export function usePipeline() {
  const [pipelineId, setPipelineId] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState(null);
  const [steps, setSteps] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [totalSteps, setTotalSteps] = useState(0);
  const [pipelineStatus, setPipelineStatus] = useState(null);
  const wsRef = useRef(null);

  const run = useCallback(async (request) => {
    setError(null);
    setSubmitting(true);
    try {
      const response = await submitPipeline(request);
      setPipelineId(response.pipeline_id);
      setStatus('RUNNING');
      setSteps(response.steps || []);
      setCurrentStep(response.current_step || 0);
      setTotalSteps(response.total_steps || 0);
      setPipelineStatus(response);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setSubmitting(false);
    }
  }, []);

  // WebSocket connection for pipeline updates
  useEffect(() => {
    if (!pipelineId) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/pipeline/${pipelineId}`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStatus(data.status);
      setSteps(data.steps || []);
      setCurrentStep(data.current_step || 0);
      setTotalSteps(data.total_steps || 0);
      setPipelineStatus(data);
    };

    ws.onerror = () => setError('Pipeline WebSocket error');
    ws.onclose = () => {};

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [pipelineId]);

  const reset = useCallback(() => {
    setPipelineId(null);
    setSubmitting(false);
    setError(null);
    setStatus(null);
    setSteps([]);
    setCurrentStep(0);
    setTotalSteps(0);
    setPipelineStatus(null);
  }, []);

  // Compute overall progress
  const progress = totalSteps > 0
    ? steps.reduce((sum, s) => sum + (s.progress || 0), 0) / totalSteps
    : 0;

  // Get last completed step's result
  const lastResult = steps.filter(s => s.status === 'SUCCESS').pop()?.result || null;

  return {
    run,
    reset,
    pipelineId,
    submitting,
    error,
    status,
    steps,
    currentStep,
    totalSteps,
    pipelineStatus,
    progress,
    lastResult,
    isRunning: submitting || status === 'RUNNING',
    isDone: status === 'SUCCESS',
    isFailed: status === 'FAILURE' || !!error,
  };
}
