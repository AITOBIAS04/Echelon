import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { ExternalLink, Play, Plus, Check, ChevronDown } from 'lucide-react';
import { listTapeEvents } from '../../api/liveTape';
import { toggleTrack, isTracked } from '../../lib/tracking';
import { ReplayDrawer } from '../replay/ReplayDrawer';
import type { TapeEvent, TapeEventType } from '../../types/liveTape';
import type { ReplayPointer } from '../../types/replay';
import { clsx } from 'clsx';

/**
 * Get event type badge color and label
 */
function getEventTypeBadge(type: TapeEventType): { bg: string; text: string; label: string } {
  switch (type) {
    case 'wing_flap':
      return { bg: '#3B82F6', text: '#FFFFFF', label: 'WING FLAP' };
    case 'fork_live':
      return { bg: '#4ADE80', text: '#FFFFFF', label: 'FORK LIVE' };
    case 'sabotage_disclosed':
      return { bg: '#FB7185', text: '#FFFFFF', label: 'SABOTAGE' };
    case 'paradox_spawn':
      return { bg: '#FACC15', text: '#FFFFFF', label: 'PARADOX' };
    case 'evidence_flip':
      return { bg: '#4ADE80', text: '#FFFFFF', label: 'EVIDENCE' };
    case 'settlement':
      return { bg: '#8B5CF6', text: '#FFFFFF', label: 'SETTLE' };
  }
}

/**
 * Format timestamp to relative time or HH:MM:SS
 */
function formatTimestamp(ts: string): string {
  const now = new Date().getTime();
  const eventTime = new Date(ts).getTime();
  const diffMs = now - eventTime;
  const diffSeconds = Math.floor(diffMs / 1000);

  // If less than 1 hour, show relative time
  if (diffSeconds < 3600) {
    if (diffSeconds < 60) {
      return `${diffSeconds}s ago`;
    }
    const minutes = Math.floor(diffSeconds / 60);
    return `${minutes}m ago`;
  }

  // Otherwise show HH:MM:SS
  const date = new Date(ts);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });
}

/**
 * Format impact value
 */
function formatImpact(value: number, prefix: string = ''): string {
  const sign = value >= 0 ? '+' : '';
  return `${prefix}${sign}${value.toFixed(2)}`;
}

/**
 * LiveTape Component
 *
 * Displays live tape events with filtering and actions.
 */
