import { Eye, Plus, Bell, Trash2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { clsx } from 'clsx';

// Mock data
const mockWatchlist = [
  {
    timeline_id: 'TL_OIL_CRISIS',
    timeline_name: 'Oil Crisis - Hormuz Strait',
    price_yes: 0.45,
    stability: 54.7,
    alert_price: 0.50,
    alert_stability: 40,
  },
  {
    timeline_id: 'TL_FED_RATE',
    timeline_name: 'Fed Rate Decision - January 2026',
    price_yes: 0.72,
    stability: 89.2,
    alert_price: null,
    alert_stability: null,
  },
];

export function Watchlist() {
  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Eye className="w-4 h-4 text-echelon-cyan" />
          <span className="text-sm text-terminal-text">Watching {mockWatchlist.length} timelines</span>
        </div>
        <button className="flex items-center gap-2 px-3 py-1.5 text-xs bg-terminal-bg border border-terminal-border rounded hover:border-echelon-cyan transition">
          <Plus className="w-3 h-3" />
          Add Timeline
        </button>
      </div>

      {/* Watchlist Items */}
      <div className="flex-1 overflow-y-auto space-y-2">
        {mockWatchlist.map((item) => (
          <div key={item.timeline_id} className="terminal-panel p-3">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <Link
                  to={`/timeline/${item.timeline_id}`}
                  className="font-medium text-terminal-text hover:text-echelon-cyan transition"
                >
                  {item.timeline_name}
                </Link>
                <div className="flex items-center gap-4 mt-1 text-xs text-terminal-muted">
                  <span>YES: ${item.price_yes.toFixed(2)}</span>
                  <span
                    className={clsx(
                      item.stability > 70
                        ? 'text-echelon-green'
                        : item.stability > 40
                        ? 'text-echelon-amber'
                        : 'text-echelon-red'
                    )}
                  >
                    Stability: {item.stability.toFixed(1)}%
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button className="p-2 text-terminal-muted hover:text-echelon-amber transition">
                  <Bell className="w-4 h-4" />
                </button>
                <button className="p-2 text-terminal-muted hover:text-echelon-red transition">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

