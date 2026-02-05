// Portfolio Page Component
// Portfolio overview with risk metrics, positions, and performance

import { useState } from 'react';
import {
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
  usePortfolioStatus();
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
    if (!equityData || equityData.length === 0) {
      // Fallback mock data for visualization
      const fallbackData = Array.from({ length: 30 }, (_, i) => ({
        value: 100000 + (i * 500) + (Math.random() - 0.4) * 3000,
      }));
      const minValue = Math.min(...fallbackData.map(d => d.value));
      const maxValue = Math.max(...fallbackData.map(d => d.value));
      const range = maxValue - minValue || 1;
      const width = 100;
      const height = 80;
      const padding = 10;

      const points = fallbackData.map((d, i) => {
        const x = (i / (fallbackData.length - 1)) * width;
        const y = height - padding - ((d.value - minValue) / range) * (height - padding * 2);
        return { x, y };
      });

      const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
      const areaPath = `${linePath} L ${width} ${height} L 0 ${height} Z`;

      return { area: areaPath, line: linePath };
    }

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
    <div className="min-h-screen flex flex-col bg-slate-950 text-terminal-text">
      {/* Main Content */}
      <main className="flex-1 flex flex-col min-h-0 overflow-hidden">
        {/* Content */}
        <div className="flex-1 flex gap-4 p-4 overflow-hidden">
          {/* Left Column - Scrollable with Main Panel Inside */}
          <div className="flex-1 min-h-0 overflow-y-auto pr-6">
            {/* Main Panel */}
            <div className="bg-slate-950 border border-terminal-border rounded-2xl flex flex-col overflow-hidden">
            {/* Header */}
            <div className="px-4 py-4 border-b border-terminal-border">
              <div className="text-sm font-semibold text-terminal-text mb-1">
                Portfolio Overview
              </div>
              <div className="text-xs text-terminal-text-muted">
                Portfolio risk metrics, positions, and performance data
              </div>
            </div>

            {/* Top Metrics */}
            <div className="grid grid-cols-3 gap-3 p-4">
              <div className="bg-slate-950 border border-terminal-border rounded-xl p-3">
                <div className="text-[10px] font-semibold text-terminal-text-muted uppercase tracking-wider mb-1">
                  Total P/L
                </div>
                <div className="text-2xl font-bold text-status-success mono">
                  +${totals.totalPL.toLocaleString()}
                </div>
              </div>
              <div className="bg-slate-950 border border-terminal-border rounded-xl p-3">
                <div className="text-[10px] font-semibold text-terminal-text-muted uppercase tracking-wider mb-1">
                  Win Rate
                </div>
                <div className="text-2xl font-bold text-terminal-text mono">
                  {totals.winRate.toFixed(0)}%
                </div>
              </div>
              <div className="bg-slate-950 border border-terminal-border rounded-xl p-3">
                <div className="text-[10px] font-semibold text-terminal-text-muted uppercase tracking-wider mb-1">
                  Positions
                </div>
                <div className="text-2xl font-bold text-terminal-text mono">
                  {positions.length}
                </div>
              </div>
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-auto px-4 pb-4">
              {/* KPI Tiles */}
              <div className="mt-4">
                <div className="text-[11px] font-semibold text-terminal-text uppercase tracking-wider mb-3">
                  Risk Metrics
                </div>
                <div className="grid grid-cols-4 gap-3">
                  {riskMetrics.map((metric, i) => (
                    <div key={i} className="bg-slate-950 border border-terminal-border rounded-xl p-3">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[11px] text-terminal-text-secondary">{metric.label}</span>
                        <span className="text-sm" style={{ color: metric.level === 'low' ? '#4ADE80' : metric.level === 'medium' ? '#F59E0B' : '#FB7185' }}>
                          {metric.icon === 'ri-dashboard-3-line' && <BarChart3 size={14} />}
                          {metric.icon === 'ri-bar-chart-box-line' && <Activity size={14} />}
                          {metric.icon === 'ri-trending-up-line' && <TrendingUp size={14} />}
                          {metric.icon === 'ri-error-warning-line' && <AlertTriangle size={14}/>}
                        </span>
                      </div>
                      <div className="text-[28px] font-bold leading-tight" style={{ color: metric.level === 'low' ? '#4ADE80' : metric.level === 'medium' ? '#F59E0B' : '#FB7185' }}>
                        {metric.value}
                      </div>
                      <div className="text-[11px] text-terminal-text-muted mono">/ {metric.max}</div>
                      <div className="mt-2">
                        <div className="h-1 bg-slate-950 rounded overflow-hidden mb-1">
                          <div className="h-full rounded transition-all" style={{ width: `${metric.value}%`, background: metric.level === 'low' ? '#4ADE80' : metric.level === 'medium' ? '#FACC15' : '#FB7185' }}></div>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded" style={{ background: metric.level === 'low' ? 'rgba(74,222,128,0.1)' : metric.level === 'medium' ? 'rgba(250,204,21,0.1)' : 'rgba(251,113,133,0.1)', color: metric.level === 'low' ? '#4ADE80' : metric.level === 'medium' ? '#FACC15' : '#FB7185' }}>
                            {metric.level.toUpperCase()}
                          </span>
                          <span className="text-[9px] text-terminal-text-muted">{metric.value}%</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Exposure Summary */}
              <div className="mt-4 p-3 bg-slate-950 border border-terminal-border rounded-xl">
                <div className="text-[11px] font-semibold text-terminal-text uppercase tracking-wider mb-3">
                  Exposure Summary
                </div>
                <div className="mb-3">
                  <div className="flex justify-between mb-1">
                    <span className="text-[11px] text-terminal-text-secondary">Total Notional</span>
                    <span className="text-xs font-semibold text-terminal-text mono">${totals.totalNotional.toLocaleString()}.00</span>
                  </div>
                </div>
                <div className="mb-3">
                  <div className="flex justify-between mb-1">
                    <span className="text-[11px] text-terminal-text-secondary">Net YES Notional</span>
                    <span className="text-xs font-semibold text-status-success mono">${totals.yesNotional.toLocaleString()}.00</span>
                  </div>
                  <div className="h-1.5 bg-slate-950 rounded overflow-hidden">
                    <div className="h-full bg-status-success" style={{ width: `${allocationTotals.yesTotal}%` }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-[11px] text-terminal-text-secondary">Net NO Notional</span>
                    <span className="text-xs font-semibold text-status-danger mono">${totals.noNotional.toLocaleString()}.00</span>
                  </div>
                  <div className="h-1.5 bg-slate-950 rounded overflow-hidden">
                    <div className="h-full bg-status-danger" style={{ width: `${allocationTotals.noTotal}%` }}></div>
                  </div>
                </div>
              </div>

              {/* Portfolio Allocation */}
              <div className="mt-4 p-3 bg-slate-950 border border-terminal-border rounded-xl">
                <div className="text-[11px] font-semibold text-terminal-text uppercase tracking-wider mb-3">
                  Portfolio Allocation
                </div>
                {allocations.map((allocation, i) => (
                  <div key={i} className="flex items-center gap-3 mb-2">
                    <span className="text-[11px] text-terminal-text mono w-20">{allocation.timelineId} ({allocation.direction})</span>
                    <div className="flex-1 h-2 bg-slate-950 rounded overflow-hidden">
                      <div className="h-full rounded" style={{ width: `${allocation.percent}%`, background: allocation.direction === 'YES' ? '#4ADE80' : '#FB7185' }}></div>
                    </div>
                    <span className="text-[11px] text-terminal-text-muted mono w-10 text-right">{allocation.percent}%</span>
                  </div>
                ))}
              </div>

              {/* Equity Curve */}
              <div className="mt-4 p-3 bg-slate-950 border border-terminal-border rounded-xl">
                <div className="flex justify-between items-center mb-3">
                  <div className="text-[11px] font-semibold text-terminal-text uppercase tracking-wider">Equity Curve (30D)</div>
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
                <div className="relative h-[120px] bg-slate-950 rounded-lg overflow-hidden">
                  <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-0 w-full h-full">
                    <defs>
                      <linearGradient id="equityGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stopColor="#10B981" stopOpacity="0.4"/>
                        <stop offset="100%" stopColor="#10B981" stopOpacity="0"/>
                      </linearGradient>
                    </defs>
                    <path d={equityAreaPath} fill="url(#equityGradient)"/>
                    <path d={equityLinePath} fill="none" stroke="#10B981" strokeWidth="1" strokeLinecap="round"/>
                  </svg>
                  <div className="absolute inset-0">
                    {[0, 25, 50, 75].map((pct) => (
                      <div key={pct} className="absolute left-0 right-0 h-px" style={{ top: `${pct}%`, background: 'rgba(255,255,255,0.1)' }}></div>
                    ))}
                  </div>
                  <div className="absolute bottom-2 left-4 right-4 flex justify-between text-[10px] text-terminal-text-muted">
                    <span>Dec 28</span>
                    <span>Jan 7</span>
                    <span>Jan 17</span>
                    <span>Jan 27</span>
                  </div>
                </div>
                <div className="grid grid-cols-4 gap-3 mt-3 pt-3 border-t border-terminal-border">
                  <div className="text-center">
                    <div className="text-lg font-bold text-status-success mono">{formatPL(equityStats.totalPL)}</div>
                    <div className="text-[10px] text-terminal-text-muted mt-0.5">Total P/L</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-terminal-text mono">{equityStats.returnPercent >= 0 ? '+' : ''}{equityStats.returnPercent}%</div>
                    <div className="text-[10px] text-terminal-text-muted mt-0.5">Return</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-terminal-text mono">{equityStats.sharpeRatio}x</div>
                    <div className="text-[10px] text-terminal-text-muted mt-0.5">Sharpe Ratio</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-status-danger mono">{formatPL(Math.abs(equityStats.maxDrawdown))}</div>
                    <div className="text-[10px] text-terminal-text-muted mt-0.5">Max Drawdown</div>
                  </div>
                </div>
              </div>

              {/* Correlation Matrix */}
              <div className="mt-4 p-3 bg-slate-950 border border-terminal-border rounded-xl">
                <div className="text-[11px] font-semibold text-terminal-text uppercase tracking-wider mb-3">
                  Position Correlations
                </div>
                <table className="w-full border-collapse text-[11px]">
                  <thead>
                    <tr>
                      <th className="p-2 text-center border border-terminal-border bg-slate-950 font-semibold text-terminal-text-muted"></th>
                      {['TL-2847', 'TL-2846', 'TL-2845', 'TL-2844'].map((tl) => (
                        <th key={tl} className="p-2 text-center border border-terminal-border bg-slate-950 font-semibold text-terminal-text-muted">{tl}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {['TL-2847', 'TL-2846', 'TL-2845', 'TL-2844'].map((tl1) => (
                      <tr key={tl1}>
                        <td className="p-2 text-center border border-terminal-border bg-slate-950 font-semibold text-terminal-text-muted">{tl1}</td>
                        {['TL-2847', 'TL-2846', 'TL-2845', 'TL-2844'].map((tl2) => {
                          const corr = getCorrelation(tl1, tl2);
                          return (
                            <td key={tl2} className="p-2 text-center border border-terminal-border" style={{ color: corr >= 0.7 ? '#FB7185' : corr >= 0.4 ? '#FACC15' : '#4ADE80' }}>
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
                <div className="text-[11px] font-semibold text-terminal-text uppercase tracking-wider mb-3">
                  Top Risks
                </div>
                <table className="w-full border-collapse bg-slate-950 border border-terminal-border rounded-xl overflow-hidden">
                  <thead>
                    <tr>
                      <th className="p-2 text-left text-[9px] font-semibold text-terminal-text-muted uppercase tracking-wider bg-slate-950 border-b border-terminal-border">Timeline</th>
                      <th className="p-2 text-left text-[9px] font-semibold text-terminal-text-muted uppercase tracking-wider bg-slate-950 border-b border-terminal-border">Risk Score</th>
                      <th className="p-2 text-left text-[9px] font-semibold text-terminal-text-muted uppercase tracking-wider bg-slate-950 border-b border-terminal-border">Drivers</th>
                      <th className="p-2 text-left text-[9px] font-semibold text-terminal-text-muted uppercase tracking-wider bg-slate-950 border-b border-terminal-border">Burn at Collapse</th>
                      <th className="p-2 text-right text-[9px] font-semibold text-terminal-text-muted uppercase tracking-wider bg-slate-950 border-b border-terminal-border">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {riskItems.map((item, i) => (
                      <tr key={i} className="border-b border-terminal-border">
                        <td className="p-2"><span className="text-xs font-semibold text-terminal-text mono">{item.timelineId}</span></td>
                        <td className="p-2"><span className="text-xs font-semibold mono" style={{ color: item.riskScore >= 70 ? '#FB7185' : item.riskScore >= 50 ? '#F59E0B' : '#4ADE80' }}>{item.riskScore}</span></td>
                        <td className="p-2"><span className="text-[10px] text-terminal-text-muted">{item.drivers}</span></td>
                        <td className="p-2"><span className="text-xs text-status-danger mono">${item.burnAtCollapse.toLocaleString()}</span></td>
                        <td className="p-2">
                          <div className="flex gap-1 justify-end">
                            <button className="px-2 py-1 bg-slate-950 border border-terminal-border rounded text-[10px] font-medium text-terminal-text-secondary hover:border-echelon-cyan/50 hover:text-echelon-cyan transition-all cursor-pointer">OPEN</button>
                            <button className="px-2 py-1 bg-slate-950 border border-terminal-border rounded text-[10px] font-medium text-terminal-text-secondary hover:border-echelon-cyan/50 hover:text-echelon-cyan transition-all cursor-pointer">REPLAY</button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Recommendations */}
              <div className="py-4">
                <div className="text-[11px] font-semibold text-terminal-text uppercase tracking-wider mb-3">
                  Recommendations
                </div>
                <ul className="list-none">
                  {recommendations.map((rec, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-terminal-text mb-2">
                      <ChevronRight size={14} className="text-echelon-cyan mt-0.5 flex-shrink-0" />
                      {rec.text}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Positions Panel */}
              <div className="flex-1 bg-slate-950 border border-terminal-border rounded-xl flex flex-col mt-4 overflow-hidden">
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
                  <button className="flex items-center gap-2 px-3 py-2 bg-slate-950 border border-terminal-border rounded-lg text-[11px] font-medium text-terminal-text-secondary hover:border-echelon-cyan/50 hover:text-echelon-cyan transition-all cursor-pointer">
                    <Filter size={12} />
                    Filter
                  </button>
                </div>
                <div className="flex-1 overflow-auto">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr>
                        <th className="text-left p-2 text-[9px] font-semibold text-terminal-text-muted uppercase tracking-wider bg-slate-950 border-b border-terminal-border sticky top-0">Timeline</th>
                        <th className="text-left p-2 text-[9px] font-semibold text-terminal-text-muted uppercase tracking-wider bg-slate-950 border-b border-terminal-border sticky top-0">Direction</th>
                        <th className="text-left p-2 text-[9px] font-semibold text-terminal-text-muted uppercase tracking-wider bg-slate-950 border-b border-terminal-border sticky top-0">Entry Price</th>
                        <th className="text-left p-2 text-[9px] font-semibold text-terminal-text-muted uppercase tracking-wider bg-slate-950 border-b border-terminal-border sticky top-0">Current Price</th>
                        <th className="text-left p-2 text-[9px] font-semibold text-terminal-text-muted uppercase tracking-wider bg-slate-950 border-b border-terminal-border sticky top-0">P/L</th>
                        <th className="text-right p-2 text-[9px] font-semibold text-terminal-text-muted uppercase tracking-wider bg-slate-950 border-b border-terminal-border sticky top-0">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {positions.map((position) => (
                        <tr key={position.id} className="border-b border-terminal-border">
                          <td className="p-2"><span className="text-xs font-semibold text-terminal-text mono">{position.timelineId}</span></td>
                          <td className="p-2">
                            <span className="inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold" style={{ background: position.direction === 'YES' ? 'rgba(74,222,128,0.1)' : 'rgba(251,113,133,0.1)', color: position.direction === 'YES' ? '#4ADE80' : '#FB7185' }}>
                              {position.direction}
                            </span>
                          </td>
                          <td className="p-2"><span className="text-xs text-terminal-text mono">${position.entryPrice.toFixed(2)}</span></td>
                          <td className="p-2"><span className="text-xs text-terminal-text mono">${position.currentPrice.toFixed(2)}</span></td>
                          <td className="p-2">
                            <span className="text-xs font-semibold mono" style={{ color: position.pnl >= 0 ? '#4ADE80' : '#FB7185' }}>
                              {position.pnl >= 0 ? '+' : ''}{formatPL(position.pnl)}
                            </span>
                          </td>
                          <td className="p-2">
                            <div className="flex gap-1 justify-end">
                              <button className="px-2 py-1 bg-slate-950 border border-terminal-border rounded text-[10px] font-medium text-terminal-text-secondary hover:border-echelon-cyan/50 hover:text-echelon-cyan transition-all cursor-pointer">OPEN</button>
                              <button className="px-2 py-1 bg-slate-950 border border-terminal-border rounded text-[10px] font-medium text-terminal-text-secondary hover:border-echelon-cyan/50 hover:text-echelon-cyan transition-all cursor-pointer">REPLAY</button>
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
            {/* End Main Panel and Left Scrollable Column */}
          </div>

          {/* Right Fixed Sidebar */}
          <aside className="w-[360px] flex-shrink-0 flex flex-col gap-4 self-start sticky top-6">
            {/* Ghost Forks Widget */}
            <div className="bg-slate-950 border border-terminal-border rounded-xl">
              <div className="flex items-center justify-between px-3 py-2 border-b border-terminal-border">
                <span className="text-[11px] font-semibold text-terminal-text uppercase tracking-wider">Ghost Forks</span>
                <button onClick={() => setShowForksPanel(true)} className="px-2 py-1 bg-slate-950 border border-terminal-border rounded text-[10px] font-medium text-terminal-text-secondary hover:border-echelon-cyan/50 hover:text-echelon-cyan transition-all cursor-pointer">VIEW ALL</button>
              </div>
              <div className="p-3">
                {ghostForks.map((fork, i) => (
                  <div key={i} className="flex items-center justify-between py-2" style={{ borderBottom: i < ghostForks.length - 1 ? '1px solid rgba(255,255,255,0.1)' : 'none' }}>
                    <span className="text-[11px] text-terminal-text mono">{fork.id}</span>
                    <span className="text-[10px] text-terminal-text-muted">{fork.timeAgo}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* My Agents Widget */}
            <div className="bg-slate-950 border border-terminal-border rounded-xl">
              <div className="flex items-center justify-between px-3 py-2 border-b border-terminal-border">
                <span className="text-[11px] font-semibold text-terminal-text uppercase tracking-wider">My Agents</span>
                <button onClick={() => setShowAgentsPanel(true)} className="px-2 py-1 bg-slate-950 border border-terminal-border rounded text-[10px] font-medium text-terminal-text-secondary hover:border-echelon-cyan/50 hover:text-echelon-cyan transition-all cursor-pointer">MANAGE</button>
              </div>
              <div className="p-3">
                {agents.slice(0, 4).map((agent, i) => (
                  <div key={i} className="flex items-center gap-2 py-2" style={{ borderBottom: i < 3 ? '1px solid rgba(255,255,255,0.1)' : 'none' }}>
                    <div className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white" style={{ background: agent.color }}>{agent.name.charAt(6)}</div>
                    <span className="text-xs text-terminal-text flex-1">{agent.name}</span>
                    <span className="text-[9px] text-terminal-text-muted px-1.5 py-0.5 bg-slate-950 rounded">{agent.archetype}</span>
                    <span className="text-xs font-semibold mono" style={{ color: agent.pnl >= 0 ? '#4ADE80' : '#FB7185' }}>{agent.pnl >= 0 ? '+' : ''}${Math.abs(agent.pnl / 1000).toFixed(1)}K</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Stats Row */}
            <div className="flex gap-3">
              <div className="flex-1 text-center p-3 bg-slate-950 border border-terminal-border rounded-xl">
                <div className="text-xl font-bold text-terminal-text mono">{agents.length}</div>
                <div className="text-[10px] text-terminal-text-muted mt-0.5">Live Agents</div>
              </div>
              <div className="flex-1 text-center p-3 bg-slate-950 border border-terminal-border rounded-xl">
                <div className="text-xl font-bold text-terminal-text mono">{agents.reduce((sum, a) => sum + a.actions, 0).toLocaleString()}</div>
                <div className="text-[10px] text-terminal-text-muted mt-0.5">Active Ops</div>
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
        style={{ position: 'fixed', top: 0, right: showAgentsPanel ? 0 : -420, bottom: 0, width: 420, background: '#151719', borderLeft: '1px solid rgba(255,255,255,0.1)', zIndex: 1500, transition: 'right 0.3s ease', display: 'flex', flexDirection: 'column' }}
      >
        <div className="flex items-center justify-between p-4 border-b border-terminal-border flex-shrink-0">
          <div className="text-sm font-semibold text-terminal-text flex items-center gap-2">
            <Bot size={18} className="text-echelon-cyan" />
            Manage Agents
          </div>
          <button onClick={() => setShowAgentsPanel(false)} className="w-8 h-8 flex items-center justify-center bg-slate-950 border border-terminal-border rounded-lg text-terminal-text-muted cursor-pointer transition-all hover:text-terminal-text">
            <X size={14} />
          </button>
        </div>
        <div className="flex-1 overflow-auto p-4">
          <div className="grid grid-cols-2 gap-3">
            {agents.map((agent, i) => (
              <div key={i} className="bg-slate-950 border border-terminal-border rounded-xl p-3">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white" style={{ background: agent.color }}>{agent.name.charAt(6)}</div>
                  <div className="flex-1">
                    <div className="text-xs font-semibold text-terminal-text">{agent.name}</div>
                    <div className="text-[10px] text-terminal-text-muted uppercase">{agent.archetype}</div>
                  </div>
                  <span className="text-sm font-semibold mono" style={{ color: agent.pnl >= 0 ? '#4ADE80' : '#FB7185' }}>{agent.pnl >= 0 ? '+' : ''}${Math.abs(agent.pnl).toLocaleString()}</span>
                </div>
                <div className="h-10 mt-2 relative">
                  <svg viewBox="0 0 100 40" className="w-full h-full">
                    <path
                      d={agent.pnl >= 0
                        ? "M0,30 L10,28 L20,25 L30,22 L40,20 L50,18 L60,15 L70,12 L80,10 L90,8 L100,5"
                        : "M0,15 L10,18 L20,22 L30,20 L40,25 L50,22 L60,28 L70,25 L80,30 L90,28 L100,32"
                      }
                      fill="none"
                      stroke={agent.pnl >= 0 ? '#4ADE80' : '#FB7185'}
                      strokeWidth="1.5"
                      strokeLinecap="round"
                    />
                  </svg>
                </div>
                <div className="flex justify-between mt-2 text-[10px] text-terminal-text-muted">
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
        style={{ position: 'fixed', top: 0, right: showForksPanel ? 0 : -420, bottom: 0, width: 420, background: '#151719', borderLeft: '1px solid rgba(255,255,255,0.1)', zIndex: 1500, transition: 'right 0.3s ease', display: 'flex', flexDirection: 'column' }}
      >
        <div className="flex items-center justify-between p-4 border-b border-terminal-border flex-shrink-0">
          <div className="text-sm font-semibold text-terminal-text flex items-center gap-2">
            <GitBranch size={18} className="text-echelon-cyan" />
            Ghost Forks
          </div>
          <button onClick={() => setShowForksPanel(false)} className="w-8 h-8 flex items-center justify-center bg-slate-950 border border-terminal-border rounded-lg text-terminal-text-muted cursor-pointer transition-all hover:text-terminal-text">
            <X size={14} />
          </button>
        </div>
        <div className="flex-1 overflow-auto p-4">
          <div className="flex flex-col gap-2">
            {forkDetails.map((fork, i) => (
              <div key={i} className="bg-slate-950 border border-terminal-border rounded-xl p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-terminal-text mono">{fork.id}</span>
                  <span className="text-[10px] text-terminal-text-muted">{fork.timeAgo}</span>
                </div>
                <div className="grid grid-cols-3 gap-3 mt-2">
                  <div className="text-center">
                    <div className="text-sm font-semibold text-terminal-text mono">{fork.probability}%</div>
                    <div className="text-[9px] text-terminal-text-muted uppercase tracking-wider">Probability</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm font-semibold text-terminal-text mono">{fork.forks}</div>
                    <div className="text-[9px] text-terminal-text-muted uppercase tracking-wider">Forks</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm font-semibold text-terminal-text mono">${(fork.volume / 1000).toFixed(0)}K</div>
                    <div className="text-[9px] text-terminal-text-muted uppercase tracking-wider">Volume</div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Founders Yield */}
          <div className="mt-6 pt-6 border-t border-terminal-border">
            <div className="flex items-center justify-between mb-3">
              <div className="text-xs font-semibold text-terminal-text uppercase tracking-wider flex items-center gap-2">
                <Star size={14} className="text-echelon-cyan" />
                Founders Yield
              </div>
              <div className="text-xl font-bold text-status-success mono">+${yieldBreakdown.total.toLocaleString()}</div>
            </div>
            <div className="grid grid-cols-4 gap-2">
              <div className="bg-slate-950 border border-terminal-border rounded-lg p-2 text-center">
                <div className="text-sm font-semibold text-terminal-text mono">${yieldBreakdown.trading.toLocaleString()}</div>
                <div className="text-[9px] text-terminal-text-muted uppercase mt-1">Trading</div>
              </div>
              <div className="bg-slate-950 border border-terminal-border rounded-lg p-2 text-center">
                <div className="text-sm font-semibold text-terminal-text mono">${yieldBreakdown.MEV.toLocaleString()}</div>
                <div className="text-[9px] text-terminal-text-muted uppercase mt-1">MEV</div>
              </div>
              <div className="bg-slate-950 border border-terminal-border rounded-lg p-2 text-center">
                <div className="text-sm font-semibold text-terminal-text mono">${yieldBreakdown.bribes.toLocaleString()}</div>
                <div className="text-[9px] text-terminal-text-muted uppercase mt-1">Bribes</div>
              </div>
              <div className="bg-slate-950 border border-terminal-border rounded-lg p-2 text-center">
                <div className="text-sm font-semibold text-terminal-text mono">${yieldBreakdown.total.toLocaleString()}</div>
                <div className="text-[9px] text-terminal-text-muted uppercase mt-1">Total</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
