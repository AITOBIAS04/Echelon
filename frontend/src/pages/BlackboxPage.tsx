// Blackbox Page Component
// Market Terminal - Analytics interface inside AppLayout

import { useState, useEffect, useRef } from 'react';
import { PriceChart } from '../components/blackbox/PriceChart';
import { OrderBookPanel } from '../components/blackbox/OrderBookPanel';
import { TimeSalesPanel } from '../components/blackbox/TimeSalesPanel';
import { AgentLeaderboard } from '../components/blackbox/AgentLeaderboard';
import { SignalInterceptsPanel } from '../components/blackbox/SignalInterceptsPanel';
import { DepthChartPanel } from '../components/blackbox/DepthChartPanel';
import { VolumeProfilePanel } from '../components/blackbox/VolumeProfilePanel';
import { HeatmapPanel } from '../components/blackbox/HeatmapPanel';
import {
  useBlackboxChart,
  useOrderBook,
  useTimeSales,
  useAgentLeaderboard,
  useIntercepts,
} from '../hooks/useBlackbox';
import { useRegisterTopActionBarActions } from '../contexts/TopActionBarActionsContext';
import type { Timeframe } from '../types/blackbox';

// Chart mode type for tabs
type ChartMode = 'price' | 'depth' | 'vol' | 'heatmap';

// Chart mode display labels
const CHART_MODE_LABELS: Record<ChartMode, string> = {
  price: 'PRICE ACTION',
  depth: 'DEPTH CHART',
  vol: 'VOL PROFILE',
  heatmap: 'HEATMAP',
};

