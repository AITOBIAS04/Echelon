import { Link } from 'react-router-dom';
import { Bot, Zap, ExternalLink, Search, Copy, Briefcase } from 'lucide-react';
import { AgentSanityIndicator } from '../agents/AgentSanityIndicator';
import { TaskAgentModal } from '../agents/TaskAgentModal';
import { clsx } from 'clsx';
import { useState } from 'react';

// Mock data - replace with real API
const mockAgents = [
  {
    id: 'AGT_MEGALODON',
    name: 'MEGALODON',
    archetype: 'SHARK',
    tier: 2,
    sanity: 78,
    max_sanity: 100,
    total_pnl: 4520.5,
    win_rate: 0.67,
    trades_count: 156,
    status: 'ACTIVE',
    current_timeline: 'TL_FED_RATE',
  },
  {
    id: 'AGT_CARDINAL',
    name: 'CARDINAL',
    archetype: 'SPY',
    tier: 1,
    sanity: 45,
    max_sanity: 100,
    total_pnl: 1230.25,
    win_rate: 0.58,
    trades_count: 89,
    status: 'GATHERING_INTEL',
    current_timeline: 'TL_GHOST_TANKER',
  },
  {
    id: 'AGT_ENVOY',
    name: 'ENVOY',
    archetype: 'DIPLOMAT',
    tier: 1,
    sanity: 92,
    max_sanity: 100,
    total_pnl: 890.0,
    win_rate: 0.72,
    trades_count: 45,
    status: 'SHIELDING',
    current_timeline: 'TL_CONTAGION',
  },
];

const archetypeColors: Record<string, string> = {
  SHARK: 'text-agent-shark bg-agent-shark/20',
  SPY: 'text-agent-spy bg-agent-spy/20',
  DIPLOMAT: 'text-agent-diplomat bg-agent-diplomat/20',
  SABOTEUR: 'text-agent-saboteur bg-agent-saboteur/20',
  WHALE: 'text-agent-whale bg-agent-whale/20',
};

const archetypeIcons: Record<string, string> = {
  SHARK: '🦈',
  SPY: '🕵️',
  DIPLOMAT: '🤝',
  SABOTEUR: '💣',
  WHALE: '🐋',
};

