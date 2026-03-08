/**
 * AgentRoster — Fleet page with roster table, KPI cards, attention strip, right rail.
 *
 * Surfaces real agent + deployment data from:
 *   GET /api/v1/agents           — roster with active_deployments_count
 *   GET /api/v1/agent-deployments — deployment list with filters
 *
 * Design ref: echelon_fleet_v1.html
 *
 * Backend limitations surfaced honestly:
 *   - No theatre list endpoint — Fleet-page deploy shows unavailable modal
 *   - No scheduler API — Scheduler panel deferred
 *   - No restart/decommission endpoints — Failed row actions deferred
 *   - No "degraded" signal — status derived from is_alive + deployments only
 */

import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  User,
  Search,
  Users,
  Activity,
  Heart,
  Rocket,
  Clock,
  AlertTriangle,
  ChevronDown,
  Eye,
  ArrowDownToLine,
} from 'lucide-react';
import { useAgentRoster } from '../../hooks/useAgents';
import { useDeploymentList, useWithdrawDeployment } from '../../hooks/useAgentDeployments';
import { DeployAgentModal } from './DeployAgentModal';
import { useRegisterTopActionBarActions } from '../../contexts/TopActionBarActionsContext';
import { useAgentsUi } from '../../contexts/AgentsUiContext';
import { LocalErrorBoundary } from '../common/LocalErrorBoundary';
import { EmptyState } from '../empty-states/EmptyState';
import { clsx } from 'clsx';
import { getArchetypeTheme } from '../../theme/agentsTheme';
import type { EnrichedAgent } from '../../hooks/useAgents';

// ── Derived agent status from backend truth ──────────────────────────

type AgentStatus = 'FAILED' | 'DEPLOYED' | 'IDLE';

function deriveStatus(agent: EnrichedAgent): AgentStatus {
  if (!agent.is_alive) return 'FAILED';
  if (agent.active_deployments_count > 0) return 'DEPLOYED';
  return 'IDLE';
}

function statusDot(status: AgentStatus): string {
  switch (status) {
    case 'FAILED': return 'bg-status-failure';
    case 'DEPLOYED': return 'bg-status-success';
    case 'IDLE': return 'bg-terminal-text-muted';
  }
}

function statusLabel(status: AgentStatus): string {
  switch (status) {
    case 'FAILED': return 'Failed';
    case 'DEPLOYED': return 'Healthy';
    case 'IDLE': return 'Idle';
  }
}

// ── Page state machine (design ref) ──────────────────────────────────

type PageState = 'EMPTY' | 'CRITICAL' | 'HEALTHY';

function derivePageState(agents: EnrichedAgent[]): PageState {
  if (agents.length === 0) return 'EMPTY';
  if (agents.some(a => !a.is_alive)) return 'CRITICAL';
  return 'HEALTHY';
}

// ── Component ────────────────────────────────────────────────────────

