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
    <div className="rounded-2xl terminal-panel flex flex-col min-h-0">
      {/* Card Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-terminal-border">
        <span className="text-sm font-semibold text-terminal-text">TIME & SALES</span>
        <span className="text-xs font-mono text-terminal-text-muted">LIVE FEED</span>
      </div>

      {/* Table */}
      <div className="flex-1 min-h-0 overflow-y-auto pr-1">
        <table className="w-full table-fixed">
          <thead className="sticky top-0 bg-terminal-header z-10">
            <tr>
              <th className="w-[88px] px-3 py-2 text-left text-xs font-medium text-terminal-text-muted">TIME</th>
              <th className="w-[72px] px-3 py-2 text-left text-xs font-medium text-terminal-text-muted">PRICE</th>
              <th className="w-[56px] px-3 py-2 text-left text-xs font-medium text-terminal-text-muted">SIZE</th>
              <th className="w-[56px] px-3 py-2 text-left text-xs font-medium text-terminal-text-muted">SIDE</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-terminal-text-muted">AGENT</th>
            </tr>
</thead>
          <tbody>
            {trades.map((trade) => (
              <tr key={trade.id} className="hover:bg-terminal-hover transition-colors">
                <td className="px-3 py-1.5 text-xs font-mono text-terminal-text-secondary">{formatTime(trade.timestamp)}</td>
                <td className={`px-3 py-1.5 text-xs font-mono ${trade.side === 'buy' ? 'text-echelon-green' : 'text-echelon-red'}`}>
                  ${trade.price.toFixed(2)}
                </td>
                <td className="px-3 py-1.5 text-xs text-terminal-text">{formatSize(trade.size)}</td>
                <td className="px-3 py-1.5">
                  <span className={`inline-block px-1.5 py-0.5 text-xs font-medium rounded ${
                    trade.side === 'buy'
                      ? 'bg-echelon-green/15 text-echelon-green'
                      : 'bg-echelon-red/15 text-echelon-red'
                  }`}>
                    {trade.side.toUpperCase()}
                  </span>
                </td>
                <td className="px-3 py-1.5 text-xs text-terminal-text truncate">{trade.agent}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
