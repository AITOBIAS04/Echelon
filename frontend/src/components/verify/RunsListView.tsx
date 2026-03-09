import { useState } from 'react';
import { ChevronLeft, ChevronRight, FlaskConical, X } from 'lucide-react';
import { clsx } from 'clsx';
import type { VerificationRun, VerificationRunStatus } from '../../types/verification';
import { ACTIVE_STATUSES } from '../../types/verification';

const PAGE_SIZE = 20;

function statusChipClass(status: VerificationRunStatus): string {
  if (status === 'COMPLETED') return 'border-[color:oklch(0.545_0.170_152_/_0.18)] bg-[var(--e-green-50)] text-[var(--e-green-600)]';
  if (status === 'FAILED') return 'border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] text-[var(--e-red-600)]';
  if (status === 'PENDING') return 'border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] text-[var(--e-text-muted)]';
  return 'border-[var(--e-purple-200)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)]';
}

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

function showProgress(status: VerificationRunStatus): boolean {
  return ACTIVE_STATUSES.includes(status) || status === 'COMPLETED';
}

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
  const completed = runs.filter((run) => run.status === 'COMPLETED').length;
  const active = runs.filter((run) => ACTIVE_STATUSES.includes(run.status)).length;
  const avgCompletion =
    runs.length > 0
      ? Math.round(
          (runs.reduce((sum, run) => sum + (run.total > 0 ? run.progress / run.total : 0), 0) / runs.length) *
            100,
        )
      : 0;

  if (isLoading && runs.length === 0) {
    return (
      <div className="space-y-4">
        <div className="grid gap-3 md:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <div
              key={index}
              className="h-24 animate-pulse rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)]"
            />
          ))}
        </div>
        {Array.from({ length: 5 }).map((_, index) => (
          <div
            key={index}
            className="h-16 animate-pulse rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)]"
          />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-bg-card)] px-6 py-8 text-center shadow-[var(--e-shadow-xs)]">
        <FlaskConical className="mx-auto mb-3 h-8 w-8 text-[var(--e-red-600)]" />
        <p className="text-[14px] font-semibold text-[var(--e-red-600)]">Failed to load verification runs</p>
        <p className="mt-1 text-[13px] text-[var(--e-text-secondary)]">{error.message}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-3 md:grid-cols-4">
        <RunStatCard label="Visible Runs" value={runs.length} />
        <RunStatCard label="Active" value={active} tone="info" />
        <RunStatCard label="Completed" value={completed} tone="success" />
        <RunStatCard
          label="Avg Completion"
          value={runs.length > 0 ? `${avgCompletion}%` : '—'}
          tone={avgCompletion >= 80 ? 'success' : avgCompletion >= 40 ? 'warning' : undefined}
        />
      </div>

      <div className="flex flex-col gap-3 rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] p-4 shadow-[var(--e-shadow-xs)] sm:flex-row sm:flex-wrap sm:items-center">
        <select
          className="h-11 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 text-[13px] text-[var(--e-text-secondary)] outline-none transition focus:border-[var(--e-purple-500)]"
          value={filters.status ?? ''}
          onChange={(e) => {
            const val = e.target.value as VerificationRunStatus | '';
            onFiltersChange({ ...filters, status: val || undefined });
            onOffsetChange(0);
          }}
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        <input
          type="text"
          className="h-11 w-full rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 text-[13px] text-[var(--e-text-primary)] outline-none transition placeholder:text-[var(--e-text-muted)] focus:border-[var(--e-purple-500)] sm:w-56"
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

        {hasFilters ? (
          <button
            className="inline-flex h-11 items-center gap-2 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 text-[12px] font-semibold text-[var(--e-text-secondary)] transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]"
            onClick={() => {
              setConstructInput('');
              onFiltersChange({});
              onOffsetChange(0);
            }}
          >
            <X className="h-3.5 w-3.5" />
            Clear
          </button>
        ) : null}
      </div>

      {runs.length === 0 ? (
        <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-8 py-12 text-center shadow-[var(--e-shadow-xs)]">
          <FlaskConical className="mx-auto mb-4 h-10 w-10 text-[var(--e-text-muted)]" aria-hidden="true" />
          <p className="text-[14px] font-semibold text-[var(--e-text-primary)]">No verification runs yet</p>
          <p className="mt-1 text-[13px] text-[var(--e-text-secondary)]">
            Start a verification run to benchmark a construct and generate a public calibration certificate.
          </p>
        </div>
      ) : (
        <>
          <div className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
            <table className="min-w-full border-collapse">
              <thead>
                <tr className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] text-left">
                  <th className="px-4 py-3 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Construct</th>
                  <th className="px-4 py-3 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Status</th>
                  <th className="px-4 py-3 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Progress</th>
                  <th className="px-4 py-3 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Created</th>
                  <th className="px-4 py-3 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Action</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <tr
                    key={run.run_id}
                    className="cursor-pointer border-b border-[var(--e-border-secondary)] transition hover:bg-[var(--e-bg-hover)] last:border-b-0"
                    onClick={() => onSelectRun(run.run_id)}
                  >
                    <td className="px-4 py-4">
                      <div className="space-y-1">
                        <div className="text-[13px] font-semibold text-[var(--e-text-primary)]">{run.construct_id}</div>
                        <div className="font-mono text-[11px] text-[var(--e-text-muted)]">{run.repo_url}</div>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <span
                        className={clsx(
                          'inline-flex rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.04em]',
                          statusChipClass(run.status),
                          ACTIVE_STATUSES.includes(run.status) && 'animate-pulse',
                        )}
                      >
                        {run.status}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      {showProgress(run.status) ? (
                        <div className="flex items-center gap-2">
                          <div className="h-1.5 w-24 overflow-hidden rounded-full bg-[var(--e-bg-sunken)]">
                            <div
                              className="h-full rounded-full bg-[var(--e-purple-500)] transition-all duration-500"
                              style={{ width: run.total > 0 ? `${(run.progress / run.total) * 100}%` : '0%' }}
                            />
                          </div>
                          <span className="font-mono text-[11px] tabular-nums text-[var(--e-text-muted)]">
                            {run.progress}/{run.total}
                          </span>
                        </div>
                      ) : (
                        <span className="text-[11px] text-[var(--e-text-muted)]">—</span>
                      )}
                    </td>
                    <td className="px-4 py-4 font-mono text-[12px] text-[var(--e-text-secondary)]">
                      {relativeTime(run.created_at)}
                    </td>
                    <td className="px-4 py-4">
                      <button
                        className="inline-flex h-9 items-center rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 text-[12px] font-semibold text-[var(--e-text-secondary)] transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]"
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

          {total > PAGE_SIZE && (
            <div className="flex items-center justify-between text-[12px] text-[var(--e-text-muted)]">
              <span>
                Showing {rangeStart}–{rangeEnd} of {total}
              </span>
              <div className="flex items-center gap-2">
                <button
                  className="inline-flex h-9 items-center gap-1 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 text-[12px] font-semibold text-[var(--e-text-secondary)] transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)] disabled:cursor-not-allowed disabled:opacity-50"
                  disabled={offset === 0}
                  onClick={() => onOffsetChange(Math.max(0, offset - PAGE_SIZE))}
                >
                  <ChevronLeft className="h-3.5 w-3.5" />
                  Prev
                </button>
                <button
                  className="inline-flex h-9 items-center gap-1 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 text-[12px] font-semibold text-[var(--e-text-secondary)] transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)] disabled:cursor-not-allowed disabled:opacity-50"
                  disabled={offset + PAGE_SIZE >= total}
                  onClick={() => onOffsetChange(offset + PAGE_SIZE)}
                >
                  Next
                  <ChevronRight className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function RunStatCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: string | number;
  tone?: 'success' | 'warning' | 'danger' | 'info';
}) {
  return (
    <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-3 shadow-[var(--e-shadow-xs)]">
      <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">{label}</div>
      <div
        className={clsx(
          'font-mono text-[24px] font-bold leading-8 tabular-nums',
          tone === 'success'
            ? 'text-[var(--e-green-600)]'
            : tone === 'warning'
              ? 'text-[var(--e-orange-600)]'
              : tone === 'danger'
                ? 'text-[var(--e-red-600)]'
                : tone === 'info'
                  ? 'text-[var(--e-purple-700)]'
                  : 'text-[var(--e-text-primary)]',
        )}
      >
        {value}
      </div>
    </div>
  );
}
