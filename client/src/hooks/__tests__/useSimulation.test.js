import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';

// Mock the API client
vi.mock('../../api/client.js', () => ({
  submitSimulation: vi.fn(),
  getStatus: vi.fn(),
}));

// Mock useWebSocket
vi.mock('../useWebSocket.js', () => ({
  useWebSocket: vi.fn(() => ({
    status: null,
    progress: 0,
    message: '',
    result: null,
    connected: false,
  })),
}));

describe('useSimulation', () => {
  let useSimulation;
  let submitSimulation;
  let useWebSocket;

  beforeEach(async () => {
    vi.resetModules();
    const simModule = await import('../useSimulation.js');
    useSimulation = simModule.useSimulation;
    submitSimulation = (await import('../../api/client.js')).submitSimulation;
    useWebSocket = (await import('../useWebSocket.js')).useWebSocket;
  });

  it('starts with null state', () => {
    const { result } = renderHook(() => useSimulation());

    expect(result.current.jobId).toBeNull();
    expect(result.current.submitting).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.isRunning).toBe(false);
    expect(result.current.isDone).toBe(false);
    expect(result.current.isFailed).toBe(false);
  });

  it('submits simulation and sets jobId', async () => {
    submitSimulation.mockResolvedValueOnce({ job_id: 'test-job-123' });

    const { result } = renderHook(() => useSimulation());

    await act(async () => {
      await result.current.run({ tool: 'rebound', params: {} });
    });

    expect(result.current.jobId).toBe('test-job-123');
    expect(result.current.submitting).toBe(false);
  });

  it('handles submission error', async () => {
    submitSimulation.mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => useSimulation());

    await act(async () => {
      await result.current.run({ tool: 'rebound', params: {} });
    });

    expect(result.current.error).toBe('Network error');
    expect(result.current.isFailed).toBe(true);
  });

  it('resets state', async () => {
    submitSimulation.mockResolvedValueOnce({ job_id: 'test-job-123' });

    const { result } = renderHook(() => useSimulation());

    await act(async () => {
      await result.current.run({ tool: 'rebound', params: {} });
    });

    act(() => {
      result.current.reset();
    });

    expect(result.current.jobId).toBeNull();
    expect(result.current.error).toBeNull();
  });
});
