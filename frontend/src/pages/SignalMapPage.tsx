import { useEffect, useMemo, useState } from 'react';
import { clsx } from 'clsx';
import {
  Activity,
  AlertTriangle,
  CircleDot,
  Radar,
  Search,
  SearchCheck,
  ShieldCheck,
  Sparkles,
  Waypoints,
} from 'lucide-react';
import { Link, useSearchParams } from 'react-router-dom';
import { useSignalMap } from '../hooks/useSignalMap';
import type { WorldMonitorSignal } from '../api/worldMonitor';

type SeverityFilter = 'all' | 'critical' | 'high' | 'moderate' | 'low';
type NodeKind = 'source' | 'category' | 'region' | 'signal';

type GraphNode = {
  id: string;
  label: string;
  kind: NodeKind;
  x: number;
  y: number;
  signal?: WorldMonitorSignal;
};

type GraphEdge = {
  from: string;
  to: string;
  kind: 'belongs' | 'correlates';
};

function humanizeKey(value: string) {
  return value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

function severityRank(severity: string) {
  switch (severity.toUpperCase()) {
    case 'CRITICAL':
      return 4;
    case 'HIGH':
      return 3;
    case 'MODERATE':
      return 2;
    case 'LOW':
      return 1;
    default:
      return 0;
  }
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

function formatTimeAgo(timestamp: string) {
  const diff = Date.now() - new Date(timestamp).getTime();
  const minutes = Math.max(0, Math.floor(diff / 60_000));
  if (minutes < 1) return 'now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
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

function SummaryStat({
  label,
  value,
  accent,
}: {
  label: string;
  value: string | number;
  accent?: 'purple' | 'green' | 'red' | 'muted';
}) {
  return (
    <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-3 shadow-[var(--e-shadow-xs)]">
      <div className="mb-1 flex items-center justify-between gap-3">
        <span className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
          {label}
        </span>
      </div>
      <div
        className={clsx(
          'font-mono text-[26px] font-bold leading-7 tabular-nums',
          accent === 'green'
            ? 'text-[var(--e-green-600)]'
            : accent === 'red'
              ? 'text-[var(--e-red-600)]'
              : accent === 'purple'
                ? 'text-[var(--e-purple-700)]'
                : 'text-[var(--e-text-primary)]',
        )}
      >
        {value}
      </div>
    </div>
  );
}

function SignalBadge({ severity }: { severity: string }) {
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

function nodeStyle(kind: NodeKind, severity?: string) {
  if (kind === 'signal') {
    const tone = severityTone(severity ?? 'low');
    if (tone === 'danger') {
      return { fill: 'var(--e-red-50)', stroke: 'var(--e-red-600)', text: 'var(--e-red-600)' };
    }
    if (tone === 'warning') {
      return { fill: 'color:oklch(0.708_0.136_62_/_0.10)', stroke: 'var(--e-orange-600)', text: 'var(--e-orange-600)' };
    }
    if (tone === 'info') {
      return { fill: 'var(--e-purple-50)', stroke: 'var(--e-purple-700)', text: 'var(--e-purple-700)' };
    }
  }

  if (kind === 'source') return { fill: 'var(--e-bg-sunken)', stroke: 'var(--e-text-muted)', text: 'var(--e-text-secondary)' };
  if (kind === 'category') return { fill: 'var(--e-purple-50)', stroke: 'var(--e-purple-500)', text: 'var(--e-purple-700)' };
  if (kind === 'region') return { fill: 'color:oklch(0.545_0.170_152_/_0.08)', stroke: 'var(--e-green-600)', text: 'var(--e-green-600)' };
  return { fill: 'var(--e-bg-card)', stroke: 'var(--e-border-primary)', text: 'var(--e-text-primary)' };
}

function buildGraph(signals: WorldMonitorSignal[]) {
  const width = 860;
  const height = 520;
  const sourceX = 120;
  const categoryX = 320;
  const signalX = 520;
  const regionX = 740;

  const sourceValues = Array.from(new Set(signals.map((signal) => signal.source)));
  const categoryValues = Array.from(new Set(signals.map((signal) => signal.category)));
  const regionValues = Array.from(new Set(signals.map((signal) => signal.region)));

  const sourceSpacing = height / (sourceValues.length + 1 || 1);
  const categorySpacing = height / (categoryValues.length + 1 || 1);
  const regionSpacing = height / (regionValues.length + 1 || 1);
  const signalSpacing = height / (signals.length + 1 || 1);

  const nodes = new Map<string, GraphNode>();
  const edges: GraphEdge[] = [];

  sourceValues.forEach((source, index) => {
    nodes.set(`source:${source}`, {
      id: `source:${source}`,
      label: humanizeKey(source),
      kind: 'source',
      x: sourceX,
      y: sourceSpacing * (index + 1),
    });
  });

  categoryValues.forEach((category, index) => {
    nodes.set(`category:${category}`, {
      id: `category:${category}`,
      label: humanizeKey(category),
      kind: 'category',
      x: categoryX,
      y: categorySpacing * (index + 1),
    });
  });

  regionValues.forEach((region, index) => {
    nodes.set(`region:${region}`, {
      id: `region:${region}`,
      label: humanizeKey(region),
      kind: 'region',
      x: regionX,
      y: regionSpacing * (index + 1),
    });
  });

  signals.forEach((signal, index) => {
    nodes.set(`signal:${signal.id}`, {
      id: `signal:${signal.id}`,
      label: signal.title,
      kind: 'signal',
      x: signalX,
      y: signalSpacing * (index + 1),
      signal,
    });

    edges.push({ from: `source:${signal.source}`, to: `signal:${signal.id}`, kind: 'belongs' });
    edges.push({ from: `category:${signal.category}`, to: `signal:${signal.id}`, kind: 'belongs' });
    edges.push({ from: `signal:${signal.id}`, to: `region:${signal.region}`, kind: 'belongs' });
  });

  const signalIds = new Set(signals.map((signal) => signal.id));
  signals.forEach((signal) => {
    signal.correlated_signals.forEach((correlatedId) => {
      if (signalIds.has(correlatedId) && signal.id < correlatedId) {
        edges.push({ from: `signal:${signal.id}`, to: `signal:${correlatedId}`, kind: 'correlates' });
      }
    });
  });

  return {
    width,
    height,
    nodes: Array.from(nodes.values()),
    edges,
  };
}

function buildCreateInvestigationLink(signal: WorldMonitorSignal) {
  const params = new URLSearchParams();
  params.set('signal_id', signal.id);
  params.set('signal_title', signal.title);
  params.set('signal_category', signal.category);
  params.set('signal_source', signal.source);
  params.set('signal_region', signal.region);
  params.set('source_surface', 'signal_map');
  if (signal.theatre_ids?.[0]) {
    params.set('theatre_id', signal.theatre_ids[0]);
  }
  return `/investigation/create?${params.toString()}`;
}

export function SignalMapPage() {
  const [searchParams] = useSearchParams();
  const { signals, heatmap, categoryCounts, sourceCounts, updatedAt, isLoading, error, isSparse, isQuiet } =
    useSignalMap();
  const initialQuery = searchParams.get('q') ?? '';
  const initialSignalId = searchParams.get('signal');
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [sourceFilter, setSourceFilter] = useState<string>('all');
  const [search, setSearch] = useState(initialQuery);
  const [selectedSignalId, setSelectedSignalId] = useState<string | null>(initialSignalId);
  const [showLegend, setShowLegend] = useState(false);

  const categoryOptions = useMemo(() => ['all', ...Object.keys(categoryCounts).sort()], [categoryCounts]);
  const sourceOptions = useMemo(() => ['all', ...Object.keys(sourceCounts).sort()], [sourceCounts]);

  const filteredSignals = useMemo(() => {
    const query = search.trim().toLowerCase();
    return signals.filter((signal) => {
      if (severityFilter !== 'all' && signal.severity.toLowerCase() !== severityFilter) return false;
      if (categoryFilter !== 'all' && signal.category !== categoryFilter) return false;
      if (sourceFilter !== 'all' && signal.source !== sourceFilter) return false;
      if (!query) return true;
      return [signal.title, signal.description, signal.source, signal.category, signal.region]
        .some((value) => value.toLowerCase().includes(query));
    });
  }, [categoryFilter, search, severityFilter, signals, sourceFilter]);

  const graphSignals = useMemo(() => filteredSignals.slice(0, 18), [filteredSignals]);
  const graph = useMemo(() => buildGraph(graphSignals), [graphSignals]);

  const selectedSignal =
    filteredSignals.find((signal) => signal.id === selectedSignalId) ??
    graphSignals[0] ??
    null;

  useEffect(() => {
    const query = searchParams.get('q') ?? '';
    const signalId = searchParams.get('signal');

    setSearch((current) => (current === query ? current : query));
    setSelectedSignalId((current) => (current === signalId ? current : signalId));
  }, [searchParams]);

  const criticalSignals = filteredSignals.filter((signal) => severityRank(signal.severity) >= 3).length;
  const contradictionCount = filteredSignals.filter((signal) => signal.correlated_signals.length > 0).length;
  const linkedInvestigationCount = new Set(
    filteredSignals.map((signal) => signal.investigation_id).filter((value): value is string => Boolean(value)),
  ).size;
  const linkedTheatreCount = new Set(
    filteredSignals.flatMap((signal) => signal.theatre_ids ?? []),
  ).size;
  const correlatedEdgeCount = filteredSignals.reduce((sum, signal) => sum + signal.correlated_signals.length, 0);

  if (error) {
    return (
      <div className="p-6">
        <div className="mx-auto max-w-4xl rounded-lg border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-bg-card)] px-8 py-14 text-center shadow-[var(--e-shadow-xs)]">
          <AlertTriangle className="mx-auto mb-4 h-10 w-10 text-[var(--e-red-600)]" />
          <h1 className="mb-2 text-[22px] font-semibold text-[var(--e-text-primary)]">Failed to load Signal Map</h1>
          <p className="text-[14px] text-[var(--e-text-secondary)]">{error.message}</p>
        </div>
      </div>
    );
  }

  if (isQuiet && !isLoading) {
    return (
      <div className="p-6">
        <div className="mx-auto max-w-6xl space-y-6">
          <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-8 py-14 text-center shadow-[var(--e-shadow-xs)]">
            <Radar className="mx-auto mb-4 h-10 w-10 text-[var(--e-purple-700)]" />
            <h1 className="mb-2 text-[26px] font-semibold tracking-[-0.02em] text-[var(--e-text-primary)]">Signal Map</h1>
            <p className="mx-auto max-w-2xl text-[14px] leading-6 text-[var(--e-text-secondary)]">
              No active OSINT signals are currently available. The signal network will populate as World Monitor sources produce live events.
            </p>
            <div className="mt-6 flex justify-center gap-3">
              <Link
                to="/world-monitor/live"
                className="inline-flex h-10 items-center gap-2 rounded-md border border-[var(--e-purple-500)] bg-[var(--e-purple-500)] px-4 text-[13px] font-semibold text-white no-underline transition hover:bg-[var(--e-purple-400)]"
              >
                <Sparkles className="h-4 w-4" />
                Open Global Map
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mx-auto max-w-[1600px] space-y-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="mb-2 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              <span>Intelligence</span>
              <span>/</span>
              <span className="text-[var(--e-text-secondary)]">Signal Map</span>
            </div>
            <h1 className="text-[30px] font-semibold tracking-[-0.02em] text-[var(--e-text-primary)]">Signal Map</h1>
            <p className="mt-2 max-w-4xl text-[14px] leading-6 text-[var(--e-text-secondary)]">
              Raw OSINT relationship surface for active signals, categories, source families, and convergence cells. Keep the graph foundation visible, then jump into the immersive globe when you need geospatial context.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <label className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--e-text-muted)]" />
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search signals, sources, clusters..."
                className="h-10 w-[260px] rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] pl-10 pr-3 text-[13px] text-[var(--e-text-primary)] outline-none transition placeholder:text-[var(--e-text-muted)] focus:border-[var(--e-purple-500)] focus:ring-2 focus:ring-[color:oklch(0.530_0.230_295_/_0.12)]"
              />
            </label>
            <Link
              to="/world-monitor/live"
              className="inline-flex h-10 items-center gap-2 rounded-md border border-[var(--e-purple-500)] bg-[var(--e-purple-500)] px-4 text-[13px] font-semibold text-white no-underline transition hover:bg-[var(--e-purple-400)]"
            >
              <Sparkles className="h-4 w-4" />
              Open Global Map
            </Link>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">
          <SummaryStat label="Clusters" value={heatmap.length} accent="purple" />
          <SummaryStat label="Signals" value={filteredSignals.length} />
          <SummaryStat label="Contradictions" value={contradictionCount} accent={contradictionCount > 0 ? 'red' : 'muted'} />
          <SummaryStat label="Investigations" value={linkedInvestigationCount} accent={linkedInvestigationCount > 0 ? 'purple' : 'muted'} />
          <SummaryStat label="Theatres" value={linkedTheatreCount} accent={linkedTheatreCount > 0 ? 'green' : 'muted'} />
          <SummaryStat label="Edges" value={`+${correlatedEdgeCount}`} accent="muted" />
        </div>

        {criticalSignals >= 4 ? (
          <div className="flex items-center gap-3 rounded-lg border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] px-5 py-3 text-[13px]">
            <AlertTriangle className="h-4 w-4 shrink-0 text-[var(--e-red-600)]" />
            <span className="font-semibold text-[var(--e-red-600)]">Escalated signal network</span>
            <span className="text-[var(--e-text-secondary)]">
              Contradictory or high-severity live signals are stacking in the current roster.
            </span>
          </div>
        ) : null}

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
          <div className="space-y-4">
            <section className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
              <div className="flex items-center justify-between gap-4 border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-3">
                <div>
                  <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Graph</div>
                  <h2 className="text-[13px] font-semibold text-[var(--e-text-primary)]">Signal Network</h2>
                </div>
                <div className="flex items-center gap-3">
                  <span className="font-mono text-[11px] text-[var(--e-text-muted)]">
                    {filteredSignals.length} visible · updated {updatedAt ? formatTimeAgo(updatedAt) : 'recently'}
                  </span>
                  <button
                    type="button"
                    onClick={() => setShowLegend((current) => !current)}
                    className="inline-flex h-8 items-center rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 text-[12px] font-semibold text-[var(--e-text-secondary)] transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]"
                  >
                    {showLegend ? 'Hide Legend' : 'Legend'}
                  </button>
                </div>
              </div>
              {showLegend ? (
                <div className="flex flex-wrap gap-6 border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-card)] px-5 py-4 text-[12px] text-[var(--e-text-secondary)]">
                  <div className="space-y-2">
                    <div className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Nodes</div>
                    <div className="flex items-center gap-2"><span className="h-3 w-3 rounded-full border border-[var(--e-text-muted)] bg-[var(--e-bg-sunken)]" /> Source</div>
                    <div className="flex items-center gap-2"><span className="h-3 w-3 rounded-full border border-[var(--e-purple-500)] bg-[var(--e-purple-50)]" /> Category</div>
                    <div className="flex items-center gap-2"><span className="h-3 w-3 rounded-full border border-[var(--e-red-600)] bg-[var(--e-red-50)]" /> Escalated Signal</div>
                    <div className="flex items-center gap-2"><span className="h-3 w-3 rounded-full border border-[var(--e-green-600)] bg-[color:oklch(0.545_0.170_152_/_0.08)]" /> Region</div>
                  </div>
                  <div className="space-y-2">
                    <div className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Edges</div>
                    <div className="flex items-center gap-2"><span className="h-px w-8 bg-[var(--e-border-primary)]" /> Belongs</div>
                    <div className="flex items-center gap-2"><span className="h-px w-8 border-t border-dashed border-[var(--e-red-600)]" /> Correlates</div>
                  </div>
                </div>
              ) : null}
              <div className="px-5 py-5">
                {isSparse ? (
                  <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-6 py-10 text-center">
                    <Waypoints className="mx-auto mb-3 h-6 w-6 text-[var(--e-purple-700)]" />
                    <div className="text-[15px] font-semibold text-[var(--e-text-primary)]">Sparse network</div>
                    <div className="mt-2 text-[13px] leading-6 text-[var(--e-text-secondary)]">
                      Only {filteredSignals.length} signal{filteredSignals.length === 1 ? '' : 's'} match the current filters. The graph becomes more legible as more live events accumulate.
                    </div>
                  </div>
                ) : (
                  <div className="overflow-hidden rounded-xl border border-[var(--e-border-secondary)] bg-[linear-gradient(180deg,var(--e-bg-card),var(--e-bg-sunken))]">
                    <svg viewBox={`0 0 ${graph.width} ${graph.height}`} className="h-[540px] w-full">
                      {graph.edges.map((edge, index) => {
                        const from = graph.nodes.find((node) => node.id === edge.from);
                        const to = graph.nodes.find((node) => node.id === edge.to);
                        if (!from || !to) return null;
                        return (
                          <line
                            key={`${edge.from}-${edge.to}-${index}`}
                            x1={from.x}
                            y1={from.y}
                            x2={to.x}
                            y2={to.y}
                            stroke={edge.kind === 'correlates' ? 'var(--e-red-600)' : 'var(--e-border-primary)'}
                            strokeWidth={edge.kind === 'correlates' ? 1.5 : 1}
                            strokeDasharray={edge.kind === 'correlates' ? '5 4' : undefined}
                            opacity={0.65}
                          />
                        );
                      })}

                      {graph.nodes.map((node) => {
                        const style = nodeStyle(node.kind, node.signal?.severity);
                        const isSelected = node.signal?.id === selectedSignal?.id;
                        const width = node.kind === 'signal' ? 120 : 88;
                        const height = node.kind === 'signal' ? 32 : 28;
                        return (
                          <g
                            key={node.id}
                            transform={`translate(${node.x}, ${node.y})`}
                            className={node.signal ? 'cursor-pointer' : undefined}
                            onClick={() => {
                              if (node.signal) {
                                setSelectedSignalId(node.signal.id);
                              }
                            }}
                          >
                            <rect
                              x={-width / 2}
                              y={-height / 2}
                              width={width}
                              height={height}
                              rx={node.kind === 'signal' ? 10 : 14}
                              fill={style.fill}
                              stroke={isSelected ? 'var(--e-purple-500)' : style.stroke}
                              strokeWidth={isSelected ? 2.5 : 1.5}
                            />
                            <text
                              textAnchor="middle"
                              dominantBaseline="central"
                              fill={style.text}
                              fontSize={node.kind === 'signal' ? 10 : 10}
                              fontWeight={node.kind === 'signal' ? 600 : 700}
                            >
                              {node.kind === 'signal'
                                ? node.label.length > 22
                                  ? `${node.label.slice(0, 22)}…`
                                  : node.label
                                : node.label.length > 16
                                  ? `${node.label.slice(0, 16)}…`
                                  : node.label}
                            </text>
                          </g>
                        );
                      })}
                    </svg>
                  </div>
                )}
              </div>
            </section>
          </div>

          <div className="space-y-4">
            <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
              <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-3">
                <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Detail</div>
                <h2 className="text-[13px] font-semibold text-[var(--e-text-primary)]">Signal Node</h2>
              </div>
              <div className="px-5 py-5">
                {selectedSignal ? (
                  <div className="space-y-4">
                    <div>
                      <div className="mb-2 flex flex-wrap items-center gap-2">
                        <SignalBadge severity={selectedSignal.severity} />
                        <span className="rounded-full bg-[var(--e-bg-sunken)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-text-muted)]">
                          {humanizeKey(selectedSignal.source)}
                        </span>
                      </div>
                      <h3 className="text-[18px] font-semibold leading-6 text-[var(--e-text-primary)]">{selectedSignal.title}</h3>
                      <p className="mt-2 text-[13px] leading-6 text-[var(--e-text-secondary)]">{selectedSignal.description}</p>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
                        <div className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Region</div>
                        <div className="mt-1 text-[13px] font-semibold text-[var(--e-text-primary)]">{humanizeKey(selectedSignal.region)}</div>
                      </div>
                      <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
                        <div className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Category</div>
                        <div className="mt-1 text-[13px] font-semibold text-[var(--e-text-primary)]">{humanizeKey(selectedSignal.category)}</div>
                      </div>
                      <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
                        <div className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Confidence</div>
                        <div className="mt-1 font-mono text-[14px] font-semibold text-[var(--e-text-primary)]">
                          {Math.round(selectedSignal.confidence * 100)}%
                        </div>
                      </div>
                      <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
                        <div className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Observed</div>
                        <div className="mt-1 font-mono text-[14px] font-semibold text-[var(--e-text-primary)]">
                          {formatTimeAgo(selectedSignal.timestamp)}
                        </div>
                      </div>
                    </div>

                    <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-4">
                      <div className="mb-2 flex items-center gap-2 text-[var(--e-text-primary)]">
                        <CircleDot className="h-4 w-4 text-[var(--e-purple-700)]" />
                        <span className="text-[12px] font-semibold uppercase tracking-[0.04em]">Correlations</span>
                      </div>
                      {selectedSignal.correlated_signals.length === 0 ? (
                        <div className="text-[12px] text-[var(--e-text-muted)]">No linked signals in the current live roster.</div>
                      ) : (
                        <div className="flex flex-wrap gap-2">
                          {selectedSignal.correlated_signals.map((id) => (
                            <span
                              key={id}
                              className="rounded-full bg-[var(--e-bg-card)] px-2 py-1 font-mono text-[10px] text-[var(--e-text-muted)]"
                            >
                              {id}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-4">
                      <div className="mb-2 flex items-center gap-2 text-[var(--e-text-primary)]">
                        <SearchCheck className="h-4 w-4 text-[var(--e-purple-700)]" />
                        <span className="text-[12px] font-semibold uppercase tracking-[0.04em]">Evidence chain</span>
                      </div>
                      <div className="space-y-2 text-[12px] leading-5 text-[var(--e-text-secondary)]">
                        <div>
                          <span className="font-semibold text-[var(--e-text-primary)]">Link type:</span>{' '}
                          {selectedSignal.link_confidence ?? 'context only'}
                          {selectedSignal.link_reason ? ` · ${humanizeKey(selectedSignal.link_reason)}` : ''}
                        </div>
                        {selectedSignal.theatre_ids && selectedSignal.theatre_ids.length > 0 ? (
                          <div>
                            <span className="font-semibold text-[var(--e-text-primary)]">Nearby theatres:</span>{' '}
                            {selectedSignal.theatre_ids.join(', ')}
                          </div>
                        ) : null}
                      </div>
                      <div className="mt-4 flex flex-wrap gap-2">
                        {selectedSignal.investigation_id ? (
                          <Link
                            to={`/investigation?investigation=${encodeURIComponent(selectedSignal.investigation_id)}`}
                            className="inline-flex h-9 items-center gap-2 rounded-md border border-[var(--e-purple-500)] bg-[var(--e-purple-500)] px-3 text-[12px] font-semibold text-white no-underline transition hover:bg-[var(--e-purple-400)]"
                          >
                            <SearchCheck className="h-4 w-4" />
                            Open Investigation
                          </Link>
                        ) : (
                          <Link
                            to={buildCreateInvestigationLink(selectedSignal)}
                            className="inline-flex h-9 items-center gap-2 rounded-md border border-[var(--e-purple-500)] bg-[var(--e-purple-500)] px-3 text-[12px] font-semibold text-white no-underline transition hover:bg-[var(--e-purple-400)]"
                          >
                            <SearchCheck className="h-4 w-4" />
                            Create Investigation
                          </Link>
                        )}
                        {selectedSignal.certificate_id ? (
                          <Link
                            to={`/verify?certificate=${encodeURIComponent(selectedSignal.certificate_id)}`}
                            className="inline-flex h-9 items-center gap-2 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 text-[12px] font-semibold text-[var(--e-green-700)] no-underline transition hover:bg-[var(--e-bg-hover)]"
                          >
                            <ShieldCheck className="h-4 w-4" />
                            Open Certificate
                          </Link>
                        ) : null}
                      </div>
                    </div>

                    <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-4">
                      <div className="mb-2 flex items-center gap-2 text-[var(--e-text-primary)]">
                        <Activity className="h-4 w-4 text-[var(--e-green-600)]" />
                        <span className="text-[12px] font-semibold uppercase tracking-[0.04em]">Flow Note</span>
                      </div>
                      <p className="text-[12px] leading-6 text-[var(--e-text-secondary)]">
                        Signal Map shows the raw OSINT topology. For geospatial monitoring and convergence overlays, use the live World Monitor globe.
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-8 text-center text-[13px] text-[var(--e-text-muted)]">
                    Select a signal to inspect its source, category, region, and correlation chain.
                  </div>
                )}
              </div>
            </section>
          </div>
        </div>

        <div className="grid gap-6 xl:grid-cols-[300px_minmax(0,1fr)_340px]">
          <div className="space-y-4">
            <section className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
              <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-3">
                <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Filters</div>
                <h2 className="text-[13px] font-semibold text-[var(--e-text-primary)]">Signal Layers</h2>
              </div>
              <div className="space-y-5 px-5 py-5">
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
                        label={option === 'all' ? 'all categories' : `${humanizeKey(option)} (${categoryCounts[option] ?? 0})`}
                        onClick={() => setCategoryFilter(option)}
                      />
                    ))}
                  </div>
                </div>

                <div>
                  <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Source</div>
                  <div className="flex max-h-[180px] flex-wrap gap-2 overflow-auto">
                    {sourceOptions.map((option) => (
                      <FilterChip
                        key={option}
                        active={sourceFilter === option}
                        label={option === 'all' ? 'all sources' : `${humanizeKey(option)} (${sourceCounts[option] ?? 0})`}
                        onClick={() => setSourceFilter(option)}
                      />
                    ))}
                  </div>
                </div>
              </div>
            </section>
          </div>

          <div className="space-y-4">
            <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
              <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-3">
                <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Feed</div>
                <h2 className="text-[13px] font-semibold text-[var(--e-text-primary)]">Visible Signals</h2>
              </div>
              <div className="space-y-3 px-5 py-5">
                {filteredSignals.length === 0 ? (
                  <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-8 text-center text-[13px] text-[var(--e-text-muted)]">
                    No signals match the current filters.
                  </div>
                ) : (
                  filteredSignals.slice(0, 8).map((signal) => (
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
                        <SignalBadge severity={signal.severity} />
                        <span className="rounded-full bg-[var(--e-bg-card)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-text-muted)]">
                          {humanizeKey(signal.category)}
                        </span>
                        <span className="font-mono text-[11px] text-[var(--e-text-muted)]">{humanizeKey(signal.region)}</span>
                      </div>
                      <div className="mt-2 text-[13px] font-semibold text-[var(--e-text-primary)]">{signal.title}</div>
                      <div className="mt-1 text-[12px] leading-5 text-[var(--e-text-secondary)]">{signal.description}</div>
                    </button>
                  ))
                )}
              </div>
            </section>
          </div>

          <div className="space-y-4">
            <section className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
              <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-3">
                <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Hot Cells</div>
                <h2 className="text-[13px] font-semibold text-[var(--e-text-primary)]">Convergence</h2>
              </div>
              <div className="space-y-3 px-5 py-5">
                {heatmap.length === 0 ? (
                  <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-6 text-center text-[13px] text-[var(--e-text-muted)]">
                    No convergence cells yet.
                  </div>
                ) : (
                  heatmap.slice(0, 6).map((cell, index) => (
                    <div key={`${cell.lat}-${cell.lon}-${index}`} className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
                      <div className="flex items-center justify-between gap-3">
                        <div className="text-[12px] font-semibold text-[var(--e-text-primary)]">
                          Cell {cell.lat.toFixed(0)}, {cell.lon.toFixed(0)}
                        </div>
                        <span className="font-mono text-[11px] text-[var(--e-text-muted)]">{cell.events} events</span>
                      </div>
                      <div className="mt-2 text-[11px] text-[var(--e-text-secondary)]">
                        Density {cell.density.toFixed(1)} · {cell.sources.length} sources · {cell.theatres.length} theatre
                        {cell.theatres.length === 1 ? '' : 's'}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}
