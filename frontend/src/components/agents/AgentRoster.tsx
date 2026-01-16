import { Link } from 'react-router-dom';
import { User, TrendingUp, Activity, Search, Copy, Briefcase } from 'lucide-react';
import { useAgents } from '../../hooks/useAgents';
import { AgentSanityIndicator } from './AgentSanityIndicator';
import { TaskAgentModal } from './TaskAgentModal';
import { clsx } from 'clsx';
import { useState } from 'react';

export function AgentRoster() {
  const { data: agentsData, isLoading } = useAgents();
  const agents = agentsData?.agents || [];
  const [taskingAgent, setTaskingAgent] = useState<any | null>(null);

  // Mock lineage data for demo
  const getMockLineage = (agentName: string) => {
    const lineages: Record<string, { gen: number; parents: string }> = {
      'MEGALODON': { gen: 1, parents: 'GENESIS' },
      'CARDINAL': { gen: 2, parents: 'MEGALODON × PHANTOM' },
      'ENVOY': { gen: 1, parents: 'GENESIS' },
      'VIPER': { gen: 3, parents: 'CARDINAL × SPECTER' },
      'ORACLE': { gen: 2, parents: 'ENVOY × CARDINAL' },
      'LEVIATHAN': { gen: 1, parents: 'GENESIS' },
    };
    return lineages[agentName] || { gen: 1, parents: 'GENESIS' };
  };

  const handleTaskAgent = (agent: any, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setTaskingAgent(agent);
  };

  const handleCopyAgent = (agent: any, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    // TODO: Copy agent strategy
    console.log('Copy agent:', agent.name);
  };

  const handleHireAgent = (agent: any, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    // TODO: Open hire modal
    console.log('Hire agent:', agent.name);
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
          {agents.map((agent) => {
            const sanity = agent.sanity || 75;
            const maxSanity = agent.max_sanity || 100;
            const sanityPercent = (sanity / maxSanity) * 100;
            const lineage = getMockLineage(agent.name);
            
            return (
              <div
                key={agent.id}
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
                
                <Link
                  to={`/agent/${agent.id}`}
                  className="block"
                >
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
                </Link>

                {/* Genealogy Metadata */}
                <div className="flex items-center gap-2 mt-2 text-xs relative z-10">
                  <span className="bg-echelon-purple/20 border border-echelon-purple/30 px-2 py-0.5 rounded text-echelon-purple font-mono">
                    GEN {lineage.gen}
                  </span>
                  <span className="text-terminal-muted">•</span>
                  <span className="text-terminal-muted">
                    {lineage.parents === 'GENESIS' ? (
                      <span className="text-echelon-cyan/60">GENESIS AGENT</span>
                    ) : (
                      <>LINEAGE: <span className="text-echelon-purple">{lineage.parents}</span></>
                    )}
                  </span>
                </div>

                <div className="flex items-center justify-between text-xs text-terminal-muted mb-3 mt-2 relative z-10">
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

                {/* Action Buttons */}
                <div className="flex gap-2 mt-4 pt-3 border-t border-terminal-border relative z-10">
                  {/* Task Button - Primary for Spies and Sharks */}
                  {(agent.archetype === 'SPY' || agent.archetype === 'SHARK') && (
                    <button
                      onClick={(e) => handleTaskAgent(agent, e)}
                      className="flex-1 px-3 py-2 border rounded text-sm font-bold transition-all flex items-center justify-center gap-2 bg-echelon-purple/20 border-echelon-purple/50 text-echelon-purple hover:bg-echelon-purple/30"
                    >
                      <Search className="w-4 h-4" />
                      TASK
                    </button>
                  )}
                  
                  {/* Copy Button - For social trading */}
                  <button
                    onClick={(e) => handleCopyAgent(agent, e)}
                    className="flex-1 px-3 py-2 bg-echelon-cyan/20 border border-echelon-cyan/50 text-echelon-cyan rounded text-sm font-bold hover:bg-echelon-cyan/30 transition-all flex items-center justify-center gap-2"
                  >
                    <Copy className="w-4 h-4" />
                    COPY
                  </button>
                  
                  {/* Hire Button */}
                  <button
                    onClick={(e) => handleHireAgent(agent, e)}
                    className="px-3 py-2 bg-echelon-amber/20 border border-echelon-amber/50 text-echelon-amber rounded text-sm font-bold hover:bg-echelon-amber/30 transition-all"
                  >
                    <Briefcase className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Task Agent Modal */}
      {taskingAgent && (
        <TaskAgentModal
          agent={taskingAgent}
          isOpen={!!taskingAgent}
          onClose={() => setTaskingAgent(null)}
        />
      )}
    </div>
  );
}

export default AgentRoster;
