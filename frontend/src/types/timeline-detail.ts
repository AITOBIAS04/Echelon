/**
 * Timeline Detail Types
 * ====================
 * 
 * TypeScript interfaces for the Timeline Detail page, including comprehensive
 * timeline state, health history, fork events, sabotage events, evidence ledger,
 * paradox status, and user position information.
 */

/**
 * TimelineDetail
 * 
 * Complete timeline information including current state, historical data,
 * related events, and user position (if applicable).
 */
export interface TimelineDetail {
  /** Unique timeline identifier */
  id: string;
  
  /** Human-readable timeline name */
  name: string;
  
  /** URL-friendly slug */
  slug: string;
  
  /** Timeline description */
  description: string;
  
  /** ISO timestamp when timeline was created */
  createdAt: string;
  
  /** ISO timestamp when timeline expires */
  expiresAt: string;
  
  // Current state
  /** Current YES share price (0-1) */
  yesPrice: number;
  
  /** Current NO share price (0-1) */
  noPrice: number;
  
  /** Timeline stability score (0-100, where 100 = most stable) */
  stability: number;
  
  /** Logic gap percentage (0-100, where higher = more unstable) */
  logicGap: number;
  
  /** Entropy rate: decay per hour (negative value, e.g., -1.2) */
  entropyRate: number;
  
  // Time series (for charts)
  /** Historical health snapshots for charting */
  healthHistory: TimelineHealthSnapshot[];
  
  // Related data
  /** Fork events (timeline forks) */
  forkTape: ForkEvent[];
  
  /** Sabotage events (attacks on timeline) */
  sabotageHistory: SabotageEvent[];
  
  /** Evidence entries (OSINT data) */
  evidenceLedger: EvidenceEntry[];
  
  /** Paradox status (if paradox is active) */
  paradoxStatus: ParadoxStatus | null;
  
  // Position info (if user has position)
  /** User's position in this timeline (if any) */
  userPosition?: UserPosition;
}

/**
 * TimelineHealthSnapshot
 * 
 * Snapshot of timeline health metrics at a specific point in time.
 * Used for charting historical trends.
 */
export interface TimelineHealthSnapshot {
  /** ISO timestamp of the snapshot */
  timestamp: string;
  
  /** Stability score at this time */
  stability: number;
  
  /** Logic gap at this time */
  logicGap: number;
  
  /** Entropy rate at this time */
  entropyRate: number;
}

/**
 * ForkEvent
 * 
 * Represents a fork in the timeline (alternative outcome branch).
 */
export interface ForkEvent {
  /** Unique fork identifier */
  id: string;
  
  /** ISO timestamp when fork was created */
  timestamp: string;
  
  /** Current status of the fork */
  status: 'open' | 'repricing' | 'locked' | 'executing' | 'settled';
  
  /** Question posed by the fork */
  question: string;
  
  /** Available options in the fork */
  options: ForkOption[];
  
  /** ISO timestamp when fork was locked (optional) */
  lockedAt?: string;
  
  /** ISO timestamp when fork was settled (optional) */
  settledAt?: string;
  
  /** Outcome that was settled (optional) */
  settledOutcome?: string;
}

/**
 * ForkOption
 * 
 * An option within a fork event.
 */
export interface ForkOption {
  /** Unique option identifier */
  id: string;
  
  /** Human-readable label for the option */
  label: string;
  
  /** Current price of this option (0-1) */
  price: number;
  
  /** Historical price data for charting */
  priceHistory: { timestamp: string; price: number }[];
}

/**
 * SabotageEvent
 * 
 * Represents a sabotage attack on the timeline.
 */
export interface SabotageEvent {
  /** Unique sabotage event identifier */
  id: string;
  
  /** ISO timestamp when sabotage was initiated */
  timestamp: string;
  
  /** Current phase of the sabotage */
  phase: 'disclosed' | 'committed' | 'executed' | 'slashed';
  
