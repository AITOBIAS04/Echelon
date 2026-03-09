import { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  ArrowDownToLine,
  ChevronDown,
  Eye,
  Search,
  Users,
} from 'lucide-react';
import { clsx } from 'clsx';
import { useAgentRoster } from '../../hooks/useAgents';
import { useDeploymentList, useWithdrawDeployment } from '../../hooks/useAgentDeployments';
import { getArchetypeTheme } from '../../theme/agentsTheme';
import type { EnrichedAgent } from '../../hooks/useAgents';
import type { AgentDeploymentSummary } from '../../types/agentDeployment';

type AgentStatus = 'FAILED' | 'DEPLOYED' | 'IDLE';
type PageState = 'EMPTY' | 'CRITICAL' | 'HEALTHY';

function deriveStatus(agent: EnrichedAgent): AgentStatus {
  if (!agent.is_alive) return 'FAILED';
  if (agent.active_deployments_count > 0) return 'DEPLOYED';
  return 'IDLE';
}

function derivePageState(agents: EnrichedAgent[]): PageState {
  if (agents.length === 0) return 'EMPTY';
  if (agents.some((agent) => !agent.is_alive)) return 'CRITICAL';
  return 'HEALTHY';
}

function formatRelativeTime(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const totalMinutes = Math.max(0, Math.floor(diffMs / 60000));
  if (totalMinutes < 1) return 'just now';
  if (totalMinutes < 60) return `${totalMinutes}m ago`;
  const totalHours = Math.floor(totalMinutes / 60);
  if (totalHours < 24) return `${totalHours}h ago`;
  const totalDays = Math.floor(totalHours / 24);
  return `${totalDays}d ago`;
}

function latestDeploymentForAgent(
  deployments: AgentDeploymentSummary[],
): AgentDeploymentSummary | null {
  if (deployments.length === 0) return null;
  return [...deployments].sort(
    (left, right) =>
      new Date(right.created_at ?? right.deployed_at).getTime() -
      new Date(left.created_at ?? left.deployed_at).getTime(),
  )[0] ?? null;
}

function StatusCell({ status }: { status: AgentStatus }) {
  const dotClass =
    status === 'FAILED'
      ? 'bg-[var(--status-danger)] shadow-[0_0_0_2px_oklch(0.545_0.185_25_/_0.18)]'
      : status === 'DEPLOYED'
        ? 'bg-[var(--status-success)] shadow-[0_0_0_2px_oklch(0.545_0.170_152_/_0.18)]'
        : 'bg-[var(--e-text-disabled)]';
  const labelClass =
    status === 'FAILED'
      ? 'text-[var(--status-danger)]'
      : status === 'DEPLOYED'
        ? 'text-[var(--e-green-600)]'
        : 'text-[var(--e-text-disabled)]';

  return (
    <div className="flex items-center gap-2">
      <span className={clsx('inline-block h-2 w-2 rounded-full', dotClass)} />
      <span className={clsx('text-[11px] font-semibold uppercase tracking-[0.03em]', labelClass)}>
        {status === 'FAILED' ? 'Failed' : status === 'DEPLOYED' ? 'Healthy' : 'Idle'}
      </span>
    </div>
  );
}

function FleetKpi({
  label,
  value,
  breakdown,
  tone,
}: {
  label: string;
  value: number;
  breakdown?: string;
  tone?: 'success' | 'warning' | 'danger' | 'muted';
}) {
  const valueClass =
    tone === 'success'
      ? 'text-[var(--e-green-600)]'
      : tone === 'warning'
        ? 'text-[var(--e-orange-600)]'
        : tone === 'danger'
          ? 'text-[var(--e-red-600)]'
          : tone === 'muted'
            ? 'text-[var(--e-text-disabled)]'
            : 'text-[var(--e-text-primary)]';

  return (
    <div className="flex-1 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-3 shadow-[var(--e-shadow-xs)]">
      <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
        {label}
      </div>
      <div className={clsx('font-mono text-[24px] font-bold leading-8 tabular-nums', valueClass)}>
        {value}
      </div>
      {breakdown ? (
        <div className="mt-1 font-mono text-[10px] text-[var(--e-text-disabled)]">{breakdown}</div>
      ) : null}
    </div>
  );
}

