import { TrendingUp, TrendingDown, AlertTriangle, Users, DollarSign, Zap } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { Timeline } from '../../types';
import { clsx } from 'clsx';

interface TimelineCardProps {
  timeline: Timeline;
  onClick?: () => void;
}

export function TimelineCard({ timeline, onClick }: TimelineCardProps) {
  // Calculate glow intensity based on gravity
  const gravityScore = timeline.gravity_score ?? 50;
  const glowIntensity = Math.min(gravityScore / 100, 1);
  const glowColor = gravityScore > 70 ? 'rgba(239, 68, 68,' :
                    gravityScore > 40 ? 'rgba(245, 158, 11,' :
                    'rgba(6, 182, 212,';

  return (
    <Link
      to={`/timeline/${timeline.id}`}
      onClick={onClick}
      className={clsx(
        'terminal-card block p-4 cursor-pointer transition-all hover:scale-[1.02]',
        gravityScore > 70 ? 'border-echelon-red/50' :
        gravityScore > 40 ? 'border-echelon-amber/30' : 'border-terminal-border',
        timeline.has_active_paradox && 'border-echelon-red/50 animate-pulse-slow'
      )}
      style={{
        boxShadow: gravityScore > 40
          ? `0 0 ${20 * glowIntensity}px ${glowColor}${glowIntensity * 0.3})`
          : 'none',
      }}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-terminal-text truncate">
            {timeline.name}
          </h3>
          <p className="text-xs text-terminal-text-muted mt-0.5">
            {timeline.id}
          </p>
          {/* Founder & Meta Badges */}
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            {/* Gravity Score Badge */}
            <div
              className="flex items-center gap-1.5 px-2 py-1 rounded border"
              style={{
                background: `rgba(${
                  gravityScore > 70 ? '239, 68, 68' :
                  gravityScore > 40 ? '245, 158, 11' :
                  '34, 197, 94'
                }, 0.2)`,
                borderColor: `rgba(${
                  gravityScore > 70 ? '239, 68, 68' :
                  gravityScore > 40 ? '245, 158, 11' :
                  '34, 197, 94'
                }, 0.5)`,
              }}
              title="Gravity Score - Higher means more agent activity and market interest"
            >
              <span className="text-[10px] text-terminal-text-muted uppercase tracking-wide">G</span>
              <span className={clsx(
                'text-sm font-mono font-bold',
                gravityScore > 70 ? 'text-echelon-red' :
                gravityScore > 40 ? 'text-echelon-amber' : 'text-echelon-green'
              )}>
                {(gravityScore / 10).toFixed(1)}
              </span>
            </div>

            {/* Founder Badge */}
            <div className="flex items-center gap-1.5 bg-echelon-cyan/10 border border-echelon-cyan/30 rounded px-2 py-0.5">
              <span className="text-[10px] text-terminal-text-muted uppercase tracking-wide">Founded by</span>
              <span className="text-xs text-echelon-cyan font-bold">
                {timeline.founder_name || timeline.dominant_agent_name || 'GENESIS'}
              </span>
            </div>

            {/* Founder's Yield Badge */}
            <div className="flex items-center gap-1 bg-echelon-amber/10 border border-echelon-amber/30 rounded px-2 py-0.5">
              <Zap className="w-3 h-3 text-echelon-amber" />
              <span className="text-xs text-echelon-amber font-mono">
                {((timeline.founder_yield_rate || 0.005) * 100).toFixed(1)}%
              </span>
            </div>

            {/* Active Agents Count */}
            <div className="flex items-center gap-1 bg-terminal-bg rounded px-2 py-0.5">
              <Users className="w-3 h-3 text-terminal-text-muted" />
              <span className="text-xs text-terminal-text-muted">{timeline.active_agent_count || 0}</span>
            </div>
          </div>
        </div>

        {timeline.has_active_paradox && (
          <div className="flex-shrink-0 ml-2">
            <AlertTriangle className="w-5 h-5 text-echelon-red animate-pulse" />
          </div>
        )}
      </div>

      {/* Prices */}
      <div className="flex gap-4 mb-3">
        <div className="flex-1">
          <div className="text-xs text-terminal-text-muted mb-1">YES</div>
          <div className="text-lg font-bold text-echelon-green">
            ${timeline.price_yes.toFixed(2)}
          </div>
        </div>
        <div className="flex-1">
          <div className="text-xs text-terminal-text-muted mb-1">NO</div>
          <div className="text-lg font-bold text-echelon-red">
            ${timeline.price_no.toFixed(2)}
          </div>
        </div>
      </div>

      {/* Stability Bar */}
      <div className="mt-3 pt-3 border-t border-terminal-border">
        <div className="flex justify-between items-center text-xs mb-1.5">
          <span className="text-terminal-text-muted uppercase tracking-wide">Stability</span>
          <span className="font-mono font-bold text-echelon-amber">
            {(timeline.stability ?? 50).toFixed(0)}%
          </span>
        </div>
        <div className="h-2 bg-terminal-border rounded-full overflow-hidden">
          <div
            className="h-full rounded-full bg-echelon-amber transition-all"
            style={{ width: `${timeline.stability ?? 50}%` }}
          />
        </div>
      </div>

      {/* Gravity Well Indicator */}
      <div className="mt-2 pt-2 border-t border-terminal-border/50">
        <div className="flex justify-between items-center text-xs mb-1">
          <span className="text-terminal-text-muted uppercase tracking-wide flex items-center gap-1">
            <span>&#x25C9;</span> Gravity Well
          </span>
          <span className={clsx(
            'font-mono',
            gravityScore > 70 ? 'text-echelon-red' :
            gravityScore > 40 ? 'text-echelon-amber' : 'text-echelon-cyan'
          )}>
            {gravityScore}%
          </span>
        </div>
        <div className="h-1.5 bg-terminal-border rounded-full overflow-hidden">
          <div
            className={clsx(
              'h-full rounded-full transition-all duration-700',
              gravityScore > 70 ? 'bg-gradient-to-r from-red-500 to-orange-500' :
              gravityScore > 40 ? 'bg-gradient-to-r from-amber-500 to-yellow-500' :
              'bg-gradient-to-r from-cyan-500 to-blue-500'
            )}
            style={{
              width: `${gravityScore}%`,
              boxShadow: gravityScore > 60
                ? '0 0 10px currentColor'
                : 'none'
            }}
          />
        </div>
        <p className="text-[10px] text-terminal-text-muted mt-1">
          {gravityScore > 70 ? '\u26A0\uFE0F High agent convergence' :
           gravityScore > 40 ? 'Moderate interest' : 'Low activity'}
        </p>
      </div>

      {/* Stats Row */}
      <div className="flex items-center gap-4 text-xs text-terminal-text-muted">
        <div className="flex items-center gap-1">
          <DollarSign className="w-3 h-3" />
          <span>${(timeline.total_volume_usd / 1000).toFixed(0)}K</span>
        </div>
        <div className="flex items-center gap-1">
          <Users className="w-3 h-3" />
          <span>{timeline.active_agent_count}</span>
        </div>
        <div className="flex items-center gap-1">
          {timeline.stability > 50 ? (
            <TrendingUp className="w-3 h-3 text-echelon-green" />
          ) : (
            <TrendingDown className="w-3 h-3 text-echelon-red" />
          )}
          <span>Vol: ${(timeline.total_volume_usd / 1000).toFixed(0)}K</span>
        </div>
      </div>
    </Link>
  );
}
