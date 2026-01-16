import { useState, useEffect, useCallback } from 'react';
import { getLaunchpadFeed } from '../api/launchpad';
import type { LaunchpadFeed } from '../types/launchpad';

/**
 * useLaunchpadFeed Hook
 * 
 * React hook for fetching and managing launchpad feed data.
 * Fetches feed on mount and provides refresh functionality.
 * 
 * @returns Object containing feed data, loading state, error, and refresh function
 * 
 * @example
 * ```tsx
 * function LaunchpadPage() {
 *   const { feed, loading, error, refresh } = useLaunchpadFeed();
 *   
 *   if (loading) return <div>Loading...</div>;
 *   if (error) return <div>Error: {error}</div>;
 *   
 *   return (
 *     <div>
 *       <h2>Trending</h2>
 *       {feed?.trending.map(launch => <LaunchCard key={launch.id} launch={launch} />)}
 *       <button onClick={refresh}>Refresh</button>
 *     </div>
 *   );
 * }
 * ```
 */
export function useLaunchpadFeed() {
  const [feed, setFeed] = useState<LaunchpadFeed | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchFeed = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getLaunchpadFeed();
      setFeed(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch launchpad feed';
      setError(errorMessage);
      setFeed(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFeed();
  }, [fetchFeed]);

  const refresh = useCallback(async () => {
    await fetchFeed();
  }, [fetchFeed]);

  return {
    feed,
    loading,
    error,
    refresh,
  };
}
