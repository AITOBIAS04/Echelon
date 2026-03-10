import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  FileText,
  Filter,
  GitBranch,
  Loader2,
  Plus,
  Search,
  ShieldCheck,
  TrendingDown,
  Sparkles,
} from 'lucide-react';
import { clsx } from 'clsx';
import { useInvestigationDetail, useInvestigationList } from '../hooks/useInvestigation';
import { EmptyState } from '../components/empty-states/EmptyState';
import { EvidenceEnvelopePanel } from '../components/investigation/EvidenceEnvelopePanel';
import { ClaimGraphPanel } from '../components/investigation/ClaimGraphPanel';
import { CounterSignalPanel } from '../components/investigation/CounterSignalPanel';
import { DriftEventsPanel } from '../components/investigation/DriftEventsPanel';
import { ReadinessCertificatePanel } from '../components/investigation/ReadinessCertificatePanel';
import type { InvestigationDetail, InvestigationSummary } from '../types/investigation';

type Tab = 'overview' | 'evidence' | 'claims' | 'counter-signals' | 'drift' | 'readiness';

const TABS: Array<{ id: Tab; label: string; icon: typeof Search; isNew?: boolean }> = [
  { id: 'overview', label: 'Overview', icon: Search },
  { id: 'evidence', label: 'Evidence', icon: FileText },
  { id: 'claims', label: 'Claims', icon: GitBranch },
  { id: 'counter-signals', label: 'Counter-Signals', icon: AlertTriangle },
  { id: 'drift', label: 'Drift', icon: TrendingDown },
  { id: 'readiness', label: 'Readiness', icon: ShieldCheck, isNew: true },
];

const STOP_LABELS: Record<string, string> = {
  OUTCOME_RESOLUTION: 'Market resolution',
  EVIDENCE_THRESHOLD: 'Evidence threshold',
  SPONSOR_DEFINED: 'Sponsor milestone',
};

function statusTone(status: string): { dot: string; text: string; bg: string } {
  switch (status) {
    case 'active':
      return {
        dot: 'bg-[var(--e-green-600)]',
        text: 'text-[var(--e-green-600)]',
        bg: 'bg-[var(--e-green-50)]',
      };
    case 'stalled':
      return {
        dot: 'bg-[var(--e-orange-600)]',
        text: 'text-[var(--e-orange-600)]',
        bg: 'bg-[color:oklch(0.708_0.136_62_/_0.10)]',
      };
    case 'completed':
      return {
        dot: 'bg-[var(--e-text-disabled)]',
        text: 'text-[var(--e-text-muted)]',
        bg: 'bg-[var(--e-bg-sunken)]',
      };
    default:
      return {
        dot: 'bg-[var(--e-text-disabled)]',
        text: 'text-[var(--e-text-muted)]',
        bg: 'bg-[var(--e-bg-sunken)]',
      };
  }
}

function StatusBadge({ status }: { status: string }) {
  const tone = statusTone(status);
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em]',
        tone.bg,
        tone.text,
      )}
    >
      <span className={clsx('h-2 w-2 rounded-full', tone.dot)} />
      {status}
    </span>
  );
}

function KpiCard({
  label,
  value,
  detail,
  tone,
}: {
  label: string;
  value: number;
  detail?: string;
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
      {detail ? <div className="mt-1 text-[11px] text-[var(--e-text-muted)]">{detail}</div> : null}
    </div>
  );
}

