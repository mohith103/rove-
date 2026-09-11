/**
 * Typed API client for the ROVE backend.
 */
import type {
  AnalysisResponse,
  CreateMissionRequest,
  MissionDetail,
  MissionSummary,
  ModelsResponse,
  ReplayPayload,
  RunCounterfactualRequest,
  RunCounterfactualResponse,
  RunExperimentRequest,
  RunExperimentResponse,
} from '../types/mission';

const API_URL =
  (import.meta.env.VITE_API_URL as string | undefined) ??
  'http://127.0.0.1:8000';

export function missionStreamUrl(missionId: string): string {
  // If API_URL is relative (e.g. "/api"), build a same-origin WebSocket URL
  if (!/^https?:/.test(API_URL)) {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${proto}//${window.location.host}${API_URL}/missions/${missionId}/stream`;
  }
  const wsBase = API_URL.replace(/^http/, 'ws');
  return `${wsBase}/missions/${missionId}/stream`;
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers ?? {}),
    },
    ...options,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status} ${res.statusText}: ${text}`);
  }
  return (await res.json()) as T;
}

export const api = {
  health: () => request<{ status: string; version: string }>('/health'),
  listModels: () => request<ModelsResponse>('/models'),
  createMission: (req: CreateMissionRequest) =>
    request<MissionSummary>('/missions', { method: 'POST', body: JSON.stringify(req) }),
  listMissions: () => request<MissionSummary[]>('/missions'),
  getMission: (id: string) => request<MissionDetail>(`/missions/${id}`),
  getReplay: (id: string) => request<ReplayPayload>(`/missions/${id}/replay`),
  pauseMission: (id: string) =>
    request<MissionSummary>(`/missions/${id}/pause`, { method: 'POST' }),
  resumeMission: (id: string) =>
    request<MissionSummary>(`/missions/${id}/resume`, { method: 'POST' }),
  applyAction: (id: string, action: number) =>
    request<MissionSummary>(`/missions/${id}/action`, {
      method: 'POST',
      body: JSON.stringify({ action }),
    }),
  runExperiment: (req: RunExperimentRequest) =>
    request<RunExperimentResponse>('/experiments', { method: 'POST', body: JSON.stringify(req) }),
  runCounterfactual: (missionId: string, req: RunCounterfactualRequest) =>
    request<RunCounterfactualResponse>(`/counterfactual/${missionId}`, {
      method: 'POST',
      body: JSON.stringify(req),
    }),
  getFailureAnalysis: (missionId: string) =>
    request<AnalysisResponse>(`/analysis/${missionId}`),
};
