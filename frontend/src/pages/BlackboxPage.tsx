/**
 * Analytics Page (formerly Blackbox)
 *
 * CFPM/LMSR prediction market terminal with impact-curve charting,
 * cost-function panels, agent leaderboard, and signal intercepts.
 */

import { useState, useEffect, useRef } from 'react';
import { PriceChart } from '../components/blackbox/PriceChart';
import { ImpactCostPanel } from '../components/blackbox/ImpactCostPanel';
import { TimeSalesPanel } from '../components/blackbox/TimeSalesPanel';
import { AgentLeaderboard } from '../components/blackbox/AgentLeaderboard';
import { SignalInterceptsPanel } from '../components/blackbox/SignalInterceptsPanel';
import { DepthChartPanel } from '../components/blackbox/DepthChartPanel';
import { VolumeProfilePanel } from '../components/blackbox/VolumeProfilePanel';
import { HeatmapPanel } from '../components/blackbox/HeatmapPanel';
import {
  useBlackboxChart,
  useTimeSales,
  useAgentLeaderboard,
  useIntercepts,
} from '../hooks/useBlackbox';
import { useRegisterTopActionBarActions } from '../contexts/TopActionBarActionsContext';
import { clsx } from 'clsx';
import type { Timeframe } from '../types/blackbox';

// ── Chart mode types ────────────────────────────────────────────────────
type ChartMode = 'price' | 'depth' | 'vol' | 'heatmap';

const CHART_MODE_LABELS: Record<ChartMode, string> = {
  price: 'PRICE ACTION',
  depth: 'IMPACT CURVE',
  vol: 'VOL PROFILE',
  heatmap: 'HEATMAP',
};