function AttentionStrip({ stalledCount, total }: { stalledCount: number; total: number }) {
  if (total === 0) return null;

  const alert = stalledCount > 0;

  return (
    <div
      className={clsx(
        'flex items-center gap-3 rounded-lg px-5 py-3 text-[13px] leading-5',
        alert
          ? 'border border-[color:oklch(0.708_0.136_62_/_0.20)] bg-[color:oklch(0.708_0.136_62_/_0.10)]'
          : 'border border-[color:oklch(0.545_0.170_152_/_0.18)] bg-[color:oklch(0.545_0.170_152_/_0.08)]',
      )}
    >
      {alert ? (
        <AlertTriangle className="h-4 w-4 shrink-0 text-[var(--e-orange-600)]" />
      ) : (
        <CheckCircle2 className="h-4 w-4 shrink-0 text-[var(--e-green-600)]" />
      )}
      <span className={clsx('font-semibold', alert ? 'text-[var(--e-orange-600)]' : 'text-[var(--e-green-600)]')}>
        {alert ? 'Stalled' : 'All Active'}
      </span>
      <span className="text-[var(--e-text-secondary)]">
        {alert
          ? `${stalledCount} investigation${stalledCount === 1 ? '' : 's'} stalled`
          : `All ${total} investigation${total === 1 ? '' : 's'} progressing`}
      </span>
    </div>
  );
}

function InvestigationCard({
  investigation,
  onClick,
}: {
  investigation: InvestigationSummary;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={clsx(
        'group w-full rounded-xl border bg-[var(--e-bg-card)] px-5 py-5 text-left shadow-[var(--e-shadow-xs)] transition hover:-translate-y-0.5 hover:border-[var(--e-purple-200)] hover:shadow-[var(--e-shadow-md)]',
        investigation.status === 'stalled'
          ? 'border-[color:oklch(0.708_0.136_62_/_0.20)]'
          : 'border-[var(--e-border-primary)]',
      )}
    >
      <div className="mb-3 flex items-center gap-2">
        <span className="font-mono text-[11px] font-semibold text-[var(--e-text-muted)]">
          {investigation.id.slice(0, 12)}
        </span>
        <StatusBadge status={investigation.status} />
        <span className="ml-auto inline-flex items-center gap-1 text-[12px] font-semibold text-[var(--e-purple-700)] opacity-0 transition group-hover:opacity-100">
          Open
          <ArrowRight className="h-3.5 w-3.5" />
        </span>
      </div>

      <div className="mb-2 text-[15px] font-semibold leading-6 text-[var(--e-text-primary)]">
        {investigation.construct_id || investigation.inquiry_class || investigation.id}
      </div>

      <div className="mb-4 flex flex-wrap items-center gap-2 text-[12px] text-[var(--e-text-muted)]">
        {investigation.theatre_id ? (
          <span className="rounded-full border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-2 py-0.5 font-mono text-[11px]">
            {investigation.theatre_id.slice(0, 12)}
          </span>
        ) : null}
        {investigation.template_name ? (
          <span className="rounded-full border border-[var(--e-purple-200)] bg-[var(--e-purple-50)] px-2 py-0.5 text-[11px] font-semibold text-[var(--e-purple-700)]">
            {investigation.template_name}
          </span>
        ) : null}
        <span>{new Date(investigation.created_at).toLocaleDateString()}</span>
      </div>

      <div className="flex flex-wrap items-center gap-3 text-[12px] text-[var(--e-text-secondary)]">
        <span>{investigation.evidence_count} evidence</span>
        <span>{investigation.claim_count} claims</span>
        <span>{investigation.counter_signal_count} counter-signals</span>
        <span>{investigation.drift_event_count} drift</span>
      </div>
    </button>
  );
}

