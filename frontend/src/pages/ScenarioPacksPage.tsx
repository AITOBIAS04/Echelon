import { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ArrowUpRight,
  BookOpen,
  Boxes,
  Eye,
  GitBranch,
  Loader2,
  Play,
  Search,
  Sparkles,
  X,
} from 'lucide-react';
import { clsx } from 'clsx';
import { EmptyState } from '../components/empty-states/EmptyState';
import { useTemplateList } from '../hooks/useScenarioPacks';

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

function BranchPreview({
  checkpoints,
  depth,
}: {
  checkpoints: number;
  depth: number;
}) {
  const nodeCount = Math.max(2, Math.min(5, checkpoints));
  const nodes = Array.from({ length: nodeCount }, (_, index) => index);

  return (
    <div className="rounded-md border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-3 py-3">
      <div className="mb-2 flex items-center justify-between text-[11px] font-medium text-[var(--e-text-muted)]">
        <span>Branch Preview</span>
        <span className="font-mono">depth {depth}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="h-2.5 w-2.5 rounded-full bg-[var(--e-purple-500)]" />
        <div className="flex flex-1 items-center gap-2">
          {nodes.map((node, index) => (
            <div key={node} className="flex flex-1 items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-[var(--e-orange-500)]" />
              {index < nodes.length - 1 ? (
                <div className="h-px flex-1 bg-[var(--e-purple-200)]" />
              ) : null}
            </div>
          ))}
        </div>
        <span className="rounded-full bg-[var(--e-purple-50)] px-2 py-0.5 font-mono text-[10px] font-semibold text-[var(--e-purple-700)]">
          fork
        </span>
        <span className="h-2.5 w-2.5 rounded-full bg-[var(--e-green-600)]" />
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: string | number;
  tone?: 'success' | 'muted' | 'purple';
}) {
  const valueClass =
    tone === 'success'
      ? 'text-[var(--e-green-600)]'
      : tone === 'purple'
        ? 'text-[var(--e-purple-700)]'
        : tone === 'muted'
          ? 'text-[var(--e-text-muted)]'
          : 'text-[var(--e-text-primary)]';

  return (
    <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-3 shadow-[var(--e-shadow-xs)]">
      <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
        {label}
      </div>
      <div className={clsx('font-mono text-[24px] font-bold leading-8 tabular-nums', valueClass)}>
        {value}
      </div>
    </div>
  );
}

