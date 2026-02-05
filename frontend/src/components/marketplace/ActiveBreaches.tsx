import { AlertTriangle, Clock, ChevronRight } from 'lucide-react';
import { clsx } from 'clsx';
import type { Breach } from '../../types/marketplace';

interface ActiveBreachesProps {
  breaches: Breach[];
  onViewAll?: () => void;
  onBreachClick?: (breach: Breach) => void;
}

/**
 * Get severity dot styles
 */
function getSeverityStyles(severity: Breach['severity']): { color: string; shadow: string } {
  const styles: Record<string, { color: string; shadow: string }> = {
    critical: {
      color: '#FB7185',
      shadow: 'rgba(251, 113, 133, 0.4)',
    },
    high: {
      color: '#F97316',
      shadow: 'transparent',
    },
    medium: {
      color: '#FACC15',
      shadow: 'transparent',
    },
    low: {
      color: '#4ADE80',
      shadow: 'transparent',
    },
  };

  return styles[severity] || styles.low;
}

/**
 * Format time display
 */
function formatBreachTime(timeString: string): string {
  // Handle both relative times (e.g., "4m") and absolute times (e.g., "28m")
  return timeString;
}

/**
 * ActiveBreaches Component
 * 
 * Sidebar panel showing active breaches:
 * - Paradoxes
 * - Stability collapses
 * - Oracle deviations
 * - Sensor contradictions
 */
export function ActiveBreaches({ breaches, onViewAll, onBreachClick }: ActiveBreachesProps) {
  if (breaches.length === 0) {
    return null;
  }

  const criticalCount = breaches.filter(b => b.severity === 'critical').length;

  return (
    <div className="flex flex-col">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-terminal-panel/95 backdrop-blur-sm px-4 py-3 border-b border-terminal-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-status-warning" />
            <span className="text-xs font-bold text-terminal-text uppercase tracking-wider">
              Active Breaches
            </span>
            {criticalCount > 0 && (
              <span className="flex items-center gap-1 px-1.5 py-0.5 bg-status-danger/20 border border-status-danger/30 rounded text-[9px] font-bold text-status-danger uppercase animate-pulse">
                {criticalCount} Critical
              </span>
            )}
          </div>
          {onViewAll && (
            <button
              onClick={onViewAll}
              className="text-[10px] text-status-info hover:underline flex items-center gap-0.5"
            >
              {breaches.length} Active
              <ChevronRight className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>

      {/* Breaches List */}
      <div className="flex-1 overflow-y-auto">
        {breaches.map((breach, index) => {
          const severityStyles = getSeverityStyles(breach.severity);

          return (
            <div
              key={breach.id || index}
              className={clsx(
                'border-b border-terminal-border last:border-b-0',
                'transition-colors hover:bg-terminal-card/50 cursor-pointer',
                breach.severity === 'critical' && 'bg-status-danger/5'
              )}
              onClick={() => onBreachClick?.(breach)}
            >
              <div className="p-3">
                {/* Top: Severity dot + Category + Time */}
                <div className="flex items-center gap-2 mb-1.5">
                  <span
                    className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                    style={{
                      backgroundColor: severityStyles.color,
                      boxShadow: severityStyles.shadow ? `0 0 6px ${severityStyles.shadow}` : 'none',
                    }}
                  />
                  <span className="text-[10px] font-bold font-mono text-terminal-text-muted uppercase tracking-wider">
                    {breach.category}
                  </span>
                  <span className="text-[10px] font-mono text-terminal-text-muted ml-auto">
                    {formatBreachTime(breach.time)}
                  </span>
                </div>

                {/* Title */}
                <p className="text-xs text-terminal-secondary leading-snug">
                  {breach.title}
                </p>

                {/* Severity indicator bar */}
                {breach.severity === 'critical' && (
                  <div className="mt-2 flex items-center gap-1.5">
                    <div className="flex-1 h-1 bg-terminal-bg rounded-full overflow-hidden">
                      <div
                        className="h-full bg-status-danger animate-pulse"
                        style={{ width: '75%' }}
                      />
                    </div>
                    <span className="text-[9px] text-status-danger font-bold uppercase">
                      Critical
                    </span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Quick Actions Footer */}
      <div className="px-4 py-3 bg-terminal-bg border-t border-terminal-border">
        <div className="flex items-center justify-between text-[10px]">
          <span className="text-terminal-text-muted">
            Last updated: Just now
          </span>
          <button className="text-status-warning hover:underline flex items-center gap-1">
            <Clock className="w-3 h-3" />
            View History
          </button>
        </div>
      </div>
    </div>
  );
}
