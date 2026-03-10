import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  ArrowUpRight,
  Briefcase,
  Download,
  Filter,
  Loader2,
  Search,
  ShieldCheck,
} from 'lucide-react';
import { usePortfolioSummary, usePositions } from '../hooks/usePortfolio';

type PositionView = 'active' | 'all' | 'settled';

function formatCurrency(value: number) {
  return `$${value.toLocaleString(undefined, { maximumFractionDigits: 2, minimumFractionDigits: 2 })}`;
}

function formatSignedCurrency(value: number) {
  const sign = value >= 0 ? '+' : '-';
  return `${sign}$${Math.abs(value).toLocaleString(undefined, {
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  })}`;
}

function formatPrice(value: number) {
  return `${Math.round(value * 100)}c`;
}

function metricTone(value: number) {
  if (value > 0) return 'text-[var(--e-green-600)]';
  if (value < 0) return 'text-[var(--e-red-600)]';
  return 'text-[var(--e-text-primary)]';
}

function exportRowsAsCsv(rows: Array<Record<string, string | number>>) {
  const headers = Object.keys(rows[0] ?? {});
  const csv = [
    headers.join(','),
    ...rows.map((row) =>
      headers
        .map((header) => {
          const value = String(row[header] ?? '');
          return `"${value.replace(/"/g, '""')}"`;
        })
        .join(','),
    ),
  ].join('\n');

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'echelon_positions.csv';
  link.click();
  URL.revokeObjectURL(url);
}

function KpiCard({
  label,
  value,
  windowLabel,
  sub,
  tone,
  accent,
}: {
  label: string;
  value: string;
  windowLabel: string;
  sub?: string;
  tone?: string;
  accent?: 'warning' | 'success';
}) {
  return (
    <div
      className={`rounded-xl border px-4 py-4 shadow-[var(--e-shadow-xs)] ${
        accent === 'warning'
          ? 'border-[var(--e-amber-200)] bg-[var(--e-amber-50)]'
          : 'border-[var(--e-border-primary)] bg-[var(--e-bg-card)]'
      }`}
    >
      <div className="mb-2 flex items-center justify-between gap-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-[var(--e-text-muted)]">
        <span>{label}</span>
        <span>{windowLabel}</span>
      </div>
      <div className={`font-mono text-[28px] font-bold leading-none tabular-nums ${tone ?? 'text-[var(--e-text-primary)]'}`}>
        {value}
      </div>
      {sub ? <div className="mt-2 text-[12px] text-[var(--e-text-secondary)]">{sub}</div> : null}
    </div>
  );
}

