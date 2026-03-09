import { Link } from 'react-router-dom';
import { clsx } from 'clsx';
import {
  ArrowUpRight,
  Globe,
  Radar,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
  Users,
} from 'lucide-react';
import { useOpsBoard } from '../hooks/useOpsBoard';

function formatTimeAgo(isoTimestamp: string): string {
  const diff = Date.now() - new Date(isoTimestamp).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return 'now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

function KpiCard({
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
                : 'text-[var(--e-text-primary)]',
        )}
      >
        {value}
      </div>
      {detail ? <div className="mt-1 text-[12px] text-[var(--e-text-muted)]">{detail}</div> : null}
    </div>
  );
}

function SectionCard({
  title,
  eyebrow,
  children,
  action,
}: {
  title: string;
  eyebrow?: string;
  children: React.ReactNode;
  action?: React.ReactNode;
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
        {action}
      </div>
      <div className="px-5 py-5">{children}</div>
    </section>
  );
}

function QuickLink({
  to,
  label,
  description,
  icon,
}: {
  to: string;
  label: string;
  description: string;
  icon: React.ReactNode;
}) {
  return (
    <Link
      to={to}
      className="group flex items-start gap-3 rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-4 no-underline shadow-[var(--e-shadow-xs)] transition hover:-translate-y-0.5 hover:border-[var(--e-purple-200)] hover:shadow-[var(--e-shadow-md)]"
    >
      <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-[var(--e-purple-200)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)]">
        {icon}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <div className="text-[14px] font-semibold text-[var(--e-text-primary)]">{label}</div>
          <ArrowUpRight className="h-3.5 w-3.5 text-[var(--e-text-muted)] transition group-hover:text-[var(--e-purple-700)]" />
        </div>
        <div className="mt-1 text-[12px] leading-5 text-[var(--e-text-secondary)]">{description}</div>
      </div>
    </Link>
  );
}

