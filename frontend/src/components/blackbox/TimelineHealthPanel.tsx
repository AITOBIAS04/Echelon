import { useTimelines } from '../../hooks/useWingFlaps';
import { useUserPosition } from '../../hooks/useUserPositions';
import { AlertTriangle, TrendingDown, Activity, TrendingUp, TrendingDown as TrendingDownIcon } from 'lucide-react';
import { clsx } from 'clsx';
import { useNavigate } from 'react-router-dom';

function TimelineCard({ timeline }: { timeline: any }) {
  const navigate = useNavigate();
  const { position } = useUserPosition(timeline.id);

  const stability = timeline.stability || 0;
  const osintAlignment = timeline.osint_alignment || 50;
  const decayRate = timeline.decay_rate_per_hour || 1;
  const logicGap = timeline.logic_gap || 0;

  const isUnstable = stability > 40 && stability <= 70;
  const isCritical = stability <= 40;

  const sabotageLevel = logicGap > 0.6 ? 'CRITICAL' :
                       logicGap > 0.4 ? 'HIGH' :
                       logicGap > 0.2 ? 'MEDIUM' : 'LOW';

  const getStabilityColor = (value: number) => {
    if (value <= 40) return 'text-red-400';
    if (value <= 70) return 'text-amber-400';
    return 'text-emerald-400';
  };

  return (
    <div
      key={timeline.id}
      className={clsx(
        'bg-slate-900/50 border border-slate-700/50 rounded-md p-3 transition-all hover:border-slate-600 cursor-pointer',
        isCritical ? 'border-red-500/30' :
        isUnstable ? 'border-amber-500/30' :
        'border-slate-700/50'
      )}
      onClick={() => navigate(`/timeline/${timeline.id}`)}
    >
      {/* Main Content */}
      <div className="flex-1 min-w-0">
        {/* Header Row */}
        <div className="flex justify-between items-start gap-2">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-slate-200 text-sm truncate leading-tight">{timeline.name}</h3>
            <span className="text-[10px] text-slate-500 font-mono">{timeline.id}</span>
          </div>
          <span className={clsx(
            'px-2 py-0.5 text-[10px] rounded flex items-center gap-1 flex-shrink-0',
            isCritical ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
            isUnstable ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
            'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
          )}>
            {isCritical && <AlertTriangle className="w-3 h-3" />}
            {isCritical ? 'Critical' : isUnstable ? 'Unstable' : 'Stable'}
          </span>
        </div>

        {/* Stability and Stats Row */}
        <div className="flex items-center gap-3 mt-2">
          {/* Mini Stability Gauge */}
          <div className="relative w-8 h-8 flex-shrink-0">
            <svg className="w-8 h-8 -rotate-90">
              <circle
                cx="16" cy="16" r="14"
                stroke="currentColor"
                strokeWidth="3"
                fill="none"
                className="text-slate-700"
              />
              <circle
                cx="16" cy="16" r="14"
                stroke="currentColor"
                strokeWidth="3"
                fill="none"
                strokeDasharray={`${Math.min(stability, 100) * 0.88} 88`}
                strokeLinecap="round"
                className={clsx(
                  'transition-all duration-300',
                  isCritical ? 'text-red-500' : isUnstable ? 'text-amber-500' : 'text-emerald-500'
                )}
              />
            </svg>
            <span className={clsx(
              'absolute inset-0 flex items-center justify-center text-[10px] font-bold font-mono',
              getStabilityColor(stability)
            )}>
              {stability.toFixed(0)}
            </span>
          </div>

          {/* Compact Stats */}
          <div className="flex-1 flex items-center gap-3 text-xs">
            {/* Reality Match */}
            <div className="flex-1">
              <div className="flex justify-between items-center mb-0.5">
                <span className="text-slate-500 text-[10px]">Reality</span>
                <span className={clsx(
                  'font-mono font-medium text-[10px]',
                  osintAlignment > 70 ? 'text-emerald-400' : osintAlignment > 40 ? 'text-amber-400' : 'text-red-400'
                )}>
                  {osintAlignment.toFixed(0)}%
                </span>
              </div>
              <div className="h-1 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className={clsx(
                    'h-full rounded-full transition-all',
                    osintAlignment > 70 ? 'bg-emerald-500' : osintAlignment > 40 ? 'bg-amber-500' : 'bg-red-500'
                  )}
                  style={{ width: `${osintAlignment}%` }}
                />
              </div>
            </div>

            {/* Decay Rate */}
            <div className="flex items-center gap-1.5">
              <TrendingDown className={clsx(
                'w-3 h-3',
                decayRate > 3 ? 'text-red-400' : 'text-slate-500'
              )} />
              <span className={clsx(
                'font-mono text-[10px]',
                decayRate > 3 ? 'text-red-400 animate-pulse' : 'text-slate-400'
              )}>
                {decayRate.toFixed(1)}/hr
              </span>
            </div>

            {/* Sabotage Risk */}
            <span className={clsx(
              'px-1.5 py-0.5 text-[10px] rounded font-medium flex-shrink-0',
              sabotageLevel === 'CRITICAL' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
              sabotageLevel === 'HIGH' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
              sabotageLevel === 'MEDIUM' ? 'bg-amber-500/5 text-amber-400 border border-amber-500/10' :
              'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
            )}>
              {sabotageLevel}
            </span>
          </div>
        </div>

        {/* User Position Badge */}
        {position && position.totalNotional > 0 && (
          <div className="flex items-center gap-2 mt-2 pt-2 border-t border-slate-700/30">
            <span className={clsx(
              'px-2 py-0.5 text-[10px] rounded flex items-center gap-1',
              position.netDirection === 'YES' && 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
              position.netDirection === 'NO' && 'bg-red-500/10 text-red-400 border border-red-500/20',
              position.netDirection === 'NEUTRAL' && 'bg-slate-800/50 border border-slate-700/50 text-slate-400'
            )}>
              {position.netDirection === 'YES' ? 'LONG' : position.netDirection === 'NO' ? 'SHORT' : 'NEUTRAL'}
            </span>
            <span className="text-[10px] text-slate-500">
              ${position.totalNotional.toLocaleString()}
            </span>
            <span className={clsx(
              'text-[10px] font-mono flex items-center gap-0.5',
              position.pnlValue >= 0 ? 'text-emerald-400' : 'text-red-400'
            )}>
              {position.pnlValue >= 0 ? <TrendingUp className="w-2.5 h-2.5" /> : <TrendingDownIcon className="w-2.5 h-2.5" />}
              {position.pnlPercent >= 0 ? '+' : ''}{position.pnlPercent.toFixed(1)}%
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

export function TimelineHealthPanel() {
  const { data: timelinesData, isLoading } = useTimelines();
  const timelines = timelinesData?.timelines || [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-blue-400 animate-pulse" />
          <span className="text-slate-400 text-xs">Loading timelines...</span>
        </div>
      </div>
    );
  }

  if (timelines.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-slate-400">
        <Activity className="w-8 h-8 mb-2 text-slate-600 opacity-50" />
        <span className="text-xs">No active timelines</span>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {timelines.map((timeline) => (
        <TimelineCard key={timeline.id} timeline={timeline} />
      ))}
    </div>
  );
}

export default TimelineHealthPanel;
