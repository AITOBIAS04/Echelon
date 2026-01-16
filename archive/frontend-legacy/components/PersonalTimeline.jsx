"use client";

import { useState, useEffect } from "react";
import useSWR from "swr";

// API config
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const fetcher = (url) => fetch(url).then(res => res.json());

/**
 * Personal Timeline View
 * ======================
 * Shows user's personal "multiverse" - their active bets as parallel realities.
 * 
 * Before betting: Shows only Master Timeline (Reality)
 * After betting: Shows split view - Reality (top) vs Their Simulation (bottom)
 */

// Timeline comparison metrics
function MetricDelta({ label, reality, simulation, unit = "", inverted = false }) {
  const delta = simulation - reality;
  const isPositive = inverted ? delta < 0 : delta > 0;
  const deltaPercent = reality !== 0 ? ((delta / reality) * 100) : 0;
  
  return (
    <div className="bg-gray-800/50 rounded-lg p-3">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className="flex justify-between items-end">
        <div className="text-lg font-mono text-white">
          {simulation.toFixed(1)}{unit}
        </div>
        <div className={`text-sm font-mono ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
          {delta >= 0 ? '+' : ''}{deltaPercent.toFixed(1)}%
        </div>
      </div>
    </div>
  );
}

// Single timeline visualization
function TimelineStrip({ timeline, isReality = false, metrics = {} }) {
  const statusColors = {
    master: "border-yellow-500 bg-yellow-900/20",
    active: "border-green-500 bg-green-900/20",
    completed: "border-blue-500 bg-blue-900/20",
    diverging: "border-purple-500 bg-purple-900/20",
  };
  
  return (
    <div className={`border-l-4 ${statusColors[timeline.status] || statusColors.active} p-4 rounded-r-lg`}>
      <div className="flex justify-between items-start mb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-lg">{isReality ? '🌍' : '🔮'}</span>
            <h3 className="font-bold text-white">{timeline.label || timeline.id}</h3>
            {isReality && (
              <span className="text-xs bg-yellow-600 text-black px-2 py-0.5 rounded">
                REALITY
              </span>
            )}
          </div>
          <p className="text-sm text-gray-400 mt-1">
            {isReality ? "What actually happened" : timeline.fork_reason || "Your simulation"}
          </p>
        </div>
        <div className="text-right">
          <div className="text-xs text-gray-500">Tick</div>
          <div className="text-lg font-mono text-purple-400">{metrics.tick || 0}</div>
        </div>
      </div>
      
      {/* Metrics row */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-gray-800/30 rounded p-2 text-center">
          <div className="text-xs text-gray-500">Tension</div>
          <div className={`text-lg font-mono ${
            (metrics.tension || 0) > 70 ? 'text-red-400' : 
            (metrics.tension || 0) > 40 ? 'text-yellow-400' : 'text-green-400'
          }`}>
            {(metrics.tension || 0).toFixed(0)}%
          </div>
        </div>
        <div className="bg-gray-800/30 rounded p-2 text-center">
          <div className="text-xs text-gray-500">Market Δ</div>
          <div className={`text-lg font-mono ${
            (metrics.marketChange || 0) >= 0 ? 'text-green-400' : 'text-red-400'
          }`}>
            {(metrics.marketChange || 0) >= 0 ? '+' : ''}{(metrics.marketChange || 0).toFixed(1)}%
          </div>
        </div>
        <div className="bg-gray-800/30 rounded p-2 text-center">
          <div className="text-xs text-gray-500">Events</div>
          <div className="text-lg font-mono text-blue-400">
            {metrics.events || 0}
          </div>
        </div>
      </div>
    </div>
  );
}

// Divergence point indicator
function DivergencePoint({ reason, timestamp }) {
  return (
    <div className="relative py-4">
      {/* Vertical line */}
      <div className="absolute left-1/2 top-0 bottom-0 w-px bg-purple-500/50" />
      
      {/* Divergence node */}
      <div className="relative flex justify-center">
        <div className="bg-purple-900 border-2 border-purple-500 rounded-lg px-4 py-2 max-w-md">
          <div className="flex items-center gap-2">
            <span className="text-purple-400">⚡</span>
            <span className="text-sm font-semibold text-purple-300">CAUSALITY BREACH</span>
          </div>
          <p className="text-xs text-gray-400 mt-1">{reason}</p>
          {timestamp && (
            <p className="text-xs text-gray-600 mt-1">
              {new Date(timestamp).toLocaleString()}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

// Main component
export default function PersonalTimeline({ userBets = [] }) {
  const [selectedBet, setSelectedBet] = useState(null);
  
  // Fetch user's active simulations
  const { data: simulations } = useSWR(
    `${API_BASE}/users/me/simulations`,
    fetcher,
    { 
      fallbackData: { simulations: [] },
      revalidateOnFocus: true,
    }
  );
  
  // Fetch reality timeline
  const { data: realityData } = useSWR(
    `${API_BASE}/timelines/REALITY`,
    fetcher,
    { 
      fallbackData: null,
      refreshInterval: 10000,
    }
  );
  
  // Mock data for demonstration
  const mockUserSimulations = userBets.length > 0 ? userBets.map((bet, i) => ({
    id: `SIM_${bet.marketId}_${i}`,
    label: bet.title || `Simulation #${i + 1}`,
    status: "active",
    fork_reason: bet.outcome === "YES" 
      ? `Betting YES on: ${bet.title}` 
      : `Betting NO on: ${bet.title}`,
    metrics: {
      tick: Math.floor(Math.random() * 100),
      tension: Math.random() * 100,
      marketChange: (Math.random() - 0.5) * 20,
      events: Math.floor(Math.random() * 10),
    },
    bet: bet,
    divergenceReason: `User bet $${bet.amount} on ${bet.outcome}`,
    divergenceTime: new Date().toISOString(),
  })) : [];
  
  const activeSimulations = simulations?.simulations || mockUserSimulations;
  
  // Reality metrics
  const realityMetrics = {
    tick: realityData?.tick || 42,
    tension: realityData?.global_tension || 35,
    marketChange: 2.3,
    events: realityData?.event_count || 5,
  };
  
  const realityTimeline = {
    id: "REALITY",
    label: "Reality (Master)",
    status: "master",
  };

  // No active bets - show only reality
  if (activeSimulations.length === 0) {
    return (
      <div className="bg-gray-900 rounded-xl p-6">
        <h2 className="text-2xl font-bold text-white mb-2 flex items-center gap-2">
          🌌 Your Multiverse
        </h2>
        <p className="text-gray-400 mb-6">
          Place a bet to create your own parallel reality
        </p>
        
        {/* Reality only view */}
        <div className="border border-gray-700 rounded-lg p-4 bg-gray-800/30">
          <TimelineStrip 
            timeline={realityTimeline} 
            isReality={true}
            metrics={realityMetrics}
          />
        </div>
        
        {/* Call to action */}
        <div className="mt-6 text-center p-8 border-2 border-dashed border-gray-700 rounded-lg">
          <div className="text-4xl mb-3">🔮</div>
          <h3 className="text-lg font-semibold text-white mb-2">
            No Active Simulations
          </h3>
          <p className="text-gray-400 text-sm mb-4">
            When you place a bet, we fork reality and run a simulation 
            based on your prediction. Watch how your timeline diverges!
          </p>
          <a 
            href="/markets" 
            className="inline-block bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg transition-colors"
          >
            Browse Markets →
          </a>
        </div>
      </div>
    );
  }

  // Has active bets - show split view
  return (
    <div className="bg-gray-900 rounded-xl p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            🌌 Your Multiverse
          </h2>
          <p className="text-gray-400">
            {activeSimulations.length} active simulation{activeSimulations.length !== 1 ? 's' : ''} running
          </p>
        </div>
        
        {/* Simulation selector if multiple */}
        {activeSimulations.length > 1 && (
          <select 
            value={selectedBet?.id || activeSimulations[0]?.id}
            onChange={(e) => setSelectedBet(activeSimulations.find(s => s.id === e.target.value))}
            className="bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-white"
          >
            {activeSimulations.map(sim => (
              <option key={sim.id} value={sim.id}>
                {sim.label}
              </option>
            ))}
          </select>
        )}
      </div>
      
      {/* Split View */}
      <div className="space-y-2">
        {/* Reality (Top) */}
        <div className="border border-gray-700 rounded-lg p-4 bg-gray-800/30">
          <TimelineStrip 
            timeline={realityTimeline} 
            isReality={true}
            metrics={realityMetrics}
          />
        </div>
        
        {/* Divergence Point */}
        <DivergencePoint 
          reason={(selectedBet || activeSimulations[0])?.divergenceReason || "Simulation forked"} 
          timestamp={(selectedBet || activeSimulations[0])?.divergenceTime}
        />
        
        {/* User's Simulation (Bottom) */}
        <div className="border border-purple-700/50 rounded-lg p-4 bg-purple-900/10">
          <TimelineStrip 
            timeline={selectedBet || activeSimulations[0]} 
            isReality={false}
            metrics={(selectedBet || activeSimulations[0])?.metrics || {}}
          />
        </div>
      </div>
      
      {/* Comparison Metrics */}
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricDelta 
          label="Tension Score"
          reality={realityMetrics.tension}
          simulation={(selectedBet || activeSimulations[0])?.metrics?.tension || 0}
          unit="%"
          inverted={true}
        />
        <MetricDelta 
          label="Market Change"
          reality={realityMetrics.marketChange}
          simulation={(selectedBet || activeSimulations[0])?.metrics?.marketChange || 0}
          unit="%"
        />
        <MetricDelta 
          label="Event Count"
          reality={realityMetrics.events}
          simulation={(selectedBet || activeSimulations[0])?.metrics?.events || 0}
        />
        <MetricDelta 
          label="Sim Progress"
          reality={realityMetrics.tick}
          simulation={(selectedBet || activeSimulations[0])?.metrics?.tick || 0}
        />
      </div>
      
      {/* Bet info */}
      {(selectedBet || activeSimulations[0])?.bet && (
        <div className="mt-6 bg-gray-800/50 rounded-lg p-4 border border-gray-700">
          <div className="flex justify-between items-center">
            <div>
              <div className="text-sm text-gray-400">Your Position</div>
              <div className="text-lg font-bold text-white">
                ${(selectedBet || activeSimulations[0]).bet.amount} on {(selectedBet || activeSimulations[0]).bet.outcome}
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-400">Potential Payout</div>
              <div className="text-lg font-bold text-green-400">
                ${((selectedBet || activeSimulations[0]).bet.amount * 1.95).toFixed(2)}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Export a simpler version for dashboard
export function PersonalTimelineCompact({ bet }) {
  if (!bet) return null;
  
  return (
    <div className="bg-gray-800/50 border border-purple-700/30 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">🔮</span>
        <span className="font-semibold text-white">Active Simulation</span>
      </div>
      <p className="text-sm text-gray-400 mb-3">{bet.title}</p>
      <div className="flex justify-between text-sm">
        <span className="text-gray-500">Your bet:</span>
        <span className="text-purple-400">${bet.amount} on {bet.outcome}</span>
      </div>
      <div className="mt-2 h-1 bg-gray-700 rounded-full overflow-hidden">
        <div 
          className="h-full bg-purple-500 animate-pulse"
          style={{ width: `${Math.random() * 60 + 20}%` }}
        />
      </div>
      <p className="text-xs text-gray-600 mt-1">Simulation in progress...</p>
    </div>
  );
}




