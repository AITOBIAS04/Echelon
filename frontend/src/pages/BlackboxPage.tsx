import { useMemo, useState, type ReactNode } from 'react';
import { clsx } from 'clsx';
import { Link } from 'react-router-dom';
import {
  Activity,
  ChartColumn,
  Download,
  ExternalLink,
  Save,
  ShieldAlert,
  Trash2,
} from 'lucide-react';
import { usePlatformAnalytics, usePortfolioAnalytics } from '../hooks/useAnalytics';
import type { AnalyticsComparison, AnalyticsBreakdownFilters, AnalyticsExplanationItem } from '../api/analytics';
import { useAnalyticsPresets } from '../hooks/useAnalyticsPresets';

type AnalyticsTab = 'platform' | 'portfolio';
type BreakdownFilterKey = keyof AnalyticsBreakdownFilters;

function toneClass(tone?: 'danger' | 'warning' | 'success' | 'info') {
  switch (tone) {
    case 'danger':
      return 'text-[var(--e-red-600)]';
    case 'warning':
      return 'text-[var(--e-orange-600)]';
    case 'success':
      return 'text-[var(--e-green-600)]';
    case 'info':
      return 'text-[var(--e-purple-700)]';
    default:
      return 'text-[var(--e-text-primary)]';
  }
}

