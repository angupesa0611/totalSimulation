import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

// Mock axios
vi.mock('axios', () => {
  const mockInstance = {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
    interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } },
  };
  return {
    default: { create: vi.fn(() => mockInstance), ...mockInstance },
    create: vi.fn(() => mockInstance),
  };
});

describe('API Client', () => {
  let client;
  let api;

  beforeEach(async () => {
    vi.resetModules();
    client = await import('../client.js');
    // Get the mocked api instance
    api = (await import('axios')).default;
  });

  describe('getLayers', () => {
    it('calls GET /layers', async () => {
      const mockLayers = [{ key: 'astrophysics', name: 'Astrophysics', tools: [] }];
      api.get.mockResolvedValueOnce({ data: mockLayers });

      const result = await client.getLayers();
      expect(api.get).toHaveBeenCalledWith('/layers');
      expect(result).toEqual(mockLayers);
    });
  });

  describe('submitSimulation', () => {
    it('calls POST /simulate with request', async () => {
      const request = { tool: 'rebound', params: { n_steps: 100 } };
      const response = { job_id: 'test-123', status: 'PENDING' };
      api.post.mockResolvedValueOnce({ data: response });

      const result = await client.submitSimulation(request);
      expect(api.post).toHaveBeenCalledWith('/simulate', request);
      expect(result.job_id).toBe('test-123');
    });
  });

  describe('sweep API functions', () => {
    it('submitSweep calls POST /sweep/', async () => {
      const request = { tool: 'rebound', base_params: {}, axes: [] };
      const response = { sweep_id: 'sweep-123', status: 'RUNNING' };
      api.post.mockResolvedValueOnce({ data: response });

      const result = await client.submitSweep(request);
      expect(api.post).toHaveBeenCalledWith('/sweep/', request);
      expect(result.sweep_id).toBe('sweep-123');
    });

    it('getSweepStatus calls GET /sweep/{id}', async () => {
      const response = { sweep_id: 's1', status: 'RUNNING', runs: [] };
      api.get.mockResolvedValueOnce({ data: response });

      const result = await client.getSweepStatus('s1');
      expect(api.get).toHaveBeenCalledWith('/sweep/s1');
      expect(result.status).toBe('RUNNING');
    });
  });

  describe('export API functions', () => {
    it('submitExport calls POST /export/', async () => {
      const request = { job_ids: ['j1'], format: 'csv' };
      const response = { export_id: 'e1', download_url: '/api/export/download/e1' };
      api.post.mockResolvedValueOnce({ data: response });

      const result = await client.submitExport(request);
      expect(api.post).toHaveBeenCalledWith('/export/', request);
      expect(result.export_id).toBe('e1');
    });
  });

  describe('DAG pipeline API', () => {
    it('submitDAGPipeline calls POST /pipeline/dag', async () => {
      const request = { steps: [{ id: 'a', tool: 'rebound' }] };
      const response = { pipeline_id: 'dag-1', status: 'RUNNING' };
      api.post.mockResolvedValueOnce({ data: response });

      const result = await client.submitDAGPipeline(request);
      expect(api.post).toHaveBeenCalledWith('/pipeline/dag', request);
      expect(result.pipeline_id).toBe('dag-1');
    });
  });
});