export function LiveTape() {
  const navigate = useNavigate();
  const [events, setEvents] = useState<TapeEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<TapeEventType | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isTypeDropdownOpen, setIsTypeDropdownOpen] = useState(false);
  const [replayOpen, setReplayOpen] = useState(false);
  const [replayPointer, setReplayPointer] = useState<ReplayPointer | null>(null);
  const [trackedStates, setTrackedStates] = useState<Record<string, boolean>>({});

  // Fetch events
  useEffect(() => {
    const fetchEvents = async () => {
      try {
        setLoading(true);
        setError(null);
        const params: { type?: TapeEventType } = {};
        if (selectedType !== 'all') {
          params.type = selectedType;
        }
        const data = await listTapeEvents(params);
        setEvents(data);

        // Initialize tracked states
        const states: Record<string, boolean> = {};
        data.forEach((event) => {
          if (event.timelineId) {
            states[event.timelineId] = isTracked(event.timelineId);
          }
        });
        setTrackedStates(states);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to fetch tape events';
        setError(errorMessage);
        setEvents([]);
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();

    // Refresh every 20 seconds
    const interval = setInterval(fetchEvents, 20000);
    return () => clearInterval(interval);
  }, [selectedType]);

  // Filter events by search query
  const filteredEvents = useMemo(() => {
    if (!searchQuery.trim()) return events;

    const query = searchQuery.toLowerCase();
    return events.filter((event) => {
      if (event.timelineTitle?.toLowerCase().includes(query)) return true;
      if (event.agentName?.toLowerCase().includes(query)) return true;
      if (event.wallet?.toLowerCase().includes(query)) return true;
      if (event.summary.toLowerCase().includes(query)) return true;
      return false;
    });
  }, [events, searchQuery]);

  const handleOpenTimeline = (timelineId: string) => {
    navigate(`/timeline/${timelineId}`);
  };

  const handleReplay = (pointer: ReplayPointer) => {
    setReplayPointer(pointer);
    setReplayOpen(true);
  };

  const handleTrack = (timelineId: string) => {
    const newTrackedState = toggleTrack(timelineId);
    setTrackedStates((prev) => ({
      ...prev,
      [timelineId]: newTrackedState,
    }));
  };

  const handleCloseReplay = () => {
    setReplayOpen(false);
    setReplayPointer(null);
  };

  const eventTypes: Array<{ value: TapeEventType | 'all'; label: string }> = [
    { value: 'all', label: 'ALL EVENTS' },
    { value: 'wing_flap', label: 'WING FLAP' },
    { value: 'fork_live', label: 'FORK LIVE' },
    { value: 'sabotage_disclosed', label: 'SABOTAGE' },
    { value: 'paradox_spawn', label: 'PARADOX' },
    { value: 'evidence_flip', label: 'EVIDENCE' },
    { value: 'settlement', label: 'SETTLEMENT' },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <span className="text-emerald-400 animate-pulse">SCANNING TAPE...</span>
      </div>
    );
  }

  if (error) {
return (
      <div className="flex flex-col items-center justify-center h-64">
        <span className="text-red-400 mb-2">ERROR: {error}</span>
        <span className="text-slate-400 text-sm">Failed to load tape events</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        {/* Event Type Dropdown */}
        <div className="relative">
          <button
            onClick={() => setIsTypeDropdownOpen(!isTypeDropdownOpen)}
            className="flex items-center gap-2 px-3 py-2 text-xs bg-slate-900/50 border border-slate-700/50 rounded text-slate-300 hover:text-blue-400 transition min-w-[160px]"
          >
            <span>{eventTypes.find((t) => t.value === selectedType)?.label || 'ALL EVENTS'}</span>
            <ChevronDown className={`w-3 h-3 transition ${isTypeDropdownOpen ? 'rotate-180' : ''}`} />
          </button>
          {isTypeDropdownOpen && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setIsTypeDropdownOpen(false)}
              />
              <div className="absolute top-full left-0 mt-1 bg-slate-800 border border-slate-700 rounded shadow-lg z-20 min-w-[160px]">
                {eventTypes.map((type) => (
                  <button
                    key={type.value}
                    onClick={() => {
                      setSelectedType(type.value);
                      setIsTypeDropdownOpen(false);
                    }}
                    className={clsx(
                      'w-full text-left px-3 py-2 text-xs hover:bg-slate-700 transition',
                      selectedType === type.value ? 'text-blue-400' : 'text-slate-400'
                    )}
                  >
                    {type.label}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>

        {/* Search Input */}
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search timeline, agent, wallet..."
          className="flex-1 px-3 py-2 text-xs bg-slate-900/50 border border-slate-700/50 rounded text-slate-300 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:text-blue-400"
        />
      </div>

      {/* Events Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs font-mono">
          <thead>
            <tr className="border-b border-slate-700/50 text-slate-500">
              <th className="text-left p-2">TIME</th>
              <th className="text-left p-2">TYPE</th>
              <th className="text-left p-2">TIMELINE</th>
              <th className="text-left p-2">AGENT/WALLET</th>
              <th className="text-left p-2">SUMMARY</th>
              <th className="text-left p-2">IMPACT</th>
              <th className="text-right p-2">ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            {filteredEvents.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center py-8 text-slate-400">
                  No events found
                </td>
              </tr>
            ) : (
              filteredEvents.map((event) => {
                const typeBadge = getEventTypeBadge(event.type);
                const tracked = event.timelineId ? trackedStates[event.timelineId] || false : false;

                return (
                  <tr
                    key={event.id}
                    className="border-b border-slate-700/50 hover:bg-slate-800/30 transition"
                  >
                    <td className="p-2 text-slate-500">{formatTimestamp(event.ts)}</td>
                    <td className="p-2">
                      <span
                        className="px-2 py-0.5 rounded text-[10px] font-bold"
                        style={{
                          backgroundColor: typeBadge.bg,
                          color: typeBadge.text,
                        }}
                      >
                        {typeBadge.label}
                      </span>
                    </td>
                    <td className="p-2 text-slate-300">
                      {event.timelineTitle || event.timelineId || '-'}
                    </td>
                    <td className="p-2 text-slate-300">
                      {event.agentName || event.wallet?.slice(0, 8) + '...' || '-'}
                    </td>
                    <td className="p-2 text-slate-400 max-w-md truncate">{event.summary}</td>
                    <td className="p-2">
                      <div className="flex items-center gap-1 flex-wrap">
                        {event.impact?.stabilityDelta !== undefined && (
                          <span className="px-1.5 py-0.5 bg-slate-800/50 rounded text-[10px]">
                            S{formatImpact(event.impact.stabilityDelta)}
                          </span>
                        )}
                        {event.impact?.logicGapDelta !== undefined && (
                          <span className="px-1.5 py-0.5 bg-slate-800/50 rounded text-[10px]">
                            L{formatImpact(event.impact.logicGapDelta)}
                          </span>
                        )}
                        {event.impact?.priceDelta !== undefined && (
                          <span className="px-1.5 py-0.5 bg-slate-800/50 rounded text-[10px]">
                            P{formatImpact(event.impact.priceDelta, '$')}
                          </span>
                        )}
                        {!event.impact && <span className="text-slate-600">-</span>}
                      </div>
                    </td>
                    <td className="p-2">
                      <div className="flex items-center justify-end gap-1">
                        {event.timelineId && (
                          <button
                            onClick={() => handleOpenTimeline(event.timelineId!)}
                            className="px-2 py-1 bg-slate-800/50 border border-slate-700/50 rounded hover:border-blue-500 hover:text-blue-400 transition text-[10px]"
                            title="Open timeline"
                          >
                            <ExternalLink className="w-3 h-3" />
                          </button>
                        )}
                        {event.replayPointer && (
                          <button
                            onClick={() => handleReplay(event.replayPointer!)}
                            className="px-2 py-1 bg-slate-800/50 border border-slate-700/50 rounded hover:border-blue-500 hover:text-blue-400 transition text-[10px]"
                            title="View replay"
                          >
                            <Play className="w-3 h-3" />
                          </button>
                        )}
                        {event.timelineId && (
                          <button
                            onClick={() => handleTrack(event.timelineId!)}
                            className={clsx(
                              'px-2 py-1 border rounded transition text-[10px] flex items-center gap-1',
                              tracked
                                ? 'bg-emerald-500/20 border-emerald-500 text-emerald-400'
                                : 'bg-slate-800/50 border-slate-700/50 hover:border-emerald-500 hover:text-emerald-400'
                            )}
                            title={tracked ? 'Untrack timeline' : 'Track timeline'}
                          >
                            {tracked ? <Check className="w-3 h-3" /> : <Plus className="w-3 h-3" />}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
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

export default LiveTape;