function RightRail({
  selected,
}: {
  selected: InvestigationSummary | null;
}) {
  return (
    <div className="space-y-4">
      <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
        <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
          <h3 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
            Domain Filters
          </h3>
        </div>
        <div className="px-4 py-4 text-[12px] leading-5 text-[var(--e-text-secondary)]">
          {selected ? (
            <>
              Domain filters are enforced at ingestion.
              <div className="mt-2 text-[11px] text-[var(--e-text-muted)]">
                Open the investigation detail to inspect committed filters.
              </div>
            </>
          ) : (
            'Select an investigation to inspect committed domain filters.'
          )}
        </div>
      </section>

      <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
        <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
          <h3 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
            Evidence Feed
          </h3>
        </div>
        <div className="space-y-2 px-4 py-4 text-[12px] text-[var(--e-text-secondary)]">
          {selected ? (
            <>
              <div className="flex items-center justify-between">
                <span>Evidence Items</span>
                <span className="font-mono text-[var(--e-text-primary)]">{selected.evidence_count}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Claims</span>
                <span className="font-mono text-[var(--e-text-primary)]">{selected.claim_count}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Drift Events</span>
                <span className="font-mono text-[var(--e-text-primary)]">{selected.drift_event_count}</span>
              </div>
              <div className="pt-1 text-[11px] text-[var(--e-text-muted)]">
                Open the detail view for the full evidence timeline.
              </div>
            </>
          ) : (
            <div className="text-[var(--e-text-muted)]">Select an investigation to inspect activity.</div>
          )}
        </div>
      </section>

      <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
        <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
          <h3 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
            Provenance Breakdown
          </h3>
        </div>
        <div className="px-4 py-4 text-[12px] leading-5 text-[var(--e-text-muted)]">
          Provenance counts require evidence-manifest data and are shown in detail panels, not on the browse list.
        </div>
      </section>
    </div>
  );
}

