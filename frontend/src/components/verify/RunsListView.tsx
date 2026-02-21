/**
 * RunsListView — Table of verification runs with filters, pagination, status chips.
 */

import { useState } from 'react';
import { ShieldCheck, ChevronLeft, ChevronRight, X } from 'lucide-react';
import { clsx } from 'clsx';
import type { VerificationRun, VerificationRunStatus } from '../../types/verification';
import { ACTIVE_STATUSES } from '../../types/verification';

const PAGE_SIZE = 20;

// ── Status chip mapping ──────────────────────────────────────────────────

function statusChipClass(status: VerificationRunStatus): string {
  if (status === 'COMPLETED') return 'chip chip-success';
  if (status === 'FAILED') return 'chip chip-danger';
  if (status === 'PENDING') return 'chip chip-neutral';
  // Active states
  return 'chip chip-info animate-pulse';
}

// ── Relative time ────────────────────────────────────────────────────────

function relativeTime(iso: string): string {
  const now = Date.now();
  const then = new Date(iso).getTime();
  const diffMs = now - then;
  const diffSec = Math.floor(diffMs / 1000);
  if (diffSec < 60) return `${diffSec}s ago`;
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin} min ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.floor(diffHr / 24);
  return `${diffDay}d ago`;
}

// ── Progress bar ─────────────────────────────────────────────────────────

function showProgress(status: VerificationRunStatus): boolean {
  return ACTIVE_STATUSES.includes(status) || status === 'COMPLETED';
}

// ── Component ────────────────────────────────────────────────────────────

interface RunsListViewProps {
  runs: VerificationRun[];
  total: number;
  isLoading: boolean;
  error: Error | null;
  filters: { status?: VerificationRunStatus; construct_id?: string };
  onFiltersChange: (f: { status?: VerificationRunStatus; construct_id?: string }) => void;
  offset: number;
  onOffsetChange: (offset: number) => void;
  onSelectRun: (runId: string) => void;
}

const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: '', label: 'All Statuses' },
  { value: 'PENDING', label: 'Pending' },
  { value: 'INGESTING', label: 'Ingesting' },
  { value: 'INVOKING', label: 'Invoking' },
  { value: 'SCORING', label: 'Scoring' },
  { value: 'CERTIFYING', label: 'Certifying' },
  { value: 'COMPLETED', label: 'Completed' },
  { value: 'FAILED', label: 'Failed' },
];

export function RunsListView({
  runs,
  total,
  isLoading,
  error,
  filters,
  onFiltersChange,
  offset,
  onOffsetChange,
  onSelectRun,
}: RunsListViewProps) {
  const [constructInput, setConstructInput] = useState(filters.construct_id ?? '');

  const hasFilters = !!filters.status || !!filters.construct_id;

  const rangeStart = offset + 1;
  const rangeEnd = Math.min(offset + PAGE_SIZE, total);

  // Loading skeleton
  if (isLoading && runs.length === 0) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-10 bg-terminal-panel border border-terminal-border rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="bg-terminal-panel border border-status-danger/20 rounded-lg p-6 text-center">
        <p className="text-xs text-status-danger">Failed to load verification runs: {error.message}</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Filter bar */}
      <div className="flex items-center gap-2 flex-wrap">
        <select
          className="terminal-input"
          value={filters.status ?? ''}
          onChange={(e) => {
            const val = e.target.value as VerificationRunStatus | '';
            onFiltersChange({ ...filters, status: val || undefined });
            onOffsetChange(0);
          }}
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>

        <input
          type="text"
          className="terminal-input w-48"
          placeholder="Filter by construct ID..."
          value={constructInput}
          onChange={(e) => setConstructInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              onFiltersChange({ ...filters, construct_id: constructInput || undefined });
              onOffsetChange(0);
            }
          }}
          onBlur={() => {
            onFiltersChange({ ...filters, construct_id: constructInput || undefined });
            onOffsetChange(0);
          }}
        />

        {hasFilters && (
          <button
            className="btn-ghost text-[10px]"
            onClick={() => {
              setConstructInput('');
              onFiltersChange({});
              onOffsetChange(0);
            }}
          >
            <X className="w-3 h-3" />
            Clear
          </button>
        )}
      </div>

      {/* Empty state */}
      {runs.length === 0 ? (
        <div className="bg-terminal-panel border border-terminal-border rounded-lg p-8 text-center">
          <ShieldCheck className="w-8 h-8 text-terminal-text-muted mx-auto mb-3" aria-hidden="true" />
          <p className="text-xs text-terminal-text-muted">No verification runs yet</p>
        </div>
      ) : (
        <>
          {/* Table */}
          <div className="overflow-x-auto">
            <table className="terminal-table">
              <thead>
                <tr>
                  <th>Construct ID</th>
                  <th>Status</th>
                  <th>Progress</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <tr
                    key={run.run_id}
                    className="cursor-pointer"
                    onClick={() => onSelectRun(run.run_id)}
                  >
                    <td className="font-mono text-echelon-cyan text-[11px]">
                      {run.construct_id}
                    </td>
                    <td>
                      <span className={statusChipClass(run.status)}>
                        {run.status}
                      </span>
                    </td>
                    <td>
                      {showProgress(run.status) ? (
                        <div className="flex items-center gap-2">
                          <div className="h-1.5 w-24 bg-terminal-border/30 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-echelon-cyan rounded-full transition-all duration-500"
                              style={{ width: run.total > 0 ? `${(run.progress / run.total) * 100}%` : '0%' }}
                            />
                          </div>
                          <span className="font-mono text-[10px] text-terminal-text-muted tabular-nums">
                            {run.progress}/{run.total}
                          </span>
                        </div>
                      ) : (
                        <span className="text-terminal-text-muted text-[10px]">—</span>
                      )}
                    </td>
                    <td className="font-mono text-terminal-text-muted text-[11px]">
                      {relativeTime(run.created_at)}
                    </td>
                    <td>
                      <button
                        className="btn-ghost text-[10px]"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectRun(run.run_id);
                        }}
                      >
                        Details
                      </button>
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
