/**
 * Investigation Dashboard
 *
 * Tabbed layout: Overview | Evidence | Claims | Signals | Drift
 * Lists all investigations and shows detail for selected investigation.
 */

import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, FileText, GitBranch, AlertTriangle, TrendingDown, ShieldAlert } from 'lucide-react';
import {
  useInvestigationList,
  useInvestigationDetail,
} from '../hooks/useInvestigation';
import { EvidenceEnvelopePanel } from '../components/investigation/EvidenceEnvelopePanel';
import { ClaimGraphPanel } from '../components/investigation/ClaimGraphPanel';
import { CounterSignalPanel } from '../components/investigation/CounterSignalPanel';
import { DriftEventsPanel } from '../components/investigation/DriftEventsPanel';
import { EmptyState } from '../components/empty-states/EmptyState';
import type { InvestigationSummary } from '../types/investigation';

type Tab = 'overview' | 'evidence' | 'claims' | 'signals' | 'drift';

const TABS: { id: Tab; label: string; icon: typeof Search }[] = [
  { id: 'overview', label: 'Overview', icon: Search },
  { id: 'evidence', label: 'Evidence', icon: FileText },
  { id: 'claims', label: 'Claims', icon: GitBranch },
  { id: 'signals', label: 'Signals', icon: AlertTriangle },
  { id: 'drift', label: 'Drift', icon: TrendingDown },
];

function StatusBadge({ status }: { status: string }) {
  const color = status === 'active'
    ? 'bg-emerald-500/20 text-emerald-400'
    : 'bg-zinc-500/20 text-zinc-400';
  return (
    <span className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase ${color}`}>
      {status}
    </span>
  );
}

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
      <div className="p-4 text-terminal-text-muted text-xs">
        Loading investigations...
      </div>
    );
  }

  if (investigations.length === 0) {
    return (
      <EmptyState
        type="ZERO_STATE"
        icon={<Search className="w-7 h-7" />}
        title="No investigations yet"
        description="Investigations let you track evidence, claims, and counter-signals across theatres."
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
    <div className="space-y-1">
      {investigations.map((inv) => (
        <button
          key={inv.id}
          onClick={() => onSelect(inv.id)}
          className={`w-full text-left px-3 py-2 rounded text-xs transition-colors ${
            selectedId === inv.id
              ? 'bg-echelon-cyan/10 border border-echelon-cyan/30'
              : 'hover:bg-terminal-surface border border-transparent'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="font-mono text-terminal-text truncate">
              {inv.id}
            </span>
            <StatusBadge status={inv.status} />
          </div>
          <div className="mt-1 flex gap-3 text-terminal-text-muted">
            <span>{inv.evidence_count} evidence</span>
            <span>{inv.claim_count} claims</span>
            <span>{inv.counter_signal_count} signals</span>
          </div>
        </button>
      ))}
    </div>
  );
}

