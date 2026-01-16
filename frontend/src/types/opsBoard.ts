/**
 * Operations Board Types
 * 
 * Types for the Operations Board feature, which provides a kanban-style
 * view of timelines and launches organized by operational status.
 */

/**
 * Operations lane identifiers
 */
export type OpsLaneId = 'new_creations' | 'about_to_happen' | 'at_risk' | 'graduation';

/**
 * Operations card type classification
 */
export type OpsCardType = 'timeline' | 'launch';

/**
 * Operations signal tags for highlighting important events or states
 */
export type OpsSignalTag =
  | 'fork_soon'
  | 'disclosure_active'
  | 'evidence_flip'
  | 'brittle'
  | 'paradox_active'
  | 'high_entropy'
  | 'sabotage_heat'
  | 'graduating';

/**
 * Operations card representing a timeline or launch in the ops board
 */
export interface OpsCard {
  /** Unique identifier for the card */
  id: string;
  
  /** Type of card (timeline or launch) */
  type: OpsCardType;
  
  /** Display title */
  title: string;
  
  /** Optional subtitle or description */
  subtitle?: string;
  
  /** Lane this card belongs to */
  lane: OpsLaneId;
  
  /** Signal tags indicating important states or events */
  tags: OpsSignalTag[];
  
  /** Stability metric (0-100, for timelines) */
  stability?: number;
  
  /** Logic gap percentage (0-100, for timelines) */
  logicGap?: number;
  
  /** Paradox proximity percentage (0-100, for timelines) */
  paradoxProximity?: number;
  
  /** Entropy rate (for timelines) */
  entropyRate?: number;
  
  /** Sabotage heat in last 24 hours (for timelines) */
  sabotageHeat24h?: number;
  
  /** Next fork ETA in seconds (for timelines) */
  nextForkEtaSec?: number;
  
  /** Quality score (0-100, for launches) */
  qualityScore?: number;
  
  /** Phase (for launches) */
  phase?: 'draft' | 'sandbox' | 'pilot' | 'graduated';
  
  /** Whether export eligible (for launches) */
  exportEligible?: boolean;
  
  /** ISO timestamp when card was created */
  createdAt: string;
  
  /** ISO timestamp when card was last updated */
  updatedAt: string;
}

/**
 * Live now summary metrics
 */
export interface LiveNowSummary {
  /** Number of forks currently live */
  forksLive: number;
  
  /** Number of active paradoxes */
  paradoxActive: number;
  
  /** Number of active breaches */
  breaches: number;
}

/**
 * Operations board data structure
 */
export interface OpsBoardData {
  /** Live now summary metrics */
  liveNow: LiveNowSummary;
  
  /** Cards organized by lane */
  lanes: Record<OpsLaneId, OpsCard[]>;
}
