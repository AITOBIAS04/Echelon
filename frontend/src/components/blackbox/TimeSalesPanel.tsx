// Time & Sales Component
// Real-time trade feed

import type { Trade } from '../../types/blackbox';

interface TimeSalesProps {
  trades: Trade[];
}

export function TimeSalesPanel({ trades }: TimeSalesProps) {
  const formatTime = (date: Date) => {
    return date.toISOString().substr(11, 8);
  };

  const formatSize = (size: number) => {
    if (size >= 1000) {
      return (size / 1000).toFixed(1) + 'K';
    }
    return size.toString();
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">TIME & SALES</span>
        <span className="mono neutral" style={{ fontSize: 10 }}>
          LIVE FEED
        </span>
      </div>
      <div className="data-list" style={{ flex: 1, overflow: 'auto', maxHeight: 280 }}>
        <div className="data-row header" style={{ position: 'sticky', top: 0 }}>
          <span className="col-time">TIME</span>
          <span className="col-price">PRICE</span>
          <span className="col-size">SIZE</span>
          <span className="col-side">SIDE</span>
          <span className="col-agent">AGENT</span>
        </div>
        {trades.map((trade) => (
          <div key={trade.id} className="data-row flash-new">
            <span className="col-time mono">{formatTime(trade.timestamp)}</span>
            <span className={`col-price ${trade.side === 'buy' ? 'positive' : 'negative'}`}>
              ${trade.price.toFixed(2)}
            </span>
            <span className="col-size">{formatSize(trade.size)}</span>
            <span className="col-side">
              <span className={`side-badge ${trade.side}`}>{trade.side.toUpperCase()}</span>
            </span>
            <span className="col-agent">{trade.agent}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
