/**
 * Paradox Console — Operations intelligence surface for market contradictions.
 *
 * Design ref: output/design_reference/echelon_paradox_console_v1.html
 *
 * Page state machine (3 mutually exclusive states):
 *   CLEAR:    active_paradoxes === 0  → green "All Clear"
 *   ACTIVE:   mixed severity          → amber attention strip
 *   CRITICAL: critical + urgent >= 2  → red escalated strip
 *
 * Data source: GET /api/v1/paradox/active (real API via useParadoxConsole)
 * Actions: Extract / Abandon wired to real mutations
 * Unsupported: Assign / Silence / Intervene — omitted (no backend)
 *
 * Backend limitations:
 *   - No resolved paradoxes endpoint → "Resolved" KPI shows 0, zero state has no recently resolved list
 *   - No per-paradox evidence context → evidence context block deferred
 *   - No per-paradox agent involvement → agent involvement rail deferred
 *   - Theatre price cross-reference not in paradox response → theatre ID only
 */

import { useMemo, useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Loader2,
  Shield,
  Trash2,
  Clock,
  Link as LinkIcon,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { useParadoxConsole } from '../hooks/useParadoxConsole';
import type { Paradox, SeverityClass } from '../types';

// ── Severity helpers ──────────────────────────────────────────────────────

type Severity = 'CRITICAL' | 'URGENT' | 'WATCH' | 'ASSIGNED';

function severityFromClass(cls: SeverityClass): Severity {
  if (cls === 'CLASS_1_CRITICAL') return 'CRITICAL';
  if (cls === 'CLASS_2_SEVERE') return 'URGENT';
  return 'WATCH';
}

const SEVERITY_STYLES: Record<Severity, { border: string; chip: string; text: string }> = {
  CRITICAL: {
    border: 'border-l-[3px] border-l-status-failure',
    chip: 'bg-status-failure text-white',
    text: 'text-status-failure',
  },
  URGENT: {
    border: 'border-l-[3px] border-l-status-failure/60',
    chip: 'bg-status-failure/10 text-status-failure border border-status-failure/30',
    text: 'text-status-failure',
  },
  WATCH: {
    border: 'border-l-[3px] border-l-status-warning',
    chip: 'bg-status-warning/10 text-status-warning border border-status-warning/30',
    text: 'text-status-warning',
  },
  ASSIGNED: {
    border: 'border-l-[3px] border-l-echelon-cyan',
    chip: 'bg-echelon-cyan/10 text-echelon-cyan border border-echelon-cyan/30',
    text: 'text-echelon-cyan',
  },
};

// ── Time formatting ───────────────────────────────────────────────────────

function formatCountdown(seconds: number): string {
  if (seconds <= 0) return '0s';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

function timeAgo(iso: string): string {
  const s = Math.max(0, Math.floor((Date.now() - new Date(iso).getTime()) / 1000));
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

/** Countdown escalation tier (>50% normal, <50% amber, <25% red, <1h critical) */
function countdownTier(p: Paradox): 'normal' | 'amber' | 'red' | 'critical' {
  if (p.time_remaining_seconds <= 3600) return 'critical';
  // Estimate total window from spawned_at to detonation_time
  const totalWindow = (new Date(p.detonation_time).getTime() - new Date(p.spawned_at).getTime()) / 1000;
  if (totalWindow <= 0) return 'critical';
  const ratio = p.time_remaining_seconds / totalWindow;
  if (ratio < 0.25) return 'red';
  if (ratio < 0.5) return 'amber';
  return 'normal';
}

const TIMER_STYLES: Record<string, string> = {
  normal: 'text-terminal-text',
  amber: 'text-status-warning',
  red: 'text-status-failure',
  critical: 'text-status-failure animate-pulse font-bold',
};

// ── Page state ────────────────────────────────────────────────────────────

type PageState = 'CLEAR' | 'ACTIVE' | 'CRITICAL';

function derivePageState(paradoxes: Paradox[]): PageState {
  if (paradoxes.length === 0) return 'CLEAR';
  const criticalCount = paradoxes.filter((p) => p.severity_class === 'CLASS_1_CRITICAL').length;
  const urgentCount = paradoxes.filter((p) => p.severity_class === 'CLASS_2_SEVERE').length;
  if (criticalCount + urgentCount >= 2) return 'CRITICAL';
  return 'ACTIVE';
}

// ── Attention Strip ───────────────────────────────────────────────────────

function AttentionStrip({
  pageState,
  paradoxes,
}: {
  pageState: PageState;
  paradoxes: Paradox[];
}) {
  if (pageState === 'CLEAR') return null;

  const criticalCount = paradoxes.filter((p) => p.severity_class === 'CLASS_1_CRITICAL').length;
  const urgentCount = paradoxes.filter((p) => p.severity_class === 'CLASS_2_SEVERE').length;
  const watchCount = paradoxes.filter((p) => p.severity_class === 'CLASS_3_MODERATE' || p.severity_class === 'CLASS_4_MINOR').length;
  const imminentCount = paradoxes.filter((p) => p.time_remaining_seconds <= 3600).length;

  const isCritical = pageState === 'CRITICAL';
  const bgClass = isCritical ? 'bg-status-failure/10 border-status-failure/20' : 'bg-status-warning/10 border-status-warning/20';
  const textClass = isCritical ? 'text-status-failure' : 'text-status-warning';
  const iconClass = isCritical ? 'text-status-failure' : 'text-status-warning';

  return (
    <div className={`flex items-center gap-3 px-5 py-2.5 rounded-lg border ${bgClass}`}>
      <AlertTriangle className={`w-4 h-4 shrink-0 ${iconClass}`} />
      <span className={`text-[13px] font-semibold ${textClass}`}>
        {paradoxes.length} Active Paradox{paradoxes.length !== 1 ? 'es' : ''}
      </span>
      <span className="text-[12px] text-terminal-text-muted">
        {criticalCount > 0 && <span className="text-status-failure font-semibold">{criticalCount} Critical</span>}
        {criticalCount > 0 && (urgentCount > 0 || watchCount > 0) && ' · '}
        {urgentCount > 0 && <span className="text-status-failure">{urgentCount} Urgent</span>}
        {urgentCount > 0 && watchCount > 0 && ' · '}
        {watchCount > 0 && <span className="text-status-warning">{watchCount} Watch</span>}
        {imminentCount > 0 && (
          <>
            {' · '}
            <span className="text-status-failure font-semibold">{imminentCount} detonation in &lt;1h</span>
          </>
        )}
      </span>
    </div>
  );
}

// ── Paradox Card ──────────────────────────────────────────────────────────

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
  const sev = severityFromClass(paradox.severity_class);
  const style = SEVERITY_STYLES[sev];
  const tier = countdownTier(paradox);
  const timerStyle = TIMER_STYLES[tier];
  const gapPct = Math.round(paradox.logic_gap * 100);

  // Card elevation for high-urgency
  const cardElevation = tier === 'critical' || tier === 'red'
    ? 'shadow-sm'
    : '';

  return (
    <div
      className={`bg-terminal-surface border border-terminal-border rounded-lg overflow-hidden ${style.border} ${cardElevation}`}
    >
      {/* Header */}
      <div className="px-4 py-3 flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className="text-[14px] font-semibold text-terminal-text leading-tight">
              {paradox.timeline_name}
            </span>
            <span className="font-mono text-[10px] text-terminal-text-muted">
              {paradox.id.slice(0, 12)}
            </span>
          </div>
          <div className="text-[12px] text-terminal-text-secondary leading-tight">
            Logic gap {gapPct}% — Decay {paradox.decay_multiplier}x
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${style.chip}`}>
            {sev}
          </span>
          <div className="flex items-center gap-1">
            <Clock className={`w-3 h-3 ${timerStyle}`} />
            <span className={`font-mono text-[12px] font-semibold tabular-nums ${timerStyle}`}>
              {formatCountdown(paradox.time_remaining_seconds)}
            </span>
          </div>
        </div>
      </div>

      {/* Body — 2-column context grid */}
      <div className="px-4 pb-3">
        <div className="grid grid-cols-2 gap-3 text-[11px]">
          {/* Linked Entities */}
          <div>
            <div className="text-[10px] font-bold uppercase tracking-wider text-terminal-text-muted mb-1.5">
              Linked Entities
            </div>
            <div className="flex flex-wrap gap-1">
              <Link
                to={`/theatre/${paradox.timeline_id}`}
                className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono bg-purple-500/8 text-purple-500 border border-purple-500/20 hover:bg-purple-500/15 transition-colors"
              >
                <LinkIcon className="w-2.5 h-2.5" />
                {paradox.timeline_id.slice(0, 10)}
              </Link>
              {paradox.carrier_agent_name && (
                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono bg-terminal-panel text-terminal-text-muted border border-terminal-border">
                  {paradox.carrier_agent_name}
                </span>
              )}
            </div>
          </div>

          {/* Connected Timelines */}
          <div>
            <div className="text-[10px] font-bold uppercase tracking-wider text-terminal-text-muted mb-1.5">
              Connected
            </div>
            {paradox.connected_timelines.length > 0 ? (
              <span className="font-mono text-terminal-text tabular-nums">
                {paradox.connected_timelines.length} timeline{paradox.connected_timelines.length !== 1 ? 's' : ''}
              </span>
            ) : (
              <span className="text-terminal-text-muted">—</span>
            )}
          </div>

          {/* Extraction Cost */}
          <div>
            <div className="text-[10px] font-bold uppercase tracking-wider text-terminal-text-muted mb-1.5">
              Extraction Cost
            </div>
            <div className="font-mono text-terminal-text tabular-nums">
              {paradox.extraction_cost_usdc.toLocaleString()} USDC
            </div>
            <div className="font-mono text-terminal-text-muted tabular-nums text-[10px]">
              {paradox.extraction_cost_echelon.toLocaleString()} ECH · {paradox.carrier_sanity_cost} sanity
            </div>
          </div>

          {/* Detonation */}
          <div>
            <div className="text-[10px] font-bold uppercase tracking-wider text-terminal-text-muted mb-1.5">
              Detonation
            </div>
            <div className="font-mono text-terminal-text tabular-nums text-[10px]">
              {new Date(paradox.detonation_time).toLocaleString()}
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="px-4 py-2.5 border-t border-terminal-border/50 bg-terminal-panel flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className={`text-[10px] font-mono font-semibold uppercase ${
            paradox.status === 'EXTRACTING' ? 'text-echelon-cyan' : style.text
          }`}>
            {paradox.status === 'EXTRACTING' ? 'Extracting' : 'Paradox Active'}
          </span>
          <span className="text-[10px] font-mono text-terminal-text-muted">
            spawned {timeAgo(paradox.spawned_at)}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          {paradox.status === 'ACTIVE' && (
            <>
              <button
                onClick={() => onExtract(paradox.id)}
                disabled={isExtracting}
                className={`inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-semibold rounded border transition-colors ${
                  sev === 'CRITICAL'
                    ? 'bg-status-failure text-white border-status-failure hover:opacity-90'
                    : 'text-terminal-text-secondary bg-terminal-surface border-terminal-border hover:text-terminal-text hover:border-terminal-text-muted'
                } disabled:opacity-50`}
              >
                {isExtracting ? <Loader2 className="w-3 h-3 animate-spin" /> : <Shield className="w-3 h-3" />}
                Extract
              </button>
              <button
                onClick={() => onAbandon(paradox.id)}
                disabled={isAbandoning}
                className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-semibold rounded border text-terminal-text-secondary bg-terminal-surface border-terminal-border hover:text-terminal-text hover:border-terminal-text-muted transition-colors disabled:opacity-50"
              >
                {isAbandoning ? <Loader2 className="w-3 h-3 animate-spin" /> : <Trash2 className="w-3 h-3" />}
                Abandon
              </button>
            </>
          )}
          <Link
            to={`/theatre/${paradox.timeline_id}`}
            className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-semibold rounded border text-terminal-text-secondary bg-terminal-surface border-terminal-border hover:text-purple-500 hover:border-purple-500/30 transition-colors"
          >
            Open Theatre
          </Link>
        </div>
      </div>
    </div>
  );
}

// ── Right Rail ────────────────────────────────────────────────────────────

function RightRail({ paradoxes }: { paradoxes: Paradox[] }) {
  const criticalCount = paradoxes.filter((p) => p.severity_class === 'CLASS_1_CRITICAL').length;
  const urgentCount = paradoxes.filter((p) => p.severity_class === 'CLASS_2_SEVERE').length;
  const watchCount = paradoxes.filter((p) => p.severity_class === 'CLASS_3_MODERATE' || p.severity_class === 'CLASS_4_MINOR').length;

  // Detonation queue — sorted by time remaining
  const detonationQueue = [...paradoxes]
    .filter((p) => p.status === 'ACTIVE')
    .sort((a, b) => a.time_remaining_seconds - b.time_remaining_seconds)
    .slice(0, 5);

  return (
    <div className="flex flex-col gap-4 sticky top-6">
      {/* Detonation Queue */}
      {detonationQueue.length > 0 && (
        <div className="bg-terminal-surface rounded-lg border border-terminal-border overflow-hidden">
          <div className="px-4 py-2.5 border-b border-terminal-border/50 bg-terminal-panel">
            <h3 className="text-[11px] font-bold uppercase tracking-wider text-terminal-text-muted">
              Detonation Queue
            </h3>
          </div>
          <div className="px-4 py-2">
            {detonationQueue.map((p) => {
              const tier = countdownTier(p);
              const sev = severityFromClass(p.severity_class);
              return (
                <div
                  key={p.id}
                  className="flex items-center justify-between py-2 border-b border-terminal-border/30 last:border-b-0"
                >
                  <div className="flex items-center gap-2 min-w-0 flex-1">
                    <span className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-bold uppercase ${SEVERITY_STYLES[sev].chip}`}>
                      {sev.slice(0, 4)}
                    </span>
                    <span className="text-[11px] text-terminal-text truncate">
                      {p.timeline_name}
                    </span>
                  </div>
                  <span className={`font-mono text-[11px] font-semibold tabular-nums shrink-0 ml-2 ${TIMER_STYLES[tier]}`}>
                    {formatCountdown(p.time_remaining_seconds)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Severity Distribution */}
      <div className="bg-terminal-surface rounded-lg border border-terminal-border overflow-hidden">
        <div className="px-4 py-2.5 border-b border-terminal-border/50 bg-terminal-panel">
          <h3 className="text-[11px] font-bold uppercase tracking-wider text-terminal-text-muted">
            Severity Distribution
          </h3>
        </div>
        <div className="px-4 py-3 space-y-2">
          {[
            { label: 'Critical', count: criticalCount, dot: 'bg-status-failure' },
            { label: 'Urgent', count: urgentCount, dot: 'bg-status-failure/60' },
            { label: 'Watch', count: watchCount, dot: 'bg-status-warning' },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${item.dot} shrink-0`} />
              <span className="text-[11px] text-terminal-text-secondary flex-1">{item.label}</span>
              <span className="font-mono text-[11px] font-semibold text-terminal-text tabular-nums">
                {item.count}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Agent Involvement — deferred (paradox API does not include per-paradox agent involvement) */}
      <div className="bg-terminal-surface rounded-lg border border-terminal-border overflow-hidden">
        <div className="px-4 py-2.5 border-b border-terminal-border/50 bg-terminal-panel">
          <h3 className="text-[11px] font-bold uppercase tracking-wider text-terminal-text-muted">
            Agent Involvement
          </h3>
        </div>
        <div className="px-4 py-3">
          {paradoxes.some((p) => p.carrier_agent_name) ? (
            <div className="space-y-2">
              {[...new Map(
                paradoxes
                  .filter((p) => p.carrier_agent_name)
                  .map((p) => [p.carrier_agent_id, { name: p.carrier_agent_name!, sanity: p.carrier_agent_sanity }])
              ).entries()].map(([agentId, agent]) => (
                <div key={agentId} className="flex items-center justify-between">
                  <span className="text-[11px] font-medium text-terminal-text">{agent.name}</span>
                  <span className="text-[10px] font-mono text-terminal-text-muted">
                    sanity {agent.sanity ?? '—'}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-[11px] text-terminal-text-muted/50">
              No carrier agents assigned
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────

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

  // Only ACTIVE + EXTRACTING paradoxes for display
  const active = useMemo(
    () => paradoxes.filter((p) => p.status === 'ACTIVE' || p.status === 'EXTRACTING'),
    [paradoxes],
  );

  // Sort by urgency: critical first, then by time remaining
  const sorted = useMemo(
    () => [...active].sort((a, b) => {
      const sevOrder: Record<string, number> = { CLASS_1_CRITICAL: 0, CLASS_2_SEVERE: 1, CLASS_3_MODERATE: 2, CLASS_4_MINOR: 3 };
      const sevDiff = (sevOrder[a.severity_class] ?? 3) - (sevOrder[b.severity_class] ?? 3);
      if (sevDiff !== 0) return sevDiff;
      return a.time_remaining_seconds - b.time_remaining_seconds;
    }),
    [active],
  );

  const pageState = useMemo(() => derivePageState(active), [active]);

  // Derived KPIs from real data only
  const criticalCount = useMemo(() => active.filter((p) => p.severity_class === 'CLASS_1_CRITICAL').length, [active]);
  const watchCount = useMemo(() => active.filter((p) => p.severity_class === 'CLASS_3_MODERATE' || p.severity_class === 'CLASS_4_MINOR').length, [active]);
  const linkedTheatres = useMemo(() => new Set(active.map((p) => p.timeline_id)).size, [active]);
  const detonationWindows = useMemo(() => active.filter((p) => p.time_remaining_seconds <= 3600).length, [active]);

  const handleExtract = async (id: string) => {
    setActionError(null);
    try {
      await extract(id);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Extraction failed');
    }
  };

  const handleAbandon = async (id: string) => {
    setActionError(null);
    try {
      await abandon(id);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Abandonment failed');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-5 h-5 text-terminal-text-muted animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-[1100px] mx-auto space-y-5">
      {/* Page header */}
      <div>
        <div className="text-[11px] font-mono text-terminal-text-muted mb-0.5 uppercase tracking-wider">
          Intelligence / Paradox Console
        </div>
        <h1 className="text-2xl font-bold text-terminal-text">Paradox Console</h1>
        <p className="text-[13px] text-terminal-text-secondary mt-0.5">
          Active contradictions, extraction status, and detonation monitoring
        </p>
      </div>

      {/* Attention strip */}
      <AttentionStrip pageState={pageState} paradoxes={active} />

      {/* KPI cards */}
      <div className="flex gap-4 p-3 px-5 bg-terminal-surface rounded-lg border border-terminal-border flex-wrap">
        {[
          { label: 'Active\nNow', value: String(active.length), color: active.length > 0 ? 'text-status-failure' : undefined },
          { label: 'Critical', value: String(criticalCount), color: criticalCount > 0 ? 'text-status-failure' : undefined },
          { label: 'Watch', value: String(watchCount), color: watchCount > 0 ? 'text-status-warning' : undefined },
          { label: 'Linked\nTheatres', value: String(linkedTheatres) },
          { label: 'Investigations', value: '—' },  // No investigation link in paradox response
          { label: 'Detonation\nWindows', value: String(detonationWindows), color: detonationWindows > 0 ? 'text-status-failure' : undefined },
          { label: 'Resolved\nToday', value: '—', color: 'text-status-success' },  // No resolved endpoint
        ].map((stat) => (
          <div
            key={stat.label}
            className="flex items-center gap-2 pr-4 border-r border-terminal-border/50 last:border-r-0 last:pr-0"
          >
            <span className={`font-mono text-[17px] font-bold tabular-nums ${stat.color ?? 'text-terminal-text'}`}>
              {stat.value}
            </span>
            <span className="text-[11px] font-medium text-terminal-text-muted leading-[14px] whitespace-pre-line">
              {stat.label}
            </span>
          </div>
        ))}
      </div>

      {/* Action error */}
      {actionError && (
        <div className="flex items-center gap-2 p-3 bg-status-failure/10 border border-status-failure/30 rounded-lg">
          <AlertTriangle className="w-4 h-4 text-status-failure shrink-0" />
          <span className="text-xs text-status-failure">{actionError}</span>
        </div>
      )}

      {/* CLEAR state — zero state */}
      {isAllClear && (
        <div className="bg-terminal-surface rounded-lg border border-terminal-border p-8">
          <div className="flex flex-col items-center text-center max-w-[420px] mx-auto">
            <div className="w-16 h-16 rounded-full bg-status-success/10 border border-status-success/20 flex items-center justify-center mb-5">
              <CheckCircle2 className="w-7 h-7 text-status-success" />
            </div>
            <h2 className="text-[17px] font-bold text-terminal-text mb-2">
              No Active Contradictions
            </h2>
            <p className="text-[13px] text-terminal-text-secondary leading-5 mb-6">
              All markets are operating within expected parameters. The paradox engine is monitoring for logic gaps, evidence staleness, and consensus divergence.
            </p>
            {/* Recently resolved — deferred (no endpoint) */}
            <div className="w-full text-left">
              <div className="text-[10px] font-bold uppercase tracking-wider text-terminal-text-muted mb-2">
                Recently Resolved
              </div>
              <div className="text-[12px] text-terminal-text-muted/50">
                No resolved paradox history available. Resolved paradox tracking requires a backend endpoint.
              </div>
              <div className="text-[10px] font-mono text-terminal-text-muted/30 mt-1">
                GET /api/v1/paradox/resolved — not yet available
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ACTIVE / CRITICAL state — roster + right rail */}
      {!isAllClear && (
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-5 items-start">
          {/* Paradox roster */}
          <div className="space-y-3">
            {sorted.map((p) => (
              <ParadoxCard
                key={p.id}
                paradox={p}
                onExtract={handleExtract}
                onAbandon={handleAbandon}
                isExtracting={isExtracting}
                isAbandoning={isAbandoning}
              />
            ))}
          </div>

          {/* Right rail */}
          <div className="hidden lg:block">
            <RightRail paradoxes={active} />
          </div>
        </div>
      )}
    </div>
  );
}
