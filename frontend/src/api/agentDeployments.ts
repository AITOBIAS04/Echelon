/**
 * Agent Deployments API Client
 *
 * Wire to backend agent deployment endpoints (Cycle 019):
 *   POST   /api/v1/agent-deployments              — create deployment
 *   GET    /api/v1/agent-deployments               — list deployments
 *   GET    /api/v1/agent-deployments/:id           — get deployment detail
 *   POST   /api/v1/agent-deployments/:id/withdraw  — withdraw deployment
 *   POST   /api/v1/agent-deployments/:id/pause     — pause deployment
 *   POST   /api/v1/agent-deployments/:id/resume    — resume deployment
 *   POST   /api/v1/agent-deployments/:id/strategy  — update strategy
 */

import { apiClient } from './client';
import type {
  AgentDeploymentCreate,
  AgentDeploymentResponse,
  DeploymentDetailResponse,
  DeploymentListResponse,
  StrategyUpdateRequest,
} from '../types/agentDeployment';

export const agentDeploymentApi = {
  create: async (req: AgentDeploymentCreate): Promise<AgentDeploymentResponse> => {
    const { data } = await apiClient.post('/api/v1/agent-deployments', req);
    return data;
  },

  list: async (params?: {
    agent_id?: string;
    theatre_id?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<DeploymentListResponse> => {
    const { data } = await apiClient.get('/api/v1/agent-deployments', { params });
    return data;
  },

  getDetail: async (deploymentId: string): Promise<DeploymentDetailResponse> => {
    const { data } = await apiClient.get(`/api/v1/agent-deployments/${deploymentId}`);
    return data;
  },

  withdraw: async (deploymentId: string): Promise<AgentDeploymentResponse> => {
    const { data } = await apiClient.post(`/api/v1/agent-deployments/${deploymentId}/withdraw`);
    return data;
  },

  pause: async (deploymentId: string): Promise<AgentDeploymentResponse> => {
    const { data } = await apiClient.post(`/api/v1/agent-deployments/${deploymentId}/pause`);
    return data;
  },

  resume: async (deploymentId: string): Promise<AgentDeploymentResponse> => {
    const { data } = await apiClient.post(`/api/v1/agent-deployments/${deploymentId}/resume`);
    return data;
  },

  updateStrategy: async (
    deploymentId: string,
    req: StrategyUpdateRequest,
  ): Promise<AgentDeploymentResponse> => {
    const { data } = await apiClient.post(
      `/api/v1/agent-deployments/${deploymentId}/strategy`,
      req,
    );
    return data;
  },
};
