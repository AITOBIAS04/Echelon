import { useQuery } from '@tanstack/react-query';
import { butterflyApi } from '../api/butterfly';

export function useWingFlaps(params?: {
  timeline_id?: string;
  agent_id?: string;
  limit?: number;
}) {
  return useQuery({
    queryKey: ['wingFlaps', params],
    queryFn: () => butterflyApi.getWingFlaps(params),
    refetchInterval: 5000, // Refetch every 5 seconds
  });
}

export function useTimelines(params?: {
  sort_by?: string;
  limit?: number;
}) {
  return useQuery({
    queryKey: ['timelines', params],
    queryFn: () => butterflyApi.getTimelineHealth(params),
    refetchInterval: 10000, // Refetch every 10 seconds
  });
}
