import { AlertTriangle, CheckCircle2, Clock3, Loader2, ShieldCheck } from 'lucide-react';
import { clsx } from 'clsx';
import { Link } from 'react-router-dom';
import { useBuildCertificate, useCertificate, useReadiness } from '../../hooks/useInvestigation';
import type { CertificateLifecycleStatus } from '../../types/investigation';

const STOP_LABELS: Record<string, string> = {
  OUTCOME_RESOLUTION: 'Outcome Resolution',
  EVIDENCE_THRESHOLD: 'Evidence Threshold',
  SPONSOR_DEFINED: 'Sponsor Defined',
};

function getStepStates(certStatus: CertificateLifecycleStatus | null) {
  if (!certStatus) {
    return { ready: 'pending', anchored: 'pending', issued: 'pending' } as const;
  }

  switch (certStatus) {
    case 'ISSUED':
    case 'ANCHORED':
      return { ready: 'reached', anchored: 'reached', issued: 'reached' } as const;
    case 'READY':
      return { ready: 'reached', anchored: 'active', issued: 'pending' } as const;
    default:
      return { ready: 'pending', anchored: 'pending', issued: 'pending' } as const;
  }
}

function Step({
  label,
  state,
  timestamp,
}: {
  label: string;
  state: 'reached' | 'active' | 'pending';
  timestamp: string | null;
}) {
  const circleClass =
    state === 'reached'
      ? 'border-[var(--e-green-600)] bg-[var(--e-green-50)] text-[var(--e-green-600)]'
      : state === 'active'
        ? 'border-[var(--e-purple-500)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)]'
        : 'border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] text-[var(--e-text-disabled)]';

  return (
    <div className="flex min-w-[110px] flex-col items-center gap-2">
      <div
        className={clsx(
          'flex h-10 w-10 items-center justify-center rounded-full border-2',
          circleClass,
          state === 'active' && 'animate-pulse',
        )}
      >
        {state === 'reached' ? <CheckCircle2 className="h-5 w-5" /> : <Clock3 className="h-4 w-4" />}
      </div>
      <div
        className={clsx(
          'text-[12px] font-semibold uppercase tracking-[0.04em]',
          state === 'reached'
            ? 'text-[var(--e-green-600)]'
            : state === 'active'
              ? 'text-[var(--e-purple-700)]'
              : 'text-[var(--e-text-muted)]',
        )}
      >
        {label}
      </div>
      <div className="min-h-[14px] font-mono text-[10px] tabular-nums text-[var(--e-text-muted)]">
        {timestamp ? new Date(timestamp).toLocaleString() : '—'}
      </div>
    </div>
  );
}

function Connector({ reached }: { reached: boolean }) {
  return (
    <div className="flex min-w-[40px] flex-1 items-center" style={{ marginTop: -28 }}>
      <div className={clsx('h-0.5 w-full rounded-full', reached ? 'bg-[var(--e-green-600)]' : 'bg-[var(--e-border-secondary)]')} />
    </div>
  );
}

