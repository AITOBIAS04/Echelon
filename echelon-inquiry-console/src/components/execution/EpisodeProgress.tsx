import type { Episode } from '../../types/execution';
import { formatScore } from '../../utils/format';

interface EpisodeProgressProps {
  episodes: Episode[];
  currentIndex: number;
  totalEpisodes: number;
  templateName: string;
  constructId: string;
  constructVersion: string;
}

function CriteriaScoreDot({ score }: { score: number }) {
  const bg =
    score >= 1.0
      ? 'bg-emerald-500'
      : score > 0
        ? 'bg-amber-500'
        : 'bg-red-500';
  return <span className={`inline-block h-2 w-2 rounded-full ${bg}`} />;
}

export function EpisodeProgress({
  episodes,
  currentIndex,
  totalEpisodes,
  templateName,
  constructId,
  constructVersion,
}: EpisodeProgressProps) {
  const progressPct = totalEpisodes > 0 ? (currentIndex / totalEpisodes) * 100 : 0;

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
          PRODUCT / Replay
        </span>
      </div>

      <div className="mb-2 text-sm text-slate-600">
        Episode {currentIndex} of {totalEpisodes}
      </div>
      <div className="mb-6 h-2 w-full overflow-hidden rounded-full bg-slate-200">
        <div
          className="h-full rounded-full bg-echelon-blue transition-[width] duration-300 ease-out"
          style={{ width: `${progressPct}%` }}
        />
      </div>

      <div className="space-y-2">
        {episodes.map((ep, idx) => (
          <div
            key={ep.episode_id}
            className="animate-fade-slide-up rounded border border-echelon-border bg-white p-3"
            style={{ animationDelay: `${idx * 50}ms` }}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0 flex-1">
                <span className="font-mono text-xs font-medium text-echelon-navy">
                  {ep.episode_id}
                </span>
                <p className="mt-0.5 line-clamp-1 text-xs text-slate-600">
                  {ep.ground_truth_summary}
                </p>
              </div>
              <div className="flex flex-shrink-0 items-center gap-2">
                <span className="font-mono text-xs text-echelon-data-text">
                  {formatScore(ep.composite_score)}
                </span>
                <span
                  className={`text-xs font-medium ${
                    ep.construct_output_class === 'PASS'
                      ? 'text-emerald-600'
                      : 'text-red-600'
                  }`}
                >
                  {ep.construct_output_class}
                </span>
              </div>
            </div>
            <div className="mt-1.5 flex gap-1">
              {Object.entries(ep.criteria_scores).map(([cid, score]) => (
                <CriteriaScoreDot key={cid} score={score} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
