import { useQuery } from '@tanstack/react-query';
import { paradoxApi } from '../api/paradox';

export function useParadoxes() {
  return useQuery({
    queryKey: ['paradoxes'],
    queryFn: () => paradoxApi.getActiveParadoxes(),
    refetchInterval: 10000, // Refetch every 10 seconds
  });
}
