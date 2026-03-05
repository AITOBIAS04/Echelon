/**
 * InvestigationProgressBar — Visual progress indicator for investigation lifecycle.
 *
 * Shows evidence count, claim status distribution, counter-signal count,
 * and integrates StopConditionProgress for stop-condition-specific tracking.
 */

import { StopConditionProgress } from './StopConditionProgress';
import type { InvestigationDetail } from '../../types/investigation';

interface InvestigationProgressBarProps {
  investigation: InvestigationDetail;
}

const CLAIM_STATUS_COLORS: Record<string, string> = {
  supported: 'bg-emerald-500',
  partially_supported: 'bg-amber-500',
  unconfirmed: 'bg-zinc-500',
  contradicted: 'bg-red-500',
};

export function InvestigationProgressBar({
  investigation,
}: InvestigationProgressBarProps) {
  const totalClaims = investigation.claims.claims.length;
  const statusSummary = investigation.claims.status_summary;
  const evidenceCount = investigation.evidence.items.length;
  const signalCount = investigation.counter_signals.signals.length;
  const materialSignals = investigation.counter_signals.signals.filter(
    (s) => s.material,
  ).length;

  return (
    <div className="space-y-3">
      {/* Stop condition progress */}
      <StopConditionProgress
        stopCondition={investigation.stop_condition}
        stopConfig={investigation.stop_config}
        evidenceCount={evidenceCount}
        claimStatusSummary={statusSummary}
        counterSignalCount={signalCount}
      />

      {/* Claim status distribution bar */}
      {totalClaims > 0 && (
        <div className="bg-terminal-surface rounded-lg p-3 border border-terminal-border">
          <div className="text-[10px] text-terminal-text-muted uppercase tracking-wider font-semibold mb-2">
            Claim Status Distribution
          </div>
          <div className="flex rounded-full h-2 overflow-hidden bg-terminal-bg">
            {Object.entries(statusSummary).map(([status, count]) => {
              const pct = (count / totalClaims) * 100;
              if (pct === 0) return null;
              return (
                <div
                  key={status}
                  className={`${CLAIM_STATUS_COLORS[status] ?? 'bg-zinc-500'} transition-all`}
                  style={{ width: `${pct}%` }}
                  title={`${status}: ${count}`}
                />
              );
            })}
          </div>
          <div className="flex gap-3 mt-2">
            {Object.entries(statusSummary).map(([status, count]) => (
              <div key={status} className="flex items-center gap-1">
                <div
                  className={`w-2 h-2 rounded-full ${CLAIM_STATUS_COLORS[status] ?? 'bg-zinc-500'}`}
                />
                <span className="text-[9px] text-terminal-text-muted">
                  {status.replace('_', ' ')} ({count})
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Corroboration indicator */}
      {materialSignals > 0 && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg px-3 py-2">
          <span className="text-[10px] text-amber-400">
            {materialSignals} material counter-signal{materialSignals !== 1 ? 's' : ''} detected — corroboration may be impacted
          </span>
        </div>
      )}
    </div>
  );
}
