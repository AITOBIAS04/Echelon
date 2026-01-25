import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ExternalLink, Plus, Check } from 'lucide-react';
import { toggleTrack, isTracked } from '../../lib/tracking';
import type { OpsCard } from '../../types/opsBoard';

/**
 * OpsCard Props
 */
export interface OpsCardProps {
  /** Card data */
  card: OpsCard;
  /** Compact mode - reduces height and simplifies layout */
  compact?: boolean;
}

/**
 * Get lane badge color and label
 */
function getLaneBadge(lane: OpsCard['lane']): { bg: string; text: string; label: string } {
  switch (lane) {
    case 'new_creations':
      return { bg: '#10B981', text: '#FFFFFF', label: 'NEW' };
    case 'about_to_happen':
      return { bg: '#F59E0B', text: '#FFFFFF', label: 'SOON' };
    case 'at_risk':
      return { bg: '#EF4444', text: '#FFFFFF', label: 'RISK' };
    case 'graduation':
      return { bg: '#8B5CF6', text: '#FFFFFF', label: 'GRAD' };
  }
}

/**
 * Get tag color
 */
function getTagColor(tag: OpsCard['tags'][0]): string {
  switch (tag) {
    case 'fork_soon':
      return '#3B82F6';
    case 'disclosure_active':
      return '#F59E0B';
    case 'evidence_flip':
      return '#10B981';
    case 'brittle':
      return '#F59E0B';
    case 'paradox_active':
      return '#EF4444';
    case 'high_entropy':
      return '#EF4444';
    case 'sabotage_heat':
      return '#EF4444';
    case 'graduating':
      return '#8B5CF6';
  }
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
 * OpsCard Component
 * 
 * Displays an operations card with title, lane badge, metrics, tags, and actions.
 * Supports compact mode for reduced height and simplified layout.
 */
export function OpsCard({ card, compact = false }: OpsCardProps) {
  const navigate = useNavigate();
  const laneBadge = getLaneBadge(card.lane);
  const [tracked, setTracked] = useState<boolean>(isTracked(card.id));

  // Update tracked state when card.id changes
  useEffect(() => {
    setTracked(isTracked(card.id));
  }, [card.id]);

  const handleView = () => {
    if (card.type === 'timeline') {
      navigate(`/timeline/${card.id}`);
    } else {
      navigate(`/launchpad/${card.id}`);
    }
  };

  const handleTrack = () => {
    const newTrackedState = toggleTrack(card.id);
    setTracked(newTrackedState);
  };

  // Determine which metrics to show
  const metrics: Array<{ label: string; value: string; color?: string }> = [];

  if (card.type === 'timeline') {
    if (card.stability !== undefined) {
      metrics.push({
        label: 'Stability',
        value: `${card.stability.toFixed(0)}%`,
        color: card.stability >= 70 ? '#10B981' : card.stability >= 50 ? '#F59E0B' : '#EF4444',
      });
    }
    if (card.logicGap !== undefined) {
      metrics.push({
        label: 'Logic Gap',
        value: `${card.logicGap.toFixed(0)}%`,
        color: card.logicGap >= 60 ? '#EF4444' : card.logicGap >= 40 ? '#F59E0B' : '#10B981',
      });
    }
    if (card.nextForkEtaSec !== undefined) {
      metrics.push({
        label: 'Next Fork',
        value: formatTimeRemaining(card.nextForkEtaSec),
        color: '#3B82F6',
      });
    }
    if (card.paradoxProximity !== undefined && card.paradoxProximity > 50) {
      metrics.push({
        label: 'Paradox',
        value: `${card.paradoxProximity.toFixed(0)}%`,
        color: '#EF4444',
      });
    }
  } else {
    // Launch metrics
    if (card.qualityScore !== undefined) {
      metrics.push({
        label: 'Quality',
        value: `${card.qualityScore.toFixed(0)}`,
        color: card.qualityScore >= 80 ? '#10B981' : card.qualityScore >= 60 ? '#F59E0B' : '#EF4444',
      });
    }
    if (card.phase) {
      metrics.push({
        label: 'Phase',
        value: card.phase.toUpperCase(),
      });
    }
  }

  // For compact mode, show only 2 metrics
  const displayMetrics = compact ? metrics.slice(0, 2) : metrics.slice(0, 4);

  if (compact) {
    return (
      <div className="bg-[#0D0D0D] border border-[#1A1A1A] rounded-lg p-3 hover:border-[#333] transition mb-2 w-[240px] md:w-[280px]">
        {/* Header: Title + Phase Badge */}
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-bold text-terminal-text uppercase tracking-wide truncate flex-1 min-w-0">
            {card.title}
          </h4>
          <span
            className="text-[10px] font-bold px-1.5 py-0.5 rounded flex-shrink-0 ml-2"
            style={{
              backgroundColor: laneBadge.bg,
              color: laneBadge.text,
            }}
          >
            {laneBadge.label}
          </span>
        </div>

        {/* Body: 2 metrics side-by-side */}
        {displayMetrics.length > 0 && (
          <div className="flex items-center gap-3 mb-2">
            {displayMetrics.map((metric, idx) => (
              <div key={idx} className="flex-1">
                <span
                  className="text-xs font-mono font-semibold"
                  style={{ color: metric.color || '#FFFFFF' }}
                >
                  {metric.value}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Footer: VIEW button + TRACK icon */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleView}
            className="flex-1 flex items-center justify-center gap-1 px-2 py-1 text-[10px] bg-transparent border border-terminal-border rounded hover:border-status-info hover:text-status-info transition"
          >
            VIEW
          </button>
          <button
            onClick={handleTrack}
            className={`p-1.5 border rounded transition ${
              tracked
                ? 'bg-status-info/20 border-status-info text-status-info'
                : 'bg-transparent border-terminal-border hover:border-status-info hover:text-status-info'
            }`}
            title={tracked ? 'Remove from watchlist' : 'Add to watchlist'}
          >
            {tracked ? <Check className="w-3 h-3" /> : <Plus className="w-3 h-3" />}
          </button>
        </div>
      </div>
    );
  }

  // Full mode (original layout)
  return (
    <div className="bg-[#111111] border border-[#1A1A1A] rounded-lg p-3 hover:border-[#333] transition mb-2">
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold text-terminal-text uppercase tracking-wide truncate mb-1">
            {card.title}
          </h4>
          {card.subtitle && (
            <p className="text-xs text-terminal-muted truncate">{card.subtitle}</p>
          )}
        </div>
        <span
          className="text-xs font-bold px-2 py-0.5 rounded flex-shrink-0 ml-2"
          style={{
            backgroundColor: laneBadge.bg,
            color: laneBadge.text,
          }}
        >
          {laneBadge.label}
        </span>
      </div>

      {/* Tags */}
      {card.tags.length > 0 && (
        <div className="flex items-center gap-1.5 flex-wrap mb-2">
          {card.tags.map((tag) => {
            const tagColor = getTagColor(tag);
            return (
              <span
                key={tag}
                className="text-[10px] px-1.5 py-0.5 rounded border"
                style={{
                  borderColor: tagColor,
                  color: tagColor,
                  backgroundColor: `${tagColor}10`,
                }}
              >
                {tag.replace('_', ' ').toUpperCase()}
              </span>
            );
          })}
        </div>
      )}

      {/* Metrics */}
      {displayMetrics.length > 0 && (
        <div className="grid grid-cols-2 gap-2 mb-3">
          {displayMetrics.map((metric, idx) => (
            <div key={idx} className="flex flex-col">
              <span className="text-[10px] text-terminal-muted uppercase">{metric.label}</span>
              <span
                className="text-xs font-mono font-semibold"
                style={{ color: metric.color || '#FFFFFF' }}
              >
                {metric.value}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2">
        <button
          onClick={handleView}
          className="flex-1 flex items-center justify-center gap-1.5 px-2 py-1.5 text-xs bg-terminal-bg border border-terminal-border rounded hover:border-status-info hover:text-status-info transition"
        >
          <ExternalLink className="w-3 h-3" />
          VIEW
        </button>
        <button
          onClick={handleTrack}
          className={`flex items-center justify-center gap-1.5 px-2 py-1.5 text-xs border rounded transition ${
            tracked
              ? 'bg-status-info/20 border-status-info text-status-info'
              : 'bg-terminal-bg border-terminal-border hover:border-status-info hover:text-status-info'
          }`}
          title={tracked ? 'Remove from watchlist' : 'Add to watchlist'}
        >
          {tracked ? <Check className="w-3 h-3" /> : <Plus className="w-3 h-3" />}
          {tracked ? 'TRACKED' : 'TRACK'}
        </button>
      </div>
    </div>
  );
}
