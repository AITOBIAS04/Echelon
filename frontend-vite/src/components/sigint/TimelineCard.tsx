import { TrendingUp, TrendingDown, AlertTriangle, Users, DollarSign } from 'lucide-react';
import type { Timeline } from '../../types';
import { clsx } from 'clsx';

interface TimelineCardProps {
  timeline: Timeline;
  onClick?: () => void;
}

export function TimelineCard({ timeline, onClick }: TimelineCardProps) {
  const stabilityColor = 
    timeline.stability >= 70 ? 'text-echelon-green' :
    timeline.stability >= 40 ? 'text-echelon-amber' :
    'text-echelon-red';

  const stabilityBg =
    timeline.stability >= 70 ? 'bg-echelon-green/10 border-echelon-green/30' :
    timeline.stability >= 40 ? 'bg-echelon-amber/10 border-echelon-amber/30' :
    'bg-echelon-red/10 border-echelon-red/30';

  return (
    <div
      onClick={onClick}
      className={clsx(
        'terminal-panel p-4 cursor-pointer transition-all hover:border-echelon-cyan/50',
        timeline.has_active_paradox && 'border-echelon-red/50 animate-pulse-slow'
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-terminal-text truncate">
            {timeline.name}
          </h3>
          <p className="text-xs text-terminal-muted mt-0.5">
            {timeline.id}
          </p>
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
          <div className="text-xs text-terminal-muted mb-1">YES</div>
          <div className="text-lg font-bold text-echelon-green">
            ${timeline.price_yes.toFixed(2)}
          </div>
        </div>
        <div className="flex-1">
          <div className="text-xs text-terminal-muted mb-1">NO</div>
          <div className="text-lg font-bold text-echelon-red">
            ${timeline.price_no.toFixed(2)}
          </div>
        </div>
      </div>

      {/* Stability Bar */}
      <div className="mb-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-terminal-muted">Stability</span>
          <span className={clsx('text-xs font-mono', stabilityColor)}>
            {timeline.stability.toFixed(1)}%
          </span>
        </div>
        <div className="h-1.5 bg-terminal-bg rounded-full overflow-hidden">
          <div
            className={clsx('h-full rounded-full transition-all', stabilityBg.replace('/10', ''))}
            style={{ width: `${timeline.stability}%` }}
          />
        </div>
      </div>

      {/* Stats Row */}
      <div className="flex items-center gap-4 text-xs text-terminal-muted">
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
          <span>G: {timeline.gravity_score.toFixed(0)}</span>
        </div>
      </div>
    </div>
  );
}
