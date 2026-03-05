/**
 * TradeHistory — Agent trade log with P&L per trade.
 * Derives from agent trades_count and win_rate (no per-trade endpoint).
 */

import type { Agent } from '../../types/agents';

interface TradeHistoryProps {
  agent: Agent;
}

export function TradeHistory({ agent }: TradeHistoryProps) {
  if (agent.trades_count === 0) {
    return (
      <div className="bg-terminal-surface border border-terminal-border rounded-xl p-6 text-center">
        <div className="text-xs text-terminal-text-muted">No trades recorded yet.</div>
      </div>
    );
  }

  const estimatedWins = Math.round(agent.trades_count * agent.win_rate);
  const estimatedLosses = agent.trades_count - estimatedWins;
  const avgPnlPerTrade = agent.trades_count > 0 ? agent.total_pnl_usd / agent.trades_count : 0;

  return (
    <div className="bg-terminal-surface border border-terminal-border rounded-xl p-4">
      <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wider mb-3">
        Trade History
      </h3>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
        <div className="bg-terminal-panel rounded-lg p-3 text-center">
          <div className="text-lg font-mono text-terminal-text">{agent.trades_count}</div>
          <div className="text-[10px] text-terminal-text-muted uppercase">Total Trades</div>
        </div>
        <div className="bg-terminal-panel rounded-lg p-3 text-center">
          <div className="text-lg font-mono text-emerald-400">{estimatedWins}</div>
          <div className="text-[10px] text-terminal-text-muted uppercase">Wins</div>
        </div>
        <div className="bg-terminal-panel rounded-lg p-3 text-center">
          <div className="text-lg font-mono text-rose-400">{estimatedLosses}</div>
          <div className="text-[10px] text-terminal-text-muted uppercase">Losses</div>
        </div>
        <div className="bg-terminal-panel rounded-lg p-3 text-center">
          <div className={`text-lg font-mono ${avgPnlPerTrade >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            {avgPnlPerTrade >= 0 ? '+' : ''}${avgPnlPerTrade.toFixed(2)}
          </div>
          <div className="text-[10px] text-terminal-text-muted uppercase">Avg P&L/Trade</div>
        </div>
      </div>

      {/* Win/Loss bar */}
      <div className="h-2 rounded-full overflow-hidden flex bg-terminal-panel">
        <div
          className="bg-emerald-500 transition-all duration-500"
          style={{ width: `${agent.win_rate * 100}%` }}
        />
        <div
          className="bg-rose-500 transition-all duration-500"
          style={{ width: `${(1 - agent.win_rate) * 100}%` }}
        />
      </div>
      <div className="flex justify-between text-[10px] text-terminal-text-muted mt-1">
        <span>{(agent.win_rate * 100).toFixed(1)}% win rate</span>
        <span>{((1 - agent.win_rate) * 100).toFixed(1)}% loss rate</span>
      </div>
    </div>
  );
}
