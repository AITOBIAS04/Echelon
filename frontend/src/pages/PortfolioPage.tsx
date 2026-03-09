import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Briefcase, Filter, Loader2, TrendingUp } from 'lucide-react';
import { EmptyState } from '../components/empty-states/EmptyState';
import { useEquityChart, usePortfolioStatus, usePortfolioSummary, usePositions } from '../hooks/usePortfolio';
import type { ChartTimeframe, PositionTab } from '../types/portfolio';

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

function metricTone(value: number) {
  if (value > 0) return 'text-[var(--e-green-600)]';
  if (value < 0) return 'text-[var(--e-red-600)]';
  return 'text-[var(--e-text-primary)]';
}

function KpiCard({
  label,
  value,
  detail,
  tone,
}: {
  label: string;
  value: string | number;
  detail?: string;
  tone?: string;
}) {
  return (
    <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-3 shadow-[var(--e-shadow-xs)]">
      <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
        {label}
      </div>
      <div className={`font-mono text-[24px] font-bold leading-8 tabular-nums ${tone ?? 'text-[var(--e-text-primary)]'}`}>
        {value}
      </div>
      {detail ? <div className="mt-1 text-[11px] text-[var(--e-text-muted)]">{detail}</div> : null}
    </div>
  );
}

export function PortfolioPage() {
  const navigate = useNavigate();
  const { positions, totals, isLoading, error } = usePositions();
  const { summary } = usePortfolioSummary();
  const { timeframe, setTimeframe } = useEquityChart();
  usePortfolioStatus();
  const [positionTab, setPositionTab] = useState<PositionTab>('positions');

  const exposureSplit = useMemo(() => {
    if (totals.totalNotional <= 0) {
      return { yes: 0, no: 0 };
    }
    return {
      yes: (totals.yesNotional / totals.totalNotional) * 100,
      no: (totals.noNotional / totals.totalNotional) * 100,
    };
  }, [totals.noNotional, totals.totalNotional, totals.yesNotional]);

  if (error) {
    return (
      <div className="p-6">
        <div className="mx-auto max-w-6xl">
          <section className="rounded-xl border border-[var(--e-red-200)] bg-[var(--e-red-50)] px-5 py-4 text-[13px] text-[var(--e-red-600)] shadow-[var(--e-shadow-xs)]">
            Failed to load portfolio. Check that the positions and portfolio summary services are available.
          </section>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <section className="grid gap-4 md:grid-cols-4">
          <KpiCard label="Total P/L" value={isLoading ? '—' : formatSignedCurrency(totals.totalPL)} tone={metricTone(totals.totalPL)} />
          <KpiCard label="Win Rate" value={isLoading ? '—' : `${totals.winRate.toFixed(0)}%`} />
          <KpiCard label="Positions" value={isLoading ? '—' : positions.length} />
          <KpiCard
            label="Total Notional"
            value={isLoading ? '—' : formatCurrency(totals.totalNotional)}
            detail={summary ? `${summary.timelines_at_risk} timeline${summary.timelines_at_risk === 1 ? '' : 's'} at risk` : undefined}
          />
        </section>

        <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
          <div className="space-y-4">
            <section className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
              <div className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-3">
                <div className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                  Exposure Summary
                </div>
              </div>
              <div className="grid gap-4 px-5 py-5 md:grid-cols-2">
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-[13px] text-[var(--e-text-secondary)]">
                    <span>Total Notional</span>
                    <span className="font-mono font-semibold text-[var(--e-text-primary)]">
                      {formatCurrency(totals.totalNotional)}
                    </span>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-[12px] text-[var(--e-text-secondary)]">
                      <span>YES exposure</span>
                      <span className="font-mono text-[var(--e-green-600)]">{formatCurrency(totals.yesNotional)}</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-[var(--e-bg-sunken)]">
                      <div className="h-full bg-[var(--e-green-600)]" style={{ width: `${exposureSplit.yes}%` }} />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-[12px] text-[var(--e-text-secondary)]">
                      <span>NO exposure</span>
                      <span className="font-mono text-[var(--e-red-600)]">{formatCurrency(totals.noNotional)}</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-[var(--e-bg-sunken)]">
                      <div className="h-full bg-[var(--e-red-600)]" style={{ width: `${exposureSplit.no}%` }} />
                    </div>
                  </div>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
                    <div className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                      Total Value
                    </div>
                    <div className="mt-2 font-mono text-[18px] font-bold text-[var(--e-text-primary)]">
                      {summary ? formatCurrency(summary.total_value_usd) : '—'}
                    </div>
                  </div>
                  <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
                    <div className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                      Unrealised P/L
                    </div>
                    <div className={`mt-2 font-mono text-[18px] font-bold ${metricTone(summary?.total_unrealised_pnl_usd ?? 0)}`}>
                      {summary ? formatSignedCurrency(summary.total_unrealised_pnl_usd) : '—'}
                    </div>
                  </div>
                  <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
                    <div className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                      Founder Yield
                    </div>
                    <div className="mt-2 font-mono text-[18px] font-bold text-[var(--e-green-600)]">
                      {summary ? formatCurrency(summary.total_founder_yield_earned_usd) : '—'}
                    </div>
                  </div>
                  <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
                    <div className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                      At Risk
                    </div>
                    <div className="mt-2 font-mono text-[18px] font-bold text-[var(--e-text-primary)]">
                      {summary ? summary.timelines_at_risk : '—'}
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <section className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
              <div className="flex items-center justify-between gap-3 border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-3">
                <div className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                  Equity Curve
                </div>
                <div className="flex flex-wrap gap-1">
                  {(['1D', '7D', '30D', 'ALL'] as ChartTimeframe[]).map((option) => (
                    <button
                      key={option}
                      type="button"
                      onClick={() => setTimeframe(option)}
                      className={`rounded-md border px-2.5 py-1 text-[10px] font-semibold transition ${
                        timeframe === option
                          ? 'border-[var(--e-purple-300)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)]'
                          : 'border-[var(--e-border-primary)] bg-[var(--e-bg-card)] text-[var(--e-text-muted)] hover:text-[var(--e-text-primary)]'
                      }`}
                    >
                      {option}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex min-h-[180px] items-center justify-center px-5 py-6 text-center">
                <div>
                  <div className="text-[13px] font-medium text-[var(--e-text-secondary)]">Equity history coming soon</div>
                  <div className="mt-2 text-[12px] text-[var(--e-text-muted)]">
                    Current portfolio contracts do not yet expose persisted equity snapshots.
                  </div>
                </div>
              </div>
            </section>

            <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
              <div className="flex items-center justify-between gap-3 border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-3">
                <div className="flex gap-2">
                  {(['positions', 'foldovers'] as PositionTab[]).map((tab) => (
                    <button
                      key={tab}
                      type="button"
                      onClick={() => setPositionTab(tab)}
                      className={`rounded-md border px-3 py-1.5 text-[12px] font-semibold capitalize transition ${
                        positionTab === tab
                          ? 'border-[var(--e-purple-300)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)]'
                          : 'border-[var(--e-border-primary)] bg-[var(--e-bg-card)] text-[var(--e-text-muted)] hover:text-[var(--e-text-primary)]'
                      }`}
                    >
                      {tab}
                    </button>
                  ))}
                </div>
                <button
                  type="button"
                  className="inline-flex items-center gap-2 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 py-2 text-[12px] font-semibold text-[var(--e-text-secondary)]"
                >
                  <Filter className="h-3.5 w-3.5" />
                  Filter
                </button>
              </div>
              <div className="px-5 py-5">
                {isLoading ? (
                  <div className="flex items-center justify-center gap-2 py-10 text-[13px] text-[var(--e-text-muted)]">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Loading positions...
                  </div>
                ) : positions.length === 0 ? (
                  <EmptyState
                    type="ZERO_STATE"
                    icon={<Briefcase className="h-7 w-7" />}
                    title="No open positions"
                    description="Positions appear here once you trade on a theatre. Browse active theatres to get started."
                    actions={[
                      {
                        label: 'Browse Theatres',
                        onClick: () => navigate('/theatres'),
                        variant: 'primary',
                      },
                    ]}
                  />
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full border-collapse">
                      <thead>
                        <tr className="border-b border-[var(--e-border-secondary)] text-left text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                          <th className="pb-3 pr-4">Theatre</th>
                          <th className="pb-3 pr-4">Side</th>
                          <th className="pb-3 pr-4">Shards</th>
                          <th className="pb-3 pr-4">Entry</th>
                          <th className="pb-3 pr-4">Current</th>
                          <th className="pb-3 pr-4">P/L</th>
                          <th className="pb-3">Stability</th>
                        </tr>
                      </thead>
                      <tbody>
                        {positions.map((position) => (
                          <tr key={`${position.timeline_id}-${position.side}`} className="border-b border-[var(--e-border-secondary)]/70 text-[13px]">
                            <td className="py-3 pr-4">
                              <div className="font-semibold text-[var(--e-text-primary)]">{position.timeline_name}</div>
                              <div className="mt-1 font-mono text-[11px] text-[var(--e-text-muted)]">{position.timeline_id}</div>
                            </td>
                            <td className="py-3 pr-4">
                              <span
                                className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] ${
                                  position.side === 'YES'
                                    ? 'bg-[var(--e-green-50)] text-[var(--e-green-600)]'
                                    : 'bg-[var(--e-red-50)] text-[var(--e-red-600)]'
                                }`}
                              >
                                {position.side}
                              </span>
                            </td>
                            <td className="py-3 pr-4 font-mono text-[var(--e-text-primary)]">{position.shards_held.toLocaleString()}</td>
                            <td className="py-3 pr-4 font-mono text-[var(--e-text-primary)]">{formatCurrency(position.average_entry_price)}</td>
                            <td className="py-3 pr-4 font-mono text-[var(--e-text-primary)]">{formatCurrency(position.current_price)}</td>
                            <td className={`py-3 pr-4 font-mono font-semibold ${metricTone(position.unrealised_pnl_usd)}`}>
                              {formatSignedCurrency(position.unrealised_pnl_usd)}
                            </td>
                            <td className="py-3 font-mono text-[var(--e-text-primary)]">{Math.round(position.timeline_stability)}%</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </section>
          </div>

          <aside className="space-y-4">
            <section className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-4 shadow-[var(--e-shadow-xs)]">
              <div className="mb-3 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                <TrendingUp className="h-4 w-4" />
                Quick Stats
              </div>
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
                <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
                  <div className="text-[11px] text-[var(--e-text-muted)]">Active Positions</div>
                  <div className="mt-2 font-mono text-[22px] font-bold text-[var(--e-text-primary)]">
                    {summary ? summary.active_position_count : '—'}
                  </div>
                </div>
                <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
                  <div className="text-[11px] text-[var(--e-text-muted)]">Founder Positions</div>
                  <div className="mt-2 font-mono text-[22px] font-bold text-[var(--e-text-primary)]">
                    {summary ? summary.active_founder_positions : '—'}
                  </div>
                </div>
              </div>
            </section>

            {summary?.highest_risk_timeline_name ? (
              <section className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-4 shadow-[var(--e-shadow-xs)]">
                <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                  Highest Risk
                </div>
                <div className="text-[14px] font-semibold text-[var(--e-text-primary)]">
                  {summary.highest_risk_timeline_name}
                </div>
                <div className="mt-1 font-mono text-[11px] text-[var(--e-text-muted)]">{summary.highest_risk_timeline_id}</div>
              </section>
            ) : null}
          </aside>
        </div>
      </div>
    </div>
  );
}
