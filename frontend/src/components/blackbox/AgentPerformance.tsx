import { clsx } from 'clsx';

const mockPerformance = [
  { name: 'MEGALODON', archetype: 'SHARK', pnl: 4520, trades: 156, winRate: 0.67 },
  { name: 'CARDINAL', archetype: 'SPY', pnl: 1230, trades: 89, winRate: 0.58 },
  { name: 'ENVOY', archetype: 'DIPLOMAT', pnl: 890, trades: 45, winRate: 0.72 },
  { name: 'VIPER', archetype: 'SABOTEUR', pnl: -340, trades: 67, winRate: 0.42 },
  { name: 'ORACLE', archetype: 'SPY', pnl: 2100, trades: 112, winRate: 0.61 },
];

export function AgentPerformance() {
  return (
    <div className="h-full overflow-y-auto">
      <div className="space-y-3">
        {mockPerformance
          .sort((a, b) => b.pnl - a.pnl)
          .map((agent, index) => (
            <div key={agent.name} className="terminal-panel p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-2xl font-bold text-terminal-muted">#{index + 1}</span>
                  <div>
                    <h3 className="font-bold text-terminal-text">{agent.name}</h3>
                    <span className="text-xs text-terminal-muted">{agent.archetype}</span>
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  <div className="text-center">
                    <div className="text-xs text-terminal-muted">Trades</div>
                    <div className="font-mono">{agent.trades}</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xs text-terminal-muted">Win Rate</div>
                    <div className="font-mono">{(agent.winRate * 100).toFixed(0)}%</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xs text-terminal-muted">P&L</div>
                    <div
                      className={clsx(
                        'font-mono font-bold',
                        agent.pnl >= 0 ? 'text-echelon-green' : 'text-echelon-red'
                      )}
                    >
                      {agent.pnl >= 0 ? '+' : ''}${agent.pnl.toLocaleString()}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
      </div>
    </div>
  );
}

