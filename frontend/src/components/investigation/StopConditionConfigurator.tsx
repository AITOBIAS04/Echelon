/**
 * StopConditionConfigurator — 3 stop condition types with config fields.
 * Used in Investigation Creation Wizard step 4.
 */

import type { StopCondition } from '../../types/investigation';

const STOP_CONDITIONS: {
  id: StopCondition;
  label: string;
  description: string;
}[] = [
  {
    id: 'OUTCOME_RESOLUTION',
    label: 'Outcome Resolution',
    description:
      'Investigation concludes when the market outcome is resolved. No additional configuration required.',
  },
  {
    id: 'EVIDENCE_THRESHOLD',
    label: 'Evidence Threshold',
    description:
      'Investigation concludes when evidence reaches a configurable quality threshold.',
  },
  {
    id: 'SPONSOR_DEFINED',
    label: 'Sponsor Defined',
    description:
      'Investigation concludes at a sponsor-specified milestone timestamp.',
  },
];

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
    <div className="space-y-4">
      <div className="text-xs text-terminal-text-muted">
        Choose when the investigation should conclude. This determines the stop condition evaluation logic.
      </div>

      {/* Condition type selector */}
      <div className="space-y-2">
        {STOP_CONDITIONS.map((sc) => {
          const isSelected = condition === sc.id;
          return (
            <button
              key={sc.id}
              type="button"
              onClick={() => {
                onConditionChange(sc.id);
                onConfigChange({});
              }}
              className={`w-full text-left p-3 rounded-lg border transition-colors ${
                isSelected
                  ? 'border-echelon-cyan/50 bg-echelon-cyan/5'
                  : 'border-terminal-border hover:border-terminal-border/80 bg-terminal-surface'
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <div
                  className={`w-3 h-3 rounded-full border ${
                    isSelected
                      ? 'border-echelon-cyan bg-echelon-cyan'
                      : 'border-terminal-border'
                  }`}
                />
                <span className="text-xs font-semibold text-terminal-text">
                  {sc.label}
                </span>
              </div>
              <p className="text-[10px] text-terminal-text-muted leading-relaxed pl-5">
                {sc.description}
              </p>
            </button>
          );
        })}
      </div>

      {/* Config fields for EVIDENCE_THRESHOLD */}
      {condition === 'EVIDENCE_THRESHOLD' && (
        <div className="bg-terminal-surface rounded-lg p-4 border border-terminal-border space-y-3">
          <div className="text-[10px] text-terminal-text-muted uppercase tracking-wider font-semibold">
            Threshold Configuration
          </div>
          <div className="grid grid-cols-2 gap-3">
            <label className="block">
              <span className="text-[10px] text-terminal-text-muted">
                Min Supported Claims
              </span>
              <input
                type="number"
                min={1}
                value={(config.min_supported_claims as number) ?? 3}
                onChange={(e) =>
                  onConfigChange({
                    ...config,
                    min_supported_claims: parseInt(e.target.value) || 1,
                  })
                }
                className="mt-1 w-full bg-terminal-bg border border-terminal-border rounded px-2 py-1.5 text-xs text-terminal-text font-mono"
              />
            </label>
            <label className="block">
              <span className="text-[10px] text-terminal-text-muted">
                Min Corroboration Score (0-1)
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
                className="mt-1 w-full bg-terminal-bg border border-terminal-border rounded px-2 py-1.5 text-xs text-terminal-text font-mono"
              />
            </label>
          </div>
        </div>
      )}

      {/* Config fields for SPONSOR_DEFINED */}
      {condition === 'SPONSOR_DEFINED' && (
        <div className="bg-terminal-surface rounded-lg p-4 border border-terminal-border space-y-3">
          <div className="text-[10px] text-terminal-text-muted uppercase tracking-wider font-semibold">
            Sponsor Configuration
          </div>
          <label className="block">
            <span className="text-[10px] text-terminal-text-muted">
              Milestone Timestamp (ISO 8601)
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
              className="mt-1 w-full bg-terminal-bg border border-terminal-border rounded px-2 py-1.5 text-xs text-terminal-text font-mono"
            />
          </label>
        </div>
      )}
    </div>
  );
}