  /** ID of the saboteur agent */
  saboteurId: string;
  
  /** Name of the saboteur agent */
  saboteurName: string;
  
  /** Type of sabotage attack */
  sabotageType: string;
  
  /** Amount staked for the sabotage */
  stakeAmount: number;
  
  /** Effect size: stability impact (negative value) */
  effectSize: number;
  
  /** ISO timestamp when sabotage was disclosed */
  disclosedAt: string;
  
  /** ISO timestamp when sabotage was executed (optional) */
  executedAt?: string;
  
  /** Whether the saboteur was slashed */
  slashed: boolean;
}

/**
 * EvidenceEntry
 * 
 * Represents an evidence entry from OSINT sources.
 */
export interface EvidenceEntry {
  /** Unique evidence identifier */
  id: string;
  
  /** ISO timestamp when evidence was recorded */
  timestamp: string;
  
  /** Source of the evidence (e.g., "RavenPack", "Spire AIS", "X API") */
  source: string;
  
  /** Headline or summary of the evidence */
  headline: string;
  
  /** Sentiment of the evidence */
  sentiment: 'bullish' | 'bearish' | 'neutral';
  
  /** Confidence level (0-100) */
  confidence: number;
  
  /** Contradiction information (if this evidence conflicts with another) */
  contradiction?: {
    /** ID of the contradicting evidence */
    conflictsWith: string;
    
    /** Reason for the contradiction */
    reason: string;
  };
  
  /** Impact on Logic Gap (how much this moved the gap) */
  impactOnGap: number;
}

/**
 * ParadoxStatus
 * 
 * Represents the current paradox status of a timeline.
 */
export interface ParadoxStatus {
  /** Whether a paradox is currently active */
  active: boolean;
  
  /** ISO timestamp when paradox was spawned */
  spawnedAt: string;
  
  /** Severity classification */
  severity: 'CLASS_3_MODERATE' | 'CLASS_2_SEVERE' | 'CLASS_1_CRITICAL';
  
  /** What triggered the paradox */
  triggerReason: 'logic_gap' | 'stability' | 'both';
  
  /** Value that triggered the paradox */
  triggerValue: number;
  
  /** Seconds remaining until paradox resolves (if countdown active) */
  countdown: number;
  
  /** Cost to extract the paradox */
  extractionCost: {
    /** Cost in USDC */
    usdc: number;
    
    /** Cost in Echelon tokens */
    echelon: number;
    
    /** Sanity cost (agent sanity points) */
    sanityCost: number;
  };
  
  /** History of extraction attempts */
  extractionHistory: ExtractionAttempt[];
  
  /** ID of agent currently carrying the paradox (optional) */
  carrierAgentId?: string;
  
  /** Name of agent currently carrying the paradox (optional) */
  carrierAgentName?: string;
}

/**
 * ExtractionAttempt
 * 
 * Represents an attempt to extract a paradox from a timeline.
 */
export interface ExtractionAttempt {
  /** ISO timestamp of the attempt */
  timestamp: string;
  
  /** ID of the agent attempting extraction */
  agentId: string;
  
  /** Name of the agent attempting extraction */
  agentName: string;
  
  /** Whether the extraction was successful */
  success: boolean;
  
  /** Cost of the attempt */
  cost: number;
  
  /** Sanity cost of the attempt */
  sanityCost: number;
}

/**
 * UserPosition
 * 
 * Represents the user's position in a timeline (if they have one).
 */
export interface UserPosition {
  /** Side of the position */
  side: 'YES' | 'NO';
  
  /** Number of shares held */
  shares: number;
  
  /** Average purchase price */
  avgPrice: number;
  
  /** Current value of the position */
  currentValue: number;
  
  /** Unrealised profit/loss */
  unrealisedPnl: number;
  
  /** Amount that would be lost if timeline collapses */
  burnAtCollapse: number;
}
