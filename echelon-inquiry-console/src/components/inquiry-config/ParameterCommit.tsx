import type { TheatreTemplate } from '../../types/inquiry';
import type { CommitmentTarget } from '../../types/inquiry';
import { COMMITMENT_TARGETS } from '../../data/templates';

interface ParameterCommitProps {
  template: TheatreTemplate;
  isCommitted: boolean;
  onCommit: () => void;
}

export function ParameterCommit({
  template,
  isCommitted,
  onCommit,
}: ParameterCommitProps) {
  const target: CommitmentTarget | undefined =
    COMMITMENT_TARGETS[template.template_id];

  if (!target) return null;

  const commitLabel =
    template.execution_path === 'PRODUCT'
      ? 'Commit Parameters (local)'
      : 'Commit + Publish (log)';

  return (
    <div>
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-echelon-navy">
        Commitment Parameters
      </h3>

      <div
        className={`rounded-lg border border-echelon-border bg-white p-4 ${
          isCommitted ? 'opacity-80' : ''
        }`}
      >
        {/* Criteria IDs */}
        <div className="mb-4">
          <span className="text-xs uppercase tracking-wider text-slate-500">
            Criteria
          </span>
          <div className="mt-1.5 flex flex-wrap gap-1.5">
            {target.template.criteria_ids.map((cid) => (
              <span
                key={cid}
                className="rounded-full bg-echelon-data-bg px-2.5 py-1 font-mono text-xs text-echelon-data-text"
              >
                {cid}
              </span>
            ))}
          </div>
        </div>

        {/* Scoring Thresholds */}
        <div className="mb-4">
          <span className="text-xs uppercase tracking-wider text-slate-500">
            Scoring Thresholds
          </span>
          <div className="mt-1.5 rounded-md bg-echelon-data-bg p-3 font-mono text-xs text-echelon-data-text">
            {Object.entries(target.template.scoring_thresholds).map(
              ([key, val]) => (
                <div key={key} className="flex justify-between py-0.5">
                  <span>{key}</span>
                  <span>{val.toFixed(1)}</span>
                </div>
              )
            )}
          </div>
        </div>

        {/* Version Pins */}
        <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div>
            <span className="text-xs uppercase tracking-wider text-slate-500">
              Construct
            </span>
            <p className="mt-0.5 font-mono text-xs text-echelon-data-text">
              {target.version_pins.construct}
            </p>
          </div>
          <div>
            <span className="text-xs uppercase tracking-wider text-slate-500">
              Scorer
            </span>
            <p className="mt-0.5 font-mono text-xs text-echelon-data-text">
              {target.version_pins.scorer}
            </p>
          </div>
          <div>
            <span className="text-xs uppercase tracking-wider text-slate-500">
              Methodology
            </span>
            <p className="mt-0.5 font-mono text-xs text-echelon-data-text">
              {target.version_pins.methodology}
            </p>
          </div>
        </div>

        {!isCommitted && (
          <button
            onClick={onCommit}
            className="mt-2 w-full rounded-md bg-echelon-navy px-6 py-2.5 font-medium text-white transition-colors hover:bg-opacity-90"
          >
            {commitLabel}
          </button>
        )}
      </div>
    </div>
  );
}
