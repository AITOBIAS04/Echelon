import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { listTapeEvents } from '../../api/liveTape';
import type { TapeEvent } from '../../types/liveTape';
import { GitBranch, Zap, Shield, AlertTriangle, FileText, TrendingUp } from 'lucide-react';

/**
 * LiveRibbon Component
 *
 * Horizontal ribbon displaying recent live events beneath the header.
 * Shows agent, event type, timeline, delta, and time-ago in compact pills.
 */
export function LiveRibbon() {
  const navigate = useNavigate();

  const { data: events, isLoading } = useQuery({
    queryKey: ['liveTapeEvents', 'ribbon'],
    queryFn: () => listTapeEvents(),
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  const formatTimeAgo = (timestamp: string): string => {
    const now = Date.now();
    const then = new Date(timestamp).getTime();
    const diffMs = now - then;
    const diffMins = Math.floor(diffMs / 60000);
    const diffSecs = Math.floor(diffMs / 1000);

    if (diffSecs < 10) return 'now';
    if (diffSecs < 60) return `${diffSecs}s`;
    if (diffMins < 60) return `${diffMins}m`;
    const diffHours = Math.floor(diffMins / 60);
    return `${diffHours}h`;
  };

  const getEventIcon = (type: TapeEvent['type']) => {
    switch (type) {
      case 'wing_flap':
        return GitBranch;
      case 'fork_live':
        return GitBranch;
      case 'sabotage_disclosed':
        return Shield;
      case 'paradox_spawn':
        return Zap;
      case 'evidence_flip':
        return AlertTriangle;
      case 'settlement':
        return FileText;
      default:
        return TrendingUp;
    }
  };

  const getEventColor = (type: TapeEvent['type']): string => {
    switch (type) {
      case 'wing_flap':
        return '#3B82F6';
      case 'fork_live':
        return '#4ADE80';
      case 'sabotage_disclosed':
        return '#FACC15';
      case 'paradox_spawn':
        return '#FB7185';
      case 'evidence_flip':
        return '#4ADE80';
      case 'settlement':
        return '#8B5CF6';
      default:
        return '#3B82F6';
    }
  };

  const formatDelta = (impact?: TapeEvent['impact']): string | null => {
    if (!impact) return null;
    if (impact.stabilityDelta !== undefined) {
      const sign = impact.stabilityDelta >= 0 ? '+' : '';
      return `${sign}${impact.stabilityDelta.toFixed(1)}%`;
    }
    if (impact.logicGapDelta !== undefined) {
      const sign = impact.logicGapDelta >= 0 ? '+' : '';
      return `${sign}${impact.logicGapDelta.toFixed(1)}%`;
    }
    if (impact.priceDelta !== undefined) {
      const sign = impact.priceDelta >= 0 ? '+' : '';
      return `${sign}${impact.priceDelta.toFixed(2)}`;
    }
    return null;
  };

  const handleEventClick = (event: TapeEvent) => {
    if (event.timelineId) {
      navigate(`/timeline/${event.timelineId}`);
    } else if (event.replayPointer) {
      navigate(`/blackbox?tab=live_tape&replay=${event.replayPointer.forkId}`);
    } else {
      navigate(`/blackbox?tab=live_tape&event=${event.id}`);
    }
  };

  if (isLoading) {
    return (
      <div className="flex-shrink-0 border-b border-slate-700/50 py-2 px-4 relative z-20">
        <div className="flex items-center gap-2 overflow-x-auto scrollbar-hide">
          <div className="text-xs text-slate-500 animate-pulse">Loading events...</div>
        </div>
      </div>
    );
  }

  const recentEvents = (events ?? []).slice(0, 15); // Show last 15 events

  if (recentEvents.length === 0) {
    return null;
  }

  return (
    <div className="flex-shrink-0 border-b border-slate-700/50 py-2 px-4 relative z-20 bg-slate-950">
      <div className="flex items-center gap-2 overflow-x-auto scrollbar-hide">
        {recentEvents.map((event) => {
          const Icon = getEventIcon(event.type);
          const color = getEventColor(event.type);
          const delta = formatDelta(event.impact);
          const timeAgo = formatTimeAgo(event.ts);

          return (
            <button
              key={event.id}
              onClick={() => handleEventClick(event)}
              className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-900/50 border border-slate-700/50 rounded hover:border-slate-600/50 hover:bg-slate-800/50 transition-all flex-shrink-0 group"
            >
              {/* Event Icon */}
              <Icon className="w-3 h-3 flex-shrink-0" style={{ color }} />

              {/* Agent */}
              {event.agentName && (
                <span className="text-[10px] font-mono text-slate-400 group-hover:text-emerald-400 transition">
                  {event.agentName}
                </span>
              )}

              {/* Event Type */}
              <span className="text-[10px] font-semibold uppercase" style={{ color }}>
                {event.type.replace(/_/g, ' ')}
              </span>

              {/* Timeline */}
              {event.timelineTitle && (
                <span className="text-[10px] text-slate-500 truncate max-w-[80px]">
                  {event.timelineTitle}
                </span>
              )}

              {/* Delta */}
              {delta && (
                <span className="text-[10px] font-mono text-emerald-400">
                  {delta}
                </span>
              )}

              {/* Time Ago */}
              <span className="text-[10px] text-slate-600 font-mono">
                {timeAgo}
              </span>
            </button>
          );
        })}
      </div>

      <style>{`
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
        .scrollbar-hide {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>
    </div>
  );
}
