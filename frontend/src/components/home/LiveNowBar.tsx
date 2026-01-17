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
    <div className="bg-[#111111] border border-[#1A1A1A] rounded-lg p-3 md:p-4 mb-4">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
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
            className="flex items-center gap-2 px-3 py-2 bg-terminal-bg border border-terminal-border rounded hover:border-[#00D4FF] hover:text-[#00D4FF] transition group flex-shrink-0"
          >
            <GitBranch className="w-4 h-4 text-[#00D4FF] group-hover:text-[#00D4FF]" />
            <div className="flex flex-col items-start">
              <span className="text-xs text-terminal-muted">Forks Live</span>
              <span className="text-sm font-mono font-bold text-terminal-text group-hover:text-[#00D4FF]">
                {liveNow.forksLive}
              </span>
            </div>
          </button>

          {/* Paradox Active */}
          <button
            onClick={handleParadoxActive}
            className="flex items-center gap-2 px-3 py-2 bg-terminal-bg border border-terminal-border rounded hover:border-[#FF3B3B] hover:text-[#FF3B3B] transition group flex-shrink-0"
          >
            <Zap className="w-4 h-4 text-[#FF3B3B] group-hover:text-[#FF3B3B]" />
            <div className="flex flex-col items-start">
              <span className="text-xs text-terminal-muted">Paradox Active</span>
              <span className="text-sm font-mono font-bold text-terminal-text group-hover:text-[#FF3B3B]">
                {liveNow.paradoxActive}
              </span>
            </div>
          </button>

          {/* Breaches */}
          <button
            onClick={handleBreaches}
            className="flex items-center gap-2 px-3 py-2 bg-terminal-bg border border-terminal-border rounded hover:border-amber-500 hover:text-amber-500 transition group flex-shrink-0"
          >
            <AlertTriangle className="w-4 h-4 text-amber-500 group-hover:text-amber-500" />
            <div className="flex flex-col items-start">
              <span className="text-xs text-terminal-muted">Breaches</span>
              <span className="text-sm font-mono font-bold text-terminal-text group-hover:text-amber-500">
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
