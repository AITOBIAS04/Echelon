import { Link } from 'react-router-dom';
import { User, TrendingUp, Activity, Search, Copy, Briefcase, Globe, BarChart3, PieChart, Brain } from 'lucide-react';
import { useAgents } from '../../hooks/useAgents';
import { AgentSanityIndicator } from './AgentSanityIndicator';
import { TaskAgentModal } from './TaskAgentModal';
import { useAgentsUi } from '../../contexts/AgentsUiContext';
import { clsx } from 'clsx';
import { useState, type ReactEventHandler } from 'react';

// Mock data for right panel widgets
const mockArchetypeDistribution = [
  { archetype: 'SHARK', emoji: '🦈', count: 3 },
  { archetype: 'SPY', emoji: '🕵️', count: 2 },
  { archetype: 'DIPLOMAT', emoji: '🤝', count: 4 },
  { archetype: 'SABOTEUR', emoji: '💣', count: 1 },
  { archetype: 'WHALE', emoji: '🐋', count: 2 },
];

const mockPerformanceSummary = {
  totalPL: 125000,
  winRate: 67,
  totalActions: 15420,
  avgSanity: 82,
  genesisAgents: 3,
};

const mockSanityDistribution = {
  stable: 8,
  stressed: 3,
  critical: 1,
  breakdown: 0,
};

// Mock lineage data for demo
function getMockLineage(agentName: string): { gen: number; parents: string } {
  const lineages: Record<string, { gen: number; parents: string }> = {
    'MEGALODON': { gen: 1, parents: 'GENESIS' },
    'CARDINAL': { gen: 2, parents: 'MEGALODON × PHANTOM' },
    'ENVOY': { gen: 1, parents: 'GENESIS' },
    'VIPER': { gen: 3, parents: 'CARDINAL × SPECTER' },
    'ORACLE': { gen: 2, parents: 'ENVOY × CARDINAL' },
    'LEVIATHAN': { gen: 1, parents: 'GENESIS' },
  };
  return lineages[agentName] || { gen: 1, parents: 'GENESIS' };
}

function getArchetypeEmoji(archetype: string): string {
  switch (archetype?.toUpperCase()) {
    case 'SHARK': return '🦈';
    case 'SPY': return '🕵️';
    case 'DIPLOMAT': return '🤝';
    case 'SABOTEUR': return '💣';
    case 'WHALE': return '🐋';
    default: return '🤖';
  }
}

