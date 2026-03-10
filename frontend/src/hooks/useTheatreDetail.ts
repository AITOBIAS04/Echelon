/**
 * useTheatreDetail — React Query hook for theatre detail + mutations.
 *
 * Fetches a single theatre by ID and exposes commit/run/settle mutations.
 * Also fetches commitment receipt and certificate when applicable.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { theatreApi } from '../api/theatres';
import type {
  TheatreResponse,
  CommitmentReceiptResponse,
  TheatreCertificateResponse,
} from '../types/theatre';

export function useTheatreDetail(
  theatreId: string | null,
  options?: { includeInvestigationContext?: boolean },
) {
  const queryClient = useQueryClient();

  // ── Theatre detail ──────────────────────────────────────────────────
  const theatreQuery = useQuery<TheatreResponse>({
    queryKey: ['theatre', theatreId, options?.includeInvestigationContext ? 'investigation_context' : 'base'],
    queryFn: () => theatreApi.getTheatre(theatreId!, options),
    enabled: !!theatreId,
    staleTime: 10_000,
  });

  const theatre = theatreQuery.data;

  // ── Commitment receipt (only for COMMITTED+ theatres) ───────────────
  const commitmentQuery = useQuery<CommitmentReceiptResponse>({
    queryKey: ['theatre', theatreId, 'commitment'],
    queryFn: () => theatreApi.getCommitment(theatreId!),
    enabled: !!theatreId && !!theatre?.commitment_hash,
    staleTime: 60_000, // Commitment is immutable once set
  });

  // ── Certificate (only for RESOLVED theatres) ────────────────────────
  const certificateQuery = useQuery<TheatreCertificateResponse>({
    queryKey: ['theatre', theatreId, 'certificate'],
    queryFn: () => theatreApi.getTheatreCertificate(theatreId!),
    enabled: !!theatreId && theatre?.state === 'RESOLVED',
    staleTime: 60_000, // Certificate is immutable once issued
  });

  // ── Mutations ───────────────────────────────────────────────────────

  const invalidateTheatre = () => {
    queryClient.invalidateQueries({ queryKey: ['theatre', theatreId] });
  };

  const commitMutation = useMutation({
    mutationFn: () => theatreApi.commitTheatre(theatreId!),
    onSuccess: () => {
      invalidateTheatre();
      queryClient.invalidateQueries({
        queryKey: ['theatre', theatreId, 'commitment'],
      });
    },
  });

  const runMutation = useMutation({
    mutationFn: () => theatreApi.runTheatre(theatreId!),
    onSuccess: invalidateTheatre,
  });

  const settleMutation = useMutation({
    mutationFn: () => theatreApi.settleTheatre(theatreId!),
    onSuccess: () => {
      invalidateTheatre();
      queryClient.invalidateQueries({
        queryKey: ['theatre', theatreId, 'certificate'],
      });
    },
  });

  return {
    // Data
    theatre: theatre ?? null,
    commitment: commitmentQuery.data ?? null,
    certificate: certificateQuery.data ?? null,

    // Loading states
    isLoading: theatreQuery.isLoading,
    isCommitmentLoading: commitmentQuery.isLoading,
    isCertificateLoading: certificateQuery.isLoading,

    // Errors
    error: theatreQuery.error,

    // Mutations
    commit: commitMutation.mutateAsync,
    isCommitting: commitMutation.isPending,
    run: runMutation.mutateAsync,
    isRunning: runMutation.isPending,
    settle: settleMutation.mutateAsync,
    isSettling: settleMutation.isPending,
  };
}
