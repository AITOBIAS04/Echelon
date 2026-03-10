/**
 * Blackbox / Analytics Hooks — Wired to real backend APIs
 *
 * Provides agent leaderboard from real data. Chart data uses
 * timeline health API for market prices. Intercepts and time sales
 * return empty — marked as "Coming Soon" in the UI.
 */

import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import type {
  Agent,
  Candle,
  ChartIndicators,
  Trade,
  Intercept,
  Timeframe,
} from '../types/blackbox';
import type { Timeline, TimelineHealthResponse } from '../types';

// ── Agent Leaderboard — Real API ────────────────────────────────────────

interface BackendAgent {
  id: string;
  name: string;
  archetype: string;
  total_pnl_usd: number;
  win_rate: number;
  trades_count: number;
  is_alive: boolean;
}

function backendToBlackboxAgent(a: BackendAgent): Agent {
  return {
    id: a.id,
    name: a.name,
    archetype: a.archetype.toLowerCase() as Agent['archetype'],
    pnl: a.total_pnl_usd,
    pnlDisplay: `${a.total_pnl_usd >= 0 ? '+' : ''}${Math.round(a.total_pnl_usd).toLocaleString()}`,
    winRate: Math.round(a.win_rate * 100),
    sharpe: 0, // Not available from API
    trades: a.trades_count,
    volume: 0,
    volumeDisplay: '--',
    status: a.is_alive ? 'Active' : 'Inactive',
  };
}

export function useAgentLeaderboard() {
  const [searchQuery, setSearchQuery] = useState('');

  const { data: resp } = useQuery({
    queryKey: ['agents', 'leaderboard'],
    queryFn: async () => {
      const { data } = await apiClient.get<{ agents: BackendAgent[] }>(
        '/api/v1/agents/',
        { params: { is_alive: true, limit: 20 } },
      );
      return data;
    },
    refetchInterval: 30_000,
  });

  const agents = useMemo(() => {
    const all = (resp?.agents ?? []).map(backendToBlackboxAgent);
    const filtered = searchQuery
      ? all.filter((a) => a.name.toLowerCase().includes(searchQuery.toLowerCase()))
      : all;
    return [...filtered].sort((a, b) => b.pnl - a.pnl);
  }, [resp, searchQuery]);

  return { agents, searchQuery, setSearchQuery };
}

// ── Chart Data — From Timeline Health ───────────────────────────────────

function timelinesToCandles(timelines: Timeline[]): Candle[] {
  // Build simple price candles from timeline stability snapshots
  if (timelines.length === 0) return [];

  const now = Date.now();
  const interval = 15 * 60 * 1000;

  return timelines.slice(0, 30).map((t, i) => {
    const price = t.price_yes;
    return {
      timestamp: now - (30 - i) * interval,
      open: price - 0.01,
      high: price + 0.02,
      low: price - 0.02,
      close: price,
      volume: Math.round(t.total_volume_usd),
    };
  });
}

export function useBlackboxChart(_timeframe: Timeframe) {
  const { data: resp } = useQuery({
    queryKey: ['butterfly', 'timelines', 'health', 'chart'],
    queryFn: async () => {
      const { data } = await apiClient.get<TimelineHealthResponse>(
        '/api/v1/butterfly/timelines/health',
      );
      return data;
    },
    refetchInterval: 15_000,
  });

  const timelines = resp?.timelines ?? [];
  const candles = useMemo(() => timelinesToCandles(timelines), [timelines]);

  const currentPrice = timelines.length > 0 ? timelines[0].price_yes : 0.5;

  const indicators: ChartIndicators = {
    rsi: 50,
    macd: 0,
    macdSignal: 0,
    macdHist: 0,
    volume: candles.length > 0 ? candles[candles.length - 1]?.volume ?? 0 : 0,
    high: candles.length > 0 ? Math.max(...candles.map((c) => c.high)) : 1,
    low: candles.length > 0 ? Math.min(...candles.map((c) => c.low)) : 0,
  };

  return { candles, currentPrice, priceChange: 0, priceChangePercent: 0, indicators };
}

// ── Coming Soon — Empty hooks ───────────────────────────────────────────

export function useTimeSales(): Trade[] {
  // Time & sales not available from current API — Coming Soon
  return [];
}

export function useIntercepts(): Intercept[] {
  // Signal intercepts not available from current API — Coming Soon
  return [];
}

export function useOrderBook() {
  return null;
}

export function useTimelines() {
  return [];
}

export function useWarChest() {
  return [];
}

export function useBlackboxRibbon() {
  return [];
}

export function useSystemStatus() {
  return { latency: 0 };
}
