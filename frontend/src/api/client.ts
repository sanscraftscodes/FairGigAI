const BASE_URL = '/api';

export async function apiRequest<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let errorMsg = `HTTP Error ${response.status}`;
    try {
      const errData = await response.json();
      if (errData && errData.detail) {
        errorMsg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(errorMsg);
  }

  return response.json();
}

// Dashboard
export const getDashboardSummary = () => apiRequest<any>('/dashboard/summary');

// Tasks
export const getTasks = (params?: { task_type?: string; priority?: string; status?: string; search?: string; page?: number; limit?: number }) => {
  const query = new URLSearchParams();
  if (params?.task_type && params.task_type !== 'all') query.append('task_type', params.task_type);
  if (params?.priority && params.priority !== 'all') query.append('priority', params.priority);
  if (params?.status && params.status !== 'all') query.append('status', params.status);
  if (params?.search) query.append('search', params.search);
  if (params?.page) query.append('page', params.page.toString());
  if (params?.limit) query.append('limit', params.limit.toString());
  return apiRequest<any>(`/tasks?${query.toString()}`);
};

export const getTaskDetail = (taskId: string) => apiRequest<any>(`/tasks/${taskId}`);
export const createTask = (data: any) => apiRequest<any>('/tasks', { method: 'POST', body: JSON.stringify(data) });
export const validateTask = (data: any) => apiRequest<any>('/tasks/validate', { method: 'POST', body: JSON.stringify(data) });

// Workers
export const getWorkers = (params?: { skill?: string; vehicle_type?: string; availability?: string; search?: string; sort_by?: string; sort_order?: string; page?: number; limit?: number }) => {
  const query = new URLSearchParams();
  if (params?.skill && params.skill !== 'all') query.append('skill', params.skill);
  if (params?.vehicle_type && params.vehicle_type !== 'all') query.append('vehicle_type', params.vehicle_type);
  if (params?.availability && params.availability !== 'all') query.append('availability', params.availability);
  if (params?.search) query.append('search', params.search);
  if (params?.sort_by) query.append('sort_by', params.sort_by);
  if (params?.sort_order) query.append('sort_order', params.sort_order);
  if (params?.page) query.append('page', params.page.toString());
  if (params?.limit) query.append('limit', params.limit.toString());
  return apiRequest<any>(`/workers?${query.toString()}`);
};

export const getWorkerDetail = (workerId: string) => apiRequest<any>(`/workers/${workerId}`);
export const createSyntheticWorker = (data: any) => apiRequest<any>('/workers/synthetic', { method: 'POST', body: JSON.stringify(data) });

// Allocation
export const previewAllocation = (data: { task_id: string; lambda_val?: number; policy?: string; max_candidates?: number }) =>
  apiRequest<any>('/allocation/preview', { method: 'POST', body: JSON.stringify(data) });

export const runAllocation = (data: { task_id: string; lambda_val?: number; policy?: string; confirm?: boolean }) =>
  apiRequest<any>('/allocation/run', { method: 'POST', body: JSON.stringify(data) });

export const explainAllocation = (data: {
  task_id: string;
  worker_id: string;
  runner_up_id?: string;
  policy?: string;
  lambda_val?: number;
  provider?: string;
  ollama_url?: string;
}) => apiRequest<any>('/allocation/explain', { method: 'POST', body: JSON.stringify(data) });

export const getAllocationDetail = (allocId: string) => apiRequest<any>(`/allocation/${allocId}`);

// Agents
export const getAgentsStatus = () => apiRequest<any>('/agents/status');
export const runAgentsWorkflow = (data: { task_id: string; lambda_val?: number; policy?: string; max_candidates?: number }) =>
  apiRequest<any>('/agents/run', { method: 'POST', body: JSON.stringify(data) });

// Fairness
export const getFairnessSummary = () => apiRequest<any>('/fairness/summary');
export const getPolicyComparison = (lambdaVal: number = 0.08) => apiRequest<any>(`/fairness/policy-comparison?lambda_val=${lambdaVal}`);
export const runLambdaSweep = () => apiRequest<any>('/fairness/sweep', { method: 'POST' });

// Model
export const getModelStatus = () => apiRequest<any>('/model/status');
export const getModelMetrics = () => apiRequest<any>('/model/metrics');

// History
export const getAllocationHistory = (params?: { policy?: string; worker_id?: string; task_id?: string; status?: string; page?: number; limit?: number }) => {
  const query = new URLSearchParams();
  if (params?.policy && params.policy !== 'all') query.append('policy', params.policy);
  if (params?.status && params.status !== 'all') query.append('status', params.status);
  if (params?.worker_id) query.append('worker_id', params.worker_id);
  if (params?.task_id) query.append('task_id', params.task_id);
  if (params?.page) query.append('page', params.page.toString());
  if (params?.limit) query.append('limit', params.limit.toString());
  return apiRequest<any>(`/history?${query.toString()}`);
};

export const getHistoryDetail = (allocId: string) => apiRequest<any>(`/history/${allocId}`);
