import { useState, useEffect, useMemo, useCallback } from 'react';
import { getMyPositions } from '../api/risk';
import type { PositionExposure } from '../types/risk';

/**
 * UserPosition
 *
 * Aggregated position data per timeline for display purposes.
 */
export interface UserPosition {
  timelineId: string;
  totalNotional: number;
  netDirection: 'YES' | 'NO' | 'NEUTRAL';
  yesNotional: number;
  noNotional: number;
  avgPrice: number;
  currentPrice: number;
  pnlPercent: number;
  pnlValue: number;
  positions: PositionExposure[];
}

/**
 * useUserPositions Hook
 * =====================
 *
 * React hook for fetching and aggregating user's positions by timeline.
 * Provides easy access to stake amounts, PnL, and direction per timeline.
 *
 * @returns Object with positions array, loading state, error, and refresh function
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { positions, loading, error } = useUserPositions();
 *
 *   if (loading) return <div>Loading...</div>;
 *
 *   return (
 *     <div>
 *       {positions.map(pos => (
 *         <div key={pos.timelineId}>
 *           {pos.timelineId}: ${pos.totalNotional.toLocaleString()}
 *           ({pos.netDirection}) PnL: {pos.pnlPercent.toFixed(1)}%
 *         </div>
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 */
export function useUserPositions() {
  const [positions, setPositions] = useState<UserPosition[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch raw positions from API
      const rawPositions = await getMyPositions();

      // Aggregate positions by timeline
      const timelineMap = new Map<string, PositionExposure[]>();

      rawPositions.forEach((pos) => {
        const existing = timelineMap.get(pos.timelineId) || [];
        existing.push(pos);
        timelineMap.set(pos.timelineId, existing);
      });

      // Convert to UserPosition array with PnL calculations
      const aggregatedPositions: UserPosition[] = Array.from(timelineMap.entries()).map(
        ([timelineId, timelinePositions]) => {
          const yesPositions = timelinePositions.filter((p) => p.direction === 'YES');
          const noPositions = timelinePositions.filter((p) => p.direction === 'NO');

          const yesNotional = yesPositions.reduce((sum, p) => sum + p.notional, 0);
          const noNotional = noPositions.reduce((sum, p) => sum + p.notional, 0);
          const totalNotional = yesNotional + noNotional;

          // Calculate weighted average entry price
          const totalYesValue = yesPositions.reduce((sum, p) => sum + p.notional * (p.avgPrice || 0), 0);
          const totalNoValue = noPositions.reduce((sum, p) => sum + p.notional * (p.avgPrice || 0), 0);
          const avgPrice =
            totalNotional > 0
              ? (totalYesValue + totalNoValue) / totalNotional
              : 0;

          // Current price (use most recent if available)
          const currentPrice =
            timelinePositions[0]?.currentPrice ||
            timelinePositions.reduce((max, p) => Math.max(max, p.currentPrice || 0), 0);

          // Calculate net direction
          let netDirection: 'YES' | 'NO' | 'NEUTRAL' = 'NEUTRAL';
          if (yesNotional > noNotional * 1.1) netDirection = 'YES';
          else if (noNotional > yesNotional * 1.1) netDirection = 'NO';

          // Calculate PnL
          const avgEntryPrice = avgPrice;
          const pnlPercent =
            avgEntryPrice > 0
              ? ((currentPrice - avgEntryPrice) / avgEntryPrice) * 100
              : 0;
          const pnlValue = totalNotional * (pnlPercent / 100);

          return {
            timelineId,
            totalNotional,
            netDirection,
            yesNotional,
            noNotional,
            avgPrice,
            currentPrice,
            pnlPercent,
            pnlValue,
            positions: timelinePositions,
          };
        }
      );

      // Sort by total notional (largest first)
      aggregatedPositions.sort((a, b) => b.totalNotional - a.totalNotional);

      setPositions(aggregatedPositions);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load positions';
      setError(errorMessage);
      console.error('Error loading user positions:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load and set up refresh interval (every 30 seconds)
  useEffect(() => {
    refresh();

    const interval = setInterval(() => {
      refresh();
    }, 30000);

    return () => {
      clearInterval(interval);
    };
  }, [refresh]);

  // Computed totals
  const totals = useMemo(() => {
    const totalValue = positions.reduce((sum, p) => sum + p.totalNotional, 0);
    const totalPnL = positions.reduce((sum, p) => sum + p.pnlValue, 0);
    const winningPositions = positions.filter((p) => p.pnlValue > 0).length;
    const losingPositions = positions.filter((p) => p.pnlValue < 0).length;

    return {
      totalValue,
      totalPnL,
      winningPositions,
      losingPositions,
      positionCount: positions.length,
    };
  }, [positions]);

  return {
    positions,
    loading,
    error,
    refresh,
    totals,
  };
}

/**
 * Get position for a specific timeline
 *
 * @param timelineId - The timeline ID to look up
 * @returns UserPosition | undefined if not found
 */
export function useUserPosition(timelineId: string) {
  const { positions, loading, error, totals } = useUserPositions();

  const position = positions.find((p) => p.timelineId === timelineId);

  return {
    position,
    loading,
    error,
    totals,
  };
}