function AttentionStrip({
  pageState,
  total,
  alive,
  failed,
}: {
  pageState: PageState;
  total: number;
  alive: number;
  failed: number;
}) {
  if (pageState === 'EMPTY') return null;

  const critical = pageState === 'CRITICAL';

  return (
    <div
      className={clsx(
        'mb-4 flex items-center gap-4 rounded-md px-5 py-3 text-[13px] leading-5',
        critical
          ? 'border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[color:oklch(0.545_0.185_25_/_0.06)]'
          : 'border border-[color:oklch(0.545_0.170_152_/_0.18)] bg-[color:oklch(0.545_0.170_152_/_0.06)]',
      )}
    >
      <AlertTriangle
        className={clsx(
          'h-5 w-5 shrink-0',
          critical ? 'text-[var(--status-danger)]' : 'text-[var(--e-green-600)]',
        )}
      />
      <span
        className={clsx(
          'font-semibold',
          critical ? 'text-[var(--status-danger)]' : 'text-[var(--e-green-600)]',
        )}
      >
        {critical
          ? `${failed} agent${failed === 1 ? '' : 's'} failed — requires intervention`
          : `All ${alive} agents healthy — scheduler nominal`}
      </span>
      <span className="text-[var(--e-text-secondary)]">{total} total provisioned</span>
    </div>
  );
}

function SparsePanel({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="overflow-hidden rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
      <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-2.5">
        <h3 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
          {title}
        </h3>
      </div>
      <div className="px-4 py-5 text-[12px] leading-5 text-[var(--e-text-muted)]">
        {description}
      </div>
    </div>
  );
}

function FilterSelect({
  value,
  onChange,
  options,
  label,
}: {
  value: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; label: string }>;
  label: string;
}) {
  return (
    <div className="relative">
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        aria-label={label}
        className="h-[30px] appearance-none rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 pr-8 text-[12px] font-medium text-[var(--e-text-secondary)] outline-none transition hover:border-[var(--e-purple-200)] focus:border-[var(--e-border-focus)]"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <ChevronDown className="pointer-events-none absolute right-2 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--e-text-muted)]" />
    </div>
  );
}

