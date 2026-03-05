/**
 * ArchetypeComparison — Radar-style chart comparing agent stats across archetypes.
 * Uses CSS-based radial display (no external chart library).
 */

import { useMemo } from 'react';
import { useAgentRoster } from '../../hooks/useAgents';
import { getArchetypeTheme } from '../../theme/agentsTheme';
import type { AgentArchetype } from '../../types/agents';

interface ArchetypeStats {
  archetype: AgentArchetype;
  count: number;
  avgWinRate: number;
  avgPnl: number;
  avgSanity: number;
  totalTrades: number;
}

export function ArchetypeComparison() {
  const { agents, isLoading } = useAgentRoster();

  const archetypeStats = useMemo((): ArchetypeStats[] => {
    const groups: Record<string, typeof agents> = {};
    for (const agent of agents) {
      (groups[agent.archetype] ??= []).push(agent);
    }

    return Object.entries(groups).map(([archetype, group]) => ({
      archetype: archetype as AgentArchetype,
      count: group.length,
      avgWinRate: group.reduce((s, a) => s + a.winRate, 0) / group.length,
      avgPnl: group.reduce((s, a) => s + a.total_pnl_usd, 0) / group.length,
      avgSanity: group.reduce((s, a) => s + (a.max_sanity > 0 ? (a.sanity / a.max_sanity) * 100 : 0), 0) / group.length,
      totalTrades: group.reduce((s, a) => s + a.trades_count, 0),
    }));
  }, [agents]);

  if (isLoading) {
    return (
      <div className="bg-terminal-surface border border-terminal-border rounded-xl p-6 text-center">
        <div className="text-xs text-terminal-text-muted">Loading archetype data...</div>
      </div>
    );
  }

  if (archetypeStats.length === 0) {
    return (
      <div className="bg-terminal-surface border border-terminal-border rounded-xl p-6 text-center">
        <div className="text-xs text-terminal-text-muted">No agents to compare.</div>
      </div>
    );
  }

  // Find maxima for normalisation
  const maxWinRate = Math.max(...archetypeStats.map((s) => s.avgWinRate), 1);
  const maxSanity = Math.max(...archetypeStats.map((s) => s.avgSanity), 1);
  const maxTrades = Math.max(...archetypeStats.map((s) => s.totalTrades), 1);

  return (
    <div className="bg-terminal-surface border border-terminal-border rounded-xl p-4">
      <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wider mb-3">
        Archetype Comparison
      </h3>

      <div className="space-y-3">
        {archetypeStats.map((stat) => {
          const theme = getArchetypeTheme(stat.archetype);
          const Icon = theme.icon;
          const winPct = (stat.avgWinRate / maxWinRate) * 100;
          const sanityPct = (stat.avgSanity / maxSanity) * 100;
          const tradePct = (stat.totalTrades / maxTrades) * 100;

          return (
            <div key={stat.archetype} className="bg-terminal-panel rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <Icon className={`w-4 h-4 ${theme.textClass}`} />
                <span className={`text-xs font-semibold ${theme.textClass}`}>{stat.archetype}</span>
                <span className="text-[10px] text-terminal-text-muted ml-auto">
                  {stat.count} agent{stat.count !== 1 ? 's' : ''}
                </span>
              </div>

              {/* Stat bars */}
              <div className="space-y-1.5">
                <div className="flex items-center gap-2 text-[10px]">
                  <span className="w-14 text-terminal-text-muted">Win Rate</span>
                  <div className="flex-1 h-1.5 bg-terminal-surface rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${theme.bgClass} transition-all duration-500`}
                      style={{ width: `${winPct}%`, backgroundColor: 'currentColor' }}
                    >
                      <div className={`h-full rounded-full opacity-60 ${theme.textClass}`} style={{ width: '100%', backgroundColor: 'currentColor' }} />
                    </div>
                  </div>
                  <span className="w-10 text-right text-terminal-text font-mono">{stat.avgWinRate.toFixed(0)}%</span>
                </div>

                <div className="flex items-center gap-2 text-[10px]">
                  <span className="w-14 text-terminal-text-muted">Sanity</span>
                  <div className="flex-1 h-1.5 bg-terminal-surface rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{ width: `${sanityPct}%`, backgroundColor: stat.avgSanity > 70 ? '#10b981' : stat.avgSanity > 40 ? '#f59e0b' : '#ef4444' }}
                    />
                  </div>
                  <span className="w-10 text-right text-terminal-text font-mono">{stat.avgSanity.toFixed(0)}%</span>
                </div>

                <div className="flex items-center gap-2 text-[10px]">
                  <span className="w-14 text-terminal-text-muted">Trades</span>
                  <div className="flex-1 h-1.5 bg-terminal-surface rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full bg-echelon-cyan/40 transition-all duration-500"
                      style={{ width: `${tradePct}%` }}
                    />
                  </div>
                  <span className="w-10 text-right text-terminal-text font-mono">{stat.totalTrades}</span>
                </div>
              </div>

              {/* P&L */}
              <div className="mt-2 text-[10px] text-right">
                <span className="text-terminal-text-muted">Avg P&L: </span>
                <span className={`font-mono ${stat.avgPnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {stat.avgPnl >= 0 ? '+' : ''}${stat.avgPnl.toFixed(2)}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
