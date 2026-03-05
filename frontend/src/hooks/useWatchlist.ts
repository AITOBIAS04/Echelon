// Watchlist Hooks — Wired to real backend APIs
// GET /api/v1/user/watchlist → WatchlistResponse
// GET /api/v1/butterfly/timelines/health → TimelineHealthResponse (for enrichment)

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import type { WatchlistResponse, WatchlistFilter, WatchlistTimeline } from '../types/watchlist';
import type { Timeline, TimelineHealthResponse } from '../types';

// ============================================
// API FETCHERS
// ============================================

async function fetchWatchlist(): Promise<WatchlistResponse> {
  const { data } = await apiClient.get<WatchlistResponse>('/api/v1/user/watchlist');
  return data;
}

async function fetchTimelines(): Promise<TimelineHealthResponse> {
  const { data } = await apiClient.get<TimelineHealthResponse>('/api/v1/butterfly/timelines/health');
  return data;
}

// ============================================
// TRANSFORMERS — Timeline → WatchlistTimeline adapter
// ============================================

function timelineToWatchlistTimeline(t: Timeline, addedAt: string): WatchlistTimeline {
  const gapPct = t.logic_gap * 100;
  return {
    id: t.id,
    name: t.name,
    slug: t.name.toLowerCase().replace(/[^a-z0-9]+/g, '-'),
    yesPrice: t.price_yes,
    noPrice: t.price_no,
    stability: t.stability,
    stabilityTrend: 'flat',
    logicGap: gapPct,
    logicGapTrend: 'stable',
    paradoxProximity: t.has_active_paradox ? 90 : Math.min(99, gapPct * 1.5),
    entropyRate: 0,
    entropyHistory: [0, 0, 0, 0, 0],
    sabotageCount1h: 0,
    sabotageCount24h: 0,
    addedAt,
  };
}

// ============================================
// CLIENT-SIDE FILTERS
// ============================================

function matchesFilter(timeline: WatchlistTimeline, filter: WatchlistFilter): boolean {
  switch (filter) {
    case 'all':
      return true;
    case 'brittle':
      return timeline.logicGap >= 40 && timeline.logicGap < 60;
    case 'paradox-watch':
      return timeline.logicGap >= 60 || timeline.logicGapTrend === 'widening';
    case 'high-entropy':
      return timeline.entropyRate < -3;
    case 'under-attack':
      return timeline.sabotageCount1h >= 3;
    default:
      return true;
  }
}

export function getFilteredCount(
  timelines: WatchlistTimeline[],
  filter: WatchlistFilter,
): number {
  return timelines.filter((t) => matchesFilter(t, filter)).length;
}

// ============================================
// HOOKS — Real API
// ============================================

export function useWatchlist(filter: WatchlistFilter = 'all') {
  const watchlistQuery = useQuery({
    queryKey: ['user', 'watchlist'],
    queryFn: fetchWatchlist,
    refetchInterval: 30_000,
  });

  const timelinesQuery = useQuery({
    queryKey: ['butterfly', 'timelines', 'health'],
    queryFn: fetchTimelines,
    refetchInterval: 15_000,
  });

  const isLoading = watchlistQuery.isLoading || timelinesQuery.isLoading;
  const error = watchlistQuery.error || timelinesQuery.error;

  const data = useMemo(() => {
    const items = watchlistQuery.data?.items ?? [];
    const timelines = timelinesQuery.data?.timelines ?? [];

    const timelineMap = new Map<string, Timeline>();
    for (const t of timelines) {
      timelineMap.set(t.id, t);
    }

    const result: WatchlistTimeline[] = [];
    for (const item of items) {
      if (item.item_type !== 'TIMELINE') continue;
      const timeline = timelineMap.get(item.item_id);
      if (timeline) {
        result.push(timelineToWatchlistTimeline(timeline, item.added_at));
      }
    }

    return result.filter((t) => matchesFilter(t, filter));
  }, [watchlistQuery.data, timelinesQuery.data, filter]);

  return {
    data,
    isLoading,
    isError: !!error,
    error,
    refetch: watchlistQuery.refetch,
  };
}
