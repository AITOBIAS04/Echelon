import { useNavigate } from 'react-router-dom';
import { GitBranch, Sparkles } from 'lucide-react';
import type { OpsCard } from '../../types/opsBoard';
import { getTrendingReason } from '../../lib/trendingRanker';

/**
 * OpsRow Props
 */
export interface OpsRowProps {
  /** Card data */
  card: OpsCard;
}

/**
 * Get lane border color
 */
function getLaneBorderColor(lane: OpsCard['lane']): string {
  switch (lane) {
    case 'new_creations':
      return '#00FF41'; // Green
    case 'about_to_happen':
      return '#FF9500'; // Orange
    case 'at_risk':
      return '#FF3B3B'; // Red
    case 'graduation':
      return '#AA66FF'; // Purple
  }
}

/**
 * Get phase badge text
 */
function getPhaseBadge(card: OpsCard): string | null {
  if (card.type === 'launch' && card.phase) {
    // Single letter abbreviation
    switch (card.phase) {
      case 'pilot':
        return 'P';
      case 'sandbox':
        return 'S';
      case 'draft':
        return 'D';
      case 'graduated':
        return 'G';
    }
  }
  if (card.type === 'timeline') {
    // Use lane as phase indicator
    switch (card.lane) {
      case 'new_creations':
        return 'N';
      case 'about_to_happen':
        return 'A';
      case 'at_risk':
        return 'R';
      case 'graduation':
        return 'G';
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
 * Get status pill text and color
 */
function getStatusPill(card: OpsCard): { text: string; color: string } | null {
  // Priority: Fork ETA > Logic Gap > Stability > Quality Score
  if (card.nextForkEtaSec !== undefined) {
    return {
      text: `Fork: ${formatTimeRemaining(card.nextForkEtaSec)}`,
      color: '#00D4FF',
    };
  }
  if (card.logicGap !== undefined) {
    const color = card.logicGap >= 40 ? '#FF3B3B' : card.logicGap >= 20 ? '#FF9500' : '#00FF41';
    return {
      text: `Gap: ${Math.round(card.logicGap)}%`,
      color,
    };
  }
  if (card.stability !== undefined) {
    const color = card.stability >= 70 ? '#00FF41' : card.stability >= 50 ? '#FF9500' : '#FF3B3B';
    return {
      text: `Stab: ${Math.round(card.stability)}%`,
      color,
    };
  }
  if (card.qualityScore !== undefined) {
    const color = card.qualityScore >= 70 ? '#00FF41' : card.qualityScore >= 50 ? '#FF9500' : '#FF3B3B';
    return {
      text: `Score: ${Math.round(card.qualityScore)}`,
      color,
    };
  }
  return null;
}

/**
 * Generate mini sparkline SVG
 */
function MiniSparkline({ color = '#00FF41' }: { color?: string }) {
  const width = 40;
  const height = 12;
  const points = [
    { x: 0, y: 8 },
    { x: 5, y: 6 },
    { x: 10, y: 4 },
    { x: 15, y: 5 },
    { x: 20, y: 3 },
    { x: 25, y: 4 },
    { x: 30, y: 2 },
    { x: 35, y: 3 },
    { x: 40, y: 1 },
  ];

  const pathData = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');

  return (
    <svg width={width} height={height} className="overflow-visible">
      <path
        d={pathData}
        fill="none"
        stroke={color}
        strokeWidth="1"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/**
 * OpsRow Component
 * 
 * High-density horizontal row component for BullX-style layout.
 * Minimal padding, compact design for maximum information density.
 */
export function OpsRow({ card }: OpsRowProps) {
  const navigate = useNavigate();
  const borderColor = getLaneBorderColor(card.lane);
  const phaseBadge = getPhaseBadge(card);
  const isTrendingLane = card.lane === 'about_to_happen';
  const trendingReason = isTrendingLane ? getTrendingReason(card) : null;
  const statusPill = isTrendingLane ? null : getStatusPill(card);

  const handleClick = () => {
    if (card.type === 'timeline') {
      navigate(`/timeline/${card.id}`);
    } else {
      navigate(`/launchpad/${card.id}`);
    }
  };

  // Choose icon based on card type
  const IconComponent = card.type === 'timeline' ? GitBranch : Sparkles;

  // Determine sparkline color based on status
  const sparklineColor = statusPill?.color || borderColor;

  const reasonToneClass = trendingReason
    ? ({
        green: 'bg-green-500/15 text-green-300 border-green-500/30',
        amber: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
        red: 'bg-red-500/15 text-red-300 border-red-500/30',
        purple: 'bg-purple-500/15 text-purple-300 border-purple-500/30',
      } as const)[trendingReason.tone]
    : '';

  return (
    <div
      className="bg-[#1a1a1a] border-l-2 p-2 flex items-center gap-2 hover:bg-[#222222] transition-all cursor-pointer group"
      style={{
        borderLeftColor: borderColor,
      }}
      onClick={handleClick}
    >
      {/* Left: Thumbnail with Phase Badge */}
      <div className="relative flex-shrink-0">
        <div className="w-10 h-10 bg-white/10 rounded border border-white/10 flex items-center justify-center">
          <IconComponent className="w-5 h-5 text-white/70" />
        </div>
        {/* Phase Badge Overlay */}
        {phaseBadge && (
          <div
            className="absolute -bottom-0.5 -right-0.5 w-4 h-4 rounded text-[8px] font-bold flex items-center justify-center"
            style={{
              backgroundColor: borderColor,
              color: '#000000',
            }}
          >
            {phaseBadge}
          </div>
        )}
      </div>

      {/* Center: Title + Status Pill */}
      <div className="flex-1 min-w-0 flex flex-col gap-0.5">
        <h4 className="text-sm font-bold text-white truncate leading-tight whitespace-nowrap overflow-hidden text-ellipsis">
          {card.title}
        </h4>
        {trendingReason ? (
          <span
            className={`text-[10px] font-mono font-semibold inline-flex items-center px-2 py-0.5 rounded border ${reasonToneClass} w-fit max-w-full truncate`}
            title={trendingReason.label}
          >
            {trendingReason.label}
          </span>
        ) : statusPill ? (
          <span
            className="text-xs font-mono font-semibold inline-block truncate"
            style={{ color: statusPill.color }}
          >
            {statusPill.text}
          </span>
        ) : null}
      </div>

      {/* Right: Mini Sparkline */}
      <div className="flex-shrink-0 opacity-60 group-hover:opacity-100 transition-opacity">
        <MiniSparkline color={sparklineColor} />
      </div>
    </div>
  );
}
