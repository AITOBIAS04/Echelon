// Order Book Component
// Real-time order book display with depth visualization

import type { OrderBook } from '../../types/blackbox';

interface OrderBookProps {
  orderBook: OrderBook | null;
  currentPrice: number;
}

export function OrderBookPanel({ orderBook, currentPrice }: OrderBookProps) {
  if (!orderBook) {
    return (
      <div className="rounded-2xl border border-terminal-border bg-terminal-panel flex flex-col min-h-0">
        <div className="flex items-center justify-between px-4 py-3 border-b border-terminal-border">
          <span className="text-sm font-semibold text-terminal-text">ORDER BOOK</span>
          <span className="text-xs font-mono tabular-nums text-terminal-text-muted">$--</span>
        </div>
        <div className="flex-1 flex items-center justify-center text-xs text-terminal-text-muted">
          Loading order book...
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-terminal-border bg-terminal-panel flex flex-col min-h-0">
      {/* Card Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-terminal-border">
        <span className="text-sm font-semibold text-terminal-text">ORDER BOOK</span>
        <span className="text-xs font-mono tabular-nums text-terminal-text-muted">${currentPrice.toFixed(2)}</span>
      </div>

      {/* Order Book Body */}
      <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
        {/* Asks Header */}
        <div className="flex items-center justify-between px-3 py-1.5 text-[10px] text-terminal-text-muted">
          <span>ASKS</span>
          <span>Total: ${(orderBook.totalAsks / 1000).toFixed(1)}K</span>
        </div>

        {/* Asks List */}
        <div className="flex-1 min-h-0 overflow-hidden flex flex-col-reverse">
          {orderBook.asks.map((ask, i) => (
            <div key={i} className="relative flex items-center h-5 text-xs">
              <div
                className="absolute inset-0 bg-echelon-red"
                style={{ opacity: 0.15, width: `${ask.depth}%` }}
              />
              <span className="z-10 w-16 px-3 py-0.5 text-echelon-red font-mono tabular-nums">
                ${ask.price.toFixed(2)}
              </span>
              <span className="z-10 flex-1 px-3 py-0.5 text-terminal-text font-mono tabular-nums text-right">
                {(ask.size / 1000).toFixed(1)}K
              </span>
            </div>
          ))}
        </div>

        {/* Spread */}
        <div className="flex items-center justify-between px-3 py-1.5 text-xs border-y border-terminal-border">
          <span className="text-terminal-text-muted">SPREAD</span>
          <div className="flex items-center gap-3">
            <span className="font-mono tabular-nums text-terminal-text">{orderBook.spread.toFixed(3)}</span>
            <span className="text-terminal-text-muted">{orderBook.spreadPercent.toFixed(2)}%</span>
          </div>
        </div>

        {/* Bids List */}
        <div className="flex-1 min-h-0 overflow-hidden">
          {orderBook.bids.map((bid, i) => (
            <div key={i} className="relative flex items-center h-5 text-xs">
              <div
                className="absolute inset-0 bg-echelon-green"
                style={{ opacity: 0.15, width: `${bid.depth}%` }}
              />
              <span className="z-10 w-16 px-3 py-0.5 text-echelon-green font-mono tabular-nums">
                ${bid.price.toFixed(2)}
              </span>
              <span className="z-10 flex-1 px-3 py-0.5 text-terminal-text font-mono tabular-nums text-right">
                {(bid.size / 1000).toFixed(1)}K
              </span>
            </div>
          ))}
        </div>

        {/* Bids Header */}
        <div className="flex items-center justify-between px-3 py-1.5 text-[10px] text-terminal-text-muted border-t border-terminal-border">
          <span>BIDS</span>
          <span>Total: ${(orderBook.totalBids / 1000).toFixed(1)}K</span>
        </div>
      </div>
    </div>
  );
}
