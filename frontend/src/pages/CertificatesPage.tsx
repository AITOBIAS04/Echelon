import { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Award, ExternalLink, Loader2, ShieldCheck } from 'lucide-react';
import { clsx } from 'clsx';
import { EmptyState } from '../components/empty-states/EmptyState';
import { useCertificateGallery, type UnifiedCertificate } from '../hooks/useCertificateGallery';

type StatusFilter = 'all' | 'deployable' | 'not-deployable';

function RoutingBadge({ hint }: { hint: string | null | undefined }) {
  if (!hint) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-2.5 py-1 text-[11px] font-semibold text-[var(--e-text-muted)]">
        <span className="h-2 w-2 rounded-full bg-[var(--e-text-disabled)]" />
        Pending
      </span>
    );
  }

  const classes: Record<string, string> = {
    ALLOWED: 'border-[color:oklch(0.545_0.170_152_/_0.18)] bg-[var(--e-green-50)] text-[var(--e-green-600)]',
    REVIEW_REQUIRED: 'border-[color:oklch(0.708_0.136_62_/_0.20)] bg-[color:oklch(0.708_0.136_62_/_0.10)] text-[var(--e-orange-600)]',
    BLOCKED: 'border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] text-[var(--e-red-600)]',
  };

  return (
    <span className={clsx('inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold', classes[hint] ?? classes.ALLOWED)}>
      <span
        className={clsx(
          'h-2 w-2 rounded-full',
          hint === 'ALLOWED'
            ? 'bg-[var(--e-green-600)]'
            : hint === 'REVIEW_REQUIRED'
              ? 'bg-[var(--e-orange-600)]'
              : 'bg-[var(--e-red-600)]',
        )}
      />
      {hint.replace(/_/g, ' ')}
    </span>
  );
}

function GateBadge({ status }: { status: string | null | undefined }) {
  if (!status) return null;

  const classes: Record<string, string> = {
    PASSED: 'border-[color:oklch(0.545_0.170_152_/_0.18)] bg-[var(--e-green-50)] text-[var(--e-green-600)]',
    PENDING: 'border-[color:oklch(0.708_0.136_62_/_0.20)] bg-[color:oklch(0.708_0.136_62_/_0.10)] text-[var(--e-orange-600)]',
    FAILED: 'border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] text-[var(--e-red-600)]',
  };

  return (
    <span className={clsx('inline-flex rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em]', classes[status] ?? classes.PENDING)}>
      {status}
    </span>
  );
}

function TierBadge({ tier }: { tier: string }) {
  const enhanced = tier.toLowerCase() === 'enhanced';
  return (
    <span
      className={clsx(
        'inline-flex rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em]',
        enhanced
          ? 'border-[var(--e-purple-200)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)]'
          : 'border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] text-[var(--e-text-muted)]',
      )}
    >
      {tier}
    </span>
  );
}

function SourceBadge({ source }: { source: string }) {
  return (
    <span
      className={clsx(
        'inline-flex rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em]',
        source === 'theatre'
          ? 'border-[var(--e-purple-200)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)]'
          : 'border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] text-[var(--e-text-muted)]',
      )}
    >
      {source}
    </span>
  );
}

function StatCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone?: 'success' | 'warning';
}) {
  const valueClass =
    tone === 'success'
      ? 'text-[var(--e-green-600)]'
      : tone === 'warning'
        ? 'text-[var(--e-orange-600)]'
        : 'text-[var(--e-text-primary)]';

  return (
    <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-3 shadow-[var(--e-shadow-xs)]">
      <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
        {label}
      </div>
      <div className={clsx('font-mono text-[24px] font-bold leading-8 tabular-nums', valueClass)}>
        {value}
      </div>
    </div>
  );
}

