/**
 * useOpsBoard — Aggregation dashboard hook
 *
 * Fetches real data from multiple endpoints via the ops dashboard API.
 * Auto-refreshes every 15 seconds.
 */

import { useQuery } from '@tanstack/react-query';
import { fetchOpsDashboard } from '../api/opsBoard';
import type { OpsDashboardData } from '../api/opsBoard';

export type { OpsDashboardData };

export function useOpsBoard() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['opsDashboard'],
    queryFn: fetchOpsDashboard,
    staleTime: 10_000,
    refetchInterval: 15_000,
  });

  return {
    data: data ?? null,
    loading: isLoading,
    error: error?.message ?? null,
    refresh: refetch,
  };
}
