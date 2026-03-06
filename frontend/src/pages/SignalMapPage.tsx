/**
 * SignalMapPage — OSINT signals + convergence heatmap.
 *
 * Uses QUIET_MONITORING when no signals, SPARSE_DATA when < 3 signals.
 */

import { Radio } from 'lucide-react';
import { useSignalMap } from '../hooks/useSignalMap';
import { EmptyState } from '../components/empty-states/EmptyState';

export function SignalMapPage() {
  const { signals, totalSignals, heatmap, isLoading, error, isSparse, isQuiet } =
    useSignalMap();

  if (error) {
    return (
      <div className="p-6 text-status-danger text-sm">
        Failed to load signal map: {error.message}
      </div>
    );
  }

  if (isQuiet && !isLoading) {
    return (
      <EmptyState
        type="QUIET_MONITORING"
        description="No active signals detected. Monitoring OSINT sources for relevant events."
        context={
          <div className="w-full h-full p-8">
            {/* Skeleton graph */}
            <div className="flex items-end justify-center gap-3 h-48">
              {Array.from({ length: 12 }).map((_, i) => (
                <div
                  key={i}
                  className="w-6 bg-terminal-panel border border-terminal-border rounded-t"
                  style={{ height: `${20 + Math.random() * 60}%` }}
                />
              ))}
            </div>
          </div>
        }
      />
    );
  }

  if (isSparse && !isLoading) {
    return (
      <div className="p-6">
        <EmptyState
          type="SPARSE_DATA"
          description={`Only ${signals.length} signal${signals.length === 1 ? '' : 's'} detected so far. The map becomes more useful as more signals flow in from connected sources.`}
        />
        {/* Still show the few signals we have */}
        <div className="mt-6 space-y-2">
          {signals.map((sig) => (
            <SignalRow key={sig.id} signal={sig} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Signal count header */}
      <div className="flex items-center gap-3">
        <Radio className="w-5 h-5 text-status-info" />
        <span className="text-sm font-bold text-terminal-text">
          {totalSignals} Signals Detected
        </span>
      </div>

      {/* Heatmap */}
      {heatmap.length > 0 && (
        <div>
          <h2 className="text-sm font-bold text-terminal-text mb-3">Convergence Heatmap</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-3">
            {heatmap.map((cell) => (
              <div
                key={cell.timeline_id}
                className="bg-terminal-surface border border-terminal-border rounded-lg p-3"
              >
                <div className="text-xs font-semibold text-terminal-text truncate mb-1">
                  {cell.timeline_name}
                </div>
                <div className="flex items-center gap-3 text-[11px]">
                  <span className="text-terminal-text-muted">
                    {cell.signal_count} signals
                  </span>
                  <span className="font-mono text-terminal-text-secondary">
                    conv: {(cell.convergence_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Signals list */}
      <div>
        <h2 className="text-sm font-bold text-terminal-text mb-3">Signal Feed</h2>
        <div className="space-y-2">
          {signals.map((sig) => (
            <SignalRow key={sig.id} signal={sig} />
          ))}
        </div>
      </div>
    </div>
  );
}

function SignalRow({ signal }: { signal: { id: string; source: string; headline: string; relevance_score: number; detected_at: string } }) {
  return (
    <div className="flex items-center gap-3 px-3 py-2 bg-terminal-surface border border-terminal-border rounded text-xs">
      <span className="font-mono text-terminal-text-muted w-16 flex-shrink-0 truncate">
        {signal.source}
      </span>
      <span className="text-terminal-text truncate flex-1">{signal.headline}</span>
      <span className="font-mono text-terminal-text-muted flex-shrink-0">
        {(signal.relevance_score * 100).toFixed(0)}%
      </span>
    </div>
  );
}
