import { useQuery } from '@tanstack/react-query';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Build-time version to force cache busting
const CODE_VERSION = 'v3-20250115-15000ms';

export const useActiveParadoxes = () => {
  // Debug: Log the refetch interval to verify it's 15 seconds
  const REFETCH_INTERVAL = 15000;
  
  // VERY OBVIOUS console logs that will show if new code is running
  console.log('%c[useParadoxes] ✅✅✅ NEW CODE VERSION ' + CODE_VERSION + ' ✅✅✅', 'color: green; font-size: 16px; font-weight: bold;');
  console.log('%c[useParadoxes] Refetch interval: ' + REFETCH_INTERVAL + 'ms (15 seconds)', 'color: green; font-weight: bold;');
  console.log('[useParadoxes] Using fetch() directly, NOT paradoxApi.getActiveParadoxes()');
  console.log('[useParadoxes] If you see getActiveParadoxes in stack trace, OLD CODE is running!');
  
  return useQuery({
    queryKey: ['paradoxes', 'active', CODE_VERSION], // Versioned queryKey
    queryFn: async () => {
      const url = `${API_BASE_URL}/api/v1/paradox/active`;
      const timestamp = new Date().toISOString();
      console.log('%c[useParadoxes] 🔄 FETCHING (not axios!) from:', 'color: blue; font-weight: bold;', url, 'at', timestamp);
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
