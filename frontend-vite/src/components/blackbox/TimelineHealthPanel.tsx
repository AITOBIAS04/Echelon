import { useTimelines } from '../../hooks/useWingFlaps';
import { Clock, AlertTriangle, TrendingDown, Activity } from 'lucide-react';
import { clsx } from 'clsx';

export function TimelineHealthPanel() {
  const { data: timelinesData, isLoading } = useTimelines();
  const timelines = timelinesData?.timelines || [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <span className="text-[#00FF41] animate-pulse">SCANNING REALITY MATRIX...</span>
      </div>
    );
  }

  if (timelines.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-500">
        <Activity className="w-12 h-12 mb-4 opacity-50" />
        <span>No active timelines detected</span>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {timelines.map((timeline) => {
        const stability = timeline.stability || 0;
        const osintAlignment = timeline.osint_alignment || 50;
        const decayRate = timeline.decay_rate_per_hour || 1;
        const logicGap = timeline.logic_gap || 0;
        
        const isUnstable = stability > 40 && stability <= 70;
        const isCritical = stability <= 40;
        
        // Determine sabotage level based on logic gap
        const sabotageLevel = logicGap > 0.6 ? 'CRITICAL' : 
                             logicGap > 0.4 ? 'HIGH' : 
                             logicGap > 0.2 ? 'MEDIUM' : 'LOW';
        
        return (
          <div
            key={timeline.id}
            className={clsx(
              'bg-[#0a0a0a] border rounded-lg p-4 transition-all hover:border-opacity-100',
              isCritical ? 'border-red-600 border-opacity-70' : 
              isUnstable ? 'border-yellow-600 border-opacity-70' : 
              'border-[#1a3a1a]'
            )}
          >
            {/* Header */}
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="font-bold text-white text-sm">{timeline.name}</h3>
                <span className="text-xs text-gray-500">{timeline.id}</span>
              </div>
              <span className={clsx(
                'px-2 py-1 text-xs rounded flex items-center gap-1',
                isCritical ? 'bg-red-900/30 text-red-400' :
                isUnstable ? 'bg-yellow-900/30 text-yellow-400' :
                'bg-green-900/30 text-green-400'
              )}>
                {isCritical && <AlertTriangle className="w-3 h-3" />}
                {isCritical ? 'CRITICAL' : isUnstable ? 'UNSTABLE' : 'STABLE'}
              </span>
            </div>

            {/* Stability Gauge + Stats */}
            <div className="flex items-center gap-4 mb-4">
              {/* Circular Gauge */}
              <div className="relative w-20 h-20 flex-shrink-0">
                <svg className="w-20 h-20 -rotate-90">
                  <circle 
                    cx="40" cy="40" r="35" 
                    stroke="#1a3a1a" 
                    strokeWidth="6" 
                    fill="none"
                  />
                  <circle 
                    cx="40" cy="40" r="35" 
                    stroke={isCritical ? '#EF4444' : isUnstable ? '#EAB308' : '#22C55E'}
                    strokeWidth="6" 
                    fill="none"
                    strokeDasharray={`${stability * 2.2} 220`}
                    strokeLinecap="round"
                    className="transition-all duration-500"
                  />
                </svg>
                <span className={clsx(
                  'absolute inset-0 flex items-center justify-center text-lg font-bold font-mono',
                  isCritical ? 'text-red-400' : isUnstable ? 'text-yellow-400' : 'text-green-400'
                )}>
                  {stability.toFixed(0)}%
                </span>
              </div>

              {/* Stats */}
              <div className="flex-1 space-y-2 text-xs">
                {/* OSINT Alignment */}
                <div>
                  <div className="flex justify-between text-gray-500 mb-1">
                    <span>REALITY MATCH</span>
                    <span className={osintAlignment > 70 ? 'text-green-400' : osintAlignment > 40 ? 'text-yellow-400' : 'text-red-400'}>
                      {osintAlignment.toFixed(0)}%
                    </span>
                  </div>
                  <div className="h-1.5 bg-[#1a3a1a] rounded-full overflow-hidden">
                    <div 
                      className={clsx(
                        'h-full rounded-full transition-all duration-500',
                        osintAlignment > 70 ? 'bg-green-500' : osintAlignment > 40 ? 'bg-yellow-500' : 'bg-red-500'
                      )}
                      style={{ width: `${osintAlignment}%` }}
                    />
                  </div>
                </div>

                {/* Decay Rate */}
                <div className="flex items-center justify-between">
                  <span className="text-gray-500 flex items-center gap-1">
                    <TrendingDown className="w-3 h-3" />
                    DECAY RATE
                  </span>
                  <span className={clsx(
                    'font-mono',
                    decayRate > 3 ? 'text-red-400 animate-pulse' : 'text-gray-300'
                  )}>
                    {decayRate.toFixed(1)}%/hr
                    {decayRate > 3 && ' ⚠️'}
                  </span>
                </div>

                {/* Sabotage Level */}
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">SABOTAGE</span>
                  <span className={clsx(
                    'px-1.5 py-0.5 rounded text-xs',
                    sabotageLevel === 'CRITICAL' ? 'bg-red-900/50 text-red-400 animate-pulse' :
                    sabotageLevel === 'HIGH' ? 'bg-orange-900/50 text-orange-400' :
                    sabotageLevel === 'MEDIUM' ? 'bg-yellow-900/50 text-yellow-400' :
                    'bg-green-900/50 text-green-400'
                  )}>
                    {sabotageLevel}
                  </span>
                </div>
              </div>
            </div>

            {/* Gravity Wells */}
            {timeline.gravity_factors && Object.keys(timeline.gravity_factors).length > 0 && (
              <div className="mb-3">
                <span className="text-xs text-gray-500 block mb-1">GRAVITY WELLS</span>
                <div className="flex flex-wrap gap-1">
                  {Object.keys(timeline.gravity_factors).slice(0, 3).map((key: string, i: number) => (
                    <span key={i} className="text-xs px-2 py-0.5 bg-[#1a3a1a] text-gray-400 rounded">
                      • {key}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Paradox Warning */}
            {timeline.has_active_paradox && (
              <div className="bg-red-900/20 border border-red-600 rounded p-2 mt-2">
                <div className="flex items-center justify-center gap-2 text-red-400">
                  <Clock className="w-4 h-4 animate-pulse" />
                  <span className="font-mono font-bold text-sm animate-pulse">
                    REALITY REAPER ACTIVE
                  </span>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

export default TimelineHealthPanel;

