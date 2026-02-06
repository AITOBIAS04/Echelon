import { useUserPositions } from '../../hooks/useUserPositions';
import { DollarSign, PieChart, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';
import { clsx } from 'clsx';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { useDemoEnabled, useDemoPositions, useDemoOutcome } from '../../demo/hooks';

function DemoPositionsPanel() {
  const positions = useDemoPositions();

  const rows = positions.map((p) => {
    const snap = useDemoOutcome(p.marketId, p.outcomeId, { price: 0.5 });
    const markPerShare = p.outcomeId === 'YES' ? snap.price : 1 - snap.price;
    const markValue = p.shares * markPerShare;
    const pnl = markValue - p.stake;
    return { p, snap, markPerShare, pnl };
  });

  const totalPnl = rows.reduce((acc, r) => acc + r.pnl, 0);

  return (
    <div className="bg-terminal-panel border border-status-paradox/20 rounded-lg overflow-hidden">
      <div className="px-3 py-2 border-b border-status-paradox/20 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <DollarSign className="w-3.5 h-3.5 text-status-paradox" />
          <span className="text-xs font-medium text-terminal-text">Demo Positions</span>
          <span className="text-xs text-terminal-text-muted">({positions.length})</span>
        </div>
        <div className="text-xs text-terminal-text-secondary">
          <span className="text-terminal-text font-mono">{'\u00A3'}{rows.reduce((acc, r) => acc + r.p.stake, 0).toFixed(0)}</span>
          <span className={clsx('ml-2 font-mono', totalPnl >= 0 ? 'text-echelon-green' : 'text-echelon-red')}>
            {totalPnl >= 0 ? '+' : ''}{'\u00A3'}{totalPnl.toFixed(2)}
          </span>
        </div>
      </div>

      <div className="p-3 space-y-2 max-h-48 overflow-y-auto">
        {rows.map(({ p, pnl, markPerShare }) => (
          <div
            key={p.id}
            className="rounded-lg border border-status-paradox/20 bg-terminal-bg/70 px-3 py-2"
          >
            <div className="flex items-center justify-between">
              <div className="text-sm text-terminal-text">{p.marketTitle}</div>
              <div className={clsx('text-sm tabular-nums', pnl >= 0 ? 'text-echelon-green' : 'text-echelon-red')}>
                {'\u00A3'}{pnl.toFixed(2)}
              </div>
            </div>

            <div className="mt-1 flex items-center justify-between text-xs text-terminal-text-secondary">
              <div className="tabular-nums">
                {p.outcomeId} Entry {(p.entryPrice * 100).toFixed(1)}% Mark {(markPerShare * 100).toFixed(1)}%
              </div>
              <div className="tabular-nums">Stake {'\u00A3'}{p.stake.toFixed(2)}</div>
            </div>
          </div>
        ))}

        {rows.length === 0 ? (
          <div className="rounded-lg border border-status-paradox/15 bg-terminal-bg/40 px-3 py-3 text-xs text-terminal-text-muted text-center">
            No demo positions yet. Place a bet in demo mode!
          </div>
        ) : null}
      </div>
    </div>
  );
}

export function PositionsPanel() {
  const demoEnabled = useDemoEnabled();
  if (demoEnabled) return <DemoPositionsPanel />;

  const navigate = useNavigate();
  const { positions, loading, error, totals, refresh } = useUserPositions();
  const [isCollapsed, setIsCollapsed] = useState(true);

  const toggleCollapse = () => setIsCollapsed(!isCollapsed);

  if (loading) {
    return (
      <div className="bg-terminal-panel border border-terminal-border rounded-lg p-3">
        <div className="flex items-center justify-center h-8">
          <span className="text-terminal-text-secondary text-xs">Loading positions...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-terminal-panel border border-terminal-border rounded-lg p-3">
        <div className="flex items-center justify-center h-8">
          <button
            onClick={refresh}
            className="text-echelon-red text-xs hover:underline"
          >
            Error loading positions. Click to retry
          </button>
        </div>
      </div>
    );
  }

  if (positions.length === 0) {
    return (
      <div className="bg-terminal-panel border border-terminal-border rounded-lg p-3">
        <div className="flex flex-col items-center justify-center h-8 text-terminal-text-secondary text-xs">
          <PieChart className="w-4 h-4 mb-1 opacity-50" />
          <span>No active positions</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-terminal-panel border border-terminal-border rounded-lg overflow-hidden transition-all duration-200">
      {/* Compact Header */}
      <button
        onClick={toggleCollapse}
        className="w-full flex items-center justify-between px-3 py-2 bg-terminal-header hover:bg-terminal-hover transition-colors border-b border-terminal-border"
      >
        <div className="flex items-center gap-2">
          <DollarSign className="w-3.5 h-3.5 text-echelon-green" />
          <span className="text-xs font-medium text-terminal-text">Your Positions</span>
          <span className="text-xs text-terminal-text-muted">({positions.length})</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-terminal-text-secondary">
            <span className="text-terminal-text font-mono">${totals.totalValue.toLocaleString()}</span>
            <span className={clsx('ml-2 font-mono', totals.totalPnL >= 0 ? 'text-echelon-green' : 'text-echelon-red')}>
              {totals.totalPnL >= 0 ? '+' : ''}{totals.totalPnL.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </span>
          {isCollapsed ? (
            <ChevronDown className="w-4 h-4 text-terminal-text-muted" />
          ) : (
            <ChevronUp className="w-4 h-4 text-terminal-text-muted" />
          )}
        </div>
      </button>

      {/* Collapsible Content */}
      {isCollapsed ? (
        // Compact Summary View - Top 5 positions as chips
        <div className="px-3 py-2 flex items-center gap-2 overflow-x-auto scrollbar-thin scrollbar-transparent">
          {positions.slice(0, 5).map((position) => (
            <div
              key={position.timelineId}
              onClick={() => navigate(`/timeline/${position.timelineId}`)}
              className="flex-shrink-0 flex items-center gap-1.5 px-2 py-1 bg-terminal-card rounded border border-terminal-border hover:bg-terminal-hover hover:border-terminal-border-light transition-all cursor-pointer"
            >
              <span className={clsx(
                'text-[10px] font-medium px-1.5 py-0.5 rounded',
                position.netDirection === 'YES' && 'bg-echelon-green/10 text-echelon-green border border-echelon-green/20',
                position.netDirection === 'NO' && 'bg-echelon-red/10 text-echelon-red border border-echelon-red/20',
                position.netDirection === 'NEUTRAL' && 'bg-terminal-card text-terminal-text-secondary border border-terminal-border'
              )}>
                {position.netDirection}
              </span>
              <span className="text-[10px] text-terminal-text font-mono max-w-[60px] truncate">
                ${(position.totalNotional / 1000).toFixed(0)}k
              </span>
              <span className={clsx(
                'text-[10px] font-mono',
                position.pnlPercent >= 0 ? 'text-echelon-green' : 'text-echelon-red'
              )}>
                {position.pnlPercent >= 0 ? '+' : ''}{position.pnlPercent.toFixed(0)}%
              </span>
            </div>
          ))}
          {positions.length > 5 && (
            <span className="flex-shrink-0 text-xs text-terminal-text-muted">
              +{positions.length - 5} more
            </span>
          )}
        </div>
      ) : (
        // Expanded Full Table View
        <div className="max-h-48 overflow-y-auto scrollbar-thin">
          <table className="terminal-table">
            <thead className="sticky top-0">
              <tr>
                <th className="text-left">Timeline</th>
                <th className="text-right">Stake</th>
                <th className="text-center">Side</th>
                <th className="text-right">PnL</th>
                <th className="text-right"></th>
              </tr>
            </thead>
            <tbody>
              {positions.map((position) => (
                <tr
                  key={position.timelineId}
                  className="cursor-pointer"
                  onClick={() => navigate(`/timeline/${position.timelineId}`)}
                >
                  <td>
                    <div className="font-mono text-terminal-text text-[10px] truncate max-w-[120px]" title={position.timelineId}>
                      {position.timelineId}
                    </div>
                  </td>
                  <td className="text-right">
                    <span className="text-terminal-text font-mono">
                      ${position.totalNotional.toLocaleString()}
                    </span>
                  </td>
                  <td className="text-center">
                    <span className={clsx(
                      'px-2 py-0.5 rounded text-[10px] font-medium',
                      position.netDirection === 'YES' && 'bg-echelon-green/10 text-echelon-green border border-echelon-green/20',
                      position.netDirection === 'NO' && 'bg-echelon-red/10 text-echelon-red border border-echelon-red/20',
                      position.netDirection === 'NEUTRAL' && 'bg-terminal-card text-terminal-text-secondary border border-terminal-border'
                    )}>
                      {position.netDirection}
                    </span>
                  </td>
                  <td className="text-right">
                    <span className={clsx(
                      'font-mono font-medium',
                      position.pnlPercent >= 0 ? 'text-echelon-green' : 'text-echelon-red'
                    )}>
                      {position.pnlPercent >= 0 ? '+' : ''}{position.pnlPercent.toFixed(1)}%
                    </span>
                  </td>
                  <td className="text-right">
                    <ExternalLink className="w-3 h-3 text-terminal-text-muted hover:text-echelon-blue ml-auto" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-terminal-header border-t border-terminal-border">
        <span className="text-[10px] text-terminal-text-muted">
          <span className="text-terminal-text-secondary">{totals.winningPositions}</span> / <span className="text-echelon-red">{totals.losingPositions}</span>
        </span>
        <button
          onClick={() => navigate('/fieldkit')}
          className="text-[10px] text-echelon-blue hover:text-echelon-blue/80 flex items-center gap-1 transition-colors"
        >
          Full portfolio
          <ExternalLink className="w-2.5 h-2.5" />
        </button>
      </div>
    </div>
  );
}

export default PositionsPanel;