function CertificateRow({ certificate }: { certificate: UnifiedCertificate }) {
  return (
    <tr className="border-b border-[var(--e-border-secondary)] align-top transition hover:bg-[var(--e-bg-hover)] last:border-b-0">
      <td className="px-4 py-4">
        <span className="font-mono text-[12px] font-semibold text-[var(--e-purple-700)]">
          {certificate.id.slice(0, 16)}
        </span>
      </td>
      <td className="px-4 py-4">
        <div className="space-y-1">
          <div className="text-[13px] font-semibold text-[var(--e-text-primary)]">
            {certificate.construct_id}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <SourceBadge source={certificate.source} />
            {certificate.theatre_id ? (
              <Link
                to={`/theatre/${certificate.theatre_id}`}
                className="text-[11px] font-medium text-[var(--e-text-muted)] no-underline transition hover:text-[var(--e-purple-700)]"
              >
                {certificate.theatre_id.slice(0, 12)}
              </Link>
            ) : null}
          </div>
        </div>
      </td>
      <td className="px-4 py-4">
        <RoutingBadge hint={certificate.routing_hint} />
      </td>
      <td className="px-4 py-4 text-right">
        <span className="font-mono text-[13px] font-semibold tabular-nums text-[var(--e-text-primary)]">
          {certificate.composite_score.toFixed(3)}
        </span>
      </td>
      <td className="px-4 py-4">
        <GateBadge status={certificate.coherence_gate_status} />
      </td>
      <td className="px-4 py-4">
        <TierBadge tier={certificate.verification_tier} />
      </td>
      <td className="px-4 py-4">
        <span className="font-mono text-[12px] tabular-nums text-[var(--e-text-secondary)]">
          {new Date(certificate.issued_at).toLocaleDateString()}
        </span>
      </td>
      <td className="px-4 py-4">
        <div className="flex justify-end gap-2">
          {certificate.theatre_id ? (
            <Link
              to={`/theatre/${certificate.theatre_id}`}
              className="inline-flex items-center gap-1 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 py-1.5 text-[11px] font-semibold text-[var(--e-text-secondary)] no-underline transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]"
            >
              <ExternalLink className="h-3 w-3" />
              View
            </Link>
          ) : null}
          <Link
            to={`/verify?certificate=${encodeURIComponent(certificate.id)}`}
            className="inline-flex items-center gap-1 rounded-md border border-[color:oklch(0.545_0.170_152_/_0.18)] bg-[var(--e-green-50)] px-3 py-1.5 text-[11px] font-semibold text-[var(--e-green-600)] no-underline transition hover:bg-[color:oklch(0.545_0.170_152_/_0.14)]"
          >
            <ShieldCheck className="h-3 w-3" />
            Verify
          </Link>
        </div>
      </td>
    </tr>
  );
}

function RightRail({ certificates }: { certificates: UnifiedCertificate[] }) {
  const recent = certificates.slice(0, 5);
  const deployableCount = certificates.filter((certificate) => certificate.is_deployable).length;
  const notDeployableCount = certificates.length - deployableCount;

  return (
    <div className="space-y-4">
      <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
        <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
          <h3 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
            Recent Certificates
          </h3>
        </div>
        <div className="px-4 py-3">
          {recent.length > 0 ? (
            recent.map((certificate) => (
              <div
                key={certificate.id}
                className="flex items-center justify-between border-b border-[var(--e-border-secondary)] py-2 last:border-b-0"
              >
                <div className="min-w-0">
                  <div className="truncate text-[12px] font-semibold text-[var(--e-text-primary)]">
                    {certificate.construct_id}
                  </div>
                  <div className="font-mono text-[10px] text-[var(--e-text-muted)]">
                    {new Date(certificate.issued_at).toLocaleDateString()}
                  </div>
                </div>
                <span
                  className={clsx(
                    'h-2 w-2 rounded-full',
                    certificate.routing_hint === 'ALLOWED'
                      ? 'bg-[var(--e-green-600)]'
                      : certificate.routing_hint === 'REVIEW_REQUIRED'
                        ? 'bg-[var(--e-orange-600)]'
                        : 'bg-[var(--e-text-disabled)]',
                  )}
                />
              </div>
            ))
          ) : (
            <div className="text-[12px] text-[var(--e-text-muted)]">No certificates yet.</div>
          )}
        </div>
      </section>

      <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
        <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
          <h3 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
            Deployment Readiness
          </h3>
        </div>
        <div className="space-y-3 px-4 py-4">
          {[
            { label: 'Deployable', count: deployableCount, color: 'bg-[var(--e-green-600)]' },
            { label: 'Not Ready', count: notDeployableCount, color: 'bg-[var(--e-orange-600)]' },
          ].map((row) => (
            <div key={row.label} className="flex items-center gap-3">
              <span className="w-20 text-[11px] text-[var(--e-text-secondary)]">{row.label}</span>
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-[var(--e-bg-sunken)]">
                <div
                  className={clsx('h-full rounded-full', row.color)}
                  style={{
                    width: certificates.length > 0 ? `${(row.count / certificates.length) * 100}%` : '0%',
                  }}
                />
              </div>
              <span className="w-6 text-right font-mono text-[10px] text-[var(--e-text-muted)]">
                {row.count}
              </span>
            </div>
          ))}
        </div>
      </section>

      <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
        <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
          <h3 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
            Source Coverage
          </h3>
        </div>
        <div className="px-4 py-4 text-[12px] leading-5 text-[var(--e-text-secondary)]">
          Currently showing <strong className="text-[var(--e-text-primary)]">theatre certificates</strong> only.
          Verification-source certificates remain deferred until the gallery hook merges them.
        </div>
      </section>
    </div>
  );
}

