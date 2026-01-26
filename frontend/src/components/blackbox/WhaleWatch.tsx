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
      case 'SHARK': return 'text-red-400';
      case 'SPY': return 'text-amber-400';
      case 'DIPLOMAT': return 'text-blue-400';
      case 'SABOTEUR': return 'text-purple-400';
      case 'WHALE': return 'text-emerald-400';
      case 'DEGEN': return 'text-orange-400';
      default: return 'text-slate-400';
    }
  };

  const getAgentArchetypeBg = (archetype: string): string => {
    switch (archetype?.toUpperCase()) {
      case 'SHARK': return 'bg-red-500/10 border-red-500/20';
      case 'SPY': return 'bg-amber-500/10 border-amber-500/20';
      case 'DIPLOMAT': return 'bg-blue-500/10 border-blue-500/20';
      case 'SABOTEUR': return 'bg-purple-500/10 border-purple-500/20';
      case 'WHALE': return 'bg-emerald-500/10 border-emerald-500/20';
      case 'DEGEN': return 'bg-orange-500/10 border-orange-500/20';
      default: return 'bg-slate-800/50 border-slate-700/50';
    }
  };

  const getActionConfig = (flapType: string, direction: string) => {
    if (flapType === 'SABOTAGE' || direction === 'DESTABILISE') {
      return {
        icon: TrendingDown,
        color: 'text-red-400',
        bg: 'bg-red-500/10 border-red-500/20',
        label: 'Destabilize'
      };
    }
    if (flapType === 'SHIELD' || direction === 'ANCHOR') {
      return {
        icon: TrendingUp,
        color: 'text-emerald-400',
        bg: 'bg-emerald-500/10 border-emerald-500/20',
        label: 'Anchor'
      };
    }
    if (flapType === 'PARADOX') {
      return {
        icon: AlertTriangle,
        color: 'text-purple-400',
        bg: 'bg-purple-500/10 border-purple-500/20',
        label: 'Paradox'
      };
    }
    return {
      icon: Zap,
      color: 'text-blue-400',
      bg: 'bg-blue-500/10 border-blue-500/20',
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
          <Radio className="w-4 h-4 text-blue-400 animate-pulse" />
          <span className="text-slate-400 text-xs">Loading intercepts...</span>
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
        <div className="bg-slate-900/50 border border-slate-700/50 rounded p-2">
          <div className="text-[10px] text-slate-500 mb-0.5">Events</div>
          <div className="text-sm font-semibold text-slate-200">{filteredFlaps.length}</div>
        </div>
        <div className="bg-slate-900/50 border border-slate-700/50 rounded p-2">
          <div className="text-[10px] text-slate-500 mb-0.5">Volume</div>
          <div className="text-sm font-semibold text-slate-200">${(totalVolume / 1000).toFixed(1)}K</div>
        </div>
        <div className="bg-slate-900/50 border border-slate-700/50 rounded p-2">
          <div className="text-[10px] text-slate-500 mb-0.5">Ripples</div>
          <div className="text-sm font-semibold text-amber-400">{divergenceCount}</div>
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
                ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                : 'bg-slate-800/50 border border-slate-700/50 text-slate-400 hover:text-slate-200 hover:border-slate-600'
            )}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Event Cards - Compact List */}
      <div className="space-y-2">
        {filteredFlaps.length === 0 ? (
          <div className="text-center py-8 bg-slate-900/50 border border-slate-700/50 rounded">
            <Radio className="w-6 h-6 mx-auto mb-2 text-slate-600 opacity-50" />
            <p className="text-slate-400 text-xs">No intercepts matching filter</p>
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
                  'bg-slate-900/50 border border-slate-700/50 rounded p-3 transition-all hover:border-slate-600',
                  isDivergence && 'border-amber-500/30'
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
                      <span className="text-sm font-medium text-slate-200 truncate">
                        {flap.agent_name || 'Unknown'}
                      </span>
                      <span className={clsx('text-[10px] px-1.5 py-0.5 rounded border', actionConfig.bg, actionConfig.color)}>
                        {actionConfig.label}
                      </span>
                      {isDivergence && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                          Ripple
                        </span>
                      )}
                    </div>

                    <div className="text-xs text-slate-400 mb-1.5 truncate">
                      {flap.timeline_id || flap.timeline_name || 'Unknown'}
                    </div>

                    {/* Metrics Row */}
                    <div className="flex items-center gap-3 text-[10px]">
                      <span className="text-slate-500">{time}</span>
                      {flap.volume_usd > 0 && (
                        <span className="text-slate-400">${flap.volume_usd.toLocaleString()}</span>
                      )}
                      {flap.stability_delta !== undefined && (
                        <span className={clsx(
                          'font-mono',
                          flap.stability_delta > 0 ? 'text-emerald-400' : flap.stability_delta < 0 ? 'text-red-400' : 'text-slate-500'
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
                  <div className="mt-2 ml-13 bg-amber-500/10 border border-amber-500/20 rounded px-2 py-1.5 flex items-center gap-2">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
                    <span className="text-[10px] text-amber-400">
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
      <div className="flex justify-between text-[10px] text-slate-500 pt-2 border-t border-slate-700/30">
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
