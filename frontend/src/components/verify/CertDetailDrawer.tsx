import { useEffect, useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { useCertificateDetail } from '../../hooks/useCertificates';
import type { ReplayScore } from '../../types/verification';

function compositeColour(score: number): string {
  if (score > 0.7) return 'text-[var(--e-green-600)]';
  if (score > 0.4) return 'text-[var(--e-orange-600)]';
  return 'text-[var(--e-red-600)]';
}

function brierColour(score: number): string {
  if (score < 0.15) return 'text-[var(--e-green-600)]';
  if (score < 0.3) return 'text-[var(--e-orange-600)]';
  return 'text-[var(--e-red-600)]';
}

type ReplaySortKey = 'precision' | 'latency';

function sortReplays(scores: ReplayScore[], sortKey: ReplaySortKey): ReplayScore[] {
  return [...scores].sort((a, b) => {
    if (sortKey === 'precision') return b.precision - a.precision;
    return a.scoring_latency_ms - b.scoring_latency_ms;
  });
}

interface CertDetailDrawerProps {
  certId: string | null;
  onClose: () => void;
}

export function CertDetailDrawer({ certId, onClose }: CertDetailDrawerProps) {
  const { certificate, isLoading } = useCertificateDetail(certId);
  const [replaySort, setReplaySort] = useState<ReplaySortKey>('precision');

  useEffect(() => {
    if (!certId) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [certId, onClose]);

  if (!certId) return null;

  return (
    <>
      <div
        className="fixed inset-0 z-[300] bg-[color:oklch(0.205_0.015_265_/_0.14)] backdrop-blur-sm"
        onClick={onClose}
      />

      <div
        className="fixed right-6 top-[72px] z-[310] flex max-h-[calc(100vh-96px)] w-[460px] flex-col overflow-hidden rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-lg)]"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-labelledby="cert-drawer-title"
      >
        <div className="flex items-start justify-between border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-4">
          <div className="min-w-0">
            <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              Certificate Detail
            </div>
            <div className="flex items-center gap-2">
              <span id="cert-drawer-title" className="truncate text-[15px] font-semibold text-[var(--e-text-primary)]">
                {certificate?.construct_id ?? 'Loading...'}
              </span>
              {certificate ? (
                <span className="inline-flex rounded-full border border-[var(--e-purple-200)] bg-[var(--e-purple-50)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-purple-700)]">
                  {certificate.domain}
                </span>
              ) : null}
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded p-1 text-[var(--e-text-muted)] transition hover:text-[var(--e-text-primary)]"
          >
            &#x2715;
          </button>
        </div>

        <div className="space-y-5 overflow-y-auto p-5">
          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 6 }).map((_, index) => (
                <div
                  key={index}
                  className="h-16 animate-pulse rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)]"
                />
              ))}
            </div>
          ) : certificate ? (
            <>
              <div className="grid grid-cols-2 gap-2">
                <ScoreCard label="Precision" value={certificate.precision.toFixed(3)} />
                <ScoreCard label="Recall" value={certificate.recall.toFixed(3)} />
                <ScoreCard label="Reply Accuracy" value={certificate.reply_accuracy.toFixed(3)} />
                <ScoreCard
                  label="Composite Score"
                  value={certificate.composite_score.toFixed(3)}
                  valueClass={compositeColour(certificate.composite_score)}
                  highlight
                />
                <ScoreCard
                  label="Brier Score"
                  value={certificate.brier.toFixed(3)}
                  valueClass={brierColour(certificate.brier)}
                />
                <ScoreCard label="Replay Count" value={String(certificate.replay_count)} />
              </div>

              <div className="space-y-2 rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] p-4">
                <span className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Methodology</span>
                <div className="space-y-1.5">
                  <DataRow label="Version" value={certificate.methodology_version} />
                  <DataRow label="Scoring Model" value={certificate.scoring_model} />
                  <DataRow label="Ground Truth" value={certificate.ground_truth_source} />
                  <DataRow label="Sample Size" value={String(certificate.sample_size)} />
                </div>
              </div>

              {certificate.replay_scores.length > 0 ? (
                <div className="space-y-2">
                  <span className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Replay Scores</span>
                  <div className="max-h-[300px] overflow-y-auto overflow-x-auto rounded-lg border border-[var(--e-border-primary)]">
                    <table className="min-w-full border-collapse">
                      <thead>
                        <tr className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] text-left">
                          <th className="px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                            <button
                              className="inline-flex items-center gap-0.5 text-inherit transition hover:text-[var(--e-text-primary)]"
                              onClick={() => setReplaySort('precision')}
                            >
                              Precision
                              {replaySort === 'precision' ? <ChevronDown className="h-3 w-3 text-[var(--e-purple-700)]" /> : null}
                            </button>
                          </th>
                          <th className="px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Recall</th>
                          <th className="px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Accuracy</th>
                          <th className="px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                            <button
                              className="inline-flex items-center gap-0.5 text-inherit transition hover:text-[var(--e-text-primary)]"
                              onClick={() => setReplaySort('latency')}
                            >
                              Latency
                              {replaySort === 'latency' ? <ChevronUp className="h-3 w-3 text-[var(--e-purple-700)]" /> : null}
                            </button>
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {sortReplays(certificate.replay_scores, replaySort).map((score) => (
                          <tr key={score.id} className="border-b border-[var(--e-border-secondary)] last:border-b-0">
                            <td className="px-3 py-2 font-mono text-[12px] tabular-nums text-[var(--e-text-primary)]">{score.precision.toFixed(3)}</td>
                            <td className="px-3 py-2 font-mono text-[12px] tabular-nums text-[var(--e-text-primary)]">{score.recall.toFixed(3)}</td>
                            <td className="px-3 py-2 font-mono text-[12px] tabular-nums text-[var(--e-text-primary)]">{score.reply_accuracy.toFixed(3)}</td>
                            <td className="px-3 py-2 font-mono text-[12px] tabular-nums text-[var(--e-text-muted)]">{score.scoring_latency_ms}ms</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : null}
            </>
          ) : (
            <div className="py-6 text-center">
              <p className="text-[13px] text-[var(--e-text-muted)]">Certificate not found</p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

function ScoreCard({
  label,
  value,
  valueClass,
  highlight,
}: {
  label: string;
  value: string;
  valueClass?: string;
  highlight?: boolean;
}) {
  return (
    <div className={`rounded-xl border p-4 ${highlight ? 'border-[var(--e-purple-200)] bg-[var(--e-purple-50)]' : 'border-[var(--e-border-primary)] bg-[var(--e-bg-card)]'}`}>
      <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">{label}</div>
      <div className={`font-mono text-[24px] font-bold leading-8 ${valueClass ?? 'text-[var(--e-text-primary)]'}`}>
        {value}
      </div>
    </div>
  );
}

function DataRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 text-[12px]">
      <span className="text-[var(--e-text-muted)]">{label}</span>
      <span className="text-right font-mono text-[var(--e-text-secondary)]">{value}</span>
    </div>
  );
}
