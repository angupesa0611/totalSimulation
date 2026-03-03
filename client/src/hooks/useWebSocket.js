import { useEffect, useRef, useState, useCallback } from 'react';

export function useWebSocket(jobId) {
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('');
  const [result, setResult] = useState(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    if (!jobId) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    let wsUrl = `${protocol}//${window.location.host}/ws/simulation/${jobId}`;
    const token = localStorage.getItem('totalSim_token');
    if (token) wsUrl += `?token=${encodeURIComponent(token)}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStatus(data.status);

      if (data.progress !== undefined) setProgress(data.progress);
      if (data.message) setMessage(data.message);

      if (data.status === 'SUCCESS' && data.result) {
        setResult(data.result);
        setProgress(1);
      }
      if (data.status === 'FAILURE') {
        setMessage(data.message || 'Simulation failed');
      }
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [jobId]);

  return { status, progress, message, result, connected };
}
