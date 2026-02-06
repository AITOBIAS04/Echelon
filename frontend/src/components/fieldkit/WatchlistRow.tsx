import { Bell, Trash2 } from 'lucide-react';
import type { WatchlistTimeline } from '../../types/watchlist';
import { LogicGapBadge } from './LogicGapBadge';
import { StabilityTrendArrow } from './StabilityTrendArrow';
import { ParadoxProximityBar } from './ParadoxProximityBar';
import { EntropySparkline } from './EntropySparkline';
import { SabotageHeatDots } from './SabotageHeatDots';

/**
 * WatchlistRow Props
 */
export interface WatchlistRowProps {
  /** Timeline data to display */
  timeline: WatchlistTimeline;
  /** Callback when remove action is triggered */
  onRemove: (id: string) => void;
  /** Callback when row is clicked (navigate to timeline) */
  onNavigate: (id: string) => void;
}

/**
 * WatchlistRow Component
 * 
 * Renders a single Watchlist timeline as a telemetry-style card row.
 * Displays comprehensive metrics including stability, logic gap, paradox proximity,
 * entropy trends, and sabotage indicators.
 * 
 * @example
 * ```tsx
 * <WatchlistRow
 *   timeline={timelineData}
 *   onRemove={(id) => removeFromWatchlist(id)}
 *   onNavigate={(id) => navigate(`/timeline/${id}`)}
 * />
 * ```
 */
export function WatchlistRow({
  timeline,
  onRemove,
  onNavigate,
}: WatchlistRowProps) {
  const handleCardClick = (e: React.MouseEvent) => {
    // Don't navigate if clicking on action buttons
    const target = e.target as HTMLElement;
    if (target.closest('button')) {
      return;
    }
    onNavigate(timeline.id);
  };

  const handleRemoveClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onRemove(timeline.id);
  };

  const handleBellClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    // TODO: Implement alert toggle
  };

  // YES price badge color - professional muted palette
  const yesPriceColor = timeline.yesPrice >= 0.5 ? '#10B981' : '#EF4444';
  const yesPriceBg = timeline.yesPrice >= 0.5
    ? 'bg-status-success/20'
    : 'bg-status-danger/20';

  return (
    <div
      onClick={handleCardClick}
      className="
        bg-terminal-panel border border-terminal-border rounded-lg p-3
        cursor-pointer transition-colors duration-150
        hover:border-terminal-border
      "
    >
      {/* Row 1: Timeline name + YES price + Logic Gap */}
      <div className="flex justify-between items-center mb-3">
        <div className="font-medium text-white">
          {timeline.name}
        </div>
        <div className="flex items-center gap-2">
          {/* YES Price Badge */}
          <span
            className={`px-2 py-0.5 rounded text-xs font-medium ${yesPriceBg}`}
            style={{ color: yesPriceColor }}
          >
            YES: {(timeline.yesPrice * 100).toFixed(1)}%
          </span>
          {/* Logic Gap Badge */}
          <LogicGapBadge
            gap={timeline.logicGap}
            showTrend={true}
            trend={timeline.logicGapTrend}
          />
        </div>
      </div>

      {/* Row 2: Stability + Paradox Proximity */}
      <div className="flex items-center gap-4 mb-3">
        <div className="flex items-center gap-1.5 text-sm text-terminal-text whitespace-nowrap">
          <span>Stability: {timeline.stability.toFixed(1)}%</span>
          <StabilityTrendArrow trend={timeline.stabilityTrend} />
        </div>
        <div className="flex-1">
          <ParadoxProximityBar proximity={timeline.paradoxProximity} />
        </div>
      </div>

      {/* Row 3: Entropy + Sabotage + Actions */}
      <div className="flex justify-between items-center">
        <EntropySparkline
          history={timeline.entropyHistory}
          currentRate={timeline.entropyRate}
        />
        <SabotageHeatDots count={timeline.sabotageCount1h} />
        <div className="flex items-center gap-2">
          <button
            onClick={handleBellClick}
            className="
              p-1.5 rounded hover:bg-terminal-panel/50
              text-terminal-text-muted hover:text-terminal-text
              transition-colors duration-150
            "
            aria-label="Toggle alerts"
          >
            <Bell className="w-4 h-4" />
          </button>
          <button
            onClick={handleRemoveClick}
            className="
              p-1.5 rounded hover:bg-echelon-red/20
              text-terminal-text-muted hover:text-red-500
              transition-colors duration-150
            "
            aria-label="Remove from watchlist"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
