import { useNavigate } from 'react-router-dom';
import { ArrowRight, GitBranch, Sparkles } from 'lucide-react';
import type { OpsCard } from '../../types/opsBoard';

/**
 * TickerCard Props
 */
export interface TickerCardProps {
  /** Card data */
  card: OpsCard;
}

/**
 * Get status indicator color based on card state
 */
function getStatusColor(card: OpsCard): 'green' | 'red' {
  // Check for paradox or high risk indicators
  if (card.paradoxProximity && card.paradoxProximity > 50) {
    return 'red';
  }
  if (card.tags.includes('paradox_active')) {
    return 'red';
  }
  if (card.tags.includes('sabotage_heat')) {
    return 'red';
  }
  // Default to green (live)
  return 'green';
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
 * Get score badge value
 */
function getScoreBadge(card: OpsCard): string | null {
  if (card.type === 'launch' && card.qualityScore !== undefined) {
    return `${card.qualityScore}`;
  }
  if (card.type === 'timeline' && card.stability !== undefined) {
    return `${Math.round(card.stability)}`;
  }
  return null;
}

/**
 * Generate simple sparkline SVG (placeholder)
 */
function SparklinePlaceholder({ color = '#00FF41' }: { color?: string }) {
  const width = 60;
  const height = 20;
  const points = [
    { x: 0, y: 15 },
    { x: 10, y: 12 },
    { x: 20, y: 8 },
    { x: 30, y: 10 },
    { x: 40, y: 5 },
    { x: 50, y: 8 },
    { x: 60, y: 3 },
  ];

  const pathData = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');

  return (
    <svg width={width} height={height} className="overflow-visible">
      <path
        d={pathData}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/**
 * TickerCard Component
 * 
 * BullX-style compact ticker card with icon, title, badges, sparkline, and action button.
 * Fixed dimensions: 260px width, 80px height.
 */
export function TickerCard({ card }: TickerCardProps) {
  const navigate = useNavigate();
  const statusColor = getStatusColor(card);
  const phaseBadge = getPhaseBadge(card);
  const scoreBadge = getScoreBadge(card);
  const glowColor = statusColor === 'green' ? '#00FF41' : '#FF3B3B';

  const handleClick = () => {
    if (card.type === 'timeline') {
      navigate(`/timeline/${card.id}`);
    } else {
      navigate(`/launchpad/${card.id}`);
    }
  };

  // Choose icon based on card type
  const IconComponent = card.type === 'timeline' ? GitBranch : Sparkles;

  return (
    <div
      className="bg-white/5 border border-white/10 rounded-lg p-3 flex items-center gap-3 hover:border-white/20 transition-all group cursor-pointer"
      style={{
        width: '260px',
        height: '80px',
        boxShadow: 'none',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = `0 0 12px ${glowColor}40`;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = 'none';
      }}
      onClick={handleClick}
    >
      {/* Left: Icon/Avatar with Status Dot */}
      <div className="relative flex-shrink-0">
        <div className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center">
          <IconComponent className="w-5 h-5 text-white/70" />
        </div>
        {/* Status Indicator Dot */}
        <div
          className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-[#0D0D0D]"
          style={{
            backgroundColor: statusColor === 'green' ? '#00FF41' : '#FF3B3B',
            boxShadow: `0 0 4px ${statusColor === 'green' ? '#00FF41' : '#FF3B3B'}`,
          }}
        />
      </div>

      {/* Middle: Title + Badges */}
      <div className="flex-1 min-w-0 flex flex-col justify-center gap-1">
        {/* Title */}
        <h4 className="text-[13px] font-bold text-white truncate leading-tight">
          {card.title}
        </h4>
        {/* Badges */}
        <div className="flex items-center gap-1.5">
          {phaseBadge && (
            <span className="px-1.5 py-0.5 bg-white/10 rounded text-[10px] font-semibold text-white/80 uppercase">
              {phaseBadge}
            </span>
          )}
          {scoreBadge && (
            <span className="px-1.5 py-0.5 bg-white/10 rounded text-[10px] font-semibold text-white/80">
              {scoreBadge}
            </span>
          )}
        </div>
      </div>

      {/* Right: Sparkline + Action Button */}
      <div className="flex flex-col items-end justify-between h-full flex-shrink-0">
        {/* Sparkline */}
        <div className="opacity-60 group-hover:opacity-100 transition-opacity">
          <SparklinePlaceholder color={statusColor === 'green' ? '#00FF41' : '#FF3B3B'} />
        </div>
        {/* Action Button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            handleClick();
          }}
          className="w-6 h-6 flex items-center justify-center bg-white/10 hover:bg-white/20 rounded border border-white/10 hover:border-white/20 transition"
        >
          <ArrowRight className="w-3 h-3 text-white/70" />
        </button>
      </div>
    </div>
  );
}
