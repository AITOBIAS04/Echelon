import type {
  PositionExposure,
  TimelineRiskState,
} from '../types/risk';

/**
 * Risk API
 * ========
 * 
 * Mock API functions for fetching position exposures and timeline risk states.
 * In production, these would call actual backend endpoints.
 */

/**
 * Get My Positions
 * 
 * Returns all positions held by the current user.
 * 
 * @returns Promise resolving to array of position exposures
 */
export async function getMyPositions(): Promise<PositionExposure[]> {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 150));

  const positions: PositionExposure[] = [
    {
      timelineId: 'tl_oil_hormuz_001',
      direction: 'YES',
      notional: 12500,
      avgPrice: 0.52,
      currentPrice: 0.45,
    },
    {
      timelineId: 'tl_fed_rate_jan26',
      direction: 'YES',
      notional: 8500,
      avgPrice: 0.68,
      currentPrice: 0.72,
    },
    {
      timelineId: 'tl_tech_reg_001',
      direction: 'NO',
      notional: 25000,
      avgPrice: 0.65,
      currentPrice: 0.62,
    },
    {
      timelineId: 'tl_oil_hormuz_001',
      direction: 'NO',
      notional: 3200,
      avgPrice: 0.48,
      currentPrice: 0.55,
    },
    {
      timelineId: 'tl_ghost_tanker',
      direction: 'YES',
      notional: 1200,
      avgPrice: 0.35,
      currentPrice: 0.42,
    },
    {
      timelineId: 'tl_ai_oversight_2026',
      direction: 'YES',
      notional: 250,
      avgPrice: 0.28,
      currentPrice: 0.31,
    },
    {
      timelineId: 'tl_cyber_attack_q1',
      direction: 'NO',
      notional: 5500,
      avgPrice: 0.72,
      currentPrice: 0.68,
    },
    {
      timelineId: 'tl_election_outcome',
      direction: 'YES',
      notional: 18000,
      avgPrice: 0.55,
      currentPrice: 0.58,
    },
    {
      timelineId: 'tl_ghost_tanker',
      direction: 'NO',
      notional: 800,
      avgPrice: 0.58,
      currentPrice: 0.55,
    },
    {
      timelineId: 'tl_ai_oversight_2026',
      direction: 'NO',
      notional: 450,
      avgPrice: 0.75,
      currentPrice: 0.69,
    },
  ];

  return positions;
}

/**
 * Get Timeline Risk States
 * 
 * Returns risk state data for the specified timelines.
 * 
 * @param timelineIds - Array of timeline IDs to fetch risk states for
 * @returns Promise resolving to array of timeline risk states
 */
export async function getTimelineRiskStates(
  timelineIds: string[]
): Promise<TimelineRiskState[]> {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 150));

  // Mock risk state data for various timelines
  const riskStateMap: Record<string, TimelineRiskState> = {
    'tl_oil_hormuz_001': {
      timelineId: 'tl_oil_hormuz_001',
      stability: 54.7,
      logicGap: 42,
      entropyRate: -2.1,
      paradoxProximity: 65,
      sabotageHeat24h: 4,
      nextForkEtaSec: 900, // 15 minutes
    },
    'tl_fed_rate_jan26': {
      timelineId: 'tl_fed_rate_jan26',
      stability: 89.2,
      logicGap: 8,
      entropyRate: -0.5,
      paradoxProximity: 12,
      sabotageHeat24h: 0,
      nextForkEtaSec: 3600, // 1 hour
    },
    'tl_tech_reg_001': {
      timelineId: 'tl_tech_reg_001',
      stability: 55.8,
      logicGap: 60,
      entropyRate: -1.8,
      paradoxProximity: 78,
      sabotageHeat24h: 2,
      nextForkEtaSec: 1800, // 30 minutes
    },
    'tl_ghost_tanker': {
      timelineId: 'tl_ghost_tanker',
      stability: 72.3,
      logicGap: 28,
      entropyRate: -1.2,
      paradoxProximity: 35,
      sabotageHeat24h: 1,
      nextForkEtaSec: 2400, // 40 minutes
    },
    'tl_ai_oversight_2026': {
      timelineId: 'tl_ai_oversight_2026',
      stability: 48.5,
      logicGap: 52,
      entropyRate: -2.5,
      paradoxProximity: 70,
      sabotageHeat24h: 3,
      nextForkEtaSec: 1200, // 20 minutes
    },
    'tl_cyber_attack_q1': {
      timelineId: 'tl_cyber_attack_q1',
      stability: 65.2,
      logicGap: 35,
      entropyRate: -1.5,
      paradoxProximity: 45,
      sabotageHeat24h: 1,
      nextForkEtaSec: 4800, // 80 minutes
    },
    'tl_election_outcome': {
      timelineId: 'tl_election_outcome',
      stability: 78.9,
      logicGap: 18,
      entropyRate: -0.8,
      paradoxProximity: 22,
      sabotageHeat24h: 0,
      nextForkEtaSec: 7200, // 2 hours
    },
  };

  // Return only requested timelines
  return timelineIds
    .map((id) => riskStateMap[id])
    .filter((state): state is TimelineRiskState => state !== undefined);
}
