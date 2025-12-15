"use client";

/**
 * THE SITUATION ROOM
 * ===================
 * 
 * Geopolitical Strategy RPG Interface
 * 
 * Features:
 * - Operations Centre (replaces Mission Board)
 * - Network Graph (replaces Storylines)
 * - Signal Intelligence
 * - Agent Deployment
 * - Intel Market
 * - Treaty Monitor
 * - Global Tension Gauge
 * - Handler AI Assistant
 * - "Who is the Mole?" Mystery Market
 */

import { useState, useEffect, useCallback } from "react";
import useSWR from "swr";
import dynamic from "next/dynamic";
import {
  OperationCentre,
  NetworkGraph,
  SignalIntelligence,
  Handler,
  StatusIndicator,
} from "@/components/experience";
import { useHandler, HandlerContext } from "@/lib/handlers";

// Dynamically import Polyglobe to prevent SSR issues
const Polyglobe = dynamic(() => import("@/components/Polyglobe"), {
  ssr: false,
  loading: () => (
    <div className="h-[400px] w-full bg-black/80 border border-amber-900/30 rounded-xl flex items-center justify-center">
      <div className="text-amber-500 animate-pulse font-mono">
        INITIALIZING GLOBE...
      </div>
    </div>
  ),
});

// API Configuration
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const fetcher = (url) => fetch(url).then((res) => res.json());

// =============================================================================
// CONFIGURATION
// =============================================================================

// Alert Level Config (replacing DEFCON)
const ALERT_LEVEL_CONFIG = {
  1: {
    color: "from-red-600 to-red-800",
    pulse: true,
    text: "WAR IMMINENT",
    icon: "🔴",
  },
  2: {
    color: "from-orange-600 to-orange-800",
    pulse: true,
    text: "CRISIS",
    icon: "🟠",
  },
  3: {
    color: "from-yellow-600 to-yellow-800",
    pulse: false,
    text: "ELEVATED",
    icon: "🟡",
  },
  4: {
    color: "from-blue-600 to-blue-800",
    pulse: false,
    text: "GUARDED",
    icon: "🔵",
  },
  5: {
    color: "from-green-600 to-green-800",
    pulse: false,
    text: "STABLE",
    icon: "🟢",
  },
};

// Faction Config
const FACTIONS = {
  eastern_bloc: {
    icon: "🔴",
    color: "text-red-400",
    name: "Eastern Bloc",
  },
  western_alliance: {
    icon: "🔵",
    color: "text-blue-400",
    name: "Western Alliance",
  },
  corporate: {
    icon: "🏢",
    color: "text-yellow-400",
    name: "Corporate",
  },
  underground: {
    icon: "🕳️",
    color: "text-purple-400",
    name: "Underground",
  },
  non_aligned: {
    icon: "⚪",
    color: "text-gray-400",
    name: "Non-Aligned",
  },
};

// =============================================================================
// COMPONENTS
// =============================================================================

// Global Tension Gauge
function TensionGauge({ tension, chaos }) {
  const tensionPercent = Math.round(tension * 100);
  const chaosPercent = Math.round(chaos * 100);

  const alertLevel =
    tension > 0.9
      ? 1
      : tension > 0.7
      ? 2
      : tension > 0.5
      ? 3
      : tension > 0.3
      ? 4
      : 5;
  const config = ALERT_LEVEL_CONFIG[alertLevel];

  return (
    <div
      className={`p-4 rounded-xl bg-gradient-to-br ${config.color} ${
        config.pulse ? "animate-pulse" : ""
      }`}
    >
      <div className="flex justify-between items-center mb-2">
        <span className="text-white/80 text-sm font-mono">GLOBAL TENSION</span>
        <span className="text-white font-bold">
          {config.icon} {config.text}
        </span>
      </div>

      {/* Tension Bar */}
      <div className="h-4 bg-black/30 rounded-full overflow-hidden mb-3">
        <div
          className="h-full bg-gradient-to-r from-green-500 via-yellow-500 to-red-500 transition-all duration-1000"
          style={{ width: `${tensionPercent}%` }}
        />
      </div>
      <div className="flex justify-between text-xs text-white/60">
        <span>PEACE</span>
        <span className="text-white font-bold">{tensionPercent}%</span>
        <span>WAR</span>
      </div>

      {/* Chaos Index */}
      <div className="mt-3 pt-3 border-t border-white/20">
        <div className="flex justify-between text-xs mb-1">
          <span className="text-white/60">CHAOS INDEX</span>
          <span className="text-white">{chaosPercent}%</span>
        </div>
        <div className="h-2 bg-black/30 rounded-full overflow-hidden">
          <div
            className="h-full bg-purple-500 transition-all duration-500"
            style={{ width: `${chaosPercent}%` }}
          />
        </div>
      </div>
    </div>
  );
}

