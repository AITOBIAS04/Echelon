/**
 * StopConditionProgress — Progress visualization for each stop condition type.
 *
 * OUTCOME_RESOLUTION: Shows market status (active/resolved)
 * EVIDENCE_THRESHOLD: Progress bar towards min claims + corroboration score
 * SPONSOR_DEFINED: Time remaining until milestone timestamp
 */

import type { StopCondition } from '../../types/investigation';

interface StopConditionProgressProps {
  stopCondition: StopCondition | string;
  stopConfig: Record<string, unknown>;
  evidenceCount: number;
  claimStatusSummary: Record<string, number>;
  counterSignalCount: number;
}

function ProgressBar({
  value,
  max,
  label,
}: {
  value: number;
  max: number;
  label: string;
}) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  const color = pct >= 100 ? 'bg-emerald-500' : pct >= 50 ? 'bg-amber-500' : 'bg-echelon-cyan';

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-[10px] text-terminal-text-muted">{label}</span>
        <span className="text-[10px] font-mono text-terminal-text">
          {value}/{max}
        </span>
      </div>
      <div className="w-full bg-terminal-bg rounded-full h-1.5">
        <div
          className={`h-1.5 rounded-full transition-all ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function StopConditionProgress({
  stopCondition,
  stopConfig,
  evidenceCount,
  claimStatusSummary,
  counterSignalCount,
}: StopConditionProgressProps) {
  const supportedClaims = (claimStatusSummary.supported ?? 0) + (claimStatusSummary.partially_supported ?? 0);
  const totalClaims = Object.values(claimStatusSummary).reduce((a, b) => a + b, 0);

  return (
    <div className="bg-terminal-surface rounded-lg p-4 border border-terminal-border space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-[10px] text-terminal-text-muted uppercase tracking-wider font-semibold">
          Stop Condition Progress
        </span>
        <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-echelon-cyan/10 text-echelon-cyan">
          {stopCondition}
        </span>
      </div>

      {stopCondition === 'OUTCOME_RESOLUTION' && (
        <div className="text-xs text-terminal-text-secondary">
          Investigation concludes on market resolution. Monitoring evidence accumulation.
        </div>
      )}

      {stopCondition === 'EVIDENCE_THRESHOLD' && (
        <div className="space-y-2">
          <ProgressBar
            value={supportedClaims}
            max={(stopConfig.min_supported_claims as number) ?? 3}
            label="Supported Claims"
          />
          {stopConfig.min_corroboration_score != null && (
            <ProgressBar
              value={evidenceCount > 0 ? Math.min(evidenceCount, 10) : 0}
              max={10}
              label="Corroboration Evidence"
            />
          )}
        </div>
      )}

      {stopCondition === 'SPONSOR_DEFINED' && (() => {
        const milestone = stopConfig.milestone_timestamp as string | undefined;
        if (!milestone) return <div className="text-xs text-terminal-text-muted">No milestone set</div>;
        const remaining = new Date(milestone).getTime() - Date.now();
        const days = Math.max(0, Math.floor(remaining / 86_400_000));
        const hours = Math.max(0, Math.floor((remaining % 86_400_000) / 3_600_000));
        return (
          <div className="text-xs text-terminal-text">
            <span className="text-terminal-text-muted">Milestone: </span>
            <span className="font-mono">{new Date(milestone).toLocaleDateString()}</span>
            <span className="text-terminal-text-muted ml-2">
              ({remaining > 0 ? `${days}d ${hours}h remaining` : 'Passed'})
            </span>
          </div>
        );
      })()}

      {/* Common stats */}
      <div className="grid grid-cols-3 gap-2 pt-2 border-t border-terminal-border/50">
        <div className="text-center">
          <div className="text-sm font-mono text-echelon-cyan">{evidenceCount}</div>
          <div className="text-[9px] text-terminal-text-muted uppercase">Evidence</div>
        </div>
        <div className="text-center">
          <div className="text-sm font-mono text-echelon-cyan">{totalClaims}</div>
          <div className="text-[9px] text-terminal-text-muted uppercase">Claims</div>
        </div>
        <div className="text-center">
          <div className="text-sm font-mono text-echelon-cyan">{counterSignalCount}</div>
          <div className="text-[9px] text-terminal-text-muted uppercase">Signals</div>
        </div>
      </div>
    </div>
  );
}
