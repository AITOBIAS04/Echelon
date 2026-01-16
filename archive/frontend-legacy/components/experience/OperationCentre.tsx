"use client";

import { useState, useEffect } from "react";
import {
  TrendingUp,
  TrendingDown,
  Shield,
  Clock,
  X,
  ArrowRight,
  CheckCircle2,
  XCircle,
  BarChart3,
  Zap,
} from "lucide-react";
import {
  DataCard,
  ConfidenceMeter,
  DataReveal,
  StatusIndicator,
  ProgressRing,
} from "./index";

// =============================================================================
// TYPES
// =============================================================================

type Phase = "intel" | "position" | "resolution";

interface IntelSource {
  id: string;
  name: string;
  accuracy: number;
  cost: number;
  content?: string;
}

interface Operation {
  id: string;
  codename: string;
  description: string;
  difficulty: number;
  timeRemaining: number;
  intelSources: IntelSource[];
  relatedMarkets: string[];
  status: "briefing" | "active" | "resolved";
  result?: {
    won: boolean;
    pnl: number;
    pnlPercent: number;
  };
}

interface OperationCentreProps {
  operation: Operation;
  userBalance: number;
  onClose: () => void;
  onPurchaseIntel: (sourceId: string) => Promise<void>;
  onConfirmPosition: (position: { type: string; amount: number }) => Promise<void>;
  walletAddress?: string;
}

// =============================================================================
// COMPONENT
// =============================================================================

