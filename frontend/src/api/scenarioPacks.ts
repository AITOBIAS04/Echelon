/**
 * Scenario Packs API Module
 *
 * Wire to backend scenario pack template endpoints:
 *   GET  /api/v1/scenario-pack-templates         — list templates
 *   GET  /api/v1/scenario-pack-templates/:id     — get template detail
 */

import { apiClient } from './client';
import type {
  ScenarioPackCreate,
  ScenarioPackResponse,
  ScenarioRunResponse,
  EpisodeTreeResponse,
  ForkReplayResponse,
  DerivedTheatreResponse,
  BranchProbabilitiesResponse,
} from '../types/scenarioPack';

export interface ScenarioPackTemplateSummary {
  id: string;
  name: string;
  family: string;
  description: string | null;
  template_status: 'RUNNABLE' | 'CATALOG_ONLY';
  checkpoint_count: number;
  fork_points_min: number;
  fork_points_max: number;
  is_seeded: boolean;
}

export interface TemplateListResponse {
  templates: ScenarioPackTemplateSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface ScenarioPackTemplateDetail extends ScenarioPackTemplateSummary {
  fantasy: string | null;
  training_primitives: string | null;
  objective_vector: Array<{ component: string; weight: number; description: string }>;
  fork_points: Array<{ trigger: string; marketQuestion: string; options: string[]; decisionWindowSec: number }>;
  saboteur_deck: Array<{ card: string; price: number; boundedEffect: number; notes: string }>;
  episode_length_sec: number | null;
  checkpoints: Array<{
    id: string;
    sequence_num: number;
    trigger: string;
    market_question: string;
    decision_window_sec: number;
    can_spawn_theatre: boolean;
    evaluator_type: string;
    branch_count: number;
  }>;
  created_at: string;
}

export const scenarioPackApi = {
  listTemplates: async (params?: {
    family?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<TemplateListResponse> => {
    const { data } = await apiClient.get('/api/v1/scenario-pack-templates', { params });
    return data;
  },

  getTemplate: async (templateId: string): Promise<ScenarioPackTemplateDetail> => {
    const { data } = await apiClient.get(`/api/v1/scenario-pack-templates/${templateId}`);
    return data;
  },

};

// ── Pack Lifecycle ─────────────────────────────────────────────────────────

export const scenarioPackLifecycleApi = {
  createPack: async (req: ScenarioPackCreate): Promise<ScenarioPackResponse> => {
    const { data } = await apiClient.post('/api/v1/scenario-packs', req);
    return data;
  },

  getPack: async (packId: string): Promise<ScenarioPackResponse> => {
    const { data } = await apiClient.get(`/api/v1/scenario-packs/${packId}`);
    return data;
  },

  commitPack: async (packId: string): Promise<ScenarioPackResponse> => {
    const { data } = await apiClient.post(`/api/v1/scenario-packs/${packId}/commit`);
    return data;
  },

  startRun: async (packId: string): Promise<ScenarioRunResponse> => {
    const { data } = await apiClient.post(`/api/v1/scenario-packs/${packId}/run`);
    return data;
  },

  getRunTree: async (packId: string, runId: string): Promise<EpisodeTreeResponse> => {
    const { data } = await apiClient.get(
      `/api/v1/scenario-packs/${packId}/runs/${runId}/tree`,
    );
    return data;
  },

  getReplay: async (packId: string, runId: string): Promise<ForkReplayResponse> => {
    const { data } = await apiClient.get(
      `/api/v1/scenario-packs/${packId}/runs/${runId}/replay`,
    );
    return data;
  },

  getDerivedTheatres: async (packId: string): Promise<DerivedTheatreResponse[]> => {
    const { data } = await apiClient.get(`/api/v1/scenario-packs/${packId}/derived-theatres`);
    return data;
  },

  getBranchProbabilities: async (templateId: string): Promise<BranchProbabilitiesResponse> => {
    const { data } = await apiClient.get(
      `/api/v1/scenario-pack-templates/${templateId}/branch-probabilities`,
    );
    return data;
  },
};
