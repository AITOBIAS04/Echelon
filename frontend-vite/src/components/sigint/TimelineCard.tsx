import { TrendingUp, TrendingDown, AlertTriangle, Users, DollarSign } from 'lucide-react';
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
          {/* Founder Badge & Info */}
          <div className="flex items-center gap-2 mt-1.5 flex-wrap">
            {/* Founder Badge */}
            {(timeline.founder_id || timeline.founder_name || timeline.dominant_agent_name) && (
              <div className="flex items-center gap-1.5 bg-echelon-cyan/20 border border-echelon-cyan/30 rounded px-2 py-0.5">
                <span className="text-[10px] text-terminal-muted uppercase">Founded by</span>
                <span className="text-xs text-echelon-cyan font-bold">
                  {timeline.founder_name || timeline.dominant_agent_name || 'GENESIS'}
                </span>
              </div>
            )}
            
            {/* Founder's Yield Badge */}
            {timeline.founder_yield_rate && timeline.founder_yield_rate > 0 && (
              <div 
                className="flex items-center gap-1 bg-echelon-amber/20 border border-echelon-amber/30 rounded px-2 py-0.5"
                title="Founder earns this % of timeline volume"
              >
                <span className="text-echelon-amber text-xs">⚡</span>
                <span className="text-xs text-echelon-amber font-mono">
                  {(timeline.founder_yield_rate * 100).toFixed(1)}% yield
                </span>
              </div>
            )}
            
            {/* Active Agents Count */}
            {timeline.active_agent_count > 0 && (
              <div className="flex items-center gap-1 text-xs text-terminal-muted">
                <span>👥</span>
                <span>{timeline.active_agent_count} agents</span>
              </div>
            )}
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

      {/* Stability Bar */}
      <div className="mt-3 pt-3 border-t border-terminal-border">
        <div className="flex justify-between items-center text-xs mb-1">
          <span className="text-terminal-muted uppercase tracking-wide">Stability</span>
          <span className={clsx(
            'font-mono font-bold',
            (timeline.stability || 0) > 70 ? 'text-echelon-green' :
            (timeline.stability || 0) > 40 ? 'text-echelon-amber' : 'text-echelon-red'
          )}>
            {(timeline.stability || 0).toFixed(0)}%
          </span>
        </div>
        <div className="h-1.5 bg-terminal-bg rounded-full overflow-hidden">
          <div 
            className={clsx(
              'h-full rounded-full transition-all duration-500',
              (timeline.stability || 0) > 70 ? 'bg-echelon-green' :
              (timeline.stability || 0) > 40 ? 'bg-echelon-amber' : 'bg-echelon-red',
              (timeline.stability || 0) < 30 && 'animate-pulse'
            )}
            style={{ width: `${Math.min(timeline.stability || 0, 100)}%` }}
          />
        </div>
        
        {/* Critical Warning */}
        {(timeline.stability || 0) < 30 && (
          <div className="flex items-center gap-1 mt-2 text-echelon-red text-xs animate-pulse">
            <span>⚠️</span>
            <span>COLLAPSE IMMINENT</span>
          </div>
        )}
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
