import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { listTapeEvents } from '../../api/liveTape';
import type { TapeEvent, TapeEventType } from '../../types/liveTape';

type RibbonEvent = Pick<TapeEvent, 'id' | 'ts' | 'type' | 'summary' | 'timelineId' | 'timelineTitle'>;

function badge(type: TapeEventType): { bg: string; text: string; label: string } {
  switch (type) {
    case 'wing_flap':
      return { bg: '#3B82F6', text: '#FFFFFF', label: 'WING FLAP' };
    case 'fork_live':
      return { bg: '#10B981', text: '#FFFFFF', label: 'FORK' };
    case 'sabotage_disclosed':
      return { bg: '#EF4444', text: '#FFFFFF', label: 'SABOTAGE' };
    case 'paradox_spawn':
      return { bg: '#F59E0B', text: '#FFFFFF', label: 'PARADOX' };
    case 'evidence_flip':
      return { bg: '#10B981', text: '#FFFFFF', label: 'FLIP' };
    case 'settlement':
      return { bg: '#10B981', text: '#FFFFFF', label: 'SETTLE' };
  }
}

function formatAgo(iso: string): string {
  const ms = Date.now() - Date.parse(iso);
  if (Number.isNaN(ms) || ms < 0) return 'now';
  const sec = Math.floor(ms / 1000);
  if (sec < 60) return `${sec}s`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m`;
  const hr = Math.floor(min / 60);
  return `${hr}h`;
}

/**
 * LiveRibbon
 * 
 * A slim, horizontally scrollable tape ribbon for the home page.
 * It is intentionally "terminal-dense" and keeps the Ops Board feeling alive.
 */
export function LiveRibbon({ maxEvents = 18 }: { maxEvents?: number }) {
  const navigate = useNavigate();
  const [events, setEvents] = useState<RibbonEvent[]>([]);

  useEffect(() => {
    let mounted = true;

    const fetchTape = async () => {
      try {
        const data = await listTapeEvents({});
        if (!mounted) return;
        const slim = data
          .slice(0, maxEvents)
          .map((e) => ({
            id: e.id,
            ts: e.ts,
            type: e.type,
            summary: e.summary,
            timelineId: e.timelineId,
            timelineTitle: e.timelineTitle,
          }));
        setEvents(slim);
      } catch {
        // Ribbon should fail silently; the OpsBoard still renders.
        if (mounted) setEvents([]);
      }
    };

    fetchTape();
    const interval = setInterval(fetchTape, 15000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [maxEvents]);

  const items = useMemo(() => {
    return events.map((e) => {
      const b = badge(e.type);
      const title = e.timelineTitle || e.summary;
      return {
        ...e,
        badge: b,
        title,
        ago: formatAgo(e.ts),
      };
    });
  }, [events]);

  if (items.length === 0) return null;

  return (
    <div className="border border-terminal-border/50 bg-terminal-bg/80 rounded-lg px-2 py-1.5">
      <div className="overflow-x-auto scrollbar-hide">
        <div className="flex items-center gap-2 min-w-max">
          {items.map((e) => (
            <button
              key={e.id}
              onClick={() => {
                if (e.timelineId) {
                  navigate(`/timeline/${e.timelineId}`);
                  return;
                }
                navigate('/blackbox?tab=live_tape');
              }}
              className="flex items-center gap-2 px-2 py-1 rounded border border-terminal-border/40 bg-black/20 hover:bg-black/35 hover:border-terminal-border/80 transition flex-shrink-0"
              title={e.summary}
            >
              <span
                className="text-[10px] font-bold px-1.5 py-0.5 rounded"
                style={{ backgroundColor: e.badge.bg, color: e.badge.text }}
              >
                {e.badge.label}
              </span>
              <span className="text-[11px] text-terminal-text truncate max-w-[220px]">{e.title}</span>
              <span className="text-[10px] font-mono text-terminal-muted">{e.ago}</span>
            </button>
          ))}
        </div>
      </div>
      <style>{`
        .scrollbar-hide::-webkit-scrollbar { display: none; }
        .scrollbar-hide { scrollbar-width: none; }
      `}</style>
    </div>
  );
}
