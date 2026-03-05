/**
 * Analytics Page (formerly Blackbox)
 *
 * Real data: Agent Leaderboard, Market prices from timeline health.
 * Coming Soon: Heatmap, Depth Chart, Volume Profile, Time & Sales.
 */

import { useState } from 'react';
import { PriceChart } from '../components/blackbox/PriceChart';
import { ImpactCostPanel } from '../components/blackbox/ImpactCostPanel';
import { AgentLeaderboard } from '../components/blackbox/AgentLeaderboard';
import {
  useBlackboxChart,
  useAgentLeaderboard,
} from '../hooks/useBlackbox';
import type { Timeframe } from '../types/blackbox';

function ComingSoonPanel({ title }: { title: string }) {
  return (
    <div className="bg-terminal-panel border border-terminal-border rounded-xl p-6 flex flex-col items-center justify-center gap-2 min-h-[200px]">
      <span className="text-xs font-semibold text-terminal-text-muted uppercase tracking-wider">
        {title}
      </span>
      <span className="text-[10px] text-terminal-text-muted">Coming Soon</span>
    </div>
  );
}

export function BlackboxPage() {
  const [timeframe, setTimeframe] = useState<Timeframe>('15m');

  const { candles, currentPrice, indicators } = useBlackboxChart(timeframe);
  const { agents, searchQuery, setSearchQuery } = useAgentLeaderboard();

  return (
    <div className="h-full w-full flex flex-col min-h-0 bg-terminal-bg text-terminal-text">
      {/* Main Grid */}
      <div className="flex-1 min-h-0 p-6 overflow-auto">
        <div className="grid grid-cols-12 gap-4">
          {/* Price Chart — col-span-9 */}
          <div className="col-span-9 flex flex-col min-h-0">
            {candles.length > 0 ? (
              <PriceChart
                candles={candles}
                currentPrice={currentPrice}
                indicators={indicators}
                timeframe={timeframe}
                onTimeframeChange={setTimeframe}
              />
            ) : (
              <ComingSoonPanel title="Price Action" />
            )}
          </div>

          {/* CFPM Impact & Cost — col-span-3 */}
          <div className="col-span-3 flex flex-col min-h-0">
            <ImpactCostPanel currentPrice={currentPrice} />
          </div>

          {/* Time & Sales — col-span-6 (Coming Soon) */}
          <div className="col-span-6">
            <ComingSoonPanel title="Time & Sales" />
          </div>

          {/* Agent Leaderboard — col-span-3 (Real Data) */}
          <div className="col-span-3 flex flex-col min-h-0">
            <AgentLeaderboard
              agents={agents}
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
            />
          </div>

          {/* Signal Intercepts — col-span-3 (Coming Soon) */}
          <div className="col-span-3">
            <ComingSoonPanel title="Signal Intercepts" />
          </div>
        </div>
      </div>
    </div>
  );
}