function ArrivalContextBanner({
  investigationId,
  searchParams,
}: {
  investigationId: string;
  searchParams: URLSearchParams;
}) {
  const created = searchParams.get('created') === '1';
  const sourceSurface = searchParams.get('source_surface');
  const signalTitle = searchParams.get('signal_title');
  const signalClass = searchParams.get('signal_class');
  const signalRegion = searchParams.get('signal_region');
  const theatreId = searchParams.get('theatre_id');
  const constructId = searchParams.get('construct_id');
  const sourceInvestigation = searchParams.get('source_investigation');

  if (!created && !sourceSurface && !signalTitle && !theatreId && !sourceInvestigation) {
    return null;
  }

  return (
    <div className="mx-5 mt-5 rounded-lg border border-[var(--e-purple-200)] bg-[var(--e-purple-50)] px-4 py-4">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 flex h-9 w-9 items-center justify-center rounded-full border border-[var(--e-purple-200)] bg-white text-[var(--e-purple-700)]">
          <Sparkles className="h-4 w-4" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-purple-700)]">
            Journey context
          </div>
          <div className="mt-1 text-[13px] leading-6 text-[var(--e-text-secondary)]">
            {created ? (
              <div>
                Investigation <span className="font-mono text-[var(--e-text-primary)]">{investigationId}</span> created successfully.
              </div>
            ) : null}
            {sourceSurface ? (
              <div>
                Launched from <span className="font-medium text-[var(--e-text-primary)]">{sourceSurface.replaceAll('_', ' ')}</span>.
              </div>
            ) : null}
            {signalTitle ? (
              <div>
                Signal context: <span className="font-medium text-[var(--e-text-primary)]">{signalTitle}</span>
                {signalClass ? ` · ${signalClass}` : ''}
                {signalRegion ? ` · ${signalRegion}` : ''}
              </div>
            ) : null}
            {theatreId || constructId ? (
              <div>
                Theatre context: <span className="font-mono text-[var(--e-text-primary)]">{constructId ?? theatreId}</span>
              </div>
            ) : null}
            {sourceInvestigation ? (
              <div>
                Derived from investigation <span className="font-mono text-[var(--e-text-primary)]">{sourceInvestigation}</span>.
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}

function SidebarItem({
  investigation,
  selected,
  onSelect,
}: {
  investigation: InvestigationSummary;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={clsx(
        'w-full border-b border-[var(--e-border-secondary)] px-4 py-3 text-left transition',
        selected
          ? 'border-l-[3px] border-l-[var(--e-purple-500)] bg-[var(--e-purple-50)]'
          : 'border-l-[3px] border-l-transparent hover:bg-[var(--e-bg-hover)]',
      )}
    >
      <div className="mb-1 flex items-center gap-2">
        <span className="font-mono text-[11px] font-semibold text-[var(--e-text-muted)]">
          {investigation.id.slice(0, 12)}
        </span>
        <StatusBadge status={investigation.status} />
      </div>
      <div className="mb-1 text-[13px] font-semibold leading-5 text-[var(--e-text-primary)]">
        {investigation.construct_id || investigation.inquiry_class || investigation.id}
      </div>
      {investigation.template_name ? (
        <div className="mb-1 text-[11px] text-[var(--e-purple-700)]">
          {investigation.template_name}
        </div>
      ) : null}
      <div className="text-[11px] text-[var(--e-text-muted)]">
        {investigation.evidence_count} evidence · {investigation.claim_count} claims
      </div>
    </button>
  );
}

function OverviewTab({ investigation }: { investigation: InvestigationDetail }) {
  return (
    <div className="space-y-5 p-5">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { label: 'Evidence', value: investigation.evidence.items.length },
          { label: 'Claims', value: investigation.claims.claims.length },
          { label: 'Counter-Signals', value: investigation.counter_signals.signals.length },
          { label: 'Drift Events', value: investigation.drift.events.length },
        ].map((card) => (
          <KpiCard key={card.label} label={card.label} value={card.value} />
        ))}
      </div>

      <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
        <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-3">
          <h3 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
            Identity
          </h3>
        </div>
        <div className="grid grid-cols-[140px_1fr] gap-x-4 gap-y-2 px-5 py-5 text-[13px]">
          <div className="text-[var(--e-text-muted)]">Investigation ID</div>
          <div className="font-mono text-[var(--e-text-primary)]">{investigation.id}</div>
          <div className="text-[var(--e-text-muted)]">Theatre</div>
          <div className="font-mono text-[var(--e-text-primary)]">{investigation.theatre_id || '—'}</div>
          <div className="text-[var(--e-text-muted)]">Construct</div>
          <div className="font-mono text-[var(--e-text-primary)]">{investigation.construct_id || '—'}</div>
          <div className="text-[var(--e-text-muted)]">Inquiry Class</div>
          <div className="font-mono text-[var(--e-text-primary)]">{investigation.inquiry_class}</div>
          <div className="text-[var(--e-text-muted)]">Template</div>
          <div className="text-[var(--e-text-primary)]">
            {investigation.template_name ? (
              <div className="flex flex-wrap items-center gap-2">
                <span>{investigation.template_name}</span>
                {investigation.template_id ? (
                  <span className="font-mono text-[11px] text-[var(--e-text-muted)]">
                    {investigation.template_id}
                  </span>
                ) : null}
              </div>
            ) : (
              'Blank / manual'
            )}
          </div>
          <div className="text-[var(--e-text-muted)]">Status</div>
          <div><StatusBadge status={investigation.status} /></div>
          <div className="text-[var(--e-text-muted)]">Stop Condition</div>
          <div className="font-mono text-[var(--e-text-primary)]">
            {STOP_LABELS[investigation.stop_condition] ?? investigation.stop_condition}
          </div>
        </div>
      </section>

      {investigation.domain_filters && investigation.domain_filters.length > 0 ? (
        <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
          <div className="flex items-center gap-2 border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-3">
            <Filter className="h-4 w-4 text-[var(--e-purple-500)]" />
            <h3 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              Domain Filters
            </h3>
          </div>
          <div className="px-5 py-5">
            <div className="flex flex-wrap gap-2">
              {investigation.domain_filters.map((filter) => (
                <span
                  key={filter}
                  className="rounded-full border border-[var(--e-purple-200)] bg-[var(--e-purple-50)] px-2.5 py-1 font-mono text-[11px] text-[var(--e-purple-700)]"
                >
                  {filter}
                </span>
              ))}
            </div>
            <div className="mt-3 text-[12px] leading-5 text-[var(--e-text-muted)]">
              Domain filters are committed at creation and enforced at evidence and counter-signal ingestion.
            </div>
          </div>
        </section>
      ) : null}

      {(investigation.committed_sources?.length ?? 0) > 0 ? (
        <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
          <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-3">
            <h3 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              Committed Sources
            </h3>
          </div>
          <div className="space-y-3 px-5 py-5">
            <div className="text-[12px] leading-5 text-[var(--e-text-secondary)]">
              These source IDs were snapshotted at creation time. They are the immutable audit anchor for the investigation template provenance.
            </div>
            <div className="flex flex-wrap gap-2">
              {investigation.committed_sources?.map((sourceId) => (
                <span
                  key={sourceId}
                  className="rounded-full border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-2.5 py-1 font-mono text-[11px] text-[var(--e-text-secondary)]"
                >
                  {sourceId}
                </span>
              ))}
            </div>
          </div>
        </section>
      ) : null}

      {investigation.has_legal_review_requirement ? (
        <div className="rounded-lg border border-[color:oklch(0.708_0.136_62_/_0.20)] bg-[color:oklch(0.708_0.136_62_/_0.10)] px-4 py-3 text-[13px] text-[var(--e-orange-600)]">
          This investigation includes sources requiring legal review.
        </div>
      ) : null}

      <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
        <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-3">
          <h3 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
            Timestamps
          </h3>
        </div>
        <div className="grid grid-cols-[100px_1fr] gap-x-4 gap-y-2 px-5 py-5 text-[13px]">
          <div className="text-[var(--e-text-muted)]">Created</div>
          <div className="font-mono text-[var(--e-text-primary)]">
            {new Date(investigation.created_at).toLocaleString()}
          </div>
          <div className="text-[var(--e-text-muted)]">Updated</div>
          <div className="font-mono text-[var(--e-text-primary)]">
            {new Date(investigation.updated_at).toLocaleString()}
          </div>
        </div>
      </section>
    </div>
  );
}

