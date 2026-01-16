/**
 * Breach Types
 * ============
 * 
 * TypeScript interfaces for the Breach detection and analysis system.
 * Breaches represent anomalies, attacks, or system failures that require
 * investigation and mitigation.
 */

/**
 * BreachSeverity
 * 
 * Severity level classification for breaches.
 */
export type BreachSeverity = 'low' | 'medium' | 'high' | 'critical';

/**
 * BreachCategory
 * 
 * Category classification for different types of breaches.
 */
export type BreachCategory =
  | 'logic_gap_spike'
  | 'sensor_contradiction'
  | 'sabotage_cluster'
  | 'oracle_flip'
  | 'stability_collapse'
  | 'paradox_detonation';

/**
 * Breach
 * 
 * Represents a detected breach in the system.
 */
export interface Breach {
  /** Unique breach identifier */
  id: string;

  /** ISO timestamp when breach was detected */
  timestamp: string;

  /** Severity level */
  severity: BreachSeverity;

  /** Category of breach */
  category: BreachCategory;

  /** Human-readable title */
  title: string;

  /** Detailed description */
  description: string;

  // Affected entities
  /** Timelines affected by this breach */
  affectedTimelines: AffectedTimeline[];

  /** Agents affected by this breach */
  affectedAgents: AffectedAgent[];

  // Analysis
  /** Root cause analysis */
  rootCause: string;

  /** Entities that benefited from this breach */
  beneficiaries: Beneficiary[];

  /** Evidence changes related to this breach */
  evidenceChanges: EvidenceChange[];

  // Status
  /** Current status of the breach */
  status: 'active' | 'investigating' | 'mitigated' | 'resolved';

  /** Whether the breach is recoverable */
  recoverable: boolean;

  /** Suggested actions to address the breach */
  suggestedActions: SuggestedAction[];

  // Resolution
  /** ISO timestamp when breach was resolved (optional) */
  resolvedAt?: string;

  /** Notes about resolution (optional) */
  resolutionNotes?: string;
}

/**
 * AffectedTimeline
 * 
 * Represents a timeline affected by a breach, with before/after metrics.
 */
export interface AffectedTimeline {
  /** Timeline identifier */
  id: string;

  /** Timeline name */
  name: string;

  /** Stability score before breach */
  stabilityBefore: number;

  /** Stability score after breach */
  stabilityAfter: number;

  /** Logic gap before breach */
  logicGapBefore: number;

  /** Logic gap after breach */
  logicGapAfter: number;
}

/**
 * AffectedAgent
 * 
 * Represents an agent affected by a breach, with impact metrics.
 */
export interface AffectedAgent {
  /** Agent identifier */
  id: string;

  /** Agent name */
  name: string;

  /** Agent archetype */
  archetype: string;

  /** P&L impact on the agent */
  pnlImpact: number;

  /** Sanity impact on the agent */
  sanityImpact: number;
}

/**
 * Beneficiary
 * 
 * Represents an entity that benefited from a breach.
 */
export interface Beneficiary {
  /** Type of beneficiary */
  type: 'agent' | 'wallet';

  /** Beneficiary identifier */
  id: string;

  /** Beneficiary name */
  name: string;

  /** Estimated gain from the breach */
  estimatedGain: number;

  /** Position before breach (optional) */
  positionBefore?: string;

  /** Position after breach (optional) */
  positionAfter?: string;
}

/**
 * EvidenceChange
 * 
 * Represents a change in evidence related to a breach.
 */
export interface EvidenceChange {
  /** ISO timestamp of the change */
  timestamp: string;

  /** Source of the evidence */
  source: string;

  /** Type of change */
  changeType: 'added' | 'removed' | 'contradicted';

  /** Description of the change */
  description: string;
}

/**
 * SuggestedAction
 * 
 * Represents a suggested action to address a breach.
 */
export interface SuggestedAction {
  /** Action identifier */
  id: string;

  /** Action description */
  action: string;

  /** Priority level */
  priority: 'immediate' | 'recommended' | 'optional';

  /** Estimated impact of the action */
  estimatedImpact: string;
}

/**
 * BreachStats
 * 
 * Statistics about breaches in the system.
 */
export interface BreachStats {
  /** Total number of active breaches */
  totalActive: number;

  /** Count of breaches by severity */
  bySeverity: Record<BreachSeverity, number>;

  /** Count of breaches by category */
  byCategory: Record<BreachCategory, number>;
}
