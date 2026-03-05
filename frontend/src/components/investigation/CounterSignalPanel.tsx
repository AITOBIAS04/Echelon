/**
 * Counter-Signal Panel
 *
 * Displays counter-signals with signal class badges,
 * material indicators, and summary statistics.
 */

import type { CounterSignal } from '../../types/investigation';

const SIGNAL_CLASS_COLORS: Record<string, string> = {
  official_denial: 'bg-red-500/20 text-red-400',
  regulatory_clearance: 'bg-emerald-500/20 text-emerald-400',
  filing_contradiction: 'bg-orange-500/20 text-orange-400',
  competing_analysis: 'bg-amber-500/20 text-amber-400',
  timeline_inconsistency: 'bg-purple-500/20 text-purple-400',
  source_reliability_degradation: 'bg-pink-500/20 text-pink-400',
  entity_status_change: 'bg-blue-500/20 text-blue-400',
  jurisdictional_conflict: 'bg-amber-500/20 text-amber-300',
  retraction_or_correction: 'bg-red-500/20 text-red-300',
  market_divergence: 'bg-yellow-500/20 text-yellow-400',
  witness_source_recantation: 'bg-violet-500/20 text-violet-400',
};

function SignalCard({ signal }: { signal: CounterSignal }) {
  const classColor = SIGNAL_CLASS_COLORS[signal.signal_class] ?? 'bg-zinc-500/20 text-zinc-400';

  return (
    <div className={`bg-terminal-surface rounded-lg p-3 border ${
      signal.material ? 'border-red-500/30' : 'border-terminal-border'
    }`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-terminal-text">
            {signal.counter_signal_id}
          </span>
          <span className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase ${classColor}`}>
            {signal.signal_class}
          </span>
          {signal.material && (
            <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-red-500/20 text-red-400">
              MATERIAL
            </span>
          )}
        </div>
        <span className="text-[10px] text-terminal-text-muted whitespace-nowrap">
          {new Date(signal.detected_at).toLocaleString()}
        </span>
      </div>

      {signal.resolution_impact && (
        <p className="mt-2 text-xs text-terminal-text">{signal.resolution_impact}</p>
      )}

      <div className="mt-2 flex gap-3 text-[10px] text-terminal-text-muted">
        <span>Method: {signal.detection_method}</span>
        {signal.evidence_ref && (
          <span className="font-mono text-echelon-cyan">{signal.evidence_ref}</span>
        )}
      </div>
    </div>
  );
}

export function CounterSignalPanel({
  signals,
  summary,
}: {
  signals: CounterSignal[];
  summary: Record<string, number>;
}) {
  if (signals.length === 0) {
    return (
      <div className="text-terminal-text-muted text-xs p-4">
        No counter-signals detected.
      </div>
    );
  }

  const materialCount = signals.filter((s) => s.material).length;

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="bg-terminal-surface rounded-lg p-3 border border-terminal-border">
        <div className="flex gap-4 text-xs">
          <div>
            <span className="text-terminal-text-muted">Total: </span>
            <span className="font-mono text-terminal-text">{signals.length}</span>
          </div>
          <div>
            <span className="text-terminal-text-muted">Material: </span>
            <span className={`font-mono ${materialCount > 0 ? 'text-red-400' : 'text-terminal-text'}`}>
              {materialCount}
            </span>
          </div>
        </div>
        {Object.keys(summary).length > 0 && (
          <div className="mt-2 flex gap-2 flex-wrap">
            {Object.entries(summary).map(([key, count]) => (
              <span key={key} className="text-[10px] text-terminal-text-muted">
                {key}: {count}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Signal cards */}
      <div className="space-y-2">
        {signals.map((signal) => (
          <SignalCard key={signal.counter_signal_id} signal={signal} />
        ))}
      </div>
    </div>
  );
}
