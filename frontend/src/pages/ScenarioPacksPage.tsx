/**
 * ScenarioPacksPage -- Scenario Packs catalog.
 *
 * Aligned to: echelon_scenario_packs_catalog_v2.html
 *
 * PRODUCT DISTINCTION:
 *   - Theatre Templates = live market contracts (Create Theatre flow)
 *   - Scenario Packs = branching RL / telemetry environments (THIS PAGE)
 *
 * Backend: GET /api/v1/scenario-pack-templates
 * template_status: RUNNABLE | CATALOG_ONLY
 */

import { useState, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Boxes, Loader2, Search, X, Play, Eye, GitBranch } from 'lucide-react';
import { EmptyState } from '../components/empty-states/EmptyState';
import { useTemplateList } from '../hooks/useScenarioPacks';

/** Human-readable family labels */
const FAMILY_LABELS: Record<string, string> = {
  NAV_UNC: 'Navigation',
  SOC_NAV: 'Social',
  MAN_FORCE: 'Manual Force',
  MARL_C3: 'Multi-Agent',
  '3D_INERT': '3D Inertial',
  LONG_HZN: 'Long Horizon',
  PUZ_LOGIC: 'Puzzle',
  ADV_AIR: 'Adversarial',
  PREC_MAN: 'Precision',
};

const FAMILIES = Object.keys(FAMILY_LABELS);

