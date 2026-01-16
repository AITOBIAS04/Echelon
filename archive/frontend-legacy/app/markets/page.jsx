// app/markets/page.jsx

"use client";

import { useState, useRef, useCallback } from "react";
import Link from "next/link";
import useSWR from "swr";
import toast from "react-hot-toast";
import { 
  ENDPOINTS, 
  POLL_INTERVALS, 
  fetcher, 
  postRequest 
} from "@/utils/api";

// Domain colors
const DOMAIN_COLORS = {
  finance: { bg: "bg-green-900/30", border: "border-green-700", text: "text-green-400", icon: "💹" },
  crypto: { bg: "bg-orange-900/30", border: "border-orange-700", text: "text-orange-400", icon: "₿" },
  sports: { bg: "bg-blue-900/30", border: "border-blue-700", text: "text-blue-400", icon: "⚽" },
  politics: { bg: "bg-purple-900/30", border: "border-purple-700", text: "text-purple-400", icon: "🗳️" },
  geopolitics: { bg: "bg-red-900/30", border: "border-red-700", text: "text-red-400", icon: "🌍" },
  unknown: { bg: "bg-gray-900/30", border: "border-gray-700", text: "text-gray-400", icon: "❓" },
};

// Duration labels
const DURATION_LABELS = {
  micro: { label: "24H", color: "text-yellow-400", bg: "bg-yellow-900/30" },
  narrative: { label: "7D", color: "text-blue-400", bg: "bg-blue-900/30" },
  macro: { label: "30D+", color: "text-purple-400", bg: "bg-purple-900/30" },
};

// Status badges
const STATUS_BADGES = {
  OPEN: { label: "OPEN", color: "bg-green-600", textColor: "text-white" },
  CLOSED: { label: "CLOSED", color: "bg-gray-600", textColor: "text-gray-300" },
  SETTLED: { label: "SETTLED", color: "bg-blue-600", textColor: "text-white" },
};

function MarketCard({ market, onSelect, previousVolume }) {
  const domain = DOMAIN_COLORS[market.domain] || DOMAIN_COLORS.unknown;
  const duration = DURATION_LABELS[market.duration] || DURATION_LABELS.narrative;
  const status = STATUS_BADGES[market.status] || STATUS_BADGES.OPEN;
  
  return (
    <div 
      className="glass-panel rounded-2xl p-6 cursor-pointer relative overflow-hidden group transition-all duration-300"
      onClick={() => onSelect(market)}
    >
      {/* Hover Gradient Blob */}
      <div className="absolute -right-10 -top-10 w-40 h-40 bg-purple-600/20 rounded-full blur-3xl group-hover:bg-purple-600/30 transition-all duration-500" />

      {/* Header Badges */}
      <div className="flex justify-between items-start mb-4 relative z-10">
        <div className="flex gap-2">
          <span className="bg-white/5 border border-white/10 text-xs px-3 py-1 rounded-full text-gray-300 backdrop-blur-md">
            {market.domain.toUpperCase()}
          </span>
          <span className="bg-white/5 border border-white/10 text-xs px-3 py-1 rounded-full text-gray-300 backdrop-blur-md">
            {market.duration.toUpperCase()}
          </span>
        </div>
        <div className="flex items-center gap-1 text-xs text-gray-400">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"/>
          LIVE
        </div>
      </div>
      
      {/* Title */}
      <h3 className="text-xl font-bold text-white mb-2 leading-tight group-hover:text-purple-300 transition-colors relative z-10">
        {market.title}
      </h3>
      
      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-4 mt-6 relative z-10">
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider">Volume</p>
          <p className="text-lg font-mono text-white">${market.total_volume?.toLocaleString()}</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-500 uppercase tracking-wider">Chance</p>
          <div className="flex justify-end items-center gap-2">
            <span className="text-lg font-mono text-green-400 font-bold">
              {(market.outcome_odds?.YES * 100).toFixed(0)}%
            </span>
            <span className="text-xs text-gray-600">YES</span>
          </div>
        </div>
      </div>
      {/* Progress Bar */}
      <div className="mt-4 h-1.5 w-full bg-gray-800 rounded-full overflow-hidden">
        <div 
          className="h-full bg-gradient-to-r from-blue-500 to-purple-500" 
          style={{ width: `${(market.outcome_odds?.YES * 100)}%` }}
        />
      </div>
    </div>
  );
}

