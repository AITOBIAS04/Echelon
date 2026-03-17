import { apiClient } from './client';

// ── Types ────────────────────────────────────────────────────────────

export interface OsintSignal {
  id: string;
  source_id: string;
  source_group: string;
  signal_type: string;
  geo_region: string | null;
  entity_ref: string | null;
  content_hash: string;
  normalised_data: Record<string, unknown>;
  investigation_id: string | null;
  collected_at: string;
}

export interface PaginatedSignalsResponse {
  signals: OsintSignal[];
  limit: number;
  offset: number;
}

export interface OsintHealthResponse {
  feeds_online: number;
  feeds_total: number;
  signal_latency_sec: number | null;
  escalation_queue_depth: number;
  replay_workers_active: number;
}

export interface SignalSummaryResponse {
  total_signals: number;
  by_source_group: Record<string, number>;
  counter_signals: number;
  certificate_candidates: number;
  convergence_cells: number;
}

export interface SignalQueryParams {
  source_group?: string;
  investigation_id?: string;
  since?: string;
  limit?: number;
  offset?: number;
}

// ── API ──────────────────────────────────────────────────────────────

export const osintApi = {
  async getSignals(params: SignalQueryParams = {}): Promise<PaginatedSignalsResponse> {
    const { data } = await apiClient.get('/api/v1/osint/signals', { params });
    return data;
  },

  async getHealth(): Promise<OsintHealthResponse> {
    const { data } = await apiClient.get('/api/v1/osint/health');
    return data;
  },

  async getSummary(): Promise<SignalSummaryResponse> {
    const { data } = await apiClient.get('/api/v1/osint/signals/summary');
    return data;
  },
};