export function ScenarioPacksPage() {
  const navigate = useNavigate();
  const [familyFilter, setFamilyFilter] = useState<string | undefined>();
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [search, setSearch] = useState('');

  const { templates, total, isLoading, error } = useTemplateList({
    family: familyFilter,
    status: statusFilter,
  });

  const filtered = search
    ? templates.filter(
        (t) =>
          t.name.toLowerCase().includes(search.toLowerCase()) ||
          (t.description ?? '').toLowerCase().includes(search.toLowerCase()),
      )
    : templates;

  const runnableCount = templates.filter((t) => t.template_status === 'RUNNABLE').length;
  const catalogCount = templates.filter((t) => t.template_status === 'CATALOG_ONLY').length;

  // Max branch depth across all templates (derived from fork_points_max)
  const maxBranchDepth = useMemo(
    () => (templates.length > 0 ? Math.max(...templates.map((t) => t.fork_points_max)) : 0),
    [templates],
  );

  return (
    <div className="p-6 max-w-[960px] mx-auto space-y-5">
      {/* Page header */}
      <div>
        <div className="text-[11px] font-mono text-terminal-text-muted mb-0.5 uppercase tracking-wider">
          Operations / Scenario Packs
        </div>
        <h1 className="text-2xl font-bold text-terminal-text">Scenario Packs</h1>
        <p className="text-[13px] text-terminal-text-secondary mt-0.5">
          Branching simulation environments for RLMF, agent training, and replay analysis
        </p>
      </div>

      {/* Stats bar */}
      <div className="flex gap-4 p-3 px-5 bg-terminal-surface rounded-lg border border-terminal-border flex-wrap">
        {[
          { label: 'Scenario\nPacks', value: isLoading ? '...' : String(total) },
          { label: 'Runnable', value: isLoading ? '...' : String(runnableCount), color: 'text-status-success' },
          { label: 'Catalog\nOnly', value: isLoading ? '...' : String(catalogCount) },
          { label: 'Max Branch\nDepth', value: isLoading ? '...' : String(maxBranchDepth) },
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

      {/* Filter bar */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex gap-0.5 bg-terminal-panel rounded-lg p-[3px] border border-terminal-border/50">
          {[
            { label: 'All', value: undefined, count: total },
            { label: 'Runnable', value: 'RUNNABLE', count: runnableCount },
            { label: 'Catalog Only', value: 'CATALOG_ONLY', count: catalogCount },
          ].map((tab) => (
            <button
              key={tab.label}
              onClick={() => setStatusFilter(tab.value)}
              className={`flex items-center gap-[5px] px-3 py-[5px] rounded-md text-xs font-medium whitespace-nowrap transition-colors ${
                statusFilter === tab.value
                  ? 'bg-terminal-surface text-terminal-text font-semibold shadow-sm'
                  : 'text-terminal-text-secondary hover:text-terminal-text'
              }`}
            >
              {tab.label}
              <span
                className={`font-mono text-[10px] font-semibold ${
                  statusFilter === tab.value ? 'text-purple-500' : 'text-terminal-text-muted'
                }`}
              >
                {isLoading ? '...' : tab.count}
              </span>
            </button>
          ))}
        </div>

        {/* Family filter pills */}
        <div className="flex items-center gap-1 flex-wrap">
          <button
            onClick={() => setFamilyFilter(undefined)}
            className={`px-2.5 py-1 rounded text-[10px] font-mono font-semibold transition-colors ${
              !familyFilter
                ? 'bg-purple-500/10 text-purple-500 border border-purple-500/20'
                : 'text-terminal-text-muted hover:text-terminal-text'
            }`}
          >
            All Families
          </button>
          {FAMILIES.map((f) => (
            <button
              key={f}
              onClick={() => setFamilyFilter(f === familyFilter ? undefined : f)}
              className={`px-2.5 py-1 rounded text-[10px] font-mono font-semibold transition-colors ${
                familyFilter === f
                  ? 'bg-purple-500/10 text-purple-500 border border-purple-500/20'
                  : 'text-terminal-text-muted hover:text-terminal-text'
              }`}
            >
              {FAMILY_LABELS[f]}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-terminal-text-muted" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-48 bg-terminal-bg border border-terminal-border rounded-lg pl-8 pr-7 py-1.5 text-xs text-terminal-text font-mono placeholder:text-terminal-text-muted/50 focus:outline-none focus:border-purple-500/50"
            placeholder="Filter packs..."
          />
          {search && (
            <button
              onClick={() => setSearch('')}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-terminal-text-muted hover:text-terminal-text"
            >
              <X className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-5 h-5 text-terminal-text-muted animate-spin" />
        </div>
      )}

      {/* Error */}
      {error && !isLoading && (
        <div className="flex items-center gap-2 p-3 bg-status-failure/10 border border-status-failure/30 rounded-lg">
          <span className="text-xs text-status-failure">
            {(error as Error)?.message ?? 'Failed to load templates'}
          </span>
        </div>
      )}

      {/* Zero state */}
      {!isLoading && !error && templates.length === 0 && (
        <EmptyState
          type="ZERO_STATE"
          icon={<Boxes className="w-7 h-7" />}
          title="No scenario packs yet"
          description="Scenario packs are branching environments for agent training and RLMF telemetry. Seed the template catalog to get started."
          actions={[]}
        />
      )}

      {/* No results */}
      {!isLoading && !error && templates.length > 0 && filtered.length === 0 && (
        <div className="py-8 text-center">
          <div className="text-[13px] text-terminal-text-muted mb-1">
            No packs match current filters
          </div>
          <button
            onClick={() => {
              setSearch('');
              setFamilyFilter(undefined);
              setStatusFilter(undefined);
            }}
            className="text-xs text-purple-500 hover:underline"
          >
            Clear filters
          </button>
        </div>
      )}

      {/* Pack grid — 3 columns per reference */}
      {!isLoading && !error && filtered.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((t) => {
            const isRunnable = t.template_status === 'RUNNABLE';

            return (
              <div
                key={t.id}
                className="bg-terminal-surface border border-terminal-border rounded-lg overflow-hidden flex flex-col hover:border-purple-300/40 hover:shadow-sm transition-all cursor-pointer group"
              >
                {/* Card header: badges + status */}
                <div className="px-4 pt-4 flex items-start justify-between gap-3">
                  <div className="flex gap-1.5 flex-wrap">
                    <span className="text-[10px] font-semibold uppercase tracking-wide px-2 py-0.5 rounded bg-purple-500/10 text-purple-500">
                      {FAMILY_LABELS[t.family] ?? t.family}
                    </span>
                  </div>
                  <span
                    className={`flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wide shrink-0 ${
                      isRunnable ? 'text-status-success' : 'text-terminal-text-muted'
                    }`}
                  >
                    <span
                      className={`w-[5px] h-[5px] rounded-full ${
                        isRunnable ? 'bg-status-success' : 'bg-terminal-text-muted/40'
                      }`}
                    />
                    {isRunnable ? 'Runnable' : 'Catalog Only'}
                  </span>
                </div>

                {/* Card body: name + premise */}
                <div className="px-4 pt-3 flex-1">
                  <div className="text-[15px] font-semibold text-terminal-text leading-[22px] mb-1">
                    {t.name}
                  </div>
                  {t.description && (
                    <div className="text-[13px] text-terminal-text-secondary leading-5 line-clamp-2">
                      {t.description}
                    </div>
                  )}
                </div>

                {/* Mini branch preview */}
                <div className="px-4 py-3 mt-3">
                  <div className="flex items-center gap-2 h-7">
                    {/* Start node */}
                    <div className="w-2 h-2 rounded-full bg-purple-500 shrink-0" />
                    <div className="flex-1 h-0.5 bg-purple-300/40" />
                    {/* Checkpoint nodes */}
                    {Array.from({ length: Math.min(t.checkpoint_count, 5) }).map((_, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-orange-500 border-2 border-orange-200 shrink-0" />
                        <div className="flex-1 h-0.5 bg-terminal-border min-w-[8px]" />
                      </div>
                    ))}
                    {t.checkpoint_count > 5 && (
                      <span className="text-[9px] text-terminal-text-muted font-mono">+{t.checkpoint_count - 5}</span>
                    )}
                    {/* Fork indicator */}
                    <div className="flex flex-col gap-0.5 -mx-1">
                      <div className="w-3 h-0.5 rounded bg-status-success -rotate-[15deg]" />
                      <div className="w-3 h-0.5 rounded bg-status-failure rotate-[15deg]" />
                    </div>
                    <div className="flex-1 h-0.5 bg-terminal-border" />
                    {/* End node */}
                    <div className="w-2 h-2 rounded-full bg-status-success shrink-0" />
                  </div>
                </div>

                {/* Metrics strip — 4 columns per reference */}
                <div className="grid grid-cols-4 gap-px bg-terminal-border/50 border-t border-terminal-border/50 mt-auto">
                  {[
                    { value: t.checkpoint_count, label: 'Checkpoints' },
                    { value: t.fork_points_max, label: 'Branch Depth' },
                    { value: '—', label: 'Outcomes' },
                    { value: '—', label: 'Events' },
                  ].map((m) => (
                    <div key={m.label} className="bg-terminal-surface py-2 px-3 text-center">
                      <span className="font-mono text-[13px] font-bold tabular-nums text-terminal-text block">
                        {m.value}
                      </span>
                      <span className="text-[9px] font-semibold uppercase tracking-wide text-terminal-text-muted">
                        {m.label}
                      </span>
                    </div>
                  ))}
                </div>

                {/* Card actions — 3 buttons per reference */}
                <div className="flex gap-px bg-terminal-border/50 border-t border-terminal-border/50">
                  <Link
                    to={`/scenario-packs/${t.id}`}
                    className="flex-1 flex items-center justify-center gap-1 py-2 text-xs font-semibold text-terminal-text-secondary bg-terminal-surface hover:text-purple-500 hover:bg-purple-500/5 transition-colors"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <Eye className="w-3 h-3" />
                    Open Pack
                  </Link>
                  {isRunnable ? (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/scenario-packs/${t.id}?launch=true`);
                      }}
                      className="flex-1 flex items-center justify-center gap-1 py-2 text-xs font-semibold text-terminal-text-secondary bg-terminal-surface hover:text-purple-500 hover:bg-purple-500/5 transition-colors"
                    >
                      <Play className="w-3 h-3" />
                      Launch
                    </button>
                  ) : (
                    <button
                      disabled
                      className="flex-1 flex items-center justify-center gap-1 py-2 text-xs font-semibold text-terminal-text-muted/40 bg-terminal-surface cursor-not-allowed"
                    >
                      Catalog Only
                    </button>
                  )}
                  <Link
                    to={`/scenario-packs/${t.id}#branch-map`}
                    className="flex-1 flex items-center justify-center gap-1 py-2 text-xs font-semibold text-terminal-text-secondary bg-terminal-surface hover:text-purple-500 hover:bg-purple-500/5 transition-colors"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <GitBranch className="w-3 h-3" />
                    Branch Map
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
