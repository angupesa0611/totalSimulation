import { useState, useCallback, useEffect, useRef } from 'react';
import { submitSweep } from '../api/client';

/**
 * Hook for managing parameter sweep submission and WebSocket tracking.
 */
export function useSweep() {
  const [sweepId, setSweepId] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState(null);
  const [runs, setRuns] = useState([]);
  const [totalRuns, setTotalRuns] = useState(0);
  const [completedRuns, setCompletedRuns] = useState(0);
  const [failedRuns, setFailedRuns] = useState(0);
  const wsRef = useRef(null);

  const run = useCallback(async (request) => {
    setError(null);
    setSubmitting(true);
    try {
      const response = await submitSweep(request);
      setSweepId(response.sweep_id);
      setStatus(response.status || 'RUNNING');
      setRuns(response.runs || []);
      setTotalRuns(response.total_runs || 0);
      setCompletedRuns(response.completed_runs || 0);
      setFailedRuns(response.failed_runs || 0);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setSubmitting(false);
    }
  }, []);

  // WebSocket connection for sweep updates
  useEffect(() => {
    if (!sweepId) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/sweep/${sweepId}`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStatus(data.status);
      setRuns(data.runs || []);
      setTotalRuns(data.total_runs || 0);
      setCompletedRuns(data.completed_runs || 0);
      setFailedRuns(data.failed_runs || 0);
    };

    ws.onerror = () => setError('Sweep WebSocket error');
    ws.onclose = () => {};

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [sweepId]);

  const reset = useCallback(() => {
    setSweepId(null);
    setSubmitting(false);
    setError(null);
    setStatus(null);
    setRuns([]);
    setTotalRuns(0);
    setCompletedRuns(0);
    setFailedRuns(0);
  }, []);

  const progress = totalRuns > 0 ? (completedRuns + failedRuns) / totalRuns : 0;

  return {
    run,
    reset,
    sweepId,
    submitting,
    error,
    status,
    runs,
    totalRuns,
    completedRuns,
    failedRuns,
    progress,
    isRunning: submitting || (status === 'RUNNING'),
    isDone: status === 'SUCCESS' || status === 'PARTIAL',
    isFailed: status === 'FAILURE' || !!error,
  };
}
