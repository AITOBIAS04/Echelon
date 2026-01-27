// Blackbox Hooks
// React hooks for Blackbox data management

import { useState, useEffect, useMemo } from 'react';
import type {
  Agent,
  Candle,
  OrderBook,
  Trade,
  ChartIndicators,
  TimelineEvent,
  WarChestItem,
  Intercept,
  RibbonEvent,
  Timeframe,
} from '../types/blackbox';

// Generate mock candles
function generateCandles(count: number, startPrice: number): Candle[] {
  const candles: Candle[] = [];
  let currentPrice = startPrice;
  const now = Date.now();
  const intervalMs = 15 * 60 * 1000; // 15m candles

  for (let i = count - 1; i >= 0; i--) {
    const open = currentPrice;
    const volatility = 0.015;
    const change = (Math.random() - 0.48) * volatility * currentPrice;
    const close = open + change;
    const high = Math.max(open, close) + Math.random() * volatility * currentPrice * 0.5;
    const low = Math.min(open, close) - Math.random() * volatility * currentPrice * 0.5;
    const volume = Math.floor(Math.random() * 40000) + 10000;

    candles.push({
      timestamp: now - i * intervalMs,
      open,
      high,
      low,
      close,
      volume,
    });

    currentPrice = close;
  }

  return candles;
}

// Generate mock order book
function generateOrderBook(midPrice: number): OrderBook {
  const bids: OrderBook['bids'] = [];
  const asks: OrderBook['asks'] = [];
  let totalBids = 0;
  let totalAsks = 0;

  for (let i = 0; i < 12; i++) {
    const bidPrice = midPrice - 0.01 * (i + 1) - Math.random() * 0.005;
    const bidSize = Math.floor(Math.random() * 49000) + 1000;
    const bidDepth = Math.random() * 100;
    totalBids += bidSize;
    bids.push({ price: bidPrice, size: bidSize, total: totalBids, depth: bidDepth });

    const askPrice = midPrice + 0.01 * (i + 1) + Math.random() * 0.005;
    const askSize = Math.floor(Math.random() * 49000) + 1000;
    const askDepth = Math.random() * 100;
    totalAsks += askSize;
    asks.push({ price: askPrice, size: askSize, total: totalAsks, depth: askDepth });
  }

  const spread = asks[0].price - bids[0].price;
  const spreadPercent = (spread / midPrice) * 100;

  return {
    bids,
    asks,
    spread,
    spreadPercent,
    midPrice,
    totalBids,
    totalAsks,
  };
}

// Mock agents data
const mockAgents: Agent[] = [
  { id: '1', name: 'LEVIATHAN', archetype: 'whale', pnl: 24560, pnlDisplay: '+24,560', winRate: 72.4, sharpe: 2.34, trades: 87, volume: 1200000, volumeDisplay: '$1.2M', status: 'Active' },
  { id: '2', name: 'TITAN', archetype: 'shark', pnl: 18420, pnlDisplay: '+18,420', winRate: 68.2, sharpe: 1.92, trades: 124, volume: 890000, volumeDisplay: '$890K', status: 'Active' },
  { id: '3', name: 'AMBASSADOR', archetype: 'diplomat', pnl: 15870, pnlDisplay: '+15,870', winRate: 74.8, sharpe: 2.15, trades: 62, volume: 650000, volumeDisplay: '$650K', status: 'Active' },
  { id: '4', name: 'CARDINAL', archetype: 'spy', pnl: 12340, pnlDisplay: '+12,340', winRate: 81.2, sharpe: 2.48, trades: 45, volume: 420000, volumeDisplay: '$420K', status: 'Active' },
  { id: '5', name: 'DEPTH', archetype: 'whale', pnl: 9850, pnlDisplay: '+9,850', winRate: 65.4, sharpe: 1.67, trades: 73, volume: 380000, volumeDisplay: '$380K', status: 'Active' },
  { id: '6', name: 'STRIKER', archetype: 'shark', pnl: 7230, pnlDisplay: '+7,230', winRate: 58.9, sharpe: 1.34, trades: 156, volume: 920000, volumeDisplay: '$920K', status: 'Active' },
  { id: '7', name: 'HARBOR', archetype: 'diplomat', pnl: 5120, pnlDisplay: '+5,120', winRate: 69.7, sharpe: 1.78, trades: 51, volume: 280000, volumeDisplay: '$280K', status: 'Active' },
  { id: '8', name: 'CHAOS', archetype: 'saboteur', pnl: -3450, pnlDisplay: '-3,450', winRate: 42.1, sharpe: 0.85, trades: 89,volume: 540000, volumeDisplay: '$540K', status: 'Active' },
];