function OverviewTab({ investigation }: { investigation: NonNullable<ReturnType<typeof useInvestigationDetail>['investigation']> }) {
  return (
    <div className="space-y-4">
      {/* Identity */}
      <div className="bg-terminal-surface rounded-lg p-4 border border-terminal-border">
        <h3 className="text-xs font-semibold text-terminal-text uppercase tracking-wider mb-3">
          Identity
        </h3>
        <dl className="grid grid-cols-2 gap-2 text-xs">
          <dt className="text-terminal-text-muted">Investigation ID</dt>
          <dd className="font-mono text-terminal-text">{investigation.id}</dd>
          <dt className="text-terminal-text-muted">Theatre</dt>
          <dd className="font-mono text-terminal-text">{investigation.theatre_id || '—'}</dd>
          <dt className="text-terminal-text-muted">Construct</dt>
          <dd className="font-mono text-terminal-text">{investigation.construct_id || '—'}</dd>
          <dt className="text-terminal-text-muted">Inquiry Class</dt>
          <dd className="font-mono text-terminal-text">{investigation.inquiry_class}</dd>
          <dt className="text-terminal-text-muted">Status</dt>
          <dd><StatusBadge status={investigation.status} /></dd>
          <dt className="text-terminal-text-muted">Stop Condition</dt>
          <dd className="font-mono text-terminal-text">{investigation.stop_condition}</dd>
        </dl>
      </div>

      {/* Legal review warning */}
      {investigation.has_legal_review_requirement && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
          <span className="text-xs text-amber-400">
            This investigation contains evidence from sources requiring legal review.
          </span>
        </div>
      )}

      {/* Counts */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { label: 'Evidence', value: investigation.evidence.items.length },
          { label: 'Claims', value: investigation.claims.claims.length },
          { label: 'Counter-Signals', value: investigation.counter_signals.signals.length },
          { label: 'Drift Events', value: investigation.drift.events.length },
        ].map((stat) => (
          <div
            key={stat.label}
            className="bg-terminal-surface rounded-lg p-3 border border-terminal-border text-center"
          >
            <div className="text-lg font-mono text-echelon-cyan">{stat.value}</div>
            <div className="text-[10px] text-terminal-text-muted uppercase">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Timestamps */}
      <div className="bg-terminal-surface rounded-lg p-4 border border-terminal-border">
        <h3 className="text-xs font-semibold text-terminal-text uppercase tracking-wider mb-3">
          Timestamps
        </h3>
        <dl className="grid grid-cols-2 gap-2 text-xs">
          <dt className="text-terminal-text-muted">Created</dt>
          <dd className="font-mono text-terminal-text">
            {new Date(investigation.created_at).toLocaleString()}
          </dd>
          <dt className="text-terminal-text-muted">Updated</dt>
          <dd className="font-mono text-terminal-text">
            {new Date(investigation.updated_at).toLocaleString()}
          </dd>
        </dl>
      </div>
    </div>
  );
}

export function InvestigationPage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const { investigations, isLoading: listLoading, error: listError } = useInvestigationList();
  const { investigation, isLoading: detailLoading } = useInvestigationDetail(selectedId);

  // Keyboard navigation for tabs (Arrow Left/Right)
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

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Search className="w-4 h-4 text-echelon-cyan" aria-hidden="true" />
        <h2 className="text-sm font-semibold text-terminal-text uppercase tracking-wider">
          Investigations
        </h2>
      </div>

      {listError && (
        <div className="bg-red-500/10 border border-red-500/30 rounded p-3 text-xs text-red-400">
          Failed to load investigations: {listError.message}
        </div>
      )}

      <div className="flex flex-col md:flex-row gap-4">
        {/* Left sidebar — investigation list */}
        <div className="w-full md:w-64 shrink-0">
          <InvestigationListPanel
            investigations={investigations}
            selectedId={selectedId}
            onSelect={setSelectedId}
            onCreateNew={() => navigate('/investigation/create')}
            isLoading={listLoading}
          />
        </div>

        {/* Right content — tabbed detail */}
        <div className="flex-1 min-w-0">
          {!selectedId ? (
            <div className="flex items-center justify-center h-64 text-terminal-text-muted text-xs">
              Select an investigation to view details
            </div>
          ) : detailLoading ? (
            <div className="flex items-center justify-center h-64 text-terminal-text-muted text-xs">
              Loading investigation...
            </div>
          ) : !investigation ? (
            <div className="flex items-center justify-center h-64 text-terminal-text-muted text-xs">
              Investigation not found
            </div>
          ) : (
            <div className="space-y-4">
              {/* Tab bar — keyboard navigable */}
              <div
                className="flex gap-1 border-b border-terminal-border overflow-x-auto"
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
                      className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium transition-colors border-b-2 -mb-px whitespace-nowrap ${
                        isActive
                          ? 'border-echelon-cyan text-echelon-cyan'
                          : 'border-transparent text-terminal-text-muted hover:text-terminal-text'
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                      {tab.label}
                    </button>
                  );
                })}
              </div>

              {/* Tab content */}
              {activeTab === 'overview' && <OverviewTab investigation={investigation} />}
              {activeTab === 'evidence' && (
                <EvidenceEnvelopePanel evidence={investigation.evidence} />
              )}
              {activeTab === 'claims' && (
                <ClaimGraphPanel claims={investigation.claims} />
              )}
              {activeTab === 'signals' && (
                <CounterSignalPanel
                  signals={investigation.counter_signals.signals}
                  summary={investigation.counter_signals.summary}
                />
              )}
              {activeTab === 'drift' && (
                <DriftEventsPanel
                  events={investigation.drift.events}
                  hasMaterialDrift={investigation.drift.has_material_drift}
                />
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default InvestigationPage;
