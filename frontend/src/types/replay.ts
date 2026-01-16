/**
 * Replay Types
 * ============
 * 
 * TypeScript interfaces for fork replay functionality, allowing users to
 * replay and analyze historical fork events with price paths and disclosure events.
 */

/**
 * Disclosure Event Type
 * 
 * Types of events that can occur during a fork's lifecycle.
 */
export type DisclosureEventType =
  | 'sabotage_disclosed'
  | 'paradox_spawn'
  | 'evidence_flip';

/**
 * Disclosure Event
 * 
 * Represents an event that occurred during a fork's lifecycle.
 */
export interface DisclosureEvent {
  /** Timestamp in milliseconds relative to fork opening */
  tMs: number;
  
  /** Type of disclosure event */
  type: DisclosureEventType;
  
  /** Human-readable label describing the event */
  label: string;
}

/**
 * Fork Option Price Path
 * 
 * Represents the price history of a fork option over time.
 */
export interface ForkOptionPricePath {
  /** Timestamp in milliseconds relative to fork opening */
  tMs: number;
  
  /** Price at this timestamp (0-1) */
  price: number;
}

/**
 * Fork Option
 * 
 * Represents an option within a fork with its price history.
 */
export interface ForkOption {
  /** Human-readable label for the option */
  label: string;
  
  /** Price path over time */
  pricePath: ForkOptionPricePath[];
}

/**
 * ForkReplay
 * 
 * Complete replay data for a fork, including price paths, disclosure events,
 * and outcome information.
 */
export interface ForkReplay {
  /** Timeline identifier */
  timelineId: string;
  
  /** Fork identifier */
  forkId: string;
  
  /** Question posed by the fork */
  forkQuestion: string;
  
  /** Available options with their price paths */
  options: ForkOption[];
  
  /** ISO timestamp when fork was opened */
  openedAt: string;
  
  /** ISO timestamp when fork was locked (optional) */
  lockedAt?: string;
  
  /** ISO timestamp when fork was executed (optional) */
  executedAt?: string;
  
  /** ISO timestamp when fork was settled (optional) */
  settledAt?: string;
  
  /** Label of the chosen option (optional) */
  chosenOption?: string;
  
  /** Outcome label (optional) */
  outcomeLabel?: string;
  
  /** Disclosure events that occurred during the fork's lifecycle */
  disclosureEvents: DisclosureEvent[];
  
  /** Additional notes about the replay (optional) */
  notes?: string;
}

/**
 * ReplayPointer
 * 
 * Pointer to a specific fork replay, used to fetch replay data.
 */
export type ReplayPointer = {
  /** Timeline identifier */
  timelineId: string;
  
  /** Fork identifier */
  forkId: string;
};
