/**
 * Watchlist Types
 * ===============
 * TypeScript interfaces for the enhanced Watchlist feature.
 * 
 * The Watchlist allows users to track timelines of interest with
 * enhanced metrics for stability, paradox proximity, and entropy tracking.
 */

/**
 * WatchlistTimeline
 * 
 * Represents a timeline that has been added to a user's watchlist,
 * with enhanced tracking metrics beyond the base Timeline interface.
 */
export interface WatchlistTimeline {
  /** Unique timeline identifier */
  id: string;
  
  /** Human-readable timeline name (e.g., "Ghost Tanker") */
  name: string;
  
  /** URL-friendly slug (e.g., "ghost-tanker") */
  slug: string;
  
  /** Current YES share price (0-1) */
  yesPrice: number;
  
  /** Current NO share price (0-1) */
  noPrice: number;
  
  /** Timeline stability score (0-100, where 100 = most stable) */
  stability: number;
  
  /** Direction of stability trend */
  stabilityTrend: 'up' | 'down' | 'flat';
  
  /** Logic gap percentage (0-100, where higher = more unstable) */
  logicGap: number;
  
  /** Direction of logic gap change */
  logicGapTrend: 'widening' | 'narrowing' | 'stable';
  
  /** Paradox proximity score (0-100, where 100 = paradox imminent) */
  paradoxProximity: number;
  
  /** Entropy rate: decay per hour (negative value, e.g., -1.2) */
  entropyRate: number;
  
  /** Historical entropy readings (last 6 hours) */
  entropyHistory: number[];
  
  /** Number of sabotage attacks in the last hour */
  sabotageCount1h: number;
  
  /** Number of sabotage attacks in the last 24 hours */
  sabotageCount24h: number;
  
  /** ISO timestamp when this timeline was added to watchlist */
  addedAt: string;
}

/**
 * WatchlistFilter
 * 
 * Filter options for viewing watchlist timelines by risk/status category.
 */
export type WatchlistFilter =
  | 'all'              // Show all timelines
  | 'brittle'          // Low stability, high logic gap
  | 'paradox-watch'    // High paradox proximity
  | 'high-entropy'     // Rapid decay rate
  | 'under-attack';    // Recent sabotage activity

/**
 * WatchlistState
 * 
 * Complete state of the watchlist including timelines, filters, and sorting.
 */
export interface WatchlistState {
  /** Array of timelines in the watchlist */
  timelines: WatchlistTimeline[];
  
  /** Currently active filter */
  activeFilter: WatchlistFilter;
  
  /** Field to sort by */
  sortBy: keyof WatchlistTimeline;
  
  /** Sort direction */
  sortOrder: 'asc' | 'desc';
}
