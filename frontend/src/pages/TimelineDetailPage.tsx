import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { clsx } from 'clsx';
import {
  AlertTriangle,
  ArrowLeft,
  BadgeCheck,
  Clock3,
  FileCheck2,
  GitCommitHorizontal,
  Loader2,
  Play,
  Radar,
  Rocket,
  SearchCheck,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import { useTheatreDetail } from '../hooks/useTheatreDetail';
import { DeployAgentModal } from '../components/agents/DeployAgentModal';
import type { TheatreCertificateResponse, TheatreResponse } from '../types/theatre';

function formatDateTime(value: string | null | undefined): string {
  if (!value) return '—';
  return new Date(value).toLocaleString();
}

function formatCompact(value: string | null | undefined, leading = 10, trailing = 6): string {
  if (!value) return '—';
  if (value.length <= leading + trailing + 1) return value;
  return `${value.slice(0, leading)}…${value.slice(-trailing)}`;
}

function toTitleCase(value: string | null | undefined): string {
  if (!value) return '—';
  return value
    .toLowerCase()
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function stateTone(state: TheatreResponse['state']) {
  switch (state) {
    case 'DRAFT':
      return 'border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] text-[var(--e-text-muted)]';
    case 'COMMITTED':
      return 'border-[var(--e-purple-200)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)]';
    case 'ACTIVE':
      return 'border-[color:oklch(0.545_0.170_152_/_0.18)] bg-[var(--e-green-50)] text-[var(--e-green-600)]';
    case 'SETTLING':
      return 'border-[color:oklch(0.708_0.136_62_/_0.20)] bg-[color:oklch(0.708_0.136_62_/_0.10)] text-[var(--e-orange-600)]';
    case 'RESOLVED':
      return 'border-[color:oklch(0.525_0.155_260_/_0.18)] bg-[color:oklch(0.525_0.155_260_/_0.08)] text-[var(--e-purple-700)]';
    case 'ARCHIVED':
      return 'border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] text-[var(--e-text-disabled)]';
    default:
      return 'border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] text-[var(--e-text-muted)]';
  }
}

function paradoxTone(level: string | null | undefined) {
  if (!level) {
    return {
      label: 'Healthy',
      classes:
        'border-[color:oklch(0.545_0.170_152_/_0.18)] bg-[var(--e-green-50)] text-[var(--e-green-600)]',
    };
  }

  const upper = level.toUpperCase();
  if (upper.includes('CRITICAL') || upper.includes('HIGH')) {
    return {
      label: toTitleCase(level),
      classes:
        'border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] text-[var(--e-red-600)]',
    };
  }
  if (upper.includes('MEDIUM') || upper.includes('ELEVATED')) {
    return {
      label: toTitleCase(level),
      classes:
        'border-[color:oklch(0.708_0.136_62_/_0.20)] bg-[color:oklch(0.708_0.136_62_/_0.10)] text-[var(--e-orange-600)]',
    };
  }

  return {
    label: toTitleCase(level),
    classes:
      'border-[color:oklch(0.545_0.170_152_/_0.18)] bg-[color:oklch(0.545_0.170_152_/_0.08)] text-[var(--e-green-600)]',
  };
}

function routingTone(certificate: TheatreCertificateResponse | null) {
  if (!certificate?.routing_hint) {
    return {
      label: 'Pending',
      classes: 'text-[var(--e-text-muted)]',
      dot: 'bg-[var(--e-text-disabled)]',
    };
  }

  switch (certificate.routing_hint) {
    case 'ALLOWED':
      return {
        label: 'Allowed',
        classes: 'text-[var(--e-green-600)]',
        dot: 'bg-[var(--e-green-600)]',
      };
    case 'REVIEW_REQUIRED':
      return {
        label: 'Review Required',
        classes: 'text-[var(--e-orange-600)]',
        dot: 'bg-[var(--e-orange-600)]',
      };
    case 'BLOCKED':
      return {
        label: 'Blocked',
        classes: 'text-[var(--e-red-600)]',
        dot: 'bg-[var(--e-red-600)]',
      };
    default:
      return {
        label: certificate.routing_hint,
        classes: 'text-[var(--e-text-muted)]',
        dot: 'bg-[var(--e-text-disabled)]',
      };
  }
}

function SectionCard({
  title,
  eyebrow,
  children,
  aside,
}: {
  title: string;
  eyebrow?: string;
  children: React.ReactNode;
  aside?: React.ReactNode;
}) {
  return (
    <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
      <div className="flex items-center justify-between gap-4 border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-3">
        <div>
          {eyebrow ? (
            <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              {eyebrow}
            </div>
          ) : null}
          <h2 className="text-[13px] font-semibold text-[var(--e-text-primary)]">{title}</h2>
        </div>
        {aside}
      </div>
      <div className="px-5 py-5">{children}</div>
    </section>
  );
}

function MetricTile({
  label,
  value,
  helper,
  tone,
}: {
  label: string;
  value: string;
  helper?: string;
  tone?: 'danger' | 'warning' | 'success';
}) {
  return (
    <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
      <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
        {label}
      </div>
      <div
        className={clsx(
          'font-mono text-[18px] font-bold tabular-nums',
          tone === 'danger'
            ? 'text-[var(--e-red-600)]'
            : tone === 'warning'
              ? 'text-[var(--e-orange-600)]'
              : tone === 'success'
                ? 'text-[var(--e-green-600)]'
                : 'text-[var(--e-text-primary)]',
        )}
      >
        {value}
      </div>
      {helper ? <div className="mt-1 text-[11px] text-[var(--e-text-muted)]">{helper}</div> : null}
    </div>
  );
}

function RiskRow({
  label,
  value,
  tone,
  helper,
}: {
  label: string;
  value: string;
  tone: 'healthy' | 'watch' | 'danger' | 'muted';
  helper?: string;
}) {
  const toneClasses: Record<typeof tone, string> = {
    healthy: 'text-[var(--e-green-600)] bg-[var(--e-green-600)]',
    watch: 'text-[var(--e-orange-600)] bg-[var(--e-orange-600)]',
    danger: 'text-[var(--e-red-600)] bg-[var(--e-red-600)]',
    muted: 'text-[var(--e-text-muted)] bg-[var(--e-text-disabled)]',
  };

  const [textClass, dotClass] = toneClasses[tone].split(' ');

  return (
    <div className="flex items-start justify-between gap-4 border-t border-[var(--e-border-secondary)] py-3 first:border-t-0 first:pt-0 last:pb-0">
      <div>
        <div className="text-[13px] text-[var(--e-text-secondary)]">{label}</div>
        {helper ? <div className="mt-1 text-[11px] text-[var(--e-text-muted)]">{helper}</div> : null}
      </div>
      <div className={clsx('inline-flex items-center gap-2 text-[12px] font-semibold', textClass)}>
        <span className={clsx('h-2.5 w-2.5 rounded-full', dotClass)} />
        {value}
      </div>
    </div>
  );
}

function ActionButton({
  label,
  icon,
  onClick,
  disabled,
  pending,
  tone = 'primary',
}: {
  label: string;
  icon: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
  pending?: boolean;
  tone?: 'primary' | 'secondary';
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled || pending}
      className={clsx(
        'inline-flex h-10 w-full items-center justify-center gap-2 rounded-md border px-4 text-[13px] font-semibold transition',
        tone === 'primary'
          ? 'border-[var(--e-purple-500)] bg-[var(--e-purple-500)] text-white hover:bg-[var(--e-purple-400)]'
          : 'border-[var(--e-border-primary)] bg-[var(--e-bg-card)] text-[var(--e-text-secondary)] hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]',
        'disabled:cursor-not-allowed disabled:border-[var(--e-border-secondary)] disabled:bg-[var(--e-bg-sunken)] disabled:text-[var(--e-text-disabled)]',
      )}
    >
      {pending ? <Loader2 className="h-4 w-4 animate-spin" /> : icon}
      {label}
    </button>
  );
}

function DetailSkeleton() {
  return (
    <div className="space-y-5 p-6">
      <div className="h-4 w-40 animate-pulse rounded bg-[var(--e-bg-sunken)]" />
      <div className="h-12 w-96 max-w-full animate-pulse rounded bg-[var(--e-bg-sunken)]" />
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_380px]">
        <div className="space-y-5">
          <div className="h-64 animate-pulse rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)]" />
          <div className="h-64 animate-pulse rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)]" />
        </div>
        <div className="h-[420px] animate-pulse rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)]" />
      </div>
    </div>
  );
}

