import { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { clsx } from 'clsx';
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  Plus,
  Search,
  ShieldCheck,
  Siren,
  TimerReset,
} from 'lucide-react';
import { EmptyState } from '../components/empty-states/EmptyState';
import { useTheatres } from '../hooks/useTheatres';
import type { Timeline } from '../types';

type ViewFilter = 'all' | 'paradox' | 'stable';
type SortOption = 'activity' | 'volume' | 'instability';

function formatPercent(value: number) {
  return `${Math.round(value)}%`;
}

function formatCurrency(value: number) {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
  return `$${Math.round(value)}`;
}

function StatusChip({ theatre }: { theatre: Timeline }) {
  if (theatre.has_active_paradox) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-red-600)]">
        <span className="h-2 w-2 rounded-full bg-[var(--e-red-600)]" />
        Paradox Active
      </span>
    );
  }

  if (theatre.hours_until_reaper !== null && theatre.hours_until_reaper <= 24) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-[color:oklch(0.708_0.136_62_/_0.20)] bg-[color:oklch(0.708_0.136_62_/_0.10)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-orange-600)]">
        <TimerReset className="h-3 w-3" />
        Ending Soon
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-[color:oklch(0.545_0.170_152_/_0.18)] bg-[color:oklch(0.545_0.170_152_/_0.08)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-green-600)]">
      <span className="h-2 w-2 rounded-full bg-[var(--e-green-600)]" />
      Healthy
    </span>
  );
}

function StatCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: string | number;
  tone?: 'danger' | 'warning' | 'success';
}) {
  return (
    <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-3 shadow-[var(--e-shadow-xs)]">
      <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
        {label}
      </div>
      <div
        className={clsx(
          'font-mono text-[24px] font-bold leading-8 tabular-nums',
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
    </div>
  );
}

function TheatreCard({ theatre }: { theatre: Timeline }) {
  const lowLiquidity = theatre.liquidity_depth_usd < 75_000;

  return (
    <article className="overflow-hidden rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)] transition hover:-translate-y-0.5 hover:border-[var(--e-purple-200)] hover:shadow-[var(--e-shadow-md)]">
      <div className="space-y-4 px-5 py-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <span className="rounded-full border border-[var(--e-purple-200)] bg-[var(--e-purple-50)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-purple-700)]">
                Theatre
              </span>
              <StatusChip theatre={theatre} />
            </div>
            <h2 className="text-[17px] font-semibold leading-6 tracking-[-0.01em] text-[var(--e-text-primary)]">
              {theatre.name}
            </h2>
            <div className="mt-2 font-mono text-[11px] text-[var(--e-text-muted)]">
              {theatre.id}
            </div>
          </div>

          <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-3 py-2 text-right">
            <div className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              Stability
            </div>
            <div className="font-mono text-[18px] font-bold tabular-nums text-[var(--e-text-primary)]">
              {formatPercent(theatre.stability)}
            </div>
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
            <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              Market
            </div>
            <div className="flex items-end justify-between">
              <div>
                <div className="text-[11px] text-[var(--e-text-muted)]">Yes</div>
                <div className="font-mono text-[18px] font-bold tabular-nums text-[var(--e-green-600)]">
                  {Math.round(theatre.price_yes * 100)}¢
                </div>
              </div>
              <div className="text-right">
                <div className="text-[11px] text-[var(--e-text-muted)]">No</div>
                <div className="font-mono text-[18px] font-bold tabular-nums text-[var(--e-red-600)]">
                  {Math.round(theatre.price_no * 100)}¢
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
            <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              Risk Context
            </div>
            <div className="space-y-1 text-[12px] text-[var(--e-text-secondary)]">
              <div className="flex items-center justify-between">
                <span>Logic Gap</span>
                <span className="font-mono text-[var(--e-text-primary)] tabular-nums">
                  {Math.round(theatre.logic_gap * 100)}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>Agents</span>
                <span className="font-mono text-[var(--e-text-primary)] tabular-nums">
                  {theatre.active_agent_count}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>Liquidity</span>
                <span
                  className={clsx(
                    'font-mono tabular-nums',
                    lowLiquidity ? 'text-[var(--e-orange-600)]' : 'text-[var(--e-text-primary)]',
                  )}
                >
                  {formatCurrency(theatre.liquidity_depth_usd)}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-3 rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              Volume
            </div>
            <div className="mt-1 font-mono text-[12px] font-semibold tabular-nums text-[var(--e-text-primary)]">
              {formatCurrency(theatre.total_volume_usd)}
            </div>
          </div>
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              Alignment
            </div>
            <div className="mt-1 font-mono text-[12px] font-semibold tabular-nums text-[var(--e-text-primary)]">
              {formatPercent(theatre.osint_alignment)}
            </div>
          </div>
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              Gravity
            </div>
            <div className="mt-1 font-mono text-[12px] font-semibold tabular-nums text-[var(--e-text-primary)]">
              {theatre.gravity_score}
            </div>
          </div>
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              Reaper
            </div>
            <div className="mt-1 font-mono text-[12px] font-semibold tabular-nums text-[var(--e-text-primary)]">
              {theatre.hours_until_reaper === null ? '—' : `${Math.round(theatre.hours_until_reaper)}h`}
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-[var(--e-border-secondary)] pt-4">
          <div className="flex flex-wrap items-center gap-2 text-[12px] text-[var(--e-text-secondary)]">
            {theatre.has_active_paradox ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-[var(--e-red-50)] px-2 py-0.5 text-[11px] font-medium text-[var(--e-red-600)]">
                <Siren className="h-3 w-3" />
                Paradox in play
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 rounded-full bg-[color:oklch(0.545_0.170_152_/_0.08)] px-2 py-0.5 text-[11px] font-medium text-[var(--e-green-600)]">
                <ShieldCheck className="h-3 w-3" />
                Stable
              </span>
            )}
            {lowLiquidity ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-[color:oklch(0.708_0.136_62_/_0.10)] px-2 py-0.5 text-[11px] font-medium text-[var(--e-orange-600)]">
                <AlertTriangle className="h-3 w-3" />
                Low liquidity
              </span>
            ) : null}
          </div>

          <Link
            to={`/theatre/${theatre.id}`}
            className="inline-flex items-center gap-1.5 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 py-2 text-[12px] font-semibold text-[var(--e-text-secondary)] no-underline transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-purple-700)]"
          >
            Open Theatre
            <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>
    </article>
  );
}

