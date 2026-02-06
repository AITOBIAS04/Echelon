import { History, Play, SkipBack, SkipForward } from 'lucide-react';

export function HistoricalReplay() {
  return (
    <div className="h-full flex flex-col items-center justify-center text-center p-8">
      <div className="w-16 h-16 rounded-full bg-terminal-panel flex items-center justify-center mb-4">
        <History className="w-8 h-8 text-echelon-amber" />
      </div>
      <h3 className="text-lg font-medium text-terminal-text mb-2">Historical Replay</h3>
      <p className="text-sm text-terminal-text-muted mb-6 max-w-md">
        Replay past events to analyse what-if scenarios. Study agent decisions,
        market movements, and paradox resolutions.
      </p>
      <div className="flex items-center gap-2">
        <button className="p-2 bg-terminal-panel border border-terminal-border rounded hover:border-echelon-cyan transition">
          <SkipBack className="w-4 h-4" />
        </button>
        <button className="p-3 bg-echelon-amber/20 border border-echelon-amber text-echelon-amber rounded hover:bg-echelon-amber/30 transition">
          <Play className="w-5 h-5" />
        </button>
        <button className="p-2 bg-terminal-panel border border-terminal-border rounded hover:border-echelon-cyan transition">
          <SkipForward className="w-4 h-4" />
        </button>
      </div>
      <p className="text-xs text-terminal-text-muted mt-4">Coming in Phase 2</p>
    </div>
  );
}