function BrowseView({
  investigations,
  loading,
  onOpen,
  onCreate,
}: {
  investigations: InvestigationSummary[];
  loading: boolean;
  onOpen: (id: string) => void;
  onCreate: () => void;
}) {
  const stalledCount = investigations.filter((item) => item.status === 'stalled').length;
  const activeCount = investigations.filter((item) => item.status === 'active').length;
  const totalEvidence = investigations.reduce((sum, item) => sum + item.evidence_count, 0);
  const totalClaims = investigations.reduce((sum, item) => sum + item.claim_count, 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-6 py-16 shadow-[var(--e-shadow-xs)]">
        <Loader2 className="mr-2 h-5 w-5 animate-spin text-[var(--e-text-muted)]" />
        <span className="text-[14px] text-[var(--e-text-muted)]">Loading investigations…</span>
      </div>
    );
  }

  if (investigations.length === 0) {
    return (
      <EmptyState
        type="ZERO_STATE"
        icon={<Search className="h-7 w-7" />}
        title="No investigations yet"
        description="Investigations gather evidence, build claim graphs, and track counter-signals for certificate readiness."
        actions={[
          {
            label: 'New Investigation',
            onClick: onCreate,
            variant: 'primary',
          },
        ]}
      />
    );
  }

  return (
    <div className="space-y-5">
      <AttentionStrip stalledCount={stalledCount} total={investigations.length} />

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <KpiCard label="Active" value={activeCount} detail={stalledCount > 0 ? `${stalledCount} stalled` : undefined} tone={stalledCount > 0 ? 'warning' : 'success'} />
        <KpiCard label="Evidence Items" value={totalEvidence} />
        <KpiCard label="Claims Tracked" value={totalClaims} />
        <KpiCard label="Stalled" value={stalledCount} tone={stalledCount > 0 ? 'warning' : 'success'} />
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_300px]">
        <div className="space-y-3">
          {investigations.map((investigation) => (
            <InvestigationCard
              key={investigation.id}
              investigation={investigation}
              onClick={() => onOpen(investigation.id)}
            />
          ))}
        </div>
        <div className="hidden lg:block">
          <RightRail selected={null} />
        </div>
      </div>
    </div>
  );
}

