import { useState, useCallback } from 'react';
import { submitRender, getRenderScenes } from '../api/client';
import { useWebSocket } from './useWebSocket';

export function useRender() {
  const [renderJobId, setRenderJobId] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [scenes, setScenes] = useState([]);
  const [scenesLoading, setScenesLoading] = useState(false);

  const ws = useWebSocket(renderJobId);

  const loadScenes = useCallback(async (toolKey) => {
    setScenesLoading(true);
    try {
      const data = await getRenderScenes(toolKey);
      setScenes(data.scenes || []);
    } catch {
      setScenes([]);
    }
    setScenesLoading(false);
  }, []);

  const startRender = useCallback(async (jobId, options = {}) => {
    setError(null);
    setSubmitting(true);
    try {
      const response = await submitRender(jobId, options);
      setRenderJobId(response.render_job_id);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setSubmitting(false);
    }
  }, []);

  const resetRender = useCallback(() => {
    setRenderJobId(null);
    setError(null);
    setSubmitting(false);
    setScenes([]);
  }, []);

  return {
    startRender,
    resetRender,
    loadScenes,
    scenes,
    scenesLoading,
    renderJobId,
    submitting,
    error,
    isRendering: submitting || (ws.status && !['SUCCESS', 'FAILURE'].includes(ws.status)),
    isDone: ws.status === 'SUCCESS',
    isFailed: ws.status === 'FAILURE' || !!error,
    progress: ws.progress,
    message: ws.message,
    result: ws.result,
  };
}
