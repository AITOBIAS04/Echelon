import { useState, useEffect, useCallback } from 'react';
import { getMyPositions, getTimelineRiskStates } from '../api/risk';
import { computePortfolioRisk } from '../lib/riskScoring';
import type { PortfolioRiskSummary } from '../types/risk';

/**
 * usePortfolioRisk Hook
 * =====================
 * 
 * React hook for fetching and computing portfolio risk analysis.
 * Automatically refreshes every 30 seconds.
 * 
 * @returns Object with summary, loading, error, and refresh function
 * 
 * @example
 * ```tsx
 * function PortfolioRiskPanel() {
 *   const { summary, loading, error, refresh } = usePortfolioRisk();
 *   
 *   if (loading) return <div>Loading...</div>;
 *   if (error) return <div>Error: {error}</div>;
 *   if (!summary) return <div>No data</div>;
 *   
 *   return (
 *     <div>
 *       <h3>Risk Index: {summary.riskIndex.toFixed(1)}</h3>
 *       <p>Total Notional: ${summary.totalNotional.toLocaleString()}</p>
 *     </div>
 *   );
 * }
 * ```
 */
export function usePortfolioRisk() {
  const [summary, setSummary] = useState<PortfolioRiskSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch positions
      const positions = await getMyPositions();

      // Extract unique timeline IDs from positions
      const timelineIds = Array.from(
        new Set(positions.map((pos) => pos.timelineId))
      );

      // Fetch risk states for those timelines
      const riskStates = await getTimelineRiskStates(timelineIds);

      // Compute portfolio risk summary
      const computedSummary = computePortfolioRisk(positions, riskStates);

      setSummary(computedSummary);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load portfolio risk';
      setError(errorMessage);
      console.error('Error loading portfolio risk:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load and set up refresh interval
  useEffect(() => {
    // Initial load
    refresh();

    // Set up interval to refresh every 30 seconds
    const interval = setInterval(() => {
      refresh();
    }, 30000); // 30 seconds

    // Cleanup interval on unmount
    return () => {
      clearInterval(interval);
    };
  }, [refresh]);

  return {
    summary,
    loading,
    error,
    refresh,
  };
}
