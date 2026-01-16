import type { ReplayPointer } from './replay';

/**
 * Live Tape Types
 * 
 * Types for the Live Tape feature, which displays a real-time feed
 * of events across timelines, agents, and forks.
 */

/**
 * Tape event type classification
 */
export type TapeEventType =
  | 'wing_flap'
  | 'fork_live'
  | 'sabotage_disclosed'
  | 'paradox_spawn'
  | 'evidence_flip'
  | 'settlement';

/**
 * Impact metrics for an event
 */
export interface EventImpact {
  /** Stability delta (can be positive or negative) */
  stabilityDelta?: number;
  /** Logic gap delta (can be positive or negative) */
  logicGapDelta?: number;
  /** Price delta (can be positive or negative) */
  priceDelta?: number;
}

/**
 * Tape event representing a single event in the live feed
 */
export interface TapeEvent {
  /** Unique identifier for the event */
  id: string;
  
  /** ISO timestamp when the event occurred */
  ts: string;
  
  /** Type of event */
  type: TapeEventType;
  
  /** Timeline ID (optional, not all events are timeline-specific) */
  timelineId?: string;
  
  /** Timeline title (for display) */
  timelineTitle?: string;
  
  /** Agent ID (optional, for agent-related events) */
  agentId?: string;
  
  /** Agent name (for display) */
  agentName?: string;
  
  /** Wallet address (optional, for wallet-related events) */
  wallet?: string;
  
  /** Human-readable summary of the event */
  summary: string;
  
  /** Impact metrics (optional) */
  impact?: EventImpact;
  
  /** Replay pointer (optional, for events that can be replayed) */
  replayPointer?: ReplayPointer;
}
