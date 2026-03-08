/**
 * Investigation Dashboard
 *
 * Design ref: output/design_reference/echelon_investigations_v1.html
 *
 * Page state machine (3 mutually exclusive states):
 *   if (total === 0)        → EMPTY state (centered CTA, no strip, no KPIs)
 *   else if (stalled > 0)   → ALERT state (orange strip)
 *   else                    → ACTIVE state (green strip)
 *
 * Browse view: attention strip + 4 KPI cards + 1fr/300px grid (card list + right rail)
 * Detail view: 280px sidebar + tabbed detail panel
 *
 * KPI values derive from list-level summary fields only (evidence_count,
 * claim_count, counter_signal_count, drift_event_count). No N+1 fetches.
 *
 * "Stalled" detection: list endpoint does not surface a stalled flag or
 * last_evidence_timestamp. We derive stalled count from status === 'stalled'
 * on InvestigationSummary. If backend doesn't emit stalled status, the count
 * stays at 0 and the attention strip shows ACTIVE (honest deferral).
 */

import { useState, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  FileText,
  GitBranch,
  AlertTriangle,
  TrendingDown,
  ShieldAlert,
  ShieldCheck,
  Filter,
  Plus,
  Loader2,
  CheckCircle2,
  ArrowRight,
} from 'lucide-react';
import {
  useInvestigationList,
  useInvestigationDetail,
} from '../hooks/useInvestigation';
import { EvidenceEnvelopePanel } from '../components/investigation/EvidenceEnvelopePanel';
import { ClaimGraphPanel } from '../components/investigation/ClaimGraphPanel';
import { CounterSignalPanel } from '../components/investigation/CounterSignalPanel';
import { DriftEventsPanel } from '../components/investigation/DriftEventsPanel';
import { ReadinessCertificatePanel } from '../components/investigation/ReadinessCertificatePanel';
import { EmptyState } from '../components/empty-states/EmptyState';
import type { InvestigationSummary } from '../types/investigation';

type Tab = 'overview' | 'evidence' | 'claims' | 'counter-signals' | 'drift' | 'readiness';

const TABS: { id: Tab; label: string; icon: typeof Search; isNew?: boolean }[] = [
  { id: 'overview', label: 'Overview', icon: Search },
  { id: 'evidence', label: 'Evidence', icon: FileText },
  { id: 'claims', label: 'Claims', icon: GitBranch },
  { id: 'counter-signals', label: 'Counter-Signals', icon: AlertTriangle },
  { id: 'drift', label: 'Drift', icon: TrendingDown },
  { id: 'readiness', label: 'Readiness', icon: ShieldCheck, isNew: true },
];

/** Humanized stop-condition labels */
const STOP_LABELS: Record<string, string> = {
  OUTCOME_RESOLUTION: 'Market resolution',
  EVIDENCE_THRESHOLD: 'Evidence threshold',
  SPONSOR_DEFINED: 'Sponsor milestone',
};

// ── Status Badge ──────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const colorMap: Record<string, string> = {
    active: 'text-status-success',
    stalled: 'text-status-warning',
    completed: 'text-terminal-text-muted',
    cancelled: 'text-status-failure',
  };
  const dotColorMap: Record<string, string> = {
    active: 'bg-status-success animate-pulse',
    stalled: 'bg-status-warning',
    completed: 'bg-terminal-text-muted',
    cancelled: 'bg-status-failure',
  };
  const textColor = colorMap[status] ?? 'text-terminal-text-muted';
  const dotColor = dotColorMap[status] ?? 'bg-terminal-text-muted';

  return (
    <span className={`flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider ${textColor}`}>
      <span className={`w-[5px] h-[5px] rounded-full ${dotColor}`} />
      {status}
    </span>
  );
}

// ── Attention Strip ───────────────────────────────────────────────────────

