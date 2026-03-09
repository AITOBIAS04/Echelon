import { apiClient } from './client';

export interface WorldMonitorGeoPoint {
  lat: number;
  lon: number;
}

export interface WorldMonitorSignal {
  id: string;
  title: string;
  description: string;
  source: string;
  category: string;
  region: string;
  level: number;
  confidence: number;
  severity: string;
  timestamp: string;
  expires_at: string;
  geo: WorldMonitorGeoPoint;
  correlated_signals: string[];
  theatre_ids: string[] | null;
  investigation_id: string | null;
  certificate_id: string | null;
  link_confidence: string | null;
  link_reason: string | null;
}

export interface WorldMonitorHeatmapCell {
  lat: number;
  lon: number;
  density: number;
  events: number;
  sources: string[];
  theatres: string[];
}

export interface WorldMonitorSummary {
  updated_at: string;
  tension_index: number;
  tension_level: string;
  chaos_index: number;
  active_missions: number;
  active_agents: number;
  active_signals: number;
  critical_signals: number;
  convergence_cells: number;
}

export interface WorldMonitorMission {
  id: string;
  title?: string;
  description?: string;
  category?: string;
  status?: string;
  reward_pool?: number;
  participants?: number;
  expires_at?: string | null;
}

export interface WorldMonitorIntelItem {
  id: string;
  title?: string;
  content?: string;
  source_agent?: string;
  source_type?: string;
  accuracy?: number;
}

export interface WorldMonitorLiveEvent {
  id: string;
  timestamp: string;
  event_type?: string;
  title: string;
  description: string;
  icon?: string;
  severity: string;
  market_impact?: string | null;
}

export interface WorldMonitorLiveResponse {
  updated_at: string;
  summary: WorldMonitorSummary;
  category_counts: Record<string, number>;
  severity_counts: Record<string, number>;
  source_counts: Record<string, number>;
  signals: WorldMonitorSignal[];
  convergence_cells: WorldMonitorHeatmapCell[];
  missions: WorldMonitorMission[];
  intel: WorldMonitorIntelItem[];
  live_feed: WorldMonitorLiveEvent[];
}

export const worldMonitorApi = {
  async getLive(): Promise<WorldMonitorLiveResponse> {
    const { data } = await apiClient.get('/api/v1/world-monitor/live');
    return data;
  },
};
