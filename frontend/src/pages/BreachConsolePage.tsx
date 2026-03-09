import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { clsx } from 'clsx';
import {
  AlertTriangle,
  ArrowUpRight,
  CheckCircle2,
  Clock3,
  Loader2,
  Shield,
  Siren,
  Trash2,
} from 'lucide-react';
import { useParadoxConsole } from '../hooks/useParadoxConsole';
import type { Paradox, SeverityClass } from '../types';

type Severity = 'CRITICAL' | 'URGENT' | 'WATCH';
type PageState = 'CLEAR' | 'ACTIVE' | 'CRITICAL';

function severityFromClass(cls: SeverityClass): Severity {
  if (cls === 'CLASS_1_CRITICAL') return 'CRITICAL';
  if (cls === 'CLASS_2_SEVERE') return 'URGENT';
  return 'WATCH';
}

function formatCountdown(seconds: number): string {
  if (seconds <= 0) return '0s';
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  if (hours > 0) return `${hours}h ${minutes}m`;
  if (minutes > 0) return `${minutes}m ${secs}s`;
  return `${secs}s`;
}

function timeAgo(iso: string): string {
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(iso).getTime()) / 1000));
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

function countdownTier(paradox: Paradox): 'normal' | 'amber' | 'red' | 'critical' {
  if (paradox.time_remaining_seconds <= 3600) return 'critical';

  const totalWindow =
    (new Date(paradox.detonation_time).getTime() - new Date(paradox.spawned_at).getTime()) /
    1000;

  if (totalWindow <= 0) return 'critical';

  const ratio = paradox.time_remaining_seconds / totalWindow;
  if (ratio < 0.25) return 'red';
  if (ratio < 0.5) return 'amber';
  return 'normal';
}

function derivePageState(paradoxes: Paradox[]): PageState {
  if (paradoxes.length === 0) return 'CLEAR';
  const criticalCount = paradoxes.filter((item) => item.severity_class === 'CLASS_1_CRITICAL').length;
  const urgentCount = paradoxes.filter((item) => item.severity_class === 'CLASS_2_SEVERE').length;
  return criticalCount + urgentCount >= 2 ? 'CRITICAL' : 'ACTIVE';
}

function AttentionStrip({
  pageState,
  paradoxes,
}: {
  pageState: PageState;
  paradoxes: Paradox[];
}) {
  if (pageState === 'CLEAR') {
    return (
      <div className="flex items-center gap-3 rounded-lg border border-[color:oklch(0.545_0.170_152_/_0.18)] bg-[color:oklch(0.545_0.170_152_/_0.08)] px-5 py-3 text-[13px] leading-5">
        <CheckCircle2 className="h-4 w-4 shrink-0 text-[var(--e-green-600)]" />
        <span className="font-semibold text-[var(--e-green-700)]">All Clear</span>
        <span className="text-[var(--e-text-secondary)]">
          No active contradictions. Markets are operating within expected parameters.
        </span>
      </div>
    );
  }

  const criticalCount = paradoxes.filter((item) => item.severity_class === 'CLASS_1_CRITICAL').length;
  const urgentCount = paradoxes.filter((item) => item.severity_class === 'CLASS_2_SEVERE').length;
  const watchCount = paradoxes.filter(
    (item) =>
      item.severity_class === 'CLASS_3_MODERATE' || item.severity_class === 'CLASS_4_MINOR',
  ).length;
  const imminentCount = paradoxes.filter((item) => item.time_remaining_seconds <= 3600).length;
  const critical = pageState === 'CRITICAL';

  return (
    <div
      className={clsx(
        'flex flex-wrap items-center gap-3 rounded-lg border px-5 py-3 text-[13px] leading-5',
        critical
          ? 'border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)]'
          : 'border-[color:oklch(0.708_0.136_62_/_0.20)] bg-[color:oklch(0.708_0.136_62_/_0.10)]',
      )}
    >
      <AlertTriangle
        className={clsx(
          'h-4 w-4 shrink-0',
          critical ? 'text-[var(--e-red-600)]' : 'text-[var(--e-orange-600)]',
        )}
      />
      <span
        className={clsx(
          'font-semibold',
          critical ? 'text-[var(--e-red-600)]' : 'text-[var(--e-orange-600)]',
        )}
      >
        {paradoxes.length} Active Paradoxes
      </span>
      <span className="text-[var(--e-text-secondary)]">
        {criticalCount > 0 ? `${criticalCount} Critical` : null}
        {criticalCount > 0 && urgentCount > 0 ? ' · ' : null}
        {urgentCount > 0 ? `${urgentCount} Urgent` : null}
        {(criticalCount > 0 || urgentCount > 0) && watchCount > 0 ? ' · ' : null}
        {watchCount > 0 ? `${watchCount} Watch` : null}
        {imminentCount > 0 ? ` · ${imminentCount} detonation in <1h` : null}
      </span>
    </div>
  );
}

