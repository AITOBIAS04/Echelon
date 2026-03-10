import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Award, ExternalLink, Search, ShieldCheck } from 'lucide-react';
import { clsx } from 'clsx';
import { useVerifyUi } from '../contexts/VerifyUiContext';
import { useVerificationRuns } from '../hooks/useVerificationRuns';
import { useCertificates } from '../hooks/useCertificates';
import { RunsListView } from '../components/verify/RunsListView';
import { RunDetailDrawer } from '../components/verify/RunDetailDrawer';
import { CertificatesListView } from '../components/verify/CertificatesListView';
import { CertDetailDrawer } from '../components/verify/CertDetailDrawer';
import { StartVerificationModal } from '../components/verify/StartVerificationModal';
import type { VerificationRunStatus, CertFilters } from '../types/verification';

export function VerifyPage() {
  const { activeTab, setActiveTab } = useVerifyUi();
  const [searchParams, setSearchParams] = useSearchParams();

  const [runFilters, setRunFilters] = useState<{
    status?: VerificationRunStatus;
    construct_id?: string;
  }>({});
  const [runOffset, setRunOffset] = useState(0);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  const { runs, total: runsTotal, isLoading: runsLoading, error: runsError, createRun, isCreating } =
    useVerificationRuns({
      ...runFilters,
      limit: 20,
      offset: runOffset,
    });

  const selectedRun = selectedRunId ? runs.find((run) => run.run_id === selectedRunId) ?? null : null;

  const [certSort, setCertSort] = useState<CertFilters['sort']>('brier_asc');
  const [certConstructFilter, setCertConstructFilter] = useState('');
  const [certOffset, setCertOffset] = useState(0);
  const [selectedCertId, setSelectedCertId] = useState<string | null>(null);
  const requestedCertificateId = searchParams.get('certificate');

  const { certificates, total: certsTotal, isLoading: certsLoading, error: certsError } =
    useCertificates({
      sort: certSort,
      construct_id: certConstructFilter || undefined,
      limit: 20,
      offset: certOffset,
    });

  const [showModal, setShowModal] = useState(false);

  const runKpis = useMemo(() => {
    const completed = runs.filter((run) => run.status === 'COMPLETED').length;
    const active = runs.filter((run) => run.status !== 'COMPLETED' && run.status !== 'FAILED').length;
    const failed = runs.filter((run) => run.status === 'FAILED').length;
    const issued = runs.filter((run) => !!run.certificate_id).length;
    return { completed, active, failed, issued };
  }, [runs]);

  const certKpis = useMemo(() => {
    const visible = certificates.length;
    const avgComposite =
      visible > 0 ? certificates.reduce((sum, cert) => sum + cert.composite_score, 0) / visible : null;
    const avgBrier = visible > 0 ? certificates.reduce((sum, cert) => sum + cert.brier, 0) / visible : null;
    const replayCoverage = certificates.reduce((sum, cert) => sum + cert.replay_count, 0);
    return { visible, avgComposite, avgBrier, replayCoverage };
  }, [certificates]);

  const skipClearRef = useRef(false);
  useEffect(() => {
    if (skipClearRef.current) {
      skipClearRef.current = false;
      return;
    }
    setSelectedRunId(null);
    setSelectedCertId(null);
  }, [activeTab]);

  useEffect(() => {
    if (!requestedCertificateId) {
      return;
    }
    skipClearRef.current = true;
    setActiveTab('certificates');
    setSelectedRunId(null);
    setSelectedCertId(requestedCertificateId);
  }, [requestedCertificateId, setActiveTab]);

  const handleViewCertificate = useCallback(
    (certificateId: string) => {
      skipClearRef.current = true;
      setSelectedRunId(null);
      setActiveTab('certificates');
      setSelectedCertId(certificateId);
      setSearchParams((current) => {
        const next = new URLSearchParams(current);
        next.set('certificate', certificateId);
        return next;
      });
    },
    [setActiveTab, setSearchParams],
  );

  const handleModalSubmit = useCallback(
    async (body: Parameters<typeof createRun>[0]) => {
      await createRun(body);
    },
    [createRun],
  );

  return (
    <div className="p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        {activeTab === 'certificates' ? (
          <section className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-5 py-5 shadow-[var(--e-shadow-xs)]">
            <div className="max-w-3xl">
              <div className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                Public Verify
              </div>
              <div className="mt-2 text-[14px] leading-6 text-[var(--e-text-secondary)]">
                Browse public certificates by construct ID. Direct hash-based verification remains deferred until the backend exposes it.
              </div>
              <div className="relative mt-4 max-w-2xl">
                <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--e-text-muted)]" />
                <input
                  type="text"
                  className="h-12 w-full rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] pl-11 pr-4 font-mono text-[14px] text-[var(--e-text-primary)] outline-none transition placeholder:font-sans placeholder:text-[var(--e-text-muted)] focus:border-[var(--e-purple-500)] focus:ring-2 focus:ring-[color:oklch(0.530_0.230_295_/_0.12)]"
                  placeholder="Filter by construct ID"
                  value={certConstructFilter}
                  onChange={(e) => {
                    setCertConstructFilter(e.target.value);
                    setCertOffset(0);
                  }}
                />
              </div>
            </div>
          </section>
        ) : null}

        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_300px]">
          <div className="space-y-6">
            {activeTab === 'runs' ? (
              <div className="grid gap-4 md:grid-cols-4">
                <KpiCard label="Visible Runs" value={runs.length} />
                <KpiCard label="Active" value={runKpis.active} tone="info" />
                <KpiCard label="Completed" value={runKpis.completed} tone="success" />
                <KpiCard label="Issued" value={runKpis.issued} tone={runKpis.issued > 0 ? 'success' : undefined} />
              </div>
            ) : (
              <div className="grid gap-4 md:grid-cols-4">
                <KpiCard label="Visible Certificates" value={certKpis.visible} />
                <KpiCard
                  label="Average Composite"
                  value={certKpis.avgComposite != null ? certKpis.avgComposite.toFixed(3) : '—'}
                  tone={
                    certKpis.avgComposite == null
                      ? undefined
                      : certKpis.avgComposite > 0.7
                        ? 'success'
                        : certKpis.avgComposite > 0.4
                          ? 'warning'
                          : 'danger'
                  }
                />
                <KpiCard
                  label="Average Brier"
                  value={certKpis.avgBrier != null ? certKpis.avgBrier.toFixed(3) : '—'}
                  tone={
                    certKpis.avgBrier == null
                      ? undefined
                      : certKpis.avgBrier < 0.15
                        ? 'success'
                        : certKpis.avgBrier < 0.3
                          ? 'warning'
                          : 'danger'
                  }
                />
                <KpiCard label="Replay Coverage" value={certKpis.replayCoverage > 0 ? certKpis.replayCoverage : '—'} />
              </div>
            )}

            <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
              <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-3">
                <div className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                  {activeTab === 'certificates' ? 'Public Browser' : 'Run Queue'}
                </div>
              </div>
              <div className="px-5 py-5">
                {activeTab === 'runs' ? (
                  <RunsListView
                    runs={runs}
                    total={runsTotal}
                    isLoading={runsLoading}
                    error={runsError}
                    filters={runFilters}
                    onFiltersChange={setRunFilters}
                    offset={runOffset}
                    onOffsetChange={setRunOffset}
                    onSelectRun={setSelectedRunId}
                  />
                ) : (
                  <CertificatesListView
                    certificates={certificates}
                    total={certsTotal}
                    isLoading={certsLoading}
                    error={certsError}
                    sort={certSort}
                    onSortChange={setCertSort}
                    constructFilter={certConstructFilter}
                    onConstructFilterChange={(val) => {
                      setCertConstructFilter(val);
                      setCertOffset(0);
                    }}
                    offset={certOffset}
                    onOffsetChange={setCertOffset}
                    onSelectCert={setSelectedCertId}
                  />
                )}
              </div>
            </section>
          </div>

          <div className="space-y-4">
            <SideCard
              eyebrow={activeTab === 'certificates' ? 'Verify Surface' : 'Run Workflow'}
              title={activeTab === 'certificates' ? 'What this page can verify' : 'How run issuance works'}
            >
              {activeTab === 'certificates' ? (
                <ul className="space-y-2 text-[13px] leading-5 text-[var(--e-text-secondary)]">
                  <li>Browse public calibration certificates by construct ID.</li>
                  <li>Inspect replay methodology, Brier score, and certificate detail.</li>
                  <li>Direct hash lookup remains deferred until the backend exposes it.</li>
                </ul>
              ) : (
                <ul className="space-y-2 text-[13px] leading-5 text-[var(--e-text-secondary)]">
                  <li>Create a verification run against a repository and oracle.</li>
                  <li>Track replay progress through ingest, invoke, scoring, and certification.</li>
                  <li>Completed runs can open the issued public certificate directly.</li>
                </ul>
              )}
            </SideCard>

            {activeTab === 'certificates' ? (
              <SideCard eyebrow="Recent Visibility" title="Current certificate view">
                {certificates.length > 0 ? (
                  <div className="space-y-3">
                    {certificates.slice(0, 4).map((cert) => (
                      <button
                        key={cert.id}
                        type="button"
                        onClick={() => setSelectedCertId(cert.id)}
                        className="flex w-full items-center justify-between rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 py-3 text-left transition hover:border-[var(--e-purple-200)] hover:bg-[var(--e-bg-hover)]"
                      >
                        <div className="min-w-0">
                          <div className="truncate text-[12px] font-semibold text-[var(--e-text-primary)]">{cert.construct_id}</div>
                          <div className="font-mono text-[10px] text-[var(--e-text-muted)]">{cert.domain}</div>
                        </div>
                        <div className="text-right">
                          <div className="font-mono text-[11px] font-semibold text-[var(--e-text-primary)]">{cert.brier.toFixed(3)}</div>
                          <div className="text-[10px] text-[var(--e-text-muted)]">Brier</div>
                        </div>
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="text-[13px] text-[var(--e-text-secondary)]">No certificates in the current filter view.</p>
                )}
              </SideCard>
            ) : (
              <SideCard eyebrow="Current queue" title="Run status mix">
                <div className="space-y-3">
                  <StatusRow label="Active" value={runKpis.active} tone="info" />
                  <StatusRow label="Completed" value={runKpis.completed} tone="success" />
                  <StatusRow label="Failed" value={runKpis.failed} tone="danger" />
                  <StatusRow label="Issued certificates" value={runKpis.issued} tone={runKpis.issued > 0 ? 'success' : undefined} />
                </div>
              </SideCard>
            )}

            <SideCard eyebrow="Operator note" title="Related surfaces">
              <div className="space-y-3">
                <LinkRow to="/certificates" icon={<Award className="h-4 w-4" />} label="Open Certificates" description="Deployment readiness and certificate routing." />
                <LinkRow to="/investigation" icon={<ShieldCheck className="h-4 w-4" />} label="Open Investigations" description="Readiness, drift, and certificate generation." />
                <LinkRow to="/home" icon={<ExternalLink className="h-4 w-4" />} label="Return to Dashboard" description="Mission control and recent operational activity." />
              </div>
            </SideCard>
          </div>
        </div>
      </div>

      <RunDetailDrawer
        run={selectedRun}
        onClose={() => setSelectedRunId(null)}
        onViewCertificate={handleViewCertificate}
      />

      <CertDetailDrawer
        certId={selectedCertId}
        onClose={() => {
          setSelectedCertId(null);
          setSearchParams((current) => {
            const next = new URLSearchParams(current);
            next.delete('certificate');
            return next;
          });
        }}
      />

      <StartVerificationModal
        open={showModal}
        onClose={() => setShowModal(false)}
        onSubmit={handleModalSubmit}
        isSubmitting={isCreating}
      />
    </div>
  );
}

function KpiCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: string | number;
  tone?: 'success' | 'warning' | 'danger' | 'info';
}) {
  return (
    <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-4 shadow-[var(--e-shadow-xs)]">
      <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
        {label}
      </div>
      <div
        className={clsx(
          'font-mono text-[28px] font-bold leading-8 tabular-nums',
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

function SideCard({
  eyebrow,
  title,
  children,
}: {
  eyebrow: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
      <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
        <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
          {eyebrow}
        </div>
        <h2 className="text-[13px] font-semibold text-[var(--e-text-primary)]">{title}</h2>
      </div>
      <div className="px-4 py-4">{children}</div>
    </section>
  );
}

function StatusRow({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone?: 'success' | 'danger' | 'info';
}) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 py-3">
      <span className="text-[12px] font-medium text-[var(--e-text-secondary)]">{label}</span>
      <span
        className={clsx(
          'font-mono text-[14px] font-semibold tabular-nums',
          tone === 'success'
            ? 'text-[var(--e-green-600)]'
            : tone === 'danger'
              ? 'text-[var(--e-red-600)]'
              : tone === 'info'
                ? 'text-[var(--e-purple-700)]'
                : 'text-[var(--e-text-primary)]',
        )}
      >
        {value}
      </span>
    </div>
  );
}

function LinkRow({
  to,
  icon,
  label,
  description,
}: {
  to: string;
  icon: React.ReactNode;
  label: string;
  description: string;
}) {
  return (
    <Link
      to={to}
      className="flex items-start gap-3 rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 py-3 no-underline transition hover:border-[var(--e-purple-200)] hover:bg-[var(--e-bg-hover)]"
    >
      <div className="mt-0.5 flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--e-purple-200)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)]">
        {icon}
      </div>
      <div className="min-w-0">
        <div className="text-[12px] font-semibold text-[var(--e-text-primary)]">{label}</div>
        <div className="mt-1 text-[12px] leading-5 text-[var(--e-text-secondary)]">{description}</div>
      </div>
    </Link>
  );
}

export default VerifyPage;
