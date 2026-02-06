import { useState, useEffect } from 'react';
import { Clock, Zap } from 'lucide-react';

/**
 * ForkCountdownRibbon Props
 */
export interface ForkCountdownRibbonProps {
  /** Next upcoming fork (optional) */
  nextFork?: {
    forkId: string;
    question: string;
    etaSeconds: number;
  };
  /** Currently active fork (optional) */
  activeFork?: {
    forkId: string;
    question: string;
    remainingSeconds: number;
  };
}

/**
 * Format seconds to MM:SS or HH:MM:SS
 */
function formatTime(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

/**
 * ForkCountdownRibbon Component
 * 
 * Thin banner displaying active fork countdown or next fork ETA.
 * Renders above the Health Metrics panel.
 */
export function ForkCountdownRibbon({
  nextFork,
  activeFork,
}: ForkCountdownRibbonProps) {
  const [currentTime, setCurrentTime] = useState(Date.now());
  const [startTime] = useState(Date.now());

  // Update time every second for countdown
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(Date.now());
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // Calculate remaining/eta seconds based on elapsed time
  const getRemainingSeconds = (): number | null => {
    if (activeFork) {
      // For active fork, decrease remainingSeconds based on elapsed time
      const elapsed = Math.floor((currentTime - startTime) / 1000);
      return Math.max(0, activeFork.remainingSeconds - elapsed);
    }
    if (nextFork) {
      // For next fork, decrease ETA based on elapsed time
      const elapsed = Math.floor((currentTime - startTime) / 1000);
      return Math.max(0, nextFork.etaSeconds - elapsed);
    }
    return null;
  };

  const remainingSeconds = getRemainingSeconds();

  return (
    <div className="w-full">
      {activeFork ? (
        <div className="bg-echelon-red/20 border border-echelon-red rounded-lg px-4 py-2 flex items-center gap-3">
          <Zap className="w-4 h-4 text-echelon-red flex-shrink-0 animate-pulse" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-echelon-red uppercase tracking-wide">
                Fork Live
              </span>
              <span className="text-xs text-terminal-text font-mono">
                {remainingSeconds !== null ? formatTime(remainingSeconds) : '--:--'}
              </span>
            </div>
            <p className="text-xs text-terminal-text-muted truncate mt-0.5">
              {activeFork.question.length > 60
                ? `${activeFork.question.substring(0, 60)}...`
                : activeFork.question}
            </p>
          </div>
        </div>
      ) : nextFork ? (
        <div className="bg-echelon-cyan/20 border border-echelon-cyan rounded-lg px-4 py-2 flex items-center gap-3">
          <Clock className="w-4 h-4 text-echelon-cyan flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-echelon-cyan uppercase tracking-wide">
                Next Fork
              </span>
              <span className="text-xs text-terminal-text font-mono">
                {remainingSeconds !== null ? formatTime(remainingSeconds) : '--:--'}
              </span>
            </div>
            <p className="text-xs text-terminal-text-muted truncate mt-0.5">
              {nextFork.question.length > 60
                ? `${nextFork.question.substring(0, 60)}...`
                : nextFork.question}
            </p>
          </div>
        </div>
      ) : (
        <div className="bg-terminal-panel border border-terminal-border rounded-lg px-4 py-2 flex items-center gap-3">
          <Clock className="w-4 h-4 text-terminal-text-muted flex-shrink-0" />
          <span className="text-xs text-terminal-text-muted">
            No upcoming forks
          </span>
        </div>
      )}
    </div>
  );
}