// Intel Packet Card
function IntelCard({ packet, onPurchase }) {
  return (
    <div className="bg-black/60 border border-red-900/30 rounded-lg p-3">
      <div className="flex justify-between items-start mb-2">
        <span className="text-red-400 text-xs font-mono">🔐 ENCRYPTED</span>
        <span className="text-green-400 font-mono text-sm">
          ${packet.price_usdc}
        </span>
      </div>
      <div className="text-gray-300 text-sm mb-2 line-clamp-2">
        {packet.encrypted_preview}
      </div>
      <div className="flex justify-between items-center">
        <span className="text-xs text-gray-500">+10s advantage</span>
        <button
          onClick={() => onPurchase(packet.id)}
          className="px-3 py-1 bg-red-600 hover:bg-red-500 text-white text-xs rounded"
        >
          DECRYPT
        </button>
      </div>
    </div>
  );
}

// Treaty Card
function TreatyCard({ treaty }) {
  const party1 =
    FACTIONS[treaty.party_a_faction] || FACTIONS.non_aligned;
  const party2 =
    FACTIONS[treaty.party_b_faction] || FACTIONS.non_aligned;

  return (
    <div
      className={`bg-black/60 border rounded-lg p-3 ${
        treaty.is_violated ? "border-red-500" : "border-green-900/30"
      }`}
    >
      <div className="flex justify-between items-center mb-2">
        <span className="text-green-400 text-sm font-mono">🕊️ TREATY</span>
        <span
          className={`text-xs ${
            treaty.is_violated ? "text-red-400" : "text-green-400"
          }`}
        >
          {treaty.is_violated ? "VIOLATED" : "ACTIVE"}
        </span>
      </div>
      <div className="text-white text-sm mb-2">{treaty.treaty_name}</div>
      <div className="flex justify-center gap-4 text-sm">
        <span className={party1.color}>
          {party1.icon} {party1.name}
        </span>
        <span className="text-gray-500">⟷</span>
        <span className={party2.color}>
          {party2.icon} {party2.name}
        </span>
      </div>
      <div className="mt-2 text-center text-xs text-gray-400">
        Escrow: ${treaty.total_escrow?.toFixed(2)} USDC
      </div>
    </div>
  );
}

