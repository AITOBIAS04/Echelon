import { useQuery } from '@tanstack/react-query';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const useActiveParadoxes = () => {
  // Debug: Log the refetch interval to verify it's 15 seconds
  const REFETCH_INTERVAL = 15000;
  console.log('[useParadoxes] ✅ NEW CODE LOADED - refetchInterval:', REFETCH_INTERVAL, 'ms (15 seconds)');
  console.log('[useParadoxes] Using fetch() directly, NOT paradoxApi.getActiveParadoxes()');
  
  return useQuery({
    queryKey: ['paradoxes', 'active', 'v2'], // Changed queryKey to force new query
    queryFn: async () => {
      const url = `${API_BASE_URL}/api/v1/paradox/active`;
      console.log('[useParadoxes] 🔄 Fetching from:', url, 'at', new Date().toISOString());
      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch paradoxes');
      const data = await response.json();
      console.log('[useParadoxes] ✅ Received', data?.paradoxes?.length || 0, 'paradoxes');
      return data;
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
