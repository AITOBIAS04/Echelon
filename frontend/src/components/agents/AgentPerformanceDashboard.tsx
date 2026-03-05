/**
 * AgentPerformanceDashboard — Full agent detail with trade history,
 * archetype comparison, and genome viewer.
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../api/client';
import type { Agent } from '../../types/agents';
import { getArchetypeTheme } from '../../theme/agentsTheme';
import { getSanityLevel } from '../../types/agents';
import { TradeHistory } from './TradeHistory';
import { GenomeViewer } from './GenomeViewer';
import { AgentSanityIndicator } from './AgentSanityIndicator';

interface AgentPerformanceDashboardProps {
  agentId: string;
}

function useAgentDetail(agentId: string) {
  return useQuery({
    queryKey: ['agent', agentId],
    queryFn: async (): Promise<Agent> => {
      const { data } = await apiClient.get<Agent>(`/api/v1/agents/${agentId}`);
      return data;
    },
    refetchInterval: 30_000,
  });
}

export function AgentPerformanceDashboard({ agentId }: AgentPerformanceDashboardProps) {
  const { data: agent, isLoading, error } = useAgentDetail(agentId);

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="bg-terminal-surface border border-terminal-border rounded-xl p-6 animate-pulse"
          >
            <div className="h-4 bg-terminal-panel rounded w-1/3 mb-3" />
            <div className="h-3 bg-terminal-panel rounded w-2/3" />
          </div>
        ))}
      </div>
    );
  }

  if (error || !agent) {
    return (
      <div className="bg-terminal-surface border border-terminal-border rounded-xl p-6 text-center">
        <div className="text-xs text-red-400">Failed to load agent data.</div>
      </div>
    );
  }

  const theme = getArchetypeTheme(agent.archetype);
  const Icon = theme.icon;
  const sanityLevel = getSanityLevel(agent.sanity, agent.max_sanity);

  return (
    <div className="space-y-4">
      {/* Agent Header */}
      <div className="bg-terminal-surface border border-terminal-border rounded-xl p-4">
        <div className="flex items-center gap-3 mb-3">
          <div className={`p-2 rounded-lg ${theme.bgClass}`}>
            <Icon className={`w-5 h-5 ${theme.textClass}`} />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-terminal-text">{agent.name}</h2>
              <span className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase ${theme.bgClass} ${theme.textClass}`}>
                {agent.archetype}
              </span>
              {!agent.is_alive && (
                <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-red-500/20 text-red-400">
                  INACTIVE
                </span>
              )}
            </div>
            <div className="text-[10px] text-terminal-text-muted mt-0.5">
              Tier {agent.tier} · Level {agent.level} · ID: {agent.id}
            </div>
          </div>
          <div className="text-right">
            <div className={`text-xl font-mono ${agent.total_pnl_usd >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {agent.total_pnl_usd >= 0 ? '+' : ''}${Math.abs(agent.total_pnl_usd).toLocaleString()}
            </div>
            <div className="text-[10px] text-terminal-text-muted">Total P&L</div>
          </div>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-terminal-panel rounded-lg p-2 text-center">
            <div className="text-sm font-mono text-terminal-text">{(agent.win_rate * 100).toFixed(1)}%</div>
            <div className="text-[9px] text-terminal-text-muted uppercase">Win Rate</div>
          </div>
          <div className="bg-terminal-panel rounded-lg p-2 text-center">
            <div className="text-sm font-mono text-terminal-text">{agent.trades_count}</div>
            <div className="text-[9px] text-terminal-text-muted uppercase">Trades</div>
          </div>
          <div className="bg-terminal-panel rounded-lg p-2 text-center">
            <AgentSanityIndicator sanity={agent.sanity} maxSanity={agent.max_sanity} name={agent.name} />
          </div>
          <div className="bg-terminal-panel rounded-lg p-2 text-center">
            <div className={`text-sm font-mono ${
              sanityLevel === 'stable' ? 'text-emerald-400' :
              sanityLevel === 'stressed' ? 'text-amber-400' :
              sanityLevel === 'critical' ? 'text-rose-400' : 'text-red-400'
            }`}>
              {sanityLevel.toUpperCase()}
            </div>
            <div className="text-[9px] text-terminal-text-muted uppercase">Status</div>
          </div>
        </div>
      </div>

      {/* Trade History */}
      <TradeHistory agent={agent} />

      {/* Genome */}
      <GenomeViewer agent={agent} />
    </div>
  );
}
