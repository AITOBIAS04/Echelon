/**
 * Risk Types
 * ==========
 * 
 * TypeScript interfaces for position exposure, timeline risk state,
 * and portfolio risk analysis.
 */

/**
 * PositionExposure
 * 
 * Represents a user's position exposure in a specific timeline.
 */
export interface PositionExposure {
  /** Unique timeline identifier */
  timelineId: string;
  
  /** Position direction: YES or NO */
  direction: 'YES' | 'NO';
  
  /** Base currency value of the position (notional) */
  notional: number;
  
  /** Average entry price (optional) */
  avgPrice?: number;
  
  /** Current market price (optional) */
  currentPrice?: number;
}

/**
 * TimelineRiskState
 * 
 * Current risk metrics for a timeline.
 */
export interface TimelineRiskState {
  /** Unique timeline identifier */
  timelineId: string;
  
  /** Timeline stability score (0-100, where 100 = most stable) */
  stability: number;
  
  /** Logic gap percentage (0-100, where higher = more unstable) */
  logicGap: number;
  
  /** Entropy rate: decay per hour as a percentage (e.g., 1.0 = 1% per hour) */
  entropyRate: number;
  
  /** Paradox proximity score (0-100, where 100 = paradox imminent) */
  paradoxProximity: number;
  
  /** Number of sabotage attacks in the last 24 hours */
  sabotageHeat24h: number;
  
  /** Time until next fork in seconds (optional) */
  nextForkEtaSec?: number;
}

/**
 * Top Risk Entry
 * 
 * Represents a top risk timeline with its risk score and drivers.
 */
export interface TopRisk {
  /** Unique timeline identifier */
  timelineId: string;
  
  /** Human-readable label for the timeline */
  label: string;
  
  /** Risk score (0-100) */
  riskScore: number;
  
  /** Human-readable list of risk drivers */
  drivers: string[];
  
  /** Estimated loss if timeline collapses now (in base currency) */
  burnAtCollapse: number;
}

/**
 * PortfolioRiskSummary
 * 
 * Aggregated risk analysis for a portfolio of timeline positions.
 */
export interface PortfolioRiskSummary {
  /** ISO timestamp when this summary was computed */
  asOf: string;
  
  /** Total notional value across all positions */
  totalNotional: number;
  
  /** Net YES notional (sum of YES positions minus NO positions) */
  netYesNotional: number;
  
  /** Net NO notional (sum of NO positions minus YES positions) */
  netNoNotional: number;
  
  /** Composite risk index (0-100, where higher = more risky) */
  riskIndex: number;
  
  /** Fragility index (0-100, combining stability, entropy, and sabotage) */
  fragilityIndex: number;
  
  /** Belief divergence index (0-100, combining logic gap and paradox proximity) */
  beliefDivergenceIndex: number;
  
  /** Top 5 riskiest timelines by weighted risk score */
  topRisks: TopRisk[];
  
  /** Non-prescriptive recommendations (e.g., "consider reducing exposure to X") */
  recommendations: string[];
}
