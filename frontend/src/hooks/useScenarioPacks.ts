/**
 * useScenarioPacks — React Query hooks for scenario pack lifecycle.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { scenarioPackApi, scenarioPackLifecycleApi } from '../api/scenarioPacks';
import type { ScenarioPackCreate } from '../types/scenarioPack';

export function useTemplateList(params?: { family?: string; status?: string }) {
  const query = useQuery({
    queryKey: ['scenario-templates', params],
    queryFn: () => scenarioPackApi.listTemplates(params),
    staleTime: 30_000,
  });

  return {
    templates: query.data?.templates ?? [],
    total: query.data?.total ?? 0,
    isLoading: query.isLoading,
    error: query.error,
  };
}

export function useTemplateDetail(templateId: string | null) {
  return useQuery({
    queryKey: ['scenario-template', templateId],
    queryFn: () => scenarioPackApi.getTemplate(templateId!),
    enabled: !!templateId,
    staleTime: 60_000,
  });
}

export function useBranchProbabilities(templateId: string | null) {
  return useQuery({
    queryKey: ['branch-probabilities', templateId],
    queryFn: () => scenarioPackLifecycleApi.getBranchProbabilities(templateId!),
    enabled: !!templateId,
    staleTime: 60_000,
  });
}

export function usePackDetail(packId: string | null) {
  return useQuery({
    queryKey: ['scenario-pack', packId],
    queryFn: () => scenarioPackLifecycleApi.getPack(packId!),
    enabled: !!packId,
    staleTime: 5_000,
    refetchInterval: 10_000,
  });
}

export function useRunTree(packId: string | null, runId: string | null) {
  return useQuery({
    queryKey: ['run-tree', packId, runId],
    queryFn: () => scenarioPackLifecycleApi.getRunTree(packId!, runId!),
    enabled: !!packId && !!runId,
    staleTime: 5_000,
  });
}

export function useRunReplay(packId: string | null, runId: string | null) {
  return useQuery({
    queryKey: ['run-replay', packId, runId],
    queryFn: () => scenarioPackLifecycleApi.getReplay(packId!, runId!),
    enabled: !!packId && !!runId,
    staleTime: 30_000,
  });
}

export function useDerivedTheatres(packId: string | null) {
  return useQuery({
    queryKey: ['derived-theatres', packId],
    queryFn: () => scenarioPackLifecycleApi.getDerivedTheatres(packId!),
    enabled: !!packId,
    staleTime: 10_000,
  });
}

export function useCreatePack() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (req: ScenarioPackCreate) => scenarioPackLifecycleApi.createPack(req),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scenario-packs'] });
    },
  });
}

export function useCommitPack() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (packId: string) => scenarioPackLifecycleApi.commitPack(packId),
    onSuccess: (_data, packId) => {
      queryClient.invalidateQueries({ queryKey: ['scenario-pack', packId] });
    },
  });
}

export function useStartRun() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (packId: string) => scenarioPackLifecycleApi.startRun(packId),
    onSuccess: (_data, packId) => {
      queryClient.invalidateQueries({ queryKey: ['scenario-pack', packId] });
    },
  });
}
