import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  ArrowDownToLine,
  Brain,
  Loader2,
  Pause,
  Play,
  Rocket,
  ShieldAlert,
} from 'lucide-react';
import { clsx } from 'clsx';
import { apiClient } from '../../api/client';
import {
  useDeploymentList,
  usePauseDeployment,
  useResumeDeployment,
  useWithdrawDeployment,
} from '../../hooks/useAgentDeployments';
import { EmptyState } from '../empty-states/EmptyState';
import { getArchetypeTheme } from '../../theme/agentsTheme';
import { getSanityLevel, type Agent } from '../../types/agents';
import type { AgentDeploymentSummary, DeploymentStatus } from '../../types/agentDeployment';

function formatCurrency(value: number): string {
  return `${value > 0 ? '+' : value < 0 ? '-' : ''}$${Math.abs(value).toLocaleString()}`;
}

function formatRelativeTime(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const minutes = Math.max(0, Math.floor(diffMs / 60000));
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function deploymentStatusClasses(status: DeploymentStatus): string {
  switch (status) {
    case 'ACTIVE':
      return 'border-[color:oklch(0.545_0.170_152_/_0.18)] bg-[color:oklch(0.545_0.170_152_/_0.10)] text-[var(--e-green-600)]';
    case 'PAUSED':
      return 'border-[color:oklch(0.708_0.136_62_/_0.20)] bg-[color:oklch(0.708_0.136_62_/_0.12)] text-[var(--e-orange-600)]';
    case 'WITHDRAWN':
      return 'border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] text-[var(--e-text-muted)]';
  }
}

function detailMetric(label: string, value: string, tone?: 'success' | 'danger' | 'warning') {
  const toneClass =
    tone === 'success'
      ? 'text-[var(--e-green-600)]'
      : tone === 'danger'
        ? 'text-[var(--e-red-600)]'
        : tone === 'warning'
          ? 'text-[var(--e-orange-600)]'
          : 'text-[var(--e-text-primary)]';

  return (
    <div className="rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-3 shadow-[var(--e-shadow-xs)]">
      <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
        {label}
      </div>
      <div className={clsx('font-mono text-[22px] font-bold leading-7 tabular-nums', toneClass)}>
        {value}
      </div>
    </div>
  );
}

function useAgentDetail(agentId: string | undefined) {
  return useQuery({
    queryKey: ['agent', agentId],
    queryFn: async (): Promise<Agent> => {
      const { data } = await apiClient.get<Agent>(`/api/v1/agents/${agentId}`);
      return data;
    },
    enabled: Boolean(agentId),
    refetchInterval: 30_000,
  });
}

function ActionButton({
  children,
  onClick,
  disabled,
}: {
  children: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="inline-flex items-center gap-1 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-2.5 py-1.5 text-[11px] font-semibold text-[var(--e-text-secondary)] transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)] disabled:cursor-not-allowed disabled:opacity-50"
    >
      {children}
    </button>
  );
}

function DeploymentRow({
  deployment,
  onPause,
  onResume,
  onRecall,
  busy,
}: {
  deployment: AgentDeploymentSummary;
  onPause: (deploymentId: string) => void;
  onResume: (deploymentId: string) => void;
  onRecall: (deploymentId: string) => void;
  busy: boolean;
}) {
  const eventTime = deployment.created_at ?? deployment.deployed_at;

  return (
    <div className="rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-4 shadow-[var(--e-shadow-xs)]">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="mb-2 flex items-center gap-2">
            <span
              className={clsx(
                'inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em]',
                deploymentStatusClasses(deployment.status),
              )}
            >
              {deployment.status}
            </span>
            <span className="font-mono text-[12px] text-[var(--e-text-muted)]">
              {deployment.id.slice(0, 12)}
            </span>
          </div>
          <div className="text-[14px] font-semibold text-[var(--e-text-primary)]">
            Theatre {deployment.theatre_id.slice(0, 12)}
          </div>
          <div className="mt-1 text-[12px] text-[var(--e-text-secondary)]">
            Strategy {deployment.strategy_profile} · updated {formatRelativeTime(eventTime)}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {deployment.status === 'ACTIVE' ? (
            <ActionButton onClick={() => onPause(deployment.id)} disabled={busy}>
              <Pause className="h-3 w-3" />
              Pause
            </ActionButton>
          ) : null}
          {deployment.status === 'PAUSED' ? (
            <ActionButton onClick={() => onResume(deployment.id)} disabled={busy}>
              <Play className="h-3 w-3" />
              Resume
            </ActionButton>
          ) : null}
          {deployment.status !== 'WITHDRAWN' ? (
            <ActionButton onClick={() => onRecall(deployment.id)} disabled={busy}>
              <ArrowDownToLine className="h-3 w-3" />
              Recall
            </ActionButton>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export function AgentDetail() {
  const { agentId } = useParams();
  const { data: agent, isLoading: agentLoading, error } = useAgentDetail(agentId);
  const { deployments, isLoading: deploymentsLoading } = useDeploymentList(
    agentId ? { agent_id: agentId } : undefined,
  );
  const withdrawDeployment = useWithdrawDeployment();
  const pauseDeployment = usePauseDeployment();
  const resumeDeployment = useResumeDeployment();

  const activeDeployments = useMemo(
    () => deployments.filter((deployment) => deployment.status !== 'WITHDRAWN'),
    [deployments],
  );
  const historicalDeployments = useMemo(
    () => deployments.filter((deployment) => deployment.status === 'WITHDRAWN'),
    [deployments],
  );

  if (!agentId) {
    return (
      <div className="p-6">
        <div className="mx-auto max-w-5xl rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-6 py-10 text-sm text-[var(--e-text-muted)] shadow-[var(--e-shadow-xs)]">
          No agent selected.
        </div>
      </div>
    );
  }

  if (agentLoading) {
    return (
      <div className="p-6">
        <div className="mx-auto flex max-w-5xl items-center justify-center rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-6 py-16 text-sm text-[var(--e-text-muted)] shadow-[var(--e-shadow-xs)]">
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Loading agent profile…
        </div>
      </div>
    );
  }

  if (error || !agent) {
    return (
      <div className="p-6">
        <div className="mx-auto max-w-5xl rounded-md border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] px-6 py-10 text-sm text-[var(--e-red-600)] shadow-[var(--e-shadow-xs)]">
          Failed to load agent detail.
        </div>
      </div>
    );
  }

  const archetypeTheme = getArchetypeTheme(agent.archetype);
  const sanityLevel = getSanityLevel(agent.sanity, agent.max_sanity);
  const busy =
    withdrawDeployment.isPending || pauseDeployment.isPending || resumeDeployment.isPending;

  return (
    <div className="p-6">
      <div className="mx-auto max-w-6xl">
        <Link
          to="/fleet"
          className="mb-5 inline-flex items-center gap-2 text-[12px] font-medium text-[var(--e-text-muted)] no-underline transition hover:text-[var(--e-text-primary)]"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Fleet
        </Link>

        <div className="mb-6 overflow-hidden rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-sm)]">
          <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-6 py-4">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div
                  className={clsx(
                    'flex h-11 w-11 items-center justify-center rounded-xl border',
                    archetypeTheme.borderClass,
                    archetypeTheme.bgClass,
                  )}
                >
                  <Brain className={clsx('h-5 w-5', archetypeTheme.textClass)} />
                </div>
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h1 className="text-[28px] font-bold tracking-[-0.02em] text-[var(--e-text-primary)]">
                      {agent.name}
                    </h1>
                    <span
                      className={clsx(
                        'inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em]',
                        archetypeTheme.borderClass,
                        archetypeTheme.bgClass,
                        archetypeTheme.textClass,
                      )}
                    >
                      {agent.archetype}
                    </span>
                    {!agent.is_alive ? (
                      <span className="inline-flex items-center rounded-full border border-[color:oklch(0.545_0.185_25_/_0.22)] bg-[var(--e-red-50)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-red-600)]">
                        Intervention Required
                      </span>
                    ) : null}
                  </div>
                  <div className="mt-1 font-mono text-[11px] text-[var(--e-text-muted)]">
                    ID {agent.id} · Tier {agent.tier} · Level {agent.level}
                  </div>
                </div>
              </div>

              <div className="text-right">
                <div
                  className={clsx(
                    'font-mono text-[24px] font-bold tabular-nums',
                    agent.total_pnl_usd > 0
                      ? 'text-[var(--e-green-600)]'
                      : agent.total_pnl_usd < 0
                        ? 'text-[var(--e-red-600)]'
                        : 'text-[var(--e-text-primary)]',
                  )}
                >
                  {formatCurrency(agent.total_pnl_usd)}
                </div>
                <div className="text-[11px] text-[var(--e-text-muted)]">Total P&amp;L</div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-3 px-6 py-5 sm:grid-cols-2 xl:grid-cols-5">
            {detailMetric('Win Rate', `${Math.round(agent.win_rate * 100)}%`, agent.win_rate >= 0.6 ? 'success' : undefined)}
            {detailMetric('Trades', agent.trades_count.toLocaleString())}
            {detailMetric('Active Deployments', agent.active_deployments_count.toString(), agent.active_deployments_count > 0 ? 'success' : undefined)}
            {detailMetric('Sanity', `${agent.sanity}/${agent.max_sanity}`, sanityLevel === 'breakdown' ? 'danger' : sanityLevel === 'critical' ? 'warning' : 'success')}
            {detailMetric('Heartbeat', agent.is_alive ? 'Alive' : 'Lost', agent.is_alive ? 'success' : 'danger')}
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_320px]">
          <div className="space-y-4">
            <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
              <div className="flex items-center justify-between border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-3">
                <div className="flex items-center gap-2">
                  <Rocket className="h-4 w-4 text-[var(--e-purple-500)]" />
                  <h2 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                    Active Deployments
                  </h2>
                </div>
                <span className="font-mono text-[11px] text-[var(--e-text-muted)]">
                  {activeDeployments.length} active
                </span>
              </div>

              <div className="space-y-3 px-5 py-5">
                {deploymentsLoading ? (
                  <div className="flex items-center justify-center py-8 text-[var(--e-text-muted)]">
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Loading deployments…
                  </div>
                ) : activeDeployments.length > 0 ? (
                  activeDeployments.map((deployment) => (
                    <DeploymentRow
                      key={deployment.id}
                      deployment={deployment}
                      onPause={(deploymentId) => pauseDeployment.mutate(deploymentId)}
                      onResume={(deploymentId) => resumeDeployment.mutate(deploymentId)}
                      onRecall={(deploymentId) => withdrawDeployment.mutate(deploymentId)}
                      busy={busy}
                    />
                  ))
                ) : (
                  <EmptyState
                    type="ZERO_STATE"
                    icon={<Rocket className="h-5 w-5" />}
                    title="No active deployments"
                    description="This agent is not currently assigned to a theatre. Deploy from a theatre detail page where the theatre context is already known."
                    className="min-h-0 py-8"
                  />
                )}
              </div>
            </section>

            <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
              <div className="flex items-center justify-between border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-3">
                <div className="flex items-center gap-2">
                  <ArrowDownToLine className="h-4 w-4 text-[var(--e-text-muted)]" />
                  <h2 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                    Deployment History
                  </h2>
                </div>
                <span className="font-mono text-[11px] text-[var(--e-text-muted)]">
                  {historicalDeployments.length} withdrawn
                </span>
              </div>

              <div className="space-y-3 px-5 py-5">
                {historicalDeployments.length > 0 ? (
                  historicalDeployments.map((deployment) => (
                    <DeploymentRow
                      key={deployment.id}
                      deployment={deployment}
                      onPause={() => undefined}
                      onResume={() => undefined}
                      onRecall={() => undefined}
                      busy
                    />
                  ))
                ) : (
                  <div className="rounded-md border border-dashed border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-5 text-[12px] text-[var(--e-text-muted)]">
                    No withdrawn deployments yet.
                  </div>
                )}
              </div>
            </section>
          </div>

          <aside className="space-y-4">
            <div className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
              <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-3">
                <h2 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                  Deployment Readiness
                </h2>
              </div>
              <div className="space-y-3 px-5 py-5 text-[12px] leading-5 text-[var(--e-text-secondary)]">
                <div className="flex items-start gap-2">
                  <span className={clsx('mt-1 h-2.5 w-2.5 rounded-full', agent.is_alive ? 'bg-[var(--e-green-600)]' : 'bg-[var(--e-red-600)]')} />
                  <div>
                    <div className="font-semibold text-[var(--e-text-primary)]">Heartbeat</div>
                    <div>{agent.is_alive ? 'Agent responding to heartbeat checks.' : 'Agent is not responding and requires intervention.'}</div>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <span className={clsx('mt-1 h-2.5 w-2.5 rounded-full', sanityLevel === 'breakdown' ? 'bg-[var(--e-red-600)]' : sanityLevel === 'critical' ? 'bg-[var(--e-orange-600)]' : 'bg-[var(--e-green-600)]')} />
                  <div>
                    <div className="font-semibold text-[var(--e-text-primary)]">Sanity window</div>
                    <div>
                      {sanityLevel === 'breakdown'
                        ? 'Below safe deployment threshold.'
                        : sanityLevel === 'critical'
                          ? 'Operational but at elevated risk.'
                          : 'Within acceptable deployment range.'}
                    </div>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <span className="mt-1 h-2.5 w-2.5 rounded-full bg-[var(--e-purple-500)]" />
                  <div>
                    <div className="font-semibold text-[var(--e-text-primary)]">Theatre target</div>
                    <div>Generic Fleet deployment remains constrained until a theatre list endpoint exists. Deploy from theatre detail when the target is known.</div>
                  </div>
                </div>
              </div>
            </div>

            {!agent.is_alive ? (
              <div className="rounded-lg border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] px-5 py-4 shadow-[var(--e-shadow-xs)]">
                <div className="flex items-start gap-3">
                  <ShieldAlert className="mt-0.5 h-5 w-5 text-[var(--e-red-600)]" />
                  <div>
                    <div className="text-[13px] font-semibold text-[var(--e-red-600)]">
                      Intervention required
                    </div>
                    <div className="mt-1 text-[12px] leading-5 text-[var(--e-red-600)]/85">
                      Restart and decommission actions are not available in the current backend. Use this page for visibility until those controls ship.
                    </div>
                  </div>
                </div>
              </div>
            ) : null}
          </aside>
        </div>
      </div>
    </div>
  );
}

export default AgentDetail;
