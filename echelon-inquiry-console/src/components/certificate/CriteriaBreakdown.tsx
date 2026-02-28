import { formatScore } from '../../utils/format';

interface CriteriaBreakdownProps {
  criteriaScores: Record<string, number>;
}

function getBarColour(score: number): string {
  if (score >= 0.9) return 'bg-emerald-500';
  if (score >= 0.5) return 'bg-amber-500';
  return 'bg-red-500';
}

export function CriteriaBreakdown({ criteriaScores }: CriteriaBreakdownProps) {
  const entries = Object.entries(criteriaScores).sort(([a], [b]) =>
    a.localeCompare(b)
  );

  return (
    <div>
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-echelon-navy">
        Criteria Breakdown
      </h3>
      <div className="space-y-2">
        {entries.map(([criteriaId, score]) => (
          <div key={criteriaId}>
            <div className="mb-1 flex items-center justify-between">
              <span className="font-mono text-xs text-echelon-data-text">
                {criteriaId}
              </span>
              <span className="font-mono text-xs text-slate-500">
                {formatScore(score)}
              </span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
              <div
                className={`h-full rounded-full ${getBarColour(score)} transition-[width] duration-500 ease-out`}
                style={{ width: `${score * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
