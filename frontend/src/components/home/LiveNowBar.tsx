import { useNavigate } from 'react-router-dom';
import { GitBranch, Zap, AlertTriangle } from 'lucide-react';
import type { LiveNowSummary } from '../../types/opsBoard';

/**
 * LiveNowBar Props
 */
export interface LiveNowBarProps {
  /** Live now summary data */
  liveNow: LiveNowSummary;
}

/**
 * LiveNowBar Component
 * 
 * Displays live metrics as clickable pills that navigate to relevant pages.
 */
export function LiveNowBar({ liveNow }: LiveNowBarProps) {
  const navigate = useNavigate();

  const handleForksLive = () => {
    navigate('/blackbox?tab=live_tape&filter=fork_live');
  };

  const handleParadoxActive = () => {
    navigate('/breaches');
  };

  const handleBreaches = () => {
    navigate('/breaches');
  };

  return (
    <div className="bg-slate-900 border border-[#1A1A1A] rounded-lg p-3 md:p-4 mb-4">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-2 h-2 bg-status-success rounded-full animate-pulse" />
        <span className="text-xs font-semibold text-terminal-text uppercase tracking-wide">
          Live Now
        </span>
      </div>
      {/* Mobile: Horizontal scroll, Desktop: Single line flex */}
      <div className="overflow-x-auto scrollbar-hide md:overflow-x-visible">
        <div className="flex items-center gap-3 md:flex-wrap min-w-max md:min-w-0">
          {/* Forks Live */}
          <button
            onClick={handleForksLive}
            className="flex items-center gap-2 px-3 py-2 bg-terminal-bg border border-terminal-border rounded hover:border-status-info hover:text-status-info transition group flex-shrink-0"
          >
            <GitBranch className="w-4 h-4 text-status-info group-hover:text-status-info" />
            <div className="flex flex-col items-start">
              <span className="text-xs text-terminal-text-secondary">Forks Live</span>
              <span className="text-sm font-mono font-bold text-terminal-text group-hover:text-status-info">
                {liveNow.forksLive}
              </span>
            </div>
          </button>

          {/* Paradox Active */}
          <button
            onClick={handleParadoxActive}
            className="flex items-center gap-2 px-3 py-2 bg-terminal-bg border border-terminal-border rounded hover:border-status-danger hover:text-status-danger transition group flex-shrink-0"
          >
            <Zap className="w-4 h-4 text-status-danger group-hover:text-status-danger" />
            <div className="flex flex-col items-start">
              <span className="text-xs text-terminal-text-secondary">Paradox Active</span>
              <span className="text-sm font-mono font-bold text-terminal-text group-hover:text-status-danger">
                {liveNow.paradoxActive}
              </span>
            </div>
          </button>

          {/* Breaches */}
          <button
            onClick={handleBreaches}
            className="flex items-center gap-2 px-3 py-2 bg-terminal-bg border border-terminal-border rounded hover:border-status-warning hover:text-status-warning transition group flex-shrink-0"
          >
            <AlertTriangle className="w-4 h-4 text-status-warning group-hover:text-status-warning" />
            <div className="flex flex-col items-start">
              <span className="text-xs text-terminal-text-secondary">Breaches</span>
              <span className="text-sm font-mono font-bold text-terminal-text group-hover:text-status-warning">
                {liveNow.breaches}
              </span>
            </div>
          </button>
        </div>
      </div>
      {/* Hide scrollbar for webkit browsers */}
      <style>{`
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
      `}</style>
    </div>
  );
}
