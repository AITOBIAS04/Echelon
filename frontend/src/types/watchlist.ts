// Watchlist Types — Aligned with backend/schemas/user_schemas.py
// API response types use snake_case matching raw JSON from backend.

// ============================================
// WATCHLIST ITEM (GET /api/v1/user/watchlist)
// ============================================

export type WatchlistItemType = 'AGENT' | 'TIMELINE';

export interface WatchlistItem {
  id: string;
  item_type: WatchlistItemType;
  item_id: string;
  item_name: string;
  added_at: string;
  current_stability: number | null;
  current_sanity: number | null;
  recent_activity: string | null;
}

export interface WatchlistAddRequest {
  item_type: WatchlistItemType;
  item_id: string;
}

export interface WatchlistResponse {
  items: WatchlistItem[];
  total_count: number;
  max_allowed: number;
}

// ============================================
// FRONTEND VIEW HELPERS
// ============================================

export type WatchlistFilter =
  | 'all'
  | 'timelines'
  | 'agents'
  | 'at-risk'
  // Legacy filter values used by Watchlist component UI
  | 'brittle'
  | 'paradox-watch'
  | 'high-entropy'
  | 'under-attack';

export interface WatchlistState {
  items: WatchlistItem[];
  activeFilter: WatchlistFilter;
  sortBy: keyof WatchlistItem;
  sortOrder: 'asc' | 'desc';
}

// ============================================
// LEGACY TYPE — Used by mock hooks, will be removed in task 1.6
// ============================================

export interface WatchlistTimeline {
  id: string;
  name: string;
  slug: string;
  yesPrice: number;
  noPrice: number;
  stability: number;
  stabilityTrend: 'up' | 'down' | 'flat';
  logicGap: number;
  logicGapTrend: 'widening' | 'narrowing' | 'stable';
  paradoxProximity: number;
  entropyRate: number;
  entropyHistory: number[];
  sabotageCount1h: number;
  sabotageCount24h: number;
  addedAt: string;
}