export function TimelineDetailPage() {
  const { theatreId, timelineId } = useParams<{ theatreId?: string; timelineId?: string }>();
  const resolvedId = theatreId ?? timelineId ?? null;
  const navigate = useNavigate();
  const [deployModalOpen, setDeployModalOpen] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const {
    theatre,
    commitment,
    certificate,
    isLoading,
    isCommitmentLoading,
    isCertificateLoading,
    error,
    commit,
    isCommitting,
    run,
    isRunning,
    settle,
    isSettling,
  } = useTheatreDetail(resolvedId);

  const paradox = paradoxTone(theatre?.paradox_risk_level);
  const routing = routingTone(certificate);

  const handleCommit = async () => {
    if (!resolvedId) return;
    setActionError(null);
    try {
      await commit();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Failed to commit theatre');
    }
  };

  const handleRun = async () => {
    if (!resolvedId) return;
    setActionError(null);
    try {
      await run();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Failed to start theatre');
    }
  };

  const handleSettle = async () => {
    if (!resolvedId) return;
    setActionError(null);
    try {
      await settle();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Failed to settle theatre');
    }
  };

  if (isLoading) {
    return <DetailSkeleton />;
  }

  if (error || !theatre) {
    return (
      <div className="p-6">
        <div className="mx-auto max-w-5xl rounded-lg border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-bg-card)] px-8 py-14 text-center shadow-[var(--e-shadow-xs)]">
          <AlertTriangle className="mx-auto mb-4 h-10 w-10 text-[var(--e-red-600)]" />
          <h1 className="mb-2 text-[22px] font-semibold text-[var(--e-text-primary)]">Unable to load theatre</h1>
          <p className="mb-6 text-[14px] text-[var(--e-text-secondary)]">
            {error instanceof Error ? error.message : 'This theatre could not be loaded from the live API.'}
          </p>
          <button
            type="button"
            onClick={() => navigate('/theatres')}
            className="inline-flex h-10 items-center gap-2 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 text-[13px] font-semibold text-[var(--e-text-secondary)] transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Theatres
          </button>
        </div>
      </div>
    );
  }

  const deployDisabled = theatre.state === 'RESOLVED' || theatre.state === 'ARCHIVED';
  const progressValue = `${Math.round(theatre.progress * 100)}%`;
  const commitmentReady = theatre.state !== 'DRAFT' || Boolean(theatre.commitment_hash);

  return (
    <div className="p-6">
      <div className="mx-auto max-w-7xl">
        <div className="mb-2 flex items-center gap-2 text-[13px] text-[var(--e-text-muted)]">
          <button
            type="button"
            onClick={() => navigate('/theatres')}
            className="inline-flex items-center gap-1.5 transition hover:text-[var(--e-purple-700)]"
          >
            <ArrowLeft className="h-4 w-4" />
            Theatres
          </button>
          <span>/</span>
          <span className="font-medium text-[var(--e-text-primary)]">{theatre.construct_id}</span>
        </div>

        <div className="mb-6 flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <span
                className={clsx(
                  'inline-flex items-center rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.05em]',
                  stateTone(theatre.state),
                )}
              >
                {theatre.state}
              </span>
              <span
                className={clsx(
                  'inline-flex items-center rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.05em]',
                  paradox.classes,
                )}
              >
                {paradox.label}
              </span>
              {theatre.inquiry_class ? (
                <span className="inline-flex items-center rounded-full border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.05em] text-[var(--e-text-muted)]">
                  {theatre.inquiry_class}
                </span>
              ) : null}
            </div>

            <h1 className="max-w-4xl text-[30px] font-semibold leading-[1.15] tracking-[-0.02em] text-[var(--e-text-primary)]">
              {theatre.construct_id}
            </h1>

            <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-[13px] text-[var(--e-text-secondary)]">
              <span className="font-mono text-[var(--e-text-muted)]">{formatCompact(theatre.id, 12, 6)}</span>
              <span>Stop condition: {toTitleCase(theatre.stop_condition)}</span>
              <span>Created {formatDateTime(theatre.created_at)}</span>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {theatre.certificate_id ? (
              <Link
                to="/certificates"
                className="inline-flex h-10 items-center gap-2 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 text-[13px] font-semibold text-[var(--e-text-secondary)] no-underline transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]"
              >
                <FileCheck2 className="h-4 w-4" />
                Certificates
              </Link>
            ) : null}
            <Link
              to={`/investigation/create?theatre_id=${encodeURIComponent(theatre.id)}&construct_id=${encodeURIComponent(theatre.construct_id)}&source_surface=theatre_detail`}
              className="inline-flex h-10 items-center gap-2 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 text-[13px] font-semibold text-[var(--e-text-secondary)] no-underline transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]"
            >
              <SearchCheck className="h-4 w-4" />
              New Investigation
            </Link>
            <button
              type="button"
              onClick={() => setDeployModalOpen(true)}
              disabled={deployDisabled}
              className="inline-flex h-10 items-center gap-2 rounded-md border border-[var(--e-purple-500)] bg-[var(--e-purple-500)] px-4 text-[13px] font-semibold text-white transition hover:bg-[var(--e-purple-400)] disabled:cursor-not-allowed disabled:border-[var(--e-border-secondary)] disabled:bg-[var(--e-bg-sunken)] disabled:text-[var(--e-text-disabled)]"
            >
              <Rocket className="h-4 w-4" />
              Deploy Agent
            </button>
          </div>
        </div>

        <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_380px]">
          <div className="space-y-5">
            <SectionCard
              title="Theatre Overview"
              eyebrow="Construct"
              aside={
                <div className="text-[12px] font-medium text-[var(--e-text-muted)]">
                  Progress <span className="font-mono tabular-nums text-[var(--e-text-primary)]">{progressValue}</span>
                </div>
              }
            >
              <div className="mb-5 rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-4">
                <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                  Current Surface
                </div>
                <p className="text-[14px] leading-6 text-[var(--e-text-secondary)]">
                  Theatre lifecycle, commitment receipt, certificate output, and paradox risk are live on this page.
                  Market execution remains deferred until a real theatre trading surface exists.
                </p>
              </div>

              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                <MetricTile label="State" value={theatre.state} helper="Live backend lifecycle" />
                <MetricTile
                  label="Episodes"
                  value={`${theatre.total_episodes}`}
                  helper="Total planned episodes"
                />
                <MetricTile
                  label="Failures"
                  value={`${theatre.failure_count}`}
                  helper={theatre.error ?? 'No current run error'}
                  tone={theatre.failure_count > 0 ? 'warning' : undefined}
                />
                <MetricTile
                  label="Certificate"
                  value={theatre.certificate_id ? 'Issued' : 'Pending'}
                  helper={theatre.certificate_id ? formatCompact(theatre.certificate_id, 10, 6) : 'No issued certificate yet'}
                  tone={theatre.certificate_id ? 'success' : undefined}
                />
              </div>
            </SectionCard>

            <SectionCard title="Risk & Trust" eyebrow="Operational Status">
              <div className="space-y-1">
                <RiskRow
                  label="Paradox risk"
                  value={paradox.label}
                  tone={
                    theatre.paradox_risk_level?.toUpperCase().includes('HIGH') ||
                    theatre.paradox_risk_level?.toUpperCase().includes('CRITICAL')
                      ? 'danger'
                      : theatre.paradox_risk_level
                        ? 'watch'
                        : 'healthy'
                  }
                  helper="Live theatre response includes paradox level + factors."
                />
                <RiskRow
                  label="Commitment"
                  value={commitmentReady ? 'Anchored' : 'Draft'}
                  tone={commitmentReady ? 'healthy' : 'muted'}
                  helper={theatre.commitment_hash ? formatCompact(theatre.commitment_hash, 12, 8) : 'No commitment hash yet'}
                />
                <RiskRow
                  label="Routing"
                  value={routing.label}
                  tone={
                    certificate?.routing_hint === 'BLOCKED'
                      ? 'danger'
                      : certificate?.routing_hint === 'REVIEW_REQUIRED'
                        ? 'watch'
                        : certificate?.routing_hint === 'ALLOWED'
                          ? 'healthy'
                          : 'muted'
                  }
                  helper={certificate?.coherence_gate_status ? `Gate ${certificate.coherence_gate_status}` : 'Certificate not yet available'}
                />
                <RiskRow
                  label="Stop condition"
                  value={toTitleCase(theatre.stop_condition)}
                  tone={theatre.stop_condition ? 'healthy' : 'muted'}
                  helper={theatre.stop_config ? `${Object.keys(theatre.stop_config).length} config entries pinned` : 'No stop config attached'}
                />
              </div>

              {theatre.paradox_risk_factors_json && Object.keys(theatre.paradox_risk_factors_json).length > 0 ? (
                <div className="mt-5 rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-4">
                  <div className="mb-3 text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                    Paradox Factors
                  </div>
                  <div className="grid gap-2 sm:grid-cols-2">
                    {Object.entries(theatre.paradox_risk_factors_json).slice(0, 6).map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between text-[12px]">
                        <span className="text-[var(--e-text-secondary)]">{toTitleCase(key)}</span>
                        <span className="font-mono text-[var(--e-text-primary)]">{String(value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </SectionCard>

            <SectionCard title="Commitment Receipt" eyebrow="Pinned Runtime">
              {theatre.commitment_hash ? (
                isCommitmentLoading ? (
                  <div className="flex items-center gap-2 text-[13px] text-[var(--e-text-muted)]">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Loading commitment receipt…
                  </div>
                ) : commitment ? (
                  <div className="space-y-4">
                    <div className="grid gap-3 md:grid-cols-2">
                      <MetricTile label="Commitment Hash" value={formatCompact(commitment.commitment_hash, 12, 8)} />
                      <MetricTile label="Committed At" value={formatDateTime(commitment.committed_at)} />
                    </div>
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-4">
                        <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                          Version Pins
                        </div>
                        <div className="space-y-2">
                          {Object.entries(commitment.version_pins).map(([key, value]) => (
                            <div key={key} className="flex items-center justify-between gap-3 text-[12px]">
                              <span className="text-[var(--e-text-secondary)]">{toTitleCase(key)}</span>
                              <span className="font-mono text-[var(--e-text-primary)]">{value}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-4">
                        <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                          Dataset Hashes
                        </div>
                        <div className="space-y-2">
                          {Object.entries(commitment.dataset_hashes).map(([key, value]) => (
                            <div key={key} className="flex items-center justify-between gap-3 text-[12px]">
                              <span className="text-[var(--e-text-secondary)]">{toTitleCase(key)}</span>
                              <span className="font-mono text-[var(--e-text-primary)]">{formatCompact(value, 10, 6)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-[13px] leading-6 text-[var(--e-text-secondary)]">
                    The theatre is committed, but the commitment receipt is not currently available in the detail query.
                  </p>
                )
              ) : (
                <div className="rounded-lg border border-dashed border-[var(--e-border-primary)] bg-[var(--e-bg-sunken)] px-4 py-4 text-[13px] leading-6 text-[var(--e-text-secondary)]">
                  This theatre is still in <span className="font-semibold text-[var(--e-text-primary)]">DRAFT</span>. Commit the
                  theatre to generate the locked commitment hash and pinned runtime receipt.
                </div>
              )}
            </SectionCard>

            <SectionCard title="Investigation Context" eyebrow="Evidence Surface">
              <div className="rounded-lg border border-dashed border-[var(--e-border-primary)] bg-[var(--e-bg-sunken)] px-4 py-4">
                <div className="mb-2 flex items-center gap-2 text-[13px] font-semibold text-[var(--e-text-primary)]">
                  <Sparkles className="h-4 w-4 text-[var(--e-purple-700)]" />
                  Theatre-linked evidence is deferred
                </div>
                <p className="text-[13px] leading-6 text-[var(--e-text-secondary)]">
                  The locked reference expects a compact evidence/investigation module here. The current theatre API does
                  not yet expose linked investigation summaries, so this surface stays intentionally sparse until that
                  join exists.
                </p>
              </div>
            </SectionCard>
          </div>

          <div className="space-y-5 lg:sticky lg:top-[104px]">
            <SectionCard title="Theatre Controls" eyebrow="Live Actions">
              <div className="mb-4 rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-4">
                <div className="mb-2 flex items-center gap-2 text-[13px] font-semibold text-[var(--e-text-primary)]">
                  <Radar className="h-4 w-4 text-[var(--e-purple-700)]" />
                  Lifecycle controls are live
                </div>
                <p className="text-[13px] leading-6 text-[var(--e-text-secondary)]">
                  This page currently surfaces commitment, run, settlement, and theatre-context agent deployment. Trade
                  execution from the theatre detail reference remains deferred.
                </p>
              </div>

              <div className="space-y-3">
                <ActionButton
                  label={theatre.state === 'DRAFT' ? 'Commit Theatre' : 'Commit Complete'}
                  icon={<GitCommitHorizontal className="h-4 w-4" />}
                  onClick={handleCommit}
                  disabled={theatre.state !== 'DRAFT'}
                  pending={isCommitting}
                  tone={theatre.state === 'DRAFT' ? 'primary' : 'secondary'}
                />
                <ActionButton
                  label={theatre.state === 'COMMITTED' ? 'Start Run' : 'Run Started'}
                  icon={<Play className="h-4 w-4" />}
                  onClick={handleRun}
                  disabled={theatre.state !== 'COMMITTED'}
                  pending={isRunning}
                  tone={theatre.state === 'COMMITTED' ? 'primary' : 'secondary'}
                />
                <ActionButton
                  label={theatre.state === 'ACTIVE' ? 'Settle Theatre' : 'Settlement Pending'}
                  icon={<BadgeCheck className="h-4 w-4" />}
                  onClick={handleSettle}
                  disabled={theatre.state !== 'ACTIVE'}
                  pending={isSettling}
                  tone={theatre.state === 'ACTIVE' ? 'primary' : 'secondary'}
                />
                <ActionButton
                  label="Deploy Agent"
                  icon={<Rocket className="h-4 w-4" />}
                  onClick={() => setDeployModalOpen(true)}
                  disabled={deployDisabled}
                  tone="secondary"
                />
              </div>

              {actionError ? (
                <div className="mt-4 flex items-start gap-2 rounded-md border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] px-3 py-3 text-[12px] leading-5 text-[var(--e-red-600)]">
                  <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" />
                  <span>{actionError}</span>
                </div>
              ) : null}
            </SectionCard>

            <SectionCard title="Certificate & Routing" eyebrow="Resolution Output">
              {theatre.state === 'RESOLVED' || theatre.certificate_id ? (
                isCertificateLoading ? (
                  <div className="flex items-center gap-2 text-[13px] text-[var(--e-text-muted)]">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Loading theatre certificate…
                  </div>
                ) : certificate ? (
                  <div className="space-y-4">
                    <div className="grid gap-3 sm:grid-cols-2">
                      <MetricTile label="Composite Score" value={certificate.composite_score.toFixed(3)} />
                      <MetricTile label="Verification Tier" value={certificate.verification_tier} />
                    </div>

                    <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-4">
                      <div className="mb-3 text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                        Routing
                      </div>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between gap-3">
                          <span className="text-[13px] text-[var(--e-text-secondary)]">Routing hint</span>
                          <span className={clsx('inline-flex items-center gap-2 text-[12px] font-semibold', routing.classes)}>
                            <span className={clsx('h-2.5 w-2.5 rounded-full', routing.dot)} />
                            {routing.label}
                          </span>
                        </div>
                        <div className="flex items-center justify-between gap-3">
                          <span className="text-[13px] text-[var(--e-text-secondary)]">Coherence gate</span>
                          <span className="font-mono text-[12px] text-[var(--e-text-primary)]">
                            {certificate.coherence_gate_status ?? '—'}
                          </span>
                        </div>
                        <div className="flex items-center justify-between gap-3">
                          <span className="text-[13px] text-[var(--e-text-secondary)]">Issued</span>
                          <span className="font-mono text-[12px] text-[var(--e-text-primary)]">
                            {formatDateTime(certificate.issued_at)}
                          </span>
                        </div>
                        <div className="flex items-center justify-between gap-3">
                          <span className="text-[13px] text-[var(--e-text-secondary)]">Replay count</span>
                          <span className="font-mono text-[12px] text-[var(--e-text-primary)]">{certificate.replay_count}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <Link
                        to="/certificates"
                        className="inline-flex h-10 flex-1 items-center justify-center gap-2 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] text-[13px] font-semibold text-[var(--e-text-secondary)] no-underline transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]"
                      >
                        <FileCheck2 className="h-4 w-4" />
                        Certificates Ledger
                      </Link>
                      <Link
                        to={`/verify?certificate=${encodeURIComponent(certificate.id)}`}
                        className="inline-flex h-10 flex-1 items-center justify-center gap-2 rounded-md border border-[var(--e-purple-500)] bg-[var(--e-purple-500)] text-[13px] font-semibold text-white no-underline transition hover:bg-[var(--e-purple-400)]"
                      >
                        <ShieldCheck className="h-4 w-4" />
                        Verify
                      </Link>
                    </div>
                  </div>
                ) : (
                  <div className="rounded-lg border border-dashed border-[var(--e-border-primary)] bg-[var(--e-bg-sunken)] px-4 py-4 text-[13px] leading-6 text-[var(--e-text-secondary)]">
                    This theatre is resolved, but the certificate detail is not available from the current response.
                  </div>
                )
              ) : (
                <div className="rounded-lg border border-dashed border-[var(--e-border-primary)] bg-[var(--e-bg-sunken)] px-4 py-4 text-[13px] leading-6 text-[var(--e-text-secondary)]">
                  Certificates appear after settlement. Routing, coherence gate status, and verification tier remain
                  unavailable until the theatre resolves.
                </div>
              )}
            </SectionCard>

            <SectionCard title="Activity Trace" eyebrow="Timestamps">
              <div className="space-y-3">
                {[
                  { label: 'Created', value: theatre.created_at, icon: Clock3 },
                  { label: 'Committed', value: theatre.committed_at, icon: GitCommitHorizontal },
                  { label: 'Resolved', value: theatre.resolved_at, icon: BadgeCheck },
                ].map((item) => (
                  <div key={item.label} className="flex items-center gap-3 rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-full border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] text-[var(--e-purple-700)]">
                      <item.icon className="h-4 w-4" />
                    </div>
                    <div className="min-w-0">
                      <div className="text-[11px] font-semibold uppercase tracking-[0.05em] text-[var(--e-text-muted)]">
                        {item.label}
                      </div>
                      <div className="font-mono text-[12px] text-[var(--e-text-primary)]">{formatDateTime(item.value)}</div>
                    </div>
                  </div>
                ))}
              </div>
            </SectionCard>
          </div>
        </div>
      </div>

      <DeployAgentModal
        open={deployModalOpen}
        onClose={() => setDeployModalOpen(false)}
        preselectedTheatreId={resolvedId ?? undefined}
      />
    </div>
  );
}
