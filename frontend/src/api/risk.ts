import type {
  PositionExposure,
  TimelineRiskState,
} from '../types/risk';

/**
 * Risk API — DEFERRED
 *
 * No backend endpoints exist for user positions or per-timeline risk states.
 * These functions return empty arrays so consumers render honest empty states
 * instead of fabricated data.
 *
 * When a real positions/risk API ships, replace these stubs with fetch calls.
 */

/**
 * Get My Positions — returns empty (no backend endpoint).
 */
export async function getMyPositions(): Promise<PositionExposure[]> {
  return [];
}

/**
 * Get Timeline Risk States — returns empty (no backend endpoint).
 */
export async function getTimelineRiskStates(
  _timelineIds: string[],
): Promise<TimelineRiskState[]> {
  return [];
}