function RiskChip({ label, tone }: { label: string; tone: 'paradox' | 'soon' | 'nominal' }) {
  const className =
    tone === 'paradox'
      ? 'border-[var(--e-red-200)] bg-[var(--e-red-50)] text-[var(--e-red-600)]'
      : tone === 'soon'
        ? 'border-[var(--e-amber-200)] bg-[var(--e-amber-50)] text-[var(--e-amber-700)]'
        : 'border-[var(--e-green-200)] bg-[var(--e-green-50)] text-[var(--e-green-700)]';

  return (
    <span className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] ${className}`}>
      {label}
    </span>
  );
}

export function PortfolioPage() {
  const navigate = useNavigate();
  const { positions, totals, isLoading, error } = usePositions();
  const { summary } = usePortfolioSummary();
  const [view, setView] = useState<PositionView>('active');

  const activeCount = positions.length;
  const settledCount = 0;
  const allCount = activeCount + settledCount;
  const atRiskCount = positions.filter((position) => position.has_active_paradox || (position.hours_until_reaper ?? Infinity) <= 168).length;

  const rows = useMemo(() => {
    const mapped = positions.map((position) => ({
      ...position,
      riskRank: position.has_active_paradox ? 0 : (position.hours_until_reaper ?? Infinity) <= 168 ? 1 : 2,
    }));
    return mapped.sort((a, b) => a.riskRank - b.riskRank || b.unrealised_pnl_usd - a.unrealised_pnl_usd);
  }, [positions]);

  const filteredRows = useMemo(() => {
    if (view === 'settled') return [];
    return rows;
  }, [rows, view]);

  const exportCurrentView = () => {
    if (filteredRows.length === 0) return;
    exportRowsAsCsv(
      filteredRows.map((position) => ({
        theatre: position.timeline_name,
        side: position.side,
        entry_price: formatPrice(position.average_entry_price),
        current_price: formatPrice(position.current_price),
        quantity: position.shards_held,
        pnl_usd: position.unrealised_pnl_usd,
        stability: Math.round(position.timeline_stability),
      })),
    );
  };

  if (error) {
    return (
      <div className="p-6">
        <div className="mx-auto max-w-7xl">
          <section className="rounded-xl border border-[var(--e-red-200)] bg-[var(--e-red-50)] px-5 py-4 text-[13px] text-[var(--e-red-600)] shadow-[var(--e-shadow-xs)]">
            Failed to load positions. Check that the positions and portfolio summary services are available.
          </section>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mx-auto max-w-7xl space-y-5">
        <section className="flex items-start justify-between gap-4">
          <div>
            <div className="mb-2 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-[var(--e-text-muted)]">
              <span>Portfolio</span>
              <span className="text-[var(--e-text-muted)]/60">/</span>
              <span>Positions</span>
            </div>
            <h1 className="text-[42px] font-semibold leading-none tracking-[-0.03em] text-[var(--e-text-primary)]">Positions</h1>
          </div>
          <button
            type="button"
            onClick={exportCurrentView}
            disabled={filteredRows.length === 0}
            className="inline-flex items-center gap-2 rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-2.5 text-[13px] font-semibold text-[var(--e-text-secondary)] shadow-[var(--e-shadow-xs)] transition hover:text-[var(--e-text-primary)] disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Download className="h-4 w-4" />
            Export
          </button>
        </section>

        <div className="flex flex-wrap gap-2">
          {([
            ['active', 'Active', activeCount],
            ['all', 'All', allCount],
            ['settled', 'Settled', settledCount],
          ] as const).map(([key, label, count]) => (
            <button
              key={key}
              type="button"
              onClick={() => setView(key)}
              className={`inline-flex items-center gap-2 rounded-xl border px-4 py-2 text-[13px] font-semibold transition ${
                view === key
                  ? 'border-[var(--e-purple-300)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)]'
                  : 'border-[var(--e-border-primary)] bg-[var(--e-bg-card)] text-[var(--e-text-secondary)] hover:text-[var(--e-text-primary)]'
              }`}
            >
              {label}
              <span className="rounded-full bg-[var(--e-bg-sunken)] px-2 py-0.5 font-mono text-[11px] text-[var(--e-text-muted)]">
                {count}
              </span>
            </button>
          ))}
        </div>

        {atRiskCount > 0 ? (
          <section className="flex items-center gap-3 rounded-xl border border-[var(--e-amber-200)] bg-[var(--e-amber-50)] px-5 py-4 text-[14px] text-[var(--e-amber-800)] shadow-[var(--e-shadow-xs)]">
            <AlertTriangle className="h-5 w-5 shrink-0" />
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold">Attention</span>
              <span>{atRiskCount} position{atRiskCount === 1 ? '' : 's'} flagged for paradox or expiry pressure.</span>
            </div>
          </section>
        ) : activeCount > 0 ? (
          <section className="flex items-center gap-3 rounded-xl border border-[var(--e-green-200)] bg-[var(--e-green-50)] px-5 py-4 text-[14px] text-[var(--e-green-800)] shadow-[var(--e-shadow-xs)]">
            <ShieldCheck className="h-5 w-5 shrink-0" />
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold">All Clear</span>
              <span>All positions nominal. No paradox or reaper risk currently flagged.</span>
            </div>
          </section>
        ) : null}

        <section className="grid gap-4 xl:grid-cols-6">
          <KpiCard label="Portfolio Value" windowLabel="total" value={isLoading ? '—' : formatCurrency(summary?.total_value_usd ?? 0)} />
          <KpiCard
            label="Unrealised P/L"
            windowLabel="open"
            value={isLoading ? '—' : formatSignedCurrency(summary?.total_unrealised_pnl_usd ?? 0)}
            tone={metricTone(summary?.total_unrealised_pnl_usd ?? 0)}
            sub={summary ? `${summary.total_unrealised_pnl_percent.toFixed(1)}%` : undefined}
          />
          <KpiCard label="Open Positions" windowLabel="active" value={isLoading ? '—' : String(activeCount)} sub={summary ? `across ${summary.timelines_at_risk + Math.max(activeCount - summary.timelines_at_risk, 0)} signals` : undefined} />
          <KpiCard label="Settled" windowLabel="30d" value={isLoading ? '—' : String(settledCount)} />
          <KpiCard label="Win Rate" windowLabel="all time" value={isLoading ? '—' : activeCount > 0 ? `${totals.winRate.toFixed(0)}%` : '—'} />
          <KpiCard
            label="Exposure at Risk"
            windowLabel="flagged"
            value={isLoading ? '—' : formatCurrency(positions.filter((position) => position.has_active_paradox || (position.hours_until_reaper ?? Infinity) <= 168).reduce((sum, position) => sum + position.shards_held * position.current_price, 0))}
            accent={atRiskCount > 0 ? 'warning' : 'success'}
            sub={atRiskCount > 0 ? `${atRiskCount} position${atRiskCount === 1 ? '' : 's'} flagged` : 'No exposure flagged'}
          />
        </section>

        <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
          <section className="overflow-hidden rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-4">
              <div className="flex flex-wrap items-center gap-3">
                <div className="relative">
                  <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--e-text-muted)]" />
                  <input
                    type="text"
                    readOnly
                    value=""
                    placeholder="Search positions..."
                    className="w-[220px] rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] py-2 pl-9 pr-3 text-[13px] text-[var(--e-text-secondary)] placeholder:text-[var(--e-text-muted)]"
                  />
                </div>
                <div className="rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 py-2 text-[13px] text-[var(--e-text-muted)]">
                  All Types
                </div>
                <div className="rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 py-2 text-[13px] text-[var(--e-text-muted)]">
                  {atRiskCount > 0 ? 'At Risk + Nominal' : 'All Risk'}
                </div>
              </div>
              <div className="text-[12px] text-[var(--e-text-muted)]">
                {view === 'settled' ? '0 settled' : `${filteredRows.length} active · ${settledCount} settled`}
              </div>
            </div>

            {isLoading ? (
              <div className="flex items-center justify-center gap-2 px-5 py-14 text-[13px] text-[var(--e-text-muted)]">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading positions...
              </div>
            ) : filteredRows.length === 0 ? (
              <div className="flex min-h-[360px] flex-col items-center justify-center px-8 py-14 text-center">
                <div className="mb-5 rounded-2xl border border-[var(--e-border-primary)] bg-[var(--e-bg-sunken)] p-5 text-[var(--e-text-muted)]">
                  <Briefcase className="h-8 w-8" />
                </div>
                <div className="text-[32px] font-semibold tracking-[-0.02em] text-[var(--e-text-primary)]">
                  {view === 'settled' ? 'No settled positions yet' : 'No positions yet'}
                </div>
                <div className="mt-3 max-w-xl text-[17px] leading-8 text-[var(--e-text-secondary)]">
                  {view === 'settled'
                    ? 'Settled outcomes will appear here once your theatres resolve and produce position history.'
                    : 'Open a position in any theatre to start building your portfolio. Active and settled positions will appear here.'}
                </div>
                <button
                  type="button"
                  onClick={() => navigate('/theatres')}
                  className="mt-8 inline-flex items-center gap-2 rounded-xl bg-[var(--e-purple-600)] px-5 py-3 text-[14px] font-semibold text-white shadow-[var(--e-shadow-sm)] transition hover:bg-[var(--e-purple-700)]"
                >
                  Browse Theatres
                </button>
              </div>
            ) : (
              <div className="overflow-x-auto px-5 py-4">
                <table className="min-w-full border-collapse">
                  <thead>
                    <tr className="border-b border-[var(--e-border-secondary)] text-left text-[11px] font-semibold uppercase tracking-[0.08em] text-[var(--e-text-muted)]">
                      <th className="pb-3 pr-4">Theatre</th>
                      <th className="pb-3 pr-4">Side</th>
                      <th className="pb-3 pr-4">Entry</th>
                      <th className="pb-3 pr-4">Current</th>
                      <th className="pb-3 pr-4 text-right">Qty</th>
                      <th className="pb-3 pr-4 text-right">P/L</th>
                      <th className="pb-3 pr-4">Risk</th>
                      <th className="pb-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredRows.map((position) => {
                      const isParadox = position.has_active_paradox;
                      const isExpiring = !isParadox && (position.hours_until_reaper ?? Infinity) <= 168;
                      return (
                        <tr
                          key={`${position.timeline_id}-${position.side}`}
                          className={`border-b border-[var(--e-border-secondary)]/70 text-[13px] ${
                            isParadox
                              ? 'bg-[var(--e-red-50)]/50'
                              : isExpiring
                                ? 'bg-[var(--e-amber-50)]/40'
                                : ''
                          }`}
                        >
                          <td className="py-4 pr-4">
                            <div className="font-semibold text-[var(--e-text-primary)]">{position.timeline_name}</div>
                            <div className="mt-1 text-[11px] text-[var(--e-text-muted)]">
                              {position.is_founder ? 'Founder position' : 'Active market'}
                            </div>
                          </td>
                          <td className="py-4 pr-4">
                            <span
                              className={`inline-flex rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.04em] ${
                                position.side === 'YES'
                                  ? 'bg-[var(--e-green-50)] text-[var(--e-green-700)]'
                                  : 'bg-[var(--e-red-50)] text-[var(--e-red-700)]'
                              }`}
                            >
                              {position.side}
                            </span>
                          </td>
                          <td className="py-4 pr-4 font-mono text-[var(--e-text-primary)]">{formatPrice(position.average_entry_price)}</td>
                          <td className="py-4 pr-4 font-mono text-[var(--e-text-primary)]">{formatPrice(position.current_price)}</td>
                          <td className="py-4 pr-4 text-right font-mono text-[var(--e-text-primary)]">{position.shards_held.toLocaleString()}</td>
                          <td className={`py-4 pr-4 text-right font-mono font-semibold ${metricTone(position.unrealised_pnl_usd)}`}>
                            <div>{formatSignedCurrency(position.unrealised_pnl_usd)}</div>
                            <div className="mt-1 text-[11px]">{position.unrealised_pnl_percent.toFixed(1)}%</div>
                          </td>
                          <td className="py-4 pr-4">
                            <div className="flex flex-wrap gap-1.5">
                              {isParadox ? <RiskChip label="Paradox" tone="paradox" /> : null}
                              {isExpiring ? <RiskChip label={`${Math.ceil((position.hours_until_reaper ?? 0) / 24)}d`} tone="soon" /> : null}
                              {!isParadox && !isExpiring ? <RiskChip label="Nominal" tone="nominal" /> : null}
                            </div>
                          </td>
                          <td className="py-4 text-right">
                            <button
                              type="button"
                              onClick={() => navigate(`/theatre/${position.timeline_id}`)}
                              className="inline-flex items-center gap-1 text-[12px] font-semibold text-[var(--e-purple-700)] transition hover:text-[var(--e-purple-800)]"
                            >
                              Open Market
                              <ArrowUpRight className="h-3.5 w-3.5" />
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <aside className="space-y-4">
            <section className="rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] p-4 shadow-[var(--e-shadow-xs)]">
              <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-[var(--e-text-muted)]">
                Portfolio posture
              </div>
              <div className="space-y-3">
                <div className="rounded-xl border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                    Active positions
                  </div>
                  <div className="mt-2 font-mono text-[22px] font-bold text-[var(--e-text-primary)]">
                    {summary ? summary.active_position_count : '—'}
                  </div>
                </div>
                <div className="rounded-xl border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                    Founder positions
                  </div>
                  <div className="mt-2 font-mono text-[22px] font-bold text-[var(--e-text-primary)]">
                    {summary ? summary.active_founder_positions : '—'}
                  </div>
                </div>
              </div>
            </section>

            <section className="rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] p-4 shadow-[var(--e-shadow-xs)]">
              <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-[var(--e-text-muted)]">
                Highest risk theatre
              </div>
              {summary?.highest_risk_timeline_name ? (
                <>
                  <div className="text-[15px] font-semibold text-[var(--e-text-primary)]">{summary.highest_risk_timeline_name}</div>
                  <div className="mt-1 text-[12px] text-[var(--e-text-secondary)]">
                    Stability {summary.highest_risk_stability ? `${Math.round(summary.highest_risk_stability)}%` : '—'}
                  </div>
                  <button
                    type="button"
                    onClick={() => navigate(`/theatre/${summary.highest_risk_timeline_id}`)}
                    className="mt-4 inline-flex items-center gap-2 rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 py-2 text-[12px] font-semibold text-[var(--e-text-secondary)] transition hover:text-[var(--e-text-primary)]"
                  >
                    Open theatre
                  </button>
                </>
              ) : (
                <div className="text-[13px] text-[var(--e-text-muted)]">No elevated risk detected across active positions.</div>
              )}
            </section>

            <section className="rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] p-4 shadow-[var(--e-shadow-xs)]">
              <div className="mb-3 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-[var(--e-text-muted)]">
                <Filter className="h-4 w-4" />
                Coverage
              </div>
              <div className="space-y-3 text-[13px] text-[var(--e-text-secondary)]">
                <div className="flex items-center justify-between gap-3">
                  <span>YES exposure</span>
                  <span className="font-mono text-[var(--e-text-primary)]">{formatCurrency(totals.yesNotional)}</span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span>NO exposure</span>
                  <span className="font-mono text-[var(--e-text-primary)]">{formatCurrency(totals.noNotional)}</span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span>Founder yield</span>
                  <span className="font-mono text-[var(--e-green-600)]">
                    {summary ? formatCurrency(summary.total_founder_yield_earned_usd) : '—'}
                  </span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span>Timelines at risk</span>
                  <span className="font-mono text-[var(--e-text-primary)]">{summary ? summary.timelines_at_risk : '—'}</span>
                </div>
              </div>
            </section>
          </aside>
        </div>
      </div>
    </div>
  );
}
