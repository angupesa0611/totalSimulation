import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

let _getToken = () => null;
let _onUnauthorized = () => {};

export function setAuthCallbacks(getToken, onUnauthorized) {
  _getToken = getToken;
  _onUnauthorized = onUnauthorized;
}

api.interceptors.request.use((config) => {
  const token = _getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      _onUnauthorized();
    }
    return Promise.reject(error);
  },
);

export async function getLayers() {
  const { data } = await api.get('/layers');
  return data;
}

export async function getPresets() {
  const { data } = await api.get('/presets');
  return data;
}

export async function getPresetParams(key) {
  const { data } = await api.get(`/presets/${key}`);
  return data;
}

export async function submitSimulation(request) {
  const { data } = await api.post('/simulate', request);
  return data;
}

export async function getStatus(jobId) {
  const { data } = await api.get(`/status/${jobId}`);
  return data;
}

export async function getResults(project = '_default') {
  const { data } = await api.get('/results', { params: { project } });
  return data;
}

export async function searchResults({ project = '_default', tool, status, q, sort = 'newest', offset = 0, limit = 20 } = {}) {
  const params = { project, sort, offset, limit };
  if (tool) params.tool = tool;
  if (status) params.status = status;
  if (q) params.q = q;
  const { data } = await api.get('/results', { params });
  return data;
}

export async function getResult(jobId, project = '_default') {
  const { data } = await api.get(`/results/${jobId}`, { params: { project } });
  return data;
}

export async function getResultMetadata(jobId, project = '_default') {
  const { data } = await api.get(`/results/${jobId}/metadata`, { params: { project } });
  return data;
}

export async function deleteResult(jobId, project = '_default') {
  const { data } = await api.delete(`/results/${jobId}`, { params: { project } });
  return data;
}

export async function getResultFiles(jobId, project = '_default') {
  const { data } = await api.get(`/results/${jobId}/files`, { params: { project } });
  return data;
}

export async function submitPipeline(request) {
  const { data } = await api.post('/pipeline', request);
  return data;
}

export async function getPipelineStatus(pipelineId) {
  const { data } = await api.get(`/pipeline/${pipelineId}`);
  return data;
}

export async function getCouplings() {
  const { data } = await api.get('/couplings');
  return data;
}

export async function getPipelines() {
  const { data } = await api.get('/pipelines');
  return data;
}

export async function getPipeline(key) {
  const { data } = await api.get(`/pipelines/${key}`);
  return data;
}

// Sweep API
export async function submitSweep(request) {
  const { data } = await api.post('/sweep/', request);
  return data;
}

export async function getSweepStatus(sweepId) {
  const { data } = await api.get(`/sweep/${sweepId}`);
  return data;
}

export async function getSweepResults(sweepId) {
  const { data } = await api.get(`/sweep/${sweepId}/results`);
  return data;
}

export async function cancelSweep(sweepId) {
  const { data } = await api.delete(`/sweep/${sweepId}`);
  return data;
}

// Export API
export async function submitExport(request) {
  const { data } = await api.post('/export/', request);
  return data;
}

export async function downloadExport(exportId) {
  window.open(`/api/export/download/${exportId}`, '_blank');
}

export async function getExportFormats() {
  const { data } = await api.get('/export/formats');
  return data;
}

// DAG Pipeline API
export async function submitDAGPipeline(request) {
  const { data } = await api.post('/pipeline/dag', request);
  return data;
}

export async function getDAGPipelineStatus(pipelineId) {
  const { data } = await api.get(`/pipeline/dag/${pipelineId}`);
  return data;
}

// Metrics
export async function getMetrics() {
  const { data } = await api.get('/metrics');
  return data;
}

// Render API
export async function getRenderScenes(toolKey) {
  const { data } = await api.get(`/render/scenes/${toolKey}`);
  return data;
}

export async function submitRender(jobId, options = {}) {
  const { data } = await api.post(`/render/from-result/${jobId}`, options);
  return data;
}

export async function getRenderableTools() {
  const { data } = await api.get('/render/tools');
  return data;
}

export async function submitPipelineRender(pipelineId, options = {}) {
  const { data } = await api.post(`/render/pipeline/${pipelineId}`, options);
  return data;
}

// Job control
export async function cancelJob(jobId, project = '_default') {
  const { data } = await api.post(`/simulate/${jobId}/cancel`, null, { params: { project } });
  return data;
}

// Projects
export async function getProjects() {
  const { data } = await api.get('/projects');
  return data;
}

export async function createProject(name) {
  const { data } = await api.post('/projects', { name });
  return data;
}

export async function deleteProject(name) {
  const { data } = await api.delete(`/projects/${name}`);
  return data;
}

// Layer activation
export async function getLayerActivation() {
  const { data } = await api.get('/layers/activation');
  return data;
}

export async function activateLayers(layers) {
  const { data } = await api.post('/layers/activate', { layers });
  return data;
}

export async function deactivateLayers(layers) {
  const { data } = await api.post('/layers/deactivate', { layers });
  return data;
}

export default api;