function AttentionStrip({ stalledCount, total }: { stalledCount: number; total: number }) {
  if (total === 0) return null;

  const isAlert = stalledCount > 0;

  return (
    <div
      className={`flex items-center gap-3 px-5 py-3 rounded-lg text-[13px] leading-5 ${
        isAlert
          ? 'bg-status-warning/8 border border-status-warning/20'
          : 'bg-status-success/8 border border-status-success/20'
      }`}
    >
      {isAlert ? (
        <AlertTriangle className="w-4 h-4 text-status-warning shrink-0" />
      ) : (
        <CheckCircle2 className="w-4 h-4 text-status-success shrink-0" />
      )}
      <span className={`font-semibold whitespace-nowrap ${isAlert ? 'text-status-warning' : 'text-status-success'}`}>
        {isAlert ? 'Stalled' : 'All Active'}
      </span>
      <span className="text-terminal-text-secondary">
        {isAlert
          ? `${stalledCount} investigation${stalledCount !== 1 ? 's' : ''} stalled`
          : `All ${total} investigation${total !== 1 ? 's' : ''} progressing`}
      </span>
    </div>
  );
}

// ── Claim Status Mini-Bar ─────────────────────────────────────────────────

function ClaimStatusMiniBar({ summary }: { summary: Record<string, number> }) {
  const supported = summary.supported ?? 0;
  const partial = summary.partially_supported ?? 0;
  const unconfirmed = summary.unconfirmed ?? 0;
  const contradicted = summary.contradicted ?? 0;
  const total = supported + partial + unconfirmed + contradicted;
  if (total === 0) return null;

  return (
    <div>
      <div className="flex h-1.5 rounded overflow-hidden">
        {supported > 0 && (
          <div className="bg-status-success" style={{ width: `${(supported / total) * 100}%` }} />
        )}
        {partial > 0 && (
          <div className="bg-status-warning" style={{ width: `${(partial / total) * 100}%` }} />
        )}
        {unconfirmed > 0 && (
          <div className="bg-terminal-text-muted/30" style={{ width: `${(unconfirmed / total) * 100}%` }} />
        )}
        {contradicted > 0 && (
          <div className="bg-status-failure" style={{ width: `${(contradicted / total) * 100}%` }} />
        )}
      </div>
      <div className="flex gap-2 mt-1 text-[9px] text-terminal-text-muted">
        {supported > 0 && <span className="text-status-success">{supported} supported</span>}
        {partial > 0 && <span className="text-status-warning">{partial} partial</span>}
        {unconfirmed > 0 && <span>{unconfirmed} unconfirmed</span>}
        {contradicted > 0 && <span className="text-status-failure">{contradicted} contradicted</span>}
      </div>
    </div>
  );
}

// ── Investigation Card (browse view) ──────────────────────────────────────

function InvestigationCard({
  inv,
  onClick,
}: {
  inv: InvestigationSummary;
  onClick: () => void;
}) {
  const isStalled = inv.status === 'stalled';

  return (
    <button
      onClick={onClick}
      className={`w-full text-left bg-terminal-surface border rounded-lg p-5 transition-all hover:shadow-sm hover:-translate-y-px cursor-pointer group ${
        isStalled
          ? 'border-l-[3px] border-l-status-warning border-t-terminal-border border-r-terminal-border border-b-terminal-border hover:border-status-warning'
          : 'border-terminal-border hover:border-purple-300/40'
      }`}
    >
      {/* Top: ID + status + open arrow */}
      <div className="flex items-center gap-2 mb-2">
        <span className="font-mono text-[11px] font-semibold text-terminal-text-muted">
          {inv.id.slice(0, 12)}
        </span>
        <StatusBadge status={inv.status} />
        <span className="ml-auto flex items-center gap-1 text-[11px] font-semibold text-purple-500 opacity-0 group-hover:opacity-100 transition-opacity">
          Open <ArrowRight className="w-3 h-3" />
        </span>
      </div>

      {/* Primary label: construct_id or inquiry_class */}
      <div className="text-[14px] font-semibold text-terminal-text leading-[20px] mb-2 line-clamp-2">
        {inv.construct_id || inv.inquiry_class || inv.id.slice(0, 12)}
      </div>

      {/* Meta row: theatre chip + created date */}
      <div className="flex items-center gap-2 mb-3 text-[11px] text-terminal-text-muted">
        {inv.theatre_id && (
          <span className="font-mono px-1.5 py-0.5 rounded bg-terminal-panel border border-terminal-border/50 text-[10px]">
            {inv.theatre_id.slice(0, 12)}
          </span>
        )}
        <span>{new Date(inv.created_at).toLocaleDateString()}</span>
      </div>

      {/* Progress row */}
      <div className="flex items-center gap-3 text-[11px] text-terminal-text-muted">
        <span>{inv.evidence_count} evidence</span>
        <span className="text-terminal-border">·</span>
        <span>{inv.claim_count} claims</span>
        <span className="text-terminal-border">·</span>
        <span>{inv.counter_signal_count} signals</span>
        <span className="text-terminal-border">·</span>
        <span>{inv.drift_event_count} drift</span>
      </div>
    </button>
  );
}

