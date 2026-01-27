// Portfolio Types
// Types for the Portfolio page

export type ChartTimeframe = '1D' | '7D' | '30D' | 'ALL';
export type PositionTab = 'positions' | 'foldovers';

export interface Position {
  id: string;
  timelineId: string;
  direction: 'YES' | 'NO';
  entryPrice: number;
  currentPrice: number;
  size: number;
  pnl: number;
  pnlPercent: number;
}

export interface RiskMetric {
  label: string;
  value: number;
  max: number;
  level: 'low' | 'medium' | 'high';
  icon: string;
}

export interface AllocationItem {
  timelineId: string;
  direction: 'YES' | 'NO';
  percent: number;
}

export interface EquityDataPoint {
  date: string;
  value: number;
}

export interface EquityStats {
  totalPL: number;
  returnPercent: number;
  sharpeRatio: number;
  maxDrawdown: number;
}

export interface CorrelationData {
  timeline1: string;
  timeline2: string;
  value: number;
  level: 'low' | 'medium' | 'high';
}

export interface RiskItem {
  timelineId: string;
  riskScore: number;
  drivers: string;
  burnAtCollapse: number;
}

export interface Recommendation {
  text: string;
}

export interface GhostFork {
  id: string;
  timeAgo: string;
}

export interface PortfolioAgent {
  id: string;
  name: string;
  archetype: string;
  pnl: number;
  color: string;
  actions: number;
  winRate: number;
  sanity: number;
}

export interface ForkDetail {
  id: string;
  timeAgo: string;
  probability: number;
  forks: number;
  volume: number;
}

export interface YieldBreakdown {
  trading: number;
 MEV: number;
  bribes: number;
  total: number;
}
