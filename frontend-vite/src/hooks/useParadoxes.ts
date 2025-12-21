import { useQuery } from '@tanstack/react-query';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const useActiveParadoxes = () => useQuery({
  queryKey: ['paradoxes', 'active'],
  queryFn: async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/paradox/active`);
    if (!response.ok) throw new Error('Failed to fetch paradoxes');
    return response.json();
  },
  refetchInterval: 15000,      // Every 15 seconds, not 1 second
  staleTime: 10000,            // Don't refetch on UI interactions
  placeholderData: (prev) => prev,  // Keep previous data (v5 syntax for keepPreviousData)
});

// Keep the old export name for backward compatibility
export function useParadoxes() {
  return useActiveParadoxes();
}
