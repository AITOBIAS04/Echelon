/**
 * Marketplace Types
 * 
 * Type definitions for the Marketplace page components:
 * - Market data structures
 * - Event types for live ribbon
 * - Signal intercepts from agents
 * - Breach alerts
 * - Alert management
 */

/**
 * Market/Card data structure
 */
export interface Market {
  id: string | number;
  category: MarketCategory;
  categoryIcon: string;
  categoryName: string;
  title: string;
  stability: number;
  stabilityStatus: 'Stable' | 'Degraded' | 'Critical';
  yesPrice: number;
  yesProb: number;
  noPrice: number;
  noProb: number;
  liquidity: number;
  nextForkEtaSec: number;
  gap: number;
  gapWarning?: boolean;
  gapDanger?: boolean;
  volume24h: number;
  tradesCount: number;
  agentLearnings: number;
  tags?: string[];
}

/**
 * Market categories
 */
export type MarketCategory = 'robotics' | 'logistics' | 'defi' | 'physics' | 'soceng';

/**
 * Live ribbon event
 */
export interface RibbonEvent {
  type: 'fork' | 'flip' | 'paradox' | 'sabotage' | 'settle' | 'wing';
  title: string;
  time: string;
  theatre?: string;
}

/**
 * Agent signal intercept
 */
export interface Intercept {
  id?: string;
  agent: string;
  agentIcon?: string;
  theatre: string;
  content: string;
  time: string;
  actions: ('Theatre' | 'Trade' | 'Shield' | 'Adjust' | 'Verify' | 'Monitor')[];
  confidence?: number;
  source?: string;
}

/**
 * Breach alert
 */
export interface Breach {
  id?: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  category: string;
  title: string;
  time: string;
  theatre?: string;
  description?: string;
  status?: 'active' | 'resolved' | 'investigating';
}

/**
 * Alert for notification system
 */
export interface Alert {
  id: string;
  type: 'price' | 'stability' | 'gap' | 'volume' | 'paradox';
  icon: string;
  title: string;
  description: string;
  theatre: string;
  condition: string;
  status: 'triggered' | 'active' | 'resolved' | 'paused';
  unread: boolean;
  time: string;
  severity?: 'critical' | 'warning' | 'info' | 'success';
}

/**
 * Comparison slot data
 */
export interface CompareSlot {
  id: string;
  name: string;
  price: number;
  change: string;
  stability: number;
  gap: number;
  volume: string;
  probability: number;
  forkIn: string;
}

/**
 * User position/bet
 */
export interface UserPosition {
  id: string;
  marketId: string;
  marketTitle: string;
  outcome: 'YES' | 'NO';
  amount: number;
  avgPrice: number;
  currentPrice: number;
  potentialPayout: number;
  unrealizedPnL: number;
  timestamp: string;
}

/**
 * Betting form data
 */
export interface BetFormData {
  marketId: string | number;
  outcome: 'YES' | 'NO';
  amount: number;
  slippageTolerance?: number;
}

/**
 * Filter state for market list
 */
export interface MarketFilterState {
  category: MarketCategory | 'all';
  searchQuery: string;
  sortBy: 'activity' | 'volume' | 'newest' | 'instability';
  minLiquidity?: number;
  maxGap?: number;
  showOnlyTrending?: boolean;
}

/**
 * Sort options
 */
export type SortOption = 'activity' | 'volume' | 'newest' | 'instability';

/**
 * Pagination state
 */
export interface PaginationState {
  page: number;
  pageSize: number;
  hasMore: boolean;
  totalCount: number;
}

/**
 * RLMF Training Data
 */
export interface RLMFTrainingData {
  totalTrades: number;
  agentLearnings: number;
  lastUpdated: string;
  trainingEfficiency: number;
}

/**
 * Market statistics
 */
export interface MarketStats {
  totalMarkets: number;
  activeMarkets: number;
  totalVolume24h: number;
  totalLiquidity: number;
  activeForks: number;
  activeBreaches: number;
}

/**
 * Create alert form data
 */
export interface CreateAlertForm {
  theatre: string;
  type: Alert['type'];
  conditionField: string;
  conditionValue: string;
  conditionOperator: '>' | '<' | '>=' | '<=' | '==';
}
