// Portfolio Page Component
// Portfolio overview with positions from real API

import { useState } from 'react';
import {
  TrendingUp,
  AlertTriangle,
  Activity,
  Filter,
  Loader2,
} from 'lucide-react';
import { usePositions, usePortfolioSummary, useEquityChart, usePortfolioStatus } from '../hooks/usePortfolio';
import type { ChartTimeframe, PositionTab } from '../types/portfolio';

export function PortfolioPage() {
  const { positions, totals, isLoading, error } = usePositions();
  const { summary } = usePortfolioSummary();
  const { timeframe: chartTimeframe, setTimeframe: setChartTimeframe } = useEquityChart();
  usePortfolioStatus();

  const [positionTab, setPositionTab] = useState<PositionTab>('positions');

  const formatPL = (value: number): string => {
    const prefix = value >= 0 ? '+' : '';
    return `${prefix}$${Math.abs(value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  if (error) {
    return (
      <div className="h-full flex items-center justify-center bg-terminal-bg text-terminal-text">
        <div className="text-center">
          <AlertTriangle size={32} className="text-status-danger mx-auto mb-3" />
          <div className="text-sm font-semibold mb-1">Failed to load portfolio</div>
          <div className="text-xs text-terminal-text-muted">Check that the backend is running</div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col min-h-0 bg-terminal-bg text-terminal-text">
      <main className="flex-1 flex flex-col min-h-0 overflow-hidden">
        <div className="flex-1 flex min-w-0 overflow-hidden gap-4 p-4">
          {/* Left Column */}
          <div className="flex-1 min-w-0 overflow-y-auto pr-6 custom-scrollbar">
            <div className="bg-terminal-bg border border-terminal-border rounded-2xl flex flex-col overflow-hidden">
              {/* Header */}
              <div className="px-4 py-4 border-b border-terminal-border">
                <div className="text-sm font-semibold text-terminal-text mb-1">
                  Portfolio Overview
                </div>
                <div className="text-xs text-terminal-text-muted">
                  Live positions and performance from real market data
                </div>
              </div>

              {/* Top Metrics */}
              <div className="grid grid-cols-3 gap-3 p-4">
                <div className="bg-terminal-bg border border-terminal-border rounded-xl p-3">
                  <div className="text-[10px] font-semibold text-terminal-text-muted uppercase tracking-wider mb-1">
                    Total P/L
                  </div>
                  <div className={`text-2xl font-bold mono ${totals.totalPL >= 0 ? 'text-status-success' : 'text-status-danger'}`}>
                    {isLoading ? '---' : formatPL(totals.totalPL)}
                  </div>
                </div>
                <div className="bg-terminal-bg border border-terminal-border rounded-xl p-3">
                  <div className="text-[10px] font-semibold text-terminal-text-muted uppercase tracking-wider mb-1">
                    Win Rate
                  </div>
                  <div className="text-2xl font-bold text-terminal-text mono">
                    {isLoading ? '---' : `${totals.winRate.toFixed(0)}%`}
                  </div>
                </div>
                <div className="bg-terminal-bg border border-terminal-border rounded-xl p-3">
                  <div className="text-[10px] font-semibold text-terminal-text-muted uppercase tracking-wider mb-1">
                    Positions
                  </div>
                  <div className="text-2xl font-bold text-terminal-text mono">
                    {isLoading ? '---' : positions.length}
                  </div>
                </div>
              </div>

              {/* Scrollable Content */}
              <div className="flex-1 overflow-auto px-4 pb-4">
                {/* Portfolio Summary */}
                {summary && (
                  <div className="mt-4 p-3 bg-terminal-bg border border-terminal-border rounded-xl">
                    <div className="text-[11px] font-semibold text-terminal-text uppercase tracking-wider mb-3">
                      Portfolio Summary
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <div className="text-[11px] text-terminal-text-secondary mb-1">Total Value</div>
                        <div className="text-sm font-semibold text-terminal-text mono">
                          ${summary.total_value_usd.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </div>
                      </div>
                      <div>
                        <div className="text-[11px] text-terminal-text-secondary mb-1">Unrealised P/L</div>
                        <div className={`text-sm font-semibold mono ${summary.total_unrealised_pnl_usd >= 0 ? 'text-status-success' : 'text-status-danger'}`}>
                          {formatPL(summary.total_unrealised_pnl_usd)} ({summary.total_unrealised_pnl_percent.toFixed(1)}%)
                        </div>
                      </div>
                      <div>
                        <div className="text-[11px] text-terminal-text-secondary mb-1">Founder Yield</div>
                        <div className="text-sm font-semibold text-status-success mono">
                          +${summary.total_founder_yield_earned_usd.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </div>
                      </div>
                      <div>
                        <div className="text-[11px] text-terminal-text-secondary mb-1">At Risk</div>
                        <div className="text-sm font-semibold text-terminal-text mono">
                          {summary.timelines_at_risk} timeline{summary.timelines_at_risk !== 1 ? 's' : ''}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Exposure Summary */}
                <div className="mt-4 p-3 bg-terminal-bg border border-terminal-border rounded-xl">
                  <div className="text-[11px] font-semibold text-terminal-text uppercase tracking-wider mb-3">
                    Exposure Summary
                  </div>
                  <div className="mb-3">
                    <div className="flex justify-between mb-1">
                      <span className="text-[11px] text-terminal-text-secondary">Total Notional</span>
                      <span className="text-xs font-semibold text-terminal-text mono">
                        ${totals.totalNotional.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </span>
                    </div>
                  </div>
                  {totals.totalNotional > 0 && (
                    <>
                      <div className="mb-3">
                        <div className="flex justify-between mb-1">
                          <span className="text-[11px] text-terminal-text-secondary">Net YES Notional</span>
                          <span className="text-xs font-semibold text-status-success mono">
                            ${totals.yesNotional.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </span>
                        </div>
                        <div className="h-1.5 bg-terminal-bg rounded overflow-hidden">
                          <div className="h-full bg-status-success" style={{ width: `${(totals.yesNotional / totals.totalNotional) * 100}%` }}></div>
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between mb-1">
                          <span className="text-[11px] text-terminal-text-secondary">Net NO Notional</span>
                          <span className="text-xs font-semibold text-status-danger mono">
                            ${totals.noNotional.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </span>
                        </div>
                        <div className="h-1.5 bg-terminal-bg rounded overflow-hidden">
                          <div className="h-full bg-status-danger" style={{ width: `${(totals.noNotional / totals.totalNotional) * 100}%` }}></div>
                        </div>
                      </div>
                    </>
                  )}
                </div>

                {/* Equity Curve placeholder */}
                <div className="mt-4 p-3 bg-terminal-bg border border-terminal-border rounded-xl">
                  <div className="flex justify-between items-center mb-3">
                    <div className="text-[11px] font-semibold text-terminal-text uppercase tracking-wider">Equity Curve</div>
                    <div className="flex gap-1">
                      {(['1D', '7D', '30D', 'ALL'] as ChartTimeframe[]).map((tf) => (
                        <button
                          key={tf}
                          onClick={() => setChartTimeframe(tf)}
                          className={`px-2.5 py-1 rounded-lg text-[10px] cursor-pointer transition-all ${chartTimeframe === tf ? 'bg-echelon-cyan/10 border border-echelon-cyan/30 text-echelon-cyan' : 'bg-transparent border border-terminal-border text-terminal-text-muted hover:text-terminal-text-secondary'}`}
                        >
                          {tf}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="relative h-[120px] bg-terminal-bg rounded-lg overflow-hidden flex items-center justify-center">
                    <span className="text-xs text-terminal-text-muted">Equity history coming soon</span>
                  </div>
                </div>

                {/* Positions Panel */}
                <div className="flex-1 bg-terminal-bg border border-terminal-border rounded-xl flex flex-col mt-4 overflow-hidden">
                  <div className="flex items-center justify-between p-3 border-b border-terminal-border">
                    <div className="flex gap-3">
                      {(['positions', 'foldovers'] as PositionTab[]).map((tab) => (
                        <button
                          key={tab}
                          onClick={() => setPositionTab(tab)}
                          className={`px-3 py-1 rounded-lg text-[11px] font-medium capitalize cursor-pointer transition-all ${positionTab === tab ? 'bg-echelon-cyan/10 border border-echelon-cyan/30 text-echelon-cyan' : 'bg-transparent border border-terminal-border text-terminal-text-muted hover:text-terminal-text-secondary'}`}
                        >
                          {tab}
                        </button>
                      ))}
                    </div>
                    <button className="flex items-center gap-2 px-3 py-2 bg-terminal-bg border border-terminal-border rounded-lg text-[11px] font-medium text-terminal-text-secondary hover:border-echelon-cyan/50 hover:text-echelon-cyan transition-all cursor-pointer">
                      <Filter size={12} />
                      Filter
                    </button>
                  </div>
                  <div className="flex-1 overflow-auto">
                    {isLoading ? (
                      <div className="flex items-center justify-center p-8">
                        <Loader2 size={20} className="animate-spin text-terminal-text-muted" />
                        <span className="ml-2 text-xs text-terminal-text-muted">Loading positions...</span>
                      </div>
                    ) : positions.length === 0 ? (
                      <div className="flex flex-col items-center justify-center p-8">
                        <Activity size={24} className="text-terminal-text-muted mb-2" />
                        <span className="text-xs text-terminal-text-muted">No positions yet</span>
                        <span className="text-[10px] text-terminal-text-muted mt-1">Trade on a timeline to see your positions here</span>
                      </div>
                    ) : (
                      <table className="w-full border-collapse">
                        <thead>
                          <tr>
                            <th className="text-left p-2 text-[9px] font-semibold text-terminal-text-muted uppercase tracking-wider bg-terminal-bg border-b border-terminal-border sticky top-0">Timeline</th>
                            <th className="text-left p-2 text-[9px] font-semibold text-terminal-text-muted uppercase tracking-wider bg-terminal-bg border-b border-terminal-border sticky top-0">Side</th>
                            <th className="text-left p-2 text-[9px] font-semibold text-terminal-text-muted uppercase tracking-wider bg-terminal-bg border-b border-terminal-border sticky top-0">Shards</th>
                            <th className="text-left p-2 text-[9px] font-semibold text-terminal-text-muted uppercase tracking-wider bg-terminal-bg border-b border-terminal-border sticky top-0">Entry</th>
                            <th className="text-left p-2 text-[9px] font-semibold text-terminal-text-muted uppercase tracking-wider bg-terminal-bg border-b border-terminal-border sticky top-0">Current</th>
                            <th className="text-left p-2 text-[9px] font-semibold text-terminal-text-muted uppercase tracking-wider bg-terminal-bg border-b border-terminal-border sticky top-0">P/L</th>
                            <th className="text-left p-2 text-[9px] font-semibold text-terminal-text-muted uppercase tracking-wider bg-terminal-bg border-b border-terminal-border sticky top-0">Stability</th>
                            <th className="text-center p-2 text-[9px] font-semibold text-terminal-text-muted uppercase tracking-wider bg-terminal-bg border-b border-terminal-border sticky top-0">Risk</th>
                          </tr>
                        </thead>
                        <tbody>
                          {positions.map((p) => (
                            <tr key={`${p.timeline_id}-${p.side}`} className="border-b border-terminal-border">
                              <td className="p-2">
                                <div className="text-xs font-semibold text-terminal-text mono">{p.timeline_name}</div>
                                <div className="text-[10px] text-terminal-text-muted mono">{p.timeline_id}</div>
                              </td>
                              <td className="p-2">
                                <span className="inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold" style={{ background: p.side === 'YES' ? 'rgba(74,222,128,0.1)' : 'rgba(251,113,133,0.1)', color: p.side === 'YES' ? '#4ADE80' : '#FB7185' }}>
                                  {p.side}
                                </span>
                              </td>
                              <td className="p-2"><span className="text-xs text-terminal-text mono">{p.shards_held.toLocaleString()}</span></td>
                              <td className="p-2"><span className="text-xs text-terminal-text mono">${p.average_entry_price.toFixed(2)}</span></td>
                              <td className="p-2"><span className="text-xs text-terminal-text mono">${p.current_price.toFixed(2)}</span></td>
                              <td className="p-2">
                                <span className={`text-xs font-semibold mono ${p.unrealised_pnl_usd >= 0 ? 'text-status-success' : 'text-status-danger'}`}>
                                  {formatPL(p.unrealised_pnl_usd)}
                                </span>
                                <div className="text-[10px] text-terminal-text-muted">
                                  {p.unrealised_pnl_percent >= 0 ? '+' : ''}{p.unrealised_pnl_percent.toFixed(1)}%
                                </div>
                              </td>
                              <td className="p-2">
                                <span className="text-xs mono" style={{ color: p.timeline_stability >= 70 ? '#4ADE80' : p.timeline_stability >= 30 ? '#F59E0B' : '#FB7185' }}>
                                  {p.timeline_stability.toFixed(0)}%
                                </span>
                              </td>
                              <td className="p-2 text-center">
                                {p.has_active_paradox && (
                                  <span className="inline-block px-1.5 py-0.5 rounded text-[9px] font-semibold bg-status-danger/10 text-status-danger">
                                    PARADOX
                                  </span>
                                )}
                                {p.is_founder && (
                                  <span className="inline-block px-1.5 py-0.5 rounded text-[9px] font-semibold bg-echelon-cyan/10 text-echelon-cyan ml-1">
                                    FOUNDER
                                  </span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Sidebar */}
          <aside className="w-[360px] flex-shrink-0 flex flex-col gap-4 self-start sticky top-6">
            {/* Summary Card */}
            {summary && (
              <div className="bg-terminal-bg border border-terminal-border rounded-xl p-3">
                <div className="text-[11px] font-semibold text-terminal-text uppercase tracking-wider mb-3">Quick Stats</div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="text-center p-2 bg-terminal-bg border border-terminal-border rounded-lg">
                    <div className="text-xl font-bold text-terminal-text mono">{summary.active_position_count}</div>
                    <div className="text-[10px] text-terminal-text-muted mt-0.5">Active Positions</div>
                  </div>
                  <div className="text-center p-2 bg-terminal-bg border border-terminal-border rounded-lg">
                    <div className="text-xl font-bold text-terminal-text mono">{summary.active_founder_positions}</div>
                    <div className="text-[10px] text-terminal-text-muted mt-0.5">Founder Positions</div>
                  </div>
                </div>
              </div>
            )}

            {/* Highest Risk Timeline */}
            {summary?.highest_risk_timeline_id && (
              <div className="bg-terminal-bg border border-terminal-border rounded-xl p-3">
                <div className="flex items-center gap-2 mb-2">
                  <AlertTriangle size={14} className="text-status-warning" />
                  <span className="text-[11px] font-semibold text-terminal-text uppercase tracking-wider">Highest Risk</span>
                </div>
                <div className="text-xs font-semibold text-terminal-text mono">{summary.highest_risk_timeline_name}</div>
                <div className="text-[10px] text-terminal-text-muted mono">{summary.highest_risk_timeline_id}</div>
                <div className="mt-2">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] text-terminal-text-muted">Stability</span>
                    <span className="text-xs font-semibold mono" style={{ color: (summary.highest_risk_stability ?? 0) >= 30 ? '#F59E0B' : '#FB7185' }}>
                      {summary.highest_risk_stability?.toFixed(0) ?? '?'}%
                    </span>
                  </div>
                  <div className="h-1.5 bg-terminal-bg rounded overflow-hidden">
                    <div className="h-full rounded" style={{ width: `${summary.highest_risk_stability ?? 0}%`, background: (summary.highest_risk_stability ?? 0) >= 30 ? '#F59E0B' : '#FB7185' }}></div>
                  </div>
                </div>
              </div>
            )}

            {/* Founder Yield Card */}
            {summary && summary.total_founder_yield_earned_usd > 0 && (
              <div className="bg-terminal-bg border border-terminal-border rounded-xl p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-semibold text-terminal-text uppercase tracking-wider flex items-center gap-2">
                    <TrendingUp size={14} className="text-echelon-cyan" />
                    Founder Yield
                  </span>
                </div>
                <div className="text-xl font-bold text-status-success mono">
                  +${summary.total_founder_yield_earned_usd.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
                <div className="text-[10px] text-terminal-text-muted mt-1">
                  Across {summary.active_founder_positions} founder position{summary.active_founder_positions !== 1 ? 's' : ''}
                </div>
              </div>
            )}
          </aside>
        </div>
      </main>
    </div>
  );
}