// Mock timeline events
const mockTimelines: TimelineEvent[] = [
  { id: 'TL-2847', title: 'ORBITAL SALVAGE F7', probability: 0.72, timeRemaining: '48h', status: 'active', forks: 7, type: 'fork' },
  { id: 'TL-2846', title: 'FED RATE DECISION', probability: 0.58, timeRemaining: '5d', status: 'active', forks: 3, type: 'market' },
  { id: 'TL-2845', title: 'VENUS OIL TANKER', probability: 0.45, timeRemaining: '12d', status: 'warning', forks: 12, type: 'sabotage' },
  { id: 'TL-2844', title: 'TAIWAN STRAIT', probability: 0.62, timeRemaining: '18d', status: 'active', forks: 5, type: 'shield' },
  { id: 'TL-2843', title: 'SPACEX LAUNCH', probability: 0.51, timeRemaining: '26d', status: 'active', forks: 8, type: 'market' },
  { id: 'TL-2842', title: 'PUTIN HEALTH RUMORS', probability: 0.38, timeRemaining: '1mo', status: 'collapsed', forks: 15, type: 'paradox' },
];

// Mock intercepts
const mockIntercepts: Intercept[] = [
  { id: '1', icon: '🎯', title: 'Large Buy Order', timestamp: new Date(), details: 'WHALE agent accumulated 50K shares at $3.78', source: 'Order Flow', severity: 'info', theatre: 'ORB_SALVAGE_F7', agent: 'WHALE' },
  { id: '2', icon: '⚠️', title: 'Unusual Volume', timestamp: new Date(), details: 'Volume spike 3x average on TL-2847', source: 'Volume Analyzer', severity: 'warning', theatre: 'TL-2847' },
  { id: '3', icon: '💀', title: 'Spread Manipulation', timestamp: new Date(), details: 'SABOTEUR agent spreading asks to move price', source: 'Market Monitor', severity: 'critical', theatre: 'FED_RATE_DECISION' },
  { id: '4', icon: '🔀', title: 'Fork Detected', timestamp: new Date(), details: 'New timeline fork: TL-2847-fork-7', source: 'Fork Scanner', severity: 'info' },
  { id: '5', icon: '🛡️', title: 'Hedge Placed', timestamp: new Date(), details: 'DIPLOMAT agent opened protective position', source: 'Position Tracker', severity: 'success' },
];

// Mock ribbon events
const mockRibbonEvents: RibbonEvent[] = [
  { id: '1', type: 'market', theatre: 'ORB_SALVAGE_F7', agent: 'MEGALODON', action: 'Opened large position', delta: '+42K', timestamp: new Date() },
  { id: '2', type: 'shield', theatre: 'ORB_SALVAGE_F7', agent: 'AEGIS', action: 'Hedge placed', delta: '+28K', timestamp: new Date() },
  { id: '3', type: 'sabotage', theatre: 'FED_RATE_DECISION', agent: 'LEECH', action: 'Spread attack detected', delta: '-15K', timestamp: new Date() },
  { id: '4', type: 'fork', theatre: 'TL-2847', agent: 'GHOST', action: 'New fork detected', delta: '7 forks', timestamp: new Date() },
];

