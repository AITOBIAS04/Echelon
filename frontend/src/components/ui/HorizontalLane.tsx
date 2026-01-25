import { type ReactNode } from 'react';
import { ChevronRight } from 'lucide-react';

/**
 * HorizontalLane Props
 */
export interface HorizontalLaneProps {
  /** Lane title */
  title: string;
  /** Icon to display next to title */
  icon?: ReactNode;
  /** Child elements to render in the horizontal scroll container */
  children: ReactNode;
  /** Optional "View All" link href */
  viewAllHref?: string;
  /** Optional "View All" click handler */
  onViewAll?: () => void;
}

/**
 * HorizontalLane Component
 * 
 * A reusable horizontal scrolling container with header and "View All" link.
 * Provides consistent styling and behavior for horizontal card lanes.
 */
export function HorizontalLane({
  title,
  icon,
  children,
  viewAllHref,
  onViewAll,
}: HorizontalLaneProps) {
  const handleViewAll = () => {
    if (onViewAll) {
      onViewAll();
    } else if (viewAllHref) {
      window.location.href = viewAllHref;
    }
  };

  const hasViewAll = viewAllHref || onViewAll;

  return (
    <div className="w-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-3 px-4 md:px-6">
        <div className="flex items-center gap-2">
          {icon && <div className="flex-shrink-0">{icon}</div>}
          <h3 className="text-lg font-bold text-terminal-text uppercase tracking-wide">
            {title}
          </h3>
        </div>
        {hasViewAll && (
          <button
            onClick={handleViewAll}
            className="flex items-center gap-1 text-xs text-terminal-text-secondary hover:text-status-info transition"
          >
            View All
            <ChevronRight className="w-3 h-3" />
          </button>
        )}
      </div>

      {/* Horizontal Scroll Container */}
      <div
        className="overflow-x-auto scrollbar-hide -mx-4 md:-mx-6 px-4 md:px-6"
        style={{
          scrollbarWidth: 'none',
          msOverflowStyle: 'none',
          WebkitOverflowScrolling: 'touch',
        }}
      >
        <div className="flex gap-3 pb-2" style={{ minWidth: 'min-content' }}>
          {children}
        </div>
      </div>

      {/* Hide scrollbar for webkit browsers */}
      <style>{`
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
      `}</style>
    </div>
  );
}
