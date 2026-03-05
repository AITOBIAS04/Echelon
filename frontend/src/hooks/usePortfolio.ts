// Portfolio Hooks — Wired to real backend APIs
// GET /api/v1/user/positions → UserPositionsResponse
// GET /api/v1/user/portfolio/summary → PortfolioSummary

import { useState, useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import type {
  UserPositionsResponse,
  PortfolioSummary,
  ChartTimeframe,
  EquityDataPoint,
} from '../types/portfolio';

// ============================================
// API FETCHERS
// ============================================

async function fetchPositions(): Promise<UserPositionsResponse> {
  const { data } = await apiClient.get<UserPositionsResponse>('/api/v1/user/positions');
  return data;
}

async function fetchPortfolioSummary(): Promise<PortfolioSummary> {
  const { data } = await apiClient.get<PortfolioSummary>('/api/v1/user/portfolio/summary');
  return data;
}

// ============================================
// HOOKS — Real API
// ============================================

export function usePositions() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['user', 'positions'],
    queryFn: fetchPositions,
    refetchInterval: 30_000,
  });

  const positions = data?.positions ?? [];

  const totals = useMemo(() => {
    const totalNotional = positions.reduce((sum, p) => sum + (p.shards_held * p.current_price), 0);
    const totalPL = positions.reduce((sum, p) => sum + p.unrealised_pnl_usd, 0);
    const yesNotional = positions
      .filter(p => p.side === 'YES')
      .reduce((sum, p) => sum + (p.shards_held * p.current_price), 0);
    const noNotional = positions
      .filter(p => p.side === 'NO')
      .reduce((sum, p) => sum + (p.shards_held * p.current_price), 0);
    const winners = positions.filter(p => p.unrealised_pnl_usd > 0).length;
    const winRate = positions.length > 0 ? (winners / positions.length) * 100 : 0;

    return { totalNotional, totalPL, yesNotional, noNotional, winRate };
  }, [positions]);

  return { positions, totals, isLoading, error };
}

export function usePortfolioSummary() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['user', 'portfolio', 'summary'],
    queryFn: fetchPortfolioSummary,
    refetchInterval: 30_000,
  });

  return { summary: data ?? null, isLoading, error };
}

// ============================================
// HOOKS — Frontend helpers (no backend dependency)
// ============================================

export function useEquityChart() {
  const [timeframe, setTimeframe] = useState<ChartTimeframe>('30D');

  const data = useMemo<EquityDataPoint[]>(() => {
    // Placeholder until a real equity history endpoint exists
    return [];
  }, []);

  return { data, timeframe, setTimeframe };
}

export function usePortfolioStatus() {
  const [clock, setClock] = useState('--:--:-- UTC');

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setClock(now.toISOString().substring(11, 19) + ' UTC');
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  return { clock };
}
