import { useEffect } from 'react';
import type { VerificationRun } from '../../types/verification';
import { ACTIVE_STATUSES } from '../../types/verification';

function statusChipClass(status: string): string {
  if (status === 'COMPLETED') return 'border-[color:oklch(0.545_0.170_152_/_0.18)] bg-[var(--e-green-50)] text-[var(--e-green-600)]';
  if (status === 'FAILED') return 'border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] text-[var(--e-red-600)]';
  if (status === 'PENDING') return 'border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] text-[var(--e-text-muted)]';
  return 'border-[var(--e-purple-200)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)]';
}

interface RunDetailDrawerProps {
  run: VerificationRun | null;
  onClose: () => void;
  onViewCertificate: (certificateId: string) => void;
}

export function RunDetailDrawer({ run, onClose, onViewCertificate }: RunDetailDrawerProps) {
  useEffect(() => {
    if (!run) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [run, onClose]);

  if (!run) return null;

  const isActive = ACTIVE_STATUSES.includes(run.status);

  return (
    <>
      <div
        className="fixed inset-0 z-[300] bg-[color:oklch(0.205_0.015_265_/_0.14)] backdrop-blur-sm"
        onClick={onClose}
      />

      <div
        className="fixed right-6 top-[72px] z-[310] flex max-h-[calc(100vh-96px)] w-[440px] flex-col overflow-hidden rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-lg)]"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-labelledby="run-drawer-title"
      >
        <div className="flex items-start justify-between border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-4">
          <div className="min-w-0">
            <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              Verification Run
            </div>
            <div className="flex items-center gap-2">
              <span id="run-drawer-title" className="truncate text-[15px] font-semibold text-[var(--e-text-primary)]">
                {run.construct_id}
              </span>
              <span className={`inline-flex rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.04em] ${statusChipClass(run.status)}`}>
                {run.status}
              </span>
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
          <section className="space-y-3 rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] p-4">
            <DataRow label="Repository" value={run.repo_url} multiline />
            <DataRow label="Created" value={new Date(run.created_at).toLocaleString()} />
            <DataRow label="Updated" value={new Date(run.updated_at).toLocaleString()} />
          </section>

          {(isActive || run.status === 'COMPLETED') && run.total > 0 ? (
            <section className="space-y-3 rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] p-4">
              <div className="flex justify-between text-[12px]">
                <span className="font-semibold uppercase tracking-[0.05em] text-[var(--e-text-muted)]">Progress</span>
                <span className="font-mono tabular-nums text-[var(--e-text-primary)]">
                  {run.progress} / {run.total} replays completed
                </span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-[var(--e-bg-sunken)]">
                <div
                  className="h-full rounded-full bg-[var(--e-purple-500)] transition-all duration-500"
                  style={{ width: `${(run.progress / run.total) * 100}%` }}
                  role="progressbar"
                  aria-valuenow={run.progress}
                  aria-valuemin={0}
                  aria-valuemax={run.total}
                />
              </div>
            </section>
          ) : null}

          {run.status === 'FAILED' && run.error ? (
            <section className="rounded-lg border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] p-4">
              <span className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-red-600)]">Error</span>
              <p className="mt-2 break-all font-mono text-[12px] text-[var(--e-red-600)]">{run.error}</p>
            </section>
          ) : null}

          {run.status === 'COMPLETED' && run.certificate_id ? (
            <button
              className="inline-flex h-11 w-full items-center justify-center rounded-md border border-[var(--e-purple-500)] bg-[var(--e-purple-500)] px-4 text-[13px] font-semibold text-white transition hover:bg-[var(--e-purple-400)]"
              onClick={() => onViewCertificate(run.certificate_id!)}
            >
              View Certificate
            </button>
          ) : null}
        </div>
      </div>
    </>
  );
}

function DataRow({
  label,
  value,
  multiline,
}: {
  label: string;
  value: string;
  multiline?: boolean;
}) {
  return (
    <div className="flex justify-between gap-4 text-[12px]">
      <span className="font-semibold uppercase tracking-[0.05em] text-[var(--e-text-muted)]">{label}</span>
      <span
        className={[
          'text-right font-mono text-[var(--e-text-secondary)]',
          multiline ? 'max-w-[250px] break-all' : '',
        ].join(' ')}
      >
        {value}
      </span>
    </div>
  );
}
