import { useQuery } from '@tanstack/react-query';
import { paradoxApi } from '../api/paradox';

export function useParadoxes() {
  return useQuery({
    queryKey: ['paradoxes'],
    queryFn: () => paradoxApi.getActiveParadoxes(),
    refetchInterval: 1000, // Refetch every second for countdown
  });
}
