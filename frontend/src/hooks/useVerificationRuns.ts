/**
 * useVerificationRuns — React Query hook for verification runs.
 *
 * Live mode: fetches from API with conditional polling (3s when active runs exist).
 * Demo mode: subscribes to demoStore verification slice with client-side filtering.
 */

import { useMemo, useSyncExternalStore } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { isDemoModeEnabled } from '../demo/demoMode';
import { demoStore } from '../demo/demoStore';
import {
  fetchVerificationRuns,
  createVerificationRun,
} from '../api/verification';
import type {
  RunFilters,
  VerificationRun,
  VerificationRunCreateRequest,
} from '../types/verification';

export function useVerificationRuns(filters: RunFilters = {}) {
  const isDemo = isDemoModeEnabled();
  const queryClient = useQueryClient();

  // ── Demo mode: subscribe to demoStore ──────────────────────────────
  const subscribe = useMemo(() => {
    if (!isDemo) return () => () => {};
    return (listener: () => void) => demoStore.subscribeVerification(listener);
  }, [isDemo]);

  const getSnapshot = useMemo(() => {
    if (!isDemo) return () => [] as VerificationRun[];
    return () => demoStore.getVerificationRuns() as VerificationRun[];
  }, [isDemo]);

  const allDemoRuns = useSyncExternalStore(subscribe, getSnapshot, getSnapshot);

  // ── Live mode: React Query ─────────────────────────────────────────
  const query = useQuery({
    queryKey: ['verificationRuns', filters],
    queryFn: () => fetchVerificationRuns(filters),
    enabled: !isDemo,
    staleTime: 5000,
    refetchInterval: (query) => {
      const runs = query.state.data?.runs ?? [];
      const hasActive = runs.some(
        (r: VerificationRun) => r.status !== 'COMPLETED' && r.status !== 'FAILED'
      );
      return hasActive ? 3000 : false;
    },
  });

  const createMutation = useMutation({
    mutationFn: (body: VerificationRunCreateRequest) =>
      createVerificationRun(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['verificationRuns'] });
    },
  });

  // ── Demo mode: client-side filter + paginate ───────────────────────
  if (isDemo) {
    let filtered = allDemoRuns;
    if (filters.status) {
      filtered = filtered.filter((r) => r.status === filters.status);
    }
    if (filters.construct_id) {
      const q = filters.construct_id.toLowerCase();
      filtered = filtered.filter((r) => r.construct_id.toLowerCase().includes(q));
    }
    const total = filtered.length;
    const offset = filters.offset ?? 0;
    const limit = filters.limit ?? 20;
    const paged = filtered.slice(offset, offset + limit);

    const demoCreateRun = async (body: VerificationRunCreateRequest) => {
      const run: VerificationRun = {
        run_id: `vr_${Math.random().toString(16).slice(2)}`,
        status: 'PENDING',
        progress: 0,
        total: 0,
        construct_id: body.construct_id,
        repo_url: body.repo_url,
        error: null,
        certificate_id: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      demoStore.addVerificationRun(run as any);
    };

    return {
      runs: paged,
      total,
      isLoading: false,
      error: null as Error | null,
      createRun: demoCreateRun,
      isCreating: false,
    };
  }

  return {
    runs: query.data?.runs ?? [],
    total: query.data?.total ?? 0,
    isLoading: query.isLoading,
    error: query.error,
    createRun: createMutation.mutateAsync,
    isCreating: createMutation.isPending,
  };
}
