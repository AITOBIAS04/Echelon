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
  PieChart,
  BarChart3,
  Brain,
  Target,
  Zap as ZapIcon,
} from 'lucide-react';
import { useAgents } from '../../hooks/useAgents';
import { AgentSanityIndicator } from './AgentSanityIndicator';
import { TaskAgentModal } from './TaskAgentModal';
import { useAgentsUi } from '../../contexts/AgentsUiContext';
import { useRegisterTopActionBarActions } from '../../contexts/TopActionBarActionsContext';
import {
  getArchetypeTheme,
  getSanityTheme,
  getTheatreTheme,
  getMovementTheme,
  getVelocityTheme,
  getConflictTheme,
  getClusterTheme,
} from '../../theme/agentsTheme';
import { clsx } from 'clsx';

// ============================================================================
// Mock Data for Global Intelligence Dashboard
// ============================================================================

const mockStats = {
  totalAgents: 12,
  deployedAgents: 8,
  movements24h: 47,
  activeConflicts: 3,
};

const mockTheatres = [
  { name: 'ORB_SALVAGE_F7', agents: 12, activity: 'high' as const, stability: 87, volume: '$142K', gap: 12 },
  { name: 'VEN_OIL_TANKER', agents: 8, activity: 'medium' as const, stability: 92, volume: '$89K', gap: 8 },
  { name: 'FED_RATE_DECISION', agents: 15, activity: 'high' as const, stability: 78, volume: '$215K', gap: 18 },
  { name: 'TAIWAN_STRAIT', agents: 5, activity: 'low' as const, stability: 95, volume: '$45K', gap: 5 },
  { name: 'NVDA_EARNINGS', agents: 9, activity: 'medium' as const, stability: 84, volume: '$128K', gap: 14 },
  { name: 'BTC_HALVING', agents: 4, activity: 'low' as const, stability: 97, volume: '$32K', gap: 3 },
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
  { name: 'SHARK', icon: Target, count: 12, focus: 'High-volatility', avgPosition: '$8,450', winRate: 68 },
  { name: 'DIPLOMAT', icon: Users, count: 8, focus: 'Stability', avgPosition: '$4,200', winRate: 72 },
  { name: 'SABOTEUR', icon: ZapIcon, count: 6, focus: 'Adversarial', avgPosition: '$3,800', winRate: 42 },
];

const mockConflicts = [
  { severity: 'high' as const, agents: ['VIPER', 'CHAOS'], theatre: 'ORB_SALVAGE_F7', positions: '$12,450 vs $8,200', impact: -15 },
  { severity: 'medium' as const, agents: ['LEVIATHAN', 'TITAN'], theatre: 'FED_RATE_DECISION', positions: '$24,500 vs $18,200', impact: 8 },
  { severity: 'low' as const, agents: ['AEGIS', 'SABOTEUR'], theatre: 'VEN_OIL_TANKER', positions: '$6,800 vs $5,200', impact: -5 },
];

// Mock archetype data for sidebar
const mockArchetypes = [
  { name: 'WHALE', count: 3 },
  { name: 'DIPLOMAT', count: 3 },
  { name: 'SABOTEUR', count: 2 },
  { name: 'SHARK', count: 2 },
  { name: 'SPY', count: 2 },
];

const mockPerformanceSummary = {
  totalPL: '$482,340',
  winRate: '68%',
  totalActions: '12,847',
  avgSanity: '72/100',
  genesisAgents: 4,
};

const mockSanityDistribution = {
  stable: 7,
  stressed: 3,
  critical: 1,
  breakdown: 1,
};

// ============================================================================
// Agent Roster Component
// ============================================================================

