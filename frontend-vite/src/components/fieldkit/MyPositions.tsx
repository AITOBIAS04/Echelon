import { ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';
import { clsx } from 'clsx';

// Mock data - replace with real API
const mockPositions = [
  {
    id: 'pos_1',
    timeline_id: 'TL_FED_RATE',
    timeline_name: 'Fed Rate Decision - January 2026',
    side: 'YES',
    shares: 500,
    avg_price: 0.65,
    current_price: 0.72,
    value_usd: 360,
    pnl_usd: 35,
    pnl_percent: 10.77,
  },
  {
    id: 'pos_2',
    timeline_id: 'TL_CONTAGION',
    timeline_name: 'Contagion Zero - Mumbai Outbreak',
    side: 'NO',
    shares: 200,
    avg_price: 0.25,
    current_price: 0.18,
    value_usd: 36,
    pnl_usd: 14,
    pnl_percent: 38.89,
  },
  {
    id: 'pos_3',
    timeline_id: 'TL_GHOST_TANKER',
    timeline_name: 'Ghost Tanker - Venezuela Dark Fleet',
    side: 'YES',
    shares: 1000,
    avg_price: 0.70,
    current_price: 0.67,
    value_usd: 670,
    pnl_usd: -30,
    pnl_percent: -4.29,
  },
];

export function MyPositions() {
  const totalValue = mockPositions.reduce((sum, p) => sum + p.value_usd, 0);
  const totalPnL = mockPositions.reduce((sum, p) => sum + p.pnl_usd, 0);

  return (
    <div className="h-full flex flex-col">
      {/* Summary */}
      <div className="flex items-center justify-between mb-4 p-3 bg-terminal-bg rounded">
        <div>
          <span className="text-xs text-terminal-muted">Portfolio Value</span>
          <div className="text-lg font-mono font-bold text-terminal-text">
            ${totalValue.toLocaleString()}
          </div>
        </div>
        <div className="text-right">
          <span className="text-xs text-terminal-muted">Unrealised P&L</span>
          <div
            className={clsx(
              'text-lg font-mono font-bold',
              totalPnL >= 0 ? 'text-echelon-green' : 'text-echelon-red'
            )}
          >
            {totalPnL >= 0 ? '+' : ''}${totalPnL.toFixed(2)}
          </div>
        </div>
      </div>

      {/* Positions Table */}
      <div className="flex-1 overflow-y-auto">
        <table className="w-full">
          <thead className="sticky top-0 bg-terminal-panel">
            <tr className="text-xs text-terminal-muted uppercase">
              <th className="text-left p-3">Timeline</th>
              <th className="text-center p-3">Side</th>
              <th className="text-right p-3">Shares</th>
              <th className="text-right p-3">Avg Price</th>
              <th className="text-right p-3">Current</th>
              <th className="text-right p-3">Value</th>
              <th className="text-right p-3">P&L</th>
              <th className="text-center p-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-terminal-border">
            {mockPositions.map((position) => (
              <tr key={position.id} className="hover:bg-terminal-bg/50 transition">
                <td className="p-3">
                  <div className="font-medium text-terminal-text text-sm">
                    {position.timeline_name}
                  </div>
                  <div className="text-xs text-terminal-muted">
                    {position.timeline_id}
                  </div>
                </td>
                <td className="p-3 text-center">
                  <span
                    className={clsx(
                      'px-2 py-1 rounded text-xs font-bold',
                      position.side === 'YES'
                        ? 'bg-echelon-green/20 text-echelon-green'
                        : 'bg-echelon-red/20 text-echelon-red'
                    )}
                  >
                    {position.side}
                  </span>
                </td>
                <td className="p-3 text-right font-mono text-sm">
                  {position.shares.toLocaleString()}
                </td>
                <td className="p-3 text-right font-mono text-sm text-terminal-muted">
                  ${position.avg_price.toFixed(2)}
                </td>
                <td className="p-3 text-right font-mono text-sm">
                  ${position.current_price.toFixed(2)}
                </td>
                <td className="p-3 text-right font-mono text-sm">
                  ${position.value_usd.toLocaleString()}
                </td>
                <td className="p-3 text-right">
                  <div
                    className={clsx(
                      'font-mono text-sm font-medium',
                      position.pnl_usd >= 0 ? 'text-echelon-green' : 'text-echelon-red'
                    )}
                  >
                    {position.pnl_usd >= 0 ? '+' : ''}${position.pnl_usd.toFixed(2)}
                  </div>
                  <div
                    className={clsx(
                      'text-xs',
                      position.pnl_percent >= 0 ? 'text-echelon-green' : 'text-echelon-red'
                    )}
                  >
                    {position.pnl_percent >= 0 ? '+' : ''}{position.pnl_percent.toFixed(1)}%
                  </div>
                </td>
                <td className="p-3 text-center">
                  <Link
                    to={`/timeline/${position.timeline_id}`}
                    className="text-terminal-muted hover:text-echelon-cyan transition"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

