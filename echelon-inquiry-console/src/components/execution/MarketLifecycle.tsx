import type { MarketPhase } from '../../types/execution';

interface MarketLifecycleProps {
  phases: MarketPhase[];
  currentPhaseIndex: number;
  templateName: string;
  constructId: string;
  constructVersion: string;
}

export function MarketLifecycle({
  phases,
  currentPhaseIndex,
  templateName,
  constructId,
  constructVersion,
}: MarketLifecycleProps) {
  return (
    <div>
      <div className="mb-4">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-echelon-navy">
          {templateName}
        </h3>
        <p className="mt-1 font-mono text-xs text-slate-500">
          {constructId}@{constructVersion}
        </p>
        <span className="mt-1 inline-block rounded border border-echelon-border px-2 py-0.5 text-xs font-medium text-echelon-navy">
          MARKET / LMSR
        </span>
      </div>

      <div className="mb-2 text-sm text-slate-600">
        Phase {currentPhaseIndex} of {phases.length}
      </div>
      <div className="mb-6 h-2 w-full overflow-hidden rounded-full bg-slate-200">
        <div
          className="h-full rounded-full bg-echelon-blue transition-[width] duration-300 ease-out"
          style={{ width: `${(currentPhaseIndex / phases.length) * 100}%` }}
        />
      </div>

      <div className="space-y-2">
        {phases.map((phase, idx) => {
          const isComplete = idx < currentPhaseIndex;
          const isCurrent = idx === currentPhaseIndex;

          if (!isComplete && !isCurrent) {
            return (
              <div
                key={phase.phase_number}
                className="rounded border border-dashed border-slate-200 p-3 opacity-40"
              >
                <span className="font-mono text-xs text-slate-400">
                  Phase {phase.phase_number}
                </span>
                <p className="mt-0.5 text-xs text-slate-400">{phase.label}</p>
              </div>
            );
          }

          return (
            <div
              key={phase.phase_number}
              className="animate-fade-slide-up rounded border border-echelon-border bg-white p-3"
              style={{ animationDelay: `${idx * 50}ms` }}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-medium text-echelon-navy">
                      Phase {phase.phase_number}
                    </span>
                    {isComplete && (
                      <span className="text-xs text-emerald-600">&#10003;</span>
                    )}
                  </div>
                  <p className="mt-0.5 text-sm font-medium text-slate-700">
                    {phase.label}
                  </p>
                  <p className="mt-0.5 text-xs text-slate-500">{phase.detail}</p>
                </div>
              </div>
              {phase.hash && isComplete && (
                <p className="mt-1 font-mono text-xs text-slate-400">
                  {phase.hash.slice(0, 16)}...
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
