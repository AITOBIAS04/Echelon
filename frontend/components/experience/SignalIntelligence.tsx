"use client";

import { useState } from "react";
import useSWR from "swr";
import {
  Copy,
  UserPlus,
  X,
  Shield,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Minus,
  Bell,
  LogOut,
} from "lucide-react";
import { LiveFeed } from "./LiveFeed";
import { DataCard } from "./DataCard";
import { ConfidenceMeter } from "./ConfidenceMeter";
import { ProgressRing } from "./ProgressRing";
import { StatusIndicator } from "./StatusIndicator";

type Tab = "signals" | "health" | "forces";

interface SignalIntelligenceProps {
  defaultTab?: Tab;
  marketId?: string;
}

interface SignalItem {
  id: string;
  timestamp: Date | string;
  label: string;
  message: string;
  level: "info" | "success" | "warning" | "danger";
  signalType: string;
  agentName: string;
  agentColor: string;
}

interface TimelineHealth {
  timelineName: string;
  status: "STABLE" | "DEGRADING" | "CRITICAL";
  timeToCollapse: number; // seconds
  realityAlignment: number;
  stabilityIndex: number;
  decayRate: number;
  sabotagePressure: number;
  shieldCoverage: number;
  netMomentum: "BULLISH" | "BEARISH" | "NEUTRAL";
}

