import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Bot, Search, Filter, TrendingUp, Heart, Zap } from 'lucide-react';
import { clsx } from 'clsx';

const mockAgents = [
  { id: 'AGT_MEGALODON', name: 'MEGALODON', archetype: 'SHARK', tier: 2, pnl: 4520, winRate: 0.67, sanity: 78, available: true },
  { id: 'AGT_CARDINAL', name: 'CARDINAL', archetype: 'SPY', tier: 1, pnl: 1230, winRate: 0.58, sanity: 45, available: true },
  { id: 'AGT_ENVOY', name: 'ENVOY', archetype: 'DIPLOMAT', tier: 1, pnl: 890, winRate: 0.72, sanity: 92, available: false },
  { id: 'AGT_VIPER', name: 'VIPER', archetype: 'SABOTEUR', tier: 2, pnl: -340, winRate: 0.42, sanity: 33, available: true },
  { id: 'AGT_ORACLE', name: 'ORACLE', archetype: 'SPY', tier: 3, pnl: 8900, winRate: 0.71, sanity: 88, available: false },
  { id: 'AGT_LEVIATHAN', name: 'LEVIATHAN', archetype: 'WHALE', tier: 3, pnl: 23400, winRate: 0.65, sanity: 95, available: true },
];

const archetypeIcons: Record<string, string> = {
  SHARK: '🦈',
  SPY: '🕵️',
  DIPLOMAT: '🤝',
  SABOTEUR: '💣',
  WHALE: '🐋',
  DEGEN: '🎰',
};

const archetypeColors: Record<string, string> = {
  SHARK: 'border-agent-shark/50 hover:border-agent-shark',
  SPY: 'border-agent-spy/50 hover:border-agent-spy',
  DIPLOMAT: 'border-agent-diplomat/50 hover:border-agent-diplomat',
  SABOTEUR: 'border-agent-saboteur/50 hover:border-agent-saboteur',
  WHALE: 'border-agent-whale/50 hover:border-agent-whale',
};

export function AgentRoster() {
  const [search, setSearch] = useState('');
  const [filterArchetype, setFilterArchetype] = useState<string>('ALL');

  const archetypes = ['ALL', 'SHARK', 'SPY', 'DIPLOMAT', 'SABOTEUR', 'WHALE'];

  const filteredAgents = mockAgents.filter((agent) => {
    const matchesSearch = agent.name.toLowerCase().includes(search.toLowerCase());
    const matchesArchetype = filterArchetype === 'ALL' || agent.archetype === filterArchetype;
    return matchesSearch && matchesArchetype;
  });

  return (
    <div className="h-full flex flex-col p-4 gap-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Bot className "w-6 h-6 text-echelon-cyan" />
          <h1 className="text-lg font-display text-terminal-text tracking-wider">
            Agent Marketplace
          </h1>
        </div>
        <span className="text-xs text-terminal-muted">
          {filteredAgents.length} agents available
        </span>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-terminal-muted" />
          <input
            type="text"
            placeholder="Search agents..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-terminal-bg border border-terminal-border rounded text-sm text-terminal-text placeholder:text-terminal-muted focus:border-echelon-cyan focus:outline-none"
          />
        </div>
        <div className="flex items-center gap-1">
          <Filter className="w-4 h-4 text-terminal-muted mr-2" />
          {archetypes.map((arch) => (
            <button
              key={arch}
              onClick={() => setFilterArchetype(arch)}
              className={clsx(
                'px-3 py-1.5 text-xs rounded transition',
                filterArchetype === arch
                  ? 'bg-echelon-cyan/20 text-echelon-cyan border border-echelon-cyan/30'
                  : 'bg-terminal-bg text-terminal-muted hover:text-terminal-text'
              )}
            >
              {arch === 'ALL' ? 'All' : archetypeIcons[arch]}
            </button>
          ))}
        </div>
      </div>

      {/* Agent Grid */}
      <div className="flex-1 overflow-y-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredAgents.map((agent) => (
            <Link
              key={agent.id}
              to={`/agent/${agent.id}`}
              className={clsx(
                'terminal-panel p-4 transition-all',
                archetypeColors[agent.archetype]
              )}
            >
              {/* Header */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{archetypeIcons[agent.archetype]}</span>
                  <div>
                    <h3 className="font-bold text-terminal-text">{agent.name}</h3>
                    <span className="text-xs text-terminal-muted">
                      {agent.archetype} • Tier {agent.tier}
                    </span>
                  </div>
                </div>
                {agent.available ? (
                  <span className="text-xs px-2 py-1 bg-echelon-green/20 text-echelon-green rounded">
                    Available
                  </span>
                ) : (
                  <span className="text-xs px-2 py-1 bg-terminal-bg text-terminal-muted rounded">
                    Hired
                  </span>
                )}
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-2 mb-3">
                <div className="text-center p-2 bg-terminal-bg rounded">
                  <TrendingUp className="w-3 h-3 mx-auto mb-1 text-terminal-muted" />
                  <div
                    className={clsx(
                      'text-sm font-mono font-bold',
                      agent.pnl >= 0 ? 'text-echelon-green' : 'text-echelon-red'
                    )}
                  >
                    ${Math.abs(agent.pnl).toLocaleString()}
                  </div>
                </div>
                <div className="text-center p-2 bg-terminal-bg rounded">
                  <Zap className="w-3 h-3 mx-auto mb-1 text-terminal-muted" />
                  <div className="text-sm font-mono font-bold text-terminal-text">
                    {(agent.winRate * 100).toFixed(0)}%
                  </div>
                </div>
                <div className="text-center p-2 bg-terminal-bg rounded">
                  <Heart className="w-3 h-3 mx-auto mb-1 text-terminal-muted" />
                  <div
                    className={clsx(
                      'text-sm font-mono font-bold',
                      agent.sanity > 70
                        ? 'text-echelon-green'
                        : agent.sanity > 30
                        ? 'text-echelon-amber'
                        : 'text-echelon-red'
                    )}
                  >
                    {agent.sanity}%
                  </div>
                </div>
              </div>

              {/* Hire Button */}
              {agent.available && (
                <button className="w-full py-2 bg-echelon-cyan/20 border border-echelon-cyan text-echelon-cyan rounded text-sm hover:bg-echelon-cyan/30 transition">
                  Hire Agent
                </button>
              )}
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

