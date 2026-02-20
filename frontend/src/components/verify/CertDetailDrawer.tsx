/**
 * CertDetailDrawer — Slide-in drawer for certificate details.
 *
 * Score cards grid, methodology info, and replay scores table.
 * Same drawer pattern as RunDetailDrawer (420px, z-[310]).
 */

import { useEffect, useState } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';
import { useCertificateDetail } from '../../hooks/useCertificates';
import type { ReplayScore } from '../../types/verification';

// ── Score colour coding ──────────────────────────────────────────────────

function compositeColour(score: number): string {
  if (score > 0.7) return 'text-status-success';
  if (score > 0.4) return 'text-status-warning';
  return 'text-status-danger';
}

function brierColour(score: number): string {
  if (score < 0.15) return 'text-status-success';
  if (score < 0.3) return 'text-status-warning';
  return 'text-status-danger';
}

// ── Replay sort ──────────────────────────────────────────────────────────

type ReplaySortKey = 'precision' | 'latency';

function sortReplays(scores: ReplayScore[], sortKey: ReplaySortKey): ReplayScore[] {
  return [...scores].sort((a, b) => {
    if (sortKey === 'precision') return b.precision - a.precision; // descending
    return a.scoring_latency_ms - b.scoring_latency_ms; // ascending
  });
}

// ── Component ────────────────────────────────────────────────────────────

interface CertDetailDrawerProps {
  certId: string | null;
  onClose: () => void;
}

export function CertDetailDrawer({ certId, onClose }: CertDetailDrawerProps) {
  const { certificate, isLoading } = useCertificateDetail(certId);
  const [replaySort, setReplaySort] = useState<ReplaySortKey>('precision');

  // Escape key to close
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
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-[300] bg-black/50"
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        className="fixed top-[60px] right-6 w-[420px] max-h-[calc(100vh-80px)] rounded-xl flex flex-col overflow-hidden z-[310] shadow-elevation-3 bg-terminal-overlay border border-terminal-border"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-labelledby="cert-drawer-title"
      >
        {/* Header */}
        <div className="section-header">
          <div className="flex items-center gap-2 min-w-0">
            <span id="cert-drawer-title" className="section-header-title truncate">
              {certificate?.construct_id ?? 'Loading...'}
            </span>
            {certificate && (
              <span className="chip chip-info text-[10px]">{certificate.domain}</span>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded transition-colors text-terminal-text-muted hover:text-terminal-text flex-shrink-0"
          >
            &#x2715;
          </button>
        </div>

        {/* Body */}
        <div className="p-4 overflow-y-auto space-y-4">
          {isLoading ? (
            <div className="space-y-3">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-16 bg-terminal-panel border border-terminal-border rounded-xl animate-pulse" />
              ))}
            </div>
          ) : certificate ? (
            <>
              {/* Score cards grid */}
              <div className="grid grid-cols-2 gap-2">
                <ScoreCard label="Precision" value={certificate.precision.toFixed(3)} />
                <ScoreCard label="Recall" value={certificate.recall.toFixed(3)} />
                <ScoreCard label="Reply Accuracy" value={certificate.reply_accuracy.toFixed(3)} />
                <ScoreCard
                  label="Composite Score"
                  value={certificate.composite_score.toFixed(3)}
                  valueClass={`text-echelon-cyan ${compositeColour(certificate.composite_score)}`}
                  highlight
                />
                <ScoreCard
                  label="Brier Score"
                  value={certificate.brier.toFixed(3)}
                  valueClass={brierColour(certificate.brier)}
                />
                <ScoreCard label="Replay Count" value={String(certificate.replay_count)} />
              </div>

              {/* Methodology section */}
              <div className="bg-terminal-card border border-terminal-border rounded-lg p-3 space-y-2">
                <span className="data-label">Methodology</span>
                <div className="space-y-1.5 mt-1">
                  <DataRow label="Version" value={certificate.methodology_version} />
                  <DataRow label="Scoring Model" value={certificate.scoring_model} />
                  <DataRow label="Ground Truth" value={certificate.ground_truth_source} />
                  <DataRow label="Sample Size" value={String(certificate.sample_size)} />
                </div>
              </div>

              {/* Replay Scores table */}
              {certificate.replay_scores.length > 0 && (
                <div className="space-y-2">
                  <span className="data-label">Replay Scores</span>
                  <div className="max-h-[300px] overflow-y-auto overflow-x-auto border border-terminal-border rounded-lg">
                    <table className="terminal-table">
                      <thead>
                        <tr>
                          <th>
                            <button
                              className="inline-flex items-center gap-0.5 hover:text-terminal-text transition-colors"
                              onClick={() => setReplaySort('precision')}
                            >
                              Precision
                              {replaySort === 'precision' && <ChevronDown className="w-3 h-3 text-echelon-cyan" />}
                            </button>
                          </th>
                          <th>Recall</th>
                          <th>Accuracy</th>
                          <th>
                            <button
                              className="inline-flex items-center gap-0.5 hover:text-terminal-text transition-colors"
                              onClick={() => setReplaySort('latency')}
                            >
                              Latency
                              {replaySort === 'latency' && <ChevronUp className="w-3 h-3 text-echelon-cyan" />}
                            </button>
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {sortReplays(certificate.replay_scores, replaySort).map((rs) => (
                          <tr key={rs.id}>
                            <td className="font-mono tabular-nums">{rs.precision.toFixed(3)}</td>
                            <td className="font-mono tabular-nums">{rs.recall.toFixed(3)}</td>
                            <td className="font-mono tabular-nums">{rs.reply_accuracy.toFixed(3)}</td>
                            <td className="font-mono tabular-nums text-terminal-text-muted">
                              {rs.scoring_latency_ms}ms
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-6">
              <p className="text-xs text-terminal-text-muted">Certificate not found</p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

// ── Sub-components ───────────────────────────────────────────────────────

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
    <div className={`bg-terminal-panel border rounded-xl p-4 ${highlight ? 'border-echelon-cyan/30' : 'border-terminal-border'}`}>
      <div className="text-xs text-terminal-text-muted uppercase tracking-wider font-semibold mb-2">
        {label}
      </div>
      <div className={`text-2xl font-mono font-bold ${valueClass ?? 'text-terminal-text'}`}>
        {value}
      </div>
    </div>
  );
}

function DataRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-xs">
      <span className="text-terminal-text-muted">{label}</span>
      <span className="font-mono text-terminal-text-secondary">{value}</span>
    </div>
  );
}
