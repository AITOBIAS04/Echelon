import type { WingFlap, AgentArchetype } from '../../types';
import { clsx } from 'clsx';

interface WingFlapFeedProps {
  flaps: WingFlap[];
  isLoading?: boolean;
}

const archetypeColors: Record<AgentArchetype, string> = {
  SHARK: 'text-agent-shark',
  SPY: 'text-agent-spy',
  DIPLOMAT: 'text-agent-diplomat',
  SABOTEUR: 'text-agent-saboteur',
  WHALE: 'text-agent-whale',
  DEGEN: 'text-terminal-muted',
};

const flapTypeIcons: Record<string, string> = {
  TRADE: '💹',
  SHIELD: '🛡️',
  SABOTAGE: '💣',
  RIPPLE: '🌊',
  PARADOX: '⚠️',
  FOUNDER_YIELD: '💰',
};

export function WingFlapFeed({ flaps, isLoading }: WingFlapFeedProps) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="terminal-panel p-3 h-20 animate-pulse" />
        ))}
      </div>
    );
  }

  if (flaps.length === 0) {
    return (
      <div className="p-4 text-center text-terminal-muted">
        No recent activity
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {flaps.map((flap) => (
        <WingFlapItem key={flap.id} flap={flap} />
      ))}
    </div>
  );
}

function WingFlapItem({ flap }: { flap: WingFlap }) {
  const timestamp = new Date(flap.timestamp);
  const timeAgo = getTimeAgo(timestamp);
  
  return (
    <div className="terminal-panel p-3 hover:bg-terminal-bg/50 transition">
      {/* Agent + Time */}
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <span>{flapTypeIcons[flap.flap_type] || '•'}</span>
          <span className={clsx('font-medium', archetypeColors[flap.agent_archetype])}>
            {flap.agent_name}
          </span>
          <span className="text-xs px-1.5 py-0.5 bg-terminal-bg rounded text-terminal-muted">
            {flap.agent_archetype}
          </span>
        </div>
        <span className="text-xs text-terminal-muted">{timeAgo}</span>
      </div>

      {/* Action */}
      <p className="text-sm text-terminal-text mb-2">
        {flap.action}
      </p>

      {/* Impact */}
      <div className="flex items-center gap-3 text-xs">
        <span className={clsx(
          'font-mono',
          flap.direction === 'ANCHOR' ? 'text-echelon-green' : 'text-echelon-red'
        )}>
          {flap.direction === 'ANCHOR' ? '+' : ''}{flap.stability_delta.toFixed(2)}%
        </span>
        <span className="text-terminal-muted">
          ${flap.volume_usd.toLocaleString(undefined, { maximumFractionDigits: 0 })}
        </span>
        <span className="text-terminal-muted truncate flex-1">
          → {flap.timeline_name}
        </span>
        {flap.spawned_ripple && (
          <span className="text-echelon-purple">🌊 Ripple</span>
        )}
      </div>
    </div>
  );
}

function getTimeAgo(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}
