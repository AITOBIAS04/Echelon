import { useState } from 'react';
import { useWingFlaps } from '../../hooks/useWingFlaps';
import { clsx } from 'clsx';

type FilterType = 'ALL' | 'SHARKS' | 'WHALES' | 'DIVERGENCE';

export function WhaleWatch() {
  const [filter, setFilter] = useState<FilterType>('ALL');
  const { data: flapsData, isLoading } = useWingFlaps();
  
  const wingFlaps = flapsData?.wing_flaps || flapsData?.flaps || [];

  const getAgentColour = (archetype: string) => {
    switch (archetype?.toUpperCase()) {
      case 'SHARK': return 'text-cyan-400';
      case 'SPY': return 'text-yellow-400';
      case 'DIPLOMAT': return 'text-blue-400';
      case 'SABOTEUR': return 'text-red-400';
      case 'WHALE': return 'text-purple-400';
      case 'DEGEN': return 'text-pink-400';
      default: return 'text-gray-400';
    }
  };

  const getActionColour = (direction: string, flapType: string) => {
    if (flapType === 'SABOTAGE') return 'text-red-400';
    if (flapType === 'SHIELD') return 'text-blue-400';
    if (flapType === 'PARADOX') return 'text-amber-400';
    return direction === 'ANCHOR' ? 'text-green-400' : 'text-red-400';
  };

  const filteredFlaps = wingFlaps.filter(flap => {
    if (filter === 'ALL') return true;
    if (filter === 'SHARKS') return flap.agent_archetype?.toUpperCase() === 'SHARK';
    if (filter === 'WHALES') return flap.agent_archetype?.toUpperCase() === 'WHALE';
    if (filter === 'DIVERGENCE') return flap.spawned_ripple; // Use ripple as proxy for divergence
    return true;
  });

  const filters: FilterType[] = ['ALL', 'SHARKS', 'WHALES', 'DIVERGENCE'];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <span className="text-[#00FF41] animate-pulse">SCANNING FREQUENCIES...</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex gap-2 text-xs">
        {filters.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={clsx(
              'px-3 py-1 rounded transition-all',
              filter === f
                ? 'bg-[#1a3a1a] text-green-400'
                : 'bg-[#0a0a0a] border border-[#1a3a1a] text-gray-500 hover:text-[#00FF41]'
            )}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Feed */}
      <div className="space-y-1 font-mono text-sm max-h-[500px] overflow-y-auto">
        {filteredFlaps.length === 0 ? (
          <div className="text-gray-500 text-center py-8">
            No intercepts matching filter
          </div>
        ) : (
          filteredFlaps.slice(0, 50).map((flap, i) => {
            const time = new Date(flap.timestamp || flap.created_at).toLocaleTimeString('en-GB', { hour12: false });
            const isDivergence = flap.spawned_ripple;
            
            return (
              <div key={flap.id || i}>
                {/* Main intercept line */}
                <div className="hover:bg-[#1a3a1a]/30 px-2 py-1 rounded transition-colors">
                  <span className="text-gray-500">[{time}]</span>
                  {' '}
                  <span className="text-gray-500">INTERCEPT:</span>
                  {' '}
                  <span className={getAgentColour(flap.agent_archetype)}>
                    {flap.agent_name || 'SYSTEM'}
                  </span>
                  {' '}
                  <span className={getActionColour(flap.direction, flap.flap_type)}>
                    {flap.action}
                  </span>
                  {' '}
                  <span className="text-gray-500">
                    ({flap.stability_delta > 0 ? '+' : ''}{flap.stability_delta?.toFixed(2)}%)
                  </span>
                  {' '}
                  <span className="text-white">
                    → {flap.timeline_id || flap.timeline_name}
                  </span>
                  {flap.volume_usd > 0 && (
                    <span className="text-gray-500 ml-2">
                      (${flap.volume_usd.toLocaleString()})
                    </span>
                  )}
                </div>
                
                {/* Divergence alert */}
                {isDivergence && (
                  <div className="bg-amber-900/20 border-l-2 border-amber-500 pl-2 py-1 ml-4 mt-1">
                    <span className="text-amber-400 animate-pulse">⚠️ RIPPLE DETECTED:</span>
                    {' '}
                    <span className="text-gray-300">
                      Cascade effect triggered to connected timelines
                    </span>
                    <span className="text-amber-300 text-xs ml-2">[BUTTERFLY EFFECT]</span>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Stats footer */}
      <div className="flex justify-between text-xs text-gray-500 pt-2 border-t border-[#1a3a1a]">
        <span>Showing {Math.min(filteredFlaps.length, 50)} of {filteredFlaps.length} intercepts</span>
        <span>Auto-refresh: 15s</span>
      </div>
    </div>
  );
}

export default WhaleWatch;

