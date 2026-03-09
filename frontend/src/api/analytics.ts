import { apiClient } from './client';

export interface AnalyticsPoint {
  timestamp: string;
  value: number;
}

export interface AnalyticsComparison {
  current_period: number;
  previous_period: number;
  delta: number;
  change_pct: number | null;
}

export interface AnalyticsExplanationItem {
  id: string;
  kind: string;
  timestamp: string;
  title: string;
  summary: string;
  tone: string;
  provenance: string;
  theatre_id?: string | null;
  investigation_id?: string | null;
  certificate_id?: string | null;
  timeline_id?: string | null;
}

export interface PlatformAnalyticsCurrent {
  active_theatres: number;
  completed_theatres: number;
  active_investigations: number;
  ready_investigations: number;
  issued_certificates: number;
  active_paradoxes: number;
  active_signals: number;
  critical_signals: number;
  convergence_cells: number;
}

export interface PlatformAnalyticsResponse {
  updated_at: string;
  range: string;
  bucket_size: string;
  current: PlatformAnalyticsCurrent;
  timeseries: Record<string, AnalyticsPoint[]>;
  comparisons: Record<string, AnalyticsComparison>;
  explanations: Record<string, AnalyticsExplanationItem[]>;
}

export interface AnalyticsBreakdownsResponse {
  updated_at: string;
  applied_filters: Record<string, string>;
  signal_categories: Record<string, number>;
  signal_sources: Record<string, number>;
  signal_severities: Record<string, number>;
  theatre_states: Record<string, number>;
  theatre_families: Record<string, number>;
  theatre_inquiry_classes: Record<string, number>;
  investigation_statuses: Record<string, number>;
  investigation_classes: Record<string, number>;
  investigation_routing_decisions: Record<string, number>;
  theatre_routing_hints: Record<string, number>;
  theatre_gate_statuses: Record<string, number>;
  agent_archetypes: Record<string, number>;
}

export interface AnalyticsBreakdownFilters {
  signal_category?: string;
  signal_source?: string;
  theatre_inquiry_class?: string;
  theatre_family?: string;
  investigation_class?: string;
  agent_archetype?: string;
}

export interface RiskTrendResponse {
  updated_at: string;
  range: string;
  bucket_size: string;
  timeseries: Record<string, AnalyticsPoint[]>;
  comparisons: Record<string, AnalyticsComparison>;
  explanations: Record<string, AnalyticsExplanationItem[]>;
}

export interface PortfolioAnalyticsCurrent {
  total_notional: number;
  total_unrealised_pnl: number;
  position_count: number;
  winning_positions: number;
  losing_positions: number;
  at_risk_positions: number;
}

export interface PortfolioPositionSummary {
  timeline_id: string;
  timeline_name: string;
  side: string;
  current_price: number;
  average_entry_price: number;
  shards_held: number;
  notional: number;
  unrealised_pnl: number;
  has_active_paradox: boolean;
  logic_gap: number;
}

export interface PortfolioAnalyticsResponse {
  updated_at: string;
  range: string;
  history_status: string;
  current: PortfolioAnalyticsCurrent;
  top_positions: PortfolioPositionSummary[];
  timeseries: AnalyticsPoint[];
}

export const analyticsApi = {
  async getPlatform(
    range = '30d',
    params?: {
      bucket_date?: string;
      theatre_inquiry_class?: string;
      theatre_family?: string;
      investigation_class?: string;
      agent_archetype?: string;
    },
  ): Promise<PlatformAnalyticsResponse> {
    const { data } = await apiClient.get('/api/v1/analytics/platform', {
      params: { range, ...params },
    });
    return data;
  },

  async getBreakdowns(filters: AnalyticsBreakdownFilters = {}): Promise<AnalyticsBreakdownsResponse> {
    const { data } = await apiClient.get('/api/v1/analytics/breakdowns', {
      params: filters,
    });
    return data;
  },

  async getRiskTrend(
    range = '30d',
    params?: {
      bucket_date?: string;
      investigation_class?: string;
    },
  ): Promise<RiskTrendResponse> {
    const { data } = await apiClient.get('/api/v1/analytics/risk-trend', {
      params: { range, ...params },
    });
    return data;
  },

  async getPortfolio(range = '30d'): Promise<PortfolioAnalyticsResponse> {
    const { data } = await apiClient.get('/api/v1/analytics/portfolio', {
      params: { range },
    });
    return data;
  },
};
