import { useNavigate } from 'react-router-dom';
import { Database, ExternalLink } from 'lucide-react';
import type { LaunchCard } from '../../types/launchpad';

/**
 * LaunchCardMini Props
 */
export interface LaunchCardMiniProps {
  /** Launch card data */
  launch: LaunchCard;
}

/**
 * Get phase badge color and label
 */
function getPhaseBadge(phase: LaunchCard['phase']): { bg: string; text: string; label: string } {
  switch (phase) {
    case 'draft':
      return { bg: '#64748B', text: '#FFFFFF', label: 'DRAFT' };
    case 'sandbox':
      return { bg: '#F59E0B', text: '#FFFFFF', label: 'SANDBOX' };
    case 'pilot':
      return { bg: '#3B82F6', text: '#FFFFFF', label: 'PILOT' };
    case 'graduated':
      return { bg: '#10B981', text: '#FFFFFF', label: 'GRADUATED' };
    case 'failed':
      return { bg: '#EF4444', text: '#FFFFFF', label: 'FAILED' };
  }
}

/**
 * Get category badge color
 */
function getCategoryColor(category: LaunchCard['category']): string {
  switch (category) {
    case 'theatre':
      return '#3B82F6';
    case 'osint':
      return '#8B5CF6';
  }
}

/**
 * Get quality score color
 */
function getQualityColor(score: number): string {
  if (score >= 80) return '#10B981'; // emerald
  if (score >= 60) return '#F59E0B'; // amber
  return '#EF4444'; // crimson
}

/**
 * LaunchCardMini Component
 * 
 * Compact card displaying launch information with phase badge,
 * quality score meter, category tag, fork range, and export badge.
 */
export function LaunchCardMini({ launch }: LaunchCardMiniProps) {
  const navigate = useNavigate();
  const phaseBadge = getPhaseBadge(launch.phase);
  const categoryColor = getCategoryColor(launch.category);
  const qualityColor = getQualityColor(launch.qualityScore);

  const handleView = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigate(`/launchpad/${launch.id}`);
  };

  return (
    <div className="bg-[#111111] border border-[#1A1A1A] rounded-lg p-4 hover:border-[#333] transition">
      {/* Header Row */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold text-terminal-text uppercase tracking-wide truncate mb-1">
            {launch.title}
          </h4>
          <div className="flex items-center gap-2 flex-wrap">
            {/* Phase Badge */}
            <span
              className="text-xs font-bold px-2 py-0.5 rounded"
              style={{
                backgroundColor: phaseBadge.bg,
                color: phaseBadge.text,
              }}
            >
              {phaseBadge.label}
            </span>
            {/* Category Tag */}
            <span
              className="text-xs px-2 py-0.5 rounded border"
              style={{
                borderColor: categoryColor,
                color: categoryColor,
                backgroundColor: `${categoryColor}10`,
              }}
            >
              {launch.category.toUpperCase()}
            </span>
            {/* Export Badge */}
            {launch.exportEligible && (
              <span className="flex items-center gap-1 text-xs text-status-info">
                <Database className="w-3 h-3" />
                EXPORT
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Quality Score Meter */}
      <div className="mb-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-terminal-text-secondary">Quality Score</span>
          <span
            className="text-xs font-mono font-semibold"
            style={{ color: qualityColor }}
          >
            {launch.qualityScore}
          </span>
        </div>
        <div className="w-full h-1.5 bg-[#1A1A1A] rounded-full overflow-hidden">
          <div
            className="h-full transition-all"
            style={{
              width: `${launch.qualityScore}%`,
              backgroundColor: qualityColor,
            }}
          />
        </div>
      </div>

      {/* Fork Range */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-terminal-text-secondary">Fork Range</span>
        <span className="text-xs font-mono text-terminal-text">
          {launch.forkTargetRange[0]}-{launch.forkTargetRange[1]}
        </span>
      </div>

      {/* Action Button */}
      <button
        onClick={handleView}
        className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs bg-terminal-bg border border-terminal-border rounded hover:border-status-info hover:text-status-info transition"
      >
        <ExternalLink className="w-3 h-3" />
        VIEW
      </button>
    </div>
  );
}