export function BlackboxPage() {
  const [timeframe, setTimeframe] = useState<Timeframe>('15m');
  const [chartMode, setChartMode] = useState<ChartMode>('price');

  // Overlay state
  const [alertPanelOpen, setAlertPanelOpen] = useState(false);
  const [comparePanelOpen, setComparePanelOpen] = useState(false);
  const [settingsPanelOpen, setSettingsPanelOpen] = useState(false);

  // Refs for backdrop click handling
  const alertPanelRef = useRef<HTMLDivElement>(null);
  const comparePanelRef = useRef<HTMLDivElement>(null);
  const settingsPanelRef = useRef<HTMLDivElement>(null);

  // Data hooks
  const { candles, currentPrice, indicators } = useBlackboxChart(timeframe);
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
      console.log('Refresh analytics data');
    },
  });

  // Close overlays on Escape
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

  // Render chart content based on mode
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
    <div className="h-full w-full flex flex-col min-h-0 bg-terminal-bg text-terminal-text">

      {/* ═══════════ Tab Row ═══════════ */}
      <div className="flex items-center gap-1.5 px-6 py-2.5 bg-terminal-panel border-b border-terminal-border">
        {(Object.keys(CHART_MODE_LABELS) as ChartMode[]).map((mode) => {
          const isActive = chartMode === mode;
          return (
            <button
              key={mode}
              onClick={() => setChartMode(mode)}
              className={clsx(
                'px-4 py-1.5 rounded-lg text-[11px] font-semibold uppercase tracking-wider transition-all duration-150',
                isActive
                  ? 'bg-terminal-card border border-terminal-border text-terminal-text shadow-elevation-1'
                  : 'border border-transparent text-terminal-text-muted hover:text-terminal-text-secondary hover:bg-terminal-card/50'
              )}
            >
              {CHART_MODE_LABELS[mode]}
            </button>
          );
        })}

        {/* CFPM engine badge */}
        <div className="ml-auto flex items-center gap-2">
          <span className="chip chip-info text-[9px]">CFPM</span>
          <span className="text-[10px] font-mono tabular-nums text-terminal-text-muted">
            b=142.5
          </span>
        </div>
      </div>

      {/* ═══════════ Main Grid ═══════════ */}
      <div className="flex-1 min-h-0 p-6 overflow-hidden">
        <div className="h-full flex flex-col min-h-0">
          <div className="grid grid-cols-12 gap-4 min-h-0 [min-height:0]">

            {/* Chart — col-span-9 */}
            <div className="col-span-9 flex flex-col min-h-0">
              {renderChartContent()}
            </div>

            {/* CFPM Impact & Cost — col-span-3 */}
            <div className="col-span-3 flex flex-col min-h-0">
              <ImpactCostPanel currentPrice={currentPrice} />
            </div>

            {/* Time & Sales — col-span-6 */}
            <div className="col-span-6 flex flex-col min-h-0">
              <TimeSalesPanel trades={trades} />
            </div>

            {/* Agent Leaderboard — col-span-3 */}
            <div className="col-span-3 flex flex-col min-h-0">
              <AgentLeaderboard agents={agents} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
            </div>

            {/* Signal Intercepts — col-span-3 */}
            <div className="col-span-3 flex flex-col min-h-0">
              <SignalInterceptsPanel intercepts={intercepts} />
            </div>

          </div>
        </div>
      </div>

      {/* ═══════════ Alert Overlay ═══════════ */}
      {alertPanelOpen && (
        <div
          className="fixed inset-0 z-[300] bg-black/50"
          onClick={() => setAlertPanelOpen(false)}
        />
      )}
      {alertPanelOpen && (
        <div
          ref={alertPanelRef}
          className="fixed top-[60px] right-6 w-96 max-h-[calc(100vh-80px)] rounded-xl flex flex-col overflow-hidden z-[310] shadow-elevation-3 bg-terminal-overlay border border-terminal-border"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="section-header">
            <span className="section-title-accented">Analytics Alerts</span>
            <button
              onClick={() => setAlertPanelOpen(false)}
              className="p-1 rounded transition-colors text-terminal-text-muted hover:text-terminal-text"
            >
              ✕
            </button>
          </div>
          <div className="p-4 overflow-y-auto max-h-[400px]">
            <p className="text-xs text-terminal-text-muted">No alerts configured for analytics.</p>
          </div>
        </div>
      )}

      {/* ═══════════ Compare Overlay ═══════════ */}
      {comparePanelOpen && (
        <div
          className="fixed inset-0 z-[300] bg-black/50"
          onClick={() => setComparePanelOpen(false)}
        />
      )}
      {comparePanelOpen && (
        <div
          ref={comparePanelRef}
          className="fixed top-[60px] right-6 w-96 max-h-[calc(100vh-80px)] rounded-xl flex flex-col overflow-hidden z-[310] shadow-elevation-3 bg-terminal-overlay border border-terminal-border"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="section-header">
            <span className="section-title-accented">Compare Theatres</span>
            <button
              onClick={() => setComparePanelOpen(false)}
              className="p-1 rounded transition-colors text-terminal-text-muted hover:text-terminal-text"
            >
              ✕
            </button>
          </div>
          <div className="p-4 overflow-y-auto max-h-[400px]">
            <p className="text-xs text-terminal-text-muted">Select theatres to compare.</p>
          </div>
        </div>
      )}

      {/* ═══════════ Settings Overlay ═══════════ */}
      {settingsPanelOpen && (
        <div
          className="fixed inset-0 z-[300] bg-black/50"
          onClick={() => setSettingsPanelOpen(false)}
        />
      )}
      {settingsPanelOpen && (
        <div
          ref={settingsPanelRef}
          className="fixed top-[60px] right-6 w-80 max-h-[calc(100vh-80px)] rounded-xl flex flex-col overflow-hidden z-[310] shadow-elevation-3 bg-terminal-overlay border border-terminal-border"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="section-header">
            <span className="section-title-accented">Analytics Settings</span>
            <button
              onClick={() => setSettingsPanelOpen(false)}
              className="p-1 rounded transition-colors text-terminal-text-muted hover:text-terminal-text"
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