// Hook for chart data
export function useBlackboxChart(timeframe: Timeframe) {
  const [candles, setCandles] = useState<Candle[]>([]);
  const [currentPrice, setCurrentPrice] = useState(3.82);
  const [priceChange] = useState(0.08);
  const [priceChangePercent, setPriceChangePercent] = useState(2.14);

  useEffect(() => {
    const initialCandles = generateCandles(60, 3.74);
    setCandles(initialCandles);
    if (initialCandles.length > 0) {
      setCurrentPrice(initialCandles[initialCandles.length - 1].close);
    }
  }, [timeframe]);

  // Simulate live updates
  useEffect(() => {
    const interval = setInterval(() => {
      setCandles((prev) => {
        const last = prev[prev.length - 1];
        const newCandle = {
          ...last,
          close: last.close + (Math.random() - 0.5) * 0.02,
          high: Math.max(last.high, last.close + Math.random() * 0.01),
          low: Math.min(last.low, last.close - Math.random() * 0.01),
          volume: last.volume + Math.floor(Math.random() * 1000),
        };
        return [...prev.slice(1), newCandle];
      });
      setCurrentPrice((prev) => prev + (Math.random() - 0.5) * 0.01);
      setPriceChangePercent((prev) => prev + (Math.random() - 0.5) * 0.1);
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const indicators = useMemo<ChartIndicators>(() => ({
    rsi: 58.3,
    macd: 0.12,
    macdSignal: 0.08,
    macdHist: 0.04,
    volume: candles.length > 0 ? candles[candles.length - 1].volume : 142000,
    high: candles.length > 0 ? Math.max(...candles.map((c) => c.high)) : 4.02,
    low: candles.length > 0 ? Math.min(...candles.map((c) => c.low)) : 3.58,
  }), [candles]);

  return { candles, currentPrice, priceChange, priceChangePercent, indicators };
}

// Hook for order book
export function useOrderBook() {
  const [orderBook, setOrderBook] = useState<OrderBook | null>(null);
  const [midPrice] = useState(3.82);

  useEffect(() => {
    setOrderBook(generateOrderBook(midPrice));
  }, [midPrice]);

  // Simulate order book updates
  useEffect(() => {
    const interval = setInterval(() => {
      setOrderBook(generateOrderBook(midPrice));
    }, 5000);

    return () => clearInterval(interval);
  }, [midPrice]);

  return orderBook;
}

// Hook for time & sales
export function useTimeSales() {
  const [trades, setTrades] = useState<Trade[]>([]);

  const generateTrade = (): Trade => ({
    id: Math.random().toString(36).substr(2, 9),
    timestamp: new Date(Date.now() - Math.random() * 30000),
    price: 3.80 + Math.random() * 0.05,
    size: Math.floor(Math.random() * 24000) + 1000,
    side: Math.random() > 0.45 ? 'buy' : 'sell',
    agent: mockAgents[Math.floor(Math.random() * 6)].name,
  });

  useEffect(() => {
    const initialTrades = Array.from({ length: 20 }, generateTrade).sort(
      (a, b) => b.timestamp.getTime() - a.timestamp.getTime()
    );
    setTrades(initialTrades);
  }, []);

  // Simulate new trades
  useEffect(() => {
    const interval = setInterval(() => {
      setTrades((prev) => {
        const newTrade = {
          ...generateTrade(),
          timestamp: new Date(),
        };
        return [newTrade, ...prev.slice(0, 19)];
      });
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  return trades;
}

// Hook for agent leaderboard
export function useAgentLeaderboard() {
  const [agents] = useState<Agent[]>(mockAgents);
  const [searchQuery, setSearchQuery] = useState('');

  const filteredAgents = useMemo(() => {
    if (!searchQuery) return agents;
    return agents.filter((a) =>
      a.name.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [agents, searchQuery]);

  const sortedAgents = useMemo(() => {
    return [...filteredAgents].sort((a, b) => b.pnl - a.pnl);
  }, [filteredAgents]);

  return { agents: sortedAgents, searchQuery, setSearchQuery };
}

// Hook for timeline data
export function useTimelines() {
  return mockTimelines;
}

// Hook for war chest data
export function useWarChest() {
  const warItems: WarChestItem[] = mockTimelines
    .filter((t) => t.type === 'fork' || t.status === 'warning')
    .map((t) => ({
      id: t.id,
      title: t.title,
      riskScore: Math.floor(Math.random() * 35) + 40,
      exposure: Math.floor(Math.random() * 90) * 1000 + 10000,
      status: t.status === 'warning' ? 'warning' : 'active',
      type: t.type,
    }));

  return warItems;
}

// Hook for intercepts
export function useIntercepts() {
  const [intercepts] = useState<Intercept[]>(mockIntercepts);
  return intercepts;
}

// Hook for ribbon events
export function useBlackboxRibbon() {
  return mockRibbonEvents;
}

// Hook for system status
export function useSystemStatus() {
  const [latency, setLatency] = useState(12);

  useEffect(() => {
    const interval = setInterval(() => {
      setLatency(Math.floor(Math.random() * 10) + 8);
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  return { latency };
}
