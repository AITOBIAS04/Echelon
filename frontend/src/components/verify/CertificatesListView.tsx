import { Award, ChevronDown, ChevronLeft, ChevronRight, Search, X } from 'lucide-react';
import { clsx } from 'clsx';
import type { CertificateSummary, CertFilters } from '../../types/verification';

const PAGE_SIZE = 20;

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
  const pageComposite =
    certificates.length > 0
      ? certificates.reduce((sum, cert) => sum + cert.composite_score, 0) / certificates.length
      : 0;
  const pageBrier =
    certificates.length > 0
      ? certificates.reduce((sum, cert) => sum + cert.brier, 0) / certificates.length
      : 0;
  const pageReplays = certificates.reduce((sum, cert) => sum + cert.replay_count, 0);

  if (isLoading && certificates.length === 0) {
    return (
      <div className="space-y-4">
        <div className="grid gap-3 md:grid-cols-3">
          {Array.from({ length: 3 }).map((_, index) => (
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
        <Award className="mx-auto mb-3 h-8 w-8 text-[var(--e-red-600)]" aria-hidden="true" />
        <p className="text-[14px] font-semibold text-[var(--e-red-600)]">Failed to load certificates</p>
        <p className="mt-1 text-[13px] text-[var(--e-text-secondary)]">{error.message}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-3 md:grid-cols-3">
        <StatCard label="Visible Certificates" value={certificates.length} />
        <StatCard
          label="Average Composite"
          value={certificates.length > 0 ? pageComposite.toFixed(3) : '—'}
          tone={pageComposite > 0.7 ? 'success' : pageComposite > 0.4 ? 'warning' : 'danger'}
        />
        <StatCard
          label="Replay Coverage"
          value={pageReplays > 0 ? String(pageReplays) : '—'}
          detail={certificates.length > 0 ? `Avg Brier ${pageBrier.toFixed(3)}` : 'No certificates in view'}
        />
      </div>

      <div className="flex flex-col gap-3 rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] p-4 shadow-[var(--e-shadow-xs)] sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--e-text-muted)]" />
          <input
            type="text"
            className="h-11 w-full rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] pl-10 pr-4 text-[13px] text-[var(--e-text-primary)] outline-none transition placeholder:text-[var(--e-text-muted)] focus:border-[var(--e-purple-500)] focus:ring-2 focus:ring-[color:oklch(0.530_0.230_295_/_0.12)]"
            placeholder="Filter by construct ID"
            value={constructFilter}
            onChange={(e) => onConstructFilterChange(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-2">
          <select
            className="h-11 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 text-[13px] text-[var(--e-text-secondary)] outline-none transition focus:border-[var(--e-purple-500)]"
            value={sort}
            onChange={(e) => onSortChange(e.target.value as CertFilters['sort'])}
          >
            <option value="brier_asc">Lowest Brier</option>
            <option value="created_desc">Newest First</option>
          </select>
          {hasFilter ? (
            <button
              className="inline-flex h-11 items-center gap-2 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 text-[12px] font-semibold text-[var(--e-text-secondary)] transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]"
              onClick={() => onConstructFilterChange('')}
            >
              <X className="h-3.5 w-3.5" />
              Clear
            </button>
          ) : null}
        </div>
      </div>

      {certificates.length === 0 ? (
        <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-8 py-12 text-center shadow-[var(--e-shadow-xs)]">
          <Award className="mx-auto mb-4 h-10 w-10 text-[var(--e-text-muted)]" aria-hidden="true" />
          <p className="text-[14px] font-semibold text-[var(--e-text-primary)]">No certificates found</p>
          <p className="mt-1 text-[13px] text-[var(--e-text-secondary)]">
            Adjust the construct filter or check back once new verification certificates are issued.
          </p>
        </div>
      ) : (
        <>
          <div className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
            <table className="min-w-full border-collapse">
              <thead>
                <tr className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] text-left">
                  <th className="px-4 py-3 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Construct</th>
                  <th className="px-4 py-3 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                    <button
                      className="inline-flex items-center gap-1 text-inherit transition hover:text-[var(--e-text-primary)]"
                      onClick={() => onSortChange('brier_asc')}
                    >
                      Brier Score
                      {sort === 'brier_asc' && <ChevronDown className="h-3 w-3 text-[var(--e-purple-700)]" />}
                    </button>
                  </th>
                  <th className="px-4 py-3 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Composite</th>
                  <th className="px-4 py-3 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Replays</th>
                  <th className="px-4 py-3 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                    <button
                      className="inline-flex items-center gap-1 text-inherit transition hover:text-[var(--e-text-primary)]"
                      onClick={() => onSortChange('created_desc')}
                    >
                      Created
                      {sort === 'created_desc' && <ChevronDown className="h-3 w-3 text-[var(--e-purple-700)]" />}
                    </button>
                  </th>
                </tr>
              </thead>
              <tbody>
                {certificates.map((cert) => (
                  <tr
                    key={cert.id}
                    className="cursor-pointer border-b border-[var(--e-border-secondary)] transition hover:bg-[var(--e-bg-hover)] last:border-b-0"
                    onClick={() => onSelectCert(cert.id)}
                  >
                    <td className="px-4 py-4">
                      <div className="space-y-1">
                        <div className="text-[13px] font-semibold text-[var(--e-text-primary)]">{cert.construct_id}</div>
                        <div className="font-mono text-[11px] text-[var(--e-text-muted)]">{cert.domain}</div>
                      </div>
                    </td>
                    <td className={clsx('px-4 py-4 font-mono text-[13px] font-semibold tabular-nums', brierColour(cert.brier))}>
                      {cert.brier.toFixed(3)}
                    </td>
                    <td className={clsx('px-4 py-4 font-mono text-[13px] font-semibold tabular-nums', compositeColour(cert.composite_score))}>
                      {cert.composite_score.toFixed(3)}
                    </td>
                    <td className="px-4 py-4 font-mono text-[12px] tabular-nums text-[var(--e-text-secondary)]">
                      {cert.replay_count}
                    </td>
                    <td className="px-4 py-4 font-mono text-[12px] tabular-nums text-[var(--e-text-secondary)]">
                      {new Date(cert.created_at).toLocaleDateString()}
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

function StatCard({
  label,
  value,
  detail,
  tone,
}: {
  label: string;
  value: string | number;
  detail?: string;
  tone?: 'success' | 'warning' | 'danger';
}) {
  return (
    <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-3 shadow-[var(--e-shadow-xs)]">
      <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
        {label}
      </div>
      <div
        className={clsx(
          'font-mono text-[24px] font-bold leading-8 tabular-nums',
          tone === 'success'
            ? 'text-[var(--e-green-600)]'
            : tone === 'warning'
              ? 'text-[var(--e-orange-600)]'
              : tone === 'danger'
                ? 'text-[var(--e-red-600)]'
                : 'text-[var(--e-text-primary)]',
        )}
      >
        {value}
      </div>
      {detail ? <div className="mt-1 text-[12px] text-[var(--e-text-muted)]">{detail}</div> : null}
    </div>
  );
}
