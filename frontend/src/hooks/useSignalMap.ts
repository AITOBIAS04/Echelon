import { useQuery } from '@tanstack/react-query';
import { worldMonitorApi, type WorldMonitorHeatmapCell, type WorldMonitorSignal } from '../api/worldMonitor';

export interface SignalMapData {
  signals: WorldMonitorSignal[];
  totalSignals: number;
  heatmap: WorldMonitorHeatmapCell[];
  categoryCounts: Record<string, number>;
  sourceCounts: Record<string, number>;
  severityCounts: Record<string, number>;
  updatedAt: string | null;
  isLoading: boolean;
  error: Error | null;
  isSparse: boolean;
  isQuiet: boolean;
}

export function useSignalMap(): SignalMapData {
  const query = useQuery({
    queryKey: ['signal-map'],
    queryFn: () => worldMonitorApi.getLive(),
    staleTime: 10_000,
    refetchInterval: 15_000,
    placeholderData: (prev) => prev,
  });

  const signals = query.data?.signals ?? [];
  const heatmap = query.data?.convergence_cells ?? [];
  const totalSignals = query.data?.summary.active_signals ?? signals.length;

  return {
    signals,
    totalSignals,
    heatmap,
    categoryCounts: query.data?.category_counts ?? {},
    sourceCounts: query.data?.source_counts ?? {},
    severityCounts: query.data?.severity_counts ?? {},
    updatedAt: query.data?.updated_at ?? null,
    isLoading: query.isLoading,
    error: (query.error as Error | null) ?? null,
    isSparse: !query.isLoading && signals.length > 0 && signals.length < 6,
    isQuiet: !query.isLoading && signals.length === 0,
  };
}
