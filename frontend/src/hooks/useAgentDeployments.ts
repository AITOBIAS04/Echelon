/**
 * useAgentDeployments — React Query hooks for agent deployment endpoints.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { agentDeploymentApi } from '../api/agentDeployments';
import type {
  AgentDeploymentCreate,
  StrategyProfile,
} from '../types/agentDeployment';

export function useDeploymentList(params?: {
  agent_id?: string;
  theatre_id?: string;
  status?: string;
}) {
  const query = useQuery({
    queryKey: ['agent-deployments', params],
    queryFn: () => agentDeploymentApi.list(params),
    staleTime: 10_000,
    refetchInterval: 15_000,
  });

  return {
    deployments: query.data?.deployments ?? [],
    total: query.data?.total ?? 0,
    isLoading: query.isLoading,
    error: query.error,
  };
}

export function useDeploymentDetail(deploymentId: string | null) {
  const query = useQuery({
    queryKey: ['agent-deployment', deploymentId],
    queryFn: () => agentDeploymentApi.getDetail(deploymentId!),
    enabled: !!deploymentId,
    staleTime: 5_000,
    refetchInterval: 10_000,
  });

  return {
    deployment: query.data ?? null,
    isLoading: query.isLoading,
    error: query.error,
  };
}

export function useCreateDeployment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (req: AgentDeploymentCreate) => agentDeploymentApi.create(req),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-deployments'] });
    },
  });
}

export function useWithdrawDeployment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (deploymentId: string) => agentDeploymentApi.withdraw(deploymentId),
    onSuccess: (_data, deploymentId) => {
      queryClient.invalidateQueries({ queryKey: ['agent-deployments'] });
      queryClient.invalidateQueries({ queryKey: ['agent-deployment', deploymentId] });
    },
  });
}

export function usePauseDeployment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (deploymentId: string) => agentDeploymentApi.pause(deploymentId),
    onSuccess: (_data, deploymentId) => {
      queryClient.invalidateQueries({ queryKey: ['agent-deployments'] });
      queryClient.invalidateQueries({ queryKey: ['agent-deployment', deploymentId] });
    },
  });
}

export function useResumeDeployment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (deploymentId: string) => agentDeploymentApi.resume(deploymentId),
    onSuccess: (_data, deploymentId) => {
      queryClient.invalidateQueries({ queryKey: ['agent-deployments'] });
      queryClient.invalidateQueries({ queryKey: ['agent-deployment', deploymentId] });
    },
  });
}

export function useUpdateStrategy() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ deploymentId, strategy }: { deploymentId: string; strategy: StrategyProfile }) =>
      agentDeploymentApi.updateStrategy(deploymentId, { strategy_profile: strategy }),
    onSuccess: (_data, { deploymentId }) => {
      queryClient.invalidateQueries({ queryKey: ['agent-deployments'] });
      queryClient.invalidateQueries({ queryKey: ['agent-deployment', deploymentId] });
    },
  });
}