export function InvestigationPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [view, setView] = useState<'browse' | 'detail'>('browse');
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { investigations, isLoading: listLoading, error: listError } = useInvestigationList();
  const { investigation, isLoading: detailLoading } = useInvestigationDetail(selectedId);
  const requestedInvestigationId = searchParams.get('investigation');
  const hasArrivalContext = useMemo(
    () =>
      ['created', 'source_surface', 'signal_title', 'signal_class', 'signal_region', 'theatre_id', 'construct_id', 'source_investigation']
        .some((key) => searchParams.has(key)),
    [searchParams],
  );

  const handleTabKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      const tabIds = TABS.map((tab) => tab.id);
      const currentIndex = tabIds.indexOf(activeTab);
      if (event.key === 'ArrowRight') {
        event.preventDefault();
        setActiveTab(tabIds[(currentIndex + 1) % tabIds.length]);
      } else if (event.key === 'ArrowLeft') {
        event.preventDefault();
        setActiveTab(tabIds[(currentIndex - 1 + tabIds.length) % tabIds.length]);
      }
    },
    [activeTab],
  );

  const openDetail = (id: string) => {
    setSelectedId(id);
    setView('detail');
    setActiveTab('overview');
  };

  useEffect(() => {
    if (!requestedInvestigationId) {
      return;
    }

    const exists = investigations.some((item) => item.id === requestedInvestigationId);
    if (!exists) {
      return;
    }

    setSelectedId(requestedInvestigationId);
    setView('detail');
    setActiveTab('overview');
  }, [investigations, requestedInvestigationId]);

  return (
    <div className="p-6">
      <div className="mx-auto max-w-7xl space-y-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              Investigation Workspace
            </div>
            <h1 className="text-[34px] font-bold tracking-[-0.03em] text-[var(--e-text-primary)]">
              Investigations
            </h1>
          </div>

          <button
            type="button"
            onClick={() => navigate('/investigation/create')}
            className="inline-flex h-10 items-center gap-2 rounded-lg bg-[var(--e-purple-500)] px-4 text-[13px] font-semibold text-[var(--e-text-inverse)] transition hover:bg-[var(--e-purple-600)]"
          >
            <Plus className="h-4 w-4" />
            New Investigation
          </button>
        </div>

        {listError ? (
          <div className="rounded-lg border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] px-5 py-4 text-[13px] text-[var(--e-red-600)] shadow-[var(--e-shadow-xs)]">
            Failed to load investigations: {listError.message}
          </div>
        ) : null}

        {view === 'browse' ? (
          <BrowseView
            investigations={investigations}
            loading={listLoading}
            onOpen={openDetail}
            onCreate={() => navigate('/investigation/create')}
          />
        ) : (
          <div className="space-y-4">
            <button
              type="button"
              onClick={() => {
                setView('browse');
                setSelectedId(null);
                const nextParams = new URLSearchParams(searchParams);
                ['investigation', 'created', 'source_surface', 'signal_id', 'signal_title', 'signal_class', 'signal_region', 'signal_category', 'signal_source', 'source_investigation', 'theatre_id', 'construct_id']
                  .forEach((key) => nextParams.delete(key));
                setSearchParams(nextParams, { replace: true });
              }}
              className="inline-flex items-center gap-2 text-[12px] font-medium text-[var(--e-text-muted)] transition hover:text-[var(--e-text-primary)]"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Investigations
            </button>

            <div className="grid min-h-[560px] grid-cols-1 overflow-hidden rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-sm)] md:grid-cols-[280px_1fr]">
              <aside className="border-r border-[var(--e-border-secondary)] bg-[var(--e-bg-card)]">
                {listLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-5 w-5 animate-spin text-[var(--e-text-muted)]" />
                  </div>
                ) : investigations.length === 0 ? (
                  <div className="p-4">
                    <EmptyState
                      type="ZERO_STATE"
                      icon={<Search className="h-6 w-6" />}
                      title="No investigations"
                      description="Create an investigation to begin."
                      actions={[
                        {
                          label: 'New Investigation',
                          onClick: () => navigate('/investigation/create'),
                          variant: 'primary',
                        },
                      ]}
                    />
                  </div>
                ) : (
                  investigations.map((item) => (
                    <SidebarItem
                      key={item.id}
                      investigation={item}
                      selected={item.id === selectedId}
                      onSelect={() => openDetail(item.id)}
                    />
                  ))
                )}
              </aside>

              <main className="min-w-0 bg-[var(--e-bg-card)]">
                {!selectedId ? (
                  <div className="flex h-full items-center justify-center px-6 py-16 text-[14px] text-[var(--e-text-muted)]">
                    Select an investigation to inspect evidence, claims, drift, and readiness.
                  </div>
                ) : detailLoading || !investigation ? (
                  <div className="flex h-full items-center justify-center px-6 py-16 text-[14px] text-[var(--e-text-muted)]">
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Loading investigation…
                  </div>
                ) : (
                  <>
                    {hasArrivalContext ? (
                      <ArrivalContextBanner investigationId={investigation.id} searchParams={searchParams} />
                    ) : null}
                    <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5">
                      <div
                        role="tablist"
                        aria-label="Investigation detail tabs"
                        onKeyDown={handleTabKeyDown}
                        className="flex flex-wrap gap-1"
                      >
                        {TABS.map((tab) => {
                          const Icon = tab.icon;
                          const active = activeTab === tab.id;
                          return (
                            <button
                              key={tab.id}
                              type="button"
                              role="tab"
                              aria-selected={active}
                              onClick={() => setActiveTab(tab.id)}
                              className={clsx(
                                'relative inline-flex items-center gap-2 px-4 py-3 text-[13px] font-medium transition',
                                active
                                  ? 'text-[var(--e-text-primary)]'
                                  : 'text-[var(--e-text-muted)] hover:text-[var(--e-text-primary)]',
                              )}
                            >
                              <Icon className="h-4 w-4" />
                              {tab.label}
                              {tab.isNew ? (
                                <span className="rounded-full bg-[var(--e-purple-50)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-purple-700)]">
                                  New
                                </span>
                              ) : null}
                              {active ? (
                                <span className="absolute inset-x-2 bottom-0 h-0.5 rounded-full bg-[var(--e-purple-500)]" />
                              ) : null}
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    {activeTab === 'overview' ? <OverviewTab investigation={investigation} /> : null}
                    {activeTab === 'evidence' ? <div className="p-5"><EvidenceEnvelopePanel evidence={investigation.evidence} /></div> : null}
                    {activeTab === 'claims' ? <div className="p-5"><ClaimGraphPanel claims={investigation.claims} /></div> : null}
                    {activeTab === 'counter-signals' ? (
                      <div className="p-5">
                        <CounterSignalPanel
                          signals={investigation.counter_signals.signals}
                          summary={investigation.counter_signals.summary}
                        />
                      </div>
                    ) : null}
                    {activeTab === 'drift' ? (
                      <div className="p-5">
                        <DriftEventsPanel
                          events={investigation.drift.events}
                          hasMaterialDrift={investigation.drift.has_material_drift}
                          investigationId={investigation.id}
                        />
                      </div>
                    ) : null}
                    {activeTab === 'readiness' ? (
                      <div className="p-5">
                        <ReadinessCertificatePanel investigationId={investigation.id} />
                      </div>
                    ) : null}
                  </>
                )}
              </main>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default InvestigationPage;