function MarketDetailModal({ market, onClose, onBet }) {
  const [selectedOutcome, setSelectedOutcome] = useState(null);
  const [betAmount, setBetAmount] = useState(10);
  const [isPlacingBet, setIsPlacingBet] = useState(false);
  
  if (!market) return null;
  
  const domain = DOMAIN_COLORS[market.domain] || DOMAIN_COLORS.unknown;
  
  const handlePlaceBet = async () => {
    if (!selectedOutcome || betAmount <= 0) return;
    setIsPlacingBet(true);
    await onBet(market.id, selectedOutcome, betAmount);
    setIsPlacingBet(false);
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[60] flex items-center justify-center p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className={`${domain.bg} ${domain.border} border-b p-6`}>
          <div className="flex justify-between items-start">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-3xl">{domain.icon}</span>
                <span className={`text-sm uppercase tracking-wider ${domain.text}`}>
                  {market.domain}
                </span>
              </div>
              <h2 className="text-2xl font-bold text-white">{market.title}</h2>
            </div>
            <button 
              onClick={onClose}
              className="text-gray-400 hover:text-white text-2xl"
            >
              ×
            </button>
          </div>
        </div>
        
        {/* Content */}
        <div className="p-6">
          <p className="text-gray-300 mb-6">{market.description}</p>
          
          {/* Market Stats */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-gray-800 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-white">${market.total_volume?.toFixed(2)}</div>
              <div className="text-xs text-gray-400">Total Volume</div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 text-center">
              <div className={`text-2xl font-bold ${
                market.virality_score > 80 ? "text-red-400" : "text-yellow-400"
              }`}>
                {market.virality_score?.toFixed(0)}
              </div>
              <div className="text-xs text-gray-400">Virality Score</div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-purple-400">
                {market.active_agents || "?"}
              </div>
              <div className="text-xs text-gray-400">Active Agents</div>
            </div>
          </div>
          
          {/* Outcome Selection */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-white mb-3">Select Outcome</h3>
            <div className="grid grid-cols-2 gap-3">
              {market.outcomes?.map((outcome) => {
                const odds = market.outcome_odds?.[outcome] || 0.5;
                const impliedOdds = (1 / odds).toFixed(2);
                const isSelected = selectedOutcome === outcome;
                
                return (
                  <button
                    key={outcome}
                    onClick={() => setSelectedOutcome(outcome)}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      isSelected 
                        ? "border-purple-500 bg-purple-900/30" 
                        : "border-gray-700 bg-gray-800 hover:border-gray-600"
                    }`}
                  >
                    <div className="text-xl font-bold text-white">{outcome}</div>
                    <div className="text-sm text-gray-400 mt-1">
                      {(odds * 100).toFixed(0)}% chance • {impliedOdds}x payout
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
          
          {/* Bet Amount */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-white mb-3">Bet Amount</h3>
            <div className="flex gap-3 items-center">
              <div className="relative flex-1">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
                <input
                  type="number"
                  value={betAmount}
                  onChange={(e) => setBetAmount(parseFloat(e.target.value) || 0)}
                  className="w-full p-3 pl-8 bg-gray-800 border border-gray-600 rounded-lg text-white font-mono"
                  min="1"
                />
              </div>
              {[10, 50, 100, 500].map((amount) => (
                <button
                  key={amount}
                  onClick={() => setBetAmount(amount)}
                  className="py-3 px-4 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-mono"
                >
                  ${amount}
                </button>
              ))}
            </div>
            {selectedOutcome && betAmount > 0 && (
              <div className="mt-3 p-3 bg-green-900/30 border border-green-700 rounded-lg">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Potential Payout:</span>
                  <span className="text-green-400 font-bold font-mono">
                    ${((betAmount / (market.outcome_odds?.[selectedOutcome] || 0.5)) * 0.95).toFixed(2)}
                  </span>
                </div>
              </div>
            )}
          </div>
          
          {/* Place Bet Button */}
          <div className="space-y-2">
            <button
              onClick={handlePlaceBet}
              disabled={!selectedOutcome || betAmount <= 0 || isPlacingBet || market.status !== "OPEN"}
              className={`w-full py-4 rounded-lg font-bold text-lg transition-all ${
                market.status !== "OPEN"
                  ? "bg-gray-700 cursor-not-allowed text-gray-500"
                  : !selectedOutcome || betAmount <= 0
                  ? "bg-gray-700 cursor-not-allowed text-gray-500"
                  : isPlacingBet
                  ? "bg-purple-900 cursor-wait"
                  : "bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500"
              }`}
            >
              {market.status !== "OPEN" 
                ? `Market ${market.status}`
                : isPlacingBet 
                ? "Placing Bet..." 
                : `Place Bet on ${selectedOutcome || "..."}`}
            </button>
            
            {/* Helper text explaining why button is disabled */}
            {(!selectedOutcome || betAmount <= 0 || market.status !== "OPEN") && !isPlacingBet && (
              <p className="text-xs text-gray-500 text-center">
                {market.status !== "OPEN" 
                  ? `This market is ${market.status.toLowerCase()}. Betting is closed.`
                  : !selectedOutcome
                  ? "Select an outcome (YES/NO) to place a bet"
                  : betAmount <= 0
                  ? "Enter a bet amount greater than $0"
                  : ""}
              </p>
            )}
          </div>
          
          {/* Source Event Info */}
          {market.source_event && (
            <div className="mt-6 p-4 bg-gray-800/50 rounded-lg text-sm">
              <div className="text-gray-400 mb-1">Source Event</div>
              <div className="text-white">{market.source_event.title}</div>
              <div className="text-gray-500 mt-1">
                via {market.source_event.source} • Sentiment: {(market.source_event.sentiment * 100).toFixed(0)}%
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function MarketsPage() {
  const [selectedMarket, setSelectedMarket] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const previousVolumesRef = useRef({}); // Track previous volumes for flash effect
  
  // Filters
  const [domainFilter, setDomainFilter] = useState(null);
  const [durationFilter, setDurationFilter] = useState(null);
  const [statusFilter, setStatusFilter] = useState(null);

  // Build query string for filters
  const getMarketsUrl = useCallback(() => {
    const params = new URLSearchParams();
    if (domainFilter) params.append("domain", domainFilter);
    if (durationFilter) params.append("duration", durationFilter);
    if (statusFilter) params.append("status", statusFilter);
    const queryString = params.toString();
    return queryString ? `${ENDPOINTS.MARKETS}?${queryString}` : ENDPOINTS.MARKETS;
  }, [domainFilter, durationFilter, statusFilter]);

  // SWR for markets - auto-refreshes, caches, revalidates on focus
  const { 
    data: marketsData, 
    error: marketsError, 
    isLoading: marketsLoading,
    mutate: mutateMarkets 
  } = useSWR(
    getMarketsUrl(),
    fetcher,
    { 
      refreshInterval: POLL_INTERVALS.NORMAL,
      revalidateOnFocus: true,
      dedupingInterval: 2000,
      fallbackData: { markets: [], total: 0, filtered: 0 },
      onSuccess: (data) => {
        // Update previous volumes for flash effect
        const newVolumes = {};
        (data.markets || []).forEach(m => {
          newVolumes[m.id] = m.total_volume;
        });
        previousVolumesRef.current = newVolumes;
      }
    }
  );

  // SWR for stats - refreshes less frequently
  const { data: stats } = useSWR(
    ENDPOINTS.MARKETS_STATS,
    fetcher,
    { 
      refreshInterval: POLL_INTERVALS.SLOW,
      revalidateOnFocus: true,
      fallbackData: null
    }
  );

  const markets = marketsData?.markets || [];
  const loading = marketsLoading;
  const error = marketsError?.message;

  // Refresh markets (fetch new events from news APIs)
  const refreshMarkets = async () => {
    setIsRefreshing(true);
    try {
      await postRequest(ENDPOINTS.MARKETS_REFRESH, {});
      // Revalidate both markets and stats
      await mutateMarkets();
    } catch (err) {
      console.error("Failed to refresh markets:", err);
    } finally {
      setIsRefreshing(false);
    }
  };

  // Place a bet
  const placeBet = async (marketId, outcome, amount) => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      toast.error("Please log in to place bets");
      return;
    }
    
    try {
      const data = await postRequest(
        ENDPOINTS.MARKET_BET(marketId), 
        { outcome, amount },
        true // authenticated
      );
      
      toast.success(`Bet Placed! Potential: $${data.potential_payout}`, {
        icon: '💸',
        style: { background: '#064e3b', color: '#fff', border: '1px solid #059669' }
      });
      setSelectedMarket(null);
      mutateMarkets(); // Refresh markets after bet
    } catch (err) {
      toast.error(err.message);
    }
  };

  // Get previous volume for flash effect
  const getPreviousVolume = (marketId) => previousVolumesRef.current[marketId];

  return (
    <div className="min-h-screen bg-gray-950 py-8 px-4">
      <div className="container mx-auto max-w-7xl">
        {/* Header */}
        <div className="flex justify-between items-start mb-8">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">
              🎰 Betting Markets
            </h1>
            <p className="text-gray-400">
              AI-powered prediction markets from real-world events
            </p>
            {!marketsError && (
              <div className="flex items-center gap-2 mt-1">
                <span className={`w-2 h-2 rounded-full ${loading ? 'bg-yellow-400' : 'bg-green-400'} animate-pulse`} />
                <span className="text-xs text-gray-500">
                  {loading ? 'Syncing...' : 'Live'} • Auto-updates every 10s
                </span>
              </div>
            )}
          </div>
          <button
            onClick={refreshMarkets}
            disabled={isRefreshing}
            className={`px-6 py-3 rounded-lg font-semibold transition-all ${
              isRefreshing 
                ? "bg-gray-700 cursor-wait" 
                : "bg-purple-600 hover:bg-purple-700"
            }`}
          >
            {isRefreshing ? "⏳ Fetching News..." : "🔄 Refresh Markets"}
          </button>
        </div>

        {/* Stats Bar */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
            <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-white">{stats.total_markets || 0}</div>
              <div className="text-xs text-gray-400">Total Markets</div>
            </div>
            <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-green-400">${stats.total_volume?.toFixed(0) || 0}</div>
              <div className="text-xs text-gray-400">Total Volume</div>
            </div>
            <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-blue-400">{stats.by_status?.OPEN || 0}</div>
              <div className="text-xs text-gray-400">Open Markets</div>
            </div>
            <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-purple-400">
                {stats.orchestrator_stats?.events_processed || 0}
              </div>
              <div className="text-xs text-gray-400">Events Processed</div>
            </div>
            <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-orange-400">
                {stats.orchestrator_stats?.markets_auto_created || 0}
              </div>
              <div className="text-xs text-gray-400">Auto-Created</div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="flex flex-wrap gap-3 mb-6">
          {/* Domain Filter */}
          <div className="flex gap-1 bg-gray-800 rounded-lg p-1">
            <button
              onClick={() => setDomainFilter(null)}
              className={`px-3 py-1 rounded text-sm transition-all ${
                !domainFilter ? "bg-purple-600 text-white" : "text-gray-400 hover:text-white"
              }`}
            >
              All
            </button>
            {Object.entries(DOMAIN_COLORS).filter(([k]) => k !== "unknown").map(([domain, config]) => (
              <button
                key={domain}
                onClick={() => setDomainFilter(domain)}
                className={`px-3 py-1 rounded text-sm transition-all ${
                  domainFilter === domain ? `${config.bg} ${config.text}` : "text-gray-400 hover:text-white"
                }`}
              >
                {config.icon} {domain}
              </button>
            ))}
          </div>
          
          {/* Duration Filter */}
          <div className="flex gap-1 bg-gray-800 rounded-lg p-1">
            <button
              onClick={() => setDurationFilter(null)}
              className={`px-3 py-1 rounded text-sm transition-all ${
                !durationFilter ? "bg-purple-600 text-white" : "text-gray-400 hover:text-white"
              }`}
            >
              Any Duration
            </button>
            {Object.entries(DURATION_LABELS).map(([duration, config]) => (
              <button
                key={duration}
                onClick={() => setDurationFilter(duration)}
                className={`px-3 py-1 rounded text-sm transition-all ${
                  durationFilter === duration ? `${config.bg} ${config.color}` : "text-gray-400 hover:text-white"
                }`}
              >
                {config.label}
              </button>
            ))}
          </div>
          
          {/* Status Filter */}
          <div className="flex gap-1 bg-gray-800 rounded-lg p-1">
            {["OPEN", "CLOSED", "SETTLED", null].map((status) => (
              <button
                key={status || "all"}
                onClick={() => setStatusFilter(status)}
                className={`px-3 py-1 rounded text-sm transition-all ${
                  statusFilter === status ? "bg-purple-600 text-white" : "text-gray-400 hover:text-white"
                }`}
              >
                {status || "All Status"}
              </button>
            ))}
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-900/30 border border-red-700 rounded-lg text-red-400">
            ⚠️ {error}
          </div>
        )}

        {/* Markets Grid */}
        {loading ? (
          <div className="text-center py-20">
            <div className="animate-spin w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full mx-auto mb-4" />
            <p className="text-gray-400">Loading markets...</p>
          </div>
        ) : markets.length === 0 ? (
          <div className="text-center py-20 bg-gray-900 rounded-xl">
            <div className="text-6xl mb-4">📊</div>
            <h3 className="text-xl font-bold text-white mb-2">No Markets Found</h3>
            <p className="text-gray-400 mb-6">
              {domainFilter || durationFilter || statusFilter 
                ? "Try adjusting your filters or refresh to fetch new events."
                : "Click 'Refresh Markets' to fetch news and create betting markets."}
            </p>
            <button
              onClick={refreshMarkets}
              disabled={isRefreshing}
              className="px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg font-semibold transition-all"
            >
              🔄 Fetch News & Create Markets
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {markets.map((market) => (
              <MarketCard 
                key={market.id} 
                market={market} 
                onSelect={setSelectedMarket}
                previousVolume={getPreviousVolume(market.id)}
              />
            ))}
          </div>
        )}

        {/* Market Detail Modal */}
        {selectedMarket && (
          <MarketDetailModal
            market={selectedMarket}
            onClose={() => setSelectedMarket(null)}
            onBet={placeBet}
          />
        )}
      </div>
    </div>
  );
}
