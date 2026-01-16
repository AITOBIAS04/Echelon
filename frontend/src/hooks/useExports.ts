import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  listExportJobs,
  createExportJob,
  getDatasetPreview,
} from '../api/exports';
import type {
  ExportJob,
  ExportScope,
  ExportFilter,
  ExportDatasetKind,
  DatasetPreview,
} from '../types/exports';

/**
 * useExports Hook
 * 
 * React hook for managing export jobs and dataset previews.
 * Provides jobs list, loading states, error handling, and preview caching.
 * 
 * @returns Object containing jobs, loading state, error, refresh function,
 *          createJob function, previews cache, and loadPreview function
 * 
 * @example
 * ```tsx
 * function ExportsPage() {
 *   const { jobs, loading, error, refresh, createJob, previews, loadPreview } = useExports();
 *   
 *   if (loading) return <div>Loading...</div>;
 *   if (error) return <div>Error: {error}</div>;
 *   
 *   return (
 *     <div>
 *       {jobs.map(job => <JobCard key={job.id} job={job} />)}
 *       <button onClick={() => loadPreview('rlmf')}>Preview RLMF</button>
 *     </div>
 *   );
 * }
 * ```
 */
export function useExports() {
  const queryClient = useQueryClient();
  
  // Cache for dataset previews (keyed by ExportDatasetKind)
  const [previews, setPreviews] = useState<
    Record<ExportDatasetKind, DatasetPreview | undefined>
  >({
    rlmf: undefined,
    human_judgement: undefined,
    audit_trace: undefined,
  });

  // Query for export jobs
  const {
    data: jobs = [],
    isLoading: jobsLoading,
    error: jobsError,
    refetch: refetchJobs,
  } = useQuery<ExportJob[], Error>({
    queryKey: ['exportJobs'],
    queryFn: () => listExportJobs(),
    staleTime: 10000, // 10 seconds
    refetchInterval: 30000, // 30 seconds for real-time updates
  });

  // Mutation for creating export jobs
  const createJobMutation = useMutation<
    ExportJob,
    Error,
    { scope: ExportScope; filter: ExportFilter }
  >({
    mutationFn: ({ scope, filter }) => createExportJob({ scope, filter }),
    onSuccess: () => {
      // Invalidate and refetch jobs after creating a new one
      queryClient.invalidateQueries({ queryKey: ['exportJobs'] });
    },
  });

  /**
   * Refresh export jobs list
   */
  const refresh = useCallback(async () => {
    await refetchJobs();
  }, [refetchJobs]);

  /**
   * Create a new export job
   */
  const createJob = useCallback(
    async (input: { scope: ExportScope; filter: ExportFilter }) => {
      try {
        await createJobMutation.mutateAsync(input);
      } catch (error) {
        // Error is handled by mutation state
        throw error;
      }
    },
    [createJobMutation]
  );

  /**
   * Load dataset preview for a specific kind
   * Caches the preview once loaded
   */
  const loadPreview = useCallback(
    async (kind: ExportDatasetKind) => {
      // Return cached preview if available
      if (previews[kind]) {
        return;
      }

      try {
        const preview = await getDatasetPreview(kind);
        setPreviews((prev) => ({
          ...prev,
          [kind]: preview,
        }));
      } catch (error) {
        // Error handling is done via error state
        throw error;
      }
    },
    [previews]
  );

  // Combine loading states
  const loading = jobsLoading || createJobMutation.isPending;

  // Combine error states
  const error =
    jobsError?.message ||
    createJobMutation.error?.message ||
    null;

  return {
    jobs,
    loading,
    error,
    refresh,
    createJob,
    previews,
    loadPreview,
  };
}
