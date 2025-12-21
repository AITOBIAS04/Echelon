import { useQuery } from '@tanstack/react-query';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const useActiveParadoxes = () => {
  // Debug: Log the refetch interval to verify it's 15 seconds
  const REFETCH_INTERVAL = 15000;
  console.log('[useParadoxes] Initializing with refetchInterval:', REFETCH_INTERVAL, 'ms (15 seconds)');
  
  return useQuery({
    queryKey: ['paradoxes', 'active'],
    queryFn: async () => {
      console.log('[useParadoxes] Fetching paradoxes from:', `${API_BASE_URL}/api/v1/paradox/active`);
      const response = await fetch(`${API_BASE_URL}/api/v1/paradox/active`);
      if (!response.ok) throw new Error('Failed to fetch paradoxes');
      return response.json();
    },
    refetchInterval: REFETCH_INTERVAL,      // Every 15 seconds, not 1 second
    staleTime: 10000,            // Don't refetch on UI interactions
    placeholderData: (prev) => prev,  // Keep previous data (v5 syntax for keepPreviousData)
  });
};

// Keep the old export name for backward compatibility
export function useParadoxes() {
  return useActiveParadoxes();
}
