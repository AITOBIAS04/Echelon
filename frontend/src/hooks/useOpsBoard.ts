import { useState, useEffect, useCallback, useRef } from 'react';
import { getOpsBoard } from '../api/opsBoard';
import type { OpsBoardData } from '../types/opsBoard';

/**
 * useOpsBoard Hook
 * 
 * React hook for fetching and managing operations board data.
 * Fetches data on mount and auto-refreshes every 20 seconds.
 * 
 * @returns Object containing data, loading state, error, and refresh function
 * 
 * @example
 * ```tsx
 * function OpsBoardPage() {
 *   const { data, loading, error, refresh } = useOpsBoard();
 *   
 *   if (loading) return <div>Loading...</div>;
 *   if (error) return <div>Error: {error}</div>;
 *   
 *   return (
 *     <div>
 *       <h2>Live Now: {data?.liveNow.forksLive} forks</h2>
 *       {data?.lanes.new_creations.map(card => <Card key={card.id} card={card} />)}
 *     </div>
 *   );
 * }
 * ```
 */
export function useOpsBoard() {
  const [data, setData] = useState<OpsBoardData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const boardData = await getOpsBoard();
      setData(boardData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch ops board data';
      setError(errorMessage);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Fetch on mount
    fetchData();

    // Set up auto-refresh every 20 seconds
    intervalRef.current = setInterval(() => {
      fetchData();
    }, 20000); // 20 seconds

    // Cleanup interval on unmount
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchData]);

  const refresh = useCallback(async () => {
    await fetchData();
  }, [fetchData]);

  return {
    data,
    loading,
    error,
    refresh,
  };
}