export function AgentRoster() {
  const { data: agentsData, isLoading } = useAgents();
  const agents = agentsData?.agents || [];
  const { activeTab } = useAgentsUi();
  const [taskingAgent, setTaskingAgent] = useState<any | null>(null);

  const handleTaskAgent: ReactEventHandler<HTMLButtonElement> = (e) => {
    e.preventDefault();
    e.stopPropagation();
    // This is a bit of a hack - we need to find the agent from the click
    // For now, we'll use a simpler approach
    const agentName = (e.target as HTMLElement).closest('[data-agent-name]')?.getAttribute('data-agent-name');
    if (agentName) {
      const agent = agents.find(a => a.name === agentName);
      if (agent) setTaskingAgent(agent);
    }
  };

  const handleCopyAgent: ReactEventHandler<HTMLButtonElement> = (e) => {
    e.preventDefault();
    e.stopPropagation();
    console.log('Copy agent');
  };

  const handleHireAgent: ReactEventHandler<HTMLButtonElement> = (e) => {
    e.preventDefault();
    e.stopPropagation();
    console.log('Hire agent');
  };

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-echelon-cyan animate-pulse">Loading agents...</div>
      </div>
    );
  }

  return (
    <div
      className="h-full min-h-0 flex flex-col overflow-hidden"
      data-testid={activeTab === 'roster' ? 'agents-tab-roster' : 'agents-tab-intel'}
    >
      {/* Main Content Area - Independent Scrolling */}
      <div className="flex-1 min-h-0 flex overflow-hidden">
        {/* Left Column - Main Content */}
        <div className="flex-1 min-w-0 overflow-hidden">
          {activeTab === 'roster' ? (
            /* ROSTER VIEW */
            <div className="h-full overflow-y-auto p-6 custom-scrollbar">
              <div className="max-w-5xl mx-auto">
                <div className="mb-6">
                  <h1 className="text-xl font-bold text-echelon-cyan flex items-center gap-3">
                    <User className="w-5 h-5" />
                    AGENT ROSTER
                  </h1>
                  <span className="text-terminal-muted text-sm mt-1 block">
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
                        data-agent-name={agent.name}
                        className={clsx(
                          'bg-terminal-panel border rounded-lg p-4 transition-all group relative overflow-hidden',
                          sanityPercent > 40
                            ? 'border-terminal-border hover:border-echelon-cyan/50'
                            : sanityPercent > 20
                              ? 'border-echelon-amber/30 hover:border-echelon-amber/50'
                              : 'border-echelon-red/50 hover:border-echelon-red animate-pulse',
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
                          {(agent.archetype === 'SPY' || agent.archetype === 'SHARK') && (
                            <button
                              onClick={handleTaskAgent}
                              className="flex-1 px-3 py-2 border rounded text-sm font-bold transition-all flex items-center justify-center gap-2 bg-echelon-purple/20 border-echelon-purple/50 text-echelon-purple hover:bg-echelon-purple/30"
                            >
                              <Search className="w-4 h-4" />
                              TASK
                            </button>
                          )}

                          <button
                            onClick={handleCopyAgent}
                            className="flex-1 px-3 py-2 bg-echelon-cyan/20 border border-echelon-cyan/50 text-echelon-cyan rounded text-sm font-bold hover:bg-echelon-cyan/30 transition-all flex items-center justify-center gap-2"
                          >
                            <Copy className="w-4 h-4" />
                            COPY
                          </button>

                          <button
                            onClick={handleHireAgent}
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
            </div>
          ) : (
            /* INTELLIGENCE VIEW */
            <div className="h-full overflow-y-auto p-6 custom-scrollbar">
              <div className="max-w-5xl mx-auto">
                <div className="mb-6">
                  <h1 className="text-xl font-bold text-echelon-cyan flex items-center gap-3">
                    <Globe className="w-5 h-5" />
                    GLOBAL INTELLIGENCE
                  </h1>
                  <p className="text-terminal-muted text-sm mt-1">
                    System-wide metrics and agent network analytics
                  </p>
                </div>

                {/* Intelligence Dashboard Grid */}
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <BarChart3 className="w-4 h-4 text-echelon-cyan" />
                      <span className="text-sm font-bold text-terminal-text">Network Health</span>
                    </div>
                    <div className="text-2xl font-mono font-bold text-echelon-green">94.2%</div>
                    <div className="text-xs text-terminal-muted mt-1">All systems operational</div>
                  </div>

                  <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <PieChart className="w-4 h-4 text-echelon-amber" />
                      <span className="text-sm font-bold text-terminal-text">Active Theatres</span>
                    </div>
                    <div className="text-2xl font-mono font-bold text-terminal-text">6</div>
                    <div className="text-xs text-terminal-muted mt-1">Across 3 market sectors</div>
                  </div>
                </div>

                {/* Intelligence Placeholder */}
                <div className="bg-terminal-panel border border-terminal-border rounded-lg p-8 text-center">
                  <Globe className="w-12 h-12 text-terminal-muted mx-auto mb-3" />
                  <h3 className="text-lg font-bold text-terminal-text mb-2">Global Intelligence Dashboard</h3>
                  <p className="text-terminal-muted text-sm max-w-md mx-auto">
                    Advanced agent network analytics, cross-theatre performance correlations,
                    and predictive modeling interfaces will be displayed here.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column - Insights Panels (Roster View Only) */}
        {activeTab === 'roster' && (
          <div className="w-72 flex-shrink-0 min-h-0 overflow-y-auto border-l border-terminal-border bg-terminal-panel/50 custom-scrollbar">
            <div className="p-4 space-y-4">
              {/* Archetype Distribution */}
              <div className="bg-terminal-panel border border-terminal-border rounded-lg overflow-hidden">
                <div className="px-3 py-2 border-b border-terminal-border bg-terminal-bg/50">
                  <span className="text-xs font-bold text-terminal-text uppercase tracking-wider flex items-center gap-2">
                    <PieChart className="w-3 h-3 text-echelon-cyan" />
                    Archetype Distribution
                  </span>
                </div>
                <div className="p-3 space-y-2">
                  {mockArchetypeDistribution.map((item, idx) => (
                    <div key={idx} className="flex items-center gap-3">
                      <span className="text-lg">{item.emoji}</span>
                      <span className="flex-1 text-sm text-terminal-text">{item.archetype}</span>
                      <span className="text-sm font-mono text-terminal-muted">{item.count}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Performance Summary */}
              <div className="bg-terminal-panel border border-terminal-border rounded-lg overflow-hidden">
                <div className="px-3 py-2 border-b border-terminal-border bg-terminal-bg/50">
                  <span className="text-xs font-bold text-terminal-text uppercase tracking-wider flex items-center gap-2">
                    <BarChart3 className="w-3 h-3 text-echelon-green" />
                    Performance Summary
                  </span>
                </div>
                <div className="p-3 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-terminal-muted">Total P/L</span>
                    <span className="font-mono text-echelon-green">+${mockPerformanceSummary.totalPL.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-terminal-muted">Win Rate</span>
                    <span className="font-mono text-terminal-text">{mockPerformanceSummary.winRate}%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-terminal-muted">Total Actions</span>
                    <span className="font-mono text-terminal-text">{mockPerformanceSummary.totalActions.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-terminal-muted">Avg Sanity</span>
                    <span className="font-mono text-terminal-text">{mockPerformanceSummary.avgSanity}/100</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-terminal-muted">Genesis Agents</span>
                    <span className="font-mono text-terminal-text">{mockPerformanceSummary.genesisAgents}</span>
                  </div>
                </div>
              </div>

              {/* Sanity Distribution */}
              <div className="bg-terminal-panel border border-terminal-border rounded-lg overflow-hidden">
                <div className="px-3 py-2 border-b border-terminal-border bg-terminal-bg/50">
                  <span className="text-xs font-bold text-terminal-text uppercase tracking-wider flex items-center gap-2">
                    <Brain className="w-3 h-3 text-echelon-purple" />
                    Sanity Distribution
                  </span>
                </div>
                <div className="p-3 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-terminal-muted">STABLE (70-100)</span>
                    <span className="font-mono text-echelon-green">{mockSanityDistribution.stable}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-terminal-muted">STRESSED (40-69)</span>
                    <span className="font-mono text-echelon-amber">{mockSanityDistribution.stressed}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-terminal-muted">CRITICAL (20-39)</span>
                    <span className="font-mono text-echelon-red">{mockSanityDistribution.critical}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-terminal-muted">BREAKDOWN (&lt;20)</span>
                    <span className="font-mono text-echelon-red">{mockSanityDistribution.breakdown}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
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
