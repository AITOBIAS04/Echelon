import { useNavigate } from 'react-router-dom';
import { GitBranch, Sparkles, TrendingUp, Clock, AlertTriangle, CheckCircle } from 'lucide-react';
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
 * Get lane accent color
 */
function getLaneAccentColor(lane: OpsCard['lane']): string {
  switch (lane) {
    case 'new_creations':
      return '#10B981'; // Emerald
    case 'about_to_happen':
      return '#F59E0B'; // Amber
    case 'at_risk':
      return '#EF4444'; // Crimson
    case 'graduation':
      return '#8B5CF6'; // Purple
  }
}

/**
 * Get phase badge text
 */
function getPhaseBadge(card: OpsCard): string | null {
  if (card.type === 'launch' && card.phase) {
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
 * Get status pill configuration
 */
function getStatusPill(card: OpsCard): { text: string; className: string } | null {
  if (card.nextForkEtaSec !== undefined) {
    return {
      text: `Fork: ${formatTimeRemaining(card.nextForkEtaSec)}`,
      className: 'bg-status-info/10 text-status-info border-status-info/20',
    };
  }
  if (card.logicGap !== undefined) {
    const colorClass = card.logicGap >= 40 
      ? 'bg-status-danger/10 text-status-danger border-status-danger/20'
      : card.logicGap >= 20 
        ? 'bg-status-warning/10 text-status-warning border-status-warning/20'
        : 'bg-status-success/10 text-status-success border-status-success/20';
    return {
      text: `Gap: ${Math.round(card.logicGap)}%`,
      className: colorClass,
    };
  }
  if (card.stability !== undefined) {
    const colorClass = card.stability >= 70 
      ? 'bg-status-success/10 text-status-success border-status-success/20'
      : card.stability >= 50 
        ? 'bg-status-warning/10 text-status-warning border-status-warning/20'
        : 'bg-status-danger/10 text-status-danger border-status-danger/20';
    return {
      text: `Stab: ${Math.round(card.stability)}%`,
      className: colorClass,
    };
  }
  if (card.score !== undefined) {
    const colorClass = card.score >= 50 
      ? 'bg-status-success/10 text-status-success border-status-success/20'
      : card.score >= 30 
        ? 'bg-status-warning/10 text-status-warning border-status-warning/20'
        : 'bg-status-danger/10 text-status-danger border-status-danger/20';
    return {
      text: `Score: ${Math.round(card.score)}`,
      className: colorClass,
    };
  }
  return null;
}

/**
 * Get metric display
 */
function getMetricDisplay(card: OpsCard): { label: string; value: string; className: string } | null {
  if (card.marketCap !== undefined) {
    return {
      label: 'MC',
      value: card.marketCap >= 1000000 
        ? `$${(card.marketCap / 1000000).toFixed(1)}M`
        : `$${(card.marketCap / 1000).toFixed(0)}K`,
className: 'text-terminal-text',
    };
  }
  if (card.volume !== undefined) {
    return {
      label: 'Vol',
      value: card.volume >= 1000000 
        ? `$${(card.volume / 1000000).toFixed(1)}M`
        : `$${(card.volume / 1000).toFixed(0)}K`,
      className: 'text-terminal-text-secondary',
    };
  }
  if (card.nextForkEtaSec !== undefined) {
    return {
      label: 'ETA',
      value: formatTimeRemaining(card.nextForkEtaSec),
      className: 'text-status-info',
    };
  }
  return null;
}

/**
 * OpsRow Component
 * 
 * BullX-style card: minimal, information-dense, subtle borders, rounded corners.
 */
export function OpsRow({ card }: OpsRowProps) {
  const navigate = useNavigate();
  const laneAccentColor = getLaneAccentColor(card.lane);
  const phaseBadge = getPhaseBadge(card);
  const statusPill = getStatusPill(card);
  const metricDisplay = getMetricDisplay(card);
  const trendingReason = card.score !== undefined ? getTrendingReason(card) : null;

  return (
    <div
      onClick={() => navigate(card.type === 'launch' ? `/launchpad/${card.id}` : `/timeline/${card.id}`)}
      className="terminal-card cursor-pointer p-3"
      style={{
        borderLeftWidth: '3px',
        borderLeftColor: laneAccentColor,
      }}
    >
      {/* Header: Name + Phase badge */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          {/* Phase badge */}
          {phaseBadge && (
            <span 
              className="flex-shrink-0 w-5 h-5 flex items-center justify-center rounded text-[10px] font-bold"
              style={{ 
                backgroundColor: `${laneAccentColor}20`,
                color: laneAccentColor,
                border: `1px solid ${laneAccentColor}40`
              }}
            >
              {phaseBadge}
            </span>
          )}
          
          {/* Card name */}
          <span className="text-sm font-medium text-terminal-text truncate">
            {card.title}
          </span>
        </div>

        {/* Status pill */}
        {statusPill && (
          <span className={`status-pill flex-shrink-0 ml-2 ${statusPill.className}`}>
            {statusPill.text}
          </span>
        )}
      </div>

      {/* Secondary info: metrics row */}
      <div className="flex items-center justify-between">
        {/* Metrics */}
        <div className="flex items-center gap-3">
          {metricDisplay && (
            <>
              <span className="text-[10px] text-terminal-text-muted font-medium">
                {metricDisplay.label}
              </span>
              <span className={`text-xs font-mono ${metricDisplay.className}`}>
                {metricDisplay.value}
              </span>
            </>
          )}
          
          {/* Fork indicator */}
          {card.nextForkEtaSec !== undefined && card.nextForkEtaSec > 0 && card.nextForkEtaSec < 600 && (
            <div className="flex items-center gap-1 text-status-warning">
              <GitBranch className="w-3 h-3" />
              <span className="text-[10px] font-mono">
                {formatTimeRemaining(card.nextForkEtaSec)}
              </span>
            </div>
          )}
        </div>

        {/* Quick icons */}
        <div className="flex items-center gap-2">
          {/* Paradox alert */}
          {card.hasParadox && (
            <div className="flex items-center gap-1 px-1.5 py-0.5 bg-status-paradox/10 border border-status-paradox/20 rounded">
              <AlertTriangle className="w-3 h-3 text-status-paradox" />
            </div>
          )}
          
          {/* Trending indicator */}
          {trendingReason && (
            <div className="flex items-center gap-1 text-status-success">
              <TrendingUp className="w-3 h-3" />
            </div>
          )}
        </div>
      </div>

      {/* Fork countdown bar (if fork imminent) */}
      {card.nextForkEtaSec !== undefined && card.nextForkEtaSec > 0 && card.nextForkEtaSec < 600 && (
        <div className="mt-2 h-1 bg-terminal-border rounded-full overflow-hidden">
          <div 
            className="h-full rounded-full transition-all duration-1000"
            style={{ 
              width: `${Math.max(0, (1 - card.nextForkEtaSec / 600) * 100)}%`,
              backgroundColor: laneAccentColor,
            }}
          />
        </div>
      )}
    </div>
  );
}
