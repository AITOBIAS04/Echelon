import { useUserPositions } from '../../hooks/useUserPositions';
import { DollarSign, PieChart, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';
import { clsx } from 'clsx';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';

export function PositionsPanel() {
  const navigate = useNavigate();
  const { positions, loading, error, totals, refresh } = useUserPositions();
  const [isCollapsed, setIsCollapsed] = useState(true);

  const toggleCollapse = () => setIsCollapsed(!isCollapsed);

  if (loading) {
    return (
      <div className="bg-slate-900/50 border border-slate-700/50 rounded-lg p-3">
        <div className="flex items-center justify-center h-8">
          <span className="text-slate-400 text-xs">Loading positions...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-slate-900/50 border border-slate-700/50 rounded-lg p-3">
        <div className="flex items-center justify-center h-8">
          <button
            onClick={refresh}
            className="text-red-400 text-xs hover:underline"
          >
            Error loading positions. Click to retry
          </button>
        </div>
      </div>
    );
  }

  if (positions.length === 0) {
    return (
      <div className="bg-slate-900/50 border border-slate-700/50 rounded-lg p-3">
        <div className="flex flex-col items-center justify-center h-8 text-slate-400 text-xs">
          <PieChart className="w-4 h-4 mb-1 opacity-50" />
          <span>No active positions</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/50 border border-slate-700/50 rounded-lg overflow-hidden transition-all duration-200">
      {/* Compact Header */}
      <button
        onClick={toggleCollapse}
        className="w-full flex items-center justify-between px-3 py-2 bg-slate-800/50 hover:bg-slate-800/70 transition-colors border-b border-slate-700/50"
      >
        <div className="flex items-center gap-2">
          <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
          <span className="text-xs font-medium text-slate-200">Your Positions</span>
          <span className="text-xs text-slate-500">({positions.length})</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400">
            <span className="text-slate-200 font-mono">${totals.totalValue.toLocaleString()}</span>
            <span className={clsx('ml-2 font-mono', totals.totalPnL >= 0 ? 'text-emerald-400' : 'text-red-400')}>
              {totals.totalPnL >= 0 ? '+' : ''}{totals.totalPnL.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </span>
          {isCollapsed ? (
            <ChevronDown className="w-4 h-4 text-slate-500" />
          ) : (
            <ChevronUp className="w-4 h-4 text-slate-500" />
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
              className="flex-shrink-0 flex items-center gap-1.5 px-2 py-1 bg-slate-800/30 rounded border border-slate-700/30 hover:bg-slate-800/60 hover:border-slate-600/50 transition-all cursor-pointer"
            >
              <span className={clsx(
                'text-[10px] font-medium px-1.5 py-0.5 rounded',
                position.netDirection === 'YES' && 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
                position.netDirection === 'NO' && 'bg-red-500/10 text-red-400 border border-red-500/20',
                position.netDirection === 'NEUTRAL' && 'bg-slate-700/30 text-slate-400 border border-slate-600/30'
              )}>
                {position.netDirection}
              </span>
              <span className="text-[10px] text-slate-300 font-mono max-w-[60px] truncate">
                ${(position.totalNotional / 1000).toFixed(0)}k
              </span>
              <span className={clsx(
                'text-[10px] font-mono',
                position.pnlPercent >= 0 ? 'text-emerald-400' : 'text-red-400'
              )}>
                {position.pnlPercent >= 0 ? '+' : ''}{position.pnlPercent.toFixed(0)}%
              </span>
            </div>
          ))}
          {positions.length > 5 && (
            <span className="flex-shrink-0 text-xs text-slate-500">
              +{positions.length - 5} more
            </span>
          )}
        </div>
      ) : (
        // Expanded Full Table View
        <div className="max-h-48 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
          <table className="w-full text-xs">
            <thead className="bg-slate-800/30 sticky top-0">
              <tr className="border-b border-slate-700/30">
                <th className="text-left p-2.5 text-slate-500 font-medium uppercase text-[10px]">Timeline</th>
                <th className="text-right p-2.5 text-slate-500 font-medium uppercase text-[10px]">Stake</th>
                <th className="text-center p-2.5 text-slate-500 font-medium uppercase text-[10px]">Side</th>
                <th className="text-right p-2.5 text-slate-500 font-medium uppercase text-[10px]">PnL</th>
                <th className="text-right p-2.5 text-slate-500 font-medium uppercase text-[10px]"></th>
              </tr>
            </thead>
            <tbody>
              {positions.map((position) => (
                <tr
                  key={position.timelineId}
                  className="border-b border-slate-700/20 hover:bg-slate-800/40 transition-colors cursor-pointer"
                  onClick={() => navigate(`/timeline/${position.timelineId}`)}
                >
                  <td className="p-2.5">
                    <div className="font-mono text-slate-300 text-[10px] truncate max-w-[120px]" title={position.timelineId}>
                      {position.timelineId}
                    </div>
                  </td>
                  <td className="p-2.5 text-right">
                    <span className="text-slate-200 font-mono">
                      ${position.totalNotional.toLocaleString()}
                    </span>
                  </td>
                  <td className="p-2.5 text-center">
                    <span className={clsx(
                      'px-2 py-0.5 rounded text-[10px] font-medium',
                      position.netDirection === 'YES' && 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
                      position.netDirection === 'NO' && 'bg-red-500/10 text-red-400 border border-red-500/20',
                      position.netDirection === 'NEUTRAL' && 'bg-slate-700/30 text-slate-400 border border-slate-600/30'
                    )}>
                      {position.netDirection}
                    </span>
                  </td>
                  <td className="p-2.5 text-right">
                    <span className={clsx(
                      'font-mono font-medium',
                      position.pnlPercent >= 0 ? 'text-emerald-400' : 'text-red-400'
                    )}>
                      {position.pnlPercent >= 0 ? '+' : ''}{position.pnlPercent.toFixed(1)}%
                    </span>
                  </td>
                  <td className="p-2.5 text-right">
                    <ExternalLink className="w-3 h-3 text-slate-500 hover:text-blue-400 ml-auto" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-slate-800/30 border-t border-slate-700/30">
        <span className="text-[10px] text-slate-500">
          <span className="text-slate-400">{totals.winningPositions}</span> / <span className="text-red-400">{totals.losingPositions}</span>
        </span>
        <button
          onClick={() => navigate('/fieldkit')}
          className="text-[10px] text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors"
        >
          Full portfolio
          <ExternalLink className="w-2.5 h-2.5" />
        </button>
      </div>
    </div>
  );
}

export default PositionsPanel;
