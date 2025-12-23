import { Link } from 'react-router-dom';
import { Bot, Heart, Zap, ExternalLink } from 'lucide-react';
import { clsx } from 'clsx';

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
  return (
    <div className="h-full overflow-y-auto">
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
        {mockAgents.map((agent) => (
          <div key={agent.id} className="terminal-panel p-4">
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className="text-3xl">{archetypeIcons[agent.archetype]}</div>
                <div>
                  <h3 className="font-bold text-terminal-text">{agent.name}</h3>
                  <div className="flex items-center gap-2">
                    <span
                      className={clsx(
                        'text-xs px-2 py-0.5 rounded',
                        archetypeColors[agent.archetype]
                      )}
                    >
                      {agent.archetype}
                    </span>
                    <span className="text-xs text-terminal-muted">Tier {agent.tier}</span>
                  </div>
                </div>
              </div>
              <Link
                to={`/agent/${agent.id}`}
                className="text-terminal-muted hover:text-echelon-cyan transition"
              >
                <ExternalLink className="w-4 h-4" />
              </Link>
            </div>

            {/* Sanity Bar */}
            <div className="mb-3">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-1 text-xs text-terminal-muted">
                  <Heart className="w-3 h-3" />
                  <span>Sanity</span>
                </div>
                <span
                  className={clsx(
                    'text-xs font-mono',
                    agent.sanity > 70
                      ? 'text-echelon-green'
                      : agent.sanity > 30
                      ? 'text-echelon-amber'
                      : 'text-echelon-red'
                  )}
                >
                  {agent.sanity}/{agent.max_sanity}
                </span>
              </div>
              <div className="h-2 bg-terminal-bg rounded-full overflow-hidden">
                <div
                  className={clsx(
                    'h-full rounded-full transition-all',
                    agent.sanity > 70
                      ? 'bg-echelon-green'
                      : agent.sanity > 30
                      ? 'bg-echelon-amber'
                      : 'bg-echelon-red'
                  )}
                  style={{ width: `${agent.sanity}%` }}
                />
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-2 mb-3">
              <div className="text-center p-2 bg-terminal-bg rounded">
                <div className="text-xs text-terminal-muted">P&L</div>
                <div
                  className={clsx(
                    'text-sm font-mono font-bold',
                    agent.total_pnl >= 0 ? 'text-echelon-green' : 'text-echelon-red'
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
            <div className="flex items-center justify-between p-2 bg-terminal-bg rounded">
              <div className="flex items-center gap-2">
                <Zap className="w-3 h-3 text-echelon-cyan" />
                <span className="text-xs text-echelon-cyan uppercase">
                  {agent.status.replace('_', ' ')}
                </span>
              </div>
              <span className="text-xs text-terminal-muted">{agent.current_timeline}</span>
            </div>
          </div>
        ))}

        {/* Add Agent Card */}
        <Link
          to="/agents"
          className="terminal-panel p-4 flex flex-col items-center justify-center min-h-[200px] border-dashed hover:border-echelon-cyan/50 transition"
        >
          <Bot className="w-8 h-8 text-terminal-muted mb-2" />
          <span className="text-sm text-terminal-muted">Hire New Agent</span>
        </Link>
      </div>
    </div>
  );
}

