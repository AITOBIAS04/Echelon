/**
 * Presets Types
 * =============
 * 
 * TypeScript interfaces and types for watchlist presets, filters, sorting,
 * and alert rules.
 */

/**
 * WatchlistSortKey
 * 
 * Available sort keys for watchlist timelines.
 */
export type WatchlistSortKey =
  | 'stability'
  | 'logic_gap'
  | 'paradox_proximity'
  | 'entropy_rate'
  | 'sabotage_heat'
  | 'next_fork_eta';

/**
 * WatchlistSortDir
 * 
 * Sort direction for watchlist timelines.
 */
export type WatchlistSortDir = 'asc' | 'desc';

/**
 * WatchlistFilterConfig
 * 
 * Filter criteria configuration for watchlist timelines.
 */
export interface WatchlistFilterConfig {
  /** Text search query for timeline names or IDs */
  query?: string;
  
  /** Minimum stability threshold (0-100) */
  minStability?: number;
  
  /** Maximum stability threshold (0-100) */
  maxStability?: number;
  
  /** Minimum logic gap threshold (0-100) */
  minLogicGap?: number;
  
  /** Maximum logic gap threshold (0-100) */
  maxLogicGap?: number;
  
  /** Show only timelines with active paradox */
  paradoxOnly?: boolean;
  
  /** Show only brittle timelines (logic gap 40-60) */
  brittleOnly?: boolean;
  
  /** Minimum sabotage heat (e.g., minimum attacks in last 24h) */
  sabotageHeatMin?: number;
  
  /** Maximum time until next fork (in seconds) */
  maxNextForkEtaSec?: number;
  
  /** Filter by timeline tags */
  tags?: string[];
}

/**
 * AlertRule
 * 
 * Alert rule configuration for watchlist monitoring.
 */
export interface AlertRule {
  /** Unique identifier for the alert rule */
  id: string;
  
  /** Human-readable name for the alert rule */
  name: string;
  
  /** Whether the alert rule is currently enabled */
  enabled: boolean;
  
  /** Severity level of the alert */
  severity: 'info' | 'warn' | 'critical';
  
  /** Alert condition configuration */
  condition: {
    /** Type of condition to evaluate */
    type: 'threshold' | 'rate_of_change' | 'event';
    
    /** Metric to monitor (for threshold and rate_of_change types) */
    metric?: 'stability' | 'logic_gap' | 'entropy_rate' | 'sabotage_heat' | 'paradox_proximity';
    
    /** Comparison operator (for threshold type) */
    op?: '>' | '>=' | '<' | '<=';
    
    /** Threshold or target value */
    value?: number;
    
    /** Time window in minutes (for rate_of_change type) */
    windowMinutes?: number;
    
    /** Event type to monitor (for event type) */
    eventType?: 'sabotage_disclosed' | 'paradox_spawn' | 'evidence_flip' | 'fork_live';
  };
  
  /** Scope of the alert rule */
  scope: {
    /** Scope type: all timelines, watchlist only, or specific timeline */
    scopeType: 'all' | 'watchlist' | 'timeline';
    
    /** Timeline ID (required if scopeType is 'timeline') */
    timelineId?: string;
  };
}

/**
 * WatchlistSavedView
 * 
 * Saved watchlist view configuration with filters, sorting, and alert rules.
 */
export interface WatchlistSavedView {
  /** Unique identifier for the saved view */
  id: string;
  
  /** Human-readable name for the saved view */
  name: string;
  
  /** ISO timestamp when the view was created */
  createdAt: string;
  
  /** ISO timestamp when the view was last updated */
  updatedAt: string;
  
  /** Sort configuration */
  sort: {
    /** Sort key */
    key: WatchlistSortKey;
    
    /** Sort direction */
    dir: WatchlistSortDir;
  };
  
  /** Filter configuration */
  filter: WatchlistFilterConfig;
  
  /** Alert rules associated with this view */
  alertRules: AlertRule[];
}