export function BlackboxPage() {
  const [timeframe, setTimeframe] = useState<Timeframe>('15m');
  const [chartMode, setChartMode] = useState<ChartMode>('price');

  // Panel state
  const [alertPanelOpen, setAlertPanelOpen] = useState(false);
  const [comparePanelOpen, setComparePanelOpen] = useState(false);
  const [settingsPanelOpen, setSettingsPanelOpen] = useState(false);

  // Refs for backdrop click handling
  const alertPanelRef = useRef<HTMLDivElement>(null);
  const comparePanelRef = useRef<HTMLDivElement>(null);
  const settingsPanelRef = useRef<HTMLDivElement>(null);

  // Data hooks
  const { candles, currentPrice, indicators } = useBlackboxChart(timeframe);
  const orderBook = useOrderBook();
  const trades = useTimeSales();
  const { agents, searchQuery, setSearchQuery } = useAgentLeaderboard();
  const intercepts = useIntercepts();

  // Register TopActionBar actions
  useRegisterTopActionBarActions({
    onAlert: () => {
      setAlertPanelOpen(prev => !prev);
      setComparePanelOpen(false);
      setSettingsPanelOpen(false);
    },
    onCompare: () => {
      setComparePanelOpen(prev => !prev);
      setAlertPanelOpen(false);
      setSettingsPanelOpen(false);
    },
    onRefresh: () => {
      // Refresh data - hooks will auto-refresh
      console.log('Refresh analytics data');
    },
  });

  // Close panels on Escape key
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setAlertPanelOpen(false);
        setComparePanelOpen(false);
        setSettingsPanelOpen(false);
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Render chart content based on chartMode
  const renderChartContent = () => {
    switch (chartMode) {
      case 'price':
        return (
          <PriceChart
            candles={candles}
            currentPrice={currentPrice}
            indicators={indicators}
            timeframe={timeframe}
            onTimeframeChange={setTimeframe}
          />
        );
      case 'depth':
        return <DepthChartPanel />;
      case 'vol':
        return <VolumeProfilePanel />;
      case 'heatmap':
        return <HeatmapPanel />;
      default:
        return null;
    }
  };

  return (
    <div className="h-full w-full flex flex-col min-h-0 bg-slate-950 text-terminal-text">

      {/* Tabs Row */}
      <div className="flex items-center gap-2 px-6 py-3 border-b border-terminal-border">
        {(Object.keys(CHART_MODE_LABELS) as ChartMode[]).map((mode) => (
          <button
            key={mode}
            onClick={() => setChartMode(mode)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
              chartMode === mode
                ? 'bg-slate-800 text-terminal-text'
                : 'text-terminal-text-muted hover:text-terminal-text-secondary hover:bg-slate-800'
            }`}
          >
            {CHART_MODE_LABELS[mode]}
          </button>
        ))}
      </div>

      {/* Main Content */}
      <div className="flex-1 min-h-0 p-6 overflow-hidden">
        <div className="h-full flex flex-col min-h-0">
          <div className="grid grid-cols-12 gap-4 min-h-0" style={{ minHeight: 0 }}>

            {/* Price Action - col-span-9 */}
            <div className="col-span-9 flex flex-col min-h-0">
              {renderChartContent()}
            </div>

            {/* Order Book - col-span-3 */}
            <div className="col-span-3 flex flex-col min-h-0">
              <OrderBookPanel orderBook={orderBook} currentPrice={currentPrice} />
            </div>

            {/* Time & Sales - col-span-6 */}
            <div className="col-span-6 flex flex-col min-h-0">
              <TimeSalesPanel trades={trades} />
            </div>

            {/* Agent Performance - col-span-3 */}
            <div className="col-span-3 flex flex-col min-h-0">
              <AgentLeaderboard agents={agents} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
            </div>

            {/* Signal Intercepts - col-span-3 */}
            <div className="col-span-3 flex flex-col min-h-0">
              <SignalInterceptsPanel intercepts={intercepts} />
            </div>

          </div>
        </div>
      </div>

      {/* Alert Panel Backdrop */}
      {alertPanelOpen && (
        <div
          className="fixed inset-0 z-40"
          style={{ background: 'rgba(0,0,0,0.3)' }}
          onClick={() => setAlertPanelOpen(false)}
        />
      )}

      {/* Alert Panel */}
      {alertPanelOpen && (
        <div
          ref={alertPanelRef}
          className="fixed top-[60px] right-6 w-96 max-h-[calc(100vh-80px)] rounded-xl flex flex-col overflow-hidden z-50 shadow-xl bg-terminal-panel border border-terminal-border"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex items-center justify-between px-4 py-3 border-b bg-terminal-card border-terminal-border">
            <span className="text-sm font-semibold text-terminal-text">Analytics Alerts</span>
            <button
              onClick={() => setAlertPanelOpen(false)}
              className="p-1 rounded transition-colors text-terminal-text-muted"
            >
              ✕
            </button>
          </div>
          <div className="p-4 overflow-y-auto" style={{ maxHeight: 400 }}>
            <p className="text-xs text-terminal-text-muted">No alerts configured for analytics.</p>
          </div>
        </div>
      )}

      {/* Compare Panel Backdrop */}
      {comparePanelOpen && (
        <div
          className="fixed inset-0 z-40"
          style={{ background: 'rgba(0,0,0,0.3)' }}
          onClick={() => setComparePanelOpen(false)}
        />
      )}

      {/* Compare Panel */}
      {comparePanelOpen && (
        <div
          ref={comparePanelRef}
          className="fixed top-[60px] right-6 w-96 max-h-[calc(100vh-80px)] rounded-xl flex flex-col overflow-hidden z-50 shadow-xl bg-terminal-panel border border-terminal-border"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex items-center justify-between px-4 py-3 border-b bg-terminal-card border-terminal-border">
            <span className="text-sm font-semibold text-terminal-text">Compare Theatres</span>
            <button
              onClick={() => setComparePanelOpen(false)}
              className="p-1 rounded transition-colors text-terminal-text-muted"
            >
              ✕
            </button>
          </div>
          <div className="p-4 overflow-y-auto" style={{ maxHeight: 400 }}>
            <p className="text-xs text-terminal-text-muted">Select theatres to compare.</p>
          </div>
        </div>
      )}

      {/* Settings Panel Backdrop */}
      {settingsPanelOpen && (
        <div
          className="fixed inset-0 z-40"
          style={{ background: 'rgba(0,0,0,0.3)' }}
          onClick={() => setSettingsPanelOpen(false)}
        />
      )}

      {/* Settings Panel */}
      {settingsPanelOpen && (
        <div
          ref={settingsPanelRef}
          className="fixed top-[60px] right-6 w-80 max-h-[calc(100vh-80px)] rounded-xl flex flex-col overflow-hidden z-50 shadow-xl bg-terminal-panel border border-terminal-border"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex items-center justify-between px-4 py-3 border-b bg-terminal-card border-terminal-border">
            <span className="text-sm font-semibold text-terminal-text">Analytics Settings</span>
            <button
              onClick={() => setSettingsPanelOpen(false)}
              className="p-1 rounded transition-colors text-terminal-text-muted"
            >
              ✕
            </button>
          </div>
          <div className="p-4">
            <p className="text-xs text-terminal-text-muted">Settings panel stub.</p>
          </div>
        </div>
      )}
    </div>
  );
}