export function CertificatesPage() {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const { certificates, total, isLoading, error, isEmpty } = useCertificateGallery();

  const filtered = useMemo(() => {
    if (statusFilter === 'all') return certificates;
    if (statusFilter === 'deployable') return certificates.filter((certificate) => certificate.is_deployable);
    return certificates.filter((certificate) => !certificate.is_deployable);
  }, [certificates, statusFilter]);

  const deployableCount = certificates.filter((certificate) => certificate.is_deployable).length;
  const notDeployableCount = certificates.length - deployableCount;
  const allowedCount = certificates.filter((certificate) => certificate.routing_hint === 'ALLOWED').length;
  const reviewCount = certificates.filter((certificate) => certificate.routing_hint === 'REVIEW_REQUIRED').length;

  if (error) {
    return (
      <div className="p-6">
        <div className="mx-auto max-w-7xl rounded-lg border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] px-5 py-4 text-[13px] text-[var(--e-red-600)] shadow-[var(--e-shadow-xs)]">
          Failed to load certificates: {error.message}
        </div>
      </div>
    );
  }

  if (isEmpty) {
    return (
      <div className="p-6">
        <div className="mx-auto max-w-5xl">
          <EmptyState
            type="NOT_YET_GENERATED"
            icon={<Award className="h-6 w-6" />}
            title="No certificates issued yet"
            description="Certificates appear here after theatre settlement and verification. Verification-source rows remain deferred until the gallery hook is expanded."
            actions={[
              {
                label: 'Browse Theatres',
                onClick: () => navigate('/theatres'),
                variant: 'primary',
              },
              {
                label: 'Verify a Certificate',
                onClick: () => navigate('/verify'),
                variant: 'secondary',
              },
            ]}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mx-auto max-w-7xl space-y-5">
        <p className="max-w-4xl text-[15px] leading-6 text-[var(--e-text-secondary)]">
          Settlement and verification artifacts from theatres and investigation workflows.
        </p>

        <div className="grid grid-cols-2 gap-3 xl:grid-cols-5">
          <StatCard label="Total Certificates" value={total} />
          <StatCard label="Routing Allowed" value={allowedCount} tone="success" />
          <StatCard label="Review Required" value={reviewCount} tone={reviewCount > 0 ? 'warning' : undefined} />
          <StatCard label="Deployable" value={deployableCount} tone="success" />
          <StatCard label="Not Deployable" value={notDeployableCount} />
        </div>

        <div className="inline-flex rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] p-1 shadow-[var(--e-shadow-xs)]">
          {[
            { label: 'All', value: 'all' as StatusFilter, count: total },
            { label: 'Deployable', value: 'deployable' as StatusFilter, count: deployableCount },
            { label: 'Not Deployable', value: 'not-deployable' as StatusFilter, count: notDeployableCount },
          ].map((tab) => (
            <button
              key={tab.label}
              type="button"
              onClick={() => setStatusFilter(tab.value)}
              className={clsx(
                'inline-flex items-center gap-2 rounded-md px-3 py-2 text-[13px] font-medium transition',
                statusFilter === tab.value
                  ? 'bg-[var(--e-purple-50)] text-[var(--e-purple-700)]'
                  : 'text-[var(--e-text-secondary)] hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]',
              )}
            >
              {tab.label}
              <span className="font-mono text-[11px] text-[var(--e-text-muted)]">{tab.count}</span>
            </button>
          ))}
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-6 py-16 shadow-[var(--e-shadow-xs)]">
            <Loader2 className="mr-2 h-5 w-5 animate-spin text-[var(--e-text-muted)]" />
            <span className="text-[14px] text-[var(--e-text-muted)]">Loading certificates…</span>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_300px]">
            <div className="overflow-hidden rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-sm)]">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)]">
                    {['Certificate ID', 'Construct / Source', 'Routing', 'Score', 'Gate', 'Tier', 'Issued', 'Actions'].map((heading, index) => (
                      <th
                        key={heading}
                        className={clsx(
                          'px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]',
                          index >= 3 && index !== 7 && 'text-right',
                          index === 7 && 'text-right',
                        )}
                      >
                        {heading}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((certificate) => (
                    <CertificateRow key={certificate.id} certificate={certificate} />
                  ))}
                </tbody>
              </table>
              <div className="flex items-center justify-between border-t border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3 text-[12px] text-[var(--e-text-muted)]">
                <span>
                  Showing <strong className="text-[var(--e-text-primary)]">{filtered.length}</strong> of{' '}
                  <strong className="text-[var(--e-text-primary)]">{total}</strong> certificates
                </span>
                <span className="font-mono text-[10px]">theatre source only</span>
              </div>
            </div>

            <div className="hidden lg:block">
              <RightRail certificates={certificates} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default CertificatesPage;