export function HomePage() {
  const { data, loading, error } = useOpsBoard();

  if (loading) {
    return (
      <div className="p-6">
        <div className="mx-auto max-w-7xl space-y-5">
          <div className="h-5 w-40 animate-pulse rounded bg-[var(--e-bg-sunken)]" />
          <div className="h-12 w-72 animate-pulse rounded bg-[var(--e-bg-sunken)]" />
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="h-28 animate-pulse rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)]" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="mx-auto max-w-4xl rounded-lg border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-bg-card)] px-8 py-14 text-center shadow-[var(--e-shadow-xs)]">
          <TriangleAlert className="mx-auto mb-4 h-10 w-10 text-[var(--e-red-600)]" />
          <h1 className="mb-2 text-[22px] font-semibold text-[var(--e-text-primary)]">Failed to load dashboard</h1>
          <p className="text-[14px] text-[var(--e-text-secondary)]">{error}</p>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const stabilityPct = Math.round(data.timelines.avgStability * 100);
  const stabilityTone =
    stabilityPct >= 70 ? 'success' : stabilityPct >= 40 ? 'warning' : 'danger';
  const hasIssues = data.paradoxes.totalActive > 0;

  return (
    <div className="p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              Mission Control
            </div>
            <h1 className="text-[30px] font-semibold tracking-[-0.02em] text-[var(--e-text-primary)]">Dashboard</h1>
            <p className="mt-2 max-w-3xl text-[14px] leading-6 text-[var(--e-text-secondary)]">
              Operator overview across theatres, paradoxes, investigations, fleet activity, and the latest wing flaps.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <Link
              to="/theatres/create"
              className="inline-flex h-10 items-center gap-2 rounded-md border border-[var(--e-purple-500)] bg-[var(--e-purple-500)] px-4 text-[13px] font-semibold text-white no-underline transition hover:bg-[var(--e-purple-400)]"
            >
              <Sparkles className="h-4 w-4" />
              Create Theatre
            </Link>
            <Link
              to="/paradox-console"
              className="inline-flex h-10 items-center gap-2 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 text-[13px] font-semibold text-[var(--e-text-secondary)] no-underline transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]"
            >
              <Radar className="h-4 w-4" />
              Paradox Console
            </Link>
          </div>
        </div>

        <div
          className={clsx(
            'flex items-center gap-3 rounded-lg px-5 py-3 text-[13px]',
            hasIssues
              ? 'border border-[color:oklch(0.708_0.136_62_/_0.20)] bg-[color:oklch(0.708_0.136_62_/_0.10)]'
              : 'border border-[color:oklch(0.545_0.170_152_/_0.18)] bg-[color:oklch(0.545_0.170_152_/_0.08)]',
          )}
        >
          {hasIssues ? (
            <TriangleAlert className="h-4 w-4 shrink-0 text-[var(--e-orange-600)]" />
          ) : (
            <ShieldCheck className="h-4 w-4 shrink-0 text-[var(--e-green-600)]" />
          )}
          <span className={clsx('font-semibold', hasIssues ? 'text-[var(--e-orange-600)]' : 'text-[var(--e-green-600)]')}>
            {hasIssues ? 'Attention required' : 'All clear'}
          </span>
          <span className="text-[var(--e-text-secondary)]">
            {hasIssues
              ? `${data.paradoxes.totalActive} active paradox${data.paradoxes.totalActive === 1 ? '' : 'es'} need monitoring.`
              : 'No active paradoxes right now. System health is stable.'}
          </span>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <KpiCard
            label="Active Theatres"
            value={data.timelines.active}
            detail={`${data.timelines.total} tracked · ${data.timelines.withParadox} with paradox`}
          />
          <KpiCard
            label="Average Stability"
            value={`${stabilityPct}%`}
            detail="Across active theatres"
            tone={stabilityTone}
          />
          <KpiCard
            label="Active Paradoxes"
            value={data.paradoxes.totalActive}
            detail={`${data.agents.alive} fleet agents available`}
            tone={data.paradoxes.totalActive > 0 ? 'danger' : 'success'}
          />
          <KpiCard
            label="Investigations"
            value={data.investigations.total}
            detail="Open investigation threads"
          />
        </div>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
          <div className="space-y-6">
            <SectionCard
              title="Operational Lanes"
              eyebrow="Quick Access"
              action={
                <Link
                  to="/world-monitor"
                  className="text-[12px] font-medium text-[var(--e-purple-700)] no-underline transition hover:underline"
                >
                  Open World Monitor
                </Link>
              }
            >
              <div className="grid gap-4 md:grid-cols-2">
                <QuickLink
                  to="/theatres"
                  label="Theatres"
                  description="Browse live theatre contracts, paradox-active constructs, and liquidity status."
                  icon={<Globe className="h-4 w-4" />}
                />
                <QuickLink
                  to="/investigation"
                  label="Investigations"
                  description="Review active investigations, evidence flow, drift events, and readiness state."
                  icon={<ShieldCheck className="h-4 w-4" />}
                />
                <QuickLink
                  to="/fleet"
                  label="Fleet"
                  description="Inspect the current roster, deployment load, and agent lifecycle state."
                  icon={<Users className="h-4 w-4" />}
                />
                <QuickLink
                  to="/certificates"
                  label="Certificates"
                  description="Track routing, coherence-gate state, and deployability across issued certificates."
                  icon={<Sparkles className="h-4 w-4" />}
                />
              </div>
            </SectionCard>

            <SectionCard title="Recent Activity" eyebrow="Wing Flaps">
              {data.recentFlaps.length === 0 ? (
                <div className="rounded-lg border border-dashed border-[var(--e-border-primary)] bg-[var(--e-bg-sunken)] px-5 py-6 text-center">
                  <div className="mb-2 text-[15px] font-semibold text-[var(--e-text-primary)]">No recent activity</div>
                  <div className="text-[13px] text-[var(--e-text-muted)]">
                    Wing flaps will appear here once agents begin acting across active theatres.
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  {data.recentFlaps.map((flap) => (
                    <div
                      key={flap.id ?? `${flap.timeline_id}-${flap.timestamp}`}
                      className="flex flex-wrap items-center gap-3 rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3"
                    >
                      <span className="rounded-full border border-[var(--e-purple-200)] bg-[var(--e-purple-50)] px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-purple-700)]">
                        {flap.flap_type}
                      </span>
                      <span className="min-w-0 flex-1 text-[13px] text-[var(--e-text-primary)]">{flap.action}</span>
                      <span className="font-mono text-[11px] text-[var(--e-text-muted)]">{flap.timeline_name}</span>
                      <span className="font-mono text-[11px] text-[var(--e-text-muted)]">{formatTimeAgo(flap.timestamp)}</span>
                    </div>
                  ))}
                </div>
              )}
            </SectionCard>
          </div>

          <div className="space-y-6">
            <SectionCard title="Status Notes" eyebrow="Current Truth">
              <div className="space-y-3 text-[13px] leading-6 text-[var(--e-text-secondary)]">
                <p>Dashboard values come from the live aggregation hook. It does not expose deltas, sub-market moves, or historical sparkline data yet.</p>
                <p>Use the linked surfaces for deeper operational views rather than expecting full drill-down analytics here.</p>
              </div>
            </SectionCard>

            <SectionCard title="Live Snapshot" eyebrow="System Pulse">
              <div className="space-y-3">
                <div className="flex items-center justify-between border-t border-[var(--e-border-secondary)] py-3 first:border-t-0 first:pt-0">
                  <span className="text-[13px] text-[var(--e-text-secondary)]">Paradox watch</span>
                  <span className={clsx('text-[12px] font-semibold', hasIssues ? 'text-[var(--e-red-600)]' : 'text-[var(--e-green-600)]')}>
                    {hasIssues ? 'Active' : 'Clear'}
                  </span>
                </div>
                <div className="flex items-center justify-between border-t border-[var(--e-border-secondary)] py-3">
                  <span className="text-[13px] text-[var(--e-text-secondary)]">Fleet availability</span>
                  <span className="font-mono text-[12px] text-[var(--e-text-primary)]">{data.agents.alive}</span>
                </div>
                <div className="flex items-center justify-between border-t border-[var(--e-border-secondary)] py-3">
                  <span className="text-[13px] text-[var(--e-text-secondary)]">Investigations open</span>
                  <span className="font-mono text-[12px] text-[var(--e-text-primary)]">{data.investigations.total}</span>
                </div>
                <div className="flex items-center justify-between border-t border-[var(--e-border-secondary)] py-3">
                  <span className="text-[13px] text-[var(--e-text-secondary)]">Recent flaps</span>
                  <span className="font-mono text-[12px] text-[var(--e-text-primary)]">{data.recentFlaps.length}</span>
                </div>
              </div>
            </SectionCard>

            <SectionCard title="Priority Paths" eyebrow="Next Actions">
              <div className="space-y-2">
                <Link
                  to="/theatres/create"
                  className="flex items-center justify-between rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3 text-[13px] font-medium text-[var(--e-text-primary)] no-underline transition hover:border-[var(--e-purple-200)] hover:bg-[var(--e-bg-hover)]"
                >
                  Create a new theatre
                  <ArrowUpRight className="h-3.5 w-3.5 text-[var(--e-text-muted)]" />
                </Link>
                <Link
                  to="/paradox-console"
                  className="flex items-center justify-between rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3 text-[13px] font-medium text-[var(--e-text-primary)] no-underline transition hover:border-[var(--e-purple-200)] hover:bg-[var(--e-bg-hover)]"
                >
                  Review active paradoxes
                  <ArrowUpRight className="h-3.5 w-3.5 text-[var(--e-text-muted)]" />
                </Link>
                <Link
                  to="/certificates"
                  className="flex items-center justify-between rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3 text-[13px] font-medium text-[var(--e-text-primary)] no-underline transition hover:border-[var(--e-purple-200)] hover:bg-[var(--e-bg-hover)]"
                >
                  Inspect certificate routing
                  <ArrowUpRight className="h-3.5 w-3.5 text-[var(--e-text-muted)]" />
                </Link>
              </div>
            </SectionCard>
          </div>
        </div>
      </div>
    </div>
  );
}
