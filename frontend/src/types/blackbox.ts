// Blackbox Types
// Types for the Blackbox trading terminal page

export type Timeframe = '1m' | '5m' | '15m' | '1H' | '4H' | '1D';

export type EventType = 'market' | 'sabotage' | 'shield' | 'fork' | 'paradox';

export type AgentArchetype = 'whale' | 'shark' | 'diplomat' | 'spy' | 'saboteur' | 'degen';

export interface Agent {
  id: string;
  name: string;
  archetype: AgentArchetype;
  pnl: number;
  pnlDisplay: string;
  winRate: number;
  sharpe: number;
  trades: number;
  volume: number;
  volumeDisplay: string;
  status: 'Active' | 'Inactive' | 'Paused';
}

export interface Candle {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface OrderBookEntry {
  price: number;
  size: number;
  total: number;
  depth: number;
}

export interface OrderBook {
  bids: OrderBookEntry[];
  asks: OrderBookEntry[];
  spread: number;
  spreadPercent: number;
  midPrice: number;
  totalBids: number;
  totalAsks: number;
}

export interface Trade {
  id: string;
  timestamp: Date;
  price: number;
  size: number;
  side: 'buy' | 'sell';
  agent: string;
}

export interface ChartIndicators {
  rsi: number;
  macd: number;
  macdSignal: number;
  macdHist: number;
  volume: number;
  high: number;
  low: number;
}

export interface TimelineEvent {
  id: string;
  title: string;
  probability: number;
  timeRemaining: string;
  status: 'active' | 'warning' | 'collapsed' | 'settled';
  forks: number;
  type: EventType;
  riskScore?: number;
  exposure?: number;
}

export interface WarChestItem {
  id: string;
  title: string;
  riskScore: number;
  exposure: number;
  status: 'active' | 'warning' | 'collapsed';
  type: EventType;
}

export interface Intercept {
  id: string;
  icon: string;
  title: string;
  timestamp: Date;
  details: string;
  source: string;
  severity: 'critical' | 'warning' | 'info' | 'success';
  theatre?: string;
  agent?: string;
}

export interface RibbonEvent {
  id: string;
  type: EventType;
  theatre: string;
  agent: string;
  action: string;
  delta: string;
  timestamp: Date;
}

export interface BlackboxState {
  currentPrice: number;
  priceChange: number;
  priceChangePercent: number;
  selectedTimeframe: Timeframe;
  selectedTab: 'markets' | 'intercepts' | 'timeline' | 'warchest';
  showAlertPanel: boolean;
  showCompareSidebar: boolean;
}

export interface BlackboxActions {
  setTimeframe: (tf: Timeframe) => void;
  setTab: (tab: 'markets' | 'intercepts' | 'timeline' | 'warchest') => void;
  toggleAlertPanel: () => void;
  toggleCompareSidebar: () => void;
}
