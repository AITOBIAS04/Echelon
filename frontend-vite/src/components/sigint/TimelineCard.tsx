import { TrendingUp, TrendingDown, AlertTriangle, Users, DollarSign, Zap } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { Timeline } from '../../types';
import { clsx } from 'clsx';

interface TimelineCardProps {
  timeline: Timeline;
  onClick?: () => void;
}

export function TimelineCard({ timeline, onClick }: TimelineCardProps) {
  return (
    <Link
      to={`/timeline/${timeline.id}`}
      onClick={onClick}
      className={clsx(
        'block terminal-panel p-4 cursor-pointer transition-all hover:border-echelon-cyan/50',
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
          {/* Founder & Meta Badges */}
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            {/* Founder Badge - Always show with fallback */}
            <div className="flex items-center gap-1.5 bg-cyan-900/20 border border-cyan-500/30 rounded px-2 py-0.5">
              <span className="text-[10px] text-gray-500 uppercase tracking-wide">Founded by</span>
              <span className="text-xs text-cyan-400 font-bold">
                {timeline.founder_name || timeline.dominant_agent_name || 'GENESIS'}
              </span>
            </div>
            
            {/* Founder's Yield Badge - Always show with fallback */}
            <div className="flex items-center gap-1 bg-amber-900/20 border border-amber-500/30 rounded px-2 py-0.5">
              <Zap className="w-3 h-3 text-amber-400" />
              <span className="text-xs text-amber-400 font-mono">
                {((timeline.founder_yield_rate || 0.005) * 100).toFixed(1)}%
              </span>
            </div>
            
            {/* Active Agents Count - Always show */}
            <div className="flex items-center gap-1 bg-terminal-bg rounded px-2 py-0.5">
              <Users className="w-3 h-3 text-terminal-muted" />
              <span className="text-xs text-terminal-muted">{timeline.active_agent_count || 0}</span>
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

      {/* Stability Bar - Always show with fallback */}
      <div className="mt-3 pt-3 border-t border-gray-800">
        <div className="flex justify-between items-center text-xs mb-1.5">
          <span className="text-gray-500 uppercase tracking-wide">Stability</span>
          <span className="font-mono font-bold text-amber-400">
            {(timeline.stability ?? 50).toFixed(0)}%
          </span>
        </div>
        <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
          <div 
            className="h-full rounded-full bg-amber-500 transition-all"
            style={{ width: `${timeline.stability ?? 50}%` }}
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
    </Link>
  );
}
