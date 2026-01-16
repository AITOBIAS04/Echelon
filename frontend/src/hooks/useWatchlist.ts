import { useQuery } from '@tanstack/react-query';
import { getMockWatchlist } from '../api/mocks/watchlist';
import type { WatchlistFilter, WatchlistTimeline } from '../types/watchlist';

/**
 * Filter function to determine if a timeline matches a filter
 * (Matches the logic from the mock API)
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
 * Get Filtered Count
 * 
 * Helper function to count timelines matching a specific filter criteria.
 * Useful for displaying filter badge counts.
 * 
 * @param timelines - Array of all timelines
 * @param filter - Filter to apply
 * @returns Count of timelines matching the filter
 * 
 * @example
 * ```ts
 * const allTimelines = await getMockWatchlist();
 * const brittleCount = getFilteredCount(allTimelines, 'brittle');
 * ```
 */
export function getFilteredCount(
  timelines: WatchlistTimeline[],
  filter: WatchlistFilter
): number {
  return timelines.filter((timeline) => matchesFilter(timeline, filter)).length;
}

/**
 * useWatchlist Hook
 * 
 * React Query hook for fetching and managing watchlist data.
 * Automatically refetches every 30 seconds for real-time updates.
 * 
 * @param filter - Filter to apply to the watchlist (default: 'all')
 * @returns Query result with data, isLoading, error, and refetch function
 * 
 * @example
 * ```tsx
 * function WatchlistComponent() {
 *   const { data, isLoading, error } = useWatchlist('brittle');
 *   
 *   if (isLoading) return <div>Loading...</div>;
 *   if (error) return <div>Error: {error.message}</div>;
 *   
 *   return (
 *     <div>
 *       {data?.map(timeline => (
 *         <WatchlistRow key={timeline.id} timeline={timeline} />
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 */
export function useWatchlist(filter: WatchlistFilter = 'all') {
  return useQuery({
    queryKey: ['watchlist', filter],
    queryFn: () => getMockWatchlist(filter),
    staleTime: 10000, // 10 seconds
    refetchInterval: 30000, // 30 seconds for real-time feel
  });
}
