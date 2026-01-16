import { useQuery } from '@tanstack/react-query';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Build-time version to force cache busting
const CODE_VERSION = 'v3-20250115-15000ms';

export const useActiveParadoxes = () => {
  const REFETCH_INTERVAL = 15000;
  
  return useQuery({
    queryKey: ['paradoxes', 'active', CODE_VERSION], // Versioned queryKey
    queryFn: async () => {
      const url = `${API_BASE_URL}/api/v1/paradox/active`;
      try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Failed to fetch paradoxes: ${response.status}`);
        const data = await response.json();
        return data;
      } catch (error: any) {
        // Suppress network suspend errors (happen during page unload/navigation)
        if (error?.message?.includes('ERR_NETWORK_IO_SUSPENDED') || 
            error?.message?.includes('Failed to fetch')) {
          // Only log in development
          if (import.meta.env.DEV) {
            console.warn('[useParadoxes] Network error (backend may be down):', error.message);
          }
        }
        throw error;
      }
    },
    refetchInterval: REFETCH_INTERVAL,      // Every 15 seconds
    staleTime: 10000,            // Don't refetch on UI interactions
    placeholderData: (prev) => prev,  // Keep previous data
    retry: 2, // Retry failed requests 2 times
    retryDelay: 1000, // Wait 1 second between retries
  });
};

// Keep the old export name for backward compatibility
export function useParadoxes() {
  return useActiveParadoxes();
}
