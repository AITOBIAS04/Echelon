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
    <div className="app-layout" style={{ minHeight: '100vh', display: 'flex', background: 'var(--bg-app)', position: 'relative' }}>
      {/* Main Content */}
      <main className="main-content" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Header */}
        <header className="header" style={{ height: 64, background: 'var(--bg-panel)', borderBottom: '1px solid var(--border-outer)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 24px', flexShrink: 0 }}>
          <div className="page-title" style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '0.02em' }}>
            Portfolio
          </div>
          <div className="header-right" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <button className="header-btn" style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px', background: 'var(--bg-card)', border: '1px solid var(--border-outer)', borderRadius: 6, color: 'var(--text-secondary)', fontSize: 12, fontWeight: 500, cursor: 'pointer', transition: 'all 0.2s' }}>
              <Plus size={14} />
              New Position
            </button>
            <div className="connection-status" style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, fontWeight: 600, color: 'var(--status-success)', background: 'rgba(74, 222, 128, 0.1)', padding: '4px 10px', borderRadius: 20, border: '1px solid rgba(74, 222, 128, 0.2)' }}>
              <span className="live-dot" style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--status-success)', animation: 'pulse 2s infinite' }}></span>
              Connected
            </div>
            <span className="clock mono" style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{clock}</span>
          </div>
        </header>

        {/* Content */}
        <div className="content-area" style={{ flex: 1, padding: 16, display: 'flex', gap: 16, overflow: 'hidden' }}>
          {/* Main Panel */}
          <div className="main-panel" style={{ flex: 1, background: 'var(--bg-card)', border: '1px solid var(--border-outer)', borderRadius: 8, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            {/* Header */}
            <div className="main-panel-header" style={{ padding: 16, borderBottom: '1px solid var(--border-outer)' }}>
              <div className="main-panel-title" style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
                Portfolio Overview
              </div>
              <div className="main-panel-subtitle" style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                Portfolio risk metrics, positions, and performance data
              </div>
            </div>

            {/* Top Metrics */}
            <div className="metrics-row" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, padding: 16 }}>
              <div className="metric-card" style={{ background: 'var(--bg-app)', border: '1px solid var(--border-outer)', borderRadius: 6, padding: 12 }}>
                <div className="metric-label" style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>
                  Total P/L
                </div>
                <div className="metric-value positive mono" style={{ fontSize: 24, fontWeight: 700, color: 'var(--status-success)' }}>
                  +${totals.totalPL.toLocaleString()}
                </div>
              </div>
              <div className="metric-card" style={{ background: 'var(--bg-app)', border: '1px solid var(--border-outer)', borderRadius: 6, padding: 12 }}>
                <div className="metric-label" style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>
                  Win Rate
                </div>
                <div className="metric-value neutral mono" style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)' }}>
                  {totals.winRate.toFixed(0)}%
                </div>
              </div>
              <div className="metric-card" style={{ background: 'var(--bg-app)', border: '1px solid var(--border-outer)', borderRadius: 6, padding: 12 }}>
                <div className="metric-label" style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>
                  Positions
                </div>
                <div className="metric-value neutral mono" style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)' }}>
                  {positions.length}
                </div>
              </div>
            </div>

            {/* Scrollable Content */}
            <div className="main-scroll" style={{ flex: 1, overflow: 'auto', padding: '0 16px 16px' }}>
              {/* KPI Tiles */}
              <div className="kpi-section" style={{ marginTop: 16 }}>
                <div className="kpi-title" style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 12 }}>
                  Risk Metrics
                </div>
                <div className="kpi-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
                  {riskMetrics.map((metric, i) => (
                    <div key={i} className="kpi-tile" style={{ background: 'var(--bg-app)', border: '1px solid var(--border-outer)', borderRadius: 8, padding: 12 }}>
                      <div className="kpi-label-row" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                        <span className="kpi-label" style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{metric.label}</span>
                        <span className="kpi-icon" style={{ fontSize: 14, color: metric.level === 'low' ? 'var(--status-success)' : metric.level === 'medium' ? 'var(--status-warning)' : 'var(--status-danger)' }}>
                          {metric.icon === 'ri-dashboard-3-line' && <BarChart3 size={14} />}
                          {metric.icon === 'ri-bar-chart-box-line' && <Activity size={14} />}
                          {metric.icon === 'ri-trending-up-line' && <TrendingUp size={14} />}
                          {metric.icon === 'ri-error-warning-line' && <AlertTriangle size={14}/>}
                        </span>
                      </div>
                      <div className="kpi-value mono" style={{ fontSize: 28, fontWeight: 700, color: metric.level === 'low' ? 'var(--status-success)' : metric.level === 'medium' ? '#F59E0B' : 'var(--status-danger)', lineHeight: 1.2 }}>
                        {metric.value}
                      </div>
                      <div className="kpi-max mono" style={{ fontSize: 11, color: 'var(--text-muted)' }}>/ {metric.max}</div>
                      <div className="risk-indicator" style={{ marginTop: 8 }}>
                        <div className="risk-bar-container" style={{ height: 4, background: 'var(--bg-card)', borderRadius: 2, overflow: 'hidden', marginBottom: 4 }}>
                          <div className={`risk-bar ${metric.level}`} style={{ height: '100%', width: `${metric.value}%`, borderRadius: 2, transition: 'width 0.3s', background: metric.level === 'low' ? 'var(--status-success)' : metric.level === 'medium' ? 'var(--status-warning)' : 'var(--status-danger)' }}></div>
                        </div>
                        <div className="risk-status-row" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <span className={`risk-status ${metric.level}`} style={{ fontSize: 9, fontWeight: 600, padding: '2px 6px', borderRadius: 3, textTransform: 'uppercase', background: metric.level === 'low' ? 'var(--status-success-bg)' : metric.level === 'medium' ? 'var(--status-warning-bg)' : 'var(--status-danger-bg)', color: metric.level === 'low' ? 'var(--status-success)' : metric.level === 'medium' ? 'var(--status-warning)' : 'var(--status-danger)' }}>
                            {metric.level.toUpperCase()}
                          </span>
                          <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>{metric.value}%</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Exposure Summary */}
              <div className="exposure-section" style={{ marginTop: 16, padding: 12, background: 'var(--bg-app)', border: '1px solid var(--border-outer)', borderRadius: 8 }}>
                <div className="exposure-title" style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 12 }}>
                  Exposure Summary
                </div>
                <div className="exposure-row" style={{ marginBottom: 12 }}>
                  <div className="exposure-label-row" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span className="exposure-label" style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Total Notional</span>
                    <span className="exposure-value mono" style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>${totals.totalNotional.toLocaleString()}.00</span>
                  </div>
                </div>
                <div className="exposure-row" style={{ marginBottom: 12 }}>
                  <div className="exposure-label-row" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span className="exposure-label" style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Net YES Notional</span>
                    <span className="exposure-value text-green mono" style={{ fontSize: 12, fontWeight: 600, color: 'var(--status-success)' }}>${totals.yesNotional.toLocaleString()}.00</span>
                  </div>
                  <div className="progress-bar" style={{ height: 6, background: 'var(--bg-card)', borderRadius: 3, overflow: 'hidden' }}>
                    <div className="progress-fill green" style={{ height: '100%', width: `${allocationTotals.yesTotal}%`, background: 'var(--status-success)' }}></div>
                  </div>
                </div>
                <div className="exposure-row">
                  <div className="exposure-label-row" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span className="exposure-label" style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Net NO Notional</span>
                    <span className="exposure-value text-red mono" style={{ fontSize: 12, fontWeight: 600, color: 'var(--status-danger)' }}>${totals.noNotional.toLocaleString()}.00</span>
                  </div>
                  <div className="progress-bar" style={{ height: 6, background: 'var(--bg-card)', borderRadius: 3, overflow: 'hidden' }}>
                    <div className="progress-fill red" style={{ height: '100%', width: `${allocationTotals.noTotal}%`, background: 'var(--status-danger)' }}></div>
                  </div>
                </div>
              </div>

              {/* Portfolio Allocation */}
              <div className="allocation-section" style={{ marginTop: 16, padding: 12, background: 'var(--bg-app)', border: '1px solid var(--border-outer)', borderRadius: 8 }}>
                <div className="allocation-title" style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 12 }}>
                  Portfolio Allocation
                </div>
                {allocations.map((allocation, i) => (
                  <div key={i} className="allocation-item" style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
                    <span className="allocation-asset mono" style={{ fontSize: 11, color: 'var(--text-primary)', width: 90 }}>{allocation.timelineId} ({allocation.direction})</span>
                    <div className="allocation-bar" style={{ flex: 1, height: 8, background: 'var(--bg-card)', borderRadius: 4, overflow: 'hidden' }}>
                      <div className={`allocation-fill ${allocation.direction === 'YES' ? 'yes' : 'no'}`} style={{ height: '100%', width: `${allocation.percent}%`, borderRadius: 4, background: allocation.direction === 'YES' ? 'var(--status-success)' : 'var(--status-danger)' }}></div>
                    </div>
                    <span className="allocation-percent mono" style={{ fontSize: 11, color: 'var(--text-muted)', width: 45, textAlign: 'right' }}>{allocation.percent}%</span>
                  </div>
                ))}
              </div>

              {/* Equity Curve */}
              <div className="equity-section" style={{ marginTop: 16, padding: 12, background: 'var(--bg-app)', border: '1px solid var(--border-outer)', borderRadius: 8 }}>
                <div className="equity-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <div className="equity-title" style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Equity Curve (30D)</div>
                  <div className="chart-controls" style={{ display: 'flex', gap: 4 }}>
                    {(['1D', '7D', '30D', 'ALL'] as ChartTimeframe[]).map((tf) => (
                      <button
                        key={tf}
                        className={`chart-btn ${chartTimeframe === tf ? 'active' : ''}`}
                        onClick={() => setChartTimeframe(tf)}
                        style={{ padding: '4px 10px', background: chartTimeframe === tf ? 'var(--echelon-cyan-bg)' : 'transparent', border: '1px solid var(--border-outer)', borderRadius: 6, color: chartTimeframe === tf ? 'var(--echelon-cyan)' : 'var(--text-muted)', fontSize: 10, cursor: 'pointer', transition: 'all 0.2s' }}
                      >
                        {tf}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="equity-chart" style={{ position: 'relative', height: 120, background: 'var(--bg-card)', borderRadius: 6, overflow: 'hidden' }}>
                  <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}>
                    <defs>
                      <linearGradient id="equityGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stopColor="var(--status-success)" stopOpacity="0.4"/>
                        <stop offset="100%" stopColor="var(--status-success)" stopOpacity="0"/>
                      </linearGradient>
                    </defs>
                    <path d={equityAreaPath} fill="url(#equityGradient)"/>
                    <path d={equityLinePath} fill="none" stroke="var(--status-success)" strokeWidth="1" strokeLinecap="round"/>
                  </svg>
                  <div className="chart-grid" style={{ position: 'absolute', inset: 0 }}>
                    {[0, 25, 50, 75].map((pct) => (
                      <div key={pct} className="chart-grid-line" style={{ position: 'absolute', left: 0, right: 0, height: 1, background: 'var(--border-outer)', top: `${pct}%` }}></div>
                    ))}
                  </div>
                  <div className="chart-labels" style={{ position: 'absolute', bottom: 8, left: 16, right: 16, display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-muted)' }}>
                    <span>Dec 28</span>
                    <span>Jan 7</span>
                    <span>Jan 17</span>
                    <span>Jan 27</span>
                  </div>
                </div>
                <div className="chart-summary" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--border-outer)' }}>
                  <div className="chart-stat" style={{ textAlign: 'center' }}>
                    <div className="chart-stat-value positive mono" style={{ fontSize: 16, fontWeight: 700, color: 'var(--status-success)' }}>{formatPL(equityStats.totalPL)}</div>
                    <div className="chart-stat-label" style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>Total P/L</div>
                  </div>
                  <div className="chart-stat" style={{ textAlign: 'center' }}>
                    <div className="chart-stat-value mono" style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>{equityStats.returnPercent >= 0 ? '+' : ''}{equityStats.returnPercent}%</div>
                    <div className="chart-stat-label" style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>Return</div>
                  </div>
                  <div className="chart-stat" style={{ textAlign: 'center' }}>
                    <div className="chart-stat-value mono" style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>{equityStats.sharpeRatio}x</div>
                    <div className="chart-stat-label" style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>Sharpe Ratio</div>
                  </div>
                  <div className="chart-stat" style={{ textAlign: 'center' }}>
                    <div className="chart-stat-value negative mono" style={{ fontSize: 16, fontWeight: 700, color: 'var(--status-danger)' }}>{formatPL(Math.abs(equityStats.maxDrawdown))}</div>
                    <div className="chart-stat-label" style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>Max Drawdown</div>
                  </div>
                </div>
              </div>

              {/* Correlation Matrix */}
              <div className="correlation-section" style={{ marginTop: 16, padding: 12, background: 'var(--bg-app)', border: '1px solid var(--border-outer)', borderRadius: 8 }}>
                <div className="correlation-title" style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 12 }}>
                  Position Correlations
                </div>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
                  <thead>
                    <tr>
                      <th style={{ padding: 8, textAlign: 'center', border: '1px solid var(--border-outer)', background: 'var(--bg-card)', fontWeight: 600, color: 'var(--text-muted)' }}></th>
                      {['TL-2847', 'TL-2846', 'TL-2845', 'TL-2844'].map((tl) => (
                        <th key={tl} style={{ padding: 8, textAlign: 'center', border: '1px solid var(--border-outer)', background: 'var(--bg-card)', fontWeight: 600, color: 'var(--text-muted)' }}>{tl}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {['TL-2847', 'TL-2846', 'TL-2845', 'TL-2844'].map((tl1) => (
                      <tr key={tl1}>
                        <td style={{ padding: 8, textAlign: 'center', border: '1px solid var(--border-outer)', background: 'var(--bg-card)', fontWeight: 600, color: 'var(--text-muted)' }}>{tl1}</td>
                        {['TL-2847', 'TL-2846', 'TL-2845', 'TL-2844'].map((tl2) => {
                          const corr = getCorrelation(tl1, tl2);
                          return (
                            <td key={tl2} style={{ padding: 8, textAlign: 'center', border: '1px solid var(--border-outer)', color: corr >= 0.7 ? 'var(--status-danger)' : corr >= 0.4 ? 'var(--status-warning)' : 'var(--status-success)' }}>
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
              <div className="risks-section" style={{ marginTop: 16 }}>
                <div className="risks-title" style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 12 }}>
                  Top Risks
                </div>
                <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse', background: 'var(--bg-app)', border: '1px solid var(--border-outer)', borderRadius: 8, overflow: 'hidden' }}>
                  <thead>
                    <tr>
                      <th style={{ padding: '8px 12px', textAlign: 'left', fontSize: 9, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', background: 'var(--bg-card)', borderBottom: '1px solid var(--border-outer)' }}>Timeline</th>
                      <th style={{ padding: '8px 12px', textAlign: 'left', fontSize: 9, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', background: 'var(--bg-card)', borderBottom: '1px solid var(--border-outer)' }}>Risk Score</th>
                      <th style={{ padding: '8px 12px', textAlign: 'left', fontSize: 9, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', background: 'var(--bg-card)', borderBottom: '1px solid var(--border-outer)' }}>Drivers</th>
                      <th style={{ padding: '8px 12px', textAlign: 'left', fontSize: 9, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', background: 'var(--bg-card)', borderBottom: '1px solid var(--border-outer)' }}>Burn at Collapse</th>
                      <th style={{ padding: '8px 12px', textAlign: 'right', fontSize: 9, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', background: 'var(--bg-card)', borderBottom: '1px solid var(--border-outer)' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {riskItems.map((item, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid var(--border-outer)' }}>
                        <td style={{ padding: '8px 12px' }}><span className="timeline-id mono" style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>{item.timelineId}</span></td>
                        <td style={{ padding: '8px 12px' }}><span className="risk-score mono" style={{ fontSize: 12, fontWeight: 600, color: item.riskScore >= 70 ? 'var(--status-danger)' : item.riskScore >= 50 ? '#F59E0B' : 'var(--status-success)' }}>{item.riskScore}</span></td>
                        <td style={{ padding: '8px 12px' }}><span className="risk-drivers" style={{ fontSize: 10, color: 'var(--text-muted)' }}>{item.drivers}</span></td>
                        <td style={{ padding: '8px 12px' }}><span className="burn-value mono" style={{ fontSize: 11, color: 'var(--status-danger)' }}>${item.burnAtCollapse.toLocaleString()}</span></td>
                        <td style={{ padding: '8px 12px' }}>
                          <div className="action-btns" style={{ display: 'flex', gap: 4, justifyContent: 'flex-end' }}>
                            <button className="action-btn" style={{ padding: '4px 8px', background: 'var(--bg-app)', border: '1px solid var(--border-outer)', borderRadius: 4, color: 'var(--text-secondary)', fontSize: 10, fontWeight: 500, cursor: 'pointer', transition: 'all 0.2s' }}>OPEN</button>
                            <button className="action-btn" style={{ padding: '4px 8px', background: 'var(--bg-app)', border: '1px solid var(--border-outer)', borderRadius: 4, color: 'var(--text-secondary)', fontSize: 10, fontWeight: 500, cursor: 'pointer', transition: 'all 0.2s' }}>REPLAY</button>
                          </div>
</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Recommendations */}
              <div className="recommendations-section" style={{ padding: '16px 0' }}>
                <div className="rec-title" style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 12 }}>
                  Recommendations
                </div>
                <ul style={{ listStyle: 'none' }}>
                  {recommendations.map((rec, i) => (
                    <li key={i} className="rec-item" style={{ display: 'flex', alignItems: 'flex-start', gap: 8, fontSize: 12, color: 'var(--text-primary)', marginBottom: 8 }}>
                      <ChevronRight size={14} style={{ color: 'var(--echelon-cyan)', marginTop: 1, flexShrink: 0 }} />
                      {rec.text}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Positions Panel */}
              <div className="positions-panel" style={{ flex: 1, background: 'var(--bg-card)', border: '1px solid var(--border-outer)', borderRadius: 8, display: 'flex', flexDirection: 'column', marginTop: 16, overflow: 'hidden' }}>
                <div className="positions-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', borderBottom: '1px solid var(--border-outer)' }}>
                  <div className="positions-tabs" style={{ display: 'flex', gap: 12 }}>
                    {(['positions', 'foldovers'] as PositionTab[]).map((tab) => (
                      <button
                        key={tab}
                        className={`positions-tab ${positionTab === tab ? 'active' : ''}`}
                        onClick={() => setPositionTab(tab)}
                        style={{ padding: '4px 12px', background: positionTab === tab ? 'var(--echelon-cyan-bg)' : 'transparent', border: 'none', color: positionTab === tab ? 'var(--echelon-cyan)' : 'var(--text-muted)', fontSize: 11, fontWeight: 500, cursor: 'pointer', borderRadius: 6, textTransform: 'capitalize', transition: 'all 0.2s' }}
                      >
                        {tab}
                      </button>
                    ))}
                  </div>
                  <button className="header-btn" style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px', background: 'var(--bg-app)', border: '1px solid var(--border-outer)', borderRadius: 6, color: 'var(--text-secondary)', fontSize: 11, fontWeight: 500, cursor: 'pointer', transition: 'all 0.2s' }}>
                    <Filter size={12} />
                    Filter
                  </button>
                </div>
                <div className="positions-table-container" style={{ flex: 1, overflow: 'auto' }}>
                  <table className="positions-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr>
                        <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: 9, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', background: 'var(--bg-app)', borderBottom: '1px solid var(--border-outer)', position: 'sticky', top: 0 }}>Timeline</th>
                        <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: 9, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', background: 'var(--bg-app)', borderBottom: '1px solid var(--border-outer)', position: 'sticky', top: 0 }}>Direction</th>
                        <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: 9, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', background: 'var(--bg-app)', borderBottom: '1px solid var(--border-outer)', position: 'sticky', top: 0 }}>Entry Price</th>
                        <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: 9, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', background: 'var(--bg-app)', borderBottom: '1px solid var(--border-outer)', position: 'sticky', top: 0 }}>Current Price</th>
                        <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: 9, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', background: 'var(--bg-app)', borderBottom: '1px solid var(--border-outer)', position: 'sticky', top: 0 }}>P/L</th>
                        <th style={{ textAlign: 'right', padding: '8px 12px', fontSize: 9, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', background: 'var(--bg-app)', borderBottom: '1px solid var(--border-outer)', position: 'sticky', top: 0 }}>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {positions.map((position) => (
                        <tr key={position.id} style={{ borderBottom: '1px solid var(--border-outer)' }}>
                          <td style={{ padding: '8px 12px' }}><span className="timeline-id mono" style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>{position.timelineId}</span></td>
                          <td style={{ padding: '8px 12px' }}>
                            <span className={`direction-badge ${position.direction.toLowerCase()}`} style={{ display: 'inline-block', padding: '2px 6px', borderRadius: 3, fontSize: 10, fontWeight: 600, background: position.direction === 'YES' ? 'var(--status-success-bg)' : 'var(--status-danger-bg)', color: position.direction === 'YES' ? 'var(--status-success)' : 'var(--status-danger)' }}>
                              {position.direction}
                            </span>
                          </td>
                          <td style={{ padding: '8px 12px' }}><span className="price mono" style={{ fontSize: 12, color: 'var(--text-primary)' }}>${position.entryPrice.toFixed(2)}</span></td>
                          <td style={{ padding: '8px 12px' }}><span className="price mono" style={{ fontSize: 12, color: 'var(--text-primary)' }}>${position.currentPrice.toFixed(2)}</span></td>
                          <td style={{ padding: '8px 12px' }}>
                            <span className={`pl-value mono ${position.pnl >= 0 ? 'positive' : 'negative'}`} style={{ fontSize: 12, fontWeight: 600, color: position.pnl >= 0 ? 'var(--status-success)' : 'var(--status-danger)' }}>
                              {position.pnl >= 0 ? '+' : ''}{formatPL(position.pnl)}
                            </span>
                          </td>
                          <td style={{ padding: '8px 12px' }}>
                            <div className="action-btns" style={{ display: 'flex', gap: 4, justifyContent: 'flex-end' }}>
                              <button className="action-btn" style={{ padding: '4px 8px', background: 'var(--bg-app)', border: '1px solid var(--border-outer)', borderRadius: 4, color: 'var(--text-secondary)', fontSize: 10, fontWeight: 500, cursor: 'pointer', transition: 'all 0.2s' }}>OPEN</button>
                              <button className="action-btn" style={{ padding: '4px 8px', background: 'var(--bg-app)', border: '1px solid var(--border-outer)', borderRadius: 4, color: 'var(--text-secondary)', fontSize: 10, fontWeight: 500, cursor: 'pointer', transition: 'all 0.2s' }}>REPLAY</button>
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
          <aside className="right-sidebar" style={{ width: 280, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Ghost Forks Widget */}
            <div className="widget" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-outer)', borderRadius: 8 }}>
              <div className="widget-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', borderBottom: '1px solid var(--border-outer)' }}>
                <span className="widget-title" style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Ghost Forks</span>
                <button className="action-btn" onClick={() => setShowForksPanel(true)} style={{ padding: '4px 8px', background: 'var(--bg-app)', border: '1px solid var(--border-outer)', borderRadius: 4, color: 'var(--text-secondary)', fontSize: 10, fontWeight: 500, cursor: 'pointer', transition: 'all 0.2s' }}>VIEW ALL</button>
              </div>
              <div className="widget-body" style={{ padding: 12 }}>
                {ghostForks.map((fork, i) => (
                  <div key={i} className="ghost-fork-item" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 0', borderBottom: i < ghostForks.length - 1 ? '1px solid var(--border-outer)' : 'none' }}>
                    <span className="ghost-fork-id mono" style={{ fontSize: 11, color: 'var(--text-primary)' }}>{fork.id}</span>
                    <span className="ghost-fork-time" style={{ fontSize: 10, color: 'var(--text-muted)' }}>{fork.timeAgo}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* My Agents Widget */}
            <div className="widget" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-outer)', borderRadius: 8 }}>
              <div className="widget-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', borderBottom: '1px solid var(--border-outer)' }}>
                <span className="widget-title" style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>My Agents</span>
                <button className="action-btn" onClick={() => setShowAgentsPanel(true)} style={{ padding: '4px 8px', background: 'var(--bg-app)', border: '1px solid var(--border-outer)', borderRadius: 4, color: 'var(--text-secondary)', fontSize: 10, fontWeight: 500, cursor: 'pointer', transition: 'all 0.2s' }}>MANAGE</button>
              </div>
              <div className="widget-body" style={{ padding: 12 }}>
                {agents.slice(0, 4).map((agent, i) => (
                  <div key={i} className="agent-item" style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 0', borderBottom: i < 3 ? '1px solid var(--border-outer)' : 'none' }}>
                    <div className="agent-avatar" style={{ width: 24, height: 24, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, fontWeight: 700, color: 'white', background: agent.color }}>{agent.name.charAt(6)}</div>
                    <span className="agent-name" style={{ fontSize: 12, color: 'var(--text-primary)', flex: 1 }}>{agent.name}</span>
                    <span className="agent-archetype" style={{ fontSize: 9, color: 'var(--text-muted)', padding: '2px 6px', background: 'var(--bg-app)', borderRadius: 3 }}>{agent.archetype}</span>
                    <span className={`agent-pnl mono ${agent.pnl >= 0 ? 'positive' : 'negative'}`} style={{ fontSize: 11, fontWeight: 600, color: agent.pnl >= 0 ? 'var(--status-success)' : 'var(--status-danger)' }}>{agent.pnl >= 0 ? '+' : ''}${Math.abs(agent.pnl / 1000).toFixed(1)}K</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Stats Row */}
            <div className="stats-row" style={{ display: 'flex', gap: 12 }}>
              <div className="stat-item" style={{ flex: 1, textAlign: 'center', padding: 12, background: 'var(--bg-card)', border: '1px solid var(--border-outer)', borderRadius: 8 }}>
                <div className="stat-value mono" style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>{agents.length}</div>
                <div className="stat-label" style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>Live Agents</div>
              </div>
              <div className="stat-item" style={{ flex: 1, textAlign: 'center', padding: 12, background: 'var(--bg-card)', border: '1px solid var(--border-outer)', borderRadius: 8 }}>
                <div className="stat-value mono" style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>{agents.reduce((sum, a) => sum + a.actions, 0).toLocaleString()}</div>
                <div className="stat-label" style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>Active Ops</div>
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
        <div className="side-panel-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 16, borderBottom: '1px solid var(--border-outer)', flexShrink: 0 }}>
          <div className="side-panel-title" style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Bot size={18} style={{ color: 'var(--echelon-cyan)' }} />
            Manage Agents
          </div>
          <button className="side-panel-close" onClick={() => setShowAgentsPanel(false)} style={{ width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-app)', border: '1px solid var(--border-outer)', borderRadius: 6, color: 'var(--text-muted)', cursor: 'pointer', transition: 'all 0.2s' }}>
            <X size={14} />
          </button>
        </div>
        <div className="side-panel-body" style={{ flex: 1, overflow: 'auto', padding: 16 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
            {agents.map((agent, i) => (
              <div key={i} className="agent-card-mini" style={{ background: 'var(--bg-app)', border: '1px solid var(--border-outer)', borderRadius: 8, padding: 12 }}>
                <div className="agent-card-header-mini" style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <div className="agent-avatar-mini" style={{ width: 28, height: 28, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 700, color: 'white', background: agent.color }}>{agent.name.charAt(6)}</div>
                  <div className="agent-info-mini" style={{ flex: 1 }}>
                    <div className="agent-name-mini" style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{agent.name}</div>
                    <div className="agent-archetype-mini" style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase' }}>{agent.archetype}</div>
                  </div>
                  <span className={`agent-pnl-mini mono ${agent.pnl >= 0 ? 'positive' : 'negative'}`} style={{ fontSize: 14, fontWeight: 600, color: agent.pnl >= 0 ? 'var(--status-success)' : 'var(--status-danger)' }}>{agent.pnl >= 0 ? '+' : ''}${Math.abs(agent.pnl).toLocaleString()}</span>
                </div>
                <div className="agent-chart-mini" style={{ height: 40, marginTop: 8, position: 'relative' }}>
                  <svg viewBox="0 0 100 40" style={{ width: '100%', height: '100%' }}>
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
                <div className="agent-stats-mini" style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8, fontSize: 10, color: 'var(--text-muted)' }}>
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
        <div className="side-panel-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 16, borderBottom: '1px solid var(--border-outer)', flexShrink: 0 }}>
          <div className="side-panel-title" style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <GitBranch size={18} style={{ color: 'var(--echelon-cyan)' }} />
            Ghost Forks
          </div>
          <button className="side-panel-close" onClick={() => setShowForksPanel(false)} style={{ width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-app)', border: '1px solid var(--border-outer)', borderRadius: 6, color: 'var(--text-muted)', cursor: 'pointer', transition: 'all 0.2s' }}>
            <X size={14} />
          </button>
        </div>
        <div className="side-panel-body" style={{ flex: 1, overflow: 'auto', padding: 16 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {forkDetails.map((fork, i) => (
              <div key={i} className="fork-item-detail" style={{ background: 'var(--bg-app)', border: '1px solid var(--border-outer)', borderRadius: 8, padding: 12 }}>
                <div className="fork-header-row" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span className="fork-id mono" style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>{fork.id}</span>
                  <span className="fork-time" style={{ fontSize: 10, color: 'var(--text-muted)' }}>{fork.timeAgo}</span>
                </div>
                <div className="fork-details" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginTop: 8 }}>
                  <div className="fork-detail" style={{ textAlign: 'center' }}>
                    <div className="fork-detail-value mono" style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>{fork.probability}%</div>
                    <div className="fork-detail-label" style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Probability</div>
                  </div>
                  <div className="fork-detail" style={{ textAlign: 'center' }}>
                    <div className="fork-detail-value mono" style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>{fork.forks}</div>
                    <div className="fork-detail-label" style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Forks</div>
                  </div>
                  <div className="fork-detail" style={{ textAlign: 'center' }}>
                    <div className="fork-detail-value mono" style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>${(fork.volume / 1000).toFixed(0)}K</div>
                    <div className="fork-detail-label" style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Volume</div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Founders Yield */}
          <div className="founders-yield-section" style={{ marginTop: 24, paddingTop: 24, borderTop: '1px solid var(--border-outer)' }}>
            <div className="yield-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <div className="yield-title" style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'flex', alignItems: 'center', gap: 8 }}>
                <Star size={14} style={{ color: 'var(--echelon-cyan)' }} />
                Founders Yield
              </div>
              <div className="yield-value mono" style={{ fontSize: 20, fontWeight: 700, color: 'var(--status-success)' }}>+${yieldBreakdown.total.toLocaleString()}</div>
            </div>
            <div className="yield-breakdown" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
              <div className="yield-item" style={{ background: 'var(--bg-app)', border: '1px solid var(--border-outer)', borderRadius: 6, padding: 8, textAlign: 'center' }}>
                <div className="yield-item-value mono" style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>${yieldBreakdown.trading.toLocaleString()}</div>
                <div className="yield-item-label" style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase', marginTop: 2 }}>Trading</div>
              </div>
              <div className="yield-item" style={{ background: 'var(--bg-app)', border: '1px solid var(--border-outer)', borderRadius: 6, padding: 8, textAlign: 'center' }}>
                <div className="yield-item-value mono" style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>${yieldBreakdown.MEV.toLocaleString()}</div>
                <div className="yield-item-label" style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase', marginTop: 2 }}>MEV</div>
              </div>
              <div className="yield-item" style={{ background: 'var(--bg-app)', border: '1px solid var(--border-outer)', borderRadius: 6, padding: 8, textAlign: 'center' }}>
                <div className="yield-item-value mono" style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>${yieldBreakdown.bribes.toLocaleString()}</div>
                <div className="yield-item-label" style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase', marginTop: 2 }}>Bribes</div>
              </div>
              <div className="yield-item" style={{ background: 'var(--bg-app)', border: '1px solid var(--border-outer)', borderRadius: 6, padding: 8, textAlign: 'center' }}>
                <div className="yield-item-value mono" style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>${yieldBreakdown.total.toLocaleString()}</div>
                <div className="yield-item-label" style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase', marginTop: 2 }}>Total</div>
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
        .header-btn:hover {
          border-color: var(--echelon-cyan) !important;
          color: var(--echelon-cyan) !important;
        }
        .action-btn:hover {
          border-color: var(--echelon-cyan) !important;
          color: var(--echelon-cyan) !important;
        }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: var(--bg-app); }
        ::-webkit-scrollbar-thumb { background: var(--border-outer); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--slate-700); }
      `}</style>
    </div>
  );
}
