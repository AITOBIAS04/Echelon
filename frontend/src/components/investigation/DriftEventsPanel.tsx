/**
 * Drift Events Panel
 *
 * Displays commitment drift events with type badges,
 * original/new values, and material drift indicator.
 */

import type { DriftEvent } from '../../types/investigation';

const IMPACT_COLORS: Record<string, string> = {
  MATERIAL: 'bg-red-500/20 text-red-400',
  NOTABLE: 'bg-amber-500/20 text-amber-400',
  MINOR: 'bg-zinc-500/20 text-zinc-400',
  material: 'bg-red-500/20 text-red-400',
  notable: 'bg-amber-500/20 text-amber-400',
  minor: 'bg-zinc-500/20 text-zinc-400',
};

function DriftEventCard({ event }: { event: DriftEvent }) {
  const impactColor = IMPACT_COLORS[event.impact_assessment] ?? 'bg-zinc-500/20 text-zinc-400';

  return (
    <div className="bg-terminal-surface rounded-lg p-3 border border-terminal-border">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-terminal-text">{event.drift_id}</span>
          <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-blue-500/20 text-blue-400">
            {event.drift_type}
          </span>
          <span className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase ${impactColor}`}>
            {event.impact_assessment}
          </span>
        </div>
        <span className="text-[10px] text-terminal-text-muted whitespace-nowrap">
          {new Date(event.detected_at).toLocaleString()}
        </span>
      </div>

      <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
        <div>
          <span className="text-terminal-text-muted">Original: </span>
          <span className="font-mono text-terminal-text">{event.original_value}</span>
        </div>
        <div>
          <span className="text-terminal-text-muted">New: </span>
          <span className="font-mono text-terminal-text">{event.new_value}</span>
        </div>
      </div>

      {event.evidence_ref && (
        <div className="mt-1 text-[10px] text-terminal-text-muted">
          Ref: <span className="font-mono text-echelon-cyan">{event.evidence_ref}</span>
        </div>
      )}
    </div>
  );
}

export function DriftEventsPanel({
  events,
  hasMaterialDrift,
}: {
  events: DriftEvent[];
  hasMaterialDrift: boolean;
}) {
  if (events.length === 0) {
    return (
      <div className="text-terminal-text-muted text-xs p-4">
        No drift events detected.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Material drift indicator */}
      {hasMaterialDrift && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-xs text-red-400">
          Material drift detected — investigation integrity may be affected.
        </div>
      )}

      {/* Drift events */}
      <div className="space-y-2">
        {events.map((event) => (
          <DriftEventCard key={event.drift_id} event={event} />
        ))}
      </div>
    </div>
  );
}
