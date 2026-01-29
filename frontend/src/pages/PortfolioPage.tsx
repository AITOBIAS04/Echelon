// Portfolio Page Component
// Portfolio overview with risk metrics, positions, and performance

import { useState } from 'react';
import { 
  Plus, 
  BarChart3, 
  TrendingUp, 
  AlertTriangle, 
  Activity,
  GitBranch,
  Bot,
  Filter,
  X,
  ChevronRight,
  Star
} from 'lucide-react';
import { usePositions, useRiskMetrics, useAllocation, useEquityChart, useCorrelations, useRiskItems, useRecommendations, useGhostForks, usePortfolioAgents, usePortfolioStatus, useForkDetails, useYieldBreakdown } from '../hooks/usePortfolio';
import type { ChartTimeframe, PositionTab } from '../types/portfolio';

export function PortfolioPage() {
  const { positions, totals } = usePositions();
  const riskMetrics = useRiskMetrics();
  const { allocations, totals: allocationTotals } = useAllocation();
  const { data: equityData, timeframe: chartTimeframe, setTimeframe: setChartTimeframe, stats: equityStats } = useEquityChart();
  const correlations = useCorrelations();
  const riskItems = useRiskItems();
  const recommendations = useRecommendations();
  const ghostForks = useGhostForks();
  const agents = usePortfolioAgents();
  const { clock } = usePortfolioStatus();
  const forkDetails = useForkDetails();
  const yieldBreakdown = useYieldBreakdown();

  const [positionTab, setPositionTab] = useState<PositionTab>('positions');
  const [showAgentsPanel, setShowAgentsPanel] = useState(false);
  const [showForksPanel, setShowForksPanel] = useState(false);

  // Get correlation value between two timelines
  const getCorrelation = (t1: string, t2: string): number => {
    const found = correlations.find(c =>
      (c.timeline1 === t1 && c.timeline2 === t2) ||
      (c.timeline1 === t2 && c.timeline2 === t1)
    );
    return found?.value ?? 1;
  };

  // Format P/L
  const formatPL = (value: number): string => {
    return `$${value.toLocaleString()}`;
  };

  // Generate equity chart path
  const generateEquityPath = (): { area: string; line: string } => {
    if (equityData.length === 0) return { area: '', line: '' };

    const minValue = Math.min(...equityData.map(d => d.value));
    const maxValue = Math.max(...equityData.map(d => d.value));
    const range = maxValue - minValue || 1;
    const width = 100;
    const height = 80;
    const padding = 10;

    const points = equityData.map((d, i) => {
      const x = (i / (equityData.length - 1)) * width;
      const y = height - padding - ((d.value - minValue) / range) * (height - padding * 2);
      return { x, y };
    });

    const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
    const areaPath = `${linePath} L ${width} ${height} L 0 ${height} Z`;

    return { area: areaPath, line: linePath };
  };

  const { area: equityAreaPath, line: equityLinePath } = generateEquityPath();

  // Close panels
  const closeAllPanels = () => {
    setShowAgentsPanel(false);
    setShowForksPanel(false);
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#0F1113] text-white">
      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-16 border-b border-[#26292E] flex items-center justify-between px-6 flex-shrink-0">
          <div className="text-base font-semibold tracking-wide">
            Portfolio
          </div>
          <div className="flex items-center gap-4">
            <button className="flex items-center gap-2 px-3 py-2 bg-[#0F1113] border border-[#26292E] rounded-lg text-xs font-medium text-gray-400 hover:border-cyan-500/50 hover:text-cyan-400 transition-all cursor-pointer">
              <Plus size={14} />
              New Position
            </button>
            <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400 bg-emerald-400/10 px-3 py-1.5 rounded-full border border-emerald-400/20">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              Connected
            </div>
            <span className="mono text-xs text-gray-400">{clock}</span>
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 p-4 flex gap-4 overflow-hidden">
          {/* Main Panel */}
          <div className="flex-1 bg-[#0F1113] border border-[#26292E] rounded-2xl flex flex-col overflow-hidden">
            {/* Header */}
            <div className="px-4 py-4 border-b border-[#26292E]">
              <div className="text-sm font-semibold text-white mb-1">
                Portfolio Overview
              </div>
              <div className="text-xs text-gray-500">
                Portfolio risk metrics, positions, and performance data
              </div>
            </div>

            {/* Top Metrics */}
            <div className="grid grid-cols-3 gap-3 p-4">
              <div className="bg-[#0F1113] border border-[#26292E] rounded-xl p-3">
                <div className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1">
                  Total P/L
                </div>
                <div className="text-2xl font-bold text-emerald-400 mono">
                  +${totals.totalPL.toLocaleString()}
                </div>
              </div>
              <div className="bg-[#0F1113] border border-[#26292E] rounded-xl p-3">
                <div className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1">
                  Win Rate
                </div>
                <div className="text-2xl font-bold text-white mono">
                  {totals.winRate.toFixed(0)}%
                </div>
              </div>
              <div className="bg-[#0F1113] border border-[#26292E] rounded-xl p-3">
                <div className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1">
                  Positions
                </div>
                <div className="text-2xl font-bold text-white mono">
                  {positions.length}
                </div>
              </div>
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-auto px-4 pb-4">
              {/* KPI Tiles */}
              <div className="mt-4">
                <div className="text-[11px] font-semibold text-white uppercase tracking-wider mb-3">
                  Risk Metrics
                </div>
                <div className="grid grid-cols-4 gap-3">
                  {riskMetrics.map((metric, i) => (
                    <div key={i} className="bg-[#0F1113] border border-[#26292E] rounded-xl p-3">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[11px] text-gray-400">{metric.label}</span>
                        <span className="text-sm" style={{ color: metric.level === 'low' ? 'var(--status-success)' : metric.level === 'medium' ? '#F59E0B' : 'var(--status-danger)' }}>
                          {metric.icon === 'ri-dashboard-3-line' && <BarChart3 size={14} />}
                          {metric.icon === 'ri-bar-chart-box-line' && <Activity size={14} />}
                          {metric.icon === 'ri-trending-up-line' && <TrendingUp size={14} />}
                          {metric.icon === 'ri-error-warning-line' && <AlertTriangle size={14}/>}
                        </span>
                      </div>
                      <div className="text-[28px] font-bold leading-tight" style={{ color: metric.level === 'low' ? 'var(--status-success)' : metric.level === 'medium' ? '#F59E0B' : 'var(--status-danger)' }}>
                        {metric.value}
                      </div>
                      <div className="text-[11px] text-gray-500 mono">/ {metric.max}</div>
                      <div className="mt-2">
                        <div className="h-1 bg-[#0F1113] rounded overflow-hidden mb-1">
                          <div className="h-full rounded transition-all" style={{ width: `${metric.value}%`, background: metric.level === 'low' ? 'var(--status-success)' : metric.level === 'medium' ? 'var(--status-warning)' : 'var(--status-danger)' }}></div>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded" style={{ background: metric.level === 'low' ? 'var(--status-success-bg)' : metric.level === 'medium' ? 'var(--status-warning-bg)' : 'var(--status-danger-bg)', color: metric.level === 'low' ? 'var(--status-success)' : metric.level === 'medium' ? 'var(--status-warning)' : 'var(--status-danger)' }}>
                            {metric.level.toUpperCase()}
                          </span>
                          <span className="text-[9px] text-gray-500">{metric.value}%</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Exposure Summary */}
              <div className="mt-4 p-3 bg-[#0F1113] border border-[#26292E] rounded-xl">
                <div className="text-[11px] font-semibold text-white uppercase tracking-wider mb-3">
                  Exposure Summary
                </div>
                <div className="mb-3">
                  <div className="flex justify-between mb-1">
                    <span className="text-[11px] text-gray-400">Total Notional</span>
                    <span className="text-xs font-semibold text-white mono">${totals.totalNotional.toLocaleString()}.00</span>
                  </div>
                </div>
                <div className="mb-3">
                  <div className="flex justify-between mb-1">
                    <span className="text-[11px] text-gray-400">Net YES Notional</span>
                    <span className="text-xs font-semibold text-emerald-400 mono">${totals.yesNotional.toLocaleString()}.00</span>
                  </div>
                  <div className="h-1.5 bg-[#0F1113] rounded overflow-hidden">
                    <div className="h-full bg-emerald-500" style={{ width: `${allocationTotals.yesTotal}%` }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-[11px] text-gray-400">Net NO Notional</span>
                    <span className="text-xs font-semibold text-red-400 mono">${totals.noNotional.toLocaleString()}.00</span>
                  </div>
                  <div className="h-1.5 bg-[#0F1113] rounded overflow-hidden">
                    <div className="h-full bg-red-500" style={{ width: `${allocationTotals.noTotal}%` }}></div>
                  </div>
                </div>
              </div>

              {/* Portfolio Allocation */}
              <div className="mt-4 p-3 bg-[#0F1113] border border-[#26292E] rounded-xl">
                <div className="text-[11px] font-semibold text-white uppercase tracking-wider mb-3">
                  Portfolio Allocation
                </div>
                {allocations.map((allocation, i) => (
                  <div key={i} className="flex items-center gap-3 mb-2">
                    <span className="text-[11px] text-white mono w-20">{allocation.timelineId} ({allocation.direction})</span>
                    <div className="flex-1 h-2 bg-[#0F1113] rounded overflow-hidden">
                      <div className="h-full rounded" style={{ width: `${allocation.percent}%`, background: allocation.direction === 'YES' ? 'var(--status-success)' : 'var(--status-danger)' }}></div>
                    </div>
                    <span className="text-[11px] text-gray-500 mono w-10 text-right">{allocation.percent}%</span>
                  </div>
                ))}
              </div>

              {/* Equity Curve */}
              <div className="mt-4 p-3 bg-[#0F1113] border border-[#26292E] rounded-xl">
                <div className="flex justify-between items-center mb-3">
                  <div className="text-[11px] font-semibold text-white uppercase tracking-wider">Equity Curve (30D)</div>
                  <div className="flex gap-1">
                    {(['1D', '7D', '30D', 'ALL'] as ChartTimeframe[]).map((tf) => (
                      <button
                        key={tf}
                        onClick={() => setChartTimeframe(tf)}
                        className={`px-2.5 py-1 rounded-lg text-[10px] cursor-pointer transition-all ${chartTimeframe === tf ? 'bg-cyan-500/10 border border-cyan-500/50 text-cyan-400' : 'text-gray-500 hover:text-gray-300'}`}
                        style={{ background: chartTimeframe === tf ? 'var(--echelon-cyan-bg)' : 'transparent', border: '1px solid var(--border-outer)', color: chartTimeframe === tf ? 'var(--echelon-cyan)' : 'var(--text-muted)' }}
                      >
                        {tf}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="relative h-[120px] bg-[#0F1113] rounded-lg overflow-hidden">
                  <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-0 w-full h-full">
                    <defs>
                      <linearGradient id="equityGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stopColor="var(--status-success)" stopOpacity="0.4"/>
                        <stop offset="100%" stopColor="var(--status-success)" stopOpacity="0"/>
                      </linearGradient>
                    </defs>
                    <path d={equityAreaPath} fill="url(#equityGradient)"/>
                    <path d={equityLinePath} fill="none" stroke="var(--status-success)" strokeWidth="1" strokeLinecap="round"/>
                  </svg>
                  <div className="absolute inset-0">
                    {[0, 25, 50, 75].map((pct) => (
                      <div key={pct} className="absolute left-0 right-0 h-px" style={{ top: `${pct}%`, background: 'var(--border-outer)' }}></div>
                    ))}
                  </div>
                  <div className="absolute bottom-2 left-4 right-4 flex justify-between text-[10px] text-gray-500">
                    <span>Dec 28</span>
                    <span>Jan 7</span>
                    <span>Jan 17</span>
                    <span>Jan 27</span>
                  </div>
                </div>
                <div className="grid grid-cols-4 gap-3 mt-3 pt-3 border-t border-[#26292E]">
                  <div className="text-center">
                    <div className="text-lg font-bold text-emerald-400 mono">{formatPL(equityStats.totalPL)}</div>
                    <div className="text-[10px] text-gray-500 mt-0.5">Total P/L</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-white mono">{equityStats.returnPercent >= 0 ? '+' : ''}{equityStats.returnPercent}%</div>
                    <div className="text-[10px] text-gray-500 mt-0.5">Return</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-white mono">{equityStats.sharpeRatio}x</div>
                    <div className="text-[10px] text-gray-500 mt-0.5">Sharpe Ratio</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-red-400 mono">{formatPL(Math.abs(equityStats.maxDrawdown))}</div>
                    <div className="text-[10px] text-gray-500 mt-0.5">Max Drawdown</div>
                  </div>
                </div>
              </div>

              {/* Correlation Matrix */}
              <div className="mt-4 p-3 bg-[#0F1113] border border-[#26292E] rounded-xl">
                <div className="text-[11px] font-semibold text-white uppercase tracking-wider mb-3">
                  Position Correlations
                </div>
                <table className="w-full border-collapse text-[11px]">
                  <thead>
                    <tr>
                      <th className="p-2 text-center border border-[#26292E] bg-[#0F1113] font-semibold text-gray-500"></th>
                      {['TL-2847', 'TL-2846', 'TL-2845', 'TL-2844'].map((tl) => (
                        <th key={tl} className="p-2 text-center border border-[#26292E] bg-[#0F1113] font-semibold text-gray-500">{tl}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {['TL-2847', 'TL-2846', 'TL-2845', 'TL-2844'].map((tl1) => (
                      <tr key={tl1}>
                        <td className="p-2 text-center border border-[#26292E] bg-[#0F1113] font-semibold text-gray-500">{tl1}</td>
                        {['TL-2847', 'TL-2846', 'TL-2845', 'TL-2844'].map((tl2) => {
                          const corr = getCorrelation(tl1, tl2);
                          return (
                            <td key={tl2} className="p-2 text-center border border-[#26292E]" style={{ color: corr >= 0.7 ? 'var(--status-danger)' : corr >= 0.4 ? 'var(--status-warning)' : 'var(--status-success)' }}>
                              {corr.toFixed(2)}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Top Risks Table */}
              <div className="mt-4">
                <div className="text-[11px] font-semibold text-white uppercase tracking-wider mb-3">
                  Top Risks
                </div>
                <table className="w-full border-collapse bg-[#0F1113] border border-[#26292E] rounded-xl overflow-hidden">
                  <thead>
                    <tr>
                      <th className="p-2 text-left text-[9px] font-semibold text-gray-500 uppercase tracking-wider bg-[#0F1113] border-b border-[#26292E]">Timeline</th>
                      <th className="p-2 text-left text-[9px] font-semibold text-gray-500 uppercase tracking-wider bg-[#0F1113] border-b border-[#26292E]">Risk Score</th>
                      <th className="p-2 text-left text-[9px] font-semibold text-gray-500 uppercase tracking-wider bg-[#0F1113] border-b border-[#26292E]">Drivers</th>
                      <th className="p-2 text-left text-[9px] font-semibold text-gray-500 uppercase tracking-wider bg-[#0F1113] border-b border-[#26292E]">Burn at Collapse</th>
                      <th className="p-2 text-right text-[9px] font-semibold text-gray-500 uppercase tracking-wider bg-[#0F1113] border-b border-[#26292E]">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {riskItems.map((item, i) => (
                      <tr key={i} className="border-b border-[#26292E]">
                        <td className="p-2"><span className="text-xs font-semibold text-white mono">{item.timelineId}</span></td>
                        <td className="p-2"><span className="text-xs font-semibold mono" style={{ color: item.riskScore >= 70 ? 'var(--status-danger)' : item.riskScore >= 50 ? '#F59E0B' : 'var(--status-success)' }}>{item.riskScore}</span></td>
                        <td className="p-2"><span className="text-[10px] text-gray-500">{item.drivers}</span></td>
                        <td className="p-2"><span className="text-xs text-red-400 mono">${item.burnAtCollapse.toLocaleString()}</span></td>
                        <td className="p-2">
                          <div className="flex gap-1 justify-end">
                            <button className="px-2 py-1 bg-[#0F1113] border border-[#26292E] rounded text-[10px] font-medium text-gray-400 hover:border-cyan-500/50 hover:text-cyan-400 transition-all cursor-pointer">OPEN</button>
                            <button className="px-2 py-1 bg-[#0F1113] border border-[#26292E] rounded text-[10px] font-medium text-gray-400 hover:border-cyan-500/50 hover:text-cyan-400 transition-all cursor-pointer">REPLAY</button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Recommendations */}
              <div className="py-4">
                <div className="text-[11px] font-semibold text-white uppercase tracking-wider mb-3">
                  Recommendations
                </div>
                <ul className="list-none">
                  {recommendations.map((rec, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-white mb-2">
                      <ChevronRight size={14} className="text-cyan-400 mt-0.5 flex-shrink-0" />
                      {rec.text}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Positions Panel */}
              <div className="flex-1 bg-[#0F1113] border border-[#26292E] rounded-xl flex flex-col mt-4 overflow-hidden">
                <div className="flex items-center justify-between p-3 border-b border-[#26292E]">
                  <div className="flex gap-3">
                    {(['positions', 'foldovers'] as PositionTab[]).map((tab) => (
                      <button
                        key={tab}
                        onClick={() => setPositionTab(tab)}
                        className={`px-3 py-1 rounded-lg text-[11px] font-medium capitalize cursor-pointer transition-all ${positionTab === tab ? 'bg-cyan-500/10 text-cyan-400' : 'text-gray-500 hover:text-gray-300'}`}
                        style={{ background: positionTab === tab ? 'var(--echelon-cyan-bg)' : 'transparent', color: positionTab === tab ? 'var(--echelon-cyan)' : 'var(--text-muted)' }}
                      >
                        {tab}
                      </button>
                    ))}
                  </div>
                  <button className="flex items-center gap-2 px-3 py-2 bg-[#0F1113] border border-[#26292E] rounded-lg text-[11px] font-medium text-gray-400 hover:border-cyan-500/50 hover:text-cyan-400 transition-all cursor-pointer">
                    <Filter size={12} />
                    Filter
                  </button>
                </div>
                <div className="flex-1 overflow-auto">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr>
                        <th className="text-left p-2 text-[9px] font-semibold text-gray-500 uppercase tracking-wider bg-[#0F1113] border-b border-[#26292E] sticky top-0">Timeline</th>
                        <th className="text-left p-2 text-[9px] font-semibold text-gray-500 uppercase tracking-wider bg-[#0F1113] border-b border-[#26292E] sticky top-0">Direction</th>
                        <th className="text-left p-2 text-[9px] font-semibold text-gray-500 uppercase tracking-wider bg-[#0F1113] border-b border-[#26292E] sticky top-0">Entry Price</th>
                        <th className="text-left p-2 text-[9px] font-semibold text-gray-500 uppercase tracking-wider bg-[#0F1113] border-b border-[#26292E] sticky top-0">Current Price</th>
                        <th className="text-left p-2 text-[9px] font-semibold text-gray-500 uppercase tracking-wider bg-[#0F1113] border-b border-[#26292E] sticky top-0">P/L</th>
                        <th className="text-right p-2 text-[9px] font-semibold text-gray-500 uppercase tracking-wider bg-[#0F1113] border-b border-[#26292E] sticky top-0">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {positions.map((position) => (
                        <tr key={position.id} className="border-b border-[#26292E]">
                          <td className="p-2"><span className="text-xs font-semibold text-white mono">{position.timelineId}</span></td>
                          <td className="p-2">
                            <span className="inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold" style={{ background: position.direction === 'YES' ? 'var(--status-success-bg)' : 'var(--status-danger-bg)', color: position.direction === 'YES' ? 'var(--status-success)' : 'var(--status-danger)' }}>
                              {position.direction}
                            </span>
                          </td>
                          <td className="p-2"><span className="text-xs text-white mono">${position.entryPrice.toFixed(2)}</span></td>
                          <td className="p-2"><span className="text-xs text-white mono">${position.currentPrice.toFixed(2)}</span></td>
                          <td className="p-2">
                            <span className="text-xs font-semibold mono" style={{ color: position.pnl >= 0 ? 'var(--status-success)' : 'var(--status-danger)' }}>
                              {position.pnl >= 0 ? '+' : ''}{formatPL(position.pnl)}
                            </span>
                          </td>
                          <td className="p-2">
                            <div className="flex gap-1 justify-end">
                              <button className="px-2 py-1 bg-[#0F1113] border border-[#26292E] rounded text-[10px] font-medium text-gray-400 hover:border-cyan-500/50 hover:text-cyan-400 transition-all cursor-pointer">OPEN</button>
                              <button className="px-2 py-1 bg-[#0F1113] border border-[#26292E] rounded text-[10px] font-medium text-gray-400 hover:border-cyan-500/50 hover:text-cyan-400 transition-all cursor-pointer">REPLAY</button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>

          {/* Right Sidebar */}
          <aside className="w-72 flex-shrink-0 flex flex-col gap-4">
            {/* Ghost Forks Widget */}
            <div className="bg-[#0F1113] border border-[#26292E] rounded-xl">
              <div className="flex items-center justify-between px-3 py-2 border-b border-[#26292E]">
                <span className="text-[11px] font-semibold text-white uppercase tracking-wider">Ghost Forks</span>
                <button onClick={() => setShowForksPanel(true)} className="px-2 py-1 bg-[#0F1113] border border-[#26292E] rounded text-[10px] font-medium text-gray-400 hover:border-cyan-500/50 hover:text-cyan-400 transition-all cursor-pointer">VIEW ALL</button>
              </div>
              <div className="p-3">
                {ghostForks.map((fork, i) => (
                  <div key={i} className="flex items-center justify-between py-2" style={{ borderBottom: i < ghostForks.length - 1 ? '1px solid var(--border-outer)' : 'none' }}>
                    <span className="text-[11px] text-white mono">{fork.id}</span>
                    <span className="text-[10px] text-gray-500">{fork.timeAgo}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* My Agents Widget */}
            <div className="bg-[#0F1113] border border-[#26292E] rounded-xl">
              <div className="flex items-center justify-between px-3 py-2 border-b border-[#26292E]">
                <span className="text-[11px] font-semibold text-white uppercase tracking-wider">My Agents</span>
                <button onClick={() => setShowAgentsPanel(true)} className="px-2 py-1 bg-[#0F1113] border border-[#26292E] rounded text-[10px] font-medium text-gray-400 hover:border-cyan-500/50 hover:text-cyan-400 transition-all cursor-pointer">MANAGE</button>
              </div>
              <div className="p-3">
                {agents.slice(0, 4).map((agent, i) => (
                  <div key={i} className="flex items-center gap-2 py-2" style={{ borderBottom: i < 3 ? '1px solid var(--border-outer)' : 'none' }}>
                    <div className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white" style={{ background: agent.color }}>{agent.name.charAt(6)}</div>
                    <span className="text-xs text-white flex-1">{agent.name}</span>
                    <span className="text-[9px] text-gray-500 px-1.5 py-0.5 bg-[#0F1113] rounded">{agent.archetype}</span>
                    <span className="text-xs font-semibold mono" style={{ color: agent.pnl >= 0 ? 'var(--status-success)' : 'var(--status-danger)' }}>{agent.pnl >= 0 ? '+' : ''}${Math.abs(agent.pnl / 1000).toFixed(1)}K</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Stats Row */}
            <div className="flex gap-3">
              <div className="flex-1 text-center p-3 bg-[#0F1113] border border-[#26292E] rounded-xl">
                <div className="text-xl font-bold text-white mono">{agents.length}</div>
                <div className="text-[10px] text-gray-500 mt-0.5">Live Agents</div>
              </div>
              <div className="flex-1 text-center p-3 bg-[#0F1113] border border-[#26292E] rounded-xl">
                <div className="text-xl font-bold text-white mono">{agents.reduce((sum, a) => sum + a.actions, 0).toLocaleString()}</div>
                <div className="text-[10px] text-gray-500 mt-0.5">Active Ops</div>
              </div>
            </div>
          </aside>
        </div>
      </main>

      {/* Backdrop */}
      {(showAgentsPanel || showForksPanel) && (
        <div 
          className="backdrop active"
          onClick={closeAllPanels}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 1400, opacity: 0, visibility: 'visible', transition: 'all 0.3s' }}
        />
      )}

      {/* AGENTS PANEL */}
      <div
        className={`side-panel ${showAgentsPanel ? 'active' : ''}`}
        style={{ position: 'fixed', top: 0, right: showAgentsPanel ? 0 : -420, bottom: 0, width: 420, background: 'var(--bg-panel)', borderLeft: '1px solid var(--border-outer)', zIndex: 1500, transition: 'right 0.3s ease', display: 'flex', flexDirection: 'column' }}
      >
        <div className="flex items-center justify-between p-4 border-b border-[#26292E] flex-shrink-0">
          <div className="text-sm font-semibold text-white flex items-center gap-2">
            <Bot size={18} className="text-cyan-400" />
            Manage Agents
          </div>
          <button onClick={() => setShowAgentsPanel(false)} className="w-8 h-8 flex items-center justify-center bg-[#0F1113] border border-[#26292E] rounded-lg text-gray-500 cursor-pointer transition-all hover:text-white">
            <X size={14} />
          </button>
        </div>
        <div className="flex-1 overflow-auto p-4">
          <div className="grid grid-cols-2 gap-3">
            {agents.map((agent, i) => (
              <div key={i} className="bg-[#0F1113] border border-[#26292E] rounded-xl p-3">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white" style={{ background: agent.color }}>{agent.name.charAt(6)}</div>
                  <div className="flex-1">
                    <div className="text-xs font-semibold text-white">{agent.name}</div>
                    <div className="text-[10px] text-gray-500 uppercase">{agent.archetype}</div>
                  </div>
                  <span className="text-sm font-semibold mono" style={{ color: agent.pnl >= 0 ? 'var(--status-success)' : 'var(--status-danger)' }}>{agent.pnl >= 0 ? '+' : ''}${Math.abs(agent.pnl).toLocaleString()}</span>
                </div>
                <div className="h-10 mt-2 relative">
                  <svg viewBox="0 0 100 40" className="w-full h-full">
                    <path
                      d={agent.pnl >= 0
                        ? "M0,30 L10,28 L20,25 L30,22 L40,20 L50,18 L60,15 L70,12 L80,10 L90,8 L100,5"
                        : "M0,15 L10,18 L20,22 L30,20 L40,25 L50,22 L60,28 L70,25 L80,30 L90,28 L100,32"
                      }
                      fill="none"
                      stroke={agent.pnl >= 0 ? 'var(--status-success)' : 'var(--status-danger)'}
                      strokeWidth="1.5"
                      strokeLinecap="round"
                    />
                  </svg>
                </div>
                <div className="flex justify-between mt-2 text-[10px] text-gray-500">
                  <span>Actions: {agent.actions.toLocaleString()}</span>
                  <span>Win: {agent.winRate}%</span>
                  <span>Sanity: {agent.sanity}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* FORKS PANEL */}
      <div
        className={`side-panel ${showForksPanel ? 'active' : ''}`}
        style={{ position: 'fixed', top: 0, right: showForksPanel ? 0 : -420, bottom: 0, width: 420, background: 'var(--bg-panel)', borderLeft: '1px solid var(--border-outer)', zIndex: 1500, transition: 'right 0.3s ease', display: 'flex', flexDirection: 'column' }}
      >
        <div className="flex items-center justify-between p-4 border-b border-[#26292E] flex-shrink-0">
          <div className="text-sm font-semibold text-white flex items-center gap-2">
            <GitBranch size={18} className="text-cyan-400" />
            Ghost Forks
          </div>
          <button onClick={() => setShowForksPanel(false)} className="w-8 h-8 flex items-center justify-center bg-[#0F1113] border border-[#26292E] rounded-lg text-gray-500 cursor-pointer transition-all hover:text-white">
            <X size={14} />
          </button>
        </div>
        <div className="flex-1 overflow-auto p-4">
          <div className="flex flex-col gap-2">
            {forkDetails.map((fork, i) => (
              <div key={i} className="bg-[#0F1113] border border-[#26292E] rounded-xl p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-white mono">{fork.id}</span>
                  <span className="text-[10px] text-gray-500">{fork.timeAgo}</span>
                </div>
                <div className="grid grid-cols-3 gap-3 mt-2">
                  <div className="text-center">
                    <div className="text-sm font-semibold text-white mono">{fork.probability}%</div>
                    <div className="text-[9px] text-gray-500 uppercase tracking-wider">Probability</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm font-semibold text-white mono">{fork.forks}</div>
                    <div className="text-[9px] text-gray-500 uppercase tracking-wider">Forks</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm font-semibold text-white mono">${(fork.volume / 1000).toFixed(0)}K</div>
                    <div className="text-[9px] text-gray-500 uppercase tracking-wider">Volume</div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Founders Yield */}
          <div className="mt-6 pt-6 border-t border-[#26292E]">
            <div className="flex items-center justify-between mb-3">
              <div className="text-xs font-semibold text-white uppercase tracking-wider flex items-center gap-2">
                <Star size={14} className="text-cyan-400" />
                Founders Yield
              </div>
              <div className="text-xl font-bold text-emerald-400 mono">+${yieldBreakdown.total.toLocaleString()}</div>
            </div>
            <div className="grid grid-cols-4 gap-2">
              <div className="bg-[#0F1113] border border-[#26292E] rounded-lg p-2 text-center">
                <div className="text-sm font-semibold text-white mono">${yieldBreakdown.trading.toLocaleString()}</div>
                <div className="text-[9px] text-gray-500 uppercase mt-1">Trading</div>
              </div>
              <div className="bg-[#0F1113] border border-[#26292E] rounded-lg p-2 text-center">
                <div className="text-sm font-semibold text-white mono">${yieldBreakdown.MEV.toLocaleString()}</div>
                <div className="text-[9px] text-gray-500 uppercase mt-1">MEV</div>
              </div>
              <div className="bg-[#0F1113] border border-[#26292E] rounded-lg p-2 text-center">
                <div className="text-sm font-semibold text-white mono">${yieldBreakdown.bribes.toLocaleString()}</div>
                <div className="text-[9px] text-gray-500 uppercase mt-1">Bribes</div>
              </div>
              <div className="bg-[#0F1113] border border-[#26292E] rounded-lg p-2 text-center">
                <div className="text-sm font-semibold text-white mono">${yieldBreakdown.total.toLocaleString()}</div>
                <div className="text-[9px] text-gray-500 uppercase mt-1">Total</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* CSS Animations */}
      <style>{`
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.5; }
          100% { opacity: 1; }
        }
      `}</style>
    </div>
  );
}
