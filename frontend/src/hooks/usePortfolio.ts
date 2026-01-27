// Portfolio Hooks
// React hooks for Portfolio data management

import { useState, useEffect, useMemo } from 'react';
import type {
  Position,
  RiskMetric,
  AllocationItem,
  EquityDataPoint,
  EquityStats,
  CorrelationData,
  RiskItem,
  Recommendation,
  GhostFork,
  PortfolioAgent,
  ForkDetail,
  YieldBreakdown,
  ChartTimeframe,
} from '../types/portfolio';

// Mock data for positions
const mockPositions: Position[] = [
  { id: '1', timelineId: 'TL-2847', direction: 'YES', entryPrice: 0.42, currentPrice: 0.58, size: 21050, pnl: 8420, pnlPercent: 38.1 },
  { id: '2', timelineId: 'TL-2846', direction: 'NO', entryPrice: 0.61, currentPrice: 0.55, size: 8550, pnl: 4280, pnlPercent: 7.0 },
  { id: '3', timelineId: 'TL-2845', direction: 'YES', entryPrice: 0.33, currentPrice: 0.38, size: 7500, pnl: 2850, pnlPercent: 15.2 },
  { id: '4', timelineId: 'TL-2844', direction: 'NO', entryPrice: 0.72, currentPrice: 0.68, size: 4250, pnl: -1420, pnlPercent: -5.6 },
  { id: '5', timelineId: 'TL-2843', direction: 'YES', entryPrice: 0.25, currentPrice: 0.31, size: 13050, pnl: 4180, pnlPercent: 24.0 },
  { id: '6', timelineId: 'TL-2842', direction: 'NO', entryPrice: 0.45, currentPrice: 0.52, size: 6600, pnl: -2640, pnlPercent: -15.6 },
];

// Mock risk metrics
const mockRiskMetrics: RiskMetric[] = [
  { label: 'Volatility', value: 18.4, max: 100, level: 'low', icon: 'ri-dashboard-3-line' },
  { label: 'VaR (95%)', value: 32.4, max: 100, level: 'medium', icon: 'ri-bar-chart-box-line' },
  { label: 'Fragility Index', value: 45.2, max: 100, level: 'medium', icon: 'ri-trending-up-line' },
  { label: 'Belief Divergence', value: 28.1, max: 100, level: 'low', icon: 'ri-error-warning-line' },
];

// Mock allocation data
const mockAllocations: AllocationItem[] = [
  { timelineId: 'TL-2847', direction: 'YES', percent: 19.8 },
  { timelineId: 'TL-2846', direction: 'NO', percent: 14.8 },
  { timelineId: 'TL-2845', direction: 'YES', percent: 12.4 },
  { timelineId: 'TL-2844', direction: 'NO', percent: 11.2 },
  { timelineId: 'TL-2843', direction: 'YES', percent: 10.5 },
  { timelineId: 'TL-2842', direction: 'NO', percent: 9.8 },
];

