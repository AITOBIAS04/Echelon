import { Link } from 'react-router-dom';
import { User, TrendingUp, Activity } from 'lucide-react';
import { useAgents } from '../../hooks/useAgents';
import { AgentSanityIndicator } from './AgentSanityIndicator';
import { clsx } from 'clsx';

export function AgentRoster() {
  const { data: agentsData, isLoading } = useAgents();
  const agents = agentsData?.agents || [];

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
          {agents.map((agent) => {
            const sanity = agent.sanity || 75;
            const maxSanity = agent.max_sanity || 100;
            const sanityPercent = (sanity / maxSanity) * 100;
            
            return (
              <Link
                key={agent.id}
                to={`/agent/${agent.id}`}
                className={clsx(
                  'bg-terminal-panel border rounded-lg p-4 transition-all group relative overflow-hidden',
                  sanityPercent > 40 
                    ? 'border-terminal-border hover:border-echelon-cyan/50'
                    : sanityPercent > 20
                      ? 'border-echelon-amber/30 hover:border-echelon-amber/50'
                      : 'border-echelon-red/50 hover:border-echelon-red animate-pulse',
                  // Glitch effect for critical sanity
                  sanityPercent <= 20 && 'relative overflow-hidden'
                )}
              >
                {/* Glitch overlay for critical agents */}
                {sanityPercent <= 20 && (
                  <div 
                    className="absolute inset-0 pointer-events-none opacity-20"
                    style={{
                      background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,0,0,0.1) 2px, rgba(255,0,0,0.1) 4px)',
                      animation: 'glitch 0.3s infinite'
                    }}
                  />
                )}
                
                <div className="flex items-start justify-between mb-3 relative z-10">
                  <div className="flex items-center gap-3">
                    <span className={clsx(
                      'text-2xl',
                      sanityPercent <= 20 && 'animate-pulse'
                    )}>
                      {getArchetypeEmoji(agent.archetype)}
                    </span>
                    <div>
                      <h3 className={clsx(
                        'font-bold transition',
                        sanityPercent <= 20 ? 'text-echelon-red' : 'text-terminal-text group-hover:text-echelon-cyan'
                      )}>
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

                <div className="flex items-center justify-between text-xs text-terminal-muted mb-3 relative z-10">
                  <span className="flex items-center gap-1">
                    <Activity className="w-3 h-3" />
                    {agent.actions_count || 0} actions
                  </span>
                  <span className="flex items-center gap-1">
                    <TrendingUp className="w-3 h-3" />
                    {((agent.win_rate || 0) * 100).toFixed(0)}% win rate
                  </span>
                </div>
                
                {/* Sanity Indicator */}
                <div className="relative z-10">
                  <AgentSanityIndicator 
                    sanity={sanity}
                    maxSanity={maxSanity}
                    name={agent.name}
                  />
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default AgentRoster;