function StatCard({
  label,
  value,
  tone,
  windowLabel,
}: {
  label: string;
  value: string | number;
  tone?: 'danger' | 'warning' | 'success';
  windowLabel?: string;
}) {
  return (
    <div
      className={clsx(
        'rounded-lg border bg-[var(--e-bg-card)] px-4 py-3 shadow-[var(--e-shadow-xs)]',
        tone === 'danger'
          ? 'border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)]'
          : 'border-[var(--e-border-primary)]',
      )}
    >
      <div className="mb-1 flex items-center justify-between gap-2">
        <div className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
          {label}
        </div>
        {windowLabel ? (
          <span className="rounded bg-[var(--e-bg-sunken)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--e-text-muted)]">
            {windowLabel}
          </span>
        ) : null}
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

function SeverityChip({ severity }: { severity: Severity }) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em]',
        severity === 'CRITICAL'
          ? 'border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] text-[var(--e-red-600)]'
          : severity === 'URGENT'
            ? 'border-[color:oklch(0.545_0.185_25_/_0.14)] bg-[color:oklch(0.545_0.185_25_/_0.06)] text-[var(--e-red-600)]'
            : 'border-[color:oklch(0.708_0.136_62_/_0.20)] bg-[color:oklch(0.708_0.136_62_/_0.10)] text-[var(--e-orange-600)]',
      )}
    >
      {severity}
    </span>
  );
}

function Countdown({
  paradox,
}: {
  paradox: Paradox;
}) {
  const tier = countdownTier(paradox);

  return (
    <div
      className={clsx(
        'inline-flex items-center gap-1.5 rounded-full px-2 py-1 font-mono text-[11px] font-semibold tabular-nums',
        tier === 'critical'
          ? 'bg-[color:oklch(0.545_0.185_25_/_0.10)] text-[var(--e-red-600)]'
          : tier === 'red'
            ? 'bg-[color:oklch(0.545_0.185_25_/_0.06)] text-[var(--e-red-600)]'
            : tier === 'amber'
              ? 'bg-[color:oklch(0.708_0.136_62_/_0.10)] text-[var(--e-orange-600)]'
              : 'bg-[var(--e-bg-sunken)] text-[var(--e-text-secondary)]',
      )}
    >
      <Clock3 className={clsx('h-3.5 w-3.5', tier === 'critical' ? 'animate-pulse' : undefined)} />
      {formatCountdown(paradox.time_remaining_seconds)}
    </div>
  );
}

