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
      <div className="panel order-book-container">
        <div className="panel-header">
          <span className="panel-title">ORDER BOOK</span>
          <span className="panel-title neutral mono" style={{ fontSize: 11 }}>
            $--
        </span>
        </div>
        <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading order book...
        </div>
      </div>
    );
  }

  return (
    <div className="panel order-book-container">
      <div className="panel-header">
        <span className="panel-title">ORDER BOOK</span>
        <span className="panel-title neutral mono" style={{ fontSize: 11 }}>
          ${currentPrice.toFixed(2)}
        </span>
      </div>
      <div className="book-sides">
        {/* Asks (sell orders) */}
        <div className="book-header-info">
          <span>ASKS</span>
          <span>Total: ${(orderBook.totalAsks / 1000).toFixed(1)}K</span>
        </div>
        <div
          style={{
            display: 'flex',
            flexDirection: 'column-reverse',
            maxHeight: 180,
            overflow: 'hidden',
          }}
        >
          {orderBook.asks.map((ask, i) => (
            <div key={i} className="book-row">
              <div
                className="depth-bar ask"
                style={{ width: `${ask.depth}%`, background: 'var(--status-danger)' }}
              />
              <span className="book-price negative" style={{ zIndex: 1 }}>
                ${ask.price.toFixed(2)}
              </span>
              <span className="book-size mono" style={{ zIndex: 1 }}>
                {(ask.size / 1000).toFixed(1)}K
              </span>
            </div>
          ))}
        </div>

        {/* Spread indicator */}
        <div className="spread-indicator">
          <span>SPREAD: {orderBook.spread.toFixed(3)}</span>
          <span>{orderBook.spreadPercent.toFixed(2)}%</span>
        </div>

        {/* Bids (buy orders) */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            maxHeight: 180,
            overflow: 'hidden',
          }}
        >
          {orderBook.bids.map((bid, i) => (
            <div key={i} className="book-row">
              <div
                className="depth-bar bid"
                style={{ width: `${bid.depth}%`, background: 'var(--status-success)' }}
              />
              <span className="book-price positive" style={{ zIndex: 1 }}>
                ${bid.price.toFixed(2)}
              </span>
              <span className="book-size mono" style={{ zIndex: 1 }}>
                {(bid.size / 1000).toFixed(1)}K
              </span>
            </div>
          ))}
        </div>
        <div className="book-header-info" style={{ borderTop: '1px solid var(--border-inner)', borderBottom: 'none' }}>
          <span>BIDS</span>
          <span>Total: ${(orderBook.totalBids / 1000).toFixed(1)}K</span>
        </div>
      </div>
    </div>
  );
}
