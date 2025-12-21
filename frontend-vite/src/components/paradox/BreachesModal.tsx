import { X, AlertTriangle } from 'lucide-react';
import type { Paradox } from '../../types';
import { ParadoxAlert } from './ParadoxAlert';

interface BreachesModalProps {
  paradoxes: Paradox[];
  onClose: () => void;
}

export function BreachesModal({ paradoxes, onClose }: BreachesModalProps) {
  // Sort by urgency (most urgent first)
  const sortedParadoxes = [...paradoxes].sort((a, b) => 
    (a.time_remaining_seconds || 0) - (b.time_remaining_seconds || 0)
  );

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
      onClick={onClose}
    >
      <div 
        className="w-full max-w-4xl max-h-[90vh] bg-terminal-panel border border-terminal-border rounded-lg shadow-2xl flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-terminal-border">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-6 h-6 text-echelon-red animate-pulse" />
            <h2 className="font-display text-2xl text-echelon-red uppercase tracking-wider">
              Active Containment Breaches
            </h2>
            <span className="text-sm text-terminal-muted">
              ({paradoxes.length} total)
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-terminal-muted hover:text-terminal-text hover:bg-terminal-bg rounded transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content - Scrollable */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {sortedParadoxes.map((paradox) => (
            <ParadoxAlert
              key={paradox.id}
              paradox={paradox}
              onExtract={() => console.log('Extract', paradox.id)}
              onAbandon={() => console.log('Abandon', paradox.id)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

