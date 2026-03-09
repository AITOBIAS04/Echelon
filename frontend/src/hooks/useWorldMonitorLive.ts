import { useQuery } from '@tanstack/react-query';
import { worldMonitorApi, type WorldMonitorLiveResponse } from '../api/worldMonitor';

export function useWorldMonitorLive() {
  const query = useQuery<WorldMonitorLiveResponse>({
    queryKey: ['world-monitor-live'],
    queryFn: () => worldMonitorApi.getLive(),
    staleTime: 10_000,
    refetchInterval: 15_000,
    placeholderData: (prev) => prev,
  });

  return {
    data:
      query.data ?? {
        updated_at: new Date(0).toISOString(),
        summary: {
          updated_at: new Date(0).toISOString(),
          tension_index: 0,
          tension_level: 'unavailable',
          chaos_index: 0,
          active_missions: 0,
          active_agents: 0,
          active_signals: 0,
          critical_signals: 0,
          convergence_cells: 0,
        },
        category_counts: {},
        severity_counts: {},
        source_counts: {},
        signals: [],
        convergence_cells: [],
        missions: [],
        intel: [],
        live_feed: [],
      },
    isLoading: query.isLoading,
    error: query.error,
  };
}