function ParadoxCard({
  paradox,
  onExtract,
  onAbandon,
  isExtracting,
  isAbandoning,
}: {
  paradox: Paradox;
  onExtract: (id: string) => void;
  onAbandon: (id: string) => void;
  isExtracting: boolean;
  isAbandoning: boolean;
}) {
  const severity = severityFromClass(paradox.severity_class);
  const countdown = countdownTier(paradox);
  const logicGapPct = Math.round(paradox.logic_gap * 100);

  return (
    <article
      className={clsx(
        'overflow-hidden rounded-xl border bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)] transition hover:shadow-[var(--e-shadow-md)]',
        severity === 'CRITICAL'
          ? 'border-[color:oklch(0.545_0.185_25_/_0.22)]'
          : severity === 'URGENT'
            ? 'border-[color:oklch(0.545_0.185_25_/_0.16)]'
            : 'border-[var(--e-border-primary)]',
        countdown === 'critical'
          ? 'ring-1 ring-[color:oklch(0.545_0.185_25_/_0.12)]'
          : undefined,
      )}
    >
      <div
        className={clsx(
          'h-1',
          severity === 'CRITICAL'
            ? 'bg-[var(--e-red-600)]'
            : severity === 'URGENT'
              ? 'bg-[color:oklch(0.545_0.185_25_/_0.70)]'
              : 'bg-[var(--e-orange-500)]',
        )}
      />

      <div className="space-y-4 px-5 py-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <h2 className="text-[17px] font-semibold tracking-[-0.01em] text-[var(--e-text-primary)]">
                {paradox.timeline_name}
              </h2>
              <span className="font-mono text-[11px] text-[var(--e-text-muted)]">
                {paradox.id.slice(0, 12)}
              </span>
            </div>
            <div
              className={clsx(
                'text-[14px] font-semibold leading-6',
                severity === 'WATCH' ? 'text-[var(--e-orange-600)]' : 'text-[var(--e-red-600)]',
              )}
            >
              Logic gap {logicGapPct}% against expected consensus.
            </div>
            <div className="mt-1 text-[13px] text-[var(--e-text-secondary)]">
              Detonation path amplified by {paradox.decay_multiplier}x decay pressure.
            </div>
          </div>

          <div className="flex flex-col items-end gap-2">
            <SeverityChip severity={severity} />
            <Countdown paradox={paradox} />
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          <section className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
            <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              Linked Entities
            </div>
            <div className="flex flex-wrap gap-2">
              <Link
                to={`/theatre/${paradox.timeline_id}`}
                className="inline-flex items-center gap-1 rounded-full border border-[var(--e-purple-200)] bg-[var(--e-purple-50)] px-2.5 py-1 text-[11px] font-medium text-[var(--e-purple-700)] no-underline transition hover:bg-[color:oklch(0.760_0.140_295_/_0.14)]"
              >
                Theatre {paradox.timeline_id.slice(0, 10)}
              </Link>
              {paradox.carrier_agent_name ? (
                <span className="inline-flex items-center gap-1 rounded-full border border-[var(--e-border-secondary)] bg-[var(--e-bg-card)] px-2.5 py-1 text-[11px] font-medium text-[var(--e-text-secondary)]">
                  Agent {paradox.carrier_agent_name}
                </span>
              ) : null}
            </div>
          </section>

          <section className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
            <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              Connected Timelines
            </div>
            <div className="text-[13px] text-[var(--e-text-secondary)]">
              {paradox.connected_timelines.length > 0
                ? `${paradox.connected_timelines.length} linked timeline${paradox.connected_timelines.length === 1 ? '' : 's'}`
                : 'No linked timelines surfaced'}
            </div>
          </section>

          <section className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
            <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              Evidence Context
            </div>
            <div className="text-[12px] leading-5 text-[var(--e-text-muted)]">
              Per-paradox evidence freshness and counter-signal context are not included in the active paradox response.
            </div>
          </section>

          <section className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
            <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              Extraction Cost
            </div>
            <div className="font-mono text-[13px] font-semibold text-[var(--e-text-primary)] tabular-nums">
              {paradox.extraction_cost_usdc.toLocaleString()} USDC
            </div>
            <div className="mt-1 font-mono text-[11px] text-[var(--e-text-muted)] tabular-nums">
              {paradox.extraction_cost_echelon.toLocaleString()} ECH · {paradox.carrier_sanity_cost}{' '}
              sanity
            </div>
          </section>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-[var(--e-border-secondary)] pt-4">
          <div className="flex flex-wrap items-center gap-3 text-[12px] text-[var(--e-text-secondary)]">
            <span
              className={clsx(
                'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em]',
                paradox.status === 'EXTRACTING'
                  ? 'bg-[var(--e-purple-50)] text-[var(--e-purple-700)]'
                  : severity === 'WATCH'
                    ? 'bg-[color:oklch(0.708_0.136_62_/_0.10)] text-[var(--e-orange-600)]'
                    : 'bg-[var(--e-red-50)] text-[var(--e-red-600)]',
              )}
            >
              {paradox.status === 'EXTRACTING' ? 'Extracting' : 'Paradox Active'}
            </span>
            <span>spawned {timeAgo(paradox.spawned_at)}</span>
            <span className="font-mono text-[var(--e-text-muted)]">
              detonation {new Date(paradox.detonation_time).toLocaleString()}
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {paradox.status === 'ACTIVE' ? (
              <>
                <button
                  type="button"
                  onClick={() => onExtract(paradox.id)}
                  disabled={isExtracting}
                  className={clsx(
                    'inline-flex items-center gap-1.5 rounded-md px-3 py-2 text-[12px] font-semibold transition',
                    severity === 'CRITICAL'
                      ? 'bg-[var(--e-red-600)] text-white hover:opacity-90'
                      : 'border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] text-[var(--e-text-secondary)] hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]',
                  )}
                >
                  {isExtracting ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Shield className="h-3.5 w-3.5" />
                  )}
                  Extract
                </button>
                <button
                  type="button"
                  onClick={() => onAbandon(paradox.id)}
                  disabled={isAbandoning}
                  className="inline-flex items-center gap-1.5 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 py-2 text-[12px] font-semibold text-[var(--e-text-secondary)] transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]"
                >
                  {isAbandoning ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Trash2 className="h-3.5 w-3.5" />
                  )}
                  Abandon
                </button>
              </>
            ) : null}

            <Link
              to={`/theatre/${paradox.timeline_id}`}
              className="inline-flex items-center gap-1.5 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 py-2 text-[12px] font-semibold text-[var(--e-text-secondary)] no-underline transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-purple-700)]"
            >
              Open Theatre
              <ArrowUpRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </div>
    </article>
  );
}

