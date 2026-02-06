import { useMemo } from 'react';
import { Shield, Crosshair } from 'lucide-react';
import type { SabotageEvent } from '../../types/timeline-detail';

/**
 * SabotageHistoryPanel Props
 */
export interface SabotageHistoryPanelProps {
  /** Array of sabotage events */
  events: SabotageEvent[];
}

/**
 * Get phase badge color
 */
function getPhaseColor(phase: SabotageEvent['phase']): string {
  switch (phase) {
    case 'disclosed':
      return '#FF9500'; // amber
    case 'committed':
      return '#FF6B00'; // orange
    case 'executed':
      return '#FF3B3B'; // red
    case 'slashed':
      return '#00FF41'; // green
    default:
      return '#666666';
  }
}

/**
 * Format timestamp to relative time
 */
function formatRelativeTime(timestamp: string): string {
  const now = new Date().getTime();
  const eventTime = new Date(timestamp).getTime();
  const diffMs = now - eventTime;
  const diffSeconds = Math.floor(diffMs / 1000);

  if (diffSeconds < 60) {
    return `${diffSeconds}s ago`;
  }
  const diffMinutes = Math.floor(diffSeconds / 60);
  if (diffMinutes < 60) {
    return `${diffMinutes}m ago`;
  }
  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) {
    return `${diffHours}h ago`;
  }
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

/**
 * Check if event is recent (within last 5 minutes)
 */
function isRecentEvent(timestamp: string): boolean {
  const now = new Date().getTime();
  const eventTime = new Date(timestamp).getTime();
  const diffMs = now - eventTime;
  return diffMs < 5 * 60 * 1000; // 5 minutes
}

/**
 * SabotageHistoryPanel Component
 * 
 * Displays a vertical timeline of sabotage events with phase-based styling.
 */
export function SabotageHistoryPanel({ events }: SabotageHistoryPanelProps) {
  // Sort events by timestamp (most recent first)
  const sortedEvents = useMemo(() => {
    return [...events].sort((a, b) => {
      const timeA = new Date(a.timestamp).getTime();
      const timeB = new Date(b.timestamp).getTime();
      return timeB - timeA; // Descending order
    });
  }, [events]);

  if (sortedEvents.length === 0) {
    return (
      <div className="bg-slate-900 rounded-lg p-4 border border-[#1A1A1A]">
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <Shield className="w-12 h-12 text-terminal-text-muted mb-3 opacity-50" />
          <p className="text-sm text-terminal-text-muted">No sabotage activity</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 rounded-lg p-4 border border-[#1A1A1A]">
      <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide mb-4">
        Sabotage History
      </h3>
      
      <div className="relative max-h-[300px] overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
        {/* Connecting line */}
        <div
          className="absolute left-[18px] top-0 bottom-0 w-0.5"
          style={{ backgroundColor: '#1A1A1A' }}
        />
        
        {/* Events */}
        <div className="relative space-y-4">
          {sortedEvents.map((event, index) => {
            const phaseColor = getPhaseColor(event.phase);
            const isRecent = isRecentEvent(event.timestamp);
            const isLast = index === sortedEvents.length - 1;

            return (
              <div key={event.id} className="relative flex gap-4">
                {/* Timeline dot and line */}
                <div className="flex flex-col items-center pt-1">
                  <div
                    className={`w-3 h-3 rounded-full border-2 border-[#111111] ${
                      isRecent ? 'animate-pulse' : ''
                    }`}
                    style={{
                      backgroundColor: phaseColor,
                      boxShadow: isRecent ? `0 0 8px ${phaseColor}` : 'none',
                    }}
                  />
                  {!isLast && (
                    <div
                      className="w-0.5 flex-1 mt-1"
                      style={{ backgroundColor: '#1A1A1A' }}
                    />
                  )}
                </div>

                {/* Event card */}
                <div className="flex-1 bg-terminal-panel rounded p-3 border border-[#1A1A1A]">
                  {/* Phase badge and timestamp */}
                  <div className="flex items-center justify-between mb-2">
                    <span
                      className="px-2 py-0.5 rounded text-xs font-semibold uppercase"
                      style={{
                        backgroundColor: `${phaseColor}20`,
                        color: phaseColor,
                        border: `1px solid ${phaseColor}`,
                      }}
                    >
                      {event.phase}
                    </span>
                    <span className="text-xs text-terminal-text-muted">
                      {formatRelativeTime(event.timestamp)}
                    </span>
                  </div>

                  {/* Event content based on phase */}
                  <div className="space-y-1 text-sm">
                    {event.phase === 'disclosed' && (
                      <>
                        <div className="flex items-center gap-2 text-terminal-text">
                          <Crosshair className="w-4 h-4 text-[#FF9500]" />
                          <span>
                            <span className="font-medium">{event.saboteurName}</span> preparing{' '}
                            <span className="font-medium">'{event.sabotageType}'</span> attack
                          </span>
                        </div>
                        <div className="text-terminal-text-muted text-xs ml-6">
                          Stake: <span className="text-terminal-text">${event.stakeAmount.toFixed(2)}</span> | Est.
                          Effect: <span className="text-red-500">-{Math.abs(event.effectSize).toFixed(1)}%</span> stability
                        </div>
                      </>
                    )}

                    {event.phase === 'committed' && (
                      <>
                        <div className="flex items-center gap-2 text-terminal-text">
                          <Crosshair className="w-4 h-4 text-[#FF6B00]" />
                          <span>
                            <span className="font-medium">{event.saboteurName}</span> committed to attack
                          </span>
                        </div>
                        <div className="text-terminal-text-muted text-xs ml-6">
                          Execution window: 30-60s
                        </div>
                      </>
                    )}

                    {event.phase === 'executed' && (
                      <>
                        <div className="flex items-center gap-2 text-terminal-text">
                          <Crosshair className="w-4 h-4 text-[#FF3B3B]" />
                          <span>Attack landed. Stability impact:{' '}
                            <span className="text-red-500 font-medium">
                              -{Math.abs(event.effectSize).toFixed(1)}%
                            </span>
                          </span>
                        </div>
                        {event.executedAt && (
                          <div className="text-terminal-text-muted text-xs ml-6">
                            Executed at: {new Date(event.executedAt).toLocaleTimeString()}
                          </div>
                        )}
                      </>
                    )}

                    {event.phase === 'slashed' && (
                      <>
                        <div className="flex items-center gap-2 text-terminal-text">
                          <Shield className="w-4 h-4 text-[#00FF41]" />
                          <span>Timeline recovered. Stake slashed.</span>
                        </div>
                        <div className="text-terminal-text-muted text-xs ml-6">
                          Burned:{' '}
                          <span className="text-green-500 font-medium">
                            ${(event.stakeAmount * 0.5).toFixed(2)}
                          </span>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
