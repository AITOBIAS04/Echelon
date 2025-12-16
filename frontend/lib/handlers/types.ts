export interface Handler {
  id: string;
  name: string;
  avatar: string; // URL or emoji
  personality: string; // System prompt
  creator: string;
  price: number; // 0 = free, >0 = cost in PLAY
  description: string;
  tags: string[]; // e.g., ['aggressive', 'data-focused']
}

export interface HandlerMessage {
  id: string;
  role: "handler" | "user";
  content: string;
  timestamp: Date;
}

export interface Operation {
  id: string;
  codename: string;
  description: string;
}

export interface Position {
  id: string;
  type: string;
  amount: number;
  marketId: string;
}

export interface Signal {
  id: string;
  type: string;
  message: string;
  timestamp: Date;
}

export interface MarketState {
  marketId: string;
  currentPrice: number;
  volume: number;
  trend: string;
}

export interface HandlerContext {
  currentOperation?: Operation;
  userPositions?: Position[];
  recentSignals?: Signal[];
  marketState?: MarketState;
}


