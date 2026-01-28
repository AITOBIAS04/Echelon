import { clsx } from 'clsx';

const mockPerformance = [
  { name: 'MEGALODON', archetype: 'SHARK', pnl: 4520, trades: 156, winRate: 0.67 },
  { name: 'CARDINAL', archetype: 'SPY', pnl: 1230, trades: 89, winRate: 0.58 },
  { name: 'ENVOY', archetype: 'DIPLOMAT', pnl: 890, trades: 45, winRate: 0.72 },
  { name: 'VIPER', archetype: 'SABOTEUR', pnl: -340, trades: 67, winRate: 0.42 },
  { name: 'ORACLE', archetype: 'SPY', pnl: 2100, trades: 112, winRate: 0.61 },
];

export function AgentPerformance() {
  const sorted = [...mockPerformance].sort((a, b) => b.pnl - a.pnl);

  return (
    <div className="h-full overflow-y-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-terminal-border bg-terminal-bg">
            <th className="text-left px-4 py-2 font-semibold text-terminal-text-muted uppercase tracking-wider text-[10px] w-12">#</th>
            <th className="text-left px-4 py-2 font-semibold text-terminal-text-muted uppercase tracking-wider text-[10px]">Agent</th>
            <th className="text-right px-4 py-2 font-semibold text-terminal-text-muted uppercase tracking-wider text-[10px] w-24">P&amp;L</th>
            <th className="text-right px-4 py-2 font-semibold text-terminal-text-muted uppercase tracking-wider text-[10px] w-20">VOL</th>
            <th className="text-right px-4 py-2 font-semibold text-terminal-text-muted uppercase tracking-wider text-[10px] w-20">Win %</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((agent, index) => (
            <tr key={agent.name} className="border-b border-terminal-border/50 hover:bg-terminal-bg/50 transition-colors">
              <td className="px-4 py-2.5 font-mono text-terminal-text-muted">{index + 1}</td>
              <td className="px-4 py-2.5">
                <span className="font-bold text-terminal-text">{agent.name}</span>
                <span className="ml-2 text-terminal-text-muted">{agent.archetype}</span>
              </td>
              <td className={clsx(
                'px-4 py-2.5 font-mono font-bold text-right',
                agent.pnl >= 0 ? 'text-status-success' : 'text-status-danger'
              )}>
                {agent.pnl >= 0 ? '+' : ''}${agent.pnl.toLocaleString()}
              </td>
              <td className="px-4 py-2.5 font-mono text-terminal-text-secondary text-right">
                {agent.trades}
              </td>
              <td className="px-4 py-2.5 font-mono text-terminal-text-secondary text-right">
                {(agent.winRate * 100).toFixed(0)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
