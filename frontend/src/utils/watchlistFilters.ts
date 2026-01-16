import type { WatchlistTimeline } from '../types/watchlist';
import type { WatchlistFilterConfig, WatchlistSortKey } from '../types/presets';

/**
 * Apply filter configuration to watchlist timelines
 */
export function applyFilter(
  timelines: WatchlistTimeline[],
  filter: WatchlistFilterConfig
): WatchlistTimeline[] {
  return timelines.filter((timeline) => {
    // Query filter
    if (filter.query) {
      const query = filter.query.toLowerCase();
      const matchesName = timeline.name.toLowerCase().includes(query);
      const matchesId = timeline.id.toLowerCase().includes(query);
      if (!matchesName && !matchesId) {
        return false;
      }
    }

    // Stability range
    if (filter.minStability !== undefined && timeline.stability < filter.minStability) {
      return false;
    }
    if (filter.maxStability !== undefined && timeline.stability > filter.maxStability) {
      return false;
    }

    // Logic gap range
    if (filter.minLogicGap !== undefined && timeline.logicGap < filter.minLogicGap) {
      return false;
    }
    if (filter.maxLogicGap !== undefined && timeline.logicGap > filter.maxLogicGap) {
      return false;
    }

    // Paradox only
    if (filter.paradoxOnly && timeline.paradoxProximity < 80) {
      return false;
    }

    // Brittle only (logic gap 40-60)
    if (filter.brittleOnly) {
      if (timeline.logicGap < 40 || timeline.logicGap >= 60) {
        return false;
      }
    }

    // Sabotage heat minimum
    if (filter.sabotageHeatMin !== undefined) {
      if (timeline.sabotageCount24h < filter.sabotageHeatMin) {
        return false;
      }
    }

    // Max next fork ETA (stub - we don't have this data in WatchlistTimeline)
    // This would require additional data from the timeline detail
    if (filter.maxNextForkEtaSec !== undefined) {
      // For now, skip this filter as we don't have nextForkEta in WatchlistTimeline
      // In production, this would check timeline.nextForkEtaSec
    }

    // Tags filter (stub - we don't have tags in WatchlistTimeline)
    if (filter.tags && filter.tags.length > 0) {
      // For now, skip this filter
      // In production, this would check timeline.tags
    }

    return true;
  });
}

/**
 * Sort watchlist timelines by sort key and direction
 */
export function applySort(
  timelines: WatchlistTimeline[],
  sortKey: WatchlistSortKey,
  sortDir: 'asc' | 'desc'
): WatchlistTimeline[] {
  const sorted = [...timelines].sort((a, b) => {
    let aValue: number;
    let bValue: number;

    switch (sortKey) {
      case 'stability':
        aValue = a.stability;
        bValue = b.stability;
        break;
      case 'logic_gap':
        aValue = a.logicGap;
        bValue = b.logicGap;
        break;
      case 'paradox_proximity':
        aValue = a.paradoxProximity;
        bValue = b.paradoxProximity;
        break;
      case 'entropy_rate':
        aValue = a.entropyRate;
        bValue = b.entropyRate;
        break;
      case 'sabotage_heat':
        aValue = a.sabotageCount24h;
        bValue = b.sabotageCount24h;
        break;
      case 'next_fork_eta':
        // Stub - use sabotage count as placeholder
        aValue = a.sabotageCount24h;
        bValue = b.sabotageCount24h;
        break;
      default:
        return 0;
    }

    if (aValue < bValue) return sortDir === 'asc' ? -1 : 1;
    if (aValue > bValue) return sortDir === 'asc' ? 1 : -1;
    return 0;
  });

  return sorted;
}