export function OperationCentre({
  operation,
  userBalance,
  onClose,
  onPurchaseIntel,
  onConfirmPosition,
  walletAddress,
}: OperationCentreProps) {
  const [currentPhase, setCurrentPhase] = useState<Phase>(
    operation.status === "resolved" ? "resolution" : "intel"
  );
  const [selectedPosition, setSelectedPosition] = useState<string | null>(null);
  const [positionAmount, setPositionAmount] = useState<number>(0);
  const [purchasedIntel, setPurchasedIntel] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(operation.timeRemaining);

  // Countdown timer
  useEffect(() => {
    if (currentPhase === "intel" && timeRemaining > 0) {
      const timer = setInterval(() => {
        setTimeRemaining((prev) => Math.max(0, prev - 1));
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [currentPhase, timeRemaining]);

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    }
    return `${minutes}m ${secs}s`;
  };

  const handlePurchaseIntel = async (sourceId: string) => {
    if (purchasedIntel.includes(sourceId) || isLoading) return;

    const source = operation.intelSources.find((s) => s.id === sourceId);
    if (!source || userBalance < source.cost) return;

    setIsLoading(true);
    try {
      await onPurchaseIntel(sourceId);
      setPurchasedIntel((prev) => [...prev, sourceId]);
    } catch (error) {
      console.error("Failed to purchase intel:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmPosition = async () => {
    if (!selectedPosition || positionAmount <= 0 || isLoading) return;

    setIsLoading(true);
    try {
      await onConfirmPosition({
        type: selectedPosition,
        amount: positionAmount,
      });
      // Move to resolution phase after successful position
      setCurrentPhase("resolution");
    } catch (error) {
      console.error("Failed to confirm position:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const calculateProjections = (type: string, amount: number) => {
    let winMultiplier = 1;
    let lossMultiplier = 0.8;

    switch (type) {
      case "LONG":
      case "SHORT":
        winMultiplier = 3; // 2-4x average
        break;
      case "HEDGE":
        winMultiplier = 1.2;
        break;
      case "LIMIT":
        winMultiplier = 2; // Variable, use 2x as default
        break;
    }

    const projectedWin = amount * winMultiplier;
    const projectedLoss = amount * lossMultiplier;
    const winPercent = Math.round((projectedWin / amount) * 100);
    const lossPercent = Math.round((projectedLoss / amount) * 100);

    return {
      win: projectedWin,
      loss: projectedLoss,
      winPercent,
      lossPercent,
    };
  };

  const positionConfigs = {
    LONG: {
      icon: TrendingUp,
      title: "LONG",
      description: "High conviction bullish",
      risk: 80,
      potential: "2-4x return",
    },
    SHORT: {
      icon: TrendingDown,
      title: "SHORT",
      description: "Contrarian bearish",
      risk: 80,
      potential: "2-4x return",
    },
    HEDGE: {
      icon: Shield,
      title: "HEDGE",
      description: "Split position both sides",
      risk: 30,
      potential: "1.2x return",
    },
    LIMIT: {
      icon: Clock,
      title: "LIMIT",
      description: "Set price trigger, wait",
      risk: 50,
      potential: "Variable",
    },
  };

  return (
    <div className="fixed inset-0 z-50 bg-[#0a0a0f]/95 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="w-full max-w-7xl bg-[#0a0a0f] border border-slate-700/30 rounded-lg shadow-2xl max-h-[95vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-[#0a0a0f]/95 backdrop-blur-md border-b border-slate-700/30 px-6 py-4 flex items-center justify-between z-10">
          <h1 className="text-2xl font-semibold text-slate-200 font-sans">
            {operation.codename}
          </h1>
          <button
            onClick={onClose}
            className="p-2 hover:bg-[#12121a] rounded-lg transition-all duration-300"
          >
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>

        {/* Phase Indicator */}
        <div className="px-6 py-4 border-b border-slate-700/20">
          <div className="flex items-center justify-center gap-4">
            {(["intel", "position", "resolution"] as Phase[]).map((p, index) => (
              <div key={p} className="flex items-center gap-4">
                <button
                  onClick={() => {
                    if (operation.status === "resolved" || p !== "resolution") {
                      setCurrentPhase(p);
                    }
                  }}
                  className={`px-4 py-2 rounded-lg text-sm font-mono transition-all duration-300 ${
                    currentPhase === p
                      ? "bg-[#6366f1] text-white"
                      : p === "resolution" && operation.status !== "resolved"
                      ? "bg-[#12121a] text-slate-500 cursor-not-allowed"
                      : "bg-[#12121a] text-slate-400 hover:bg-[#12121a]/80"
                  }`}
                  disabled={p === "resolution" && operation.status !== "resolved"}
                >
                  {p === "intel" && "PHASE 1: INTEL"}
                  {p === "position" && "PHASE 2: POSITION"}
                  {p === "resolution" && "PHASE 3: RESOLUTION"}
                </button>
                {index < 2 && (
                  <ArrowRight className="w-4 h-4 text-slate-500" />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {currentPhase === "intel" && (
            <div className="animate-fade-in">
              <Phase1Intelligence
                operation={operation}
                timeRemaining={timeRemaining}
                formatTime={formatTime}
                purchasedIntel={purchasedIntel}
                userBalance={userBalance}
                onPurchaseIntel={handlePurchaseIntel}
                isLoading={isLoading}
                onContinue={() => setCurrentPhase("position")}
              />
            </div>
          )}

          {currentPhase === "position" && (
            <div className="animate-fade-in">
              <Phase2Position
                selectedPosition={selectedPosition}
                positionAmount={positionAmount}
                positionConfigs={positionConfigs}
                userBalance={userBalance}
                onSelectPosition={setSelectedPosition}
                onAmountChange={setPositionAmount}
                onConfirm={handleConfirmPosition}
                calculateProjections={calculateProjections}
                isLoading={isLoading}
              />
            </div>
          )}

          {currentPhase === "resolution" && operation.result && (
            <div className="animate-fade-in">
              <Phase3Resolution result={operation.result} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// PHASE 1: INTELLIGENCE BRIEFING
// =============================================================================

function Phase1Intelligence({
  operation,
  timeRemaining,
  formatTime,
  purchasedIntel,
  userBalance,
  onPurchaseIntel,
  isLoading,
  onContinue,
}: {
  operation: Operation;
  timeRemaining: number;
  formatTime: (s: number) => string;
  purchasedIntel: string[];
  userBalance: number;
  onPurchaseIntel: (id: string) => void;
  isLoading: boolean;
  onContinue: () => void;
}) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Section - Operation Overview */}
        <div className="lg:col-span-1 space-y-4">
          <DataCard title={operation.codename} subtitle={operation.description}>
            <div className="space-y-4">
              <div>
                <div className="text-xs text-slate-400 mb-2">Time Remaining</div>
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-[#6366f1]" />
                  <span className="text-lg font-mono text-slate-200">
                    {formatTime(timeRemaining)}
                  </span>
                </div>
              </div>

              <div>
                <div className="text-xs text-slate-400 mb-2">Difficulty</div>
                <ConfidenceMeter value={operation.difficulty} variant="bar" />
              </div>

              <div>
                <div className="text-xs text-slate-400 mb-2">Risk Rating</div>
                <ConfidenceMeter value={operation.difficulty} variant="bar" />
              </div>

              {operation.relatedMarkets.length > 0 && (
                <div>
                  <div className="text-xs text-slate-400 mb-2">
                    Related Markets
                  </div>
                  <div className="space-y-1">
                    {operation.relatedMarkets.map((market, idx) => (
                      <div key={idx} className="text-sm font-mono text-slate-300">
                        • {market}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </DataCard>
        </div>

        {/* Right Section - Intel Sources */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-lg font-semibold text-slate-200 font-sans">
            Intel Sources
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {operation.intelSources.map((source) => {
              const isPurchased = purchasedIntel.includes(source.id);
              const canAfford = userBalance >= source.cost;

              return (
                <DataCard
                  key={source.id}
                  title={source.name}
                  priority={
                    source.cost >= 30
                      ? "danger"
                      : source.cost >= 15
                      ? "warning"
                      : "success"
                  }
                >
                  <div className="space-y-4">
                    <div>
                      <div className="text-xs text-slate-400 mb-2">
                        Accuracy Rating
                      </div>
                      <ConfidenceMeter
                        value={source.accuracy}
                        variant="compact"
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-sm text-slate-400">Cost:</span>
                      <span className="text-lg font-mono text-slate-200">
                        {source.cost} PLAY
                      </span>
                    </div>

                    {!isPurchased ? (
                      <>
                        <DataReveal revealed={false}>
                          <div className="space-y-2 text-sm text-slate-400">
                            <div>Intel data hidden...</div>
                            <div>Purchase to reveal</div>
                          </div>
                        </DataReveal>
                        <button
                          onClick={() => onPurchaseIntel(source.id)}
                          disabled={!canAfford || isLoading}
                          className="w-full py-2 px-4 bg-[#6366f1] hover:bg-[#6366f1]/80 disabled:bg-[#12121a] disabled:text-slate-500 text-white rounded-lg text-sm font-mono transition-all duration-300"
                        >
                          {!canAfford
                            ? "Insufficient Balance"
                            : "Access Intel"}
                        </button>
                      </>
                    ) : (
                      <DataReveal revealed={true}>
                        <div className="space-y-3">
                          {source.content ? (
                            <div className="text-sm text-slate-300 whitespace-pre-line">
                              {source.content}
                            </div>
                          ) : (
                            <div className="space-y-2">
                              <div className="text-xs text-slate-400">
                                KEY FACTS
                              </div>
                              <ul className="list-disc list-inside space-y-1 text-sm text-slate-300">
                                <li>High confidence signal detected</li>
                                <li>Multiple source confirmations</li>
                                <li>Timeline: 18-24 hours</li>
                              </ul>
                              <div className="pt-2 border-t border-slate-700/30">
                                <div className="flex items-center justify-between text-xs">
                                  <span className="text-slate-400">
                                    Confidence:
                                  </span>
                                  <span className="text-slate-200 font-mono">
                                    {source.accuracy}%
                                  </span>
                                </div>
                                <div className="flex items-center justify-between text-xs mt-1">
                                  <span className="text-slate-400">
                                    Timestamp:
                                  </span>
                                  <span className="text-slate-200 font-mono">
                                    {new Date().toLocaleTimeString()}
                                  </span>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      </DataReveal>
                    )}
                  </div>
                </DataCard>
              );
            })}
          </div>

          <div className="flex justify-end pt-4">
            <button
              onClick={onContinue}
              className="px-6 py-3 bg-[#6366f1] hover:bg-[#6366f1]/80 text-white rounded-lg font-mono transition-all duration-300 flex items-center gap-2"
            >
              Proceed to Position Builder
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// PHASE 2: POSITION BUILDER
// =============================================================================

function Phase2Position({
  selectedPosition,
  positionAmount,
  positionConfigs,
  userBalance,
  onSelectPosition,
  onAmountChange,
  onConfirm,
  calculateProjections,
  isLoading,
}: {
  selectedPosition: string | null;
  positionAmount: number;
  positionConfigs: Record<
    string,
    {
      icon: any;
      title: string;
      description: string;
      risk: number;
      potential: string;
    }
  >;
  userBalance: number;
  onSelectPosition: (type: string) => void;
  onAmountChange: (amount: number) => void;
  onConfirm: () => void;
  calculateProjections: (type: string, amount: number) => {
    win: number;
    loss: number;
    winPercent: number;
    lossPercent: number;
  };
  isLoading: boolean;
}) {
  const projections =
    selectedPosition && positionAmount > 0
      ? calculateProjections(selectedPosition, positionAmount)
      : null;

  const quickAmounts = [25, 50, 75, 100];

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-slate-200 font-sans">
        Select Position Type
      </h2>

      {/* Position Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {(["LONG", "SHORT", "HEDGE", "LIMIT"] as string[]).map((type) => {
          const config = positionConfigs[type];
          const Icon = config.icon;
          const isSelected = selectedPosition === type;

          return (
            <DataCard
              key={type}
              title={config.title}
              subtitle={config.description}
              priority={
                config.risk >= 70
                  ? "danger"
                  : config.risk >= 40
                  ? "warning"
                  : "success"
              }
              onClick={() => onSelectPosition(type)}
              className={`cursor-pointer transition-all duration-300 ${
                isSelected ? "ring-2 ring-[#6366f1]" : ""
              }`}
            >
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-[#12121a] rounded-lg">
                    <Icon className="w-5 h-5 text-slate-300" />
                  </div>
                  <div className="flex-1">
                    <div className="text-xs text-slate-400 mb-1">Risk</div>
                    <ConfidenceMeter value={config.risk} variant="compact" />
                  </div>
                </div>
                <div className="flex items-center justify-between pt-2 border-t border-slate-700/30">
                  <span className="text-xs text-slate-400">Potential:</span>
                  <span className="text-sm font-mono text-slate-200">
                    {config.potential}
                  </span>
                </div>
              </div>
            </DataCard>
          );
        })}
      </div>

      {/* Position Builder */}
      {selectedPosition && (
        <div className="animate-fade-in">
          <DataCard
            title={`Build Position: ${positionConfigs[selectedPosition].title}`}
            priority="none"
          >
            <div className="space-y-6">
              {/* Amount Input */}
              <div>
                <label className="block text-sm text-slate-400 mb-2 font-sans">
                  Position Amount (PLAY)
                </label>
                <div className="flex gap-2 mb-2">
                  {quickAmounts.map((percent) => (
                    <button
                      key={percent}
                      onClick={() => {
                        onAmountChange((userBalance * percent) / 100);
                      }}
                      className="px-4 py-2 bg-[#12121a] hover:bg-[#12121a]/80 text-slate-400 rounded-lg text-sm font-mono transition-all duration-300"
                    >
                      {percent === 100 ? "MAX" : `${percent}%`}
                    </button>
                  ))}
                </div>
                <input
                  type="number"
                  value={positionAmount || ""}
                  onChange={(e) => onAmountChange(Number(e.target.value))}
                  placeholder="Enter amount"
                  max={userBalance}
                  className="w-full px-4 py-2 bg-[#0a0a0f] border border-slate-700/30 rounded-lg text-slate-200 font-mono focus:outline-none focus:ring-2 focus:ring-[#6366f1] transition-all duration-300"
                />
                <div className="text-xs text-slate-500 mt-1">
                  Available: {userBalance.toFixed(2)} PLAY
                </div>
              </div>

              {/* Projected Outcomes */}
              {projections && (
                <div className="grid grid-cols-2 gap-4 p-4 bg-[#0a0a0f] rounded-lg border border-slate-700/30">
                  <div className="flex items-center gap-3">
                    <CheckCircle2 className="w-5 h-5 text-[#22c55e]" />
                    <div>
                      <div className="text-xs text-slate-400">If WIN</div>
                      <div className="text-lg font-mono text-[#22c55e]">
                        +${projections.win.toFixed(2)} (+{projections.winPercent}%)
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <XCircle className="w-5 h-5 text-[#ef4444]" />
                    <div>
                      <div className="text-xs text-slate-400">If LOSE</div>
                      <div className="text-lg font-mono text-[#ef4444]">
                        -${projections.loss.toFixed(2)} (-{projections.lossPercent}%)
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Current Market Odds */}
              <div className="text-sm text-slate-400">
                Current market odds:{" "}
                <span className="font-mono text-slate-200">55% win / 45% lose</span>
              </div>

              {/* Confirm Button */}
              <button
                onClick={onConfirm}
                disabled={positionAmount <= 0 || isLoading}
                className="w-full py-3 px-6 bg-[#6366f1] hover:bg-[#6366f1]/80 disabled:bg-[#12121a] disabled:text-slate-500 text-white rounded-lg font-mono transition-all duration-300 flex items-center justify-center gap-2"
              >
                {isLoading ? "Processing..." : "Confirm Position"}
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </DataCard>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// PHASE 3: RESOLUTION & DEBRIEF
// =============================================================================

function Phase3Resolution({
  result,
}: {
  result: {
    won: boolean;
    pnl: number;
    pnlPercent: number;
  };
}) {
  const isPositive = result.won;

  return (
    <div className="space-y-6">
      {/* Row 1: Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <DataCard
          title="Position Result"
          priority={isPositive ? "success" : "danger"}
        >
          <div className="text-2xl font-mono font-semibold">
            <span className={isPositive ? "text-[#22c55e]" : "text-[#ef4444]"}>
              {isPositive ? "+" : ""}${result.pnl.toFixed(2)}
            </span>
            <span className="text-slate-400 ml-2">
              ({isPositive ? "+" : ""}
              {result.pnlPercent}%)
            </span>
          </div>
        </DataCard>

        <DataCard title="Your Accuracy" priority="none">
          <div className="space-y-2">
            <div className="text-2xl font-mono font-semibold text-slate-200">
              73%
            </div>
            <div className="text-sm text-slate-400">
              vs market average 51%
            </div>
          </div>
        </DataCard>

        <DataCard title="Time to Resolution" priority="none">
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-[#6366f1]" />
            <span className="text-xl font-mono text-slate-200">4.2 hours</span>
          </div>
        </DataCard>
      </div>

      {/* Row 2: Impact Analysis */}
      <DataCard
        title="Impact Analysis"
        priority="none"
        headerAddon={<BarChart3 className="w-5 h-5 text-[#6366f1]" />}
      >
        <div className="space-y-4">
          <div>
            <div className="text-sm text-slate-400 mb-2">
              Your position influenced these markets:
            </div>
            <div className="space-y-2">
              {[
                { name: "Oil Futures", change: 2.3 },
                { name: "USD/EUR", change: -0.8 },
                { name: "Tech Index", change: 1.5 },
              ].map((market, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3 bg-[#0a0a0f] rounded-lg"
                >
                  <span className="font-mono text-slate-200">{market.name}</span>
                  <span
                    className={`font-mono font-semibold ${
                      market.change > 0 ? "text-[#22c55e]" : "text-[#ef4444]"
                    }`}
                  >
                    {market.change > 0 ? "+" : ""}
                    {market.change.toFixed(2)}%
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-2 border-t border-slate-700/30">
            <div className="text-sm text-slate-400">
              New operations unlocked:{" "}
              <span className="font-mono text-slate-200">2</span>
            </div>
          </div>
        </div>
      </DataCard>

      {/* Row 3: Progression */}
      <DataCard title="Progression" priority="none">
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <Zap className="w-6 h-6 text-[#f59e0b]" />
            <span className="text-3xl font-mono font-semibold text-slate-200">
              +150 XP
            </span>
          </div>

          <div className="flex items-center justify-center">
            <ProgressRing value={65} size={100} label="LEVEL 3" />
          </div>

          <div className="text-center text-sm text-slate-400">
            Next level: 35% remaining
          </div>

          <div className="flex justify-center pt-2">
            <button className="px-6 py-3 bg-[#6366f1] hover:bg-[#6366f1]/80 text-white rounded-lg font-mono transition-all duration-300 flex items-center gap-2">
              View Next Operations
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </DataCard>
    </div>
  );
}