// ── Right Rail ────────────────────────────────────────────────────────────

function RightRail({ investigations, selectedId }: { investigations: InvestigationSummary[]; selectedId: string | null }) {
  const selected = investigations.find((i) => i.id === selectedId);

  return (
    <div className="space-y-4">
      {/* Domain Filters — only for selected investigation detail view */}
      <div className="bg-terminal-surface rounded-lg border border-terminal-border overflow-hidden">
        <div className="px-4 py-2.5 border-b border-terminal-border/50 bg-terminal-panel flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-terminal-text-muted" />
          <h3 className="text-[11px] font-bold uppercase tracking-wider text-terminal-text-muted">
            Domain Filters
          </h3>
        </div>
        <div className="p-4">
          <div className="text-[12px] text-terminal-text-muted leading-4">
            Domain filters are committed at investigation creation and enforced at evidence/signal ingestion.
          </div>
          <div className="text-[10px] text-terminal-text-muted/50 mt-2 font-mono">
            Select an investigation to view its committed filters.
          </div>
        </div>
      </div>

      {/* Evidence Feed — deferred: requires per-investigation fetch */}
      <div className="bg-terminal-surface rounded-lg border border-terminal-border overflow-hidden">
        <div className="px-4 py-2.5 border-b border-terminal-border/50 bg-terminal-panel">
          <h3 className="text-[11px] font-bold uppercase tracking-wider text-terminal-text-muted">
            Evidence Feed
          </h3>
        </div>
        <div className="p-4">
          {selected ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-terminal-text-muted">Evidence Items</span>
                <span className="font-mono text-terminal-text">{selected.evidence_count}</span>
              </div>
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-terminal-text-muted">Claims</span>
                <span className="font-mono text-terminal-text">{selected.claim_count}</span>
              </div>
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-terminal-text-muted">Drift Events</span>
                <span className="font-mono text-terminal-text">{selected.drift_event_count}</span>
              </div>
              <div className="text-[10px] text-terminal-text-muted/50 mt-2">
                Open investigation for full evidence timeline.
              </div>
            </div>
          ) : (
            <div className="text-[11px] text-terminal-text-muted/50">
              Select an investigation to see activity summary.
            </div>
          )}
        </div>
      </div>

      {/* Provenance Breakdown — deferred to detail view (N+1 concern) */}
      <div className="bg-terminal-surface rounded-lg border border-terminal-border overflow-hidden">
        <div className="px-4 py-2.5 border-b border-terminal-border/50 bg-terminal-panel">
          <h3 className="text-[11px] font-bold uppercase tracking-wider text-terminal-text-muted">
            Provenance Breakdown
          </h3>
        </div>
        <div className="p-4">
          <div className="text-[11px] text-terminal-text-muted/50">
            Provenance breakdown requires evidence manifest data. Open an investigation detail view for per-evidence provenance analysis.
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Sidebar Item (for CERT READY badge) ───────────────────────────────────

function SidebarItem({
  inv,
  isSelected,
  onSelect,
}: {
  inv: InvestigationSummary;
  isSelected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      onClick={onSelect}
      className={`w-full text-left px-4 py-3 border-b border-terminal-border/30 transition-colors ${
        isSelected
          ? 'bg-purple-500/8 border-l-[3px] border-l-purple-500'
          : 'hover:bg-terminal-surface/50 border-l-[3px] border-l-transparent'
      }`}
    >
      <div className="flex items-center gap-2 mb-0.5">
        <span className="font-mono text-[11px] font-semibold text-terminal-text-muted">
          {inv.id.slice(0, 12)}
        </span>
        <StatusBadge status={inv.status} />
      </div>

      {(inv.construct_id || inv.inquiry_class) && (
        <div className="text-[13px] font-semibold text-terminal-text leading-tight mb-1 line-clamp-2">
          {inv.construct_id || inv.inquiry_class}
        </div>
      )}

      <div className="flex items-center gap-2 text-[11px] text-terminal-text-muted">
        <span>{inv.evidence_count} evidence</span>
        <span className="text-terminal-border">·</span>
        <span>{inv.claim_count} claims</span>
      </div>
    </button>
  );
}

// ── Investigation List Panel (sidebar in detail view) ─────────────────────

function InvestigationListPanel({
  investigations,
  selectedId,
  onSelect,
  onCreateNew,
  isLoading,
}: {
  investigations: InvestigationSummary[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onCreateNew: () => void;
  isLoading: boolean;
}) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-5 h-5 text-terminal-text-muted animate-spin" />
      </div>
    );
  }

  if (investigations.length === 0) {
    return (
      <EmptyState
        type="ZERO_STATE"
        icon={<Search className="w-7 h-7" />}
        title="No investigations yet"
        description="Investigations gather evidence, build claim graphs, and track counter-signals to inform market positions."
        actions={[
          {
            label: 'New Investigation',
            onClick: onCreateNew,
            variant: 'primary',
          },
        ]}
      />
    );
  }

  return (
    <div className="flex flex-col">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-terminal-border/50">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-terminal-text-muted">
          Investigations
        </span>
        <span className="font-mono text-[11px] font-semibold text-terminal-text-muted">
          {investigations.length}
        </span>
      </div>

      <div className="flex flex-col">
        {investigations.map((inv) => (
          <SidebarItem
            key={inv.id}
            inv={inv}
            isSelected={selectedId === inv.id}
            onSelect={() => onSelect(inv.id)}
          />
        ))}
      </div>
    </div>
  );
}

