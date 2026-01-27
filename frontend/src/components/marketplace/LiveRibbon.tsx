import { GitFork, FlipHorizontal, ShieldAlert, Zap, CheckCircle2, AlertTriangle } from 'lucide-react';
import { clsx } from 'clsx';
import type { RibbonEvent } from '../../types/marketplace';

interface LiveRibbonProps {
  events: RibbonEvent[];
  onEventClick?: (event: RibbonEvent) => void;
}

/**
 * Get event tag styles
 */
function getEventTagStyles(type: RibbonEvent['type']): { bg: string; text: string; icon: React.ElementType } {
  const styles: Record<string, { bg: string; text: string; icon: React.ElementType }> = {
    fork: {
      bg: 'rgba(74, 222, 128, 0.2)',
      text: '#4ADE80',
      icon: GitFork,
    },
    flip: {
      bg: 'rgba(74, 222, 128, 0.2)',
      text: '#4ADE80',
      icon: FlipHorizontal,
    },
    paradox: {
      bg: 'rgba(139, 92, 246, 0.2)',
      text: '#8B5CF6',
      icon: AlertTriangle,
    },
    sabotage: {
      bg: 'rgba(251, 113, 133, 0.2)',
      text: '#FB7185',
      icon: ShieldAlert,
    },
    settle: {
      bg: 'rgba(74, 222, 128, 0.2)',
      text: '#4ADE80',
      icon: CheckCircle2,
    },
    wing: {
      bg: 'rgba(59, 130, 246, 0.2)',
      text: '#3B82F6',
      icon: Zap,
    },
  };

  return styles[type] || styles.fork;
}

/**
 * Format time display
 */
function formatTime(timeString: string): string {
  // Handle both relative times (e.g., "4m") and absolute times (e.g., "14:32:05")
  if (timeString.includes(':')) {
    return timeString;
  }
  return timeString;
}

/**
 * LiveRibbon Component
 * 
 * Horizontal scrolling ribbon showing live events:
 * - Forks (market splits)
 * - Paradoxes (logical contradictions)
 * - Consensus shifts (flips)
 * - Sabotages (market attacks)
 * - Settlements (market resolution)
 */
export function LiveRibbon({ events, onEventClick }: LiveRibbonProps) {
  if (events.length === 0) {
    return null;
  }

  return (
    <div className="w-full bg-terminal-bg border-b border-terminal-border overflow-hidden">
      <div className="flex items-center gap-2 py-2 px-4">
        {/* Live indicator - shifted to the left */}
        <div className="flex items-center gap-1.5 px-2 py-1 bg-status-success/20 border border-status-success/30 rounded-full flex-shrink-0">
          <span className="w-1.5 h-1.5 bg-status-success rounded-full animate-pulse" />
          <span className="text-[10px] font-bold text-status-success uppercase tracking-wider">
            Live
          </span>
        </div>
        
        {/* Divider */}
        <div style={{ width: 1, height: 20, background: 'var(--border-outer)' }}></div>

        {/* Event items */}
        <div className="flex items-center gap-2 overflow-x-auto scrollbar-hide" style={{ flex: 1 }}>
          {events.map((event, index) => {
            const tagStyles = getEventTagStyles(event.type);

            return (
              <button
                key={index}
                onClick={() => onEventClick?.(event)}
                className={clsx(
                  'flex items-center gap-2 px-3 py-1.5 rounded-full border transition-all',
                  'hover:scale-105 active:scale-95 flex-shrink-0 cursor-pointer',
                  'border-transparent'
                )}
                style={{
                  backgroundColor: `${tagStyles.text}15`,
                  borderColor: `${tagStyles.text}30`,
                }}
              >
                <span
                  className="text-[10px] font-bold px-1.5 py-0.5 rounded"
                  style={{
                    backgroundColor: tagStyles.bg,
                    color: tagStyles.text,
                  }}
                >
                  {event.type.toUpperCase()}
                </span>

                <span className="text-xs text-terminal-secondary truncate max-w-[200px]">
                  {event.title}
                </span>

                <span className="text-[10px] font-mono text-terminal-muted border-l border-terminal-border pl-2">
                  {formatTime(event.time)}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      <style>{`
        .scrollbar-hide {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
      `}</style>
    </div>
  );
}