export function MarketplacePage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [viewFilter, setViewFilter] = useState<ViewFilter>('all');
  const [sortBy, setSortBy] = useState<SortOption>('activity');

  const { theatres, total, isLoading, error, isEmpty } = useTheatres({
    sortBy:
      sortBy === 'activity'
        ? 'stability'
        : sortBy === 'volume'
          ? 'volume'
          : 'logic_gap',
    sortOrder: sortBy === 'instability' ? 'desc' : 'desc',
    limit: 100,
  });

  const filtered = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return theatres
      .filter((theatre) => {
        if (viewFilter === 'paradox') return theatre.has_active_paradox;
        if (viewFilter === 'stable') return !theatre.has_active_paradox;
        return true;
      })
      .filter((theatre) => {
        if (!needle) return true;
        return (
          theatre.name.toLowerCase().includes(needle) ||
          theatre.id.toLowerCase().includes(needle) ||
          (theatre.dominant_agent_name ?? '').toLowerCase().includes(needle)
        );
      });
  }, [search, theatres, viewFilter]);

  const paradoxCount = theatres.filter((theatre) => theatre.has_active_paradox).length;
  const stableCount = theatres.filter((theatre) => !theatre.has_active_paradox).length;
  const avgStability =
    theatres.length > 0
      ? Math.round(theatres.reduce((sum, theatre) => sum + theatre.stability, 0) / theatres.length)
      : 0;
  const lowLiquidityCount = theatres.filter((theatre) => theatre.liquidity_depth_usd < 75_000).length;

  return (
    <div className="p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <p className="max-w-3xl text-[15px] leading-6 text-[var(--e-text-secondary)]">
            Browse live theatres, inspect paradox pressure, and open the full theatre surface for deployment and resolution context.
          </p>
          <button
            type="button"
            onClick={() => navigate('/theatres/create')}
            className="inline-flex items-center gap-2 rounded-lg bg-[var(--e-purple-500)] px-4 py-2.5 text-[13px] font-semibold text-white transition hover:bg-[var(--e-purple-400)]"
          >
            <Plus className="h-4 w-4" />
            Create Theatre
          </button>
        </div>

        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Total Theatres" value={total} />
          <StatCard label="Paradox Active" value={paradoxCount} tone={paradoxCount > 0 ? 'danger' : undefined} />
          <StatCard label="Average Stability" value={`${avgStability}%`} tone="success" />
          <StatCard label="Low Liquidity" value={lowLiquidityCount} tone={lowLiquidityCount > 0 ? 'warning' : undefined} />
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="inline-flex rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] p-1 shadow-[var(--e-shadow-xs)]">
            {[
              { id: 'all', label: 'All', count: total },
              { id: 'paradox', label: 'Paradox Active', count: paradoxCount },
              { id: 'stable', label: 'Stable', count: stableCount },
            ].map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setViewFilter(tab.id as ViewFilter)}
                className={clsx(
                  'inline-flex items-center gap-2 rounded-md px-3 py-2 text-[13px] font-medium transition',
                  viewFilter === tab.id
                    ? 'bg-[var(--e-purple-50)] text-[var(--e-purple-700)]'
                    : 'text-[var(--e-text-secondary)] hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]',
                )}
              >
                {tab.label}
                <span className="font-mono text-[11px] tabular-nums text-[var(--e-text-muted)]">
                  {tab.count}
                </span>
              </button>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--e-text-muted)]" />
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search theatres…"
                className="h-10 w-64 rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] pl-9 pr-4 text-[13px] text-[var(--e-text-primary)] outline-none transition placeholder:text-[var(--e-text-muted)] focus:border-[var(--e-border-focus)]"
              />
            </div>

            <select
              value={sortBy}
              onChange={(event) => setSortBy(event.target.value as SortOption)}
              className="h-10 rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 text-[13px] text-[var(--e-text-secondary)] outline-none transition focus:border-[var(--e-border-focus)]"
            >
              <option value="activity">Most Stable</option>
              <option value="volume">Highest Volume</option>
              <option value="instability">Highest Instability</option>
            </select>
          </div>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-6 py-16 shadow-[var(--e-shadow-xs)]">
            <Activity className="mr-2 h-5 w-5 animate-pulse text-[var(--e-text-muted)]" />
            <span className="text-[14px] text-[var(--e-text-muted)]">Loading theatres…</span>
          </div>
        ) : error ? (
          <div className="rounded-lg border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] px-5 py-4 text-[13px] text-[var(--e-red-600)] shadow-[var(--e-shadow-xs)]">
            {(error as Error)?.message ?? 'Failed to load theatres'}
          </div>
        ) : isEmpty ? (
          <EmptyState
            type="ZERO_STATE"
            icon={<Activity className="h-7 w-7" />}
            title="No theatres yet"
            description="Create a theatre from a template to start generating live markets and runtime state."
            actions={[
              {
                label: 'Create Theatre',
                onClick: () => navigate('/theatres/create'),
                variant: 'primary',
              },
            ]}
          />
        ) : filtered.length === 0 ? (
          <EmptyState
            type="NO_RESULTS"
            filterDescription={search || viewFilter !== 'all' ? `${viewFilter !== 'all' ? viewFilter : ''} ${search}`.trim() : undefined}
            onClearFilters={() => {
              setSearch('');
              setViewFilter('all');
            }}
          />
        ) : (
          <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
            {filtered.map((theatre) => (
              <TheatreCard key={theatre.id} theatre={theatre} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
