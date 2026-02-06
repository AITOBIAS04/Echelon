// Agent Leaderboard Component
// Performance tracking for AI agents

import type { Agent } from '../../types/blackbox';

interface AgentLeaderboardProps {
  agents: Agent[];
  searchQuery: string;
  onSearchChange: (query: string) => void;
}

const ARCHETYPE_COLORS: Record<string, { bg: string; text: string; icon: string }> = {
  whale: { bg: 'rgba(74, 222, 128, 0.15)', text: '#4ADE80', icon: '🐋' },
  shark: { bg: 'rgba(59, 130, 246, 0.15)', text: '#3B82F6', icon: '🦈' },
  diplomat: { bg: 'rgba(139, 92, 246, 0.15)', text: '#8B5CF6', icon: '🎭' },
  spy: { bg: 'rgba(250, 204, 21, 0.15)', text: '#FACC15', icon: '🕵️' },
  saboteur: { bg: 'rgba(251, 113, 133, 0.15)', text: '#FB7185', icon: '💣' },
  degen: { bg: 'rgba(248, 113, 113, 0.15)', text: '#F87171', icon: '🎲' },
};

const RANK_COLORS = ['#FFD700', '#C0C0C0', '#CD7F32', '#6B7280'];

export function AgentLeaderboard({ agents, searchQuery, onSearchChange }: AgentLeaderboardProps) {
  return (
    <div className="rounded-2xl terminal-panel flex flex-col min-h-0">
      {/* Card Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-terminal-border">
        <span className="text-sm font-semibold text-terminal-text">AGENT PERFORMANCE</span>
        <input
          type="text"
          placeholder="Filter agents..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-28 terminal-input"
        />
      </div>

      {/* Table */}
<div className="flex-1 min-h-0 overflow-y-auto pr-1">
        <table className="w-full table-fixed">
          <thead className="sticky top-0 bg-terminal-header z-10">
            <tr>
              <th className="w-[28px] px-2 py-2 text-left text-xs font-medium text-terminal-text-muted">#</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-terminal-text-muted">AGENT</th>
              <th className="w-[96px] px-3 py-2 text-left text-xs font-medium text-terminal-text-muted">P&L</th>
              <th className="w-[88px] px-3 py-2 text-left text-xs font-medium text-terminal-text-muted">VOL</th>
            </tr>
          </thead>
          <tbody>
            {agents.map((agent, index) => {
              const archetypeStyle = ARCHETYPE_COLORS[agent.archetype] || ARCHETYPE_COLORS.degen;
              const rankColor = index < 4 ? RANK_COLORS[index] : 'transparent';

              return (
                <tr key={agent.id} className="hover:bg-terminal-hover transition-colors">
                  <td className="px-2 py-1.5 text-xs font-mono font-medium text-terminal-text-secondary">
                    <span style={{ color: rankColor !== 'transparent' ? rankColor : undefined }}>
                      {index + 1}
                    </span>
                  </td>
                  <td className="px-3 py-1.5">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-6 h-6 rounded flex items-center justify-center text-xs font-bold text-white"
                        style={{ background: archetypeStyle.text }}
                      >
                        {agent.name[0]}
                      </div>
                      <div className="min-w-0">
                        <div className="text-xs font-medium text-terminal-text truncate">{agent.name}</div>
                        <div className="text-[10px] text-terminal-text-muted">{agent.winRate}% WR · {agent.sharpe} SR</div>
                      </div>
                    </div>
                  </td>
                  <td className={`px-3 py-1.5 text-xs font-mono font-medium ${agent.pnl >= 0 ? 'text-echelon-green' : 'text-echelon-red'}`}>
                    {agent.pnlDisplay}
                  </td>
                  <td className="px-3 py-1.5 text-xs font-mono text-terminal-text-secondary">
                    {agent.volumeDisplay}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
