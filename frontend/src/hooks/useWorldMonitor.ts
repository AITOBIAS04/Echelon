/**
 * useWorldMonitor — Aggregated world view combining timeline health,
 * gravity trends, and ripple propagation.
 *
 * Backend endpoints:
 *   GET /api/v1/butterfly/timelines/health — all timeline metrics
 *   GET /api/v1/butterfly/wing-flaps       — ripple/activity feed
 *
 * Note: gravity trending endpoint may not be separate from timeline health.
 * Timeline health already includes gravity_score and gravity_factors.
 */

import { useQuery } from '@tanstack/react-query';
import { butterflyApi } from '../api/butterfly';
import type { Timeline, WingFlap } from '../types';

export interface WorldMonitorData {
  timelines: Timeline[];
  recentActivity: WingFlap[];
  stats: {
    totalTimelines: number;
    activeParadoxes: number;
    avgStability: number;
    highGravityCount: number;
  };
}

export function useWorldMonitor() {
  // Timeline health — all timelines with metrics
  const healthQuery = useQuery({
    queryKey: ['world-monitor', 'health'],
    queryFn: () => butterflyApi.getTimelineHealth({ limit: 100 }),
    staleTime: 10_000,
    refetchInterval: 20_000,
    placeholderData: (prev) => prev,
  });

  // Recent wing flaps — activity feed
  const activityQuery = useQuery({
    queryKey: ['world-monitor', 'activity'],
    queryFn: () => butterflyApi.getWingFlaps({ limit: 20 }),
    staleTime: 10_000,
    refetchInterval: 15_000,
    placeholderData: (prev) => prev,
  });

  const timelines = healthQuery.data?.timelines ?? [];
  const recentActivity = activityQuery.data?.flaps ?? [];

  // Compute aggregate stats
  const stats = {
    totalTimelines: timelines.length,
    activeParadoxes: timelines.filter((t) => t.has_active_paradox).length,
    avgStability:
      timelines.length > 0
        ? timelines.reduce((sum, t) => sum + t.stability, 0) / timelines.length
        : 0,
    highGravityCount: timelines.filter((t) => t.gravity_score > 70).length,
  };

  const isQuiet =
    !healthQuery.isLoading &&
    stats.activeParadoxes === 0 &&
    stats.avgStability > 70;

  return {
    timelines,
    recentActivity,
    stats,
    isLoading: healthQuery.isLoading || activityQuery.isLoading,
    error: healthQuery.error ?? activityQuery.error,
    isQuiet,
    isEmpty: !healthQuery.isLoading && timelines.length === 0,
  };
}
