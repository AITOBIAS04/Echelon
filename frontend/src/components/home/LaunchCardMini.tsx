import { useNavigate } from 'react-router-dom';
import { Database, ExternalLink } from 'lucide-react';
import type { LaunchCard } from '../../types/launchpad';
import { PHASE_COLORS, CATEGORY_COLORS, getQualityColor } from '../../constants/launchpad';

/**
 * LaunchCardMini Props
 */
export interface LaunchCardMiniProps {
  /** Launch card data */
  launch: LaunchCard;
}

/**
 * LaunchCardMini Component
 * 
 * Compact card displaying launch information with phase badge,
 * quality score meter, category tag, fork range, and export badge.
 */
export function LaunchCardMini({ launch }: LaunchCardMiniProps) {
  const navigate = useNavigate();
  const phaseBadge = PHASE_COLORS[launch.phase];
  const categoryColor = CATEGORY_COLORS[launch.category];
  const qualityColor = getQualityColor(launch.qualityScore);

  const handleView = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigate(`/launchpad/${launch.id}`);
  };

  return (
    <div className="terminal-card group relative overflow-hidden p-4 hover:shadow-elevation-2 hover:scale-[1.005]">
      {/* Top-edge gradient highlight */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-terminal-border-light/60 to-transparent" />

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
          <span className="data-label">Quality Score</span>
          <span
            className="data-value"
            style={{ color: qualityColor }}
          >
            {launch.qualityScore}
          </span>
        </div>
        <div className="w-full h-1.5 bg-terminal-border rounded-full overflow-hidden">
          <div
            className="h-full transition-all rounded-full"
            style={{
              width: `${launch.qualityScore}%`,
              background: `linear-gradient(90deg, ${qualityColor}88, ${qualityColor})`,
            }}
          />
        </div>
      </div>

      {/* Fork Range */}
      <div className="flex items-center justify-between mb-3">
        <span className="data-label">Fork Range</span>
        <span className="data-value">
          {launch.forkTargetRange[0]}-{launch.forkTargetRange[1]}
        </span>
      </div>

      {/* Action Button */}
      <button
        onClick={handleView}
        className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs font-semibold bg-terminal-bg border border-terminal-border rounded-lg transition-all group-hover:border-echelon-cyan/30 group-hover:text-echelon-cyan text-terminal-text-secondary"
      >
        <ExternalLink className="w-3 h-3" />
        VIEW
      </button>
    </div>
  );
}
