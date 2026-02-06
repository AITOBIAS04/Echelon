import { useState, useEffect } from 'react';
import { X, AlertTriangle, FileText } from 'lucide-react';
import { getForkReplay } from '../../api/replay';
import type { ForkReplay, ReplayPointer, DisclosureEvent } from '../../types/replay';

/**
 * ReplayDrawer Props
 */
export interface ReplayDrawerProps {
  /** Whether the drawer is open */
  open: boolean;
  /** Callback when drawer should close */
  onClose: () => void;
  /** Replay pointer (null when no replay selected) */
  pointer: ReplayPointer | null;
}

/**
 * Get fork status based on timestamps
 */
function getForkStatus(replay: ForkReplay): {
  status: 'open' | 'locked' | 'executed' | 'settled';
  label: string;
  color: string;
} {
  if (replay.settledAt) {
    return {
      status: 'settled',
      label: 'Settled',
      color: '#00FF41', // green
    };
  }
  if (replay.executedAt) {
    return {
      status: 'executed',
      label: 'Executed',
      color: '#9932CC', // purple
    };
  }
  if (replay.lockedAt) {
    return {
      status: 'locked',
      label: 'Locked',
      color: '#FF3B3B', // red
    };
  }
  return {
    status: 'open',
    label: 'Open',
    color: '#22D3EE', // cyan
  };
}

/**
 * Format timestamp to relative time
 */
function formatRelativeTime(timestamp: string, openedAt: string): string {
  const opened = new Date(openedAt).getTime();
  const event = new Date(timestamp).getTime();
  const diffMs = event - opened;
  const diffMins = Math.floor(diffMs / (1000 * 60));
  
  if (diffMins < 1) {
    return 'Just now';
  }
  if (diffMins < 60) {
    return `${diffMins}m`;
  }
  const hours = Math.floor(diffMins / 60);
  return `${hours}h`;
}

/**
 * Get disclosure event icon and color
 */
function getDisclosureEventStyle(
  type: DisclosureEvent['type']
): { icon: typeof AlertTriangle; color: string } {
  switch (type) {
    case 'sabotage_disclosed':
      return { icon: AlertTriangle, color: '#FF3B3B' }; // red
    case 'paradox_spawn':
      return { icon: AlertTriangle, color: '#FF9500' }; // amber
    case 'evidence_flip':
      return { icon: FileText, color: '#22D3EE' }; // cyan
  }
}

/**
 * Price Path Sparkline Component
 * 
 * Renders a simple SVG line chart for price path visualization.
 */
