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
    <div className="rounded-2xl border border-[#26292E] bg-[#0F1113] flex flex-col min-h-0">
      {/* Card Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#26292E]">
        <span className="text-sm font-semibold text-[#F1F5F9]">AGENT PERFORMANCE</span>
        <input
          type="text"
          placeholder="Filter agents..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-28 px-2 py-1 text-xs bg-[#0B0C0E] border border-[#26292E] text-[#F1F5F9] rounded outline-none"
        />
      </div>

      {/* Table */}
<div className="flex-1 min-h-0 overflow-y-auto pr-1">
        <table className="w-full table-fixed">
          <thead className="sticky top-0 bg-[#0F1113] z-10">
            <tr>
              <th className="w-[28px] px-2 py-2 text-left text-xs font-medium text-[#64748B]">#</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-[#64748B]">AGENT</th>
              <th className="w-[96px] px-3 py-2 text-left text-xs font-medium text-[#64748B]">P&L</th>
              <th className="w-[88px] px-3 py-2 text-left text-xs font-medium text-[#64748B]">VOL</th>
            </tr>
          </thead>
          <tbody>
            {agents.map((agent, index) => {
              const archetypeStyle = ARCHETYPE_COLORS[agent.archetype] || ARCHETYPE_COLORS.degen;
              const rankColor = index < 4 ? RANK_COLORS[index] : 'transparent';

              return (
                <tr key={agent.id} className="hover:bg-[#1A1D23] transition-colors">
                  <td className="px-2 py-1.5 text-xs font-mono font-medium text-[#94A3B8]">
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
                        <div className="text-xs font-medium text-[#F1F5F9] truncate">{agent.name}</div>
                        <div className="text-[10px] text-[#64748B]">{agent.winRate}% WR · {agent.sharpe} SR</div>
                      </div>
                    </div>
                  </td>
                  <td className={`px-3 py-1.5 text-xs font-mono font-medium ${agent.pnl >= 0 ? 'text-[#4ADE80]' : 'text-[#FB7185]'}`}>
                    {agent.pnlDisplay}
                  </td>
                  <td className="px-3 py-1.5 text-xs font-mono text-[#94A3B8]">
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
