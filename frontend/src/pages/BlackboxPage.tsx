// Blackbox Page Component
// Market Terminal - Analytics interface inside AppLayout

import { useState, useEffect, useRef } from 'react';
import { PriceChart } from '../components/blackbox/PriceChart';
import { OrderBookPanel } from '../components/blackbox/OrderBookPanel';
import { TimeSalesPanel } from '../components/blackbox/TimeSalesPanel';
import { AgentLeaderboard } from '../components/blackbox/AgentLeaderboard';
import { SignalInterceptsPanel } from '../components/blackbox/SignalInterceptsPanel';
import {
  useBlackboxChart,
  useOrderBook,
  useTimeSales,
  useAgentLeaderboard,
  useIntercepts,
} from '../hooks/useBlackbox';
import { useRegisterTopActionBarActions } from '../contexts/TopActionBarActionsContext';
import type { Timeframe } from '../types/blackbox';

export function BlackboxPage() {
  const [timeframe, setTimeframe] = useState<Timeframe>('15m');
  
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

  return (
    <div className="h-full flex flex-col" style={{ backgroundColor: '#0B0C0E', color: '#F1F5F9' }}>
      
      {/* Market Terminal Grid */}
      <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
        <div className="flex-1 min-h-0 flex flex-col p-4 overflow-hidden">
          
          {/* Main Grid Layout */}
          <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
            
            {/* Top Section: Price Chart */}
            <div className="flex-shrink-0" style={{ height: '40%', minHeight: 200 }}>
              <PriceChart
                candles={candles}
                currentPrice={currentPrice}
                indicators={indicators}
                timeframe={timeframe}
                onTimeframeChange={setTimeframe}
              />
            </div>
            
            {/* Bottom Section: Split Grid */}
            <div className="flex-1 min-h-0 flex flex-row gap-4 mt-4 overflow-hidden">
              
              {/* Left: Time & Sales */}
              <div className="flex-1 min-w-0 overflow-hidden" style={{ minWidth: 0 }}>
                <TimeSalesPanel trades={trades} />
              </div>
              
              {/* Center: Agent Performance */}
              <div className="flex-1 min-w-0 overflow-hidden" style={{ minWidth: 0 }}>
                <AgentLeaderboard agents={agents} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
              </div>
              
              {/* Right Sidebar: Order Book + Signal Intercepts */}
              <div className="w-80 flex-shrink-0 flex flex-col gap-4 overflow-hidden">
                <OrderBookPanel orderBook={orderBook} currentPrice={currentPrice} />
                <SignalInterceptsPanel intercepts={intercepts} />
              </div>
              
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
          className="fixed top-[60px] right-6 w-96 max-h-[calc(100vh-80px)] rounded-xl flex flex-col overflow-hidden z-50 shadow-xl"
          onClick={(e) => e.stopPropagation()}
          style={{
            background: '#151719',
            border: '1px solid #26292E',
          }}
        >
          <div className="flex items-center justify-between px-4 py-3 border-b" style={{ background: '#121417', borderColor: '#26292E' }}>
            <span className="text-sm font-semibold" style={{ color: '#F1F5F9' }}>Analytics Alerts</span>
            <button
              onClick={() => setAlertPanelOpen(false)}
              className="p-1 rounded transition-colors"
              style={{ color: '#64748B' }}
            >
              ✕
            </button>
          </div>
          <div className="p-4 overflow-y-auto" style={{ maxHeight: 400 }}>
            <p className="text-xs" style={{ color: '#64748B' }}>No alerts configured for analytics.</p>
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
          className="fixed top-[60px] right-6 w-96 max-h-[calc(100vh-80px)] rounded-xl flex flex-col overflow-hidden z-50 shadow-xl"
          onClick={(e) => e.stopPropagation()}
          style={{
            background: '#151719',
            border: '1px solid #26292E',
          }}
        >
          <div className="flex items-center justify-between px-4 py-3 border-b" style={{ background: '#121417', borderColor: '#26292E' }}>
            <span className="text-sm font-semibold" style={{ color: '#F1F5F9' }}>Compare Theatres</span>
            <button
              onClick={() => setComparePanelOpen(false)}
              className="p-1 rounded transition-colors"
              style={{ color: '#64748B' }}
            >
              ✕
            </button>
          </div>
          <div className="p-4 overflow-y-auto" style={{ maxHeight: 400 }}>
            <p className="text-xs" style={{ color: '#64748B' }}>Select theatres to compare.</p>
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
          className="fixed top-[60px] right-6 w-80 max-h-[calc(100vh-80px)] rounded-xl flex flex-col overflow-hidden z-50 shadow-xl"
          onClick={(e) => e.stopPropagation()}
          style={{
            background: '#151719',
            border: '1px solid #26292E',
          }}
        >
          <div className="flex items-center justify-between px-4 py-3 border-b" style={{ background: '#121417', borderColor: '#26292E' }}>
            <span className="text-sm font-semibold" style={{ color: '#F1F5F9' }}>Analytics Settings</span>
            <button
              onClick={() => setSettingsPanelOpen(false)}
              className="p-1 rounded transition-colors"
              style={{ color: '#64748B' }}
            >
              ✕
            </button>
          </div>
          <div className="p-4">
            <p className="text-xs" style={{ color: '#64748B' }}>Settings panel stub.</p>
          </div>
        </div>
      )}
    </div>
  );
}
