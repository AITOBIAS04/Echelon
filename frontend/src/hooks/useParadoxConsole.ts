/**
 * useParadoxConsole — Extended paradox hook with extraction and abandonment.
 *
 * Wraps the existing paradox API with additional mutation endpoints:
 *   POST /api/v1/paradox/:id/extract          — extract a paradox
 *   GET  /api/v1/paradox/:id/extraction-preview — preview extraction cost
 *   POST /api/v1/paradox/:id/abandon          — abandon a paradox
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import type { Paradox, ParadoxListResponse } from '../types';

// ── Extraction types (not yet in main types — backend returns these) ────

export interface ExtractionPreview {
  paradox_id: string;
  extraction_cost_usdc: number;
  extraction_cost_echelon: number;
  carrier_sanity_cost: number;
  estimated_stability_gain: number;
}

export interface ExtractionResult {
  paradox_id: string;
  status: string;
  extraction_reward_usdc: number;
  stability_restored: number;
}

export interface AbandonmentResult {
  paradox_id: string;
  status: string;
  detonation_triggered: boolean;
}

// ── API functions ───────────────────────────────────────────────────────

async function fetchActiveParadoxes(): Promise<ParadoxListResponse> {
  const { data } = await apiClient.get('/api/v1/paradox/active');
  return data;
}

async function fetchParadox(paradoxId: string): Promise<Paradox> {
  const { data } = await apiClient.get(`/api/v1/paradox/${paradoxId}`);
  return data;
}

async function previewExtraction(paradoxId: string): Promise<ExtractionPreview> {
  const { data } = await apiClient.get(`/api/v1/paradox/${paradoxId}/extraction-preview`);
  return data;
}

async function extractParadox(paradoxId: string): Promise<ExtractionResult> {
  const { data } = await apiClient.post(`/api/v1/paradox/${paradoxId}/extract`);
  return data;
}

async function abandonParadox(paradoxId: string): Promise<AbandonmentResult> {
  const { data } = await apiClient.post(`/api/v1/paradox/${paradoxId}/abandon`);
  return data;
}

// ── Hook ────────────────────────────────────────────────────────────────

export function useParadoxConsole() {
  const queryClient = useQueryClient();

  // Active paradoxes list
  const listQuery = useQuery<ParadoxListResponse>({
    queryKey: ['paradoxes', 'active'],
    queryFn: fetchActiveParadoxes,
    refetchInterval: 15_000,
    staleTime: 10_000,
    placeholderData: (prev) => prev,
    retry: 2,
    retryDelay: 1000,
  });

  // Extract mutation
  const extractMutation = useMutation({
    mutationFn: extractParadox,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['paradoxes'] });
    },
  });

  // Abandon mutation
  const abandonMutation = useMutation({
    mutationFn: abandonParadox,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['paradoxes'] });
    },
  });

  const paradoxes = listQuery.data?.paradoxes ?? [];
  const totalActive = listQuery.data?.total_active ?? 0;

  return {
    // Data
    paradoxes,
    totalActive,
    isAllClear: !listQuery.isLoading && totalActive === 0,

    // Loading / error
    isLoading: listQuery.isLoading,
    error: listQuery.error,

    // Actions
    extract: extractMutation.mutateAsync,
    isExtracting: extractMutation.isPending,
    abandon: abandonMutation.mutateAsync,
    isAbandoning: abandonMutation.isPending,

    // Preview (not a mutation — call as needed)
    previewExtraction,

    // Individual paradox fetch (for detail views)
    fetchParadox,
  };
}
