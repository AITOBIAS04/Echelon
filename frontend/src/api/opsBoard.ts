/**
 * Operations Board API — Aggregation from real endpoints
 *
 * Fetches summary data from existing endpoints to build
 * the aggregation dashboard. No mock data.
 */

import { apiClient } from './client';
import type { TimelineHealthResponse, WingFlapFeedResponse } from '../types';

export interface OpsDashboardData {
  timelines: {
    total: number;
    active: number;
    withParadox: number;
    avgStability: number;
  };
  agents: {
    total: number;
    alive: number;
  };
  paradoxes: {
    totalActive: number;
  };
  investigations: {
    total: number;
  };
  recentFlaps: WingFlapFeedResponse['flaps'];
}

export async function fetchOpsDashboard(): Promise<OpsDashboardData> {
  // Parallel fetch from existing endpoints
  const [timelinesResp, agentsResp, paradoxResp, investigationsResp, flapsResp] =
    await Promise.allSettled([
      apiClient.get<TimelineHealthResponse>('/api/v1/butterfly/timelines/health'),
      apiClient.get<{ agents: unknown[]; total: number }>('/api/v1/agents', {
        params: { limit: 1 },
      }),
      apiClient.get<{ paradoxes: unknown[]; total_active: number }>(
        '/api/v1/paradox/active',
      ),
      apiClient.get<{ investigations: unknown[]; total: number }>(
        '/api/v1/investigations/',
      ),
      apiClient.get<WingFlapFeedResponse>('/api/v1/butterfly/flaps', {
        params: { limit: 10 },
      }),
    ]);

  const timelines =
    timelinesResp.status === 'fulfilled'
      ? timelinesResp.value.data.timelines
      : [];
  const agentTotal =
    agentsResp.status === 'fulfilled' ? agentsResp.value.data.total : 0;
  const paradoxTotal =
    paradoxResp.status === 'fulfilled'
      ? paradoxResp.value.data.total_active
      : 0;
  const investigationTotal =
    investigationsResp.status === 'fulfilled'
      ? investigationsResp.value.data.total
      : 0;
  const flaps =
    flapsResp.status === 'fulfilled' ? flapsResp.value.data.flaps : [];

  // All timelines returned by /health are active
  const withParadox = timelines.filter((t) => t.has_active_paradox).length;
  const avgStability =
    timelines.length > 0
      ? timelines.reduce((sum, t) => sum + t.stability, 0) /
        timelines.length
      : 0;

  return {
    timelines: {
      total: timelines.length,
      active: timelines.length,
      withParadox,
      avgStability,
    },
    agents: {
      total: agentTotal,
      alive: agentTotal, // API returns alive agents by default
    },
    paradoxes: {
      totalActive: paradoxTotal,
    },
    investigations: {
      total: investigationTotal,
    },
    recentFlaps: flaps,
  };
}