export function AgentRoster() {
  const { data: agentsData, isLoading } = useAgents();
  const agents = agentsData?.agents || [];
  const [taskingAgent, setTaskingAgent] = useState<any | null>(null);
  const [movementFilter, setMovementFilter] = useState<string>('all');
  const [movements, setMovements] = useState(mockMovements);

  // Helper function to get cluster icon
  const getClusterIcon = (name: string) => {
    switch (name) {
      case 'SHARK': return Target;
      case 'DIPLOMAT': return Users;
      case 'SABOTEUR': return ZapIcon;
      default: return Target;
    }
  };

  // Use context for tab state - THIS IS THE KEY FIX
  const { activeTab, setActiveTab } = useAgentsUi();

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
        <div className="flex-1 flex min-h-0">
          {/* Left Panel - Agent Grid */}
          <div className="flex-1 overflow-y-auto p-6">
            <div className="max-w-5xl mx-auto pr-4">
              <div className="flex items-center justify-between mb-6">
                <h1 className="text-2xl font-bold text-cyan-400 flex items-center gap-3">
                  <User className="w-6 h-6" />
                  AGENT ROSTER
                </h1>
                <span className="text-slate-500 text-sm">
                  {agents.length} agents active
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {agents.map((agent) => {
                  const sanity = agent.sanity || 75;
                  const maxSanity = agent.max_sanity || 100;
                  const sanityPercent = (sanity / maxSanity) * 100;
                  const lineage = getMockLineage(agent.name);
                  const archetypeTheme = getArchetypeTheme(agent.archetype);
                  const sanityTheme = getSanityTheme(sanityPercent);
                  const isPositivePL = (agent.total_pnl_usd || 0) >= 0;

                  return (
                    <div
                      key={agent.id}
                      className={clsx(
                        'bg-slate-900 border rounded-lg p-4 transition-all group relative overflow-hidden',
                        archetypeTheme.borderClass,
                        sanityTheme.cardHoverClass,
                        sanityTheme.glowClass
                      )}
                    >
                      {/* Glitch overlay for breakdown state */}
                      {sanityPercent <= 20 && (
                        <div
                          className="absolute inset-0 pointer-events-none opacity-20"
                          style={{
                            background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,0,0,0.1) 2px, rgba(255,0,0,0.1) 4px)',
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
                              {archetypeTheme.emoji}
                            </span>
                            <div>
                              <h3 className={clsx(
                                'font-bold transition',
                                sanityPercent <= 20 ? 'text-rose-500' : 'text-slate-200 group-hover:text-cyan-400'
                              )}>
                                {agent.name}
                              </h3>
                              <span className={clsx(
                                'text-xs uppercase',
                                archetypeTheme.textClass
                              )}>
                                {agent.archetype}
                              </span>
                            </div>
                          </div>
                          <span className={clsx(
                            'text-lg font-mono font-bold',
                            isPositivePL ? 'text-emerald-400' : 'text-rose-500'
                          )}>
                            ${(agent.total_pnl_usd || 0).toLocaleString()}
                          </span>
                        </div>
                      </Link>

                      {/* Genealogy Metadata */}
                      <div className="flex items-center gap-2 mt-2 text-xs relative z-10">
                        <span className={clsx(
                          'border px-2 py-0.5 rounded font-mono',
                          archetypeTheme.bgClass,
                          archetypeTheme.borderClass,
                          archetypeTheme.textClass
                        )}>
                          GEN {lineage.gen}
                        </span>
                        <span className="text-slate-500">•</span>
                        <span className="text-slate-500">
                          {lineage.parents === 'GENESIS' ? (
                            <span className="text-cyan-400/60">GENESIS AGENT</span>
                          ) : (
                            <>LINEAGE: <span className="text-purple-400">{lineage.parents}</span></>
                          )}
                        </span>
                      </div>

                      <div className="flex items-center justify-between text-xs text-slate-500 mb-3 mt-2 relative z-10">
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
                      <div className="flex gap-2 mt-4 pt-3 border-t border-slate-700 relative z-10">
                        {(agent.archetype === 'SPY' || agent.archetype === 'SHARK') && (
                          <button
                            onClick={(e) => handleTaskAgent(agent, e)}
                            className={clsx(
                              'flex-1 px-3 py-2 border rounded text-sm font-bold transition-all flex items-center justify-center gap-2',
                              archetypeTheme.bgClass,
                              archetypeTheme.borderClass,
                              archetypeTheme.textClass,
                              `hover:${archetypeTheme.bgClass.replace('/10', '/20')}`
                            )}
                          >
                            <Search className="w-4 h-4" />
                            TASK
                          </button>
                        )}

                        <button
                          onClick={(e) => handleCopyAgent(agent, e)}
                          className="flex-1 px-3 py-2 border rounded text-sm font-bold transition-all flex items-center justify-center gap-2 bg-cyan-500/20 border-cyan-500/50 text-cyan-400 hover:bg-cyan-500/30"
                        >
                          <Copy className="w-4 h-4" />
                          COPY
                        </button>

                        <button
                          onClick={(e) => handleHireAgent(agent, e)}
                          className="px-3 py-2 border rounded text-sm font-bold transition-all bg-amber-500/20 border-amber-500/50 text-amber-400 hover:bg-amber-500/30"
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

          {/* Right Sidebar - Panels */}
          <aside className="w-72 flex-shrink-0 overflow-y-auto border-l border-slate-700 bg-slate-900/50">
            {/* Archetype Distribution */}
            <div className="p-4 border-b border-slate-700">
              <div className="flex items-center gap-2 mb-3">
                <PieChart className="w-4 h-4 text-cyan-400" />
                <h3 className="font-semibold text-slate-200">Archetype Distribution</h3>
              </div>
              <div className="space-y-2">
                {mockArchetypes.map((archetype) => {
                  const theme = getArchetypeTheme(archetype.name);
                  return (
                    <div key={archetype.name} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <span className={theme.textClass}>{theme.emoji}</span>
                        <span className="text-slate-500">{archetype.name}</span>
                      </div>
                      <span className="font-mono text-slate-300">{archetype.count}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Performance Summary */}
            <div className="p-4 border-b border-slate-700">
              <div className="flex items-center gap-2 mb-3">
                <BarChart3 className="w-4 h-4 text-emerald-400" />
                <h3 className="font-semibold text-slate-200">Performance Summary</h3>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Total P/L</span>
                  <span className="font-mono font-bold text-emerald-400">{mockPerformanceSummary.totalPL}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Win Rate</span>
                  <span className="font-mono text-slate-300">{mockPerformanceSummary.winRate}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Total Actions</span>
                  <span className="font-mono text-slate-300">{mockPerformanceSummary.totalActions}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Avg Sanity</span>
                  <span className="font-mono text-slate-300">{mockPerformanceSummary.avgSanity}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Genesis Agents</span>
                  <span className="font-mono text-slate-300">{mockPerformanceSummary.genesisAgents}</span>
                </div>
              </div>
            </div>

            {/* Sanity Distribution */}
            <div className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Brain className="w-4 h-4 text-purple-400" />
                <h3 className="font-semibold text-slate-200">Sanity Distribution</h3>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">STABLE (70-100)</span>
                  <span className="font-mono text-emerald-400">{mockSanityDistribution.stable} agents</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">STRESSED (40-69)</span>
                  <span className="font-mono text-amber-400">{mockSanityDistribution.stressed} agents</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">CRITICAL (20-39)</span>
                  <span className="font-mono text-rose-400">{mockSanityDistribution.critical} agent</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">BREAKDOWN (&lt;20)</span>
                  <span className="font-mono text-red-500">{mockSanityDistribution.breakdown} agent</span>
                </div>
              </div>
            </div>
          </aside>
        </div>
      )}

      {/* Global Intelligence View */}
      {activeTab === 'intel' && (
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto">
            {/* Stats Row - KPI Cards */}
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="w-10 h-10 rounded bg-cyan-500/20 flex items-center justify-center">
                    <Users className="w-5 h-5 text-cyan-400" />
                  </div>
                  <span className="text-xs text-emerald-400">+2 this week</span>
                </div>
                <div className="text-2xl font-bold text-slate-200">{mockStats.totalAgents}</div>
                <div className="text-sm text-slate-500">Total Agents</div>
              </div>

              <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="w-10 h-10 rounded bg-emerald-500/20 flex items-center justify-center">
                    <MapPin className="w-5 h-5 text-emerald-400" />
                  </div>
                  <span className="text-xs text-slate-500">67% utilization</span>
                </div>
                <div className="text-2xl font-bold text-slate-200">{mockStats.deployedAgents}</div>
                <div className="text-sm text-slate-500">Deployed</div>
              </div>

              <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="w-10 h-10 rounded bg-purple-500/20 flex items-center justify-center">
                    <History className="w-5 h-5 text-purple-400" />
                  </div>
                  <span className="text-xs text-emerald-400">+12 from yesterday</span>
                </div>
                <div className="text-2xl font-bold text-slate-200">{mockStats.movements24h}</div>
                <div className="text-sm text-slate-500">Movements (24h)</div>
              </div>

              <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="w-10 h-10 rounded bg-rose-500/20 flex items-center justify-center">
                    <AlertTriangle className="w-5 h-5 text-rose-400" />
                  </div>
                  <span className="text-xs text-emerald-400">-1 from yesterday</span>
                </div>
                <div className="text-2xl font-bold text-slate-200">{mockStats.activeConflicts}</div>
                <div className="text-sm text-slate-500">Active Conflicts</div>
              </div>
            </div>

            {/* Dashboard Grid */}
            <div className="grid grid-cols-2 gap-4 mb-4">
              {/* Deployment Heat Map */}
              <div className="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
                <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-cyan-400" />
                    <span className="font-semibold text-slate-200">Deployment Heat Map</span>
                  </div>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    <span className="text-xs text-slate-500">LIVE</span>
                  </span>
                </div>
                <div className="p-4">
                  <div className="grid grid-cols-2 gap-3">
                    {mockTheatres.map((theatre) => {
                      const theatreTheme = getTheatreTheme(theatre.activity);
                      return (
                        <div
                          key={theatre.name}
                          className={clsx(
                            'rounded border p-3 transition-all',
                            theatreTheme.borderClass,
                            theatreTheme.bgClass
                          )}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-mono text-xs text-slate-300">{theatre.name}</span>
                            <span className={clsx('text-xs font-medium', theatreTheme.textClass)}>
                              {theatreTheme.indicator}
                            </span>
                          </div>
                          <div className="flex items-center gap-3 text-xs text-slate-500">
                            <span>{theatre.agents} agents</span>
                          </div>
                          <div className="flex items-center gap-3 mt-2 text-xs">
                            <span><span className="text-slate-500">Stab</span> <span className="text-slate-300">{theatre.stability}%</span></span>
                            <span><span className="text-slate-500">Vol</span> <span className="text-slate-300">{theatre.volume}</span></span>
                            <span><span className="text-slate-500">Gap</span> <span className="text-slate-300">{theatre.gap}%</span></span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Movement Feed */}
              <div className="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
                <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700">
                  <div className="flex items-center gap-2">
                    <History className="w-4 h-4 text-purple-400" />
                    <span className="font-semibold text-slate-200">Movement Feed</span>
                  </div>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    <span className="text-xs text-slate-500">LIVE</span>
                  </span>
                </div>
                <div className="flex items-center gap-1 px-4 py-2 border-b border-slate-700">
                  <button
                    onClick={() => setMovementFilter('all')}
                    className={clsx(
                      'px-3 py-1 text-xs rounded transition-all',
                      movementFilter === 'all' ? 'bg-cyan-500/20 text-cyan-400' : 'text-slate-500 hover:text-slate-300'
                    )}
                  >
                    All
                  </button>
                  <button
                    onClick={() => setMovementFilter('deploy')}
                    className={clsx(
                      'px-3 py-1 text-xs rounded transition-all',
                      movementFilter === 'deploy' ? 'bg-emerald-500/20 text-emerald-400' : 'text-slate-500 hover:text-slate-300'
                    )}
                  >
                    Deploy
                  </button>
                  <button
                    onClick={() => setMovementFilter('withdraw')}
                    className={clsx(
                      'px-3 py-1 text-xs rounded transition-all',
                      movementFilter === 'withdraw' ? 'bg-rose-500/20 text-rose-400' : 'text-slate-500 hover:text-slate-300'
                    )}
                  >
                    Withdraw
                  </button>
                  <button
                    onClick={() => setMovementFilter('strategy')}
                    className={clsx(
                      'px-3 py-1 text-xs rounded transition-all',
                      movementFilter === 'strategy' ? 'bg-amber-500/20 text-amber-400' : 'text-slate-500 hover:text-slate-300'
                    )}
                  >
                    Strategy
                  </button>
                </div>
                <div className="max-h-80 overflow-y-auto">
                  {filteredMovements.map((movement, idx) => {
                    const movementTheme = getMovementTheme(movement.type);
                    const velocityTheme = getVelocityTheme(movement.velocity);
                    return (
                      <div
                        key={idx}
                        className="flex items-center gap-3 px-4 py-2 border-b border-slate-800 hover:bg-slate-800/50 transition-colors"
                      >
                        <span className="font-mono text-xs text-slate-500 w-16">{movement.time}</span>
                        <div className={clsx(
                          'w-6 h-6 rounded flex items-center justify-center text-xs font-bold',
                          movementTheme.bgClass,
                          movementTheme.textClass
                        )}>
                          {movement.type === 'deploy' && <ArrowRight className="w-3 h-3" />}
                          {movement.type === 'withdraw' && <ArrowLeft className="w-3 h-3" />}
                          {movement.type === 'strategy' && <Zap className="w-3 h-3" />}
                        </div>
                        <div className="flex-1 min-w-0">
                          <span className="font-medium text-slate-300">{movement.agent}</span>
                          <span className="text-slate-500 text-xs"> {movement.action} </span>
                          <span className="text-cyan-400 text-xs">{movement.theatre}</span>
                        </div>
                        <span className={clsx('text-xs font-mono font-bold', velocityTheme.colorClass)}>
                          {movement.velocity}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Strategy Clusters */}
            <div className="grid grid-cols-3 gap-4 mb-4">
              {mockClusters.map((cluster) => {
                const clusterTheme = getClusterTheme(cluster.winRate);
                const ClusterIcon = getClusterIcon(cluster.name);
                return (
                  <div key={cluster.name} className="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
                    <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700">
                      <div className="flex items-center gap-2">
                        <ClusterIcon className="w-4 h-4 text-cyan-400" />
                        <span className="font-semibold text-slate-200">{cluster.name} Cluster</span>
                      </div>
                      <span className="text-xs text-slate-500">{cluster.count} agents</span>
                    </div>
                    <div className="p-4 space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-500">Focus</span>
                        <span className="text-slate-300">{cluster.focus}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-500">Avg Position</span>
                        <span className="text-slate-300">{cluster.avgPosition}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-500">Win Rate</span>
                        <span className={clsx(
                          'font-bold',
                          cluster.winRate >= 60 ? clusterTheme.winRateGoodClass : cluster.winRate >= 40 ? clusterTheme.winRateWarningClass : clusterTheme.winRateDangerClass
                        )}>
                          {cluster.winRate}%
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Agent Conflicts & Interactions */}
            <div className="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-700">
                <AlertTriangle className="w-4 h-4 text-rose-400" />
                <span className="font-semibold text-slate-200">Agent Conflicts & Interactions</span>
              </div>
              <div className="p-4 space-y-3">
                {mockConflicts.map((conflict, idx) => {
                  const conflictTheme = getConflictTheme(conflict.severity, conflict.impact);
                  return (
                    <div
                      key={idx}
                      className={clsx(
                        'rounded border p-4',
                        conflictTheme.borderClass,
                        conflictTheme.bgClass
                      )}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <span className={clsx(
                          'text-xs font-bold px-2 py-0.5 rounded',
                          conflictTheme.badgeBgClass,
                          conflictTheme.badgeTextClass
                        )}>
                          {conflictTheme.badge}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-slate-300">
                          <span className="font-semibold">{conflict.agents[0]}</span>
                          <span className="text-slate-500 mx-1">vs</span>
                          <span className="font-semibold">{conflict.agents[1]}</span>
                        </span>
                        <span className="text-xs text-cyan-400">{conflict.theatre}</span>
                      </div>
                      <div className="flex items-center gap-4 text-sm">
                        <span className="text-slate-500">Opposing positions: <span className="text-slate-300">{conflict.positions}</span></span>
                        <span className={clsx('font-medium', conflictTheme.impactClass)}>
                          Stability impact: {conflict.impact > 0 ? '+' : ''}{conflict.impact}%
                        </span>
                      </div>
                    </div>
                  );
                })}
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
