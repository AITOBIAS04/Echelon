import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  User,
  TrendingUp,
  Activity,
  Search,
  Copy,
  Briefcase,
  Users,
  MapPin,
  History,
  AlertTriangle,
  ArrowRight,
  ArrowLeft,
  Zap,
} from 'lucide-react';
import { useAgents } from '../../hooks/useAgents';
import { AgentSanityIndicator } from './AgentSanityIndicator';
import { TaskAgentModal } from './TaskAgentModal';
import { useRegisterTopActionBarActions } from '../../contexts/TopActionBarActionsContext';
import { clsx } from 'clsx';

// Tab type
type AgentsTab = 'roster' | 'intel';

// Mock data for Global Intelligence dashboard
const mockStats = {
  totalAgents: 12,
  deployedAgents: 8,
  movements24h: 47,
  activeConflicts: 3,
};

const mockTheatres = [
  { name: 'ORB_SALVAGE_F7', agents: 12, activity: 'high', stability: 87, volume: '$142K', gap: 12 },
  { name: 'VEN_OIL_TANKER', agents: 8, activity: 'medium', stability: 92, volume: '$89K', gap: 8 },
  { name: 'FED_RATE_DECISION', agents: 15, activity: 'high', stability: 78, volume: '$215K', gap: 18 },
  { name: 'TAIWAN_STRAIT', agents: 5, activity: 'low', stability: 95, volume: '$45K', gap: 5 },
  { name: 'NVDA_EARNINGS', agents: 9, activity: 'medium', stability: 84, volume: '$128K', gap: 14 },
  { name: 'BTC_HALVING', agents: 4, activity: 'low', stability: 97, volume: '$32K', gap: 3 },
];

const mockMovements = [
  { time: '14:32:45', agent: 'LEVIATHAN', action: 'deployed to', theatre: 'ORB_SALVAGE_F7', velocity: '+3', type: 'deploy' as const },
  { time: '14:32:42', agent: 'VIPER', action: 'withdrew from', theatre: 'VEN_OIL_TANKER', velocity: '-2', type: 'withdraw' as const },
  { time: '14:32:38', agent: 'CHAOS', action: 'deployed to', theatre: 'FED_RATE_DECISION', velocity: '+4', type: 'deploy' as const },
  { time: '14:32:35', agent: 'AMBASSADOR', action: 'deployed to', theatre: 'TAIWAN_STRAIT', velocity: '+2', type: 'deploy' as const },
  { time: '14:32:30', agent: 'CARDINAL', action: 'withdrew from', theatre: 'ORB_SALVAGE_F7', velocity: '-1', type: 'withdraw' as const },
  { time: '14:32:25', agent: 'TITAN', action: 'shifted to', theatre: 'conservative strategy', velocity: '~0', type: 'strategy' as const },
  { time: '14:32:20', agent: 'SHADOW', action: 'deployed to', theatre: 'NVDA_EARNINGS', velocity: '+1', type: 'deploy' as const },
];

const mockClusters = [
  { name: 'SHARK', emoji: '🦈', count: 12, focus: 'High-volatility', avgPosition: '$8,450', winRate: 68 },
  { name: 'DIPLOMAT', emoji: '🤝', count: 8, focus: 'Stability', avgPosition: '$4,200', winRate: 72 },
  { name: 'SABOTEUR', emoji: '💣', count: 6, focus: 'Adversarial', avgPosition: '$3,800', winRate: 42 },
];

const mockConflicts = [
  { severity: 'high' as const, agents: ['VIPER', 'CHAOS'], theatre: 'ORB_SALVAGE_F7', positions: '$12,450 vs $8,200', impact: -15 },
  { severity: 'medium' as const, agents: ['LEVIATHAN', 'TITAN'], theatre: 'FED_RATE_DECISION', positions: '$24,500 vs $18,200', impact: 8 },
  { severity: 'low' as const, agents: ['AEGIS', 'SABOTEUR'], theatre: 'VEN_OIL_TANKER', positions: '$6,800 vs $5,200', impact: -5 },
];

// Helper to get archetype emoji
function getArchetypeEmoji(archetype: string): string {
  const emojis: Record<string, string> = {
    WHALE: '🐋',
    SHARK: '🦈',
    DIPLOMAT: '🤝',
    SABOTEUR: '💣',
    SPY: '🕵️',
    SPY_MASTER: '🎭',
    FRONTRUNNER: '🏎️',
    HEDGER: '🛡️',
    GENESIS: '🌟',
    MEDIUM: '📊',
    ROBOT: '🤖',
  };
  return emojis[archetype] || '🤖';
}

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