export function MyAgents() {
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

  const handleTaskAgent = (agent: any) => {
    setTaskingAgent(agent);
  };

  const handleCopyAgent = (agent: any) => {
    // TODO: Copy agent strategy
    console.log('Copy agent:', agent.name);
  };

  const handleHireAgent = (agent: any) => {
    // TODO: Open hire modal
    console.log('Hire agent:', agent.name);
  };

  return (
    <div className="h-full overflow-y-auto">
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
        {mockAgents.map((agent) => {
          const sanityPercent = (agent.sanity / agent.max_sanity) * 100;
          const lineage = getMockLineage(agent.name);
          
          return (
            <div 
              key={agent.id} 
              className={clsx(
                'terminal-card p-4 relative overflow-hidden transition-all',
                sanityPercent > 40
                  ? 'border-terminal-border'
                  : sanityPercent > 20
                    ? 'border-status-warning/30'
                    : 'border-status-danger/50 animate-pulse',
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
              
              {/* Header */}
              <div className="flex items-start justify-between mb-3 relative z-10">
                <div className="flex items-center gap-3">
                  <div className={clsx(
                    'text-3xl',
                    sanityPercent <= 20 && 'animate-pulse'
                  )}>
                    {archetypeIcons[agent.archetype]}
                  </div>
                  <div>
                    <h3 className={clsx(
                      'font-bold',
                      sanityPercent <= 20 ? 'text-status-danger' : 'text-terminal-text'
                    )}>
                      {agent.name}
                    </h3>
                    <div className="flex items-center gap-2">
                      <span
                        className={clsx(
                          'text-xs px-2 py-0.5 rounded',
                          archetypeColors[agent.archetype]
                        )}
                      >
                        {agent.archetype}
                      </span>
                      <span className="text-xs text-terminal-text-secondary">Tier {agent.tier}</span>
                    </div>
                  </div>
                </div>
                <Link
                  to={`/agent/${agent.id}`}
                  className="text-terminal-text-secondary hover:text-status-info transition"
                >
                  <ExternalLink className="w-4 h-4" />
                </Link>
              </div>

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

              {/* Sanity Indicator */}
              <div className="relative z-10">
                <AgentSanityIndicator 
                  sanity={agent.sanity}
                  maxSanity={agent.max_sanity}
                  name={agent.name}
                />
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-2 mb-3 relative z-10">
                <div className="text-center p-2 bg-terminal-bg rounded">
                  <div className="text-xs text-terminal-muted">P&L</div>
                  <div
                    className={clsx(
                      'text-sm font-mono font-bold',
                      agent.total_pnl >= 0 ? 'text-status-success' : 'text-status-danger'
                    )}
                  >
                    ${agent.total_pnl.toLocaleString()}
                  </div>
                </div>
                <div className="text-center p-2 bg-terminal-bg rounded">
                  <div className="text-xs text-terminal-muted">Win Rate</div>
                  <div className="text-sm font-mono font-bold text-terminal-text">
                    {(agent.win_rate * 100).toFixed(0)}%
                  </div>
                </div>
                <div className="text-center p-2 bg-terminal-bg rounded">
                  <div className="text-xs text-terminal-muted">Trades</div>
                  <div className="text-sm font-mono font-bold text-terminal-text">
                    {agent.trades_count}
                  </div>
                </div>
              </div>

              {/* Status */}
              <div className="flex items-center justify-between p-2 bg-terminal-bg rounded relative z-10">
                <div className="flex items-center gap-2">
                  <Zap className="w-3 h-3 text-status-info" />
                  <span className="text-xs text-status-info uppercase">
                    {agent.status.replace('_', ' ')}
                  </span>
                </div>
                <span className="text-xs text-terminal-text-secondary">{agent.current_timeline}</span>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2 mt-4 pt-3 border-t border-terminal-border relative z-10">
                {/* Task Button - Primary for Spies and Sharks */}
                {(agent.archetype === 'SPY' || agent.archetype === 'SHARK') && (
                  <button
                    onClick={() => handleTaskAgent(agent)}
                    className="flex-1 px-3 py-2 border rounded text-sm font-bold transition-all flex items-center justify-center gap-2 bg-status-paradox/20 border-status-paradox/50 text-status-paradox hover:bg-status-paradox/30"
                  >
                    <Search className="w-4 h-4" />
                    TASK
                  </button>
                )}

                {/* Copy Button - For social trading */}
                <button
                  onClick={() => handleCopyAgent(agent)}
                  className="flex-1 px-3 py-2 bg-status-info/20 border border-status-info/50 text-status-info rounded text-sm font-bold hover:bg-status-info/30 transition-all flex items-center justify-center gap-2"
                >
                  <Copy className="w-4 h-4" />
                  COPY
                </button>

                {/* Hire Button */}
                <button
                  onClick={() => handleHireAgent(agent)}
                  className="px-3 py-2 bg-status-warning/20 border border-status-warning/50 text-status-warning rounded text-sm font-bold hover:bg-status-warning/30 transition-all"
                >
                  <Briefcase className="w-4 h-4" />
                </button>
              </div>
            </div>
          );
        })}

        {/* Add Agent Card */}
        <Link
          to="/agents"
          className="terminal-card p-4 flex flex-col items-center justify-center min-h-[200px] border-dashed hover:border-status-info/50 transition"
        >
          <Bot className="w-8 h-8 text-terminal-text-secondary mb-2" />
          <span className="text-sm text-terminal-text-secondary">Hire New Agent</span>
        </Link>
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

