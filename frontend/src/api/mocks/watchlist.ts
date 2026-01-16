import type { WatchlistTimeline, WatchlistFilter } from '../../types/watchlist';

/**
 * Mock Watchlist Data
 * ===================
 * 
 * Provides sample watchlist timeline data for development and testing.
 * Includes realistic telemetry data for various risk scenarios.
 */

/**
 * Sample timeline: Oil Crisis - Hormuz Strait
 * Category: brittle + under attack
 */
const timeline1: WatchlistTimeline = {
  id: 'tl_oil_hormuz_001',
  name: 'Oil Crisis - Hormuz Strait',
  slug: 'oil-crisis-hormuz-strait',
  yesPrice: 0.45,
  noPrice: 0.55,
  stability: 54.7,
  stabilityTrend: 'down',
  logicGap: 42,
  logicGapTrend: 'widening',
  paradoxProximity: 70,
  entropyRate: -2.1,
  entropyHistory: [-1.8, -1.9, -2.0, -2.1, -2.1, -2.1],
  sabotageCount1h: 3,
  sabotageCount24h: 12,
  addedAt: '2025-01-15T10:30:00Z',
};

/**
 * Sample timeline: Fed Rate Decision - January 2026
 * Category: healthy
 */
const timeline2: WatchlistTimeline = {
  id: 'tl_fed_rate_jan26',
  name: 'Fed Rate Decision - January 2026',
  slug: 'fed-rate-decision-january-2026',
  yesPrice: 0.72,
  noPrice: 0.28,
  stability: 89.2,
  stabilityTrend: 'flat',
  logicGap: 8,
  logicGapTrend: 'stable',
  paradoxProximity: 13,
  entropyRate: -0.5,
  entropyHistory: [-0.5, -0.5, -0.5, -0.5, -0.5, -0.5],
  sabotageCount1h: 0,
  sabotageCount24h: 2,
  addedAt: '2025-01-10T08:15:00Z',
};

/**
 * Sample timeline: Contagion Zero - Mumbai
 * Category: paradox-watch
 */
const timeline3: WatchlistTimeline = {
  id: 'tl_contagion_mumbai',
  name: 'Contagion Zero - Mumbai',
  slug: 'contagion-zero-mumbai',
  yesPrice: 0.33,
  noPrice: 0.67,
  stability: 38.5,
  stabilityTrend: 'down',
  logicGap: 62,
  logicGapTrend: 'widening',
  paradoxProximity: 95,
  entropyRate: -4.2,
  entropyHistory: [-3.1, -3.5, -3.8, -4.0, -4.1, -4.2],
  sabotageCount1h: 1,
  sabotageCount24h: 8,
  addedAt: '2025-01-12T14:20:00Z',
};

/**
 * Sample timeline: Ghost Tanker - Venezuela
 * Category: under attack + high entropy
 */
const timeline4: WatchlistTimeline = {
  id: 'tl_ghost_tanker_ven',
  name: 'Ghost Tanker - Venezuela',
  slug: 'ghost-tanker-venezuela',
  yesPrice: 0.58,
  noPrice: 0.42,
  stability: 61.2,
  stabilityTrend: 'down',
  logicGap: 35,
  logicGapTrend: 'widening',
  paradoxProximity: 58,
  entropyRate: -3.8,
  entropyHistory: [-2.9, -3.1, -3.3, -3.5, -3.7, -3.8],
  sabotageCount1h: 5,
  sabotageCount24h: 18,
  addedAt: '2025-01-14T16:45:00Z',
};

/**
 * All mock timelines
 */
const allTimelines: WatchlistTimeline[] = [
  timeline1,
  timeline2,
  timeline3,
  timeline4,
];

/**
 * Filter function to determine if a timeline matches a filter
 */
function matchesFilter(timeline: WatchlistTimeline, filter: WatchlistFilter): boolean {
  switch (filter) {
    case 'all':
      return true;
    
    case 'brittle':
      // logicGap >= 40 AND logicGap < 60
      return timeline.logicGap >= 40 && timeline.logicGap < 60;
    
    case 'paradox-watch':
      // logicGap >= 60 OR logicGapTrend === 'widening'
      return timeline.logicGap >= 60 || timeline.logicGapTrend === 'widening';
    
    case 'high-entropy':
      // entropyRate < -3
      return timeline.entropyRate < -3;
    
    case 'under-attack':
      // sabotageCount1h >= 3
      return timeline.sabotageCount1h >= 3;
    
    default:
      return true;
  }
}

/**
 * Get Mock Watchlist
 * 
 * Returns filtered watchlist timelines with simulated network delay.
 * 
 * @param filter - Optional filter to apply to the results
 * @returns Promise resolving to array of WatchlistTimeline
 * 
 * @example
 * ```ts
 * // Get all timelines
 * const all = await getMockWatchlist();
 * 
 * // Get brittle timelines
 * const brittle = await getMockWatchlist('brittle');
 * 
 * // Get timelines under attack
 * const attacked = await getMockWatchlist('under-attack');
 * ```
 */
export async function getMockWatchlist(
  filter?: WatchlistFilter
): Promise<WatchlistTimeline[]> {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 100));
  
  // Apply filter if provided
  if (filter) {
    return allTimelines.filter((timeline) => matchesFilter(timeline, filter));
  }
  
  // Return all timelines if no filter
  return allTimelines;
}