export function AgentRoster() {
  const { data: agentsData, isLoading } = useAgents();
  const agents = agentsData?.agents || [];
  const [taskingAgent, setTaskingAgent] = useState<any | null>(null);
  const [activeTab, setActiveTab] = useState<AgentsTab>('roster');
  const [movementFilter, setMovementFilter] = useState<string>('all');
  const [movements, setMovements] = useState(mockMovements);

  // Register TopActionBar action handlers
  useRegisterTopActionBarActions({
    agentRoster: () => setActiveTab('roster'),
    globalIntel: () => setActiveTab('intel'),
  });

  // Simulate live movement feed updates
  useEffect(() => {
    if (activeTab !== 'intel') return;

    const interval = setInterval(() => {
      if (Math.random() > 0.5) {
        const newMovement = {
          time: new Date().toISOString().slice(11, 19),
          agent: ['LEVIATHAN', 'VIPER', 'TITAN', 'SHADOW', 'CHAOS', 'AMBASSADOR'][Math.floor(Math.random() * 6)],
          action: ['deployed to', 'withdrew from', 'shifted to'][Math.floor(Math.random() * 3)],
          theatre: ['ORB_SALVAGE_F7', 'VEN_OIL_TANKER', 'FED_RATE_DECISION', 'NVDA_EARNINGS'][Math.floor(Math.random() * 4)],
          velocity: ['+1', '+2', '+3', '+4', '-1', '-2', '~0'][Math.floor(Math.random() * 7)],
          type: ['deploy', 'withdraw', 'strategy'][Math.floor(Math.random() * 3)] as 'deploy' | 'withdraw' | 'strategy',
        };
        setMovements(prev => [newMovement, ...prev.slice(0, 19)]);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [activeTab]);

  const handleTaskAgent = (agent: any, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setTaskingAgent(agent);
  };

  const handleCopyAgent = (agent: any, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    console.log('Copy agent:', agent.name);
  };

  const handleHireAgent = (agent: any, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    console.log('Hire agent:', agent.name);
  };

  const filteredMovements = movements.filter(m => {
    if (movementFilter === 'all') return true;
    if (movementFilter === 'deploy') return m.type === 'deploy';
    if (movementFilter === 'withdraw') return m.type === 'withdraw';
    if (movementFilter === 'strategy') return m.type === 'strategy';
    return true;
  });

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-cyan-400 animate-pulse">Loading agents...</div>
      </div>
    );
  }

  return (
    <div
      className="h-full flex flex-col"
      data-testid={activeTab === 'roster' ? 'agents-tab-roster' : 'agents-tab-intel'}
    >
      {/* Agent Roster View */}
      {activeTab === 'roster' && (
        <div className="flex-1 overflow-y-auto p-6">
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
        </div>
      )}

      {/* Global Intelligence View */}
      {activeTab === 'intel' && (
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto">
            {/* Stats Row - KPI Cards */}
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="w-10 h-10 rounded bg-echelon-cyan/20 flex items-center justify-center">
                    <Users className="w-5 h-5 text-echelon-cyan" />
                  </div>
                  <span className="text-xs text-echelon-green">+2 this week</span>
                </div>
                <div className="text-2xl font-bold text-terminal-text">{mockStats.totalAgents}</div>
                <div className="text-sm text-terminal-muted">Total Agents</div>
              </div>

              <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="w-10 h-10 rounded bg-echelon-green/20 flex items-center justify-center">
                    <MapPin className="w-5 h-5 text-echelon-green" />
                  </div>
                  <span className="text-xs text-terminal-muted">67% utilization</span>
                </div>
                <div className="text-2xl font-bold text-terminal-text">{mockStats.deployedAgents}</div>
                <div className="text-sm text-terminal-muted">Deployed</div>
              </div>

              <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="w-10 h-10 rounded bg-echelon-purple/20 flex items-center justify-center">
                    <History className="w-5 h-5 text-echelon-purple" />
                  </div>
                  <span className="text-xs text-echelon-green">+12 from yesterday</span>
                </div>
                <div className="text-2xl font-bold text-terminal-text">{mockStats.movements24h}</div>
                <div className="text-sm text-terminal-muted">Movements (24h)</div>
              </div>

              <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="w-10 h-10 rounded bg-echelon-red/20 flex items-center justify-center">
                    <AlertTriangle className="w-5 h-5 text-echelon-red" />
                  </div>
                  <span className="text-xs text-echelon-green">-1 from yesterday</span>
                </div>
                <div className="text-2xl font-bold text-terminal-text">{mockStats.activeConflicts}</div>
                <div className="text-sm text-terminal-muted">Active Conflicts</div>
              </div>
            </div>

            {/* Dashboard Grid */}
            <div className="grid grid-cols-2 gap-4 mb-4">
              {/* Deployment Heat Map */}
              <div className="bg-terminal-panel border border-terminal-border rounded-lg overflow-hidden">
                <div className="flex items-center justify-between px-4 py-3 border-b border-terminal-border">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-echelon-cyan" />
                    <span className="font-semibold text-terminal-text">Deployment Heat Map</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-echelon-green animate-pulse"></span>
                      <span className="text-xs text-terminal-muted">LIVE</span>
                    </span>
                  </div>
                </div>
                <div className="p-4">
                  <div className="grid grid-cols-2 gap-3">
                    {mockTheatres.map((theatre) => (
                      <div
                        key={theatre.name}
                        className={clsx(
                          'rounded border p-3 transition-all',
                          theatre.activity === 'high' && 'border-echelon-red/50 bg-echelon-red/10',
                          theatre.activity === 'medium' && 'border-echelon-amber/50 bg-echelon-amber/10',
                          theatre.activity === 'low' && 'border-echelon-green/50 bg-echelon-green/10'
                        )}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-mono text-xs text-terminal-text">{theatre.name}</span>
                          <span className={clsx(
                            'text-xs font-medium',
                            theatre.activity === 'high' && 'text-echelon-red',
                            theatre.activity === 'medium' && 'text-echelon-amber',
                            theatre.activity === 'low' && 'text-echelon-green'
                          )}>
                            {theatre.activity === 'high' && '🔥'}
                            {theatre.activity === 'medium' && '🟡'}
                            {theatre.activity === 'low' && '🟢'}
                          </span>
                        </div>
                        <div className="flex items-center gap-3 text-xs text-terminal-muted">
                          <span>{theatre.agents} agents</span>
                        </div>
                        <div className="flex items-center gap-3 mt-2 text-xs">
                          <span><span className="text-terminal-muted">Stab</span> <span className="text-terminal-text">{theatre.stability}%</span></span>
                          <span><span className="text-terminal-muted">Vol</span> <span className="text-terminal-text">{theatre.volume}</span></span>
                          <span><span className="text-terminal-muted">Gap</span> <span className="text-terminal-text">{theatre.gap}%</span></span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Movement Feed */}
              <div className="bg-terminal-panel border border-terminal-border rounded-lg overflow-hidden">
                <div className="flex items-center justify-between px-4 py-3 border-b border-terminal-border">
                  <div className="flex items-center gap-2">
                    <History className="w-4 h-4 text-echelon-purple" />
                    <span className="font-semibold text-terminal-text">Movement Feed</span>
                  </div>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-echelon-green animate-pulse"></span>
                    <span className="text-xs text-terminal-muted">LIVE</span>
                  </span>
                </div>
                <div className="flex items-center gap-1 px-4 py-2 border-b border-terminal-border">
                  <button
                    onClick={() => setMovementFilter('all')}
                    className={clsx(
                      'px-3 py-1 text-xs rounded transition-all',
                      movementFilter === 'all' ? 'bg-echelon-cyan/20 text-echelon-cyan' : 'text-terminal-muted hover:text-terminal-text'
                    )}
                  >
                    All
                  </button>
                  <button
                    onClick={() => setMovementFilter('deploy')}
                    className={clsx(
                      'px-3 py-1 text-xs rounded transition-all',
                      movementFilter === 'deploy' ? 'bg-echelon-green/20 text-echelon-green' : 'text-terminal-muted hover:text-terminal-text'
                    )}
                  >
                    Deploy
                  </button>
                  <button
                    onClick={() => setMovementFilter('withdraw')}
                    className={clsx(
                      'px-3 py-1 text-xs rounded transition-all',
                      movementFilter === 'withdraw' ? 'bg-echelon-red/20 text-echelon-red' : 'text-terminal-muted hover:text-terminal-text'
                    )}
                  >
                    Withdraw
                  </button>
                  <button
                    onClick={() => setMovementFilter('strategy')}
                    className={clsx(
                      'px-3 py-1 text-xs rounded transition-all',
                      movementFilter === 'strategy' ? 'bg-echelon-amber/20 text-echelon-amber' : 'text-terminal-muted hover:text-terminal-text'
                    )}
                  >
                    Strategy
                  </button>
                </div>
                <div className="max-h-80 overflow-y-auto">
                  {filteredMovements.map((movement, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-3 px-4 py-2 border-b border-terminal-border/50 hover:bg-terminal-card/50 transition-colors"
                    >
                      <span className="font-mono text-xs text-terminal-muted w-16">{movement.time}</span>
                      <div className={clsx(
                        'w-6 h-6 rounded flex items-center justify-center text-xs font-bold',
                        movement.type === 'deploy' && 'bg-echelon-green/20 text-echelon-green',
                        movement.type === 'withdraw' && 'bg-echelon-red/20 text-echelon-red',
                        movement.type === 'strategy' && 'bg-echelon-amber/20 text-echelon-amber'
                      )}>
                        {movement.type === 'deploy' && <ArrowRight className="w-3 h-3" />}
                        {movement.type === 'withdraw' && <ArrowLeft className="w-3 h-3" />}
                        {movement.type === 'strategy' && <Zap className="w-3 h-3" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <span className="font-medium text-terminal-text">{movement.agent}</span>
                        <span className="text-terminal-muted text-xs"> {movement.action} </span>
                        <span className="text-echelon-cyan text-xs">{movement.theatre}</span>
                      </div>
                      <span className={clsx(
                        'text-xs font-mono font-bold',
                        movement.velocity.includes('+') && 'text-echelon-green',
                        movement.velocity.includes('-') && 'text-echelon-red',
                        movement.velocity === '~0' && 'text-terminal-muted'
                      )}>
                        {movement.velocity}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Strategy Clusters */}
            <div className="grid grid-cols-3 gap-4 mb-4">
              {mockClusters.map((cluster) => (
                <div key={cluster.name} className="bg-terminal-panel border border-terminal-border rounded-lg overflow-hidden">
                  <div className="flex items-center justify-between px-4 py-3 border-b border-terminal-border">
                    <div className="flex items-center gap-2">
                      <span>{cluster.emoji}</span>
                      <span className="font-semibold text-terminal-text">{cluster.name} Cluster</span>
                    </div>
                    <span className="text-xs text-terminal-muted">{cluster.count} agents</span>
                  </div>
                  <div className="p-4 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-terminal-muted">Focus</span>
                      <span className="text-terminal-text">{cluster.focus}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-terminal-muted">Avg Position</span>
                      <span className="text-terminal-text">{cluster.avgPosition}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-terminal-muted">Win Rate</span>
                      <span className={clsx(
                        'font-bold',
                        cluster.winRate >= 60 ? 'text-echelon-green' : cluster.winRate >= 40 ? 'text-echelon-amber' : 'text-echelon-red'
                      )}>
                        {cluster.winRate}%
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Agent Conflicts & Interactions */}
            <div className="bg-terminal-panel border border-terminal-border rounded-lg overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-3 border-b border-terminal-border">
                <AlertTriangle className="w-4 h-4 text-echelon-red" />
                <span className="font-semibold text-terminal-text">Agent Conflicts & Interactions</span>
              </div>
              <div className="p-4 space-y-3">
                {mockConflicts.map((conflict, idx) => (
                  <div
                    key={idx}
                    className={clsx(
                      'rounded border p-4',
                      conflict.severity === 'high' && 'border-echelon-red/50 bg-echelon-red/5',
                      conflict.severity === 'medium' && 'border-echelon-amber/50 bg-echelon-amber/5',
                      conflict.severity === 'low' && 'border-echelon-green/50 bg-echelon-green/5'
                    )}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <span className={clsx(
                        'text-xs font-bold px-2 py-0.5 rounded',
                        conflict.severity === 'high' && 'bg-echelon-red/20 text-echelon-red',
                        conflict.severity === 'medium' && 'bg-echelon-amber/20 text-echelon-amber',
                        conflict.severity === 'low' && 'bg-echelon-green/20 text-echelon-green'
                      )}>
                        {conflict.severity === 'high' && '⚠️ HIGH IMPACT'}
                        {conflict.severity === 'medium' && '🟡 MEDIUM'}
                        {conflict.severity === 'low' && '🟢 LOW'}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-terminal-text">
                        <span className="font-semibold">{conflict.agents[0]}</span>
                        <span className="text-terminal-muted mx-1">vs</span>
                        <span className="font-semibold">{conflict.agents[1]}</span>
                      </span>
                      <span className="text-xs text-echelon-cyan">{conflict.theatre}</span>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="text-terminal-muted">Opposing positions: <span className="text-terminal-text">{conflict.positions}</span></span>
                      <span className={clsx(
                        'font-medium',
                        conflict.impact > 0 ? 'text-echelon-green' : 'text-echelon-red'
                      )}>
                        Stability impact: {conflict.impact > 0 ? '+' : ''}{conflict.impact}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

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
