/**
 * useTheatres — React Query hook for theatre listing.
 *
 * Note: There is no GET /api/v1/theatres (list) endpoint.
 * The theatre listing uses the butterfly timeline health API,
 * same as useMarketplace. This hook wraps the same data source
 * but exposes it with theatre-oriented naming.
 *
 * For individual theatre detail + mutations, see useTheatreDetail.
 */

import { useQuery } from '@tanstack/react-query';
import { butterflyApi } from '../api/butterfly';
import type { TimelineHealthResponse } from '../types';

export interface TheatreListFilters {
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  limit?: number;
}

export function useTheatres(filters?: TheatreListFilters) {
  const query = useQuery<TimelineHealthResponse>({
    queryKey: ['theatres', 'list', filters],
    queryFn: () =>
      butterflyApi.getTimelineHealth({
        sort_by: filters?.sortBy,
        sort_order: filters?.sortOrder,
        limit: filters?.limit,
      }),
    staleTime: 10_000,
    refetchInterval: 15_000,
    placeholderData: (prev) => prev,
  });

  return {
    theatres: query.data?.timelines ?? [],
    total: query.data?.total_count ?? 0,
    isLoading: query.isLoading,
    error: query.error,
    isEmpty: !query.isLoading && (query.data?.timelines?.length ?? 0) === 0,
  };
}
