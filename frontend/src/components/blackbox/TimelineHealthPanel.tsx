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
    if (value <= 40) return 'text-echelon-red';
    if (value <= 70) return 'text-echelon-amber';
    return 'text-echelon-green';
  };

  return (
    <div
      key={timeline.id}
      className={clsx(
        'bg-terminal-panel border border-terminal-border rounded-md p-3 transition-all hover:border-terminal-border-light cursor-pointer',
        isCritical ? 'border-echelon-red/30' :
        isUnstable ? 'border-echelon-amber/30' :
        'border-terminal-border'
      )}
      onClick={() => navigate(`/timeline/${timeline.id}`)}
    >
      {/* Main Content */}
      <div className="flex-1 min-w-0">
        {/* Header Row */}
        <div className="flex justify-between items-start gap-2">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-terminal-text text-sm truncate leading-tight">{timeline.name}</h3>
            <span className="text-[10px] text-terminal-text-muted font-mono">{timeline.id}</span>
          </div>
          <span className={clsx(
            'px-2 py-0.5 text-[10px] rounded flex items-center gap-1 flex-shrink-0',
            isCritical ? 'bg-echelon-red/10 text-echelon-red border border-echelon-red/20' :
            isUnstable ? 'bg-echelon-amber/10 text-echelon-amber border border-echelon-amber/20' :
            'bg-echelon-green/10 text-echelon-green border border-echelon-green/20'
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
                className="text-terminal-text-muted"
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
                <span className="text-terminal-text-muted text-[10px]">Reality</span>
                <span className={clsx(
                  'font-mono font-medium text-[10px]',
                  osintAlignment > 70 ? 'text-echelon-green' : osintAlignment > 40 ? 'text-echelon-amber' : 'text-echelon-red'
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
                decayRate > 3 ? 'text-echelon-red' : 'text-terminal-text-muted'
              )} />
              <span className={clsx(
                'font-mono text-[10px]',
                decayRate > 3 ? 'text-echelon-red animate-pulse' : 'text-terminal-text-secondary'
              )}>
                {decayRate.toFixed(1)}/hr
              </span>
            </div>

            {/* Sabotage Risk */}
            <span className={clsx(
              'px-1.5 py-0.5 text-[10px] rounded font-medium flex-shrink-0',
              sabotageLevel === 'CRITICAL' ? 'bg-echelon-red/10 text-echelon-red border border-echelon-red/20' :
              sabotageLevel === 'HIGH' ? 'bg-echelon-amber/10 text-echelon-amber border border-echelon-amber/20' :
              sabotageLevel === 'MEDIUM' ? 'bg-amber-500/5 text-echelon-amber border border-echelon-amber/10' :
              'bg-echelon-green/10 text-echelon-green border border-echelon-green/20'
            )}>
              {sabotageLevel}
            </span>
          </div>
        </div>

        {/* User Position Badge */}
        {position && position.totalNotional > 0 && (
          <div className="flex items-center gap-2 mt-2 pt-2 border-t border-terminal-border">
            <span className={clsx(
              'px-2 py-0.5 text-[10px] rounded flex items-center gap-1',
              position.netDirection === 'YES' && 'bg-echelon-green/10 text-echelon-green border border-echelon-green/20',
              position.netDirection === 'NO' && 'bg-echelon-red/10 text-echelon-red border border-echelon-red/20',
              position.netDirection === 'NEUTRAL' && 'bg-terminal-card border border-terminal-border text-terminal-text-secondary'
            )}>
              {position.netDirection === 'YES' ? 'LONG' : position.netDirection === 'NO' ? 'SHORT' : 'NEUTRAL'}
            </span>
            <span className="text-[10px] text-terminal-text-muted">
              ${position.totalNotional.toLocaleString()}
            </span>
            <span className={clsx(
              'text-[10px] font-mono flex items-center gap-0.5',
              position.pnlValue >= 0 ? 'text-echelon-green' : 'text-echelon-red'
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
          <Activity className="w-4 h-4 text-echelon-blue animate-pulse" />
          <span className="text-terminal-text-secondary text-xs">Loading timelines...</span>
        </div>
      </div>
    );
  }

  if (timelines.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-terminal-text-secondary">
        <Activity className="w-8 h-8 mb-2 text-terminal-text-muted opacity-50" />
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