export function ReadinessCertificatePanel({ investigationId }: { investigationId: string }) {
  const { readiness, isLoading: readinessLoading } = useReadiness(investigationId);
  const { certificate } = useCertificate(investigationId);
  const buildCertificate = useBuildCertificate(investigationId);

  if (readinessLoading) {
    return (
      <div className="flex items-center justify-center py-10 text-[var(--e-text-muted)]">
        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
        Loading readiness…
      </div>
    );
  }

  if (!readiness) return null;

  const isReady = readiness.stop_condition_status === 'READY';
  const hasCertificate = readiness.has_certificate;
  const certificateStatus = certificate?.certificate_status ?? readiness.certificate_status;
  const steps = getStepStates(hasCertificate ? certificateStatus : null);

  return (
    <div className="space-y-4">
      <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
        <div className="flex items-center gap-2 border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-3">
          <h3 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
            Stop Condition Readiness
          </h3>
          {readiness.stop_condition_evaluated_at ? (
            <span className="ml-auto font-mono text-[10px] text-[var(--e-text-muted)]">
              evaluated {new Date(readiness.stop_condition_evaluated_at).toLocaleString()}
            </span>
          ) : null}
        </div>

        <div className="space-y-4 px-5 py-5">
          <span
            className={clsx(
              'inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-[13px] font-semibold',
              isReady
                ? 'border-[color:oklch(0.545_0.170_152_/_0.18)] bg-[var(--e-green-50)] text-[var(--e-green-600)]'
                : 'border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] text-[var(--e-text-muted)]',
            )}
          >
            <span
              className={clsx(
                'h-2 w-2 rounded-full',
                isReady ? 'bg-[var(--e-green-600)]' : 'bg-[var(--e-text-disabled)]',
              )}
            />
            {readiness.stop_condition_status ?? 'NOT_EVALUATED'}
          </span>

          <div className="grid grid-cols-[120px_1fr] gap-x-4 gap-y-2 text-[13px]">
            <div className="text-[var(--e-text-muted)]">Stop Condition</div>
            <div className="text-[var(--e-text-primary)]">
              {STOP_LABELS[readiness.stop_condition] ?? readiness.stop_condition}
            </div>
            <div className="text-[var(--e-text-muted)]">Detail</div>
            <div className="text-[var(--e-text-primary)]">{readiness.stop_condition_reason ?? '—'}</div>
            <div className="text-[var(--e-text-muted)]">Last Evaluated</div>
            <div className="font-mono text-[var(--e-text-primary)]">
              {readiness.stop_condition_evaluated_at
                ? new Date(readiness.stop_condition_evaluated_at).toLocaleString()
                : '—'}
            </div>
          </div>
        </div>
      </section>

      {isReady && !hasCertificate ? (
        <div className="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-[var(--e-purple-200)] bg-[var(--e-purple-50)] px-5 py-4">
          <div className="flex min-w-0 items-start gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full border border-[var(--e-purple-200)] bg-white text-[var(--e-purple-700)]">
              <ShieldCheck className="h-4 w-4" />
            </div>
            <div className="min-w-0 text-[13px] leading-6 text-[var(--e-text-secondary)]">
              <strong className="text-[var(--e-text-primary)]">Stop condition met.</strong> This
              investigation is ready for certificate issuance. The certificate will be queued for
              the next 00:00 UTC batch-anchor cycle.
            </div>
          </div>

          <button
            type="button"
            onClick={() => buildCertificate.mutate()}
            disabled={buildCertificate.isPending}
            className="inline-flex h-10 items-center gap-2 rounded-lg bg-[var(--e-purple-500)] px-4 text-[13px] font-semibold text-[var(--e-text-inverse)] transition hover:bg-[var(--e-purple-600)] disabled:cursor-not-allowed disabled:bg-[var(--e-purple-200)] disabled:text-[var(--e-text-disabled)]"
          >
            {buildCertificate.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />}
            Build Certificate
          </button>
        </div>
      ) : null}

      {buildCertificate.isError ? (
        <div className="flex items-center gap-3 rounded-lg border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] px-4 py-3 text-[13px] text-[var(--e-red-600)]">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          {(buildCertificate.error as Error)?.message ?? 'Certificate build failed'}
        </div>
      ) : null}

      <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
        <div className="flex items-center gap-2 border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-3">
          <h3 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
            Certificate Lifecycle
          </h3>
          <span className="ml-auto text-[11px] text-[var(--e-text-muted)]">
            {certificate ? certificate.certificate_id.slice(0, 16) : isReady ? 'Awaiting build' : 'Awaiting readiness'}
          </span>
        </div>

        <div className="px-6 py-6">
          <div className="flex items-start justify-center">
            <Step label="READY" state={steps.ready} timestamp={certificate?.ready_at ?? null} />
            <Connector reached={steps.anchored === 'reached'} />
            <Step label="ANCHORED" state={steps.anchored} timestamp={certificate?.anchored_at ?? null} />
            <Connector reached={steps.issued === 'reached'} />
            <Step label="ISSUED" state={steps.issued} timestamp={certificate?.issued_at ?? null} />
          </div>

          {certificateStatus === 'READY' && hasCertificate ? (
            <div className="mt-4 text-center text-[12px] text-[var(--e-text-muted)]">
              Queued for next 00:00 UTC batch-anchor cycle
            </div>
          ) : null}
        </div>

        {certificate ? (
          <>
            <div className="border-t border-[var(--e-border-secondary)] px-5 py-4">
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <div className="rounded-md border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-3 py-3">
                  <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-text-muted)]">
                    Certificate ID
                  </div>
                  <div className="font-mono text-[12px] text-[var(--e-text-primary)]">
                    {certificate.certificate_id}
                  </div>
                </div>
                <div className="rounded-md border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-3 py-3">
                  <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-text-muted)]">
                    Status
                  </div>
                  <div className="font-mono text-[12px] text-[var(--e-text-primary)]">
                    {certificate.certificate_status}
                  </div>
                </div>
                <div className="rounded-md border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-3 py-3">
                  <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-text-muted)]">
                    Hash
                  </div>
                  <div className="font-mono text-[12px] text-[var(--e-text-primary)]">
                    {certificate.certificate_hash}
                  </div>
                </div>
                <div className="rounded-md border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-3 py-3">
                  <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-text-muted)]">
                    Anchor Hash
                  </div>
                  <div className="font-mono text-[12px] text-[var(--e-text-primary)]">
                    {certificate.batch_anchor_hash ?? '—'}
                  </div>
                </div>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3 border-t border-[var(--e-border-secondary)] px-5 py-4">
              <span
                className={clsx(
                  'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[12px] font-semibold',
                  certificate.routing_decision === 'ALLOWED'
                    ? 'border-[color:oklch(0.545_0.170_152_/_0.18)] bg-[var(--e-green-50)] text-[var(--e-green-600)]'
                    : 'border-[color:oklch(0.708_0.136_62_/_0.20)] bg-[color:oklch(0.708_0.136_62_/_0.10)] text-[var(--e-orange-600)]',
                )}
              >
                <span
                  className={clsx(
                    'h-2 w-2 rounded-full',
                    certificate.routing_decision === 'ALLOWED'
                      ? 'bg-[var(--e-green-600)]'
                      : 'bg-[var(--e-orange-600)]',
                  )}
                />
                {certificate.routing_decision.replace(/_/g, ' ')}
              </span>
              <span className="text-[12px] leading-5 text-[var(--e-text-secondary)]">
                {certificate.routing_reason}
              </span>
            </div>

            <div className="flex flex-wrap gap-2 border-t border-[var(--e-border-secondary)] px-5 py-4">
              <Link
                to="/certificates"
                className="inline-flex h-10 items-center gap-2 rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 text-[13px] font-semibold text-[var(--e-text-secondary)] no-underline transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]"
              >
                <ShieldCheck className="h-4 w-4" />
                Certificates Ledger
              </Link>
              <Link
                to={`/verify?certificate=${encodeURIComponent(certificate.certificate_id)}`}
                className="inline-flex h-10 items-center gap-2 rounded-lg bg-[var(--e-purple-500)] px-4 text-[13px] font-semibold text-[var(--e-text-inverse)] no-underline transition hover:bg-[var(--e-purple-600)]"
              >
                <ShieldCheck className="h-4 w-4" />
                Open Verify
              </Link>
            </div>

            {certificate.routing_decision === 'REVIEW_REQUIRED' ? (
              <div className="border-t border-[var(--e-border-secondary)] bg-[color:oklch(0.708_0.136_62_/_0.10)] px-5 py-4 text-[12px] leading-5 text-[var(--e-orange-600)]">
                Routing decision: REVIEW_REQUIRED — coherence gate evaluation triggered. Batch-anchor progression is not blocked by routing decision in the current implementation.
              </div>
            ) : null}
          </>
        ) : null}
      </section>
    </div>
  );
}

export default ReadinessCertificatePanel;
