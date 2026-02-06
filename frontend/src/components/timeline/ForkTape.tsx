import { useState, useMemo, useEffect, useRef } from 'react';
import { Play } from 'lucide-react';
import type { ForkEvent, ForkOption } from '../../types/timeline-detail';
import type { ReplayPointer } from '../../types/replay';
import { ReplayDrawer } from '../replay/ReplayDrawer';

/**
 * ForkTape Props
 */
export interface ForkTapeProps {
  /** Timeline identifier */
  timelineId: string;
  /** Array of fork events */
  forks: ForkEvent[];
  /** Callback when a fork card is clicked */
  onForkClick?: (forkId: string) => void;
}

type ForkFilter = 'all' | 'open' | 'locked' | 'settled';

/**
 * ForkOptionSparkline Component
 * 
 * Mini sparkline chart for fork option price history.
 */
function ForkOptionSparkline({ priceHistory }: { priceHistory: ForkOption['priceHistory'] }) {
  const width = 40;
  const height = 16;
  const padding = 2;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;

  if (!priceHistory || priceHistory.length === 0) {
    return (
      <svg width={width} height={height} className="opacity-50">
        <line
          x1={padding}
          y1={height / 2}
          x2={width - padding}
          y2={height / 2}
          stroke="#666"
          strokeWidth={1}
        />
      </svg>
    );
  }

  // Find min and max for scaling
  const prices = priceHistory.map((p) => p.price);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const priceRange = maxPrice - minPrice || 1;

  // Calculate points
  const points = priceHistory.map((point, index) => {
    const x = padding + (index / (priceHistory.length - 1 || 1)) * chartWidth;
    const normalized = (point.price - minPrice) / priceRange;
    const y = padding + chartHeight - normalized * chartHeight;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg width={width} height={height} className="overflow-visible">
      <polyline
        points={points}
        fill="none"
        stroke="#22D3EE"
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/**
 * Format time remaining or elapsed
 */
function formatTimeRemaining(
  timestamp: string | undefined,
  status: ForkEvent['status']
): string {
  if (!timestamp) return '';

  const now = new Date().getTime();
  const targetTime = new Date(timestamp).getTime();
  const diffMs = targetTime - now;
  const diffSeconds = Math.abs(Math.floor(diffMs / 1000));

  if (status === 'settled') {
    // Elapsed time
    if (diffSeconds < 60) {
      return `Settled ${diffSeconds}s ago`;
    }
    const minutes = Math.floor(diffSeconds / 60);
    if (minutes < 60) {
      return `Settled ${minutes}m ago`;
    }
    const hours = Math.floor(minutes / 60);
    return `Settled ${hours}h ago`;
  } else {
    // Remaining time
    if (diffSeconds < 60) {
      return `${status === 'open' ? 'Locks' : 'Executes'} in ${diffSeconds}s`;
    }
    const minutes = Math.floor(diffSeconds / 60);
    const seconds = diffSeconds % 60;
    if (minutes < 60) {
      return `${status === 'open' ? 'Locks' : 'Executes'} in ${minutes}m ${seconds}s`;
    }
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `${status === 'open' ? 'Locks' : 'Executes'} in ${hours}h ${remainingMinutes}m`;
  }
}

/**
 * Get status badge color
 */
function getStatusColor(status: ForkEvent['status']): string {
  switch (status) {
    case 'open':
      return '#22D3EE'; // cyan
    case 'repricing':
      return '#FF9500'; // amber
    case 'locked':
      return '#FF3B3B'; // red
    case 'executing':
      return '#9932CC'; // purple
    case 'settled':
      return '#666666'; // grey
    default:
      return '#666666';
  }
}

/**
 * ForkTape Component
 * 
 * Displays a live feed of fork events with filtering and mini sparklines.
 */
export function ForkTape({ timelineId, forks, onForkClick }: ForkTapeProps) {
  const [activeFilter, setActiveFilter] = useState<ForkFilter>('all');
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [, setTimeNow] = useState(Date.now());
  const [replayOpen, setReplayOpen] = useState(false);
  const [replayPointer, setReplayPointer] = useState<ReplayPointer | null>(null);

  // Update time every second for countdowns (triggers re-render)
  useEffect(() => {
    const interval = setInterval(() => {
      setTimeNow(Date.now());
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // Filter forks based on active filter
  const filteredForks = useMemo(() => {
    if (activeFilter === 'all') return forks;
    return forks.filter((fork) => {
      if (activeFilter === 'open') return fork.status === 'open';
      if (activeFilter === 'locked') return fork.status === 'locked';
      if (activeFilter === 'settled') return fork.status === 'settled';
      return true;
    });
  }, [forks, activeFilter]);

  // Auto-scroll to top when new forks are added
  useEffect(() => {
    if (scrollContainerRef.current && forks.length > 0) {
      scrollContainerRef.current.scrollTop = 0;
    }
  }, [forks.length]);

  const handleForkClick = (forkId: string) => {
    if (onForkClick) {
      onForkClick(forkId);
    }
  };

  const handleReplayClick = (e: React.MouseEvent, forkId: string) => {
    e.stopPropagation(); // Prevent triggering fork card click
    setReplayPointer({ timelineId, forkId });
    setReplayOpen(true);
  };

  const handleCloseReplay = () => {
    setReplayOpen(false);
    setReplayPointer(null);
  };

  return (
    <div className="bg-terminal-panel rounded-lg p-4 border border-terminal-border">
      {/* Filter Bar */}
      <div className="flex items-center gap-2 mb-4">
        {(['all', 'open', 'locked', 'settled'] as ForkFilter[]).map((filter) => (
          <button
            key={filter}
            onClick={() => setActiveFilter(filter)}
            className={`px-3 py-1 text-xs rounded transition ${
              activeFilter === filter
                ? 'border border-echelon-cyan text-echelon-cyan bg-echelon-cyan/10'
                : 'border border-terminal-border text-terminal-text-muted hover:text-terminal-text-secondary'
            }`}
          >
            {filter.charAt(0).toUpperCase() + filter.slice(1)}
          </button>
        ))}
      </div>

      {/* Fork Cards List */}
      <div
        ref={scrollContainerRef}
        className="space-y-2 max-h-[400px] overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent"
      >
        {filteredForks.length === 0 ? (
          <div className="text-center py-8 text-terminal-text-muted text-sm">
            No {activeFilter === 'all' ? '' : activeFilter}{' '}
            {activeFilter === 'all' ? 'forks' : 'forks'} yet
          </div>
        ) : (
          filteredForks.map((fork) => {
            const statusColor = getStatusColor(fork.status);
            const timeText =
              fork.status === 'open'
                ? formatTimeRemaining(fork.lockedAt, fork.status)
                : fork.status === 'locked' || fork.status === 'executing'
                ? formatTimeRemaining(fork.settledAt, fork.status)
                : fork.status === 'settled'
                ? formatTimeRemaining(fork.settledAt, fork.status)
                : '';

            return (
              <div
                key={fork.id}
                onClick={() => handleForkClick(fork.id)}
                className={`bg-terminal-panel border border-terminal-border rounded p-3 cursor-pointer transition hover:border-terminal-border ${
                  onForkClick ? 'hover:border-echelon-cyan/50' : ''
                }`}
              >
                {/* Header Row */}
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <span
                      className="px-2 py-0.5 rounded text-xs font-semibold uppercase whitespace-nowrap"
                      style={{
                        backgroundColor: `${statusColor}20`,
                        color: statusColor,
                        border: `1px solid ${statusColor}`,
                      }}
                    >
                      {fork.status}
                    </span>
                    <span className="text-sm text-terminal-text truncate">
                      {fork.question.length > 60
                        ? `${fork.question.substring(0, 60)}...`
                        : fork.question}
                    </span>
                  </div>
                  {timeText && (
                    <span className="text-xs text-terminal-text-muted whitespace-nowrap">
                      {timeText}
                    </span>
                  )}
                </div>

                {/* Options Section */}
                <div className="space-y-2">
                  {fork.options.map((option) => (
                    <div
                      key={option.id}
                      className="flex items-center gap-3 bg-terminal-panel rounded p-2"
                    >
                      <span className="text-xs text-terminal-text flex-1 min-w-0">
                        {option.label}
                      </span>
                      <span
                        className="px-2 py-0.5 rounded text-xs font-mono"
                        style={{
                          backgroundColor: `${statusColor}20`,
                          color: statusColor,
                        }}
                      >
                        {(option.price * 100).toFixed(1)}%
                      </span>
                      <ForkOptionSparkline priceHistory={option.priceHistory} />
                    </div>
                  ))}
                </div>

                {/* Replay Button */}
                <div className="mt-3 pt-3 border-t border-terminal-border">
                  <button
                    onClick={(e) => handleReplayClick(e, fork.id)}
                    className="flex items-center gap-2 px-3 py-1.5 w-full bg-terminal-bg border border-terminal-border rounded text-xs font-medium text-terminal-text hover:border-echelon-cyan hover:text-echelon-cyan transition-colors"
                  >
                    <Play className="w-3 h-3" />
                    REPLAY
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Replay Drawer */}
      <ReplayDrawer
        open={replayOpen}
        onClose={handleCloseReplay}
        pointer={replayPointer}
      />
    </div>
  );
}
