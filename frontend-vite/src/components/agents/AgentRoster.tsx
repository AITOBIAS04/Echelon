import { Link } from 'react-router-dom';
import { User, TrendingUp, Activity } from 'lucide-react';
import { useAgents } from '../../hooks/useAgents';
import { clsx } from 'clsx';

export function AgentRoster() {
  const { data: agentsData, isLoading } = useAgents();
  const agents = agentsData?.agents || [];

  const getArchetypeColour = (archetype: string) => {
    switch (archetype?.toUpperCase()) {
      case 'SHARK': return 'text-cyan-400 border-cyan-400/30';
      case 'SPY': return 'text-yellow-400 border-yellow-400/30';
      case 'DIPLOMAT': return 'text-blue-400 border-blue-400/30';
      case 'SABOTEUR': return 'text-red-400 border-red-400/30';
      case 'WHALE': return 'text-purple-400 border-purple-400/30';
      default: return 'text-gray-400 border-gray-400/30';
    }
  };

  const getArchetypeEmoji = (archetype: string) => {
    switch (archetype?.toUpperCase()) {
      case 'SHARK': return '🦈';
      case 'SPY': return '🕵️';
      case 'DIPLOMAT': return '🤝';
      case 'SABOTEUR': return '💣';
      case 'WHALE': return '🐋';
      default: return '🤖';
    }
  };

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-echelon-cyan animate-pulse">Loading agents...</div>
      </div>
    );
  }

  return (
    <div className="h-full p-6 overflow-auto">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-echelon-cyan flex items-center gap-3">
            <User className="w-6 h-6" />
            AGENT ROSTER
          </h1>
          <span className="text-terminal-muted text-sm">
            {agents.length} agents active
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((agent) => (
            <Link
              key={agent.id}
              to={`/agent/${agent.id}`}
              className={clsx(
                'terminal-panel p-4 border hover:border-echelon-cyan/50 transition-all group',
                getArchetypeColour(agent.archetype)
              )}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{getArchetypeEmoji(agent.archetype)}</span>
                  <div>
                    <h3 className="font-bold text-terminal-text group-hover:text-echelon-cyan transition">
                      {agent.name}
                    </h3>
                    <span className="text-xs text-terminal-muted uppercase">
                      {agent.archetype}
                    </span>
                  </div>
                </div>
                <span className={clsx(
                  'text-lg font-mono font-bold',
                  (agent.total_pnl_usd || 0) >= 0 ? 'text-echelon-green' : 'text-echelon-red'
                )}>
                  ${(agent.total_pnl_usd || 0).toLocaleString()}
                </span>
              </div>

              <div className="flex items-center justify-between text-xs text-terminal-muted">
                <span className="flex items-center gap-1">
                  <Activity className="w-3 h-3" />
                  {agent.actions_count || 0} actions
                </span>
                <span className="flex items-center gap-1">
                  <TrendingUp className="w-3 h-3" />
                  {((agent.win_rate || 0) * 100).toFixed(0)}% win rate
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

export default AgentRoster;
