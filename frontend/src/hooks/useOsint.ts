import { useQuery } from '@tanstack/react-query';
import { osintApi, type SignalQueryParams } from '../api/osint';

export function useOsintSignals(params: SignalQueryParams = {}) {
  return useQuery({
    queryKey: ['osint', 'signals', params],
    queryFn: () => osintApi.getSignals(params),
    refetchInterval: 30_000,
    staleTime: 15_000,
  });
}

export function useOsintHealth() {
  return useQuery({
    queryKey: ['osint', 'health'],
    queryFn: () => osintApi.getHealth(),
    refetchInterval: 20_000,
    staleTime: 10_000,
  });
}

export function useOsintSummary() {
  return useQuery({
    queryKey: ['osint', 'summary'],
    queryFn: () => osintApi.getSummary(),
    refetchInterval: 30_000,
    staleTime: 15_000,
  });
}
