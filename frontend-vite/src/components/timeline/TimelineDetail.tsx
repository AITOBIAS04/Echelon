import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Users, AlertTriangle, Clock } from 'lucide-react';
import { clsx } from 'clsx';

// Mock data - would fetch by timelineId
const mockTimeline = {
  id: 'TL_CONTAGION',
  name: 'Contagion Zero - Mumbai Outbreak',
  narrative: 'What if the unusual respiratory illness cluster in Mumbai is the start of a new pandemic?',
  price_yes: 0.82,
  price_no: 0.18,
  stability: 23.4,
  logic_gap: 47,
  gravity_score: 84,
  total_volume_usd: 340000,
  liquidity_depth_usd: 45000,
  active_agent_count: 28,
  has_active_paradox: true,
  paradox_detonation: '2h 49m 19s',
  decay_rate_per_hour: 5,
  connected_timelines: ['TL_FED_RATE', 'TL_PHARMA'],
};

export function TimelineDetail() {
  const { timelineId } = useParams();

  return (
    <div className="h-full flex flex-col p-4 gap-4 overflow-y-auto">
      {/* Back Link */}
      <Link
        to="/"
        className="flex items-center gap-2 text-terminal-muted hover:text-echelon-cyan transition w-fit"
      >
        <ArrowLeft className="w-4 h-4" />
        <span className="text-sm">Back to SIGINT</span>
      </Link>

      {/* Paradox Warning */}
      {mockTimeline.has_active_paradox && (
        <div className="terminal-panel p-4 border-echelon-red/50 bg-echelon-red/10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-6 h-6 text-echelon-red animate-pulse" />
              <div>
                <h3 className="font-bold text-echelon-red">ACTIVE CONTAINMENT BREACH</h3>
                <p className="text-sm text-terminal-muted">
                  Logic Gap: {mockTimeline.logic_gap}% | Decay: {mockTimeline.decay_rate_per_hour}x
                </p>
              </div>
            </div>
            <div className="text-right">
              <div className="flex items-center gap-2 text-echelon-red">
                <Clock className="w-4 h-4" />
                <span className="font-mono text-xl">{mockTimeline.paradox_detonation}</span>
              </div>
              <span className="text-xs text-terminal-muted">until detonation</span>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="grid grid-cols-3 gap-4">
        {/* Left Column - Info */}
        <div className="col-span-2 space-y-4">
          {/* Header */}
          <div className="terminal-panel p-4">
            <h1 className="text-xl font-bold text-terminal-text mb-2">{mockTimeline.name}</h1>
            <p className="text-sm text-terminal-muted mb-4">{mockTimeline.narrative}</p>
            <div className="flex items-center gap-4 text-xs text-terminal-muted">
              <span>{mockTimeline.id}</span>
              <span>G: {mockTimeline.gravity_score}</span>
              <span className="flex items-center gap-1">
                <Users className="w-3 h-3" />
                {mockTimeline.active_agent_count} agents
              </span>
            </div>
          </div>

          {/* Price Cards */}
          <div className="grid grid-cols-2 gap-4">
            <div className="terminal-panel p-4 border-echelon-green/30">
              <div className="text-sm text-terminal-muted mb-1">YES</div>
              <div className="text-4xl font-mono font-bold text-echelon-green mb-2">
                ${mockTimeline.price_yes.toFixed(2)}
              </div>
              <button className="w-full py-2 bg-echelon-green/20 border border-echelon-green text-echelon-green rounded hover:bg-echelon-green/30 transition">
                Buy YES
              </button>
            </div>
            <div className="terminal-panel p-4 border-echelon-red/30">
              <div className="text-sm text-terminal-muted mb-1">NO</div>
              <div className="text-4xl font-mono font-bold text-echelon-red mb-2">
                ${mockTimeline.price_no.toFixed(2)}
              </div>
              <button className="w-full py-2 bg-echelon-red/20 border border-echelon-red text-echelon-red rounded hover:bg-echelon-red/30 transition">
                Buy NO
              </button>
            </div>
          </div>

          {/* Stats */}
          <div className="terminal-panel p-4">
            <h3 className="terminal-header mb-3">Timeline Metrics</h3>
            <div className="grid grid-cols-4 gap-4">
              <div>
                <div className="text-xs text-terminal-muted mb-1">Volume (24h)</div>
                <div className="font-mono text-terminal-text">
                  ${(mockTimeline.total_volume_usd / 1000).toFixed(0)}K
                </div>
              </div>
              <div>
                <div className="text-xs text-terminal-muted mb-1">Liquidity</div>
                <div className="font-mono text-terminal-text">
                  ${(mockTimeline.liquidity_depth_usd / 1000).toFixed(0)}K
                </div>
              </div>
              <div>
                <div className="text-xs text-terminal-muted mb-1">Logic Gap</div>
                <div
                  className={clsx(
                    'font-mono',
                    mockTimeline.logic_gap > 40 ? 'text-echelon-red' : 'text-terminal-text'
                  )}
                >
                  {mockTimeline.logic_gap}%
                </div>
              </div>
              <div>
                <div className="text-xs text-terminal-muted mb-1">Decay Rate</div>
                <div className="font-mono text-echelon-amber">{mockTimeline.decay_rate_per_hour}%/hr</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column - Stability & Actions */}
        <div className="space-y-4">
          {/* Stability */}
          <div className="terminal-panel p-4">
            <h3 className="terminal-header mb-3">Stability</h3>
            <div className="relative h-32 flex items-center justify-center">
              <div
                className={clsx(
                  'text-5xl font-mono font-bold',
                  mockTimeline.stability > 70
                    ? 'text-echelon-green'
                    : mockTimeline.stability > 40
                    ? 'text-echelon-amber'
                    : 'text-echelon-red glow-red'
                )}
              >
                {mockTimeline.stability.toFixed(1)}%
              </div>
            </div>
            <div className="h-2 bg-terminal-bg rounded-full overflow-hidden">
              <div
                className={clsx(
                  'h-full rounded-full transition-all',
                  mockTimeline.stability > 70
                    ? 'bg-echelon-green'
                    : mockTimeline.stability > 40
                    ? 'bg-echelon-amber'
                    : 'bg-echelon-red'
                )}
                style={{ width: `${mockTimeline.stability}%` }}
              />
            </div>
          </div>

          {/* Connected Timelines */}
          <div className="terminal-panel p-4">
            <h3 className="terminal-header mb-3">Ripple Targets</h3>
            <div className="space-y-2">
              {mockTimeline.connected_timelines.map((tl) => (
                <Link
                  key={tl}
                  to={`/timeline/${tl}`}
                  className="block p-2 bg-terminal-bg rounded text-sm text-terminal-muted hover:text-echelon-cyan transition"
                >
                  → {tl}
                </Link>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="terminal-panel p-4">
            <h3 className="terminal-header mb-3">Actions</h3>
            <div className="space-y-2">
              <button className="w-full py-2 bg-echelon-cyan/20 border border-echelon-cyan text-echelon-cyan rounded text-sm hover:bg-echelon-cyan/30 transition">
                Deploy Shield
              </button>
              <button className="w-full py-2 bg-terminal-bg border border-terminal-border text-terminal-muted rounded text-sm hover:border-echelon-purple hover:text-echelon-purple transition">
                Create Fork
              </button>
              <button className="w-full py-2 bg-terminal-bg border border-terminal-border text-terminal-muted rounded text-sm hover:border-echelon-amber hover:text-echelon-amber transition">
                Add to Watchlist
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