function PriceSparkline({
  pricePath,
  color = '#22D3EE',
  width = 200,
  height = 40,
}: {
  pricePath: { tMs: number; price: number }[];
  color?: string;
  width?: number;
  height?: number;
}) {
  if (pricePath.length === 0) {
    return (
      <div className="flex items-center justify-center h-10 text-terminal-text-muted text-xs">
        No data
      </div>
    );
  }

  // Normalize price path to SVG coordinates
  const maxT = Math.max(...pricePath.map((p) => p.tMs));
  const minPrice = Math.min(...pricePath.map((p) => p.price));
  const maxPrice = Math.max(...pricePath.map((p) => p.price));
  const priceRange = maxPrice - minPrice || 0.01;

  const padding = 2;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;

  const points = pricePath
    .map((point) => {
      const x = padding + (point.tMs / maxT) * chartWidth;
      const y = padding + chartHeight - ((point.price - minPrice) / priceRange) * chartHeight;
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="overflow-visible">
      <polyline
        points={points}
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
 * ReplayDrawer Component
 * 
 * Right-side drawer for displaying fork replay data with price paths,
 * disclosure events, and outcome information.
 */
export function ReplayDrawer({ open, onClose, pointer }: ReplayDrawerProps) {
  const [replay, setReplay] = useState<ForkReplay | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch replay when drawer opens and pointer is available
  useEffect(() => {
    if (open && pointer) {
      setLoading(true);
      setError(null);
      getForkReplay(pointer)
        .then((data) => {
          setReplay(data);
          setLoading(false);
        })
        .catch((err) => {
          setError(err instanceof Error ? err.message : 'Failed to load replay');
          setLoading(false);
        });
    } else {
      setReplay(null);
      setError(null);
    }
  }, [open, pointer]);

  // Handle ESC key to close drawer
  useEffect(() => {
    if (!open) return;

    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [open, onClose]);

  if (!open) {
    return null;
  }

  const forkStatus = replay ? getForkStatus(replay) : null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/80 z-[200] md:bg-black/60"
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        className={`
          fixed top-0 right-0 bottom-0 z-[210]
          w-full md:w-[420px]
          bg-terminal-overlay border-l border-terminal-border
          flex flex-col
          shadow-xl
          transform transition-transform duration-300 ease-out
          ${open ? 'translate-x-0' : 'translate-x-full'}
        `}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-terminal-border">
          <h2 className="text-lg font-bold text-terminal-text uppercase tracking-wide">
            Fork Replay
          </h2>
          <button
            onClick={onClose}
            className="p-1.5 text-terminal-text-muted hover:text-terminal-text transition-colors"
            aria-label="Close drawer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="text-terminal-text-muted">Loading replay...</div>
            </div>
          )}

          {error && (
            <div className="bg-red-500/20 border border-red-500 rounded-lg p-4">
              <p className="text-sm text-red-500 font-semibold mb-1">Error</p>
              <p className="text-xs text-terminal-text-muted">
                {error === 'Replay not available for this timeline yet'
                  ? 'Replay not available for this timeline yet'
                  : error}
              </p>
            </div>
          )}

          {replay && !loading && (
            <>
              {/* Section 1: Fork Header */}
              <div>
                <h3 className="text-xs font-semibold text-terminal-text-muted uppercase tracking-wide mb-2">
                  Fork Question
                </h3>
                <p className="text-sm text-terminal-text font-medium mb-2">
                  {replay.forkQuestion}
                </p>
                <p className="text-xs text-terminal-text-muted font-mono">
                  Timeline: {replay.timelineId}
                </p>
              </div>

              {/* Section 2: Fork Status */}
              {forkStatus && (
                <div>
                  <h3 className="text-xs font-semibold text-terminal-text-muted uppercase tracking-wide mb-2">
                    Status
                  </h3>
                  <div className="flex items-center gap-2">
                    <span
                      className="px-2 py-1 rounded text-xs font-semibold uppercase"
                      style={{
                        backgroundColor: `${forkStatus.color}20`,
                        color: forkStatus.color,
                        border: `1px solid ${forkStatus.color}`,
                      }}
                    >
                      {forkStatus.label}
                    </span>
                    {replay.openedAt && (
                      <span className="text-xs text-terminal-text-muted">
                        Opened {formatRelativeTime(replay.openedAt, replay.openedAt)}
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Section 3: Price Paths */}
              <div>
                <h3 className="text-xs font-semibold text-terminal-text-muted uppercase tracking-wide mb-3">
                  Price Paths
                </h3>
                <div className="space-y-4">
                  {replay.options.map((option, index) => {
                    const isChosen = option.label === replay.chosenOption;
                    const optionColor = isChosen ? '#00FF41' : '#22D3EE'; // green if chosen, cyan otherwise
                    
                    return (
                      <div
                        key={index}
                        className="bg-terminal-bg rounded border border-terminal-border p-3"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-terminal-text">
                            {option.label}
                            {isChosen && (
                              <span className="ml-2 text-xs text-green-500">✓ Chosen</span>
                            )}
                          </span>
                          {option.pricePath.length > 0 && (
                            <span className="text-xs font-mono text-terminal-text-muted">
                              {(option.pricePath[option.pricePath.length - 1].price * 100).toFixed(1)}%
                            </span>
                          )}
                        </div>
                        <PriceSparkline
                          pricePath={option.pricePath}
                          color={optionColor}
                          width={200}
                          height={40}
                        />
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Section 4: Disclosure Events */}
              {replay.disclosureEvents.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-terminal-text-muted uppercase tracking-wide mb-3">
                    Disclosure Events
                  </h3>
                  <div className="space-y-2">
                    {replay.disclosureEvents.map((event, index) => {
                      const { icon: Icon, color } = getDisclosureEventStyle(event.type);
                      
                      return (
                        <div
                          key={index}
                          className="flex items-start gap-3 bg-terminal-bg rounded border border-terminal-border p-3"
                        >
                          <Icon className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color }} />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <span
                                className="px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase"
                                style={{
                                  backgroundColor: `${color}20`,
                                  color: color,
                                }}
                              >
                                {event.type.replace('_', ' ')}
                              </span>
                              <span className="text-xs text-terminal-text-muted font-mono">
                                +{formatRelativeTime(
                                  new Date(new Date(replay.openedAt).getTime() + event.tMs).toISOString(),
                                  replay.openedAt
                                )}
                              </span>
                            </div>
                            <p className="text-xs text-terminal-text">{event.label}</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Section 5: Decision + Outcome */}
              {(replay.chosenOption || replay.outcomeLabel) && (
                <div>
                  <h3 className="text-xs font-semibold text-terminal-text-muted uppercase tracking-wide mb-3">
                    Outcome
                  </h3>
                  <div className="bg-terminal-bg rounded border border-terminal-border p-4 space-y-2">
                    {replay.chosenOption && (
                      <div>
                        <span className="text-xs text-terminal-text-muted">Chosen Option:</span>
                        <span className="ml-2 text-sm font-semibold text-green-500">
                          {replay.chosenOption}
                        </span>
                      </div>
                    )}
                    {replay.outcomeLabel && (
                      <div>
                        <span className="text-xs text-terminal-text-muted">Outcome:</span>
                        <p className="mt-1 text-sm text-terminal-text">
                          {replay.outcomeLabel}
                        </p>
                      </div>
                    )}
                    {replay.settledAt && (
                      <div className="pt-2 border-t border-terminal-border">
                        <span className="text-xs text-terminal-text-muted">
                          Settled: {new Date(replay.settledAt).toLocaleString()}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Notes */}
              {replay.notes && (
                <div>
                  <h3 className="text-xs font-semibold text-terminal-text-muted uppercase tracking-wide mb-2">
                    Notes
                  </h3>
                  <p className="text-xs text-terminal-text-muted leading-relaxed">
                    {replay.notes}
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}
