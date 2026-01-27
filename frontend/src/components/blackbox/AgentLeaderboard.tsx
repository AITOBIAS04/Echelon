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
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">AGENT PERFORMANCE</span>
        <div className="panel-controls">
          <input
            type="text"
            placeholder="Filter agents..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            style={{
              width: 120,
              background: 'var(--bg-app)',
              border: '1px solid var(--border-outer)',
              color: 'var(--text-primary)',
              padding: '4px 8px',
              borderRadius: 4,
              fontSize: 11,
              outline: 'none',
            }}
          />
        </div>
      </div>
      <div className="data-list" style={{ flex: 1, overflow: 'auto', maxHeight: 280 }}>
        <div className="data-row header" style={{ position: 'sticky', top: 0 }}>
          <span className="rank-col">#</span>
          <span className="agent-col">AGENT</span>
          <span className="metric-col">P&L</span>
          <span className="metric-col">VOL</span>
        </div>
        {agents.map((agent, index) => {
          const archetypeStyle = ARCHETYPE_COLORS[agent.archetype] || ARCHETYPE_COLORS.degen;
          const rankColor = index < 4 ? RANK_COLORS[index] : 'transparent';

          return (
            <div key={agent.id} className="leaderboard-row">
              <span
                className="rank-col mono"
                style={{
                  fontWeight: 600,
                  color: rankColor !== 'transparent' ? rankColor : 'var(--text-muted)',
                }}
              >
                {index + 1}
              </span>
              <span className="agent-col" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span
                  className="agent-avatar"
                  style={{
                    width: 24,
                    height: 24,
                    borderRadius: 4,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 11,
                    fontWeight: 700,
                    color: '#fff',
                    background: archetypeStyle.text,
                  }}
                >
                  {agent.name[0]}
                </span>
                <div>
                  <div style={{ fontWeight: 500, fontSize: 11 }}>{agent.name}</div>
                  <div style={{ fontSize: 9, color: 'var(--text-muted)', marginTop: 1 }}>
                    {agent.winRate}% WR · {agent.sharpe} SR
                  </div>
                </div>
              </span>
              <span
                className={`metric-col mono ${agent.pnl >= 0 ? 'positive' : 'negative'}`}
                style={{ fontWeight: 600 }}
              >
                {agent.pnlDisplay}
              </span>
              <span className="metric-col mono" style={{ color: 'var(--text-secondary)' }}>
                {agent.volumeDisplay}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