function RightRail({
  paradoxes,
  pageState,
}: {
  paradoxes: Paradox[];
  pageState: PageState;
}) {
  const criticalCount = paradoxes.filter((item) => item.severity_class === 'CLASS_1_CRITICAL').length;
  const urgentCount = paradoxes.filter((item) => item.severity_class === 'CLASS_2_SEVERE').length;
  const watchCount = paradoxes.filter(
    (item) =>
      item.severity_class === 'CLASS_3_MODERATE' || item.severity_class === 'CLASS_4_MINOR',
  ).length;

  const detonationQueue = [...paradoxes]
    .filter((item) => item.status === 'ACTIVE' || item.status === 'EXTRACTING')
    .sort((a, b) => a.time_remaining_seconds - b.time_remaining_seconds)
    .slice(0, 5);

  const carrierAgents = [...new Map(
    paradoxes
      .filter((item) => item.carrier_agent_id && item.carrier_agent_name)
      .map((item) => [
        item.carrier_agent_id,
        {
          name: item.carrier_agent_name!,
          sanity: item.carrier_agent_sanity,
        },
      ]),
  ).values()];

  return (
    <div className="space-y-4">
      {pageState === 'CRITICAL' && detonationQueue.length > 0 ? (
        <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
          <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
            <h3 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              Detonation Queue
            </h3>
          </div>
          <div className="space-y-3 px-4 py-4">
            {detonationQueue.map((item) => (
              <div key={item.id} className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <div className="truncate text-[12px] font-semibold text-[var(--e-text-primary)]">
                    {item.timeline_name}
                  </div>
                  <div className="mt-1 text-[11px] text-[var(--e-text-muted)]">
                    {severityFromClass(item.severity_class)}
                  </div>
                </div>
                <span
                  className={clsx(
                    'font-mono text-[11px] font-semibold tabular-nums',
                    countdownTier(item) === 'critical'
                      ? 'text-[var(--e-red-600)]'
                      : countdownTier(item) === 'amber'
                        ? 'text-[var(--e-orange-600)]'
                        : 'text-[var(--e-text-secondary)]',
                  )}
                >
                  {formatCountdown(item.time_remaining_seconds)}
                </span>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
        <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
          <h3 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
            Severity Distribution
          </h3>
        </div>
        <div className="space-y-3 px-4 py-4 text-[12px] text-[var(--e-text-secondary)]">
          {[
            { label: 'Critical', count: criticalCount, tone: 'bg-[var(--e-red-600)]' },
            { label: 'Urgent', count: urgentCount, tone: 'bg-[color:oklch(0.545_0.185_25_/_0.70)]' },
            { label: 'Watch', count: watchCount, tone: 'bg-[var(--e-orange-600)]' },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-2">
              <span className={clsx('h-2.5 w-2.5 rounded-full', item.tone)} />
              <span className="flex-1">{item.label}</span>
              <span className="font-mono text-[var(--e-text-primary)] tabular-nums">{item.count}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
        <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
          <h3 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
            Agent Involvement
          </h3>
        </div>
        <div className="px-4 py-4 text-[12px] text-[var(--e-text-secondary)]">
          {carrierAgents.length > 0 ? (
            <div className="space-y-3">
              {carrierAgents.map((agent) => (
                <div key={agent.name} className="flex items-center justify-between gap-3">
                  <span className="font-medium text-[var(--e-text-primary)]">{agent.name}</span>
                  <span className="font-mono text-[11px] text-[var(--e-text-muted)]">
                    sanity {agent.sanity ?? '—'}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-[var(--e-text-muted)]">
              Carrier-agent assignments are sparse in the active paradox feed.
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

export function BreachConsolePage() {
  const {
    paradoxes,
    isLoading,
    isAllClear,
    extract,
    isExtracting,
    abandon,
    isAbandoning,
  } = useParadoxConsole();
  const [actionError, setActionError] = useState<string | null>(null);

  const active = useMemo(
    () => paradoxes.filter((item) => item.status === 'ACTIVE' || item.status === 'EXTRACTING'),
    [paradoxes],
  );

  const sorted = useMemo(
    () =>
      [...active].sort((a, b) => {
        const severityOrder: Record<SeverityClass, number> = {
          CLASS_1_CRITICAL: 0,
          CLASS_2_SEVERE: 1,
          CLASS_3_MODERATE: 2,
          CLASS_4_MINOR: 3,
        };
        const severityDiff = severityOrder[a.severity_class] - severityOrder[b.severity_class];
        if (severityDiff !== 0) return severityDiff;
        return a.time_remaining_seconds - b.time_remaining_seconds;
      }),
    [active],
  );

  const pageState = useMemo(() => derivePageState(active), [active]);
  const criticalCount = useMemo(
    () => active.filter((item) => item.severity_class === 'CLASS_1_CRITICAL').length,
    [active],
  );
  const watchCount = useMemo(
    () =>
      active.filter(
        (item) =>
          item.severity_class === 'CLASS_3_MODERATE' || item.severity_class === 'CLASS_4_MINOR',
      ).length,
    [active],
  );
  const linkedTheatres = useMemo(() => new Set(active.map((item) => item.timeline_id)).size, [active]);
  const detonationWindows = useMemo(
    () => active.filter((item) => item.time_remaining_seconds <= 3600).length,
    [active],
  );

  async function handleExtract(id: string) {
    setActionError(null);
    try {
      await extract(id);
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Extraction failed');
    }
  }

  async function handleAbandon(id: string) {
    setActionError(null);
    try {
      await abandon(id);
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Abandonment failed');
    }
  }

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="mx-auto flex max-w-7xl items-center justify-center rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-6 py-16 shadow-[var(--e-shadow-xs)]">
          <Loader2 className="mr-2 h-5 w-5 animate-spin text-[var(--e-text-muted)]" />
          <span className="text-[14px] text-[var(--e-text-muted)]">Loading paradoxes…</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              Intelligence / Paradox Console
            </div>
            <h1 className="text-[34px] font-bold tracking-[-0.03em] text-[var(--e-text-primary)]">
              Paradox Console
            </h1>
            <p className="mt-2 max-w-3xl text-[15px] leading-6 text-[var(--e-text-secondary)]">
              Monitor active contradictions, detonation windows, and live extraction decisions from the real paradox feed.
            </p>
          </div>

          <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-3 shadow-[var(--e-shadow-xs)]">
            <div className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              Surface
            </div>
            <div className="mt-1 text-[13px] font-medium text-[var(--e-text-primary)]">
              Real paradox roster / honest deferred context
            </div>
          </div>
        </div>

        <AttentionStrip pageState={pageState} paradoxes={active} />

        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-7">
          <StatCard label="Active" value={active.length} windowLabel="now" />
          <StatCard label="Critical" value={criticalCount} tone={criticalCount > 0 ? 'danger' : undefined} />
          <StatCard label="Watch" value={watchCount} tone={watchCount > 0 ? 'warning' : undefined} />
          <StatCard label="Linked Theatres" value={linkedTheatres} />
          <StatCard label="Investigations" value="—" />
          <StatCard label="Detonation Windows" value={detonationWindows} tone={detonationWindows > 0 ? 'danger' : undefined} />
          <StatCard label="Resolved" value="—" windowLabel="today" tone="success" />
        </div>

        {actionError ? (
          <div className="flex items-center gap-2 rounded-lg border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] px-4 py-3 text-[13px] text-[var(--e-red-600)]">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            {actionError}
          </div>
        ) : null}

        {isAllClear ? (
          <div className="rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-8 py-16 text-center shadow-[var(--e-shadow-xs)]">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full border border-[color:oklch(0.545_0.170_152_/_0.18)] bg-[color:oklch(0.545_0.170_152_/_0.08)]">
              <CheckCircle2 className="h-7 w-7 text-[var(--e-green-600)]" />
            </div>
            <h2 className="mt-5 text-[22px] font-semibold text-[var(--e-text-primary)]">
              No active paradoxes detected
            </h2>
            <p className="mx-auto mt-3 max-w-2xl text-[15px] leading-6 text-[var(--e-text-secondary)]">
              All markets are operating within expected parameters. The paradox engine is watching for logic gaps, decayed evidence confidence, and contradiction escalation.
            </p>
            <div className="mx-auto mt-8 max-w-xl rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-4 text-left">
              <div className="mb-2 flex items-center gap-2 text-[12px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                <Siren className="h-3.5 w-3.5" />
                Recently Resolved
              </div>
              <div className="text-[13px] text-[var(--e-text-muted)]">
                No resolved paradox history available. The backend does not expose a resolved-paradox feed yet.
              </div>
            </div>
          </div>
        ) : (
          <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_300px]">
            <div className="space-y-4">
              {sorted.map((paradox) => (
                <ParadoxCard
                  key={paradox.id}
                  paradox={paradox}
                  onExtract={handleExtract}
                  onAbandon={handleAbandon}
                  isExtracting={isExtracting}
                  isAbandoning={isAbandoning}
                />
              ))}
            </div>

            <div className="space-y-4">
              <RightRail paradoxes={active} pageState={pageState} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