// ── Overview Tab ──────────────────────────────────────────────────────────

function OverviewTab({ investigation }: { investigation: NonNullable<ReturnType<typeof useInvestigationDetail>['investigation']> }) {
  return (
    <div className="p-5 space-y-5">
      {/* KPI cards — design ref: inv-kpi (24px mono values, separate cards) */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { label: 'Evidence', value: investigation.evidence.items.length },
          { label: 'Claims', value: investigation.claims.claims.length },
          { label: 'Counter-Signals', value: investigation.counter_signals.signals.length },
          { label: 'Drift Events', value: investigation.drift.events.length },
        ].map((stat) => (
          <div
            key={stat.label}
            className="bg-terminal-surface rounded-lg p-3 border border-terminal-border"
          >
            <div className="text-[11px] font-semibold uppercase tracking-wider text-terminal-text-muted mb-0.5">
              {stat.label}
            </div>
            <div className="text-2xl font-mono font-bold text-terminal-text tabular-nums leading-8">
              {stat.value}
            </div>
          </div>
        ))}
      </div>

      {/* Identity — design ref: detail-section with sunken header */}
      <div className="bg-terminal-surface rounded-lg border border-terminal-border overflow-hidden">
        <div className="px-5 py-2.5 border-b border-terminal-border/50 bg-terminal-panel">
          <h3 className="text-[11px] font-bold uppercase tracking-wider text-terminal-text-muted">
            Identity
          </h3>
        </div>
        <div className="p-5">
          <dl className="grid grid-cols-[140px_1fr] gap-x-4 gap-y-2 text-[13px]">
            <dt className="text-terminal-text-muted">Investigation ID</dt>
            <dd className="font-mono text-terminal-text text-xs">{investigation.id}</dd>
            <dt className="text-terminal-text-muted">Theatre</dt>
            <dd className="font-mono text-terminal-text text-xs">{investigation.theatre_id || '\u2014'}</dd>
            <dt className="text-terminal-text-muted">Construct</dt>
            <dd className="font-mono text-terminal-text text-xs">{investigation.construct_id || '\u2014'}</dd>
            <dt className="text-terminal-text-muted">Inquiry Class</dt>
            <dd className="font-mono text-terminal-text text-xs">{investigation.inquiry_class}</dd>
            <dt className="text-terminal-text-muted">Status</dt>
            <dd><StatusBadge status={investigation.status} /></dd>
            <dt className="text-terminal-text-muted">Stop Condition</dt>
            <dd className="font-mono text-terminal-text text-xs">
              {STOP_LABELS[investigation.stop_condition] ?? investigation.stop_condition}
            </dd>
          </dl>
        </div>
      </div>

      {/* Domain filters — committed at creation, enforced at ingestion */}
      {investigation.domain_filters && investigation.domain_filters.length > 0 && (
        <div className="bg-terminal-surface rounded-lg border border-terminal-border overflow-hidden">
          <div className="px-5 py-2.5 border-b border-terminal-border/50 bg-terminal-panel flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-terminal-text-muted" />
            <h3 className="text-[11px] font-bold uppercase tracking-wider text-terminal-text-muted">
              Domain Filters
            </h3>
            <span className="font-mono text-[11px] text-terminal-text-muted ml-auto">
              {investigation.domain_filters.length} active
            </span>
          </div>
          <div className="p-5">
            <div className="flex flex-wrap gap-1.5">
              {investigation.domain_filters.map((filter) => (
                <span
                  key={filter}
                  className="px-2 py-0.5 rounded text-[10px] font-mono bg-echelon-cyan/10 text-echelon-cyan border border-echelon-cyan/20"
                >
                  {filter}
                </span>
              ))}
            </div>
            <div className="text-[10px] text-terminal-text-muted/50 mt-3">
              Domain filters are immutable after commit. Evidence and counter-signals are validated against these filters at ingestion.
            </div>
          </div>
        </div>
      )}

      {/* Legal review warning */}
      {investigation.has_legal_review_requirement && (
        <div className="bg-status-warning/10 border border-status-warning/30 rounded-lg p-3 flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-status-warning shrink-0" />
          <span className="text-xs text-status-warning">
            This investigation contains evidence from sources requiring legal review.
          </span>
        </div>
      )}

      {/* Claim status distribution (if claims have statuses) */}
      {investigation.claims.status_summary && Object.keys(investigation.claims.status_summary).length > 0 && (
        <div className="bg-terminal-surface rounded-lg border border-terminal-border overflow-hidden">
          <div className="px-5 py-2.5 border-b border-terminal-border/50 bg-terminal-panel">
            <h3 className="text-[11px] font-bold uppercase tracking-wider text-terminal-text-muted">
              Claim Status Distribution
            </h3>
          </div>
          <div className="p-5">
            <ClaimStatusMiniBar summary={investigation.claims.status_summary} />
          </div>
        </div>
      )}

      {/* Timestamps — design ref: detail-section */}
      <div className="bg-terminal-surface rounded-lg border border-terminal-border overflow-hidden">
        <div className="px-5 py-2.5 border-b border-terminal-border/50 bg-terminal-panel">
          <h3 className="text-[11px] font-bold uppercase tracking-wider text-terminal-text-muted">
            Timestamps
          </h3>
        </div>
        <div className="p-5">
          <dl className="grid grid-cols-[100px_1fr] gap-x-4 gap-y-2 text-[13px]">
            <dt className="text-terminal-text-muted">Created</dt>
            <dd className="font-mono text-terminal-text text-xs">
              {new Date(investigation.created_at).toLocaleString()}
            </dd>
            <dt className="text-terminal-text-muted">Updated</dt>
            <dd className="font-mono text-terminal-text text-xs">
              {new Date(investigation.updated_at).toLocaleString()}
            </dd>
          </dl>
        </div>
      </div>
    </div>
  );
}

