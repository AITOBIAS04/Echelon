import { useState } from 'react';
import { useWingFlaps } from '../../hooks/useWingFlaps';
import { clsx } from 'clsx';
import { TrendingUp, TrendingDown, AlertTriangle, Radio, Zap } from 'lucide-react';

type FilterType = 'ALL' | 'SHARKS' | 'WHALES' | 'DIVERGENCE';

export function WhaleWatch() {
  const [filter, setFilter] = useState<FilterType>('ALL');
  const { data: flapsData, isLoading } = useWingFlaps();

  const wingFlaps = flapsData?.flaps || [];

  const getAgentArchetypeColor = (archetype: string): string => {
    switch (archetype?.toUpperCase()) {
      case 'SHARK': return 'text-echelon-red';
      case 'SPY': return 'text-echelon-amber';
      case 'DIPLOMAT': return 'text-echelon-blue';
      case 'SABOTEUR': return 'text-status-paradox';
      case 'WHALE': return 'text-echelon-green';
      case 'DEGEN': return 'text-echelon-amber';
      default: return 'text-terminal-text-secondary';
    }
  };

  const getAgentArchetypeBg = (archetype: string): string => {
    switch (archetype?.toUpperCase()) {
      case 'SHARK': return 'bg-echelon-red/10 border-echelon-red/20';
      case 'SPY': return 'bg-echelon-amber/10 border-echelon-amber/20';
      case 'DIPLOMAT': return 'bg-echelon-blue/10 border-echelon-blue/20';
      case 'SABOTEUR': return 'bg-status-paradox/10 border-status-paradox/20';
      case 'WHALE': return 'bg-echelon-green/10 border-echelon-green/20';
      case 'DEGEN': return 'bg-echelon-amber/10 border-echelon-amber/20';
      default: return 'bg-terminal-card border-terminal-border';
    }
  };

  const getActionConfig = (flapType: string, direction: string) => {
    if (flapType === 'SABOTAGE' || direction === 'DESTABILISE') {
      return {
        icon: TrendingDown,
        color: 'text-echelon-red',
        bg: 'bg-echelon-red/10 border-echelon-red/20',
        label: 'Destabilize'
      };
    }
    if (flapType === 'SHIELD' || direction === 'ANCHOR') {
      return {
        icon: TrendingUp,
        color: 'text-echelon-green',
        bg: 'bg-echelon-green/10 border-echelon-green/20',
        label: 'Anchor'
      };
    }
    if (flapType === 'PARADOX') {
      return {
        icon: AlertTriangle,
        color: 'text-status-paradox',
        bg: 'bg-status-paradox/10 border-status-paradox/20',
        label: 'Paradox'
      };
    }
    return {
      icon: Zap,
      color: 'text-echelon-blue',
      bg: 'bg-echelon-blue/10 border-echelon-blue/20',
      label: direction || 'Action'
    };
  };

  const filteredFlaps = wingFlaps.filter((flap: any) => {
    if (filter === 'ALL') return true;
    if (filter === 'SHARKS') return flap.agent_archetype?.toUpperCase() === 'SHARK';
    if (filter === 'WHALES') return flap.agent_archetype?.toUpperCase() === 'WHALE';
    if (filter === 'DIVERGENCE') return flap.spawned_ripple;
    return true;
  });

  const filters: FilterType[] = ['ALL', 'SHARKS', 'WHALES', 'DIVERGENCE'];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="flex items-center gap-2">
          <Radio className="w-4 h-4 text-echelon-blue animate-pulse" />
          <span className="text-terminal-text-secondary text-xs">Loading intercepts...</span>
        </div>
      </div>
    );
  }

  // Summary stats
  const totalVolume = filteredFlaps.reduce((sum: number, f: any) => sum + (f.volume_usd || 0), 0);
  const divergenceCount = filteredFlaps.filter((f: any) => f.spawned_ripple).length;

  return (
    <div className="space-y-3">
      {/* Summary Stats - Compact Row */}
      <div className="grid grid-cols-3 gap-2">
        <div className="bg-terminal-panel border border-terminal-border rounded p-2">
          <div className="text-[10px] text-terminal-text-muted mb-0.5">Events</div>
          <div className="text-sm font-semibold text-terminal-text">{filteredFlaps.length}</div>
        </div>
        <div className="bg-terminal-panel border border-terminal-border rounded p-2">
          <div className="text-[10px] text-terminal-text-muted mb-0.5">Volume</div>
          <div className="text-sm font-semibold text-terminal-text">${(totalVolume / 1000).toFixed(1)}K</div>
        </div>
        <div className="bg-terminal-panel border border-terminal-border rounded p-2">
          <div className="text-[10px] text-terminal-text-muted mb-0.5">Ripples</div>
          <div className="text-sm font-semibold text-echelon-amber">{divergenceCount}</div>
        </div>
      </div>

      {/* Filters - Compact Row */}
      <div className="flex gap-1.5">
        {filters.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={clsx(
              'px-2.5 py-1 rounded text-xs transition-all font-medium',
              filter === f
                ? 'bg-echelon-blue/20 text-echelon-blue border border-echelon-blue/30'
                : 'bg-terminal-card border border-terminal-border text-terminal-text-secondary hover:text-terminal-text hover:border-terminal-border-light'
            )}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Event Cards - Compact List */}
      <div className="space-y-2">
        {filteredFlaps.length === 0 ? (
          <div className="text-center py-8 bg-terminal-panel border border-terminal-border rounded">
            <Radio className="w-6 h-6 mx-auto mb-2 text-terminal-text-muted opacity-50" />
            <p className="text-terminal-text-secondary text-xs">No intercepts matching filter</p>
          </div>
        ) : (
          filteredFlaps.slice(0, 50).map((flap: any, i: number) => {
            const time = new Date(flap.timestamp || flap.created_at).toLocaleTimeString('en-GB', { hour12: false });
            const isDivergence = flap.spawned_ripple;
            const actionConfig = getActionConfig(flap.flap_type, flap.direction);
            const ActionIcon = actionConfig.icon;

            return (
              <div
                key={flap.id || i}
                className={clsx(
                  'bg-terminal-panel border border-terminal-border rounded p-3 transition-all hover:border-terminal-border-light',
                  isDivergence && 'border-echelon-amber/30'
                )}
              >
                <div className="flex items-start gap-3">
                  {/* Agent Icon Tile - 40x40px */}
                  <div className={clsx(
                    'w-10 h-10 rounded flex items-center justify-center border flex-shrink-0',
                    getAgentArchetypeBg(flap.agent_archetype)
                  )}>
                    <span className={clsx('font-bold text-sm', getAgentArchetypeColor(flap.agent_archetype))}>
                      {flap.agent_archetype?.charAt(0) || '?'}
                    </span>
                  </div>

                  {/* Main Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-terminal-text truncate">
                        {flap.agent_name || 'Unknown'}
                      </span>
                      <span className={clsx('text-[10px] px-1.5 py-0.5 rounded border', actionConfig.bg, actionConfig.color)}>
                        {actionConfig.label}
                      </span>
                      {isDivergence && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-echelon-amber/10 text-echelon-amber border border-echelon-amber/20">
                          Ripple
                        </span>
                      )}
                    </div>

                    <div className="text-xs text-terminal-text-secondary mb-1.5 truncate">
                      {flap.timeline_id || flap.timeline_name || 'Unknown'}
                    </div>

                    {/* Metrics Row */}
                    <div className="flex items-center gap-3 text-[10px]">
                      <span className="text-terminal-text-muted">{time}</span>
                      {flap.volume_usd > 0 && (
                        <span className="text-terminal-text-secondary">${flap.volume_usd.toLocaleString()}</span>
                      )}
                      {flap.stability_delta !== undefined && (
                        <span className={clsx(
                          'font-mono',
                          flap.stability_delta > 0 ? 'text-echelon-green' : flap.stability_delta < 0 ? 'text-echelon-red' : 'text-terminal-text-muted'
                        )}>
                          {flap.stability_delta > 0 ? '+' : ''}{flap.stability_delta?.toFixed(2)}%
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Action Indicator */}
                  <div className={clsx(
                    'w-7 h-7 rounded flex items-center justify-center flex-shrink-0',
                    actionConfig.bg
                  )}>
                    <ActionIcon className={clsx('w-3.5 h-3.5', actionConfig.color)} />
                  </div>
                </div>

                {/* Divergence Alert */}
                {isDivergence && (
                  <div className="mt-2 ml-13 bg-echelon-amber/10 border border-echelon-amber/20 rounded px-2 py-1.5 flex items-center gap-2">
                    <AlertTriangle className="w-3.5 h-3.5 text-echelon-amber flex-shrink-0" />
                    <span className="text-[10px] text-echelon-amber">
                      Ripple — cascade to connected timelines
                    </span>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Footer */}
      <div className="flex justify-between text-[10px] text-terminal-text-muted pt-2 border-t border-terminal-border">
        <span>{Math.min(filteredFlaps.length, 50)}/{filteredFlaps.length} events</span>
        <span className="flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          15s
        </span>
      </div>
    </div>
  );
}

export default WhaleWatch;