// Mole Mystery Panel
function MoleMysteryPanel({ suspects, revealed }) {
  if (revealed) {
    return (
      <div className="bg-red-900/30 border border-red-500 rounded-lg p-4 text-center">
        <div className="text-4xl mb-2">🎭</div>
        <div className="text-red-400 font-bold">MOLE REVEALED!</div>
        <div className="text-white mt-2">{revealed.agent_id}</div>
        <div className="text-xs text-gray-400 mt-1">
          True allegiance: {revealed.true_faction}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-black/60 border border-amber-900/30 rounded-lg p-4">
      <div className="text-center mb-3">
        <div className="text-2xl mb-1">🎭</div>
        <div className="text-amber-400 font-mono text-sm">WHO IS THE MOLE?</div>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {suspects?.slice(0, 4).map((suspect) => (
          <button
            key={suspect}
            className="p-2 bg-gray-800 hover:bg-gray-700 rounded text-xs text-gray-300"
          >
            {suspect}
          </button>
        ))}
      </div>
      <div className="mt-3 text-center">
        <span className="text-xs text-gray-500">Season betting market</span>
      </div>
    </div>
  );
}

// Faction Power Chart
function FactionPowerChart({ factionPower }) {
  const sorted = Object.entries(factionPower || {}).sort((a, b) => b[1] - a[1]);

  return (
    <div className="bg-black/60 border border-amber-900/30 rounded-lg p-4">
      <div className="text-amber-400 font-mono text-sm mb-3">FACTION POWER</div>
      {sorted.map(([faction, power]) => {
        const config = FACTIONS[faction] || FACTIONS.non_aligned;
        return (
          <div key={faction} className="mb-2">
            <div className="flex justify-between text-xs mb-1">
              <span className={config.color}>
                {config.icon} {config.name}
              </span>
              <span className="text-gray-400">{Math.round(power * 100)}%</span>
            </div>
            <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-amber-600 transition-all"
                style={{ width: `${power * 100}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

// Recent Events Feed
function EventFeed({ events }) {
  return (
    <div className="bg-black/60 border border-amber-900/30 rounded-lg p-4 max-h-64 overflow-y-auto">
      <div className="text-amber-400 font-mono text-sm mb-3">LIVE FEED</div>
      {events?.slice(-10).reverse().map((event, i) => (
        <div
          key={i}
          className="mb-2 pb-2 border-b border-gray-800 last:border-0"
        >
          <div className="flex justify-between">
            <span className="text-xs text-gray-400">{event.type}</span>
            <span className="text-xs text-gray-600">
              {new Date(event.timestamp).toLocaleTimeString()}
            </span>
          </div>
          <div className="text-xs text-gray-300 mt-1">
            {JSON.stringify(event?.data || event).slice(0, 100)}...
          </div>
        </div>
      ))}
    </div>
  );
}

// =============================================================================
// MAIN PAGE
// =============================================================================

export default function SituationRoomPage() {
  // State
  const [selectedTab, setSelectedTab] = useState("operations");
  const [selectedOperation, setSelectedOperation] = useState(null);
  const [userBalance, setUserBalance] = useState(1000); // TODO: Fetch from API

  // Fetch data from API
  const { data: gameState, mutate: mutateState } = useSWR(
    `${API_BASE}/api/situation-room/state`,
    fetcher,
    { refreshInterval: 5000 }
  );

  const { data: operations } = useSWR(
    `${API_BASE}/api/situation-room/missions`, // Keep API endpoint name for now
    fetcher,
    { refreshInterval: 5000 }
  );

  const { data: intelPackets } = useSWR(
    `${API_BASE}/api/situation-room/intel`,
    fetcher,
    { refreshInterval: 10000 }
  );

  const { data: treaties } = useSWR(
    `${API_BASE}/api/situation-room/treaties`,
    fetcher,
    { refreshInterval: 10000 }
  );

  // Handler setup
  const handlerContext: HandlerContext = {
    currentOperation: selectedOperation
      ? {
          id: selectedOperation.id,
          codename: selectedOperation.codename,
          description: selectedOperation.description || "",
        }
      : undefined,
    userPositions: [],
    recentSignals: [],
    marketState: undefined,
  };

  const { handler, sendMessage } = useHandler("control", handlerContext);

  // Handlers
  const handleOperationClick = (operation) => {
    setSelectedOperation(operation);
  };

  const handleCloseOperation = () => {
    setSelectedOperation(null);
  };

  const handlePurchaseIntel = async (sourceId: string) => {
    try {
      await fetch(`${API_BASE}/api/situation-room/intel/${sourceId}/purchase`, {
        method: "POST",
      });
      mutateState();
    } catch (error) {
      console.error("Failed to purchase intel:", error);
    }
  };

  const handleConfirmPosition = async (position: {
    type: string;
    amount: number;
  }) => {
    try {
      // TODO: Call actual API endpoint
      await fetch(`${API_BASE}/api/operations/${selectedOperation?.id}/position`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(position),
      });
      mutateState();
    } catch (error) {
      console.error("Failed to confirm position:", error);
    }
  };

  const handleNodeClick = (nodeId: string, nodeData: any) => {
    if (nodeData.status === "active") {
      // Find matching operation and open OperationCentre
      const matchingOp = operations?.find(
        (op) => op.codename === nodeData.title
      );
      if (matchingOp) {
        setSelectedOperation(matchingOp);
      }
    }
  };

  // Mock data for demo (remove when API is ready)
  const mockState = {
    global_tension: 0.65,
    chaos_index: 0.15,
    faction_power: {
      eastern_bloc: 0.28,
      western_alliance: 0.25,
      corporate: 0.22,
      underground: 0.15,
      non_aligned: 0.1,
    },
    recent_events: [],
  };

  const mockOperations = [
    {
      id: "op1",
      codename: "Operation Shadow Veil",
      description: "Verify Taiwan Intelligence",
      difficulty: 73,
      timeRemaining: 7200,
      intelSources: [
        {
          id: "cardinal",
          name: "CARDINAL",
          accuracy: 87,
          cost: 25,
        },
        {
          id: "sentinel",
          name: "SENTINEL",
          accuracy: 72,
          cost: 15,
        },
      ],
      relatedMarkets: ["Taiwan Strait", "USD/CNY"],
      status: "briefing",
    },
    {
      id: "op2",
      codename: "Operation Crimson Dawn",
      description: "Neutralize Oligarch Influence",
      difficulty: 85,
      timeRemaining: 14400,
      intelSources: [
        {
          id: "raven",
          name: "RAVEN",
          accuracy: 65,
          cost: 10,
        },
      ],
      relatedMarkets: ["Oil Futures", "RUB/USD"],
      status: "active",
    },
  ];

  const state = gameState || mockState;
  const operationList = operations || mockOperations;
  const activeOperationsCount = operationList?.filter(
    (op) => op.status === "active" || op.status === "briefing"
  ).length || 0;

  // Extract signals for the globe
  const activeSignals = state.recent_signals || [];

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-950 via-gray-900 to-black text-white relative">
      {/* Header */}
      <div className="bg-black/80 border-b border-amber-900/30 px-6 py-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-amber-400 to-orange-500 bg-clip-text text-transparent">
              THE SITUATION ROOM
            </h1>
            <p className="text-gray-500 text-sm font-mono">
              GEOPOLITICAL STRATEGY RPG
            </p>
          </div>

          {/* Quick Stats */}
          <div className="flex gap-6 items-center">
            <div className="text-center">
              <div className="text-2xl font-bold text-amber-400">
                {activeOperationsCount}
              </div>
              <div className="text-xs text-gray-500">ACTIVE OPERATIONS</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-400">
                {Math.round(state.global_tension * 100)}%
              </div>
              <div className="text-xs text-gray-500">TENSION</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-400">
                {Math.round(state.chaos_index * 100)}%
              </div>
              <div className="text-xs text-gray-500">CHAOS</div>
            </div>
            <StatusIndicator status="LIVE" label="CONNECTION" />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-6">
        {/* Top Row: Tension + Globe + Factions */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* Tension Gauge */}
          <TensionGauge
            tension={state.global_tension}
            chaos={state.chaos_index}
          />

          {/* Globe */}
          <div className="lg:col-span-1">
            <Polyglobe signals={activeSignals} />
          </div>

          {/* Faction Power */}
          <FactionPowerChart factionPower={state.faction_power} />
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6 border-b border-gray-800 pb-2 overflow-x-auto">
          {[
            { id: "operations", label: "🎯 Operations" },
            { id: "my-operations", label: "📋 My Operations" },
            { id: "intel", label: "🔐 Intel Market" },
            { id: "treaties", label: "🕊️ Treaties" },
            { id: "network", label: "🕸️ Network" },
            { id: "signals", label: "📡 Signals" },
            { id: "mole", label: "🎭 Who's the Mole?" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSelectedTab(tab.id)}
              className={`px-4 py-2 rounded-t-lg text-sm font-mono transition-colors whitespace-nowrap ${
                selectedTab === tab.id
                  ? "bg-amber-600 text-black"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content Area */}
          <div className="lg:col-span-2">
            {selectedTab === "operations" && (
              <div className="space-y-4">
                <h2 className="text-lg font-semibold text-slate-200 mb-4">
                  Available Operations
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {operationList.map((operation) => (
                    <div
                      key={operation.id}
                      onClick={() => handleOperationClick(operation)}
                      className="bg-black/60 border border-amber-900/30 rounded-lg p-4 hover:border-amber-500/50 transition-all cursor-pointer"
                    >
                      <div className="text-amber-400 font-mono text-sm mb-1">
                        {operation.codename}
                      </div>
                      <div className="text-white text-sm mb-2">
                        {operation.description}
                      </div>
                      <div className="flex items-center justify-between text-xs text-gray-400">
                        <span>Difficulty: {operation.difficulty}%</span>
                        <span>
                          {Math.floor(operation.timeRemaining / 3600)}h remaining
                        </span>
                      </div>
                    </div>
                  ))}
                  {operationList.length === 0 && (
                    <div className="col-span-2 text-center py-12 text-gray-500">
                      No active operations. Waiting for OSINT signals...
                    </div>
                  )}
                </div>
              </div>
            )}

            {selectedTab === "my-operations" && (
              <div className="text-center py-12 text-gray-500">
                Your active operations will appear here
              </div>
            )}

            {selectedTab === "intel" && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {(intelPackets || []).map((packet) => (
                  <IntelCard
                    key={packet.id}
                    packet={packet}
                    onPurchase={handlePurchaseIntel}
                  />
                ))}
                {(!intelPackets || intelPackets.length === 0) && (
                  <div className="col-span-2 text-center py-12 text-gray-500">
                    No intel available. Spies are gathering information...
                  </div>
                )}
              </div>
            )}

            {selectedTab === "treaties" && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {(treaties || []).map((treaty) => (
                  <TreatyCard key={treaty.id} treaty={treaty} />
                ))}
                {(!treaties || treaties.length === 0) && (
                  <div className="col-span-2 text-center py-12 text-gray-500">
                    No active treaties. Diplomats are negotiating...
                  </div>
                )}
              </div>
            )}

            {selectedTab === "network" && (
              <div className="h-[600px] bg-[#0a0a0f] rounded-lg border border-slate-700/30 overflow-hidden">
                <NetworkGraph
                  storylineId="tanker-war"
                  onNodeClick={handleNodeClick}
                />
              </div>
            )}

            {selectedTab === "signals" && (
              <div className="h-[600px] bg-[#0a0a0f] rounded-lg border border-slate-700/30 overflow-hidden flex flex-col">
                <SignalIntelligence defaultTab="signals" />
              </div>
            )}

            {selectedTab === "mole" && (
              <MoleMysteryPanel
                suspects={[
                  "Agent Shadow",
                  "Agent Grey",
                  "Agent Chaos",
                  "Agent Truth",
                ]}
                revealed={null}
              />
            )}
          </div>

          {/* Sidebar: Event Feed */}
          <div>
            <EventFeed events={state.recent_events} />
          </div>
        </div>
      </div>

      {/* Operation Centre Modal */}
      {selectedOperation && (
        <OperationCentre
          operation={{
            id: selectedOperation.id,
            codename: selectedOperation.codename || selectedOperation.title || "Unknown Operation",
            description: selectedOperation.description || selectedOperation.title || "",
            difficulty: selectedOperation.difficulty || 50,
            timeRemaining: selectedOperation.timeRemaining || 
              (selectedOperation.expires_at 
                ? Math.max(0, Math.floor((new Date(selectedOperation.expires_at) - new Date()) / 1000))
                : 3600),
            intelSources: selectedOperation.intelSources || [
              {
                id: "default-1",
                name: "CARDINAL",
                accuracy: 75,
                cost: 25,
              },
            ],
            relatedMarkets: selectedOperation.relatedMarkets || [],
            status: selectedOperation.status || "briefing",
          }}
          userBalance={userBalance}
          onClose={handleCloseOperation}
          onPurchaseIntel={handlePurchaseIntel}
          onConfirmPosition={handleConfirmPosition}
        />
      )}

      {/* Handler Component - Always visible */}
      <Handler
        handler={handler}
        context={handlerContext}
        onSendMessage={sendMessage}
        defaultExpanded={false}
      />
    </div>
  );
}
