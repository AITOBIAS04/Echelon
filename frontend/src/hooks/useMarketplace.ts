// Marketplace Hooks — Wired to real backend APIs
// GET /api/v1/butterfly/timelines/health → TimelineHealthResponse

import { useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import type { Market, RibbonEvent, Intercept, Breach } from '../types/marketplace';
import type { Timeline, TimelineHealthResponse, WingFlapFeedResponse } from '../types';

// ============================================
// API FETCHERS
// ============================================

async function fetchTimelines(): Promise<TimelineHealthResponse> {
  const { data } = await apiClient.get<TimelineHealthResponse>('/api/v1/butterfly/timelines/health');
  return data;
}

async function fetchRecentFlaps(): Promise<WingFlapFeedResponse> {
  const { data } = await apiClient.get<WingFlapFeedResponse>('/api/v1/butterfly/flaps', {
    params: { limit: 20 },
  });
  return data;
}

// ============================================
// TRANSFORMERS — Timeline → Market adapter
// ============================================

function getStabilityStatus(stability: number): 'Stable' | 'Degraded' | 'Critical' {
  if (stability >= 70) return 'Stable';
  if (stability >= 30) return 'Degraded';
  return 'Critical';
}

function timelineToMarket(t: Timeline): Market {
  return {
    id: t.id,
    category: 'defi',
    categoryIcon: '',
    categoryName: 'Market',
    title: t.name,
    stability: t.stability,
    stabilityStatus: getStabilityStatus(t.stability),
    yesPrice: t.price_yes,
    yesProb: Math.round(t.price_yes * 100),
    noPrice: t.price_no,
    noProb: Math.round(t.price_no * 100),
    liquidity: t.liquidity_depth_usd,
    nextForkEtaSec: 0,
    gap: t.logic_gap * 100,
    gapWarning: t.logic_gap >= 0.3,
    gapDanger: t.logic_gap >= 0.5,
    volume24h: t.total_volume_usd,
    tradesCount: t.active_agent_count,
    agentLearnings: 0,
  };
}

// ============================================
// HOOKS — Real API
// ============================================

export function useMarketData() {
  const { data: resp, isLoading, error } = useQuery({
    queryKey: ['butterfly', 'timelines', 'health'],
    queryFn: fetchTimelines,
    refetchInterval: 15_000,
  });

  const data = (resp?.timelines ?? []).map(timelineToMarket);

  return { data, isLoading, error: error ?? null };
}

export function useRibbonEvents() {
  const { data: resp, isLoading } = useQuery({
    queryKey: ['butterfly', 'flaps', 'recent'],
    queryFn: fetchRecentFlaps,
    refetchInterval: 10_000,
  });

  const data: RibbonEvent[] = (resp?.flaps ?? []).slice(0, 8).map((flap) => ({
    type: flap.flap_type === 'RIPPLE' ? 'fork' as const
      : flap.flap_type === 'PARADOX' ? 'paradox' as const
      : flap.flap_type === 'SABOTAGE' ? 'sabotage' as const
      : 'wing' as const,
    title: flap.action,
    time: formatTimeAgo(flap.timestamp),
    theatre: flap.timeline_name,
  }));

  return { data, isLoading };
}

export function useIntercepts() {
  // No backend endpoint for agent signal intercepts yet — return empty
  return { data: [] as Intercept[], isLoading: false };
}

export function useBreaches() {
  // Breach feed is covered by Paradox API (wired in task 1.5)
  return { data: [] as Breach[], isLoading: false };
}

export function useMarketUpdates(_marketId: string | number) {
  // Real-time updates will use WebSocket in sprint 5
  return null;
}

export function useBetting() {
  const [isBetting, setIsBetting] = useState(false);
  const [betError, setBetError] = useState<string | null>(null);

  const placeBet = useCallback(async (
    _marketId: string | number,
    _outcome: 'YES' | 'NO',
    _amount: number
  ) => {
    setIsBetting(true);
    setBetError(null);
    try {
      // TODO: Wire to real LMSR trade endpoint
      setBetError('Trading not yet connected');
      return { success: false, error: 'Trading not yet connected' };
    } finally {
      setIsBetting(false);
    }
  }, []);

  return { placeBet, isBetting, betError };
}

export function useMarketStats() {
  const { data: resp } = useQuery({
    queryKey: ['butterfly', 'timelines', 'health'],
    queryFn: fetchTimelines,
    refetchInterval: 30_000,
  });

  const timelines = resp?.timelines ?? [];
  return {
    totalMarkets: timelines.length,
    activeMarkets: timelines.length,
    totalVolume24h: timelines.reduce((sum, t) => sum + t.total_volume_usd, 0),
    activeForks: timelines.filter(t => t.connected_timeline_ids.length > 0).length,
    activeBreaches: timelines.filter(t => t.has_active_paradox).length,
  };
}

// ============================================
// HELPERS
// ============================================

function formatTimeAgo(isoTimestamp: string): string {
  const diff = Date.now() - new Date(isoTimestamp).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return 'now';
  if (mins < 60) return `${mins}m`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h`;
  return `${Math.floor(hours / 24)}d`;
}
