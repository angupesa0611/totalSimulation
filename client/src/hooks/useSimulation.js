import { useState, useCallback } from 'react';
import { submitSimulation, getStatus, cancelJob } from '../api/client';
import { useWebSocket } from './useWebSocket';

export function useSimulation() {
  const [jobId, setJobId] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [cancelled, setCancelled] = useState(false);

  const ws = useWebSocket(jobId);

  const run = useCallback(async (request) => {
    setError(null);
    setSubmitting(true);
    setCancelled(false);
    try {
      const response = await submitSimulation(request);
      setJobId(response.job_id);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setSubmitting(false);
    }
  }, []);

  const cancel = useCallback(async () => {
    if (!jobId) return;
    try {
      await cancelJob(jobId);
      setCancelled(true);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    }
  }, [jobId]);

  const reset = useCallback(() => {
    setJobId(null);
    setError(null);
    setSubmitting(false);
    setCancelled(false);
  }, []);

  const terminalStates = ['SUCCESS', 'FAILURE', 'REVOKED', 'CANCELLED'];

  return {
    run,
    cancel,
    reset,
    jobId,
    submitting,
    error,
    cancelled,
    status: cancelled ? 'CANCELLED' : ws.status,
    progress: ws.progress,
    message: ws.message,
    result: ws.result,
    connected: ws.connected,
    isRunning: !cancelled && (submitting || !!(ws.status && !terminalStates.includes(ws.status))),
    isDone: ws.status === 'SUCCESS',
    isFailed: ws.status === 'FAILURE' || !!error,
    isCancelled: cancelled || ws.status === 'REVOKED',
  };
}