function humanizeKey(value: string) {
  return value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

function AnalyticsKpi({
  label,
  value,
  detail,
  tone,
}: {
  label: string;
  value: string | number;
  detail?: string;
  tone?: 'danger' | 'warning' | 'success' | 'info';
}) {
  return (
    <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-4 shadow-[var(--e-shadow-xs)]">
      <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
        {label}
      </div>
      <div className={clsx('font-mono text-[28px] font-bold leading-8 tabular-nums', toneClass(tone))}>
        {value}
      </div>
      {detail ? <div className="mt-1 text-[12px] text-[var(--e-text-muted)]">{detail}</div> : null}
    </div>
  );
}

function exportBlob(filename: string, content: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function SectionCard({
  title,
  eyebrow,
  children,
  action,
}: {
  title: string;
  eyebrow?: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
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

function BreakdownRows({
  rows,
  emptyLabel,
}: {
  rows: Array<{ label: string; value: number; tone?: 'purple' | 'green' | 'orange' | 'red' }>;
  emptyLabel: string;
}) {
  const maxValue = rows.length > 0 ? Math.max(...rows.map((row) => row.value), 1) : 1;

  if (rows.length === 0) {
    return <div className="text-[13px] text-[var(--e-text-muted)]">{emptyLabel}</div>;
  }

  return (
    <div className="space-y-3">
      {rows.map((row) => (
        <div key={row.label} className="grid grid-cols-[120px_minmax(0,1fr)_60px] items-center gap-3">
          <div className="truncate text-[12px] font-medium text-[var(--e-text-secondary)]">{row.label}</div>
          <div className="h-2 overflow-hidden rounded-full bg-[var(--e-bg-sunken)]">
            <div
              className={clsx(
                'h-full rounded-full',
                row.tone === 'green'
                  ? 'bg-[var(--e-green-500)]'
                  : row.tone === 'orange'
                    ? 'bg-[var(--e-orange-500)]'
                    : row.tone === 'red'
                      ? 'bg-[var(--e-red-500)]'
                      : 'bg-[var(--e-purple-500)]',
              )}
              style={{ width: `${Math.max((row.value / maxValue) * 100, 6)}%` }}
            />
          </div>
          <div className="text-right font-mono text-[12px] font-semibold tabular-nums text-[var(--e-text-primary)]">
            {row.value}
          </div>
        </div>
      ))}
    </div>
  );
}

function SparseCard({
  title,
  description,
  eyebrow,
}: {
  title: string;
  description: string;
  eyebrow: string;
}) {
  return (
    <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-sunken)] px-5 py-8 text-center">
      <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
        {eyebrow}
      </div>
      <div className="text-[15px] font-semibold text-[var(--e-text-primary)]">{title}</div>
      <p className="mx-auto mt-2 max-w-xl text-[13px] leading-6 text-[var(--e-text-secondary)]">{description}</p>
    </div>
  );
}

function TrendStack({
  title,
  description,
  rows,
  selectedDate,
  onSelectDate,
}: {
  title: string;
  description: string;
  rows: Array<{
    label: string;
    points: Array<{ timestamp: string | Date; value: number }>;
    tone: 'purple' | 'green' | 'orange' | 'red';
    comparison?: AnalyticsComparison;
  }>;
  selectedDate?: string;
  onSelectDate?: (value?: string) => void;
}) {
  return (
    <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-card)] px-4 py-4">
      <div className="text-[13px] font-semibold text-[var(--e-text-primary)]">{title}</div>
      <div className="mt-1 text-[12px] leading-5 text-[var(--e-text-secondary)]">{description}</div>
      <div className="mt-4 space-y-4">
        {rows.map((row) => {
          const maxValue = row.points.length > 0 ? Math.max(...row.points.map((point) => point.value), 1) : 1;
          const barClass =
            row.tone === 'green'
              ? 'bg-[var(--e-green-500)]'
              : row.tone === 'orange'
                ? 'bg-[var(--e-orange-500)]'
                : row.tone === 'red'
                  ? 'bg-[var(--e-red-500)]'
                  : 'bg-[var(--e-purple-500)]';

          return (
            <div key={row.label} className="space-y-2">
              <div className="flex items-center justify-between gap-3">
                <div className="text-[12px] font-medium text-[var(--e-text-secondary)]">{row.label}</div>
                <div className="text-right">
                  <div className="font-mono text-[11px] text-[var(--e-text-muted)]">
                    {row.points.length > 0 ? `${Math.round(row.points[row.points.length - 1]!.value)}` : '—'}
                  </div>
                  {row.comparison ? (
                    <div
                      className={clsx(
                        'mt-1 font-mono text-[10px]',
                        row.comparison.delta > 0
                          ? 'text-[var(--e-green-600)]'
                          : row.comparison.delta < 0
                            ? 'text-[var(--e-red-600)]'
                            : 'text-[var(--e-text-muted)]',
                      )}
                    >
                      {formatComparison(row.comparison)}
                    </div>
                  ) : null}
                </div>
              </div>
              {row.points.length === 0 ? (
                <div className="rounded-md border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-3 py-2 text-[12px] text-[var(--e-text-muted)]">
                  No data yet.
                </div>
              ) : (
                <div className="flex items-end gap-1">
                  {row.points.map((point) => (
                    <button
                      type="button"
                      key={`${row.label}-${String(point.timestamp)}`}
                      onClick={() => {
                        if (!onSelectDate) {
                          return;
                        }
                        const bucket = new Date(point.timestamp).toISOString().slice(0, 10);
                        onSelectDate(selectedDate === bucket ? undefined : bucket);
                      }}
                      className={clsx(
                        'flex-1 rounded-t-sm bg-[var(--e-bg-sunken)] text-left transition',
                        onSelectDate ? 'cursor-pointer hover:ring-1 hover:ring-[var(--e-purple-300)]' : 'cursor-default',
                        selectedDate === new Date(point.timestamp).toISOString().slice(0, 10)
                          ? 'ring-2 ring-[var(--e-purple-400)]'
                          : '',
                      )}
                      title={`${new Date(point.timestamp).toLocaleDateString()} · ${Math.round(point.value)}`}
                    >
                      <div
                        className={clsx('w-full rounded-t-sm', barClass)}
                        style={{
                          height: `${Math.max((point.value / maxValue) * 72, point.value > 0 ? 8 : 2)}px`,
                        }}
                      />
                    </button>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
      {onSelectDate ? (
        <div className="mt-3 text-[11px] text-[var(--e-text-muted)]">
          Click a day bar to filter explanations to that bucket.
        </div>
      ) : null}
    </div>
  );
}

function FilterSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="flex min-w-[150px] flex-col gap-1">
      <span className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
        {label}
      </span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-10 rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 text-[13px] text-[var(--e-text-primary)] shadow-[var(--e-shadow-xs)] outline-none focus:border-[var(--e-purple-400)]"
      >
        <option value="">All</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {humanizeKey(option)}
          </option>
        ))}
      </select>
    </label>
  );
}

function explanationToneClass(tone: string) {
  switch (tone) {
    case 'success':
      return 'border-[var(--e-green-200)] bg-[var(--e-green-50)]';
    case 'warning':
      return 'border-[var(--e-orange-200)] bg-[var(--e-orange-50)]';
    case 'danger':
      return 'border-[var(--e-red-200)] bg-[var(--e-red-50)]';
    case 'info':
      return 'border-[var(--e-purple-200)] bg-[var(--e-purple-50)]';
    default:
      return 'border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)]';
  }
}

function provenanceLabel(provenance: string) {
  switch (provenance) {
    case 'persisted_lifecycle':
      return {
        label: 'Persisted lifecycle',
        className: 'border-[var(--e-purple-200)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)]',
      };
    case 'persisted_operational_context':
      return {
        label: 'Persisted context',
        className: 'border-[var(--e-orange-200)] bg-[var(--e-orange-50)] text-[var(--e-orange-700)]',
      };
    case 'live_registry':
      return {
        label: 'Live registry',
        className: 'border-[var(--e-green-200)] bg-[var(--e-green-50)] text-[var(--e-green-700)]',
      };
    case 'inferred_operational_context':
      return {
        label: 'Inferred context',
        className: 'border-[var(--e-border-primary)] bg-[var(--e-bg-card)] text-[var(--e-text-muted)]',
      };
    default:
      return {
        label: provenance.replace(/_/g, ' '),
        className: 'border-[var(--e-border-primary)] bg-[var(--e-bg-card)] text-[var(--e-text-muted)]',
      };
  }
}

function ExplanationLinks({ item }: { item: AnalyticsExplanationItem }) {
  const links: Array<{ label: string; to: string }> = [];
  if (item.theatre_id) {
    links.push({ label: 'Open theatre', to: `/theatre/${item.theatre_id}` });
  }
  if (item.investigation_id) {
    links.push({ label: 'Open investigation', to: `/investigations?investigation=${item.investigation_id}` });
  }
  if (item.certificate_id) {
    links.push({ label: 'Open verify', to: `/verify?certificate=${item.certificate_id}` });
  }

  if (links.length === 0) {
    return null;
  }

  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {links.map((link) => (
        <Link
          key={`${item.id}-${link.label}`}
          to={link.to}
          className="inline-flex items-center gap-1 rounded-full border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-2.5 py-1 text-[11px] font-semibold text-[var(--e-text-primary)] shadow-[var(--e-shadow-xs)] transition hover:border-[var(--e-purple-300)] hover:text-[var(--e-purple-700)]"
        >
          {link.label}
          <ExternalLink className="h-3 w-3" />
        </Link>
      ))}
    </div>
  );
}

function ExplanationList({
  title,
  eyebrow,
  items,
  emptyLabel,
}: {
  title: string;
  eyebrow: string;
  items: AnalyticsExplanationItem[];
  emptyLabel: string;
}) {
  return (
    <div className="space-y-3">
      <div>
        <div className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">{eyebrow}</div>
        <div className="mt-1 text-[13px] font-semibold text-[var(--e-text-primary)]">{title}</div>
      </div>
      {items.length === 0 ? (
        <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3 text-[12px] text-[var(--e-text-muted)]">
          {emptyLabel}
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <div
              key={`${title}-${item.id}`}
              className={clsx(
                'rounded-lg border px-4 py-3 shadow-[var(--e-shadow-xs)]',
                explanationToneClass(item.tone),
              )}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <div className="text-[12px] font-semibold text-[var(--e-text-primary)]">{item.title}</div>
                    <span
                      className={clsx(
                        'inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold',
                        provenanceLabel(item.provenance).className,
                      )}
                    >
                      {provenanceLabel(item.provenance).label}
                    </span>
                  </div>
                  <div className="mt-1 text-[12px] leading-5 text-[var(--e-text-secondary)]">{item.summary}</div>
                </div>
                <div className="whitespace-nowrap font-mono text-[11px] text-[var(--e-text-muted)]">
                  {new Date(item.timestamp).toLocaleDateString()}
                </div>
              </div>
              <ExplanationLinks item={item} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function formatComparison(comparison: AnalyticsComparison) {
  const delta = comparison.delta;
  const sign = delta > 0 ? '+' : delta < 0 ? '' : '';
  if (comparison.change_pct == null) {
    return `${sign}${Math.round(delta)} vs prev`;
  }
  return `${sign}${Math.round(delta)} (${sign}${Math.round(comparison.change_pct)}%)`;
}

export function BlackboxPage() {
  const [activeTab, setActiveTab] = useState<AnalyticsTab>('platform');
  const [breakdownFilters, setBreakdownFilters] = useState<AnalyticsBreakdownFilters>({});
  const [selectedPlatformBucket, setSelectedPlatformBucket] = useState<string | undefined>();
  const [selectedRiskBucket, setSelectedRiskBucket] = useState<string | undefined>();
  const { platform, breakdowns, riskTrend, isLoading: platformLoading, error: platformErrorRaw } =
    usePlatformAnalytics('30d', breakdownFilters, {
      platform: selectedPlatformBucket,
      risk: selectedRiskBucket,
    });
  const {
    portfolio,
    isLoading: portfolioLoading,
    error: portfolioErrorRaw,
  } = usePortfolioAnalytics();
  const {
    views,
    selectedViewId,
    selectedView,
    selectView,
    createView,
    saveIntoView,
    removeView,
  } = useAnalyticsPresets();

  const platformError = platformErrorRaw instanceof Error ? platformErrorRaw.message : null;
  const portfolioError = portfolioErrorRaw instanceof Error ? portfolioErrorRaw.message : null;

  const categoryRows = useMemo(
    () =>
      Object.entries(breakdowns.signal_categories)
        .sort((left, right) => right[1] - left[1])
        .slice(0, 5)
        .map(([label, value]) => ({ label: humanizeKey(label), value, tone: 'purple' as const })),
    [breakdowns.signal_categories],
  );

  const sourceRows = useMemo(
    () =>
      Object.entries(breakdowns.signal_sources)
        .sort((left, right) => right[1] - left[1])
        .slice(0, 5)
        .map(([label, value]) => ({ label: humanizeKey(label), value, tone: 'green' as const })),
    [breakdowns.signal_sources],
  );

  const severityRows = useMemo(
    () =>
      Object.entries(breakdowns.signal_severities)
        .sort((left, right) => right[1] - left[1])
        .map(([label, value]) => ({
          label: humanizeKey(label),
          value,
          tone:
            label === 'critical'
              ? ('red' as const)
              : label === 'high'
                ? ('orange' as const)
                      : ('purple' as const),
        })),
    [breakdowns.signal_severities],
  );

  const theatreTrend = platform.timeseries.theatres_created ?? [];
  const investigationTrend = platform.timeseries.investigations_created ?? [];
  const certificateTrend = platform.timeseries.certificates_issued ?? [];
  const paradoxTrend = riskTrend.timeseries.active_paradoxes ?? [];
  const driftTrend = riskTrend.timeseries.material_drift_events ?? [];
  const reviewRequiredTrend = riskTrend.timeseries.review_required_certificates ?? [];
  const lifecycleExplanations = useMemo(
    () => [
      ...(platform.explanations.theatres_created ?? []),
      ...(platform.explanations.investigations_created ?? []),
      ...(platform.explanations.certificates_issued ?? []),
      ...(platform.explanations.deployments_created ?? []),
      ...(platform.explanations.deployment_lifecycle ?? []),
      ...(platform.explanations.certificate_ready ?? []),
      ...(platform.explanations.wing_flaps ?? []),
    ].sort((left, right) => new Date(right.timestamp).getTime() - new Date(left.timestamp).getTime()).slice(0, 6),
    [platform.explanations],
  );
  const riskExplanations = useMemo(
    () => [
      ...(riskTrend.explanations.active_paradoxes ?? []),
      ...(riskTrend.explanations.material_drift_events ?? []),
      ...(riskTrend.explanations.readiness_met ?? []),
      ...(riskTrend.explanations.review_required_certificates ?? []),
      ...(riskTrend.explanations.routing_transitions ?? []),
    ].sort((left, right) => new Date(right.timestamp).getTime() - new Date(left.timestamp).getTime()).slice(0, 6),
    [riskTrend.explanations],
  );
  const portfolioCurrent = portfolio.current ?? {
    total_notional: 0,
    total_unrealised_pnl: 0,
    position_count: 0,
    winning_positions: 0,
    losing_positions: 0,
    at_risk_positions: 0,
  };
  const portfolioHasData = portfolioCurrent.position_count > 0;

  const activeBreakdownFilterCount = Object.keys(breakdownFilters).length;
  const signalCategoryOptions = useMemo(
    () => Object.keys(breakdowns.signal_categories),
    [breakdowns.signal_categories],
  );
  const signalSourceOptions = useMemo(
    () => Object.keys(breakdowns.signal_sources),
    [breakdowns.signal_sources],
  );
  const theatreFamilyOptions = useMemo(
    () => Object.keys(breakdowns.theatre_families),
    [breakdowns.theatre_families],
  );
  const theatreInquiryOptions = useMemo(
    () => Object.keys(breakdowns.theatre_inquiry_classes),
    [breakdowns.theatre_inquiry_classes],
  );
  const investigationClassOptions = useMemo(
    () => Object.keys(breakdowns.investigation_classes),
    [breakdowns.investigation_classes],
  );
  const agentArchetypeOptions = useMemo(
    () => Object.keys(breakdowns.agent_archetypes),
    [breakdowns.agent_archetypes],
  );

  const updateBreakdownFilter = (key: BreakdownFilterKey, value: string) => {
    setBreakdownFilters((current) => {
      if (!value) {
        const next = { ...current };
        delete next[key];
        return next;
      }
      return { ...current, [key]: value };
    });
  };

  const clearBreakdownFilters = () => setBreakdownFilters({});

  const applyView = (viewId: string) => {
    const view = views.find((candidate) => candidate.id === viewId);
    if (!view) {
      return;
    }
    setActiveTab(view.tab);
    setBreakdownFilters(view.filters ?? {});
    setSelectedPlatformBucket(view.selectedPlatformBucket);
    setSelectedRiskBucket(view.selectedRiskBucket);
    selectView(view.id);
  };

  const saveCurrentView = () => {
    const name = window.prompt('Save analytics view as:', selectedView?.name ?? '');
    if (!name) {
      return;
    }
    if (selectedView && selectedView.name === name) {
      saveIntoView(selectedView.id, {
        tab: activeTab,
        filters: breakdownFilters,
        selectedPlatformBucket,
        selectedRiskBucket,
      });
      return;
    }
    createView({
      name,
      tab: activeTab,
      filters: breakdownFilters,
      selectedPlatformBucket,
      selectedRiskBucket,
    });
  };

  const updateSelectedView = () => {
    if (!selectedView) {
      saveCurrentView();
      return;
    }
    saveIntoView(selectedView.id, {
      tab: activeTab,
      filters: breakdownFilters,
      selectedPlatformBucket,
      selectedRiskBucket,
    });
  };

  const deleteSelectedView = () => {
    if (!selectedView) {
      return;
    }
    if (window.confirm(`Delete analytics view "${selectedView.name}"?`)) {
      removeView(selectedView.id);
    }
  };

  const exportCurrentJson = () => {
    const payload =
      activeTab === 'platform'
        ? {
            exported_at: new Date().toISOString(),
            tab: activeTab,
            filters: breakdownFilters,
            selectedPlatformBucket,
            selectedRiskBucket,
            platform,
            breakdowns,
            riskTrend,
          }
        : {
            exported_at: new Date().toISOString(),
            tab: activeTab,
            portfolio,
          };
    exportBlob(
      `analytics-${activeTab}-${new Date().toISOString().slice(0, 10)}.json`,
      JSON.stringify(payload, null, 2),
      'application/json',
    );
  };

  const exportCurrentCsv = () => {
    if (activeTab === 'platform') {
      const lines = [
        'section,label,value',
        `current,active_theatres,${platform.current.active_theatres}`,
        `current,completed_theatres,${platform.current.completed_theatres}`,
        `current,active_investigations,${platform.current.active_investigations}`,
        `current,ready_investigations,${platform.current.ready_investigations}`,
        `current,issued_certificates,${platform.current.issued_certificates}`,
        `current,active_paradoxes,${platform.current.active_paradoxes}`,
        `current,active_signals,${platform.current.active_signals}`,
        `current,critical_signals,${platform.current.critical_signals}`,
        ...Object.entries(breakdowns.signal_categories).map(([label, value]) => `signal_category,${label},${value}`),
        ...Object.entries(breakdowns.signal_sources).map(([label, value]) => `signal_source,${label},${value}`),
        ...Object.entries(breakdowns.investigation_classes).map(([label, value]) => `investigation_class,${label},${value}`),
      ];
      exportBlob(
        `analytics-${activeTab}-${new Date().toISOString().slice(0, 10)}.csv`,
        lines.join('\n'),
        'text/csv;charset=utf-8',
      );
      return;
    }

    const lines = [
      'timeline_id,timeline_name,side,current_price,average_entry_price,shards_held,notional,unrealised_pnl,has_active_paradox,logic_gap',
      ...portfolio.top_positions.map((position) =>
        [
          position.timeline_id,
          `"${position.timeline_name.replace(/"/g, '""')}"`,
          position.side,
          position.current_price,
          position.average_entry_price,
          position.shards_held,
          position.notional,
          position.unrealised_pnl,
          position.has_active_paradox,
          position.logic_gap,
        ].join(','),
      ),
    ];
    exportBlob(
      `analytics-${activeTab}-${new Date().toISOString().slice(0, 10)}.csv`,
      lines.join('\n'),
      'text/csv;charset=utf-8',
    );
  };

  return (
    <div className="p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <section className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-4 shadow-[var(--e-shadow-xs)]">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                Analytics Views
              </div>
              <div className="mt-1 text-[13px] text-[var(--e-text-secondary)]">
                Save, update, and export the current backend-backed analytics slice.
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={saveCurrentView}
                className="inline-flex items-center gap-2 rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 py-2 text-[12px] font-semibold text-[var(--e-text-primary)] shadow-[var(--e-shadow-xs)] hover:border-[var(--e-purple-300)] hover:text-[var(--e-purple-700)]"
              >
                <Save className="h-4 w-4" />
                Save view
              </button>
              <button
                type="button"
                onClick={updateSelectedView}
                className="inline-flex items-center gap-2 rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 py-2 text-[12px] font-semibold text-[var(--e-text-primary)] shadow-[var(--e-shadow-xs)] hover:border-[var(--e-purple-300)] hover:text-[var(--e-purple-700)]"
              >
                <Save className="h-4 w-4" />
                Update selected
              </button>
              <button
                type="button"
                onClick={exportCurrentJson}
                className="inline-flex items-center gap-2 rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 py-2 text-[12px] font-semibold text-[var(--e-text-primary)] shadow-[var(--e-shadow-xs)] hover:border-[var(--e-purple-300)] hover:text-[var(--e-purple-700)]"
              >
                <Download className="h-4 w-4" />
                Export JSON
              </button>
              <button
                type="button"
                onClick={exportCurrentCsv}
                className="inline-flex items-center gap-2 rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 py-2 text-[12px] font-semibold text-[var(--e-text-primary)] shadow-[var(--e-shadow-xs)] hover:border-[var(--e-purple-300)] hover:text-[var(--e-purple-700)]"
              >
                <Download className="h-4 w-4" />
                Export CSV
              </button>
              {selectedView ? (
                <button
                  type="button"
                  onClick={deleteSelectedView}
                  className="inline-flex items-center gap-2 rounded-lg border border-[var(--e-red-200)] bg-[var(--e-red-50)] px-3 py-2 text-[12px] font-semibold text-[var(--e-red-600)] shadow-[var(--e-shadow-xs)] hover:border-[var(--e-red-300)]"
                >
                  <Trash2 className="h-4 w-4" />
                  Delete selected
                </button>
              ) : null}
            </div>
          </div>
        </section>

        <section className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-4 shadow-[var(--e-shadow-xs)]">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div>
              <div className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                Phase 5
              </div>
              <div className="mt-1 text-[13px] font-semibold text-[var(--e-text-primary)]">
                Saved views
              </div>
            </div>
            <div className="text-[11px] text-[var(--e-text-muted)]">
              Stored in this browser only.
            </div>
          </div>
          {views.length === 0 ? (
            <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3 text-[12px] text-[var(--e-text-muted)]">
              No analytics views saved yet.
            </div>
          ) : (
            <div className="flex flex-wrap gap-2">
              {views.map((view) => (
                <button
                  key={view.id}
                  type="button"
                  onClick={() => applyView(view.id)}
                  className={clsx(
                    'rounded-full border px-3 py-1.5 text-[12px] font-semibold transition',
                    selectedViewId === view.id
                      ? 'border-[var(--e-purple-300)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)]'
                      : 'border-[var(--e-border-primary)] bg-[var(--e-bg-card)] text-[var(--e-text-primary)] hover:border-[var(--e-purple-300)] hover:text-[var(--e-purple-700)]',
                  )}
                >
                  {view.name}
                </button>
              ))}
            </div>
          )}
        </section>

        <div className="border-b border-[var(--e-border-primary)]">
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => setActiveTab('platform')}
              className={clsx(
                'h-10 px-5 text-[13px] font-semibold transition',
                activeTab === 'platform'
                  ? 'border-b-2 border-[var(--e-purple-500)] text-[var(--e-purple-700)]'
                  : 'text-[var(--e-text-muted)] hover:text-[var(--e-text-primary)]',
              )}
            >
              Platform
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('portfolio')}
              className={clsx(
                'h-10 px-5 text-[13px] font-semibold transition',
                activeTab === 'portfolio'
                  ? 'border-b-2 border-[var(--e-purple-500)] text-[var(--e-purple-700)]'
                  : 'text-[var(--e-text-muted)] hover:text-[var(--e-text-primary)]',
              )}
            >
              Portfolio
            </button>
          </div>
        </div>

        {activeTab === 'platform' ? (
          <>
            {platformError ? (
              <SparseCard
                eyebrow="Load issue"
                title="Platform analytics unavailable"
                description={platformError}
              />
            ) : null}

            <div className="grid gap-4 md:grid-cols-4">
              <AnalyticsKpi
                label="Active Theatres"
                value={platformLoading ? '—' : platform.current.active_theatres}
                detail="Open theatre lifecycle"
              />
              <AnalyticsKpi
                label="Issued Certificates"
                value={platformLoading ? '—' : platform.current.issued_certificates}
                detail="Theatre + investigation"
                tone={platform.current.issued_certificates > 0 ? 'success' : undefined}
              />
              <AnalyticsKpi
                label="Active Paradoxes"
                value={platformLoading ? '—' : platform.current.active_paradoxes}
                detail="Persisted paradox windows"
                tone={platform.current.active_paradoxes > 0 ? 'warning' : 'success'}
              />
              <AnalyticsKpi
                label="Investigations"
                value={platformLoading ? '—' : platform.current.active_investigations}
                detail={`${platform.current.ready_investigations} ready for certificate`}
                tone={platform.current.active_investigations > 0 ? 'info' : undefined}
              />
            </div>

            <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_300px]">
              <div className="space-y-4">
                <SectionCard title="Operational distribution" eyebrow="Platform">
                  <div className="mb-5 space-y-3 rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] p-4">
                    <div className="flex flex-wrap items-end justify-between gap-3">
                      <div>
                        <div className="text-[12px] font-semibold text-[var(--e-text-primary)]">
                          Drilldown filters
                        </div>
                        <div className="mt-1 text-[12px] text-[var(--e-text-secondary)]">
                          Slice the distribution layer by persisted backend dimensions. Trend windows remain global until slice-specific series ship.
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={clearBreakdownFilters}
                        disabled={activeBreakdownFilterCount === 0}
                        className={clsx(
                          'rounded-lg px-3 py-2 text-[12px] font-semibold transition',
                          activeBreakdownFilterCount === 0
                            ? 'cursor-not-allowed bg-[var(--e-bg-card)] text-[var(--e-text-muted)]'
                            : 'bg-[var(--e-purple-50)] text-[var(--e-purple-700)] hover:bg-[var(--e-purple-100)]',
                        )}
                      >
                        Clear filters
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-3">
                      <FilterSelect
                        label="Signal category"
                        value={breakdownFilters.signal_category ?? ''}
                        options={signalCategoryOptions}
                        onChange={(value) => updateBreakdownFilter('signal_category', value)}
                      />
                      <FilterSelect
                        label="Signal source"
                        value={breakdownFilters.signal_source ?? ''}
                        options={signalSourceOptions}
                        onChange={(value) => updateBreakdownFilter('signal_source', value)}
                      />
                      <FilterSelect
                        label="Theatre family"
                        value={breakdownFilters.theatre_family ?? ''}
                        options={theatreFamilyOptions}
                        onChange={(value) => updateBreakdownFilter('theatre_family', value)}
                      />
                      <FilterSelect
                        label="Theatre class"
                        value={breakdownFilters.theatre_inquiry_class ?? ''}
                        options={theatreInquiryOptions}
                        onChange={(value) => updateBreakdownFilter('theatre_inquiry_class', value)}
                      />
                      <FilterSelect
                        label="Investigation class"
                        value={breakdownFilters.investigation_class ?? ''}
                        options={investigationClassOptions}
                        onChange={(value) => updateBreakdownFilter('investigation_class', value)}
                      />
                      <FilterSelect
                        label="Agent archetype"
                        value={breakdownFilters.agent_archetype ?? ''}
                        options={agentArchetypeOptions}
                        onChange={(value) => updateBreakdownFilter('agent_archetype', value)}
                      />
                    </div>
                    {activeBreakdownFilterCount > 0 ? (
                      <div className="text-[12px] text-[var(--e-text-muted)]">
                        Showing {activeBreakdownFilterCount} applied filter{activeBreakdownFilterCount === 1 ? '' : 's'} from the analytics backend.
                      </div>
                    ) : null}
                  </div>
                  <div className="grid gap-4 lg:grid-cols-3">
                    <div className="space-y-3">
                      <div className="flex items-center gap-2 text-[var(--e-text-primary)]">
                        <ChartColumn className="h-4 w-4 text-[var(--e-purple-700)]" />
                        <span className="text-[12px] font-semibold uppercase tracking-[0.04em]">Signal categories</span>
                      </div>
                      <BreakdownRows rows={categoryRows} emptyLabel="No category counts available." />
                    </div>
                    <div className="space-y-3">
                      <div className="flex items-center gap-2 text-[var(--e-text-primary)]">
                        <Activity className="h-4 w-4 text-[var(--e-green-600)]" />
                        <span className="text-[12px] font-semibold uppercase tracking-[0.04em]">Source families</span>
                      </div>
                      <BreakdownRows rows={sourceRows} emptyLabel="No source-family counts available." />
                    </div>
                    <div className="space-y-3">
                      <div className="flex items-center gap-2 text-[var(--e-text-primary)]">
                        <ShieldAlert className="h-4 w-4 text-[var(--e-orange-600)]" />
                        <span className="text-[12px] font-semibold uppercase tracking-[0.04em]">Severity mix</span>
                      </div>
                      <BreakdownRows rows={severityRows} emptyLabel="No severity counts available." />
                    </div>
                  </div>
                  <div className="mt-5 grid gap-4 lg:grid-cols-3">
                    <div className="space-y-3">
                      <div className="text-[12px] font-semibold uppercase tracking-[0.04em] text-[var(--e-text-primary)]">
                        Theatre families
                      </div>
                      <BreakdownRows
                        rows={Object.entries(breakdowns.theatre_families).map(([label, value]) => ({
                          label: humanizeKey(label),
                          value,
                          tone: 'green' as const,
                        }))}
                        emptyLabel="No theatre-family counts available."
                      />
                    </div>
                    <div className="space-y-3">
                      <div className="text-[12px] font-semibold uppercase tracking-[0.04em] text-[var(--e-text-primary)]">
                        Investigation classes
                      </div>
                      <BreakdownRows
                        rows={Object.entries(breakdowns.investigation_classes).map(([label, value]) => ({
                          label: humanizeKey(label),
                          value,
                          tone: 'purple' as const,
                        }))}
                        emptyLabel="No investigation-class counts available."
                      />
                    </div>
                    <div className="space-y-3">
                      <div className="text-[12px] font-semibold uppercase tracking-[0.04em] text-[var(--e-text-primary)]">
                        Agent archetypes
                      </div>
                      <BreakdownRows
                        rows={Object.entries(breakdowns.agent_archetypes).map(([label, value]) => ({
                          label: humanizeKey(label),
                          value,
                          tone: 'orange' as const,
                        }))}
                        emptyLabel="No agent-archetype counts available."
                      />
                    </div>
                  </div>
                </SectionCard>

                <SectionCard title="Trend window" eyebrow="Timeseries">
                  {theatreTrend.length === 0 &&
                  investigationTrend.length === 0 &&
                  certificateTrend.length === 0 &&
                  paradoxTrend.length === 0 ? (
                    <SparseCard
                      eyebrow="Sparse data"
                      title="Trend data will deepen over time"
                      description="The analytics API is now reading persisted lifecycle timestamps. As more theatres, investigations, and certificates move through the system, these trend windows will become more informative."
                    />
                  ) : (
                    <div className="grid gap-4 lg:grid-cols-2">
                      <div className="space-y-3">
                        <TrendStack
                          title="Lifecycle volume"
                          description="Daily counts from persisted creation and issuance timestamps."
                          rows={[
                            {
                              label: 'Theatres created',
                              points: theatreTrend,
                              tone: 'purple',
                              comparison: platform.comparisons.theatres_created,
                            },
                            {
                              label: 'Investigations created',
                              points: investigationTrend,
                              tone: 'green',
                              comparison: platform.comparisons.investigations_created,
                            },
                            {
                              label: 'Certificates issued',
                              points: certificateTrend,
                              tone: 'orange',
                              comparison: platform.comparisons.certificates_issued,
                            },
                          ]}
                          selectedDate={selectedPlatformBucket}
                          onSelectDate={setSelectedPlatformBucket}
                        />
                      </div>

                      <div className="space-y-3">
                        <TrendStack
                          title="Risk pressure"
                          description="Daily state from persisted paradox and investigation controls."
                          rows={[
                            {
                              label: 'Active paradoxes',
                              points: paradoxTrend,
                              tone: 'red',
                              comparison: riskTrend.comparisons.active_paradoxes,
                            },
                            {
                              label: 'Material drift',
                              points: driftTrend,
                              tone: 'orange',
                              comparison: riskTrend.comparisons.material_drift_events,
                            },
                            {
                              label: 'Review-required certs',
                              points: reviewRequiredTrend,
                              tone: 'purple',
                              comparison: riskTrend.comparisons.review_required_certificates,
                            },
                          ]}
                          selectedDate={selectedRiskBucket}
                          onSelectDate={setSelectedRiskBucket}
                        />
                      </div>
                    </div>
                  )}
                  <div className="mt-5 border-t border-[var(--e-border-secondary)] pt-5">
                    <div className="mb-4">
                      <div className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                        Phase 4
                      </div>
                      <div className="mt-1 text-[13px] font-semibold text-[var(--e-text-primary)]">
                        Event-linked explanations
                      </div>
                      <div className="mt-1 text-[12px] leading-5 text-[var(--e-text-secondary)]">
                        Each explanation comes from a persisted backend record or a live paradox window, not frontend inference.
                      </div>
                      {selectedPlatformBucket || selectedRiskBucket ? (
                        <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-[var(--e-text-muted)]">
                          {selectedPlatformBucket ? (
                            <button
                              type="button"
                              onClick={() => setSelectedPlatformBucket(undefined)}
                              className="rounded-full border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-2.5 py-1 hover:border-[var(--e-purple-300)] hover:text-[var(--e-purple-700)]"
                            >
                              Lifecycle bucket: {selectedPlatformBucket} ×
                            </button>
                          ) : null}
                          {selectedRiskBucket ? (
                            <button
                              type="button"
                              onClick={() => setSelectedRiskBucket(undefined)}
                              className="rounded-full border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-2.5 py-1 hover:border-[var(--e-purple-300)] hover:text-[var(--e-purple-700)]"
                            >
                              Risk bucket: {selectedRiskBucket} ×
                            </button>
                          ) : null}
                        </div>
                      ) : null}
                    </div>
                    <div className="grid gap-4 lg:grid-cols-2">
                      <ExplanationList
                        title="Lifecycle drivers"
                        eyebrow="Platform"
                        items={lifecycleExplanations}
                        emptyLabel="No recent lifecycle records in the current analytics window."
                      />
                      <ExplanationList
                        title="Risk drivers"
                        eyebrow="Pressure"
                        items={riskExplanations}
                        emptyLabel="No recent risk records in the current analytics window."
                      />
                    </div>
                  </div>
                </SectionCard>
              </div>

              <div className="space-y-4">
                <SectionCard title="Current scope" eyebrow="Operator note">
                  <div className="space-y-3 text-[13px] leading-6 text-[var(--e-text-secondary)]">
                    <p>
                      Analytics is now backed by dedicated platform endpoints instead of frontend composition, but it is still a first truthful layer rather than a full quant stack.
                    </p>
                    <p>
                      Historical equity curves and richer portfolio risk history remain deferred until the backend stores snapshot series. The charts shown here come from persisted lifecycle timestamps and live registry counts only.
                    </p>
                  </div>
                </SectionCard>

                <SectionCard title="Current totals" eyebrow="Live now">
                  <div className="space-y-3">
                    <MetricRow label="Active signals" value={platform.current.active_signals} />
                    <MetricRow label="Critical signals" value={platform.current.critical_signals} tone="warning" />
                    <MetricRow label="Convergence cells" value={platform.current.convergence_cells} />
                    <MetricRow label="Ready investigations" value={platform.current.ready_investigations} />
                    <MetricRow label="Completed theatres" value={platform.current.completed_theatres} />
                    <MetricRow label="Issued certificates" value={platform.current.issued_certificates} tone="info" />
                  </div>
                </SectionCard>
              </div>
            </div>
          </>
        ) : (
          <div className="space-y-4">
            <div className="grid gap-4 md:grid-cols-4">
              <AnalyticsKpi
                label="Total Notional"
                value={portfolioHasData ? Math.round(portfolioCurrent.total_notional).toLocaleString() : '—'}
                detail="Current snapshot only"
              />
              <AnalyticsKpi
                label="Unrealised P&L"
                value={portfolioHasData ? Math.round(portfolioCurrent.total_unrealised_pnl).toLocaleString() : '—'}
                detail="Marked from current timeline price"
                tone={
                  portfolioHasData
                    ? portfolioCurrent.total_unrealised_pnl < 0
                      ? 'danger'
                      : portfolioCurrent.total_unrealised_pnl > 0
                        ? 'success'
                        : undefined
                    : undefined
                }
              />
              <AnalyticsKpi
                label="Open Positions"
                value={portfolioHasData ? portfolioCurrent.position_count : '—'}
                detail="Persisted position rows"
              />
              <AnalyticsKpi
                label="At-risk Positions"
                value={portfolioHasData ? portfolioCurrent.at_risk_positions : '—'}
                detail="Paradox or elevated logic gap"
                tone={portfolioHasData && portfolioCurrent.at_risk_positions > 0 ? 'warning' : undefined}
              />
            </div>

            {portfolioError ? (
              <SparseCard eyebrow="Load issue" title="Portfolio analytics unavailable" description={portfolioError} />
            ) : portfolioLoading ? (
              <SparseCard
                eyebrow="Loading"
                title="Checking portfolio analytics"
                description="Querying position exposure and timeline risk state contracts."
              />
            ) : !portfolioHasData ? (
              <SparseCard
                eyebrow="Sparse data"
                title="No portfolio analytics yet"
                description="Portfolio analytics currently use a truthful current snapshot only. Historical equity curves and richer risk trend APIs remain deferred until those contracts ship."
              />
            ) : (
              <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_300px]">
                <SectionCard title="Largest exposures" eyebrow="Portfolio">
                  <div className="space-y-3">
                    {portfolio.top_positions.map((position) => (
                      <div key={position.timeline_id} className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-card)] px-4 py-4">
                        <div className="flex items-center justify-between gap-3">
                          <div className="text-[14px] font-semibold text-[var(--e-text-primary)]">{position.timeline_name}</div>
                          <div
                            className={clsx(
                              'font-mono text-[13px] font-semibold',
                              toneClass(
                                position.unrealised_pnl < 0
                                  ? 'danger'
                                  : position.unrealised_pnl > 0
                                    ? 'success'
                                    : undefined,
                              ),
                            )}
                          >
                            {Math.round(position.unrealised_pnl)}
                          </div>
                        </div>
                        <div className="mt-2 text-[12px] leading-5 text-[var(--e-text-secondary)]">
                          {position.side} · {position.shards_held} shards · entry {position.average_entry_price.toFixed(2)} · current {position.current_price.toFixed(2)}
                        </div>
                      </div>
                    ))}
                  </div>
                </SectionCard>

                <SectionCard title="Current scope" eyebrow="Snapshot">
                  <div className="space-y-3 text-[13px] leading-6 text-[var(--e-text-secondary)]">
                    <p>
                      Portfolio analytics now show a truthful current snapshot derived from persisted positions and current timeline prices.
                    </p>
                    <p>
                      Historical equity curves, rolling comparisons, and richer per-position risk trend remain deferred until the backend stores portfolio snapshots over time.
                    </p>
                  </div>
                </SectionCard>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function MetricRow({
  label,
  value,
  tone,
}: {
  label: string;
  value: string | number;
  tone?: 'warning' | 'info';
}) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
      <div className="text-[12px] font-medium text-[var(--e-text-secondary)]">{label}</div>
      <div className={clsx('font-mono text-[12px] font-semibold tabular-nums', toneClass(tone))}>{value}</div>
    </div>
  );
}
