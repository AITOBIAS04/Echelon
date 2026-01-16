import { useQuery } from '@tanstack/react-query';
import { getMockTimelineDetail } from '../api/mocks/timeline-detail';

/**
 * useTimelineDetail Hook
 * 
 * React Query hook for fetching timeline detail data.
 * 
 * @param timelineId - Timeline identifier
 * @returns Query result with data, isLoading, error, and refetch function
 * 
 * @example
 * ```tsx
 * function TimelineDetailPage() {
 *   const { id } = useParams();
 *   const { data, isLoading, error } = useTimelineDetail(id!);
 *   
 *   if (isLoading) return <div>Loading...</div>;
 *   if (error) return <div>Error: {error.message}</div>;
 *   
 *   return <div>{data?.name}</div>;
 * }
 * ```
 */
export function useTimelineDetail(timelineId: string | undefined) {
  return useQuery({
    queryKey: ['timeline', timelineId],
    queryFn: () => {
      if (!timelineId) {
        throw new Error('Timeline ID is required');
      }
      return getMockTimelineDetail(timelineId);
    },
    enabled: !!timelineId,
    staleTime: 10000, // 10 seconds
    refetchInterval: 30000, // 30 seconds for real-time updates
  });
}
