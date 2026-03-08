/**
 * AgentDetail — Agent detail page with deployment info.
 *
 * Shows agent overview + active deployments + deployment history.
 * Actions: Pause/Resume/Withdraw for ACTIVE deployments.
 *
 * Design ref: echelon_fleet_v1.html (agent detail rail)
 * Backend: GET /api/v1/agents/{id}, GET /api/v1/agent-deployments?agent_id={id}
 */

import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Rocket, Pause, Play, ArrowDownToLine, Loader2 } from 'lucide-react';
import { clsx } from 'clsx';
import { AgentPerformanceDashboard } from './AgentPerformanceDashboard';
import { ArchetypeComparison } from './ArchetypeComparison';
import {
  useDeploymentList,
  useWithdrawDeployment,
  usePauseDeployment,
  useResumeDeployment,
} from '../../hooks/useAgentDeployments';
import { EmptyState } from '../empty-states/EmptyState';
import type { DeploymentStatus } from '../../types/agentDeployment';

function statusBadgeClasses(status: DeploymentStatus): string {
  switch (status) {
    case 'ACTIVE':
      return 'bg-status-success/15 text-status-success';
    case 'PAUSED':
      return 'bg-status-warning/15 text-status-warning';
    case 'WITHDRAWN':
      return 'bg-terminal-panel text-terminal-text-muted';
  }
}

export function AgentDetail() {
  const { agentId } = useParams();
  const { deployments, isLoading: deploymentsLoading } = useDeploymentList(
    agentId ? { agent_id: agentId } : undefined,
  );
  const withdrawDeployment = useWithdrawDeployment();
  const pauseDeployment = usePauseDeployment();
  const resumeDeployment = useResumeDeployment();

  if (!agentId) {
    return (
      <div className="h-full p-6 text-terminal-text-muted text-xs">
        No agent ID provided.
      </div>
    );
  }

  const activeDeployments = deployments.filter(d => d.status === 'ACTIVE' || d.status === 'PAUSED');
  const historicalDeployments = deployments.filter(d => d.status === 'WITHDRAWN');

  return (
    <div className="h-full p-6 overflow-auto">
      <div className="max-w-5xl mx-auto">
        <Link
          to="/fleet"
          className="flex items-center gap-2 text-terminal-text-muted hover:text-echelon-cyan mb-6 transition text-xs"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Fleet
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Main — Agent detail + trade history + genome */}
          <div className="lg:col-span-2 space-y-4">
            <AgentPerformanceDashboard agentId={agentId} />

            {/* ── Active Deployments ─────────────────────────────── */}
            <div className="bg-terminal-panel border border-terminal-border rounded-lg overflow-hidden">
              <div className="px-4 py-2.5 border-b border-terminal-border/50 bg-terminal-surface flex items-center gap-2">
                <Rocket className="w-3.5 h-3.5 text-terminal-text-muted" />
                <h3 className="text-[10px] font-bold uppercase tracking-wider text-terminal-text-muted">
                  Active Deployments
                </h3>
                <span className="font-mono text-[10px] text-terminal-text-muted ml-auto">
                  {activeDeployments.length} active
                </span>
              </div>
              <div className="p-4">
                {deploymentsLoading ? (
                  <div className="flex items-center justify-center py-6">
                    <Loader2 className="w-4 h-4 text-terminal-text-muted animate-spin" />
                  </div>
                ) : activeDeployments.length > 0 ? (
                  <div className="space-y-2">
                    {activeDeployments.map(d => (
                      <div
                        key={d.id}
                        className="flex items-center justify-between p-3 rounded bg-terminal-surface border border-terminal-border/50"
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <span className={clsx(
                            'px-1.5 py-0.5 rounded text-[9px] font-mono font-semibold uppercase',
                            statusBadgeClasses(d.status),
                          )}>
                            {d.status}
                          </span>
                          <div className="min-w-0">
                            <div className="font-mono text-xs text-terminal-text">
                              Theatre: <span className="text-echelon-cyan">{d.theatre_id.slice(0, 12)}</span>
                            </div>
                            <div className="text-[10px] text-terminal-text-muted">
                              Strategy: {d.strategy_profile} · Deployed {new Date(d.deployed_at).toLocaleDateString()}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-1.5 shrink-0 ml-3">
                          {d.status === 'ACTIVE' && (
                            <button
                              onClick={() => pauseDeployment.mutate(d.id)}
                              disabled={pauseDeployment.isPending}
                              className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-semibold text-terminal-text-muted hover:text-status-warning hover:bg-status-warning/10 transition-colors"
                              title="Pause deployment"
                            >
                              <Pause className="w-3 h-3" />
                              Pause
                            </button>
                          )}
                          {d.status === 'PAUSED' && (
                            <button
                              onClick={() => resumeDeployment.mutate(d.id)}
                              disabled={resumeDeployment.isPending}
                              className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-semibold text-terminal-text-muted hover:text-status-success hover:bg-status-success/10 transition-colors"
                              title="Resume deployment"
                            >
                              <Play className="w-3 h-3" />
                              Resume
                            </button>
                          )}
                          <button
                            onClick={() => withdrawDeployment.mutate(d.id)}
                            disabled={withdrawDeployment.isPending}
                            className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-semibold text-terminal-text-muted hover:text-status-failure hover:bg-status-failure/10 transition-colors"
                            title="Withdraw (recall) deployment"
                          >
                            <ArrowDownToLine className="w-3 h-3" />
                            Recall
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyState
                    type="ZERO_STATE"
                    icon={<Rocket className="w-5 h-5" />}
                    title="No active deployments"
                    description="This agent is not currently deployed to any theatre. Deploy from a theatre detail page where the theatre context is known."
                    className="min-h-0 py-6"
                  />
                )}
              </div>
            </div>

            {/* ── Deployment History ──────────────────────────────── */}
            {historicalDeployments.length > 0 && (
              <div className="bg-terminal-panel border border-terminal-border rounded-lg overflow-hidden">
                <div className="px-4 py-2.5 border-b border-terminal-border/50 bg-terminal-surface flex items-center gap-2">
                  <h3 className="text-[10px] font-bold uppercase tracking-wider text-terminal-text-muted">
                    Deployment History
                  </h3>
                  <span className="font-mono text-[10px] text-terminal-text-muted ml-auto">
                    {historicalDeployments.length} withdrawn
                  </span>
                </div>
                <div className="p-4 space-y-2">
                  {historicalDeployments.map(d => (
                    <div
                      key={d.id}
                      className="flex items-center gap-3 p-2 rounded text-xs text-terminal-text-muted"
                    >
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-semibold bg-terminal-panel text-terminal-text-muted">
                        WITHDRAWN
                      </span>
                      <span className="font-mono text-[10px]">{d.theatre_id.slice(0, 12)}</span>
                      <span>{d.strategy_profile}</span>
                      <span className="ml-auto font-mono text-[10px]">
                        {new Date(d.deployed_at).toLocaleDateString()}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Sidebar — Archetype comparison */}
          <div>
            <ArchetypeComparison />
          </div>
        </div>
      </div>
    </div>
  );
}

export default AgentDetail;