export function ScenarioPacksPage() {
  const navigate = useNavigate();
  const [familyFilter, setFamilyFilter] = useState<string | undefined>(undefined);
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);
  const [search, setSearch] = useState('');

  const { templates, total, isLoading, error } = useTemplateList({
    family: familyFilter,
    status: statusFilter,
  });

  const filtered = useMemo(() => {
    if (!search.trim()) return templates;
    const value = search.trim().toLowerCase();
    return templates.filter(
      (template) =>
        template.name.toLowerCase().includes(value) ||
        (template.description ?? '').toLowerCase().includes(value),
    );
  }, [search, templates]);

  const runnableCount = templates.filter((template) => template.template_status === 'RUNNABLE').length;
  const catalogCount = templates.filter((template) => template.template_status === 'CATALOG_ONLY').length;
  const maxBranchDepth = templates.length > 0 ? Math.max(...templates.map((template) => template.fork_points_max)) : 0;

  return (
    <div className="p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <p className="max-w-3xl text-[15px] leading-6 text-[var(--e-text-secondary)]">
            Browse branching runtime environments for training, evaluation, calibration, and replay.
          </p>
          <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-3 shadow-[var(--e-shadow-xs)]">
            <div className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              Surface
            </div>
            <div className="mt-1 text-[13px] font-medium text-[var(--e-text-primary)]">
              Catalog / runnable split preserved
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Total Packs" value={isLoading ? '…' : total} />
          <StatCard label="Runnable" value={isLoading ? '…' : runnableCount} tone="success" />
          <StatCard label="Catalog Only" value={isLoading ? '…' : catalogCount} tone="muted" />
          <StatCard label="Max Branch Depth" value={isLoading ? '…' : maxBranchDepth} tone="purple" />
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="inline-flex rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] p-1 shadow-[var(--e-shadow-xs)]">
            {[
              { label: 'All', value: undefined, count: total },
              { label: 'Runnable', value: 'RUNNABLE', count: runnableCount },
              { label: 'Catalog Only', value: 'CATALOG_ONLY', count: catalogCount },
            ].map((tab) => (
              <button
                key={tab.label}
                type="button"
                onClick={() => setStatusFilter(tab.value)}
                className={clsx(
                  'inline-flex items-center gap-2 rounded-md px-3 py-2 text-[13px] font-medium transition',
                  statusFilter === tab.value
                    ? 'bg-[var(--e-purple-50)] text-[var(--e-purple-700)]'
                    : 'text-[var(--e-text-secondary)] hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]',
                )}
              >
                {tab.label}
                <span className="font-mono text-[11px] tabular-nums text-[var(--e-text-muted)]">
                  {isLoading ? '…' : tab.count}
                </span>
              </button>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <div className="flex flex-wrap gap-1.5">
              <button
                type="button"
                onClick={() => setFamilyFilter(undefined)}
                className={clsx(
                  'rounded-full border px-3 py-1 text-[11px] font-semibold transition',
                  !familyFilter
                    ? 'border-[var(--e-purple-200)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)]'
                    : 'border-[var(--e-border-primary)] bg-[var(--e-bg-card)] text-[var(--e-text-secondary)] hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]',
                )}
              >
                All Families
              </button>
              {Object.entries(FAMILY_LABELS).map(([key, label]) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => setFamilyFilter((current) => (current === key ? undefined : key))}
                  className={clsx(
                    'rounded-full border px-3 py-1 text-[11px] font-semibold transition',
                    familyFilter === key
                      ? 'border-[var(--e-purple-200)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)]'
                      : 'border-[var(--e-border-primary)] bg-[var(--e-bg-card)] text-[var(--e-text-secondary)] hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]',
                  )}
                >
                  {label}
                </button>
              ))}
            </div>

            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--e-text-muted)]" />
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search packs…"
                className="h-10 w-56 rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] pl-9 pr-9 text-[13px] text-[var(--e-text-primary)] outline-none transition placeholder:text-[var(--e-text-muted)] focus:border-[var(--e-border-focus)]"
              />
              {search ? (
                <button
                  type="button"
                  onClick={() => setSearch('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--e-text-muted)] transition hover:text-[var(--e-text-primary)]"
                >
                  <X className="h-4 w-4" />
                </button>
              ) : null}
            </div>
          </div>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-6 py-16 shadow-[var(--e-shadow-xs)]">
            <Loader2 className="mr-2 h-5 w-5 animate-spin text-[var(--e-text-muted)]" />
            <span className="text-[14px] text-[var(--e-text-muted)]">Loading templates…</span>
          </div>
        ) : error ? (
          <div className="rounded-lg border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] px-5 py-4 text-[13px] text-[var(--e-red-600)] shadow-[var(--e-shadow-xs)]">
            {(error as Error)?.message ?? 'Failed to load scenario pack templates'}
          </div>
        ) : templates.length === 0 ? (
          <EmptyState
            type="ZERO_STATE"
            icon={<Boxes className="h-7 w-7" />}
            title="No scenario packs yet"
            description="Seed the pack catalog to start browsing runnable and catalog-only environments."
            actions={[]}
          />
        ) : filtered.length === 0 ? (
          <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-6 py-14 text-center shadow-[var(--e-shadow-xs)]">
            <div className="text-[15px] font-semibold text-[var(--e-text-primary)]">
              No packs match these filters
            </div>
            <button
              type="button"
              onClick={() => {
                setSearch('');
                setFamilyFilter(undefined);
                setStatusFilter(undefined);
              }}
              className="mt-3 text-[13px] font-medium text-[var(--e-purple-700)] transition hover:text-[var(--e-purple-500)]"
            >
              Clear filters
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2 xl:grid-cols-3">
            {filtered.map((template) => {
              const isRunnable = template.template_status === 'RUNNABLE';
              const canLaunch = isRunnable;
              const outcomesValue = '—';
              const telemetryValue = '—';

              return (
                <article
                  key={template.id}
                  className="flex h-full flex-col rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-sm)] transition hover:-translate-y-0.5 hover:border-[var(--e-purple-200)] hover:shadow-[var(--e-shadow-md)]"
                >
                  <div className="flex items-start justify-between gap-3 px-5 pt-5">
                    <div className="flex flex-wrap gap-2">
                      <span className="inline-flex items-center rounded-full border border-[var(--e-purple-200)] bg-[var(--e-purple-50)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-purple-700)]">
                        {FAMILY_LABELS[template.family] ?? template.family}
                      </span>
                    </div>
                    <span
                      className={clsx(
                        'inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.04em]',
                        isRunnable
                          ? 'bg-[var(--e-green-50)] text-[var(--e-green-600)]'
                          : 'bg-[var(--e-bg-sunken)] text-[var(--e-text-muted)]',
                      )}
                    >
                      <span
                        className={clsx(
                          'h-2 w-2 rounded-full',
                          isRunnable ? 'bg-[var(--e-green-600)]' : 'bg-[var(--e-text-disabled)]',
                        )}
                      />
                      {template.template_status === 'RUNNABLE' ? 'Runnable' : 'Catalog Only'}
                    </span>
                  </div>

                  <div className="flex flex-1 flex-col px-5 pb-5 pt-4">
                    <div className="mb-2 text-[20px] font-bold tracking-[-0.02em] text-[var(--e-text-primary)]">
                      {template.name}
                    </div>
                    <p className="mb-4 line-clamp-2 min-h-[44px] text-[14px] leading-6 text-[var(--e-text-secondary)]">
                      {template.description ?? 'No scenario summary provided.'}
                    </p>

                    <BranchPreview checkpoints={template.checkpoint_count} depth={template.fork_points_max} />

                    <div className="mt-4 grid grid-cols-4 gap-2 rounded-md border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-3 py-3">
                      {[
                        { label: 'Checkpoints', value: template.checkpoint_count },
                        { label: 'Branch Depth', value: template.fork_points_max },
                        { label: 'Outcomes', value: outcomesValue },
                        { label: 'Events', value: telemetryValue },
                      ].map((metric) => (
                        <div key={metric.label} className="min-w-0">
                          <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-text-muted)]">
                            {metric.label}
                          </div>
                          <div className="truncate font-mono text-[13px] font-semibold text-[var(--e-text-primary)]">
                            {metric.value}
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="mt-4 flex flex-wrap gap-2">
                      <Link
                        to={`/scenario-packs/${template.id}`}
                        className="inline-flex items-center gap-1.5 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 py-2 text-[12px] font-semibold text-[var(--e-text-secondary)] no-underline transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]"
                      >
                        <Eye className="h-3.5 w-3.5" />
                        Open Pack
                      </Link>

                      {canLaunch ? (
                        <button
                          type="button"
                          onClick={() => navigate(`/scenario-packs/${template.id}?launch=true`)}
                          className="inline-flex items-center gap-1.5 rounded-md bg-[var(--e-purple-500)] px-3 py-2 text-[12px] font-semibold text-[var(--e-text-inverse)] transition hover:bg-[var(--e-purple-600)]"
                        >
                          <Play className="h-3.5 w-3.5" />
                          Launch
                        </button>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-sunken)] px-3 py-2 text-[12px] font-semibold text-[var(--e-text-disabled)]">
                          <BookOpen className="h-3.5 w-3.5" />
                          Catalog Only
                        </span>
                      )}

                      <Link
                        to={`/scenario-packs/${template.id}#branch-map`}
                        className="inline-flex items-center gap-1.5 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 py-2 text-[12px] font-semibold text-[var(--e-text-secondary)] no-underline transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]"
                      >
                        <GitBranch className="h-3.5 w-3.5" />
                        Branch Map
                      </Link>
                    </div>

                    <div className="mt-4 flex items-center justify-between border-t border-[var(--e-border-secondary)] pt-4">
                      <div className="inline-flex items-center gap-2 text-[12px] text-[var(--e-text-muted)]">
                        <Sparkles className="h-4 w-4 text-[var(--e-purple-500)]" />
                        {template.is_seeded ? 'Seeded template' : 'Unseeded template'}
                      </div>
                      <Link
                        to={`/scenario-packs/${template.id}`}
                        className="inline-flex items-center gap-1 text-[12px] font-semibold text-[var(--e-purple-700)] no-underline transition hover:text-[var(--e-purple-500)]"
                      >
                        View detail
                        <ArrowUpRight className="h-3.5 w-3.5" />
                      </Link>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