// ── Browse View ──────────────────────────────────────────────────────────

function BrowseView({
  investigations,
  isLoading,
  onSelect,
  onCreateNew,
}: {
  investigations: InvestigationSummary[];
  isLoading: boolean;
  onSelect: (id: string) => void;
  onCreateNew: () => void;
}) {
  const stalledCount = useMemo(
    () => investigations.filter((i) => i.status === 'stalled').length,
    [investigations],
  );
  const activeCount = useMemo(
    () => investigations.filter((i) => i.status === 'active').length,
    [investigations],
  );
  const totalEvidence = useMemo(
    () => investigations.reduce((s, i) => s + i.evidence_count, 0),
    [investigations],
  );
  const totalClaims = useMemo(
    () => investigations.reduce((s, i) => s + i.claim_count, 0),
    [investigations],
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-5 h-5 text-terminal-text-muted animate-spin" />
      </div>
    );
  }

  if (investigations.length === 0) {
    return (
      <EmptyState
        type="ZERO_STATE"
        icon={<Search className="w-7 h-7" />}
        title="No investigations yet"
        description="Investigations gather evidence, build claim graphs, and track counter-signals to inform market positions."
        actions={[
          {
            label: 'New Investigation',
            onClick: onCreateNew,
            variant: 'primary',
          },
        ]}
      />
    );
  }

  return (
    <>
      {/* Attention strip */}
      <AttentionStrip stalledCount={stalledCount} total={investigations.length} />

      {/* 4 KPI cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className={`bg-terminal-surface border rounded-lg p-3 flex flex-col gap-0.5 ${stalledCount > 0 ? 'border-status-warning/25' : 'border-terminal-border'}`}>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-terminal-text-muted leading-4">
            Active
          </span>
          <span className={`font-mono text-2xl font-bold tabular-nums leading-8 ${activeCount > 0 ? 'text-status-success' : 'text-terminal-text-muted'}`}>
            {activeCount}
          </span>
          {stalledCount > 0 && (
            <span className="text-[10px] font-mono text-status-warning">{stalledCount} stalled</span>
          )}
        </div>
        <div className="bg-terminal-surface border border-terminal-border rounded-lg p-3 flex flex-col gap-0.5">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-terminal-text-muted leading-4">
            Evidence Items
          </span>
          <span className="font-mono text-2xl font-bold tabular-nums leading-8 text-terminal-text">
            {totalEvidence}
          </span>
        </div>
        <div className="bg-terminal-surface border border-terminal-border rounded-lg p-3 flex flex-col gap-0.5">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-terminal-text-muted leading-4">
            Claims Tracked
          </span>
          <span className="font-mono text-2xl font-bold tabular-nums leading-8 text-terminal-text">
            {totalClaims}
          </span>
        </div>
        <div className={`bg-terminal-surface border rounded-lg p-3 flex flex-col gap-0.5 ${stalledCount > 0 ? 'border-status-warning/25 bg-status-warning/4' : 'border-terminal-border'}`}>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-terminal-text-muted leading-4">
            Stalled
          </span>
          <span className={`font-mono text-2xl font-bold tabular-nums leading-8 ${stalledCount > 0 ? 'text-status-warning' : 'text-status-success'}`}>
            {stalledCount}
          </span>
        </div>
      </div>

      {/* 1fr 300px grid: card list + right rail */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-5 items-start">
        <div className="space-y-3">
          {investigations.map((inv) => (
            <InvestigationCard
              key={inv.id}
              inv={inv}
              onClick={() => onSelect(inv.id)}
            />
          ))}
        </div>
        <div className="hidden lg:block">
          <RightRail investigations={investigations} selectedId={null} />
        </div>
      </div>
    </>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────

export function InvestigationPage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [view, setView] = useState<'browse' | 'detail'>('browse');

  const { investigations, isLoading: listLoading, error: listError } = useInvestigationList();
  const { investigation, isLoading: detailLoading } = useInvestigationDetail(selectedId);

  const handleTabKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      const tabIds = TABS.map((t) => t.id);
      const idx = tabIds.indexOf(activeTab);
      if (e.key === 'ArrowRight') {
        e.preventDefault();
        setActiveTab(tabIds[(idx + 1) % tabIds.length]);
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        setActiveTab(tabIds[(idx - 1 + tabIds.length) % tabIds.length]);
      }
    },
    [activeTab],
  );

  const openDetail = (id: string) => {
    setSelectedId(id);
    setView('detail');
    setActiveTab('overview');
  };

  const backToBrowse = () => {
    setView('browse');
    setSelectedId(null);
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-5">
      {/* Page header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 text-[13px] text-terminal-text-muted mb-0.5">
            <span>Echelon</span>
            <span className="text-terminal-border">/</span>
            <span className="text-terminal-text font-semibold">Investigations</span>
          </div>
          <h1 className="text-2xl font-bold text-terminal-text leading-8">Investigations</h1>
        </div>
        <button
          onClick={() => navigate('/investigation/create')}
          className="flex items-center gap-1.5 h-9 px-4 rounded-lg text-[13px] font-semibold bg-echelon-cyan text-terminal-bg transition-colors hover:opacity-90"
        >
          <Plus className="w-4 h-4" />
          New Investigation
        </button>
      </div>

      {/* Error state */}
      {listError && (
        <div className="p-4 bg-status-failure/10 border border-status-failure/30 rounded-lg text-xs text-status-failure">
          Failed to load investigations: {listError.message}
        </div>
      )}

      {/* Browse vs Detail view */}
      {view === 'browse' ? (
        <BrowseView
          investigations={investigations}
          isLoading={listLoading}
          onSelect={openDetail}
          onCreateNew={() => navigate('/investigation/create')}
        />
      ) : (
        <>
          {/* Back to browse */}
          <button
            onClick={backToBrowse}
            className="flex items-center gap-1.5 text-[13px] font-medium text-terminal-text-secondary hover:text-terminal-text transition-colors"
          >
            <ArrowRight className="w-4 h-4 rotate-180" />
            Back to Investigations
          </button>

          {/* Detail layout: 280px sidebar + tabbed content */}
          <div
            className="grid grid-cols-1 md:grid-cols-[280px_1fr] border border-terminal-border rounded-lg overflow-hidden bg-terminal-surface"
            style={{ minHeight: 480 }}
          >
            {/* Left sidebar */}
            <div className="border-r border-terminal-border bg-terminal-surface overflow-y-auto">
              <InvestigationListPanel
                investigations={investigations}
                selectedId={selectedId}
                onSelect={openDetail}
                onCreateNew={() => navigate('/investigation/create')}
                isLoading={listLoading}
              />
            </div>

            {/* Right content — tabbed detail */}
            <div className="bg-terminal-surface min-w-0">
              {!selectedId ? (
                <div className="flex flex-col items-center justify-center h-full text-center px-6">
                  <Search className="w-7 h-7 text-terminal-text-muted/40 mb-3" />
                  <div className="text-[13px] text-terminal-text-muted font-medium">
                    Select an investigation to view details
                  </div>
                </div>
              ) : detailLoading ? (
                <div className="flex items-center justify-center h-full">
                  <Loader2 className="w-5 h-5 text-terminal-text-muted animate-spin" />
                </div>
              ) : !investigation ? (
                <div className="flex items-center justify-center h-full text-terminal-text-muted text-xs">
                  Investigation not found
                </div>
              ) : (
                <div>
                  {/* Tab bar — sunken bg, underline active indicator */}
                  <div
                    className="flex items-center gap-0 border-b border-terminal-border px-4 bg-terminal-panel overflow-x-auto"
                    role="tablist"
                    onKeyDown={handleTabKeyDown}
                  >
                    {TABS.map((tab) => {
                      const Icon = tab.icon;
                      const isActive = activeTab === tab.id;
                      return (
                        <button
                          key={tab.id}
                          role="tab"
                          aria-selected={isActive}
                          tabIndex={isActive ? 0 : -1}
                          onClick={() => setActiveTab(tab.id)}
                          className={`flex items-center gap-1.5 px-4 py-3 text-[13px] font-medium border-b-2 -mb-px transition-colors whitespace-nowrap ${
                            isActive
                              ? 'border-echelon-cyan text-echelon-cyan font-semibold'
                              : 'border-transparent text-terminal-text-muted hover:text-terminal-text'
                          }`}
                        >
                          <Icon className="w-3.5 h-3.5" />
                          {tab.label}
                          {tab.isNew && (
                            <span className="px-1 py-0.5 rounded text-[8px] font-bold uppercase bg-purple-500/10 text-purple-500 border border-purple-500/20 leading-none">
                              new
                            </span>
                          )}
                        </button>
                      );
                    })}
                  </div>

                  {/* Tab content */}
                  {activeTab === 'overview' && <OverviewTab investigation={investigation} />}
                  {activeTab === 'evidence' && (
                    <div className="p-5">
                      <EvidenceEnvelopePanel evidence={investigation.evidence} />
                    </div>
                  )}
                  {activeTab === 'claims' && (
                    <div className="p-5">
                      <ClaimGraphPanel claims={investigation.claims} />
                    </div>
                  )}
                  {activeTab === 'counter-signals' && (
                    <div className="p-5">
                      <CounterSignalPanel
                        signals={investigation.counter_signals.signals}
                        summary={investigation.counter_signals.summary}
                      />
                    </div>
                  )}
                  {activeTab === 'drift' && (
                    <div className="p-5">
                      <DriftEventsPanel
                        events={investigation.drift.events}
                        hasMaterialDrift={investigation.drift.has_material_drift}
                        investigationId={investigation.id}
                      />
                    </div>
                  )}
                  {activeTab === 'readiness' && (
                    <div className="p-5">
                      <ReadinessCertificatePanel investigationId={investigation.id} />
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default InvestigationPage;