// Mock equity curve data
function generateEquityData(timeframe: ChartTimeframe): EquityDataPoint[] {
  const days = timeframe === '1D' ? 1 : timeframe === '7D' ? 7 : timeframe === '30D' ? 30 : 90;
  const data: EquityDataPoint[] = [];
  let baseValue = 100000;

  for (let i = 0; i < days; i++) {
    const change = (Math.random() - 0.45) * 2000;
    baseValue += change;
    data.push({
      date: new Date(Date.now() - (days - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      value: baseValue,
    });
  }

  return data;
}

// Mock correlation data
const mockCorrelations: CorrelationData[] = [
  { timeline1: 'TL-2847', timeline2: 'TL-2846', value: 0.84, level: 'high' },
  { timeline1: 'TL-2847', timeline2: 'TL-2845', value: 0.52, level: 'medium' },
  { timeline1: 'TL-2847', timeline2: 'TL-2844', value: 0.31, level: 'low' },
  { timeline1: 'TL-2846', timeline2: 'TL-2845', value: 0.47, level: 'medium' },
  { timeline1: 'TL-2846', timeline2: 'TL-2844', value: 0.28, level: 'low' },
  { timeline1: 'TL-2845', timeline2: 'TL-2844', value: 0.19, level: 'low' },
];

// Mock risk items
const mockRisks: RiskItem[] = [
  { timelineId: 'TL-2847', riskScore: 58.4, drivers: 'Entropy, Logic Gap', burnAtCollapse: 24850 },
  { timelineId: 'TL-2846', riskScore: 72.1, drivers: 'Sabotage, Instability', burnAtCollapse: 18420 },
  { timelineId: 'TL-2845', riskScore: 51.8, drivers: 'Paradox Proximity', burnAtCollapse: 12180 },
];

// Mock recommendations
const mockRecommendations: Recommendation[] = [
  { text: 'Consider reducing exposure to TL-2846 as sabotage heat increases' },
  { text: 'Diversify YES positions across more independent timelines' },
];

// Mock ghost forks
const mockGhostForks: GhostFork[] = [
  { id: 'TL-2847-fork-7', timeAgo: '2m ago' },
  { id: 'TL-2846-fork-3', timeAgo: '8m ago' },
  { id: 'TL-2845-fork-12', timeAgo: '15m ago' },
];

// Mock portfolio agents
const mockAgents: PortfolioAgent[] = [
  { id: '1', name: 'AGENT-A', archetype: 'WHALE', pnl: 8200, color: '#3B82F6', actions: 2847, winRate: 78, sanity: 85 },
  { id: '2', name: 'AGENT-B', archetype: 'SABOTEUR', pnl: -2400, color: '#8B5CF6', actions: 1456, winRate: 68, sanity: 52 },
  { id: '3', name: 'AGENT-C', archetype: 'DIPLOMAT', pnl: 4100, color: '#F59E0B', actions: 1234, winRate: 71, sanity: 92 },
  { id: '4', name: 'AGENT-D', archetype: 'SNIPER', pnl: 6800, color: '#10B981', actions: 892, winRate: 82, sanity: 78 },
  { id: '5', name: 'AGENT-E', archetype: 'HUNTER', pnl: 3500, color: '#EC4899', actions: 678, winRate: 75, sanity: 88 },
  { id: '6', name: 'AGENT-F', archetype: 'BUILDER', pnl: 5200, color: '#6366F1', actions: 1567, winRate: 79, sanity: 72 },
];

// Mock fork details
const mockForkDetails: ForkDetail[] = [
  { id: 'TL-2847-fork-7', timeAgo: '2m ago', probability: 72, forks: 7, volume: 124500 },
  { id: 'TL-2846-fork-3', timeAgo: '8m ago', probability: 58, forks: 3, volume: 89200 },
  { id: 'TL-2845-fork-12', timeAgo: '15m ago', probability: 45, forks: 12, volume: 67300 },
];

// Mock yield breakdown
const mockYieldBreakdown: YieldBreakdown = {
  trading: 4200,
  MEV: 2800,
  bribes: 1850,
  total: 8850,
};

// Hook for portfolio positions
export function usePositions() {
  const [positions] = useState<Position[]>(mockPositions);

  const totals = useMemo(() => {
    const totalNotional = positions.reduce((sum, p) => sum + p.size, 0);
    const totalPL = positions.reduce((sum, p) => sum + p.pnl, 0);
    const yesNotional = positions.filter(p => p.direction === 'YES').reduce((sum, p) => sum + p.size, 0);
    const noNotional = positions.filter(p => p.direction === 'NO').reduce((sum, p) => sum + p.size, 0);
    const winRate = positions.filter(p => p.pnl > 0).length / positions.length * 100;

    return { totalNotional, totalPL, yesNotional, noNotional, winRate };
  }, [positions]);

  return { positions, totals };
}

// Hook for risk metrics
export function useRiskMetrics() {
  return mockRiskMetrics;
}

// Hook for portfolio allocation
export function useAllocation() {
  const [allocations] = useState<AllocationItem[]>(mockAllocations);

  const totals = useMemo(() => {
    const yesTotal = allocations.filter(a => a.direction === 'YES').reduce((sum, a) => sum + a.percent, 0);
    const noTotal = allocations.filter(a => a.direction === 'NO').reduce((sum, a) => sum + a.percent, 0);
    return { yesTotal, noTotal };
  }, [allocations]);

  return { allocations, totals };
}

// Hook for equity chart
export function useEquityChart() {
  const [timeframe, setTimeframe] = useState<ChartTimeframe>('30D');
  const [data] = useState<EquityDataPoint[]>(() => generateEquityData('30D'));

  const stats = useMemo<EquityStats>(() => ({
    totalPL: 12450,
    returnPercent: 8.4,
    sharpeRatio: 2.1,
    maxDrawdown: -2850,
  }), []);

  return { data, timeframe, setTimeframe, stats };
}

// Hook for correlation matrix
export function useCorrelations() {
  return mockCorrelations;
}

// Hook for risk items
export function useRiskItems() {
  return mockRisks;
}

// Hook for recommendations
export function useRecommendations() {
  return mockRecommendations;
}

// Hook for ghost forks
export function useGhostForks() {
  return mockGhostForks;
}

// Hook for portfolio agents
export function usePortfolioAgents() {
  return mockAgents;
}

// Hook for fork details
export function useForkDetails() {
  return mockForkDetails;
}

// Hook for yield breakdown
export function useYieldBreakdown() {
  return mockYieldBreakdown;
}

// Hook for system status
export function usePortfolioStatus() {
  const [clock, setClock] = useState('--:--:-- UTC');
  const [latency] = useState(12);

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setClock(now.toISOString().substr(11, 8) + ' UTC');
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  return { clock, latency };
}
