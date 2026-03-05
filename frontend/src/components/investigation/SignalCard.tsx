/**
 * SignalCard — Source-badged counter-signal card.
 * Shows signal class, detection method, materiality, and source badge.
 */

import type { CounterSignal } from '../../types/investigation';

const SIGNAL_CLASS_COLORS: Record<string, string> = {
  official_denial: 'bg-red-500/20 text-red-400',
  regulatory_clearance: 'bg-emerald-500/20 text-emerald-400',
  market_contradiction: 'bg-amber-500/20 text-amber-400',
  source_retraction: 'bg-orange-500/20 text-orange-400',
  temporal_inconsistency: 'bg-purple-500/20 text-purple-400',
  methodology_challenge: 'bg-blue-500/20 text-blue-400',
  data_quality_flag: 'bg-zinc-500/20 text-zinc-400',
  competing_evidence: 'bg-cyan-500/20 text-cyan-400',
  expert_dissent: 'bg-pink-500/20 text-pink-400',
  statistical_anomaly: 'bg-indigo-500/20 text-indigo-400',
  provenance_dispute: 'bg-yellow-500/20 text-yellow-400',
};

interface SignalCardProps {
  signal: CounterSignal;
  onCreateInvestigation?: (signal: CounterSignal) => void;
}

export function SignalCard({ signal, onCreateInvestigation }: SignalCardProps) {
  const classColor = SIGNAL_CLASS_COLORS[signal.signal_class] ?? 'bg-zinc-500/20 text-zinc-400';

  return (
    <div className="bg-terminal-surface rounded-lg p-3 border border-terminal-border">
      <div className="flex items-center justify-between mb-2">
        <span className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase ${classColor}`}>
          {signal.signal_class.replace(/_/g, ' ')}
        </span>
        <div className="flex items-center gap-2">
          {signal.material && (
            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono uppercase bg-red-500/20 text-red-400">
              Material
            </span>
          )}
          <span className="text-[10px] text-terminal-text-muted font-mono">
            {new Date(signal.detected_at).toLocaleDateString()}
          </span>
        </div>
      </div>

      <div className="space-y-1 text-xs">
        <div className="flex items-center gap-2">
          <span className="text-terminal-text-muted">Detection:</span>
          <span className="text-terminal-text">{signal.detection_method}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-terminal-text-muted">Impact:</span>
          <span className="text-terminal-text">{signal.resolution_impact}</span>
        </div>
        {signal.evidence_ref && (
          <div className="flex items-center gap-2">
            <span className="text-terminal-text-muted">Evidence:</span>
            <span className="font-mono text-echelon-cyan text-[10px]">
              {signal.evidence_ref}
            </span>
          </div>
        )}
      </div>

      {onCreateInvestigation && (
        <button
          type="button"
          onClick={() => onCreateInvestigation(signal)}
          className="mt-2 w-full text-[10px] text-echelon-cyan hover:text-echelon-cyan/80 border border-echelon-cyan/20 hover:border-echelon-cyan/40 rounded py-1.5 transition-colors"
        >
          Create Investigation from Signal
        </button>
      )}
    </div>
  );
}