interface MarketForce {
  marketId: string;
  marketName: string;
  sabotageAmount: number;
  shieldAmount: number;
  currentPrice: number;
  topSaboteurs: Array<{ agentName: string; amount: number; isUser?: boolean }>;
  topDefenders: Array<{ agentName: string; amount: number; isUser?: boolean }>;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const fetcher = (url: string) => fetch(url).then((res) => res.json());

// Mock data generators
const generateMockSignals = (): SignalItem[] => {
  const types = [
    { type: "DIVERGENCE DETECTED", level: "warning" as const },
    { type: "ACCUMULATION ALERT", level: "danger" as const },
    { type: "POSITION CLOSED", level: "info" as const },
    { type: "INTEL PUBLISHED", level: "success" as const },
  ];

  const agents = [
    { name: "CARDINAL", color: "#6366f1" },
    { name: "SENTINEL", color: "#22c55e" },
    { name: "RAVEN", color: "#f59e0b" },
    { name: "PHOENIX", color: "#ef4444" },
  ];

  return Array.from({ length: 10 }, (_, i) => {
    const type = types[Math.floor(Math.random() * types.length)];
    const agent = agents[Math.floor(Math.random() * agents.length)];
    return {
      id: `sig-${i}`,
      timestamp: new Date(Date.now() - i * 60000),
      label: type.type,
      message: `${agent.name} ${type.type.toLowerCase()}: Market activity detected`,
      level: type.level,
      signalType: type.type,
      agentName: agent.name,
      agentColor: agent.color,
    };
  });
};

const generateMockTimelineHealth = (): TimelineHealth => ({
  timelineName: "The Tanker War",
  status: "DEGRADING",
  timeToCollapse: 7200, // 2 hours
  realityAlignment: 73,
  stabilityIndex: 58,
  decayRate: 2.3,
  sabotagePressure: 45,
  shieldCoverage: 32,
  netMomentum: "BEARISH",
});

const generateMockMarketForces = (marketId?: string): MarketForce => ({
  marketId: marketId || "market-1",
  marketName: "Strait of Hormuz Closure",
  sabotageAmount: 125000,
  shieldAmount: 89000,
  currentPrice: 0.62,
  topSaboteurs: [
    { agentName: "CARDINAL", amount: 45000, isUser: false },
    { agentName: "RAVEN", amount: 32000, isUser: false },
    { agentName: "You", amount: 25000, isUser: true },
    { agentName: "PHOENIX", amount: 23000, isUser: false },
  ],
  topDefenders: [
    { agentName: "SENTINEL", amount: 38000, isUser: false },
    { agentName: "GUARDIAN", amount: 28000, isUser: false },
    { agentName: "You", amount: 15000, isUser: true },
    { agentName: "WARDEN", amount: 8000, isUser: false },
  ],
});

export default function SignalIntelligence({
  defaultTab = "signals",
  marketId,
}: SignalIntelligenceProps) {
  const [activeTab, setActiveTab] = useState<Tab>(defaultTab);
  const [selectedMarket, setSelectedMarket] = useState(marketId || "market-1");

  // Fetch signals
  const { data: signals, mutate: mutateSignals } = useSWR<SignalItem[]>(
    `${API_BASE}/api/agents/signals`,
    fetcher,
    {
      refreshInterval: 5000,
      fallbackData: generateMockSignals(),
      onError: () => {
        // Use mock data on error
      },
    }
  );

  // Fetch timeline health
  const { data: timelineHealth, mutate: mutateHealth } = useSWR<TimelineHealth>(
    `${API_BASE}/api/timeline/health`,
    fetcher,
    {
      refreshInterval: 10000,
      fallbackData: generateMockTimelineHealth(),
    }
  );

  // Fetch market forces
  const { data: marketForces, mutate: mutateForces } = useSWR<MarketForce>(
    `${API_BASE}/api/markets/${selectedMarket}/forces`,
    fetcher,
    {
      refreshInterval: 10000,
      fallbackData: generateMockMarketForces(selectedMarket),
    }
  );

  const handleCopySignal = (signalId: string) => {
    const signal = signals?.find((s) => s.id === signalId);
    if (signal) {
      navigator.clipboard.writeText(
        `${signal.signalType}: ${signal.message}`
      );
    }
  };

  const handleFollowAgent = (agentName: string) => {
    // TODO: Implement follow agent
    console.log("Follow agent:", agentName);
  };

  const handleDismissSignal = (signalId: string) => {
    // TODO: Implement dismiss signal
    mutateSignals((current) =>
      current?.filter((s) => s.id !== signalId) || []
    );
  };

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  const totalForce = marketForces
    ? marketForces.sabotageAmount + marketForces.shieldAmount
    : 0;
  const sabotagePercent = marketForces
    ? (marketForces.sabotageAmount / totalForce) * 100
    : 50;
  const shieldPercent = marketForces
    ? (marketForces.shieldAmount / totalForce) * 100
    : 50;

  return (
    <div className="w-full h-full bg-[#0a0a0f] flex flex-col min-h-0">
      {/* Tab Bar */}
      <div className="flex border-b border-slate-700/30 flex-shrink-0">
        {[
          { id: "signals", label: "AGENT SIGNALS" },
          { id: "health", label: "TIMELINE HEALTH" },
          { id: "forces", label: "MARKET FORCES" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as Tab)}
            className={`px-6 py-3 text-sm font-mono transition-all duration-300 ${
              activeTab === tab.id
                ? "bg-[#12121a] text-slate-200 border-b-2 border-[#6366f1]"
                : "text-slate-400 hover:text-slate-300 hover:bg-[#12121a]/50"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === "signals" && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-slate-200 font-sans mb-4">
              Agent Signals
            </h2>
            <LiveFeed
              items={
                signals?.map((signal) => ({
                  id: signal.id,
                  timestamp: signal.timestamp,
                  label: signal.signalType,
                  message: signal.message,
                  level: signal.level,
                })) || []
              }
              title="Live Agent Activity"
            />
            {/* Custom rendering for signals with action buttons */}
            <div className="space-y-2 mt-4">
              {signals?.map((signal) => (
                <DataCard
                  key={signal.id}
                  title=""
                  priority={
                    signal.level === "danger"
                      ? "danger"
                      : signal.level === "warning"
                      ? "warning"
                      : signal.level === "success"
                      ? "success"
                      : "none"
                  }
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-xs font-mono text-slate-400">
                          {new Date(signal.timestamp).toLocaleTimeString()}
                        </span>
                        <span
                          className={`text-xs font-mono px-2 py-0.5 rounded ${
                            signal.level === "danger"
                              ? "bg-red-500/20 text-red-300"
                              : signal.level === "warning"
                              ? "bg-amber-500/20 text-amber-300"
                              : signal.level === "success"
                              ? "bg-green-500/20 text-green-300"
                              : "bg-slate-500/20 text-slate-300"
                          }`}
                        >
                          {signal.signalType}
                        </span>
                        <span
                          className="text-sm font-mono font-semibold"
                          style={{ color: signal.agentColor }}
                        >
                          {signal.agentName}
                        </span>
                      </div>
                      <p className="text-sm text-slate-300">{signal.message}</p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleCopySignal(signal.id)}
                        className="p-2 hover:bg-[#12121a] rounded transition-all duration-300"
                        title="Copy"
                      >
                        <Copy className="w-4 h-4 text-slate-400" />
                      </button>
                      <button
                        onClick={() => handleFollowAgent(signal.agentName)}
                        className="p-2 hover:bg-[#12121a] rounded transition-all duration-300"
                        title="Follow"
                      >
                        <UserPlus className="w-4 h-4 text-slate-400" />
                      </button>
                      <button
                        onClick={() => handleDismissSignal(signal.id)}
                        className="p-2 hover:bg-[#12121a] rounded transition-all duration-300"
                        title="Dismiss"
                      >
                        <X className="w-4 h-4 text-slate-400" />
                      </button>
                    </div>
                  </div>
                </DataCard>
              ))}
            </div>
          </div>
        )}

        {activeTab === "health" && timelineHealth && (
          <div className="space-y-6">
            {/* Top Row - Status Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <DataCard
                title={timelineHealth.timelineName}
                priority={
                  timelineHealth.status === "CRITICAL"
                    ? "danger"
                    : timelineHealth.status === "DEGRADING"
                    ? "warning"
                    : "success"
                }
                headerAddon={
                  <StatusIndicator
                    status={
                      timelineHealth.status === "CRITICAL"
                        ? "CRITICAL"
                        : timelineHealth.status === "DEGRADING"
                        ? "PROCESSING"
                        : "LIVE"
                    }
                    label={timelineHealth.status}
                  />
                }
              >
                <div className="space-y-3">
                  <div>
                    <div className="text-xs text-slate-400 mb-1">
                      Time to Estimated Collapse
                    </div>
                    <div className="text-lg font-mono text-slate-200">
                      {formatTime(timelineHealth.timeToCollapse)}
                    </div>
                  </div>
                </div>
              </DataCard>
            </div>

            {/* Metrics Grid */}
            <div>
              <h3 className="text-md font-semibold text-slate-200 font-sans mb-4">
                Stability Metrics
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <DataCard title="Reality Alignment" priority="none">
                  <ConfidenceMeter
                    value={timelineHealth.realityAlignment}
                    variant="bar"
                    label=""
                  />
                  <div className="text-xs text-slate-400 mt-2">
                    {timelineHealth.realityAlignment}% match with real events
                  </div>
                </DataCard>

                <DataCard title="Stability Index" priority="none">
                  <ConfidenceMeter
                    value={timelineHealth.stabilityIndex}
                    variant="bar"
                    label=""
                  />
                  <div className="text-xs text-slate-400 mt-2">
                    Resistance to collapse
                  </div>
                </DataCard>

                <DataCard title="Decay Rate" priority="none">
                  <div className="text-2xl font-mono text-slate-200">
                    {timelineHealth.decayRate}%
                  </div>
                  <div className="text-xs text-slate-400 mt-2">per hour</div>
                </DataCard>
              </div>
            </div>

            {/* Pressure Analysis */}
            <DataCard title="Pressure Analysis" priority="none">
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-400">
                      Sabotage Pressure
                    </span>
                    <span className="text-sm font-mono text-red-300">
                      {timelineHealth.sabotagePressure}%
                    </span>
                  </div>
                  <ConfidenceMeter
                    value={timelineHealth.sabotagePressure}
                    variant="bar"
                    label=""
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-400">
                      Shield Coverage
                    </span>
                    <span className="text-sm font-mono text-green-300">
                      {timelineHealth.shieldCoverage}%
                    </span>
                  </div>
                  <ConfidenceMeter
                    value={timelineHealth.shieldCoverage}
                    variant="bar"
                    label=""
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-400">Net Momentum</span>
                    <span
                      className={`text-sm font-mono font-semibold ${
                        timelineHealth.netMomentum === "BULLISH"
                          ? "text-green-300"
                          : timelineHealth.netMomentum === "BEARISH"
                          ? "text-red-300"
                          : "text-slate-300"
                      }`}
                    >
                      {timelineHealth.netMomentum}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    {timelineHealth.netMomentum === "BULLISH" && (
                      <TrendingUp className="w-5 h-5 text-green-300" />
                    )}
                    {timelineHealth.netMomentum === "BEARISH" && (
                      <TrendingDown className="w-5 h-5 text-red-300" />
                    )}
                    {timelineHealth.netMomentum === "NEUTRAL" && (
                      <Minus className="w-5 h-5 text-slate-300" />
                    )}
                    <div className="flex-1 h-1 bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all duration-500 ${
                          timelineHealth.netMomentum === "BULLISH"
                            ? "bg-green-500"
                            : timelineHealth.netMomentum === "BEARISH"
                            ? "bg-red-500"
                            : "bg-slate-500"
                        }`}
                        style={{
                          width: `${
                            timelineHealth.netMomentum === "BULLISH"
                              ? 60
                              : timelineHealth.netMomentum === "BEARISH"
                              ? 40
                              : 50
                          }%`,
                        }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </DataCard>

            {/* Action Buttons */}
            <div className="flex gap-4">
              <button className="px-4 py-2 bg-[#6366f1] hover:bg-[#6366f1]/80 text-white rounded-lg text-sm font-mono transition-all duration-300 flex items-center gap-2">
                <Shield className="w-4 h-4" />
                Deploy Shield $50
              </button>
              <button className="px-4 py-2 bg-[#ef4444] hover:bg-[#ef4444]/80 text-white rounded-lg text-sm font-mono transition-all duration-300 flex items-center gap-2">
                <LogOut className="w-4 h-4" />
                Exit All Positions
              </button>
              <button className="px-4 py-2 bg-[#12121a] hover:bg-[#12121a]/80 text-slate-300 border border-slate-700 rounded-lg text-sm font-mono transition-all duration-300 flex items-center gap-2">
                <Bell className="w-4 h-4" />
                Set Alert
              </button>
            </div>
          </div>
        )}

        {activeTab === "forces" && marketForces && (
          <div className="space-y-6">
            {/* Market Selector */}
            <div>
              <label className="block text-sm text-slate-400 mb-2 font-sans">
                Select Market
              </label>
              <select
                value={selectedMarket}
                onChange={(e) => setSelectedMarket(e.target.value)}
                className="px-4 py-2 bg-[#0a0a0f] border border-slate-700 rounded-lg text-slate-200 font-mono focus:outline-none focus:ring-2 focus:ring-[#6366f1]"
              >
                <option value="market-1">Strait of Hormuz Closure</option>
                <option value="market-2">Oil Price Shock</option>
                <option value="market-3">Naval Blockade</option>
              </select>
            </div>

            {/* Tug-of-War Visualization */}
            <DataCard title="Market Forces" priority="none">
              <div className="space-y-4">
                <div className="relative h-16 bg-[#0a0a0f] rounded-lg border border-slate-700 overflow-hidden">
                  {/* Sabotage side (left) */}
                  <div
                    className="absolute left-0 top-0 h-full bg-red-500/30 transition-all duration-500 flex items-center justify-end pr-4"
                    style={{ width: `${sabotagePercent}%` }}
                  >
                    <span className="text-xs font-mono text-red-300">
                      ${(marketForces.sabotageAmount / 1000).toFixed(0)}k
                    </span>
                  </div>

                  {/* Shield side (right) */}
                  <div
                    className="absolute right-0 top-0 h-full bg-green-500/30 transition-all duration-500 flex items-center justify-start pl-4"
                    style={{ width: `${shieldPercent}%` }}
                  >
                    <span className="text-xs font-mono text-green-300">
                      ${(marketForces.shieldAmount / 1000).toFixed(0)}k
                    </span>
                  </div>

                  {/* Center marker */}
                  <div
                    className="absolute top-0 bottom-0 w-0.5 bg-slate-200 transition-all duration-500"
                    style={{ left: `${marketForces.currentPrice * 100}%` }}
                  >
                    <div className="absolute -top-2 left-1/2 transform -translate-x-1/2 w-4 h-4 bg-slate-200 rounded-full" />
                  </div>

                  {/* Labels */}
                  <div className="absolute inset-0 flex items-center justify-between px-4 pointer-events-none">
                    <span className="text-xs font-mono text-red-300 font-semibold">
                      SABOTAGE
                    </span>
                    <span className="text-xs font-mono text-slate-400">
                      {marketForces.currentPrice.toFixed(2)}
                    </span>
                    <span className="text-xs font-mono text-green-300 font-semibold">
                      SHIELDS
                    </span>
                  </div>
                </div>
              </div>
            </DataCard>

            {/* Leaderboards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <DataCard title="Top Saboteurs" priority="danger">
                <div className="space-y-2">
                  {marketForces.topSaboteurs.map((agent, idx) => (
                    <div
                      key={idx}
                      className={`flex items-center justify-between p-2 rounded ${
                        agent.isUser ? "bg-red-500/20 border border-red-500/30" : ""
                      }`}
                    >
                      <span className="text-sm font-mono text-slate-300">
                        {idx + 1}. {agent.agentName}
                        {agent.isUser && (
                          <span className="ml-2 text-xs text-red-300">(You)</span>
                        )}
                      </span>
                      <span className="text-sm font-mono text-red-300">
                        ${(agent.amount / 1000).toFixed(1)}k
                      </span>
                    </div>
                  ))}
                </div>
              </DataCard>

              <DataCard title="Top Defenders" priority="success">
                <div className="space-y-2">
                  {marketForces.topDefenders.map((agent, idx) => (
                    <div
                      key={idx}
                      className={`flex items-center justify-between p-2 rounded ${
                        agent.isUser ? "bg-green-500/20 border border-green-500/30" : ""
                      }`}
                    >
                      <span className="text-sm font-mono text-slate-300">
                        {idx + 1}. {agent.agentName}
                        {agent.isUser && (
                          <span className="ml-2 text-xs text-green-300">(You)</span>
                        )}
                      </span>
                      <span className="text-sm font-mono text-green-300">
                        ${(agent.amount / 1000).toFixed(1)}k
                      </span>
                    </div>
                  ))}
                </div>
              </DataCard>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-4">
              <button className="px-4 py-2 bg-[#ef4444] hover:bg-[#ef4444]/80 text-white rounded-lg text-sm font-mono transition-all duration-300 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                Join Attack $50
              </button>
              <button className="px-4 py-2 bg-[#22c55e] hover:bg-[#22c55e]/80 text-white rounded-lg text-sm font-mono transition-all duration-300 flex items-center gap-2">
                <Shield className="w-4 h-4" />
                Deploy Shield $50
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

