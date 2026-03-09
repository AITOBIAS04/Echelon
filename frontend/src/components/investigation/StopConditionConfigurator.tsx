/**
 * StopConditionConfigurator — bounded readiness contract configuration.
 */

import type { StopCondition } from '../../types/investigation';

const STOP_CONDITIONS: Array<{
  id: StopCondition;
  label: string;
  description: string;
}> = [
  {
    id: 'OUTCOME_RESOLUTION',
    label: 'Outcome Resolution',
    description:
      'The investigation concludes when the market outcome resolves. This is the most direct certificate path.',
  },
  {
    id: 'EVIDENCE_THRESHOLD',
    label: 'Evidence Threshold',
    description:
      'The investigation concludes when a configured evidence quality threshold is met through corroborated claims.',
  },
  {
    id: 'SPONSOR_DEFINED',
    label: 'Sponsor Defined',
    description:
      'The investigation concludes when a sponsor-defined milestone or timestamp is reached.',
  },
] as const;

interface StopConditionConfiguratorProps {
  condition: StopCondition;
  config: Record<string, unknown>;
  onConditionChange: (condition: StopCondition) => void;
  onConfigChange: (config: Record<string, unknown>) => void;
}

export function StopConditionConfigurator({
  condition,
  config,
  onConditionChange,
  onConfigChange,
}: StopConditionConfiguratorProps) {
  return (
    <div className="space-y-5">
      <div className="rounded-2xl border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-4">
        <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--e-text-muted)]">
          Stop-condition contract
        </div>
        <p className="mt-2 text-sm leading-6 text-[var(--e-text-secondary)]">
          This is the rule that feeds readiness and certificate progression. Choose the one that honestly matches the inquiry, not the one that produces the earliest completion.
        </p>
      </div>

      <div className="space-y-3">
        {STOP_CONDITIONS.map((stopCondition) => {
          const selected = condition === stopCondition.id;
          return (
            <button
              key={stopCondition.id}
              type="button"
              onClick={() => {
                onConditionChange(stopCondition.id);
                onConfigChange({});
              }}
              className={`w-full rounded-2xl border px-4 py-4 text-left transition ${
                selected
                  ? 'border-purple-200 bg-purple-100/70'
                  : 'border-[var(--e-border-primary)] bg-[var(--e-bg-sunken)] hover:bg-[var(--e-bg-hover)]'
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-[var(--e-text-primary)]">
                    {stopCondition.label}
                  </div>
                  <p className="mt-2 text-sm leading-6 text-[var(--e-text-secondary)]">
                    {stopCondition.description}
                  </p>
                </div>
                <div
                  className={`mt-0.5 flex h-5 w-5 items-center justify-center rounded-full border ${
                    selected
                      ? 'border-purple-300 bg-purple-500 text-white'
                      : 'border-[var(--e-border-primary)] bg-[var(--e-bg-card)] text-[var(--e-text-muted)]'
                  }`}
                >
                  {selected ? '✓' : ''}
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {condition === 'EVIDENCE_THRESHOLD' && (
        <div className="rounded-2xl border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-4">
          <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--e-text-muted)]">
            Threshold Configuration
          </div>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <label className="block">
              <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--e-text-muted)]">
                Min Supported Claims
              </span>
              <input
                type="number"
                min={1}
                value={(config.min_supported_claims as number) ?? 3}
                onChange={(e) =>
                  onConfigChange({
                    ...config,
                    min_supported_claims: parseInt(e.target.value, 10) || 1,
                  })
                }
                className="mt-2 w-full rounded-xl border border-[var(--e-border-secondary)] bg-[var(--e-bg-elevated)] px-3 py-2 text-sm font-mono text-[var(--e-text-primary)] outline-none transition focus:border-[var(--e-border-focus)] focus:ring-2 focus:ring-[color:oklch(0.53_0.23_295_/_0.12)]"
              />
            </label>

            <label className="block">
              <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--e-text-muted)]">
                Min Corroboration Score
              </span>
              <input
                type="number"
                min={0}
                max={1}
                step={0.1}
                value={(config.min_corroboration_score as number) ?? 0.7}
                onChange={(e) =>
                  onConfigChange({
                    ...config,
                    min_corroboration_score: parseFloat(e.target.value) || 0,
                  })
                }
                className="mt-2 w-full rounded-xl border border-[var(--e-border-secondary)] bg-[var(--e-bg-elevated)] px-3 py-2 text-sm font-mono text-[var(--e-text-primary)] outline-none transition focus:border-[var(--e-border-focus)] focus:ring-2 focus:ring-[color:oklch(0.53_0.23_295_/_0.12)]"
              />
            </label>
          </div>
        </div>
      )}

      {condition === 'SPONSOR_DEFINED' && (
        <div className="rounded-2xl border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-4">
          <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--e-text-muted)]">
            Sponsor Configuration
          </div>
          <label className="mt-4 block">
            <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--e-text-muted)]">
              Milestone Timestamp
            </span>
            <input
              type="datetime-local"
              value={
                config.milestone_timestamp
                  ? (config.milestone_timestamp as string).slice(0, 16)
                  : ''
              }
              onChange={(e) =>
                onConfigChange({
                  ...config,
                  milestone_timestamp: e.target.value
                    ? new Date(e.target.value).toISOString()
                    : undefined,
                })
              }
              className="mt-2 w-full rounded-xl border border-[var(--e-border-secondary)] bg-[var(--e-bg-elevated)] px-3 py-2 text-sm font-mono text-[var(--e-text-primary)] outline-none transition focus:border-[var(--e-border-focus)] focus:ring-2 focus:ring-[color:oklch(0.53_0.23_295_/_0.12)]"
            />
          </label>
        </div>
      )}
    </div>
  );
}
