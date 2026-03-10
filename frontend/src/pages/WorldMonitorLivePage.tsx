import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { clsx } from 'clsx';
import {
  Activity,
  ArrowLeft,
  Award,
  BellRing,
  ExternalLink,
  Globe2,
  Radar,
  Search,
  ShieldCheck,
  ShieldAlert,
  Signal,
  Sparkles,
  TriangleAlert,
} from 'lucide-react';
import { useWorldMonitorLive } from '../hooks/useWorldMonitorLive';
import type { WorldMonitorIntelItem, WorldMonitorLiveEvent, WorldMonitorMission, WorldMonitorSignal } from '../api/worldMonitor';

type SeverityFilter = 'all' | 'critical' | 'high' | 'moderate' | 'low';

function humanizeKey(value: string) {
  return value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

function severityTone(severity: string) {
  switch (severity.toUpperCase()) {
    case 'CRITICAL':
      return 'danger';
    case 'HIGH':
      return 'warning';
    case 'MODERATE':
      return 'info';
    default:
      return 'muted';
  }
}

function matchesSeverity(signal: WorldMonitorSignal, filter: SeverityFilter) {
  const severity = signal.severity.toLowerCase();
  if (filter === 'all') return true;
  return severity === filter;
}

function formatTimeAgo(timestamp: string) {
  const diff = Date.now() - new Date(timestamp).getTime();
  const minutes = Math.max(0, Math.floor(diff / 60_000));
  if (minutes < 1) return 'now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

function formatCurrency(value: number) {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${Math.round(value / 1_000)}K`;
  return `$${Math.round(value)}`;
}

function projectGeo(lat: number, lon: number) {
  const left = `${((lon + 180) / 360) * 100}%`;
  const top = `${((90 - lat) / 180) * 100}%`;
  return { left, top };
}

function buildSignalMapLink(signal: WorldMonitorSignal) {
  const params = new URLSearchParams();
  params.set('signal', signal.id);
  params.set('q', signal.title);
  return `/signal-map?${params.toString()}`;
}

function buildCreateInvestigationLink(signal: WorldMonitorSignal) {
  const params = new URLSearchParams();
  params.set('signal_id', signal.id);
  params.set('signal_title', signal.title);
  params.set('signal_category', signal.category);
  params.set('signal_source', signal.source);
  params.set('signal_region', signal.region);
  params.set('source_surface', 'world_monitor_live');
  if (signal.theatre_ids?.[0]) {
    params.set('theatre_id', signal.theatre_ids[0]);
  }
  return `/investigation/create?${params.toString()}`;
}

function SectionCard({
  title,
  eyebrow,
  children,
  action,
  className,
}: {
  title: string;
  eyebrow?: string;
  children: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={clsx(
        'overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]',
        className,
      )}
    >
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

function FilterChip({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={clsx(
        'inline-flex h-8 items-center rounded-full border px-3 text-[11px] font-semibold uppercase tracking-[0.04em] transition',
        active
          ? 'border-[var(--e-purple-500)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)]'
          : 'border-[var(--e-border-primary)] bg-[var(--e-bg-card)] text-[var(--e-text-secondary)] hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]',
      )}
    >
      {label}
    </button>
  );
}

function EvidenceChainStep({
  tone,
  title,
  description,
  children,
}: {
  tone: 'muted' | 'persisted' | 'verified';
  title: string;
  description: string;
  children?: ReactNode;
}) {
  return (
    <div
      className={clsx(
        'rounded-lg border px-4 py-4',
        tone === 'muted'
          ? 'border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)]'
          : tone === 'persisted'
            ? 'border-[var(--e-purple-200)] bg-[var(--e-purple-50)]'
            : 'border-[color:oklch(0.723_0.173_150_/_0.24)] bg-[var(--e-green-50)]',
      )}
    >
      <div className="flex items-start gap-3">
        <div
          className={clsx(
            'mt-0.5 flex h-8 w-8 items-center justify-center rounded-full border text-[11px] font-semibold',
            tone === 'muted'
              ? 'border-[var(--e-border-primary)] bg-[var(--e-bg-card)] text-[var(--e-text-muted)]'
              : tone === 'persisted'
                ? 'border-[var(--e-purple-200)] bg-white text-[var(--e-purple-700)]'
                : 'border-[color:oklch(0.723_0.173_150_/_0.24)] bg-white text-[var(--e-green-700)]',
          )}
        >
          {tone === 'muted' ? <Globe2 className="h-4 w-4" /> : tone === 'persisted' ? <ShieldCheck className="h-4 w-4" /> : <Award className="h-4 w-4" />}
        </div>
        <div className="min-w-0 flex-1">
          <div
            className={clsx(
              'text-[11px] font-semibold uppercase tracking-[0.06em]',
              tone === 'muted'
                ? 'text-[var(--e-text-muted)]'
                : tone === 'persisted'
                  ? 'text-[var(--e-purple-700)]'
                  : 'text-[var(--e-green-700)]',
            )}
          >
            {title}
          </div>
          <p className="mt-1 text-[13px] leading-5 text-[var(--e-text-secondary)]">{description}</p>
          {children ? <div className="mt-3">{children}</div> : null}
        </div>
      </div>
    </div>
  );
}

function SignalSeverityBadge({ severity }: { severity: string }) {
  const tone = severityTone(severity);

  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em]',
        tone === 'danger'
          ? 'border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] text-[var(--e-red-600)]'
          : tone === 'warning'
            ? 'border-[color:oklch(0.708_0.136_62_/_0.20)] bg-[color:oklch(0.708_0.136_62_/_0.10)] text-[var(--e-orange-600)]'
            : tone === 'info'
              ? 'border-[var(--e-purple-200)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)]'
              : 'border-[var(--e-border-primary)] bg-[var(--e-bg-sunken)] text-[var(--e-text-muted)]',
      )}
    >
      {severity}
    </span>
  );
}

function FeedRow({ event }: { event: WorldMonitorLiveEvent }) {
  const severity = event.severity.toUpperCase();
  return (
    <div className="flex items-start gap-3 border-b border-[var(--e-border-secondary)] py-3 last:border-b-0">
      <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] text-[16px]">
        {event.icon ?? '•'}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <div className="text-[13px] font-semibold text-[var(--e-text-primary)]">{event.title}</div>
          <SignalSeverityBadge severity={severity} />
        </div>
        <div className="mt-1 text-[12px] leading-5 text-[var(--e-text-secondary)]">{event.description}</div>
        <div className="mt-2 font-mono text-[11px] text-[var(--e-text-muted)]">{formatTimeAgo(event.timestamp)}</div>
      </div>
    </div>
  );
}

function IntelRow({ item }: { item: WorldMonitorIntelItem }) {
  return (
    <div className="border-b border-[var(--e-border-secondary)] py-3 last:border-b-0">
      <div className="flex flex-wrap items-center gap-2">
        <div className="text-[13px] font-semibold text-[var(--e-text-primary)]">{item.title ?? 'Intel item'}</div>
        {item.source_type ? (
          <span className="rounded-full bg-[var(--e-bg-sunken)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-text-muted)]">
            {humanizeKey(item.source_type)}
          </span>
        ) : null}
      </div>
      {item.content ? (
        <div className="mt-1 line-clamp-2 text-[12px] leading-5 text-[var(--e-text-secondary)]">{item.content}</div>
      ) : null}
      <div className="mt-2 flex items-center justify-between gap-3 text-[11px] text-[var(--e-text-muted)]">
        <span>{item.source_agent ?? 'Unknown source'}</span>
        {typeof item.accuracy === 'number' ? (
          <span className="font-mono">{Math.round(item.accuracy * 100)}% accuracy</span>
        ) : null}
      </div>
    </div>
  );
}

function MissionRow({ mission }: { mission: WorldMonitorMission }) {
  return (
    <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-card)] px-4 py-4">
      <div className="flex flex-wrap items-center gap-2">
        {mission.category ? (
          <span className="rounded-full bg-[var(--e-purple-50)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-purple-700)]">
            {humanizeKey(mission.category)}
          </span>
        ) : null}
        {mission.status ? (
          <span className="rounded-full bg-[var(--e-bg-sunken)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-text-muted)]">
            {humanizeKey(mission.status)}
          </span>
        ) : null}
      </div>
      <div className="mt-2 text-[14px] font-semibold text-[var(--e-text-primary)]">{mission.title ?? mission.id}</div>
      {mission.description ? (
        <div className="mt-1 text-[12px] leading-5 text-[var(--e-text-secondary)]">{mission.description}</div>
      ) : null}
      <div className="mt-3 grid grid-cols-3 gap-3 text-[11px] text-[var(--e-text-muted)]">
        <div>
          <div className="font-semibold uppercase tracking-[0.04em]">Reward</div>
          <div className="mt-1 font-mono text-[var(--e-text-primary)]">
            {typeof mission.reward_pool === 'number' ? formatCurrency(mission.reward_pool) : '—'}
          </div>
        </div>
        <div>
          <div className="font-semibold uppercase tracking-[0.04em]">Participants</div>
          <div className="mt-1 font-mono text-[var(--e-text-primary)]">{mission.participants ?? '—'}</div>
        </div>
        <div>
          <div className="font-semibold uppercase tracking-[0.04em]">Expires</div>
          <div className="mt-1 font-mono text-[var(--e-text-primary)]">
            {mission.expires_at ? formatTimeAgo(mission.expires_at) : '—'}
          </div>
        </div>
      </div>
    </div>
  );
}

export function WorldMonitorLivePage() {
  const { data, isLoading, error } = useWorldMonitorLive();
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [sourceFilter, setSourceFilter] = useState<string>('all');
  const [search, setSearch] = useState('');
  const [selectedSignalId, setSelectedSignalId] = useState<string | null>(null);

  const sourceOptions = useMemo(() => ['all', ...Object.keys(data.source_counts).sort()], [data.source_counts]);
  const categoryOptions = useMemo(() => ['all', ...Object.keys(data.category_counts).sort()], [data.category_counts]);

  const filteredSignals = useMemo(() => {
    const query = search.trim().toLowerCase();
    return data.signals.filter((signal) => {
      if (!matchesSeverity(signal, severityFilter)) return false;
      if (categoryFilter !== 'all' && signal.category !== categoryFilter) return false;
      if (sourceFilter !== 'all' && signal.source !== sourceFilter) return false;
      if (!query) return true;
      return [
        signal.title,
        signal.description,
        signal.region,
        signal.source,
        signal.category,
      ].some((value) => value.toLowerCase().includes(query));
    });
  }, [categoryFilter, data.signals, search, severityFilter, sourceFilter]);

  const mapSignals = useMemo(() => filteredSignals.slice(0, 80), [filteredSignals]);
  const heatCells = data.convergence_cells.slice(0, 40);
  const selectedSignal =
    filteredSignals.find((signal) => signal.id === selectedSignalId) ??
    mapSignals[0] ??
    null;
  const relatedTheatres = selectedSignal?.theatre_ids ?? [];
  const pageCritical =
    data.summary.tension_index >= 70 || data.summary.critical_signals >= 4 || heatCells.length >= 6;

  useEffect(() => {
    if (selectedSignalId && filteredSignals.some((signal) => signal.id === selectedSignalId)) {
      return;
    }

    setSelectedSignalId(filteredSignals[0]?.id ?? null);
  }, [filteredSignals, selectedSignalId]);

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="mx-auto max-w-[1600px] space-y-5">
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
          <h1 className="mb-2 text-[22px] font-semibold text-[var(--e-text-primary)]">Failed to load Global Map</h1>
          <p className="text-[14px] text-[var(--e-text-secondary)]">
            {error instanceof Error ? error.message : 'Unknown error'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mx-auto max-w-[1600px] space-y-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              Intelligence
            </div>
            <h1 className="text-[30px] font-semibold tracking-[-0.02em] text-[var(--e-text-primary)]">Global Map</h1>
            <p className="mt-2 max-w-4xl text-[14px] leading-6 text-[var(--e-text-secondary)]">
              Live geospatial monitor built from World Monitor snapshot data: event-level OSINT, convergence cells, mission queue, intel desk, and Situation Room feed.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <Link
              to="/world-monitor"
              className="inline-flex h-10 items-center gap-2 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 text-[13px] font-semibold text-[var(--e-text-secondary)] no-underline transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Summary
            </Link>
            <Link
              to={selectedSignal ? buildSignalMapLink(selectedSignal) : '/signal-map'}
              className="inline-flex h-10 items-center gap-2 rounded-md border border-[var(--e-purple-500)] bg-[var(--e-purple-500)] px-4 text-[13px] font-semibold text-white no-underline transition hover:bg-[var(--e-purple-400)]"
            >
              <Sparkles className="h-4 w-4" />
              Open Signal Map
            </Link>
          </div>
        </div>

        <div
          className={clsx(
            'flex items-center gap-3 rounded-lg px-5 py-3 text-[13px]',
            pageCritical
              ? 'border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)]'
              : 'border border-[color:oklch(0.545_0.170_152_/_0.18)] bg-[color:oklch(0.545_0.170_152_/_0.08)]',
          )}
        >
          {pageCritical ? (
            <ShieldAlert className="h-4 w-4 shrink-0 text-[var(--e-red-600)]" />
          ) : (
            <Radar className="h-4 w-4 shrink-0 text-[var(--e-green-600)]" />
          )}
          <span className={clsx('font-semibold', pageCritical ? 'text-[var(--e-red-600)]' : 'text-[var(--e-green-600)]')}>
            {pageCritical ? 'Escalated global state' : 'Live global watch'}
          </span>
          <span className="text-[var(--e-text-secondary)]">
            Tension index {Math.round(data.summary.tension_index)} · {data.summary.critical_signals} high-priority signal
            {data.summary.critical_signals === 1 ? '' : 's'} · {data.summary.convergence_cells} convergence cell
            {data.summary.convergence_cells === 1 ? '' : 's'}
          </span>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <KpiCard
            label="Tension Index"
            value={Math.round(data.summary.tension_index)}
            detail={humanizeKey(data.summary.tension_level)}
            tone={data.summary.tension_index >= 70 ? 'danger' : data.summary.tension_index >= 45 ? 'warning' : 'success'}
          />
          <KpiCard label="Live Signals" value={data.summary.active_signals} detail="Event-level OSINT markers" tone={data.summary.active_signals > 40 ? 'warning' : undefined} />
          <KpiCard label="Convergence" value={data.summary.convergence_cells} detail="Geo heat cells" />
          <KpiCard label="Mission Queue" value={data.summary.active_missions} detail={`${data.live_feed.length} live feed events`} />
        </div>

        <div className="grid gap-6 xl:grid-cols-[300px_minmax(0,1fr)_340px]">
          <div className="space-y-4">
            <SectionCard title="Layers" eyebrow="Filters">
              <div className="space-y-5">
                <div>
                  <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Severity</div>
                  <div className="flex flex-wrap gap-2">
                    {(['all', 'critical', 'high', 'moderate', 'low'] as SeverityFilter[]).map((option) => (
                      <FilterChip key={option} active={severityFilter === option} label={option} onClick={() => setSeverityFilter(option)} />
                    ))}
                  </div>
                </div>

                <div>
                  <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Category</div>
                  <div className="flex flex-wrap gap-2">
                    {categoryOptions.map((option) => (
                      <FilterChip
                        key={option}
                        active={categoryFilter === option}
                        label={option === 'all' ? 'all categories' : `${humanizeKey(option)} (${data.category_counts[option] ?? 0})`}
                        onClick={() => setCategoryFilter(option)}
                      />
                    ))}
                  </div>
                </div>

                <div>
                  <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Source Layer</div>
                  <div className="flex max-h-[180px] flex-wrap gap-2 overflow-auto">
                    {sourceOptions.map((option) => (
                      <FilterChip
                        key={option}
                        active={sourceFilter === option}
                        label={option === 'all' ? 'all sources' : `${humanizeKey(option)} (${data.source_counts[option] ?? 0})`}
                        onClick={() => setSourceFilter(option)}
                      />
                    ))}
                  </div>
                </div>

                <label className="block">
                  <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Search</div>
                  <div className="relative">
                    <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--e-text-muted)]" />
                    <input
                      value={search}
                      onChange={(event) => setSearch(event.target.value)}
                      placeholder="Search event titles, regions, or sources"
                      className="h-10 w-full rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] pl-10 pr-3 text-[13px] text-[var(--e-text-primary)] outline-none transition placeholder:text-[var(--e-text-muted)] focus:border-[var(--e-purple-500)] focus:ring-2 focus:ring-[color:oklch(0.530_0.230_295_/_0.12)]"
                    />
                  </div>
                </label>
              </div>
            </SectionCard>

            <SectionCard title="Mission Queue" eyebrow="Assignments">
              {data.missions.length === 0 ? (
                <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-8 text-center text-[13px] text-[var(--e-text-muted)]">No active missions.</div>
              ) : (
                <div className="space-y-3">
                  {data.missions.slice(0, 4).map((mission) => <MissionRow key={mission.id} mission={mission} />)}
                </div>
              )}
            </SectionCard>
          </div>

          <div className="space-y-4">
            <SectionCard
              title="Global Activity Canvas"
              eyebrow="Immersive View"
              action={
                <span className="rounded-full border border-[color:oklch(0.525_0.155_260_/_0.18)] bg-[color:oklch(0.525_0.155_260_/_0.10)] px-2.5 py-1 font-mono text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-purple-700)]">
                  Event-level
                </span>
              }
              className="overflow-hidden"
            >
              <div className="relative overflow-hidden rounded-xl border border-[color:oklch(0.200_0.015_265_/_0.18)] bg-[radial-gradient(circle_at_top,rgba(100,60,180,0.18),transparent_30%),linear-gradient(180deg,#08111c_0%,#05080f_100%)] px-4 py-4 text-white">
                <div className="relative mb-4 flex items-center justify-between gap-3">
                  <div>
                    <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-white/55">Live Events</div>
                    <div className="mt-1 text-[15px] font-semibold text-white">
                      {mapSignals.length} visible event{mapSignals.length === 1 ? '' : 's'}
                    </div>
                  </div>
                  <div className="rounded-full border border-white/10 bg-white/5 px-3 py-1 font-mono text-[11px] text-white/70">
                    {heatCells.length} convergence cell{heatCells.length === 1 ? '' : 's'}
                  </div>
                </div>

                <div className="relative h-[520px] overflow-hidden rounded-xl border border-white/10 bg-[radial-gradient(circle_at_50%_50%,rgba(72,102,190,0.16),transparent_38%),linear-gradient(180deg,rgba(255,255,255,0.02),rgba(255,255,255,0.01))]">
                  <div className="pointer-events-none absolute inset-[8%] rounded-[48%] border border-white/8" />
                  <div className="pointer-events-none absolute inset-[14%] rounded-[48%] border border-white/6" />
                  <div className="pointer-events-none absolute inset-[20%] rounded-[48%] border border-white/5" />

                  {heatCells.map((cell, index) => {
                    const pos = projectGeo(cell.lat, cell.lon);
                    const size = Math.max(36, Math.min(120, cell.events * 10));
                    return (
                      <div
                        key={`${cell.lat}-${cell.lon}-${index}`}
                        className="pointer-events-none absolute -translate-x-1/2 -translate-y-1/2 rounded-full border border-orange-300/25 bg-orange-400/10 blur-[2px]"
                        style={{ left: pos.left, top: pos.top, width: `${size}px`, height: `${size}px` }}
                      />
                    );
                  })}

                  {mapSignals.length === 0 ? (
                    <div className="flex h-full items-center justify-center">
                      <div className="max-w-sm rounded-xl border border-white/10 bg-black/25 px-6 py-6 text-center backdrop-blur-sm">
                        <Signal className="mx-auto mb-3 h-6 w-6 text-white/70" />
                        <div className="text-[15px] font-semibold text-white">No events match the current filters</div>
                        <div className="mt-2 text-[13px] leading-6 text-white/65">
                          Clear or widen the active filters to repopulate the global activity canvas.
                        </div>
                      </div>
                    </div>
                  ) : (
                    mapSignals.map((signal) => {
                      const pos = projectGeo(signal.geo.lat, signal.geo.lon);
                      const tone = severityTone(signal.severity);
                      return (
                        <button
                          type="button"
                          key={signal.id}
                          onClick={() => setSelectedSignalId(signal.id)}
                          className="absolute -translate-x-1/2 -translate-y-1/2"
                          style={{ left: pos.left, top: pos.top }}
                          title={`${signal.title} · ${humanizeKey(signal.category)} · ${Math.round(signal.confidence * 100)}%`}
                        >
                          <div
                            className={clsx(
                              'absolute inset-0 -m-2 rounded-full blur-md transition',
                              tone === 'danger'
                                ? 'bg-red-500/25'
                                : tone === 'warning'
                                  ? 'bg-orange-400/20'
                                  : tone === 'info'
                                    ? 'bg-purple-400/20'
                                    : 'bg-sky-400/15',
                              selectedSignal?.id === signal.id && 'opacity-100',
                            )}
                          />
                          <div
                            className={clsx(
                              'relative h-3.5 w-3.5 rounded-full border transition',
                              tone === 'danger'
                                ? 'border-red-200 bg-red-400'
                                : tone === 'warning'
                                  ? 'border-orange-200 bg-orange-300'
                                  : tone === 'info'
                                    ? 'border-purple-200 bg-purple-300'
                                    : 'border-sky-200 bg-sky-300',
                              selectedSignal?.id === signal.id && 'scale-125 ring-4 ring-white/15',
                            )}
                          />
                        </button>
                      );
                    })
                  )}
                </div>

                <div className="mt-4 grid gap-3 md:grid-cols-3">
                  <div className="rounded-lg border border-white/10 bg-black/20 px-4 py-3">
                    <div className="text-[10px] font-semibold uppercase tracking-[0.06em] text-white/50">Signal contract</div>
                    <div className="mt-2 text-[12px] leading-5 text-white/70">
                      Event markers come from the dedicated World Monitor live route with geo resolved from signal raw data or region centres.
                    </div>
                  </div>
                  <div className="rounded-lg border border-white/10 bg-black/20 px-4 py-3">
                    <div className="text-[10px] font-semibold uppercase tracking-[0.06em] text-white/50">Convergence overlay</div>
                    <div className="mt-2 text-[12px] leading-5 text-white/70">
                      Large orange fields indicate multi-domain convergence cells from the live heatmap accumulator.
                    </div>
                  </div>
                  <div className="rounded-lg border border-white/10 bg-black/20 px-4 py-3">
                    <div className="text-[10px] font-semibold uppercase tracking-[0.06em] text-white/50">Current limitation</div>
                    <div className="mt-2 text-[12px] leading-5 text-white/70">
                      Theatre links remain explicitly inferred through convergence-cell matches. Investigation and certificate jump-offs now use persisted evidence-chain links when those records exist; otherwise the panel falls back to contextual investigation creation from the selected signal.
                    </div>
                  </div>
                </div>
              </div>
            </SectionCard>

            <div className="grid gap-4 xl:grid-cols-2">
              <SectionCard title="Signal Roster" eyebrow="OSINT feed">
                {filteredSignals.length === 0 ? (
                  <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-8 text-center text-[13px] text-[var(--e-text-muted)]">No signals match the current filters.</div>
                ) : (
                  <div className="space-y-3">
                    {filteredSignals.slice(0, 8).map((signal) => (
                      <button
                        key={signal.id}
                        type="button"
                        onClick={() => setSelectedSignalId(signal.id)}
                        className={clsx(
                          'w-full rounded-lg border px-4 py-3 text-left transition',
                          selectedSignal?.id === signal.id
                            ? 'border-[var(--e-purple-500)] bg-[var(--e-purple-50)]'
                            : 'border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] hover:border-[var(--e-border-primary)] hover:bg-[var(--e-bg-hover)]',
                        )}
                      >
                        <div className="flex flex-wrap items-center gap-2">
                          <SignalSeverityBadge severity={signal.severity} />
                          <span className="rounded-full bg-[var(--e-bg-card)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-text-muted)]">
                            {humanizeKey(signal.category)}
                          </span>
                          <span className="rounded-full bg-[var(--e-bg-card)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-text-muted)]">
                            {humanizeKey(signal.source)}
                          </span>
                          <span className="font-mono text-[11px] text-[var(--e-text-muted)]">{humanizeKey(signal.region)}</span>
                        </div>
                        <div className="mt-2 text-[13px] font-semibold text-[var(--e-text-primary)]">{signal.title}</div>
                        <div className="mt-1 text-[12px] leading-5 text-[var(--e-text-secondary)]">{signal.description}</div>
                        <div className="mt-2 flex items-center justify-between gap-3 text-[11px] text-[var(--e-text-muted)]">
                          <span>{formatTimeAgo(signal.timestamp)}</span>
                          <span className="font-mono">{Math.round(signal.confidence * 100)}% confidence</span>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </SectionCard>

              <SectionCard title="Live Feed" eyebrow="Situation Room">
                {data.live_feed.length === 0 ? (
                  <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-8 text-center text-[13px] text-[var(--e-text-muted)]">No live events yet.</div>
                ) : (
                  data.live_feed.slice(0, 8).map((event) => <FeedRow key={event.id} event={event} />)
                )}
              </SectionCard>
            </div>
          </div>

          <div className="space-y-4">
            <SectionCard title="Signal Brief" eyebrow="Selected event">
              {selectedSignal ? (
                <div className="space-y-4">
                  <div>
                    <div className="mb-2 flex flex-wrap items-center gap-2">
                      <SignalSeverityBadge severity={selectedSignal.severity} />
                      <span className="rounded-full bg-[var(--e-bg-sunken)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-text-muted)]">
                        {humanizeKey(selectedSignal.source)}
                      </span>
                      <span className="rounded-full bg-[var(--e-bg-sunken)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-text-muted)]">
                        {humanizeKey(selectedSignal.category)}
                      </span>
                    </div>
                    <h3 className="text-[18px] font-semibold leading-6 text-[var(--e-text-primary)]">
                      {selectedSignal.title}
                    </h3>
                    <p className="mt-2 text-[13px] leading-6 text-[var(--e-text-secondary)]">
                      {selectedSignal.description}
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
                      <div className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                        Region
                      </div>
                      <div className="mt-1 text-[13px] font-semibold text-[var(--e-text-primary)]">
                        {humanizeKey(selectedSignal.region)}
                      </div>
                    </div>
                    <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
                      <div className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                        Confidence
                      </div>
                      <div className="mt-1 font-mono text-[13px] font-semibold text-[var(--e-text-primary)]">
                        {Math.round(selectedSignal.confidence * 100)}%
                      </div>
                    </div>
                    <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
                      <div className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                        Observed
                      </div>
                      <div className="mt-1 font-mono text-[13px] font-semibold text-[var(--e-text-primary)]">
                        {formatTimeAgo(selectedSignal.timestamp)}
                      </div>
                    </div>
                    <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
                      <div className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                        Correlations
                      </div>
                      <div className="mt-1 font-mono text-[13px] font-semibold text-[var(--e-text-primary)]">
                        {selectedSignal.correlated_signals.length}
                      </div>
                    </div>
                  </div>

                  <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-4">
                    <div className="mb-3 flex items-center justify-between gap-3">
                      <div>
                        <div className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                          Evidence chain
                        </div>
                        <div className="mt-1 text-[12px] text-[var(--e-text-secondary)]">
                          Context first, persisted evidence second, verifiable output last.
                        </div>
                      </div>
                      <Link
                        to={buildSignalMapLink(selectedSignal)}
                        className="inline-flex h-9 items-center gap-2 rounded-md border border-[var(--e-purple-500)] bg-[var(--e-purple-500)] px-3 text-[12px] font-semibold text-white no-underline transition hover:bg-[var(--e-purple-400)]"
                      >
                        <Sparkles className="h-3.5 w-3.5" />
                        Open in Signal Map
                      </Link>
                    </div>

                    <div className="space-y-3">
                      <EvidenceChainStep
                        tone="muted"
                        title="Geo match"
                        description={
                          relatedTheatres.length > 0
                            ? 'This signal is near theatres in the matched convergence cell. Useful context, but not a hard ownership link.'
                            : 'No nearby theatre constructs are linked for this signal in the current live contract.'
                        }
                      >
                        {relatedTheatres.length > 0 ? (
                          <div className="space-y-2">
                            <div className="flex flex-wrap gap-2">
                              {relatedTheatres.map((theatreId) => (
                                <Link
                                  key={theatreId}
                                  to={`/theatre/${theatreId}`}
                                  className="inline-flex h-9 items-center gap-2 rounded-md border border-[var(--e-border-primary)] bg-white px-3 text-[12px] font-semibold text-[var(--e-text-secondary)] no-underline transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]"
                                >
                                  <ExternalLink className="h-3.5 w-3.5" />
                                  {theatreId}
                                </Link>
                              ))}
                            </div>
                            <p className="text-[12px] leading-5 text-[var(--e-text-muted)]">
                              Inferred link via <span className="font-mono">convergence_cell_geo_match</span>.
                            </p>
                          </div>
                        ) : null}
                      </EvidenceChainStep>

                      <EvidenceChainStep
                        tone={selectedSignal.investigation_id ? 'persisted' : 'muted'}
                        title="Ingested into investigation"
                        description={
                          selectedSignal.investigation_id
                            ? `This signal was receipted into Investigation ${selectedSignal.investigation_id} through the persisted evidence chain.`
                            : 'This signal has not yet been linked to a persisted investigation ingestion record.'
                        }
                      >
                        {selectedSignal.investigation_id ? (
                          <div className="flex flex-wrap items-center gap-2">
                            <Link
                              to={`/investigation?investigation=${selectedSignal.investigation_id}`}
                              className="inline-flex h-9 items-center gap-2 rounded-md border border-[var(--e-purple-200)] bg-white px-3 text-[12px] font-semibold text-[var(--e-purple-700)] no-underline transition hover:bg-[var(--e-purple-50)]"
                            >
                              Open Investigation
                            </Link>
                            <span className="text-[12px] text-[var(--e-text-muted)]">
                              Persisted link via <span className="font-mono">signal_ingested</span>.
                            </span>
                          </div>
                        ) : (
                          <div className="flex flex-wrap items-center gap-2">
                            <Link
                              to={buildCreateInvestigationLink(selectedSignal)}
                              className="inline-flex h-9 items-center gap-2 rounded-md border border-[var(--e-purple-200)] bg-white px-3 text-[12px] font-semibold text-[var(--e-purple-700)] no-underline transition hover:bg-[var(--e-purple-50)]"
                            >
                              Create Investigation
                            </Link>
                            <span className="text-[12px] text-[var(--e-text-muted)]">
                              No persisted investigation link yet. Start a bounded inquiry from this signal context.
                            </span>
                          </div>
                        )}
                      </EvidenceChainStep>

                      <EvidenceChainStep
                        tone={selectedSignal.certificate_id ? 'verified' : 'muted'}
                        title="Produced certificate"
                        description={
                          selectedSignal.certificate_id && selectedSignal.investigation_id
                            ? `Investigation ${selectedSignal.investigation_id} produced Certificate ${selectedSignal.certificate_id}.`
                            : selectedSignal.investigation_id
                              ? 'The linked investigation has not produced a persisted certificate record yet.'
                              : 'A certificate link only appears after a persisted investigation in this evidence chain produces one.'
                        }
                      >
                        {selectedSignal.certificate_id ? (
                          <div className="flex flex-wrap items-center gap-2">
                            <Link
                              to={`/verify?certificate=${selectedSignal.certificate_id}`}
                              className="inline-flex h-9 items-center gap-2 rounded-md border border-[color:oklch(0.723_0.173_150_/_0.24)] bg-white px-3 text-[12px] font-semibold text-[var(--e-green-700)] no-underline transition hover:bg-[var(--e-green-50)]"
                            >
                              Verify Certificate
                            </Link>
                            <Link
                              to={`/verify?certificate=${selectedSignal.certificate_id}`}
                              className="inline-flex h-9 items-center gap-2 rounded-md border border-[var(--e-border-primary)] bg-white px-3 text-[12px] font-semibold text-[var(--e-text-secondary)] no-underline transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]"
                            >
                              Open Certificate
                            </Link>
                            <span className="text-[12px] text-[var(--e-text-muted)]">
                              Persisted link via <span className="font-mono">investigation_certificate</span>.
                            </span>
                          </div>
                        ) : null}
                      </EvidenceChainStep>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-8 text-center text-[13px] text-[var(--e-text-muted)]">
                  Select a marker or a roster item to inspect the event, nearby theatres, and evidence-chain links.
                </div>
              )}
            </SectionCard>

            <SectionCard title="Intel Desk" eyebrow="Purchased / available">
              {data.intel.length === 0 ? (
                <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-8 text-center text-[13px] text-[var(--e-text-muted)]">No intel available right now.</div>
              ) : (
                data.intel.slice(0, 6).map((item) => <IntelRow key={item.id} item={item} />)
              )}
            </SectionCard>

            <SectionCard title="Monitor Pulse" eyebrow="Status">
              <div className="space-y-3">
                <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
                  <div className="mb-1 flex items-center gap-2 text-[var(--e-text-primary)]">
                    <BellRing className="h-4 w-4 text-[var(--e-purple-700)]" />
                    <span className="font-semibold">Tension</span>
                  </div>
                  <div className="font-mono text-[22px] font-bold tabular-nums text-[var(--e-text-primary)]">{Math.round(data.summary.tension_index)}</div>
                  <div className="mt-1 text-[12px] text-[var(--e-text-muted)]">{humanizeKey(data.summary.tension_level)}</div>
                </div>

                <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
                  <div className="mb-1 flex items-center gap-2 text-[var(--e-text-primary)]">
                    <Activity className="h-4 w-4 text-[var(--e-orange-600)]" />
                    <span className="font-semibold">Chaos Index</span>
                  </div>
                  <div className="font-mono text-[22px] font-bold tabular-nums text-[var(--e-text-primary)]">{Math.round(data.summary.chaos_index)}</div>
                  <div className="mt-1 text-[12px] text-[var(--e-text-muted)]">{data.summary.active_agents} active agents</div>
                </div>

                <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
                  <div className="mb-1 flex items-center gap-2 text-[var(--e-text-primary)]">
                    <Globe2 className="h-4 w-4 text-[var(--e-green-600)]" />
                    <span className="font-semibold">Coverage</span>
                  </div>
                  <div className="font-mono text-[22px] font-bold tabular-nums text-[var(--e-text-primary)]">{new Set(data.signals.map((signal) => signal.region)).size}</div>
                  <div className="mt-1 text-[12px] text-[var(--e-text-muted)]">Active monitored region{new Set(data.signals.map((signal) => signal.region)).size === 1 ? '' : 's'}</div>
                </div>
              </div>
            </SectionCard>
          </div>
        </div>
      </div>
    </div>
  );
}
