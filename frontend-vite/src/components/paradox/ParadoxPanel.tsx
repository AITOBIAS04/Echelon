import { AlertTriangle, Clock, Zap, Skull } from 'lucide-react';
import { useParadoxes } from '../../hooks/useParadoxes';
import { ParadoxAlert } from './ParadoxAlert';
import type { Paradox } from '../../types';

export function ParadoxPanel() {
  const { data: paradoxData, isLoading } = useParadoxes();
  const paradoxes = paradoxData?.paradoxes || [];

  return (
    <div className="h-full flex flex-col gap-4 p-4" data-panel="paradox" data-testid="paradox-panel">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <AlertTriangle className="w-6 h-6 text-echelon-red" />
          <h1 className="font-display text-2xl text-echelon-red uppercase tracking-wider">
            Paradox Containment
          </h1>
        </div>
        <div className="text-sm text-terminal-muted">
          {paradoxes.length} active breach{paradoxes.length !== 1 ? 'es' : ''}
        </div>
      </div>

      {/* Active Paradoxes */}
      {isLoading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-terminal-muted">Loading paradoxes...</div>
        </div>
      ) : paradoxes.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center gap-4 text-terminal-muted">
          <AlertTriangle className="w-16 h-16 text-echelon-green opacity-50" />
          <div className="text-lg">All timelines stable</div>
          <div className="text-sm text-center max-w-md">
            No active paradoxes detected. The counterfactual layer is operating within normal parameters.
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto space-y-4">
          {paradoxes.map((paradox) => (
            <ParadoxAlert
              key={paradox.id}
              paradox={paradox}
              onExtract={() => console.log('Extract paradox', paradox.id)}
              onAbandon={() => console.log('Abandon timeline', paradox.timeline_id)}
            />
          ))}
        </div>
      )}

      {/* Stats Footer */}
      <div className="terminal-panel p-4 grid grid-cols-3 gap-4 text-center">
        <div>
          <div className="text-xs text-terminal-muted mb-1">Total Detected</div>
          <div className="text-lg font-mono text-echelon-purple">
            {paradoxData?.total_active || 0}
          </div>
        </div>
        <div>
          <div className="text-xs text-terminal-muted mb-1">Extracting</div>
          <div className="text-lg font-mono text-echelon-amber">
            {paradoxes.filter(p => p.status === 'EXTRACTING').length}
          </div>
        </div>
        <div>
          <div className="text-xs text-terminal-muted mb-1">Resolved</div>
          <div className="text-lg font-mono text-echelon-green">
            {paradoxes.filter(p => p.status === 'RESOLVED').length}
          </div>
        </div>
      </div>
    </div>
  );
}