export function AgentRoster() {
  const navigate = useNavigate();
  const { agents, isLoading } = useAgentRoster();
  const { deployments } = useDeploymentList();
  const withdrawDeployment = useWithdrawDeployment();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [archetypeFilter, setArchetypeFilter] = useState('all');
  const [theatreFilter, setTheatreFilter] = useState('all');

  const activeDeployments = useMemo(
    () => deployments.filter((deployment) => deployment.status === 'ACTIVE'),
    [deployments],
  );

  const deploymentsByAgent = useMemo(() => {
    const grouped = new Map<string, AgentDeploymentSummary[]>();
    for (const deployment of deployments) {
      const existing = grouped.get(deployment.agent_id) ?? [];
      existing.push(deployment);
      grouped.set(deployment.agent_id, existing);
    }
    return grouped;
  }, [deployments]);

  const theatreOptions = useMemo(() => {
    const uniqueIds = [...new Set(activeDeployments.map((deployment) => deployment.theatre_id))].sort();
    return uniqueIds.map((id) => ({ value: id, label: id.slice(0, 12) }));
  }, [activeDeployments]);

  const archetypeOptions = useMemo(
    () =>
      [...new Set(agents.map((agent) => agent.archetype))].sort().map((value) => ({
        value,
        label: value,
      })),
    [agents],
  );

  const kpis = useMemo(() => {
    const total = agents.length;
    const alive = agents.filter((agent) => agent.is_alive).length;
    const deployed = agents.filter((agent) => agent.active_deployments_count > 0).length;
    const idle = agents.filter((agent) => agent.is_alive && agent.active_deployments_count === 0).length;
    const failed = agents.filter((agent) => !agent.is_alive).length;
    return { total, alive, deployed, idle, failed };
  }, [agents]);

  const pageState = derivePageState(agents);

  const filteredAgents = useMemo(() => {
    const search = searchQuery.trim().toLowerCase();
    const order: Record<AgentStatus, number> = { FAILED: 0, DEPLOYED: 1, IDLE: 2 };

    return [...agents]
      .filter((agent) => {
        const status = deriveStatus(agent);
        const agentDeployments = deploymentsByAgent.get(agent.id) ?? [];
        const deployedTo = agentDeployments.map((deployment) => deployment.theatre_id);

        if (search) {
          const haystack = `${agent.name} ${agent.archetype} ${agent.id}`.toLowerCase();
          if (!haystack.includes(search)) return false;
        }

        if (statusFilter !== 'all' && status !== statusFilter) return false;
        if (archetypeFilter !== 'all' && agent.archetype !== archetypeFilter) return false;
        if (theatreFilter !== 'all' && !deployedTo.includes(theatreFilter)) return false;

        return true;
      })
      .sort((left, right) => {
        const statusDiff = order[deriveStatus(left)] - order[deriveStatus(right)];
        if (statusDiff !== 0) return statusDiff;
        return left.name.localeCompare(right.name);
      });
  }, [agents, archetypeFilter, deploymentsByAgent, searchQuery, statusFilter, theatreFilter]);

  const archetypeDistribution = useMemo(() => {
    return archetypeOptions.map(({ value }) => {
      const count = agents.filter((agent) => agent.archetype === value).length;
      const pct = agents.length > 0 ? Math.round((count / agents.length) * 100) : 0;
      return { archetype: value, count, pct };
    });
  }, [agents, archetypeOptions]);

  const recentEvents = useMemo(() => {
    return [...deployments]
      .sort(
        (left, right) =>
          new Date(right.created_at ?? right.deployed_at).getTime() -
          new Date(left.created_at ?? left.deployed_at).getTime(),
      )
      .slice(0, 6);
  }, [deployments]);

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="mx-auto max-w-7xl animate-pulse rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-6 py-10 text-sm text-[var(--e-text-muted)] shadow-[var(--e-shadow-xs)]">
          Loading agents…
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="text-[13px] font-semibold uppercase tracking-[0.08em] text-[var(--e-text-muted)]">
              Fleet
            </div>
            <div>
              <h1 className="text-[44px] font-semibold tracking-[-0.04em] text-[var(--e-text-primary)]">
                Agents
              </h1>
              <p className="mt-2 max-w-2xl text-[16px] leading-7 text-[var(--e-text-secondary)]">
                Review provisioned operators, inspect live deployments, and route new agent deployment through known theatre context.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => navigate('/theatres')}
            className="inline-flex items-center gap-2 rounded-md border border-[var(--e-purple-500)] bg-[var(--e-purple-500)] px-4 py-2.5 text-[14px] font-semibold text-white shadow-[var(--e-shadow-sm)] transition hover:border-[var(--e-purple-600)] hover:bg-[var(--e-purple-600)]"
          >
            Deploy Agent
          </button>
        </div>

        {agents.length === 0 ? (
          <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-8 py-14 text-center shadow-[var(--e-shadow-sm)]">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] text-[var(--e-text-muted)]">
              <Users className="h-6 w-6" />
            </div>
            <h2 className="mb-2 text-[24px] font-bold tracking-[-0.02em] text-[var(--e-text-primary)]">
              No agents provisioned
            </h2>
            <p className="mx-auto max-w-xl text-[14px] leading-6 text-[var(--e-text-secondary)]">
              Fleet is empty. To deploy an agent, open a theatre detail page and use the deploy action from that known theatre context.
            </p>
          </div>
        ) : (
          <>
            <AttentionStrip
              pageState={pageState}
              total={kpis.total}
              alive={kpis.alive}
              failed={kpis.failed}
            />

            <div className="flex flex-wrap gap-3">
              <FleetKpi label="Total" value={kpis.total} />
              <FleetKpi
                label="Alive"
                value={kpis.alive}
                breakdown={`${kpis.total > 0 ? Math.round((kpis.alive / kpis.total) * 100) : 0}% alive`}
                tone={kpis.alive === kpis.total ? 'success' : undefined}
              />
              <FleetKpi
                label="Deployed"
                value={kpis.deployed}
                breakdown={`${kpis.deployed} assigned`}
                tone={kpis.deployed > 0 ? 'success' : undefined}
              />
              <FleetKpi
                label="Idle"
                value={kpis.idle}
                breakdown={`${kpis.idle} awaiting assignment`}
                tone={kpis.idle > 0 ? 'warning' : undefined}
              />
              <FleetKpi
                label="Failed"
                value={kpis.failed}
                breakdown={`${kpis.failed} intervention`}
                tone={kpis.failed > 0 ? 'danger' : 'muted'}
              />
            </div>

            <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_300px]">
              <div>
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <div className="relative">
                      <Search className="pointer-events-none absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--e-text-muted)]" />
                      <input
                        value={searchQuery}
                        onChange={(event) => setSearchQuery(event.target.value)}
                        placeholder="Search agents..."
                        className="h-[30px] w-[200px] rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] pl-8 pr-3 text-[12px] text-[var(--e-text-primary)] outline-none transition placeholder:text-[var(--e-text-muted)] focus:border-[var(--e-border-focus)]"
                      />
                    </div>
                    <FilterSelect
                      label="Status"
                      value={statusFilter}
                      onChange={setStatusFilter}
                      options={[
                        { value: 'all', label: 'All statuses' },
                        { value: 'DEPLOYED', label: 'Deployed' },
                        { value: 'IDLE', label: 'Idle' },
                        { value: 'FAILED', label: 'Failed' },
                      ]}
                    />
                    <FilterSelect
                      label="Archetype"
                      value={archetypeFilter}
                      onChange={setArchetypeFilter}
                      options={[{ value: 'all', label: 'All archetypes' }, ...archetypeOptions]}
                    />
                    <FilterSelect
                      label="Theatre"
                      value={theatreFilter}
                      onChange={setTheatreFilter}
                      options={[{ value: 'all', label: 'All theatres' }, ...theatreOptions]}
                    />
                  </div>
                  <span className="text-[12px] font-medium text-[var(--e-text-muted)]">
                    {filteredAgents.length} agent{filteredAgents.length === 1 ? '' : 's'}
                  </span>
                </div>

                <div className="overflow-hidden rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr>
                        {['Status', 'Name', 'Archetype', 'Deployed to', 'Last Action', 'P&L', 'Actions'].map(
                          (header, index) => (
                            <th
                              key={header}
                              className={clsx(
                                'bg-[var(--e-bg-sunken)] px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]',
                                index >= 5 && 'text-right',
                              )}
                            >
                              {header}
                            </th>
                          ),
                        )}
                      </tr>
                    </thead>
                    <tbody>
                      {filteredAgents.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="px-6 py-10 text-center text-[13px] text-[var(--e-text-muted)]">
                            No agents match the current filters.
                          </td>
                        </tr>
                      ) : (
                        filteredAgents.map((agent) => {
                          const status = deriveStatus(agent);
                          const agentDeployments = deploymentsByAgent.get(agent.id) ?? [];
                          const activeForAgent = agentDeployments.filter((deployment) => deployment.status === 'ACTIVE');
                          const lastDeployment = latestDeploymentForAgent(agentDeployments);
                          const archetypeTheme = getArchetypeTheme(agent.archetype);

                          return (
                            <tr
                              key={agent.id}
                              className={clsx(
                                'border-b border-[var(--e-border-secondary)] transition hover:bg-[var(--e-bg-hover)]',
                                status === 'FAILED' && 'bg-[color:oklch(0.545_0.185_25_/_0.03)]',
                              )}
                            >
                              <td className={clsx('px-3 py-2.5', status === 'FAILED' && 'shadow-[inset_3px_0_0_var(--status-danger)]')}>
                                <StatusCell status={status} />
                              </td>
                              <td className="px-3 py-2.5">
                                <Link
                                  to={`/fleet/${agent.id}`}
                                  className="font-semibold text-[var(--e-text-primary)] no-underline hover:text-[var(--e-purple-700)]"
                                >
                                  {agent.name}
                                </Link>
                              </td>
                              <td className="px-3 py-2.5">
                                <span
                                  className={clsx(
                                    'inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em]',
                                    archetypeTheme.bgClass,
                                    archetypeTheme.borderClass,
                                    archetypeTheme.textClass,
                                  )}
                                >
                                  {agent.archetype}
                                </span>
                              </td>
                              <td className="px-3 py-2.5">
                                {activeForAgent.length > 0 ? (
                                  <div className="flex flex-wrap gap-1">
                                    {activeForAgent.slice(0, 2).map((deployment) => (
                                      <span
                                        key={deployment.id}
                                        className="rounded-full border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-2 py-0.5 font-mono text-[10px] text-[var(--e-text-secondary)]"
                                      >
                                        {deployment.theatre_id.slice(0, 12)}
                                      </span>
                                    ))}
                                    {activeForAgent.length > 2 ? (
                                      <span className="rounded-full border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-2 py-0.5 font-mono text-[10px] text-[var(--e-text-secondary)]">
                                        +{activeForAgent.length - 2}
                                      </span>
                                    ) : null}
                                  </div>
                                ) : (
                                  <span className="text-[12px] text-[var(--e-text-muted)]">Undeployed</span>
                                )}
                              </td>
                              <td className="px-3 py-2.5">
                                <div className="text-[13px] text-[var(--e-text-primary)]">
                                  {status === 'FAILED'
                                    ? 'Agent heartbeat missing'
                                    : lastDeployment
                                      ? `${lastDeployment.status === 'WITHDRAWN' ? 'Recalled' : 'Deployed'} ${formatRelativeTime(lastDeployment.created_at ?? lastDeployment.deployed_at)}`
                                      : 'Awaiting assignment'}
                                </div>
                                <div className="text-[11px] text-[var(--e-text-muted)]">
                                  {lastDeployment
                                    ? lastDeployment.strategy_profile
                                    : status === 'FAILED'
                                      ? 'Intervention required'
                                      : 'No deployment events yet'}
                                </div>
                              </td>
                              <td className="px-3 py-2.5 text-right">
                                <span
                                  className={clsx(
                                    'font-mono text-[13px] font-semibold tabular-nums',
                                    agent.total_pnl_usd > 0
                                      ? 'text-[var(--e-green-600)]'
                                      : agent.total_pnl_usd < 0
                                        ? 'text-[var(--e-red-600)]'
                                        : 'text-[var(--e-text-muted)]',
                                  )}
                                >
                                  {agent.total_pnl_usd > 0 ? '+' : agent.total_pnl_usd < 0 ? '-' : ''}
                                  ${Math.abs(agent.total_pnl_usd).toLocaleString()}
                                </span>
                              </td>
                              <td className="px-3 py-2.5 text-right">
                                <div className="flex items-center justify-end gap-1.5">
                                  <Link
                                    to={`/fleet/${agent.id}`}
                                    className="inline-flex items-center gap-1 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-2.5 py-1.5 text-[11px] font-semibold text-[var(--e-text-secondary)] no-underline transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]"
                                  >
                                    <Eye className="h-3 w-3" />
                                    View
                                  </Link>
                                  {status === 'DEPLOYED' && activeForAgent[0] ? (
                                    <button
                                      type="button"
                                      onClick={() => withdrawDeployment.mutate(activeForAgent[0].id)}
                                      disabled={withdrawDeployment.isPending}
                                      className="inline-flex items-center gap-1 rounded-md px-2.5 py-1.5 text-[11px] font-semibold text-[var(--e-text-muted)] transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-red-600)]"
                                    >
                                      <ArrowDownToLine className="h-3 w-3" />
                                      Recall
                                    </button>
                                  ) : null}
                                  {status === 'IDLE' ? (
                                    <button
                                      type="button"
                                      onClick={() => navigate('/theatres')}
                                      className="inline-flex items-center gap-1 rounded-md border border-[var(--e-purple-200)] bg-[var(--e-purple-50)] px-2.5 py-1.5 text-[11px] font-semibold text-[var(--e-purple-700)] transition hover:bg-[var(--e-purple-100)]"
                                    >
                                      Deploy via Theatre
                                    </button>
                                  ) : null}
                                </div>
                              </td>
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="space-y-4">
                <SparsePanel
                  title="Scheduler Status"
                  description="No scheduler API is available yet. This panel will show queue depth, heartbeat, and cycle timing when the scheduler surface ships."
                />

                <div className="overflow-hidden rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
                  <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-2.5">
                    <h3 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                      Archetype Distribution
                    </h3>
                  </div>
                  <div className="space-y-3 px-4 py-4">
                    {archetypeDistribution.map(({ archetype, count, pct }) => {
                      const theme = getArchetypeTheme(archetype);
                      return (
                        <div key={archetype} className="flex items-center gap-2">
                          <span className={clsx('w-16 text-[11px] font-medium', theme.textClass)}>
                            {archetype}
                          </span>
                          <div className="h-2 flex-1 overflow-hidden rounded-full bg-[var(--e-bg-sunken)]">
                            <div className={clsx('h-full rounded-full', theme.bgClass)} style={{ width: `${pct}%` }} />
                          </div>
                          <span className="w-7 text-right font-mono text-[11px] text-[var(--e-text-secondary)]">
                            {count}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="overflow-hidden rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
                  <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-2.5">
                    <h3 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                      Recent Events
                    </h3>
                  </div>
                  <div className="px-4 py-3">
                    {recentEvents.length > 0 ? (
                      <div className="space-y-2">
                        {recentEvents.map((event) => (
                          <div key={event.id} className="flex items-center gap-2 text-[12px]">
                            <span
                              className={clsx(
                                'h-2 w-2 rounded-full',
                                event.status === 'WITHDRAWN'
                                  ? 'bg-[var(--e-orange-600)]'
                                  : event.status === 'PAUSED'
                                    ? 'bg-[var(--status-warning)]'
                                    : 'bg-[var(--status-success)]',
                              )}
                            />
                            <span className="min-w-0 flex-1 truncate text-[var(--e-text-primary)]">
                              {event.status === 'WITHDRAWN'
                                ? `Deployment withdrawn from ${event.theatre_id.slice(0, 12)}`
                                : event.status === 'PAUSED'
                                  ? `Deployment paused in ${event.theatre_id.slice(0, 12)}`
                                  : `Deployment active in ${event.theatre_id.slice(0, 12)}`}
                            </span>
                            <span className="font-mono text-[10px] text-[var(--e-text-muted)]">
                              {formatRelativeTime(event.created_at ?? event.deployed_at)}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-[12px] text-[var(--e-text-muted)]">
                        No deployment events yet.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default AgentRoster;
