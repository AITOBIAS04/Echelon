import { useQuery } from '@tanstack/react-query';
import { getMockBreaches } from '../api/mocks/breaches';
import type { Breach } from '../types/breach';

/**
 * React Query hook for fetching breaches
 * 
 * Auto-refetches every 30 seconds for real-time updates
 */
export function useBreaches() {
  return useQuery<Breach[], Error>({
    queryKey: ['breaches'],
    queryFn: () => getMockBreaches(),
    staleTime: 10000, // 10 seconds
    refetchInterval: 30000, // 30 seconds for real-time feel
  });
}
