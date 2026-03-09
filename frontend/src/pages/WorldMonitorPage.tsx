import { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { clsx } from 'clsx';
import {
  Activity,
  ArrowUpRight,
  Clock3,
  Globe2,
  Radar,
  Search,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
  Waves,
} from 'lucide-react';
import { EmptyState } from '../components/empty-states/EmptyState';
import { useWorldMonitor } from '../hooks/useWorldMonitor';
import type { Timeline, WingFlap } from '../types';

type MonitorFilter = 'all' | 'paradox' | 'unstable' | 'gravity';

function formatPercent(value: number) {
  return `${Math.round(value)}%`;
}

function formatCurrency(value: number) {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${Math.round(value / 1_000)}K`;
  return `$${Math.round(value)}`;
}

function formatTimeAgo(timestamp: string) {
  const deltaMs = Date.now() - new Date(timestamp).getTime();
  const deltaMinutes = Math.max(0, Math.floor(deltaMs / 60_000));
  if (deltaMinutes < 1) return 'now';
  if (deltaMinutes < 60) return `${deltaMinutes}m ago`;
  const hours = Math.floor(deltaMinutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

function getPageState(activeParadoxes: number, recentActivityCount: number) {
  if (activeParadoxes >= 3) return 'critical';
  if (activeParadoxes > 0 || recentActivityCount > 0) return 'active';
  return 'quiet';
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
  tone?: 'danger' | 'warning' | 'success';
}) {
  return (
    <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-4 shadow-[var(--e-shadow-xs)]">
      <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
        {label}
      </div>
      <div
        className={clsx(
          'font-mono text-[28px] font-bold leading-8 tabular-nums',
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
      {detail ? <div className="mt-1 text-[12px] text-[var(--e-text-muted)]">{detail}</div> : null}
    </div>
  );
}

function FilterButton({
  active,
  label,
  count,
  onClick,
}: {
  active: boolean;
  label: string;
  count: number;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={clsx(
        'inline-flex h-9 items-center gap-2 rounded-full border px-4 text-[12px] font-semibold transition',
        active
          ? 'border-[var(--e-purple-500)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)]'
          : 'border-[var(--e-border-primary)] bg-[var(--e-bg-card)] text-[var(--e-text-secondary)] hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]',
      )}
    >
      <span>{label}</span>
      <span
        className={clsx(
          'rounded-full px-2 py-0.5 font-mono text-[10px] tabular-nums',
          active
            ? 'bg-[var(--e-purple-100)] text-[var(--e-purple-700)]'
            : 'bg-[var(--e-bg-sunken)] text-[var(--e-text-muted)]',
        )}
      >
        {count}
      </span>
    </button>
  );
}

function TheatreStatusChip({ timeline }: { timeline: Timeline }) {
  if (timeline.has_active_paradox) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-red-600)]">
        <span className="h-2 w-2 rounded-full bg-[var(--e-red-600)]" />
        Paradox Active
      </span>
    );
  }

  if (timeline.stability < 55 || timeline.gravity_score >= 80) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-[color:oklch(0.708_0.136_62_/_0.20)] bg-[color:oklch(0.708_0.136_62_/_0.10)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-orange-600)]">
        <Clock3 className="h-3 w-3" />
        Watching
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-[color:oklch(0.545_0.170_152_/_0.18)] bg-[color:oklch(0.545_0.170_152_/_0.08)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-green-600)]">
      <ShieldCheck className="h-3 w-3" />
      Healthy
    </span>
  );
}

function TimelineRow({ timeline }: { timeline: Timeline }) {
  const lowLiquidity = timeline.liquidity_depth_usd < 75_000;

  return (
    <article className="grid gap-4 border-b border-[var(--e-border-secondary)] px-5 py-4 transition last:border-b-0 hover:bg-[var(--e-bg-hover)] md:grid-cols-[minmax(0,1.2fr)_140px_140px_140px_120px]">
      <div className="min-w-0">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <TheatreStatusChip timeline={timeline} />
          {timeline.gravity_score >= 80 ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-[var(--e-purple-50)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-purple-700)]">
              Gravity Hotspot
            </span>
          ) : null}
        </div>
        <div className="truncate text-[15px] font-semibold text-[var(--e-text-primary)]">{timeline.name}</div>
        <div className="mt-1 truncate font-mono text-[11px] text-[var(--e-text-muted)]">{timeline.id}</div>
        <div className="mt-3 flex flex-wrap gap-3 text-[12px] text-[var(--e-text-secondary)]">
          <span>Alignment {formatPercent(timeline.osint_alignment)}</span>
          <span>Agents {timeline.active_agent_count}</span>
          <span className={lowLiquidity ? 'text-[var(--e-orange-600)]' : undefined}>
            Liquidity {formatCurrency(timeline.liquidity_depth_usd)}
          </span>
        </div>
      </div>

      <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-3 py-3">
        <div className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
          Stability
        </div>
        <div className="mt-2 font-mono text-[20px] font-bold tabular-nums text-[var(--e-text-primary)]">
          {formatPercent(timeline.stability)}
        </div>
      </div>

      <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-3 py-3">
        <div className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
          Gravity
        </div>
        <div
          className={clsx(
            'mt-2 font-mono text-[20px] font-bold tabular-nums',
            timeline.gravity_score >= 80
              ? 'text-[var(--e-red-600)]'
              : timeline.gravity_score >= 60
                ? 'text-[var(--e-orange-600)]'
                : 'text-[var(--e-text-primary)]',
          )}
        >
          {timeline.gravity_score}
        </div>
      </div>

      <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-3 py-3">
        <div className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
          Reaper
        </div>
        <div className="mt-2 font-mono text-[20px] font-bold tabular-nums text-[var(--e-text-primary)]">
          {timeline.hours_until_reaper === null ? '—' : `${Math.round(timeline.hours_until_reaper)}h`}
        </div>
      </div>

      <div className="flex items-center md:justify-end">
        <Link
          to={`/theatre/${timeline.id}`}
          className="inline-flex h-10 items-center gap-2 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 text-[12px] font-semibold text-[var(--e-text-secondary)] no-underline transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-purple-700)]"
        >
          Open Theatre
          <ArrowUpRight className="h-3.5 w-3.5" />
        </Link>
      </div>
    </article>
  );
}

function WingFlapRow({ flap }: { flap: WingFlap }) {
  const positive = flap.stability_delta >= 0;

  return (
    <div className="flex items-start justify-between gap-3 border-b border-[var(--e-border-secondary)] py-3 last:border-b-0">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <span className="rounded-full border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-text-muted)]">
            {flap.flap_type}
          </span>
          <span className="text-[11px] text-[var(--e-text-muted)]">{formatTimeAgo(flap.timestamp)}</span>
        </div>
        <div className="mt-1 text-[13px] font-semibold text-[var(--e-text-primary)]">{flap.timeline_name}</div>
        <div className="mt-1 text-[12px] text-[var(--e-text-secondary)]">
          {flap.agent_name} · {flap.action} · {formatCurrency(flap.volume_usd)}
        </div>
      </div>

      <div className="text-right">
        <div
          className={clsx(
            'font-mono text-[13px] font-semibold tabular-nums',
            positive ? 'text-[var(--e-green-600)]' : 'text-[var(--e-red-600)]',
          )}
        >
          {positive ? '+' : ''}
          {flap.stability_delta.toFixed(1)}
        </div>
        <div className="mt-1 text-[11px] text-[var(--e-text-muted)]">
          {Math.round(flap.timeline_stability)}% stable
        </div>
      </div>
    </div>
  );
}

export function WorldMonitorPage() {
  const { timelines, recentActivity, stats, isLoading, error, isQuiet, isEmpty } = useWorldMonitor();
  const [filter, setFilter] = useState<MonitorFilter>('all');
  const [search, setSearch] = useState('');
  const navigate = useNavigate();

  const pageState = getPageState(stats.activeParadoxes, recentActivity.length);

  const filteredTimelines = useMemo(() => {
    const query = search.trim().toLowerCase();

    return timelines
      .filter((timeline) => {
        if (filter === 'paradox') return timeline.has_active_paradox;
        if (filter === 'unstable') return timeline.stability < 55;
        if (filter === 'gravity') return timeline.gravity_score >= 70;
        return true;
      })
      .filter((timeline) => {
        if (!query) return true;
        return (
          timeline.name.toLowerCase().includes(query) ||
          timeline.id.toLowerCase().includes(query) ||
          (timeline.dominant_agent_name ?? '').toLowerCase().includes(query)
        );
      })
      .sort((a, b) => {
        if (a.has_active_paradox !== b.has_active_paradox) {
          return a.has_active_paradox ? -1 : 1;
        }
        return b.gravity_score - a.gravity_score;
      });
  }, [filter, search, timelines]);

  const activeHotspots = useMemo(
    () => timelines.filter((timeline) => timeline.has_active_paradox || timeline.gravity_score >= 75).slice(0, 5),
    [timelines],
  );

  const quietCount = Math.max(0, timelines.length - stats.activeParadoxes);

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="mx-auto max-w-7xl space-y-5">
          <div className="h-5 w-40 animate-pulse rounded bg-[var(--e-bg-sunken)]" />
          <div className="h-12 w-72 animate-pulse rounded bg-[var(--e-bg-sunken)]" />
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {Array.from({ length: 4 }).map((_, index) => (
              <div
                key={index}
                className="h-28 animate-pulse rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)]"
              />
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
          <h1 className="mb-2 text-[22px] font-semibold text-[var(--e-text-primary)]">
            Failed to load World Monitor
          </h1>
          <p className="text-[14px] text-[var(--e-text-secondary)]">{error.message}</p>
        </div>
      </div>
    );
  }

  if (isEmpty) {
    return (
      <div className="p-6">
        <div className="mx-auto max-w-6xl rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
          <EmptyState
            type="ZERO_STATE"
            title="No theatres tracked"
            description="World Monitor becomes active once theatres exist. Create a theatre to begin tracking stability, gravity, paradox risk, and recent wing flaps."
            actions={[
              {
                label: 'Create Theatre',
                onClick: () => navigate('/theatres/create'),
              },
            ]}
            icon={<Globe2 className="h-6 w-6" />}
          />
        </div>
      </div>
    );
  }

  const activeCounts = {
    all: timelines.length,
    paradox: timelines.filter((timeline) => timeline.has_active_paradox).length,
    unstable: timelines.filter((timeline) => timeline.stability < 55).length,
    gravity: timelines.filter((timeline) => timeline.gravity_score >= 70).length,
  };

  return (
    <div className="p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              Intelligence
            </div>
            <h1 className="text-[30px] font-semibold tracking-[-0.02em] text-[var(--e-text-primary)]">
              World Monitor
            </h1>
            <p className="mt-2 max-w-3xl text-[14px] leading-6 text-[var(--e-text-secondary)]">
              Global watch across live theatres, paradox pressure, gravity hotspots, and the latest wing flaps. Event-map and regional clustering remain deferred until the world-monitor event APIs exist.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <Link
              to="/world-monitor/live"
              className="inline-flex h-10 items-center gap-2 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 text-[13px] font-semibold text-[var(--e-text-secondary)] no-underline transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]"
            >
              <Radar className="h-4 w-4" />
              Open Global Map
            </Link>
            <Link
              to="/theatres/create"
              className="inline-flex h-10 items-center gap-2 rounded-md border border-[var(--e-purple-500)] bg-[var(--e-purple-500)] px-4 text-[13px] font-semibold text-white no-underline transition hover:bg-[var(--e-purple-400)]"
            >
              <Sparkles className="h-4 w-4" />
              Create Theatre
            </Link>
            <Link
              to="/theatres"
              className="inline-flex h-10 items-center gap-2 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 text-[13px] font-semibold text-[var(--e-text-secondary)] no-underline transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]"
            >
              <Globe2 className="h-4 w-4" />
              Open Theatres
            </Link>
          </div>
        </div>

        <div
          className={clsx(
            'flex items-center gap-3 rounded-lg px-5 py-3 text-[13px]',
            pageState === 'critical'
              ? 'border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[color:oklch(0.545_0.185_25_/_0.08)]'
              : pageState === 'active'
                ? 'border border-[color:oklch(0.545_0.170_152_/_0.18)] bg-[color:oklch(0.545_0.170_152_/_0.08)]'
                : 'border border-[var(--e-border-primary)] bg-[var(--e-bg-sunken)]',
          )}
        >
          {pageState === 'critical' ? (
            <TriangleAlert className="h-4 w-4 shrink-0 text-[var(--e-red-600)]" />
          ) : pageState === 'active' ? (
            <Radar className="h-4 w-4 shrink-0 text-[var(--e-green-600)]" />
          ) : (
            <ShieldCheck className="h-4 w-4 shrink-0 text-[var(--e-text-muted)]" />
          )}
          <span
            className={clsx(
              'font-semibold',
              pageState === 'critical'
                ? 'text-[var(--e-red-600)]'
                : pageState === 'active'
                  ? 'text-[var(--e-green-600)]'
                  : 'text-[var(--e-text-muted)]',
            )}
          >
            {pageState === 'critical'
              ? 'Escalated'
              : pageState === 'active'
                ? 'Active monitoring'
                : 'Quiet monitoring'}
          </span>
          <span className="text-[var(--e-text-secondary)]">
            {pageState === 'critical'
              ? `${stats.activeParadoxes} paradox-active theatres are live. Prioritize hotspot review and theatre-level intervention.`
              : pageState === 'active'
                ? `${recentActivity.length} recent wing flap${recentActivity.length === 1 ? '' : 's'} and ${stats.activeParadoxes} paradox-active theatre${stats.activeParadoxes === 1 ? '' : 's'} are being tracked.`
                : `${quietCount} theatre${quietCount === 1 ? '' : 's'} remain calm. Global event-map enrichment is deferred until dedicated event endpoints exist.`}
          </span>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <KpiCard label="Tracked Theatres" value={stats.totalTimelines} detail="Live health feed" />
          <KpiCard
            label="Paradox Active"
            value={stats.activeParadoxes}
            detail="Theatres with active paradoxes"
            tone={stats.activeParadoxes > 0 ? 'danger' : 'success'}
          />
          <KpiCard
            label="Average Stability"
            value={`${Math.round(stats.avgStability)}%`}
            detail="Across tracked theatres"
            tone={stats.avgStability >= 70 ? 'success' : stats.avgStability >= 50 ? 'warning' : 'danger'}
          />
          <KpiCard
            label="Gravity Hotspots"
            value={stats.highGravityCount}
            detail="Gravity score ≥ 70"
            tone={stats.highGravityCount > 0 ? 'warning' : 'success'}
          />
        </div>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
          <div className="space-y-6">
            <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
              <div className="flex items-center justify-between gap-4 border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-3">
                <div>
                  <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                    Deferred Enrichment
                  </div>
                  <h2 className="text-[13px] font-semibold text-[var(--e-text-primary)]">Global Event Map</h2>
                </div>
                <span className="rounded-full border border-[var(--e-border-secondary)] bg-[var(--e-bg-card)] px-2.5 py-1 font-mono text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-text-muted)]">
                  Awaiting event API
                </span>
              </div>

              <div className="grid gap-5 px-5 py-5 lg:grid-cols-[1.2fr_0.8fr]">
                <div className="rounded-xl border border-dashed border-[var(--e-border-primary)] bg-[var(--e-bg-sunken)] p-6">
                  <div className="mb-4 flex items-center gap-3">
                    <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-[var(--e-purple-200)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)]">
                      <Globe2 className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="text-[14px] font-semibold text-[var(--e-text-primary)]">World-event layer deferred</div>
                      <div className="text-[12px] text-[var(--e-text-muted)]">
                        The locked reference expects regional event clusters, domain mix, and linked event entities. The live hook currently exposes theatre health and wing flaps only.
                      </div>
                    </div>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-card)] px-4 py-3">
                      <div className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                        Available now
                      </div>
                      <ul className="mt-3 space-y-2 text-[12px] leading-5 text-[var(--e-text-secondary)]">
                        <li>Tracked theatre health and stability</li>
                        <li>Active paradox detection</li>
                        <li>Gravity hotspot ranking</li>
                        <li>Recent wing flap activity</li>
                      </ul>
                    </div>

                    <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-card)] px-4 py-3">
                      <div className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                        Deferred until backend exists
                      </div>
                      <ul className="mt-3 space-y-2 text-[12px] leading-5 text-[var(--e-text-secondary)]">
                        <li>World event roster and regional clusters</li>
                        <li>Signal freshness and domain mix</li>
                        <li>Linked theatre and investigation entities</li>
                        <li>Geographic escalation map</li>
                      </ul>
                    </div>
                  </div>
                </div>

                <div className="rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] p-5">
                  <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                    Gravity Hotspots
                  </div>
                  {activeHotspots.length === 0 ? (
                    <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-8 text-center text-[13px] text-[var(--e-text-muted)]">
                      No hotspots right now.
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {activeHotspots.map((timeline) => (
                        <Link
                          key={timeline.id}
                          to={`/theatre/${timeline.id}`}
                          className="block rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3 no-underline transition hover:border-[var(--e-purple-200)] hover:bg-[var(--e-bg-hover)]"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <div className="truncate text-[13px] font-semibold text-[var(--e-text-primary)]">
                                {timeline.name}
                              </div>
                              <div className="mt-1 text-[11px] text-[var(--e-text-muted)]">
                                {timeline.has_active_paradox ? 'Paradox active' : 'High gravity pressure'}
                              </div>
                            </div>
                            <div className="font-mono text-[12px] font-semibold tabular-nums text-[var(--e-text-primary)]">
                              {timeline.gravity_score}
                            </div>
                          </div>
                          <div className="mt-3 h-2 overflow-hidden rounded-full bg-[var(--e-bg-card)]">
                            <div
                              className={clsx(
                                'h-full rounded-full',
                                timeline.has_active_paradox
                                  ? 'bg-[var(--e-red-600)]'
                                  : 'bg-[var(--e-orange-500)]',
                              )}
                              style={{ width: `${Math.min(100, timeline.gravity_score)}%` }}
                            />
                          </div>
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </section>

            <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
              <div className="flex flex-col gap-3 border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-4 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                    Live Roster
                  </div>
                  <h2 className="text-[13px] font-semibold text-[var(--e-text-primary)]">Tracked Theatres</h2>
                </div>

                <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                  <div className="flex flex-wrap gap-2">
                    <FilterButton active={filter === 'all'} label="All" count={activeCounts.all} onClick={() => setFilter('all')} />
                    <FilterButton active={filter === 'paradox'} label="Paradox" count={activeCounts.paradox} onClick={() => setFilter('paradox')} />
                    <FilterButton active={filter === 'unstable'} label="Unstable" count={activeCounts.unstable} onClick={() => setFilter('unstable')} />
                    <FilterButton active={filter === 'gravity'} label="Gravity" count={activeCounts.gravity} onClick={() => setFilter('gravity')} />
                  </div>

                  <label className="relative block min-w-[220px]">
                    <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--e-text-muted)]" />
                    <input
                      value={search}
                      onChange={(event) => setSearch(event.target.value)}
                      placeholder="Search theatres..."
                      className="h-10 w-full rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] pl-10 pr-3 text-[13px] text-[var(--e-text-primary)] outline-none transition placeholder:text-[var(--e-text-muted)] focus:border-[var(--e-purple-500)] focus:ring-2 focus:ring-[color:oklch(0.530_0.230_295_/_0.12)]"
                    />
                  </label>
                </div>
              </div>

              {filteredTimelines.length === 0 ? (
                <EmptyState
                  type="NO_RESULTS"
                  title="No theatres match"
                  description="Adjust the search or filter to see tracked theatres."
                  filterDescription={filter === 'all' ? search : `${filter} + ${search || 'all search'}`}
                  onClearFilters={() => {
                    setFilter('all');
                    setSearch('');
                  }}
                  className="min-h-[220px]"
                />
              ) : (
                <div>
                  {filteredTimelines.map((timeline) => (
                    <TimelineRow key={timeline.id} timeline={timeline} />
                  ))}
                </div>
              )}
            </section>
          </div>

          <aside className="space-y-4">
            <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
              <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
                <div className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                  Recent Activity
                </div>
              </div>
              <div className="px-4 py-3">
                {recentActivity.length === 0 ? (
                  <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-8 text-center text-[13px] text-[var(--e-text-muted)]">
                    No recent wing flaps.
                  </div>
                ) : (
                  recentActivity.slice(0, 6).map((flap) => <WingFlapRow key={flap.id} flap={flap} />)
                )}
              </div>
            </section>

            <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
              <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
                <div className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                  Monitor Notes
                </div>
              </div>
              <div className="space-y-3 px-4 py-4 text-[12px] leading-5 text-[var(--e-text-secondary)]">
                <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
                  <div className="mb-1 flex items-center gap-2 text-[var(--e-text-primary)]">
                    <Activity className="h-4 w-4 text-[var(--e-purple-700)]" />
                    <span className="font-semibold">Live scope</span>
                  </div>
                  World Monitor is currently theatre-health centric. It shows stability, gravity, paradox pressure, and wing flaps from the live butterfly endpoints.
                </div>

                <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
                  <div className="mb-1 flex items-center gap-2 text-[var(--e-text-primary)]">
                    <Waves className="h-4 w-4 text-[var(--e-orange-600)]" />
                    <span className="font-semibold">Deferred enrichments</span>
                  </div>
                  Regional event clusters, signal freshness, domain mix, and linked investigation entities remain deferred until dedicated world-monitor APIs exist.
                </div>
              </div>
            </section>
          </aside>
        </div>

        {isQuiet ? (
          <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
            <EmptyState
              type="ALL_CLEAR"
              description="No active paradox pressure right now. Continue background monitoring while the world-event layer remains deferred."
              recentItems={recentActivity.slice(0, 3).map((flap) => ({
                label: `${flap.timeline_name} · ${flap.action}`,
                time: formatTimeAgo(flap.timestamp),
              }))}
              className="min-h-[180px]"
            />
          </div>
        ) : null}
      </div>
    </div>
  );
}
