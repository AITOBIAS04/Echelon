import { apiClient } from './client';

export interface SituationRoomSignal {
  id: string;
  source: string;
  region: string;
  level: number;
  confidence: number;
  severity: string;
  description: string;
  timestamp: string;
  expires_at: string;
  correlated_signals: string[];
}

export interface SituationRoomState {
  tension_index: number;
  tension_level: string;
  peace_percentage: number;
  chaos_index: number;
  active_missions: number;
  active_agents: number;
  last_updated: string;
  recent_signals?: SituationRoomSignal[];
}

export interface SituationRoomMission {
  id: string;
  title: string;
  description: string;
  category: string;
  status: string;
  tension_impact: number;
  reward_pool: number;
  time_remaining: number | null;
  participants: number;
  created_at: string;
  mission_type?: string | null;
  base_reward_usdc?: number | null;
  codename?: string | null;
  difficulty?: number | null;
  expires_at?: string | null;
  duration_minutes?: number | null;
  assigned_agents?: string[];
  max_agents?: number | null;
  required_roles?: string[];
}

export interface SituationRoomIntel {
  id: string;
  title: string;
  content: string;
  source_agent: string;
  source_type: string;
  accuracy: number;
  price: number;
  expires_at: string | null;
  purchased_by: string[];
}

export interface SituationRoomLiveEvent {
  id: string;
  timestamp: string;
  event_type: string;
  title: string;
  description: string;
  icon: string;
  severity: string;
  market_impact?: string | null;
}

export const situationRoomApi = {
  async getState(): Promise<SituationRoomState> {
    const { data } = await apiClient.get('/api/situation-room/state');
    return data;
  },

  async getMissions(): Promise<SituationRoomMission[]> {
    const { data } = await apiClient.get('/api/situation-room/missions');
    return data;
  },

  async getIntel(): Promise<SituationRoomIntel[]> {
    const { data } = await apiClient.get('/api/situation-room/intel');
    return data;
  },

  async getLiveFeed(limit = 20): Promise<SituationRoomLiveEvent[]> {
    const { data } = await apiClient.get('/api/situation-room/live-feed', {
      params: { limit },
    });
    return data;
  },
};