export function AgentRoster() {
  const { agents, isLoading } = useAgentRoster();
  const { deployments } = useDeploymentList({ status: 'ACTIVE' });
  const withdrawDeployment = useWithdrawDeployment();
  const [deployModalOpen, setDeployModalOpen] = useState(false);
  const { activeTab, setActiveTab } = useAgentsUi();

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [archetypeFilter, setArchetypeFilter] = useState<string>('all');

  // Register TopActionBar action handlers
  useRegisterTopActionBarActions({
    agentRoster: () => setActiveTab('roster'),
    globalIntel: () => setActiveTab('intel'),
    deployAgent: () => setDeployModalOpen(true),
  });

  // Build deployment lookup: agent_id → theatre_ids
  const deploymentsByAgent = useMemo(() => {
    const map = new Map<string, Array<{ id: string; theatre_id: string; strategy_profile: string }>>();
    for (const d of deployments) {
      const list = map.get(d.agent_id) ?? [];
      list.push({ id: d.id, theatre_id: d.theatre_id, strategy_profile: d.strategy_profile });
      map.set(d.agent_id, list);
    }
    return map;
  }, [deployments]);

  // Derive KPI stats from real data
  const kpis = useMemo(() => {
    const total = agents.length;
    const alive = agents.filter(a => a.is_alive).length;
    const deployed = agents.filter(a => a.is_alive && a.active_deployments_count > 0).length;
    const idle = agents.filter(a => a.is_alive && a.active_deployments_count === 0).length;
    const failed = agents.filter(a => !a.is_alive).length;
    return { total, alive, deployed, idle, failed };
  }, [agents]);

  const pageState = useMemo(() => derivePageState(agents), [agents]);

  // Archetype distribution for right rail
  const archetypeDistribution = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const a of agents) {
      counts[a.archetype] = (counts[a.archetype] || 0) + 1;
    }
    return Object.entries(counts)
      .map(([archetype, count]) => ({ archetype, count, pct: agents.length > 0 ? Math.round((count / agents.length) * 100) : 0 }))
      .sort((a, b) => b.count - a.count);
  }, [agents]);

  // Filter agents
  const filteredAgents = useMemo(() => {
    let result = [...agents];

    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      result = result.filter(a => a.name.toLowerCase().includes(q) || a.archetype.toLowerCase().includes(q));
    }

    if (statusFilter !== 'all') {
      result = result.filter(a => deriveStatus(a) === statusFilter);
    }

    if (archetypeFilter !== 'all') {
      result = result.filter(a => a.archetype === archetypeFilter);
    }

    // Sort: failed first, then deployed, then idle
    const order: Record<AgentStatus, number> = { FAILED: 0, DEPLOYED: 1, IDLE: 2 };
    result.sort((a, b) => order[deriveStatus(a)] - order[deriveStatus(b)]);

    return result;
  }, [agents, searchQuery, statusFilter, archetypeFilter]);

  // Unique archetypes for filter
  const archetypes = useMemo(
    () => [...new Set(agents.map(a => a.archetype))].sort(),
    [agents],
  );

  const handleRecall = (deploymentId: string) => {
    withdrawDeployment.mutate(deploymentId);
  };

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-terminal-text-muted animate-pulse text-sm">Loading fleet...</div>
      </div>
    );
  }

  if (agents.length === 0) {
    return (
      <EmptyState
        type="ZERO_STATE"
        icon={<User className="w-7 h-7" />}
        title="No agents provisioned"
        description="Agents appear here once provisioned. To deploy an agent, open a theatre detail page and use the Deploy Agent action — the theatre context is required."
      />
    );
  }

  return (
    <div
      className="h-full flex flex-col"
      data-testid={activeTab === 'roster' ? 'agents-tab-roster' : 'agents-tab-intel'}
    >
      {/* ── Roster Tab ─────────────────────────────────────────────── */}
      {activeTab === 'roster' && (
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto">

            {/* ── Attention Strip ──────────────────────────────────── */}
            <AttentionStrip pageState={pageState} kpis={kpis} />

            {/* ── KPI Cards ────────────────────────────────────────── */}
            <div className="flex gap-3 mb-4">
              <KpiCard label="Total" value={kpis.total} />
              <KpiCard label="Alive" value={kpis.alive} total={kpis.total} variant={kpis.alive === kpis.total ? 'success' : undefined} />
              <KpiCard label="Deployed" value={kpis.deployed} />
              <KpiCard label="Idle" value={kpis.idle} variant={kpis.idle > 0 ? 'warning' : undefined} />
              <KpiCard label="Failed" value={kpis.failed} variant={kpis.failed > 0 ? 'danger' : 'zero'} />
            </div>

            {/* ── Main Grid: Table + Right Rail ────────────────────── */}
            <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-4">
              {/* Left: Filter + Table */}
              <div>
                {/* Filter bar */}
                <div className="flex items-center gap-3 mb-3">
                  <div className="relative flex-1 max-w-xs">
                    <Search className="w-3.5 h-3.5 text-terminal-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Search agents..."
                      className="w-full h-8 pl-9 pr-3 bg-terminal-bg border border-terminal-border rounded-lg text-xs text-terminal-text placeholder:text-terminal-text-muted focus:border-echelon-cyan/40 outline-none"
                    />
                  </div>
                  <FilterDropdown
                    label="Status"
                    value={statusFilter}
                    onChange={setStatusFilter}
                    options={[
                      { value: 'all', label: 'All' },
                      { value: 'DEPLOYED', label: 'Deployed' },
                      { value: 'IDLE', label: 'Idle' },
                      { value: 'FAILED', label: 'Failed' },
                    ]}
                  />
                  <FilterDropdown
                    label="Archetype"
                    value={archetypeFilter}
                    onChange={setArchetypeFilter}
                    options={[
                      { value: 'all', label: 'All' },
                      ...archetypes.map(a => ({ value: a, label: a })),
                    ]}
                  />
                  <span className="text-xs text-terminal-text-muted ml-auto">
                    {filteredAgents.length} agent{filteredAgents.length !== 1 ? 's' : ''}
                  </span>
                </div>

                {/* Roster Table */}
                <div className="bg-terminal-panel border border-terminal-border rounded-lg overflow-hidden">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-terminal-border bg-terminal-surface">
                        <th className="text-left px-4 py-2.5 font-semibold text-terminal-text-muted uppercase tracking-wider text-[10px]">Status</th>
                        <th className="text-left px-4 py-2.5 font-semibold text-terminal-text-muted uppercase tracking-wider text-[10px]">Name</th>
                        <th className="text-left px-4 py-2.5 font-semibold text-terminal-text-muted uppercase tracking-wider text-[10px]">Archetype</th>
                        <th className="text-left px-4 py-2.5 font-semibold text-terminal-text-muted uppercase tracking-wider text-[10px]">Deployed To</th>
                        <th className="text-left px-4 py-2.5 font-semibold text-terminal-text-muted uppercase tracking-wider text-[10px]">P&L</th>
                        <th className="text-right px-4 py-2.5 font-semibold text-terminal-text-muted uppercase tracking-wider text-[10px]">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredAgents.length === 0 ? (
                        <tr>
                          <td colSpan={6} className="py-8">
                            <EmptyState
                              type="NO_RESULTS"
                              filterDescription={searchQuery || statusFilter !== 'all' ? `${searchQuery} ${statusFilter}` : undefined}
                              onClearFilters={() => { setSearchQuery(''); setStatusFilter('all'); setArchetypeFilter('all'); }}
                            />
                          </td>
                        </tr>
                      ) : (
                        filteredAgents.map((agent) => {
                          const status = deriveStatus(agent);
                          const agentDeployments = deploymentsByAgent.get(agent.id) ?? [];

                          return (
                            <tr
                              key={agent.id}
                              className="border-b border-terminal-border/50 hover:bg-terminal-card/50 transition-colors"
                            >
                              {/* Status */}
                              <td className="px-4 py-3">
                                <div className="flex items-center gap-2">
                                  <span className={clsx('w-2 h-2 rounded-full', statusDot(status))} />
                                  <span className={clsx(
                                    'text-[10px] font-semibold uppercase',
                                    status === 'FAILED' && 'text-status-failure',
                                    status === 'DEPLOYED' && 'text-status-success',
                                    status === 'IDLE' && 'text-terminal-text-muted',
                                  )}>
                                    {statusLabel(status)}
                                  </span>
                                </div>
                              </td>

                              {/* Name */}
                              <td className="px-4 py-3">
                                <Link
                                  to={`/fleet/${agent.id}`}
                                  className="font-semibold text-terminal-text hover:text-echelon-cyan transition-colors"
                                >
                                  {agent.name}
                                </Link>
                              </td>

                              {/* Archetype */}
                              <td className="px-4 py-3">
                                <span className={clsx(
                                  'inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-semibold',
                                  getArchetypeTheme(agent.archetype).bgClass,
                                  getArchetypeTheme(agent.archetype).textClass,
                                )}>
                                  {agent.archetype}
                                </span>
                              </td>

                              {/* Deployed To */}
                              <td className="px-4 py-3">
                                {agentDeployments.length > 0 ? (
                                  <div className="flex flex-wrap gap-1">
                                    {agentDeployments.map(d => (
                                      <span key={d.id} className="font-mono text-[10px] text-echelon-cyan bg-echelon-cyan/10 px-1.5 py-0.5 rounded">
                                        {d.theatre_id.slice(0, 8)}
                                      </span>
                                    ))}
                                  </div>
                                ) : (
                                  <span className="text-terminal-text-muted">—</span>
                                )}
                              </td>

                              {/* P&L */}
                              <td className="px-4 py-3">
                                <span className={clsx(
                                  'font-mono font-semibold',
                                  agent.total_pnl_usd >= 0 ? 'text-status-success' : 'text-status-failure',
                                )}>
                                  {agent.total_pnl_usd >= 0 ? '+' : ''}${Math.abs(agent.total_pnl_usd).toLocaleString()}
                                </span>
                              </td>

                              {/* Actions */}
                              <td className="px-4 py-3 text-right">
                                <div className="flex items-center gap-1.5 justify-end">
                                  <Link
                                    to={`/fleet/${agent.id}`}
                                    className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-semibold bg-terminal-surface border border-terminal-border text-terminal-text-muted hover:text-terminal-text hover:border-terminal-text-muted transition-colors"
                                  >
                                    <Eye className="w-3 h-3" />
                                    View
                                  </Link>
                                  {status === 'DEPLOYED' && agentDeployments.length > 0 && (
                                    <button
                                      onClick={() => handleRecall(agentDeployments[0].id)}
                                      disabled={withdrawDeployment.isPending}
                                      className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-semibold text-terminal-text-muted hover:text-status-failure hover:bg-status-failure/10 transition-colors"
                                    >
                                      <ArrowDownToLine className="w-3 h-3" />
                                      Recall
                                    </button>
                                  )}
                                  {status === 'IDLE' && (
                                    <span
                                      className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-semibold text-terminal-text-muted/50 cursor-not-allowed"
                                      title="Deploy from a theatre detail page where theatre_id is known"
                                    >
                                      <Rocket className="w-3 h-3" />
                                      Deploy
                                    </span>
                                  )}
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

              {/* ── Right Rail ───────────────────────────────────────── */}
              <div className="space-y-4">
                {/* Scheduler Status — deferred (no API) */}
                <div className="bg-terminal-panel border border-terminal-border rounded-lg overflow-hidden">
                  <div className="px-4 py-2.5 border-b border-terminal-border/50 bg-terminal-surface">
                    <h3 className="text-[10px] font-bold uppercase tracking-wider text-terminal-text-muted">
                      Scheduler Status
                    </h3>
                  </div>
                  <div className="p-4">
                    <div className="text-xs text-terminal-text-muted text-center py-4">
                      No scheduler API available
                    </div>
                  </div>
                </div>

                {/* Archetype Distribution — real data */}
                <div className="bg-terminal-panel border border-terminal-border rounded-lg overflow-hidden">
                  <div className="px-4 py-2.5 border-b border-terminal-border/50 bg-terminal-surface">
                    <h3 className="text-[10px] font-bold uppercase tracking-wider text-terminal-text-muted">
                      Archetype Distribution
                    </h3>
                  </div>
                  <div className="p-4 space-y-2">
                    {archetypeDistribution.length > 0 ? (
                      archetypeDistribution.map(({ archetype, count, pct }) => (
                        <div key={archetype} className="flex items-center gap-2">
                          <span className={clsx(
                            'text-[10px] font-mono font-semibold w-16',
                            getArchetypeTheme(archetype).textClass,
                          )}>
                            {archetype}
                          </span>
                          <div className="flex-1 h-2 bg-terminal-bg rounded-full overflow-hidden">
                            <div
                              className={clsx('h-full rounded-full', getArchetypeTheme(archetype).bgClass)}
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                          <span className="text-[10px] font-mono text-terminal-text-muted w-6 text-right">
                            {count}
                          </span>
                        </div>
                      ))
                    ) : (
                      <div className="text-xs text-terminal-text-muted text-center py-2">No agents</div>
                    )}
                  </div>
                </div>

                {/* Recent Events Feed — deferred without WebSocket */}
                <div className="bg-terminal-panel border border-terminal-border rounded-lg overflow-hidden">
                  <div className="px-4 py-2.5 border-b border-terminal-border/50 bg-terminal-surface">
                    <h3 className="text-[10px] font-bold uppercase tracking-wider text-terminal-text-muted">
                      Recent Events
                    </h3>
                  </div>
                  <div className="p-4">
                    <EmptyState
                      type="SPARSE_DATA"
                      description="Event feed requires WebSocket integration. Deployment actions are polled every 15s."
                      className="min-h-0 bg-transparent p-0"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Intelligence Tab — Real data with sparse states ──────── */}
      {activeTab === 'intel' && (
        <LocalErrorBoundary name="Global Intelligence">
          <div className="flex-1 overflow-y-auto p-6">
            <div className="max-w-7xl mx-auto">
              {/* KPI row from real data */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Users className="w-4 h-4 text-terminal-text-muted" />
                    <span className="text-[10px] font-bold uppercase tracking-wider text-terminal-text-muted">Total</span>
                  </div>
                  <div className="text-2xl font-bold font-mono text-terminal-text">{kpis.total}</div>
                </div>
                <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Rocket className="w-4 h-4 text-terminal-text-muted" />
                    <span className="text-[10px] font-bold uppercase tracking-wider text-terminal-text-muted">Deployed</span>
                  </div>
                  <div className="text-2xl font-bold font-mono text-terminal-text">{kpis.deployed}</div>
                  <div className="text-[10px] text-terminal-text-muted">
                    {kpis.total > 0 ? Math.round((kpis.deployed / kpis.total) * 100) : 0}% utilization
                  </div>
                </div>
                <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Clock className="w-4 h-4 text-terminal-text-muted" />
                    <span className="text-[10px] font-bold uppercase tracking-wider text-terminal-text-muted">Idle</span>
                  </div>
                  <div className="text-2xl font-bold font-mono text-terminal-text">{kpis.idle}</div>
                </div>
                <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertTriangle className="w-4 h-4 text-terminal-text-muted" />
                    <span className="text-[10px] font-bold uppercase tracking-wider text-terminal-text-muted">Failed</span>
                  </div>
                  <div className={clsx('text-2xl font-bold font-mono', kpis.failed > 0 ? 'text-status-failure' : 'text-terminal-text')}>
                    {kpis.failed}
                  </div>
                </div>
              </div>

              {/* Deployment Heat Map — sparse state (no theatre list) */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div className="bg-terminal-panel border border-terminal-border rounded-lg overflow-hidden">
                  <div className="px-4 py-2.5 border-b border-terminal-border/50 bg-terminal-surface flex items-center gap-2">
                    <Activity className="w-3.5 h-3.5 text-terminal-text-muted" />
                    <span className="text-[10px] font-bold uppercase tracking-wider text-terminal-text-muted">Deployment Heat Map</span>
                  </div>
                  <div className="p-4">
                    <EmptyState
                      type="SPARSE_DATA"
                      description="Heat map requires a theatre list endpoint (GET /api/v1/theatres) which is not yet available. Theatre data will populate automatically when the endpoint ships."
                      className="min-h-0 bg-transparent p-0"
                    />
                  </div>
                </div>

                {/* Movement Feed — sparse state */}
                <div className="bg-terminal-panel border border-terminal-border rounded-lg overflow-hidden">
                  <div className="px-4 py-2.5 border-b border-terminal-border/50 bg-terminal-surface flex items-center gap-2">
                    <Activity className="w-3.5 h-3.5 text-terminal-text-muted" />
                    <span className="text-[10px] font-bold uppercase tracking-wider text-terminal-text-muted">Movement Feed</span>
                  </div>
                  <div className="p-4">
                    <EmptyState
                      type="SPARSE_DATA"
                      description="Live movement feed requires WebSocket event integration (AGENT_DEPLOYED, AGENT_WITHDRAWN). Deployment data is polled every 15s via React Query."
                      className="min-h-0 bg-transparent p-0"
                    />
                  </div>
                </div>
              </div>

              {/* Archetype Distribution — real data */}
              <div className="bg-terminal-panel border border-terminal-border rounded-lg overflow-hidden">
                <div className="px-4 py-2.5 border-b border-terminal-border/50 bg-terminal-surface flex items-center gap-2">
                  <Heart className="w-3.5 h-3.5 text-terminal-text-muted" />
                  <span className="text-[10px] font-bold uppercase tracking-wider text-terminal-text-muted">Archetype Distribution</span>
                </div>
                <div className="p-4">
                  {archetypeDistribution.length > 0 ? (
                    <div className="space-y-3">
                      {/* Stacked bar */}
                      <div className="flex h-6 rounded-lg overflow-hidden">
                        {archetypeDistribution.map(({ archetype, pct }) => (
                          <div
                            key={archetype}
                            className={clsx('h-full', getArchetypeTheme(archetype).bgClass)}
                            style={{ width: `${pct}%` }}
                            title={`${archetype}: ${pct}%`}
                          />
                        ))}
                      </div>
                      {/* Legend */}
                      <div className="flex flex-wrap gap-3">
                        {archetypeDistribution.map(({ archetype, count, pct }) => (
                          <div key={archetype} className="flex items-center gap-1.5">
                            <span className={clsx('w-2.5 h-2.5 rounded-sm', getArchetypeTheme(archetype).bgClass)} />
                            <span className="text-[10px] font-mono text-terminal-text-muted">
                              {archetype} ({count}, {pct}%)
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="text-xs text-terminal-text-muted text-center py-4">No agents</div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </LocalErrorBoundary>
      )}

      {/* Deploy Agent Modal */}
      <DeployAgentModal
        open={deployModalOpen}
        onClose={() => setDeployModalOpen(false)}
      />
    </div>
  );
}

// ── Attention Strip ──────────────────────────────────────────────────

function AttentionStrip({ pageState, kpis }: { pageState: PageState; kpis: { failed: number; total: number; alive: number } }) {
  if (pageState === 'EMPTY') return null; // Zero state handled upstream

  return (
    <div
      className={clsx(
        'flex items-center gap-3 px-4 py-2.5 rounded-lg mb-4 text-xs',
        pageState === 'CRITICAL' && 'bg-status-failure/[0.06] border border-status-failure/[0.18]',
        pageState === 'HEALTHY' && 'bg-status-success/[0.06] border border-status-success/[0.18]',
      )}
    >
      <span className={clsx(
        'w-2 h-2 rounded-full flex-shrink-0',
        pageState === 'CRITICAL' && 'bg-status-failure',
        pageState === 'HEALTHY' && 'bg-status-success',
      )} />
      <span className={clsx(
        'font-semibold',
        pageState === 'CRITICAL' && 'text-status-failure',
        pageState === 'HEALTHY' && 'text-status-success',
      )}>
        {pageState === 'CRITICAL'
          ? `${kpis.failed} agent${kpis.failed !== 1 ? 's' : ''} failed — requires intervention`
          : `All ${kpis.alive} agents healthy — scheduler nominal`
        }
      </span>
    </div>
  );
}

// ── KPI Card ─────────────────────────────────────────────────────────

function KpiCard({
  label,
  value,
  total,
  variant,
}: {
  label: string;
  value: number;
  total?: number;
  variant?: 'success' | 'warning' | 'danger' | 'zero';
}) {
  return (
    <div className="flex-1 bg-terminal-panel border border-terminal-border rounded-lg p-3">
      <div className="text-[10px] font-bold uppercase tracking-wider text-terminal-text-muted mb-1">
        {label}
      </div>
      <div className={clsx(
        'text-xl font-mono font-bold tabular-nums',
        variant === 'success' && 'text-status-success',
        variant === 'warning' && 'text-status-warning',
        variant === 'danger' && value > 0 && 'text-status-failure',
        variant === 'zero' && value === 0 && 'text-terminal-text-muted',
        !variant && 'text-terminal-text',
      )}>
        {value}
      </div>
      {total != null && (
        <div className="text-[10px] font-mono text-terminal-text-muted">
          {total > 0 ? Math.round((value / total) * 100) : 0}%
        </div>
      )}
    </div>
  );
}

// ── Filter Dropdown ──────────────────────────────────────────────────

function FilterDropdown({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: Array<{ value: string; label: string }>;
}) {
  const [open, setOpen] = useState(false);
  const selectedLabel = options.find(o => o.value === value)?.label ?? label;

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 h-8 px-3 bg-terminal-bg border border-terminal-border rounded-lg text-xs text-terminal-text-muted hover:text-terminal-text transition-colors"
      >
        <span>{value === 'all' ? label : selectedLabel}</span>
        <ChevronDown className={clsx('w-3 h-3 transition', open && 'rotate-180')} />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute top-full left-0 mt-1 w-36 bg-terminal-panel border border-terminal-border rounded-lg shadow-lg z-20 py-1">
            {options.map(o => (
              <button
                key={o.value}
                onClick={() => { onChange(o.value); setOpen(false); }}
                className={clsx(
                  'w-full text-left px-3 py-1.5 text-xs hover:bg-terminal-card/50 transition-colors',
                  value === o.value ? 'text-echelon-cyan' : 'text-terminal-text',
                )}
              >
                {o.label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export default AgentRoster;
