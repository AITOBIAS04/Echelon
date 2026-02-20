/**
 * CertificatesListView — Public certificate browser with sort, filter, pagination.
 */

import { useState } from 'react';
import { Award, ChevronLeft, ChevronRight, ChevronUp, ChevronDown, X } from 'lucide-react';
import type { CertificateSummary, CertFilters } from '../../types/verification';

const PAGE_SIZE = 20;

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

// ── Component ────────────────────────────────────────────────────────────

interface CertificatesListViewProps {
  certificates: CertificateSummary[];
  total: number;
  isLoading: boolean;
  error: Error | null;
  sort: CertFilters['sort'];
  onSortChange: (sort: CertFilters['sort']) => void;
  constructFilter: string;
  onConstructFilterChange: (val: string) => void;
  offset: number;
  onOffsetChange: (offset: number) => void;
  onSelectCert: (certId: string) => void;
}

export function CertificatesListView({
  certificates,
  total,
  isLoading,
  error,
  sort,
  onSortChange,
  constructFilter,
  onConstructFilterChange,
  offset,
  onOffsetChange,
  onSelectCert,
}: CertificatesListViewProps) {
  const rangeStart = offset + 1;
  const rangeEnd = Math.min(offset + PAGE_SIZE, total);
  const hasFilter = !!constructFilter;

  // Loading skeleton
  if (isLoading && certificates.length === 0) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-10 bg-terminal-panel border border-terminal-border rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  // Error
  if (error) {
    return (
      <div className="bg-terminal-panel border border-status-danger/20 rounded-lg p-6 text-center">
        <p className="text-xs text-status-danger">Failed to load certificates: {error.message}</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Filter bar */}
      <div className="flex items-center gap-2 flex-wrap">
        <input
          type="text"
          className="terminal-input w-48"
          placeholder="Filter by construct ID..."
          value={constructFilter}
          onChange={(e) => onConstructFilterChange(e.target.value)}
        />
        {hasFilter && (
          <button
            className="btn-ghost text-[10px]"
            onClick={() => onConstructFilterChange('')}
          >
            <X className="w-3 h-3" />
            Clear
          </button>
        )}
      </div>

      {/* Empty state */}
      {certificates.length === 0 ? (
        <div className="bg-terminal-panel border border-terminal-border rounded-lg p-8 text-center">
          <Award className="w-8 h-8 text-terminal-text-muted mx-auto mb-3" aria-hidden="true" />
          <p className="text-xs text-terminal-text-muted">No certificates found</p>
        </div>
      ) : (
        <>
          {/* Table */}
          <div className="overflow-x-auto">
            <table className="terminal-table">
              <thead>
                <tr>
                  <th>Construct ID</th>
                  <th>
                    <button
                      className="inline-flex items-center gap-1 hover:text-terminal-text transition-colors"
                      onClick={() => onSortChange('brier_asc')}
                    >
                      Brier Score
                      {sort === 'brier_asc' && <ChevronUp className="w-3 h-3 text-echelon-cyan" />}
                    </button>
                  </th>
                  <th>Composite Score</th>
                  <th>Replays</th>
                  <th>
                    <button
                      className="inline-flex items-center gap-1 hover:text-terminal-text transition-colors"
                      onClick={() => onSortChange('created_desc')}
                    >
                      Created
                      {sort === 'created_desc' && <ChevronDown className="w-3 h-3 text-echelon-cyan" />}
                    </button>
                  </th>
                </tr>
              </thead>
              <tbody>
                {certificates.map((cert) => (
                  <tr
                    key={cert.id}
                    className="cursor-pointer"
                    onClick={() => onSelectCert(cert.id)}
                  >
                    <td className="font-mono text-echelon-cyan text-[11px]">
                      {cert.construct_id}
                    </td>
                    <td className={`font-mono tabular-nums ${brierColour(cert.brier)}`}>
                      {cert.brier.toFixed(3)}
                    </td>
                    <td className={`font-mono tabular-nums ${compositeColour(cert.composite_score)}`}>
                      {cert.composite_score.toFixed(3)}
                    </td>
                    <td className="font-mono tabular-nums">
                      {cert.replay_count}
                    </td>
                    <td className="font-mono text-terminal-text-muted text-[11px]">
                      {new Date(cert.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {total > PAGE_SIZE && (
            <div className="flex items-center justify-between text-xs text-terminal-text-muted">
              <span>
                Showing {rangeStart}–{rangeEnd} of {total}
              </span>
              <div className="flex items-center gap-1">
                <button
                  className="btn-ghost text-[10px]"
                  disabled={offset === 0}
                  onClick={() => onOffsetChange(Math.max(0, offset - PAGE_SIZE))}
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                  Prev
                </button>
                <button
                  className="btn-ghost text-[10px]"
                  disabled={offset + PAGE_SIZE >= total}
                  onClick={() => onOffsetChange(offset + PAGE_SIZE)}
                >
                  Next
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
