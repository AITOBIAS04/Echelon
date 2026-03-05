// Portfolio Types — Aligned with backend/schemas/user_schemas.py
// API response types use snake_case matching raw JSON from backend.

// ============================================
// USER POSITION (GET /api/v1/user/positions)
// ============================================

export interface UserPosition {
  timeline_id: string;
  timeline_name: string;
  side: 'YES' | 'NO';
  shards_held: number;
  average_entry_price: number;
  current_price: number;
  unrealised_pnl_usd: number;
  unrealised_pnl_percent: number;
  timeline_stability: number;
  has_active_paradox: boolean;
  hours_until_reaper: number | null;
  is_founder: boolean;
  founder_yield_earned_usd: number;
}

export interface UserPositionsResponse {
  positions: UserPosition[];
  total_value_usd: number;
  total_unrealised_pnl_usd: number;
  total_founder_yield_usd: number;
}

// ============================================
// PORTFOLIO SUMMARY (GET /api/v1/user/portfolio/summary)
// ============================================

export interface PortfolioSummary {
  total_value_usd: number;
  total_unrealised_pnl_usd: number;
  total_unrealised_pnl_percent: number;
  active_position_count: number;
  timelines_at_risk: number;
  total_founder_yield_earned_usd: number;
  active_founder_positions: number;
  highest_risk_timeline_id: string | null;
  highest_risk_timeline_name: string | null;
  highest_risk_stability: number | null;
}

// ============================================
// PRIVATE FORK (GET /api/v1/user/forks)
// ============================================

export interface PrivateFork {
  id: string;
  name: string;
  narrative: string;
  created_at: string;
  status: 'DRAFT' | 'RUNNING' | 'COMPLETE';
  stability: number;
  simulation_result: string | null;
  can_publish: boolean;
  publish_cost_echelon: number;
}

export interface PrivateForksResponse {
  forks: PrivateFork[];
  total_count: number;
  max_allowed: number;
}

// ============================================
// FRONTEND VIEW HELPERS
// ============================================

export type ChartTimeframe = '1D' | '7D' | '30D' | 'ALL';
export type PositionTab = 'positions' | 'foldovers';

export interface EquityDataPoint {
  date: string;
  value: number;
}
