/**
 * useInvestigation — React Query hooks for investigation endpoints.
 *
 * Provides hooks for listing investigations, fetching detail, and
 * accessing sub-resources (evidence, claims, counter-signals, drift, certificate).
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchInvestigations,
  fetchInvestigation,
  fetchEvidence,
  fetchClaims,
  fetchCounterSignals,
  fetchDrift,
  fetchCertificate,
  createInvestigation,
} from '../api/investigation';
import type {
  InvestigationSummary,
  InvestigationDetail,
  EvidenceEnvelopeManifest,
  ClaimGraphSummary,
  CounterSignal,
  DriftEvent,
  InvestigationCertificate,
} from '../types/investigation';

// ── List ─────────────────────────────────────────────────────────────────

export function useInvestigationList() {
  const query = useQuery({
    queryKey: ['investigations'],
    queryFn: fetchInvestigations,
    staleTime: 10_000,
    refetchInterval: 15_000,
  });

  return {
    investigations: (query.data?.investigations ?? []) as InvestigationSummary[],
    total: query.data?.total ?? 0,
    isLoading: query.isLoading,
    error: query.error,
  };
}

// ── Detail ───────────────────────────────────────────────────────────────

export function useInvestigationDetail(investigationId: string | null) {
  const query = useQuery({
    queryKey: ['investigation', investigationId],
    queryFn: () => fetchInvestigation(investigationId!),
    enabled: !!investigationId,
    staleTime: 5_000,
    refetchInterval: 10_000,
  });

  return {
    investigation: (query.data ?? null) as InvestigationDetail | null,
    isLoading: query.isLoading,
    error: query.error,
  };
}

// ── Evidence ─────────────────────────────────────────────────────────────

export function useEvidence(investigationId: string | null) {
  const query = useQuery({
    queryKey: ['investigation', investigationId, 'evidence'],
    queryFn: () => fetchEvidence(investigationId!),
    enabled: !!investigationId,
    staleTime: 5_000,
  });

  return {
    evidence: (query.data ?? null) as EvidenceEnvelopeManifest | null,
    isLoading: query.isLoading,
    error: query.error,
  };
}

// ── Claims ───────────────────────────────────────────────────────────────

export function useClaims(investigationId: string | null) {
  const query = useQuery({
    queryKey: ['investigation', investigationId, 'claims'],
    queryFn: () => fetchClaims(investigationId!),
    enabled: !!investigationId,
    staleTime: 5_000,
  });

  return {
    claims: (query.data ?? null) as ClaimGraphSummary | null,
    isLoading: query.isLoading,
    error: query.error,
  };
}

// ── Counter-Signals ──────────────────────────────────────────────────────

export function useCounterSignals(investigationId: string | null) {
  const query = useQuery({
    queryKey: ['investigation', investigationId, 'counter-signals'],
    queryFn: () => fetchCounterSignals(investigationId!),
    enabled: !!investigationId,
    staleTime: 5_000,
  });

  return {
    signals: (query.data?.signals ?? []) as CounterSignal[],
    summary: (query.data?.summary ?? {}) as Record<string, number>,
    isLoading: query.isLoading,
    error: query.error,
  };
}

// ── Drift ────────────────────────────────────────────────────────────────

export function useDrift(investigationId: string | null) {
  const query = useQuery({
    queryKey: ['investigation', investigationId, 'drift'],
    queryFn: () => fetchDrift(investigationId!),
    enabled: !!investigationId,
    staleTime: 5_000,
  });

  return {
    events: (query.data?.events ?? []) as DriftEvent[],
    hasMaterialDrift: query.data?.has_material_drift ?? false,
    isLoading: query.isLoading,
    error: query.error,
  };
}

// ── Certificate ──────────────────────────────────────────────────────────

export function useCertificate(investigationId: string | null) {
  const query = useQuery({
    queryKey: ['investigation', investigationId, 'certificate'],
    queryFn: () => fetchCertificate(investigationId!),
    enabled: !!investigationId,
    staleTime: 30_000,
  });

  return {
    certificate: (query.data ?? null) as InvestigationCertificate | null,
    isLoading: query.isLoading,
    error: query.error,
  };
}

// ── Create ──────────────────────────────────────────────────────────────

export function useCreateInvestigation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createInvestigation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['investigations'] });
    },
  });
}
