// Marketplace Types — Aligned with backend/schemas/butterfly_schemas.py
// The frontend "Market" is a view over TimelineHealth from the backend.
// API response types use snake_case matching raw JSON from backend.
// TimelineHealth is the canonical API type (defined in index.ts as Timeline).

// ============================================
// MARKET CATEGORY (frontend-only presentation)
// ============================================

export type MarketCategory = 'robotics' | 'logistics' | 'defi' | 'physics' | 'soceng';

// ============================================
// RIBBON / FEED EVENTS
// ============================================

export interface RibbonEvent {
  type: 'fork' | 'flip' | 'paradox' | 'sabotage' | 'settle' | 'wing';
  title: string;
  time: string;
  theatre?: string;
}

// ============================================
// MARKET FILTER / SORT (frontend state)
// ============================================

export type SortOption = 'activity' | 'volume' | 'newest' | 'instability';

export interface MarketFilterState {
  category: MarketCategory | 'all';
  searchQuery: string;
  sortBy: SortOption;
  minLiquidity?: number;
  maxGap?: number;
  showOnlyTrending?: boolean;
}

export interface PaginationState {
  page: number;
  pageSize: number;
  hasMore: boolean;
  totalCount: number;
}

// ============================================
// MARKET STATS (derived from TimelineHealthResponse)
// ============================================

export interface MarketStats {
  totalMarkets: number;
  activeMarkets: number;
  totalVolume24h: number;
  totalLiquidity: number;
  activeForks: number;
  activeBreaches: number;
}

// ============================================
// COMPARISON (frontend-only)
// ============================================

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

// ============================================
// BETTING (frontend → backend)
// ============================================

export interface BetFormData {
  marketId: string;
  outcome: 'YES' | 'NO';
  amount: number;
  slippageTolerance?: number;
}

// ============================================
// LEGACY TYPES — Used by mock hooks, will be removed in tasks 1.3-1.5
// ============================================

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
  net_inflow_24h?: number;
  net_inflow_7d?: number;
}

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

export interface Alert {
  id: string;
  type: 'price' | 'stability' | 'gap' | 'volume' | 'paradox';
  icon?: string;
  title: string;
  description: string;
  theatre: string;
  condition: string;
  status: 'triggered' | 'active' | 'resolved' | 'paused';
  unread: boolean;
  time: string;
  severity?: 'critical' | 'warning' | 'info' | 'success';
}

export interface CreateAlertForm {
  theatre: string;
  type: Alert['type'];
  conditionField: string;
  conditionValue: string;
  conditionOperator: '>' | '<' | '>=' | '<=' | '==';
}

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

export interface RLMFTrainingData {
  totalTrades: number;
  agentLearnings: number;
  lastUpdated: string;
  trainingEfficiency: number;
}
