import { useQuery } from '@tanstack/react-query';
import {
  analyticsApi,
  type AnalyticsBreakdownFilters,
  type AnalyticsBreakdownsResponse,
  type PlatformAnalyticsResponse,
  type PortfolioAnalyticsResponse,
  type RiskTrendResponse,
} from '../api/analytics';

const EMPTY_PLATFORM: PlatformAnalyticsResponse = {
  updated_at: new Date(0).toISOString(),
  range: '30d',
  bucket_size: 'day',
  current: {
    active_theatres: 0,
    completed_theatres: 0,
    active_investigations: 0,
    ready_investigations: 0,
    issued_certificates: 0,
    active_paradoxes: 0,
    active_signals: 0,
    critical_signals: 0,
    convergence_cells: 0,
  },
  timeseries: {},
  comparisons: {},
  explanations: {},
};

const EMPTY_BREAKDOWNS: AnalyticsBreakdownsResponse = {
  updated_at: new Date(0).toISOString(),
  applied_filters: {},
  signal_categories: {},
  signal_sources: {},
  signal_severities: {},
  theatre_states: {},
  theatre_families: {},
  theatre_inquiry_classes: {},
  investigation_statuses: {},
  investigation_classes: {},
  investigation_routing_decisions: {},
  theatre_routing_hints: {},
  theatre_gate_statuses: {},
  agent_archetypes: {},
};

const EMPTY_RISK_TREND: RiskTrendResponse = {
  updated_at: new Date(0).toISOString(),
  range: '30d',
  bucket_size: 'day',
  timeseries: {},
  comparisons: {},
  explanations: {},
};

const EMPTY_PORTFOLIO: PortfolioAnalyticsResponse = {
  updated_at: new Date(0).toISOString(),
  range: '30d',
  history_status: 'current_snapshot_only',
  current: {
    total_notional: 0,
    total_unrealised_pnl: 0,
    position_count: 0,
    winning_positions: 0,
    losing_positions: 0,
    at_risk_positions: 0,
  },
  top_positions: [],
  timeseries: [],
};

export function usePlatformAnalytics(
  range = '30d',
  filters: AnalyticsBreakdownFilters = {},
  explanationBuckets: { platform?: string; risk?: string } = {},
) {
  const platform = useQuery<PlatformAnalyticsResponse>({
    queryKey: ['analytics', 'platform', range, explanationBuckets.platform, filters.theatre_inquiry_class, filters.theatre_family, filters.investigation_class, filters.agent_archetype],
    queryFn: () =>
      analyticsApi.getPlatform(range, {
        bucket_date: explanationBuckets.platform,
        theatre_inquiry_class: filters.theatre_inquiry_class,
        theatre_family: filters.theatre_family,
        investigation_class: filters.investigation_class,
        agent_archetype: filters.agent_archetype,
      }),
    staleTime: 10_000,
    refetchInterval: 15_000,
    placeholderData: (previous) => previous,
  });

  const breakdowns = useQuery<AnalyticsBreakdownsResponse>({
    queryKey: ['analytics', 'breakdowns', filters],
    queryFn: () => analyticsApi.getBreakdowns(filters),
    staleTime: 10_000,
    refetchInterval: 15_000,
    placeholderData: (previous) => previous,
  });

  const riskTrend = useQuery<RiskTrendResponse>({
    queryKey: ['analytics', 'risk-trend', range, explanationBuckets.risk, filters.investigation_class],
    queryFn: () =>
      analyticsApi.getRiskTrend(range, {
        bucket_date: explanationBuckets.risk,
        investigation_class: filters.investigation_class,
      }),
    staleTime: 10_000,
    refetchInterval: 15_000,
    placeholderData: (previous) => previous,
  });

  return {
    platform: platform.data ?? EMPTY_PLATFORM,
    breakdowns: breakdowns.data ?? EMPTY_BREAKDOWNS,
    riskTrend: riskTrend.data ?? EMPTY_RISK_TREND,
    isLoading: platform.isLoading || breakdowns.isLoading || riskTrend.isLoading,
    error: platform.error ?? breakdowns.error ?? riskTrend.error,
  };
}

export function usePortfolioAnalytics(range = '30d') {
  const query = useQuery<PortfolioAnalyticsResponse>({
    queryKey: ['analytics', 'portfolio', range],
    queryFn: () => analyticsApi.getPortfolio(range),
    staleTime: 10_000,
    refetchInterval: 15_000,
    placeholderData: (previous) => previous,
  });

  return {
    portfolio: query.data ?? EMPTY_PORTFOLIO,
    isLoading: query.isLoading,
    error: query.error,
  };
}
