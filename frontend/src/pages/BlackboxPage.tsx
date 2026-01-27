// Blackbox Page Component
// Signal Intelligence Terminal - Main trading interface

import { useState } from 'react';
import { PriceChart } from '../components/blackbox/PriceChart';
import { OrderBookPanel } from '../components/blackbox/OrderBookPanel';
import { TimeSalesPanel } from '../components/blackbox/TimeSalesPanel';
import { AgentLeaderboard } from '../components/blackbox/AgentLeaderboard';
import { SignalInterceptsPanel } from '../components/blackbox/SignalInterceptsPanel';
import { LiveRibbon } from '../components/blackbox/LiveRibbon';
import { TimelineGrid } from '../components/blackbox/TimelineGrid';
import { WarChestGrid } from '../components/blackbox/WarChestGrid';
import {
  useBlackboxChart,
  useOrderBook,
  useTimeSales,
  useAgentLeaderboard,
  useTimelines,
  useWarChest,
  useIntercepts,
  useBlackboxRibbon,
  useSystemStatus,
} from '../hooks/useBlackbox';
import type { Timeframe } from '../types/blackbox';

type TabType = 'markets' | 'intercepts' | 'timeline' | 'warchest';

export function BlackboxPage() {
  const [timeframe, setTimeframe] = useState<Timeframe>('15m');
  const [activeTab, setActiveTab] = useState<TabType>('markets');

  // Data hooks
  const { candles, currentPrice, indicators } = useBlackboxChart(timeframe);
  const orderBook = useOrderBook();
  const trades = useTimeSales();
  const { agents, searchQuery, setSearchQuery } = useAgentLeaderboard();
  const timelines = useTimelines();
  const warChest = useWarChest();
  const intercepts = useIntercepts();
  const ribbonEvents = useBlackboxRibbon();
  const { latency } = useSystemStatus();

  const tabs: { id: TabType; label: string }[] = [
    { id: 'markets', label: 'Market Terminal' },
    { id: 'intercepts', label: 'Signal Intercepts' },
    { id: 'timeline', label: 'Timeline Health' },
    { id: 'warchest', label: 'War Chest' },
  ];

  return (
    <div className="container" style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-app)' }}>
      {/* Live Intel Ribbon */}
      <LiveRibbon events={ribbonEvents} />

      {/* Tab Navigation */}
      <div className="tab-nav" style={{ flexShrink: 0, display: 'flex', gap: 8, padding: '12px 24px', background: 'var(--bg-app)', borderBottom: '1px solid var(--border-outer)' }}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '8px 16px',
              background: activeTab === tab.id ? 'var(--bg-panel)' : 'transparent',
              border: activeTab === tab.id ? '1px solid var(--border-outer)' : '1px solid transparent',
              borderRadius: 20,
              color: activeTab === tab.id ? 'var(--text-primary)' : 'var(--text-secondary)',
              fontSize: 12,
              fontWeight: 500,
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Main Content */}
{activeTab === 'markets' && (
        <main className="tab-content active" style={{ flex: 1, minHeight: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <div className="grid-layout" style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 16, height: '100%', padding: 16, overflow: 'hidden' }}>
            
            {/* Left Column: Chart + Bottom Split */}
            <div className="chart-section" style={{ display: 'flex', flexDirection: 'column', gap: 16, minWidth: 0, overflow: 'hidden' }}>
              
              {/* Chart */}
              <PriceChart
                candles={candles}
                currentPrice={currentPrice}
                indicators={indicators}
                timeframe={timeframe}
                onTimeframeChange={setTimeframe}
              />

              {/* Bottom Split */}
              <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, minHeight: 0, overflow: 'hidden' }}>
                <TimeSalesPanel trades={trades} />
                <AgentLeaderboard agents={agents} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
              </div>
            </div>

            {/* Right Sidebar: Order Book + Intercepts */}
            <div className="sidebar-section" style={{ display: 'flex', flexDirection: 'column', gap: 16, minWidth: 0, overflow: 'hidden' }}>
              <OrderBookPanel orderBook={orderBook} currentPrice={currentPrice} />
              <SignalInterceptsPanel intercepts={intercepts} />
            </div>
          </div>
        </main>
      )}

      {activeTab === 'intercepts' && (
        <main className="tab-content active" style={{ flex: 1, overflow: 'auto' }}>
          <div className="panel" style={{ margin: 16, padding: 0, display: 'flex', flexDirection: 'column', height: 'calc(100% - 32px)' }}>
            <div className="panel-header">
              <span className="panel-title">SIGNAL LOGS</span>
            </div>
            <div className="data-list" style={{ flex: 1, overflow: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-outer)' }}>
                    <th style={{ padding: '8px 16px', textAlign: 'left', fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>TIME</th>
                    <th style={{ padding: '8px 16px', textAlign: 'left', fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>TYPE</th>
                    <th style={{ padding: '8px 16px', textAlign: 'left', fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>THEATRE</th>
                    <th style={{ padding: '8px 16px', textAlign: 'left', fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>AGENT</th>
                    <th style={{ padding: '8px 16px', textAlign: 'left', fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>ACTION</th>
                    <th style={{ padding: '8px 16px', textAlign: 'right', fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>VOLUME</th>
                  </tr>
                </thead>
                <tbody>
                  {intercepts.map((intercept, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid var(--border-inner)' }}>
                      <td className="mono" style={{ padding: '8px 16px', fontSize: 11, color: 'var(--text-muted)' }}>
                        {intercept.timestamp.toISOString().substr(11, 8)}
                      </td>
                      <td style={{ padding: '8px 16px' }}>
                        <span className={`ribbon-tag ${intercept.severity === 'critical' ? 'sabotage' : intercept.severity === 'warning' ? 'market' : intercept.severity === 'success' ? 'shield' : 'market'}`} style={{ fontSize: 9, fontWeight: 700, padding: '2px 6px', borderRadius: 4 }}>
                          {intercept.severity.toUpperCase()}
                        </span>
                      </td>
                      <td style={{ padding: '8px 16px', fontSize: 11 }}>{intercept.theatre || '—'}</td>
                      <td style={{ padding: '8px 16px', fontSize: 11 }}>{intercept.agent || '—'}</td>
                      <td style={{ padding: '8px 16px', fontSize: 11, color: 'var(--text-secondary)' }}>{intercept.title}</td>
                      <td className="numeric mono" style={{ padding: '8px 16px', fontSize: 11, textAlign: 'right' }}>—</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      )}

      {activeTab === 'timeline' && (
        <main className="tab-content active" style={{ flex: 1, overflow: 'auto' }}>
          <TimelineGrid timelines={timelines} />
        </main>
      )}

      {activeTab === 'warchest' && (
        <main className="tab-content active" style={{ flex: 1, overflow: 'auto' }}>
          <WarChestGrid items={warChest} />
        </main>
      )}

      {/* Footer */}
      <footer className="app-footer" style={{ flexShrink: 0, background: 'var(--bg-panel)', borderTop: '1px solid var(--border-outer)', padding: '4px 24px', display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-muted)' }}>
        <div className="flex-center" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span><span className="live-dot" style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--status-success)', marginRight: 6 }}></span> System Optimal</span>
          <span>Latency: {latency}ms</span>
        </div>
        <div className="flex-center" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span>Echelon Protocol Inc.</span>
          <span>Restricted Access</span>
        </div>
      </footer>

      {/* CSS Animations */}
      <style>{`
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.5; }
          100% { opacity: 1; }
        }
        .tab-btn:hover {
          color: var(--text-primary) !important;
          background: var(--bg-card) !important;
        }
        .nav-btn:hover {
          border-color: var(--text-muted) !important;
          color: var(--text-primary) !important;
        }
        .action-btn:hover {
          border-color: var(--text-muted) !important;
          color: var(--text-primary) !important;
        }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: var(--bg-app); }
        ::-webkit-scrollbar-thumb { background: var(--border-outer); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--slate-700); }
      `}</style>
    </div>
  );
}
