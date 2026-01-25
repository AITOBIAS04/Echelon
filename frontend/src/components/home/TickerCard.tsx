import { useNavigate } from 'react-router-dom';
import { Eye, GitBranch, Sparkles } from 'lucide-react';
import { toggleTrack, isTracked } from '../../lib/tracking';
import { useState, useEffect } from 'react';
import type { OpsCard } from '../../types/opsBoard';

/**
 * TickerCard Props
 */
export interface TickerCardProps {
  /** Card data */
  card: OpsCard;
}

/**
 * Get lane border color
 */
function getLaneBorderColor(lane: OpsCard['lane']): string {
  switch (lane) {
    case 'new_creations':
      return '#10B981'; // emerald
    case 'about_to_happen':
      return '#F59E0B'; // amber
    case 'at_risk':
      return '#EF4444'; // crimson
    case 'graduation':
      return '#8B5CF6'; // purple
  }
}

/**
 * Get phase badge text
 */
function getPhaseBadge(card: OpsCard): string | null {
  if (card.type === 'launch' && card.phase) {
    return card.phase.toUpperCase();
  }
  if (card.type === 'timeline') {
    // Use lane as phase indicator
    switch (card.lane) {
      case 'new_creations':
        return 'NEW';
      case 'about_to_happen':
        return 'SOON';
      case 'at_risk':
        return 'RISK';
      case 'graduation':
        return 'GRAD';
    }
  }
  return null;
}

/**
 * Format time remaining
 */
function formatTimeRemaining(seconds: number): string {
  if (seconds < 60) {
    return `${seconds}s`;
  }
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) {
    return `${minutes}m`;
  }
  const hours = Math.floor(minutes / 60);
  return `${hours}h`;
}

/**
 * Get metric color based on value
 */
function getMetricColor(value: number, type: 'gap' | 'stability' | 'other'): string {
  if (type === 'gap') {
    // Higher gap = worse (crimson)
    if (value >= 40) return '#EF4444';
    if (value >= 20) return '#F59E0B';
    return '#10B981';
  }
  if (type === 'stability') {
    // Higher stability = better (emerald)
    if (value >= 70) return '#10B981';
    if (value >= 50) return '#F59E0B';
    return '#EF4444';
  }
  return '#F1F5F9';
}

/**
 * TickerCard Component
 * 
 * High-density BullX-style card with left image, right content, and metrics grid.
 * Layout: Flex Row (Left Image | Right Content).
 */
export function TickerCard({ card }: TickerCardProps) {
  const navigate = useNavigate();
  const [tracked, setTracked] = useState<boolean>(isTracked(card.id));
  const borderColor = getLaneBorderColor(card.lane);
  const phaseBadge = getPhaseBadge(card);

  useEffect(() => {
    setTracked(isTracked(card.id));
  }, [card.id]);

  const handleClick = () => {
    if (card.type === 'timeline') {
      navigate(`/timeline/${card.id}`);
    } else {
      navigate(`/launchpad/${card.id}`);
    }
  };

  const handleTrack = (e: React.MouseEvent) => {
    e.stopPropagation();
    const newTrackedState = toggleTrack(card.id);
    setTracked(newTrackedState);
  };

  // Choose icon based on card type
  const IconComponent = card.type === 'timeline' ? GitBranch : Sparkles;

  // Extract ticker/ID from card.id (e.g., "ops_new_timeline_1" -> "TL-001")
  const tickerId = card.id.split('_').pop()?.toUpperCase() || 'N/A';

  return (
    <div
      className="bg-[#1a1a1a] border-l-2 rounded-lg p-3 flex items-start gap-3 hover:bg-[#222222] transition-all group cursor-pointer relative"
      style={{
        borderLeftColor: borderColor,
      }}
      onClick={handleClick}
    >
      {/* Left: Category Icon/Image */}
      <div className="relative flex-shrink-0">
        <div className="w-14 h-14 bg-white/10 rounded-lg flex items-center justify-center border border-white/10">
          <IconComponent className="w-7 h-7 text-white/70" />
        </div>
        {/* Phase Badge Overlay */}
        {phaseBadge && (
          <div
            className="absolute -bottom-1 -right-1 px-1.5 py-0.5 rounded text-[10px] font-bold uppercase"
            style={{
              backgroundColor: borderColor,
              color: '#000000',
            }}
          >
            {phaseBadge}
          </div>
        )}
      </div>

      {/* Right: Content */}
      <div className="flex-1 min-w-0 flex flex-col gap-2">
        {/* Row 1: Title + Ticker/ID */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-bold text-white truncate leading-tight">
              {card.title}
            </h4>
            <p className="text-xs text-terminal-text-secondary font-mono mt-0.5">
              {card.type === 'timeline' ? 'TL' : 'LN'}-{tickerId}
            </p>
          </div>
        </div>

        {/* Row 2: Metrics Grid */}
        <div className="grid grid-cols-2 gap-2">
          {/* Gap Metric */}
          {card.logicGap !== undefined && (
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-terminal-text-secondary">Gap:</span>
              <span
                className="text-xs font-mono font-semibold"
                style={{ color: getMetricColor(card.logicGap, 'gap') }}
              >
                {Math.round(card.logicGap)}%
              </span>
            </div>
          )}

          {/* Stability Metric */}
          {card.stability !== undefined && (
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-terminal-text-secondary">Stab:</span>
              <span
                className="text-xs font-mono font-semibold"
                style={{ color: getMetricColor(card.stability, 'stability') }}
              >
                {Math.round(card.stability)}%
              </span>
            </div>
          )}

          {/* Fork ETA Metric */}
          {card.nextForkEtaSec !== undefined && (
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-terminal-text-secondary">Fork:</span>
              <span className="text-xs font-mono font-semibold text-status-info">
                {formatTimeRemaining(card.nextForkEtaSec)}
              </span>
            </div>
          )}

          {/* Quality Score (for launches) */}
          {card.qualityScore !== undefined && (
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-terminal-text-secondary">Score:</span>
              <span
                className="text-xs font-mono font-semibold"
                style={{ color: getMetricColor(card.qualityScore, 'stability') }}
              >
                {Math.round(card.qualityScore)}
              </span>
            </div>
          )}
        </div>

        {/* Footer: Quick Action Button */}
        <div className="flex items-center justify-end mt-auto pt-1">
          <button
            onClick={handleTrack}
            className="w-6 h-6 flex items-center justify-center bg-white/5 hover:bg-white/10 rounded border border-white/10 hover:border-white/20 transition"
            title={tracked ? 'Remove from watchlist' : 'Add to watchlist'}
          >
            <Eye className="w-3.5 h-3.5 text-white/60" />
          </button>
        </div>
      </div>
    </div>
  );
}
