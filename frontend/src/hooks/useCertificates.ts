/**
 * useCertificates — React Query hooks for verification certificates.
 *
 * Live mode: fetches from API with 30s stale time.
 * Demo mode: subscribes to demoStore verification slice with client-side sort/filter.
 */

import { useMemo, useSyncExternalStore } from 'react';
import { useQuery } from '@tanstack/react-query';
import { isDemoModeEnabled } from '../demo/demoMode';
import { demoStore } from '../demo/demoStore';
import { fetchCertificates, fetchCertificate } from '../api/verification';
import type {
  CertFilters,
  CertificateSummary,
  Certificate,
} from '../types/verification';

export function useCertificates(filters: CertFilters = {}) {
  const isDemo = isDemoModeEnabled();

  // ── Demo mode: subscribe to demoStore ──────────────────────────────
  const subscribe = useMemo(() => {
    if (!isDemo) return () => () => {};
    return (listener: () => void) => demoStore.subscribeVerification(listener);
  }, [isDemo]);

  const getSnapshot = useMemo(() => {
    if (!isDemo) return () => [] as CertificateSummary[];
    return () => demoStore.getCertificates() as unknown as CertificateSummary[];
  }, [isDemo]);

  const allDemoCerts = useSyncExternalStore(subscribe, getSnapshot, getSnapshot);

  // ── Live mode: React Query ─────────────────────────────────────────
  const query = useQuery({
    queryKey: ['certificates', filters],
    queryFn: () => fetchCertificates(filters),
    enabled: !isDemo,
    staleTime: 30000,
  });

  if (isDemo) {
    let filtered = [...allDemoCerts];

    // Filter by construct_id
    if (filters.construct_id) {
      const q = filters.construct_id.toLowerCase();
      filtered = filtered.filter((c) => c.construct_id.toLowerCase().includes(q));
    }

    // Sort
    if (filters.sort === 'created_desc') {
      filtered.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    } else {
      // Default: brier_asc
      filtered.sort((a, b) => a.brier - b.brier);
    }

    const total = filtered.length;
    const offset = filters.offset ?? 0;
    const limit = filters.limit ?? 20;
    const paged = filtered.slice(offset, offset + limit);

    return {
      certificates: paged,
      total,
      isLoading: false,
      error: null as Error | null,
    };
  }

  return {
    certificates: query.data?.certificates ?? [],
    total: query.data?.total ?? 0,
    isLoading: query.isLoading,
    error: query.error,
  };
}

export function useCertificateDetail(certId: string | null) {
  const isDemo = isDemoModeEnabled();

  // ── Demo mode: find cert in demoStore ──────────────────────────────
  const subscribe = useMemo(() => {
    if (!isDemo) return () => () => {};
    return (listener: () => void) => demoStore.subscribeVerification(listener);
  }, [isDemo]);

  const getSnapshot = useMemo(() => {
    if (!isDemo || !certId) return () => undefined as Certificate | undefined;
    return () => {
      const certs = demoStore.getCertificates();
      return (certs.find((c) => c.id === certId) as unknown as Certificate) ?? undefined;
    };
  }, [isDemo, certId]);

  const demoCert = useSyncExternalStore(subscribe, getSnapshot, getSnapshot);

  // ── Live mode: React Query ─────────────────────────────────────────
  const query = useQuery({
    queryKey: ['certificate', certId],
    queryFn: () => fetchCertificate(certId!),
    enabled: !isDemo && !!certId,
  });

  if (isDemo) {
    return {
      certificate: demoCert,
      isLoading: false,
      error: null as Error | null,
    };
  }

  return {
    certificate: query.data ?? undefined,
    isLoading: query.isLoading,
    error: query.error,
  };
}
