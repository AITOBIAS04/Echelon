/**
 * useSignalMap — OSINT signals + convergence heatmap.
 *
 * Backend endpoints:
 *   GET /api/v1/osint/signals        — OSINT signal feed
 *   GET /api/v1/convergence/heatmap  — convergence data
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';

// ── Types (backend response shapes) ─────────────────────────────────────

export interface OSINTSignal {
  id: string;
  source: string;
  headline: string;
  url: string | null;
  relevance_score: number;
  sentiment: number;
  entities: string[];
  timeline_ids: string[];
  detected_at: string;
}

export interface OSINTSignalsResponse {
  signals: OSINTSignal[];
  total: number;
}

export interface HeatmapCell {
  timeline_id: string;
  timeline_name: string;
  signal_count: number;
  convergence_score: number;
  dominant_sentiment: number;
}

export interface HeatmapResponse {
  cells: HeatmapCell[];
  generated_at: string;
}

// ── API functions ───────────────────────────────────────────────────────

async function fetchSignals(params?: {
  limit?: number;
  offset?: number;
}): Promise<OSINTSignalsResponse> {
  const { data } = await apiClient.get('/api/v1/osint/signals', { params });
  return data;
}

async function fetchHeatmap(): Promise<HeatmapResponse> {
  const { data } = await apiClient.get('/api/v1/convergence/heatmap');
  return data;
}

// ── Hook ────────────────────────────────────────────────────────────────

export function useSignalMap() {
  const signalsQuery = useQuery<OSINTSignalsResponse>({
    queryKey: ['signal-map', 'signals'],
    queryFn: () => fetchSignals({ limit: 50 }),
    staleTime: 15_000,
    refetchInterval: 30_000,
    placeholderData: (prev) => prev,
  });

  const heatmapQuery = useQuery<HeatmapResponse>({
    queryKey: ['signal-map', 'heatmap'],
    queryFn: fetchHeatmap,
    staleTime: 30_000,
    refetchInterval: 60_000,
    placeholderData: (prev) => prev,
  });

  const signals = signalsQuery.data?.signals ?? [];
  const heatmap = heatmapQuery.data?.cells ?? [];

  const isSparse = !signalsQuery.isLoading && signals.length < 3;
  const isQuiet = !signalsQuery.isLoading && signals.length === 0;

  return {
    signals,
    totalSignals: signalsQuery.data?.total ?? 0,
    heatmap,
    heatmapGeneratedAt: heatmapQuery.data?.generated_at ?? null,
    isLoading: signalsQuery.isLoading || heatmapQuery.isLoading,
    error: signalsQuery.error ?? heatmapQuery.error,
    isSparse,
    isQuiet,
  };
}
