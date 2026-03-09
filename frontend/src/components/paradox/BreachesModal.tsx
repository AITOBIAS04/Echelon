import { X, AlertTriangle } from 'lucide-react';
import { useEffect } from 'react';
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

  // Add escape key handler to close modal
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  return (
    <div 
      className="fixed inset-0 z-[300] flex items-center justify-center bg-[color:oklch(0.205_0.015_265_/_0.42)] px-4 backdrop-blur-[2px]"
      onClick={onClose}
      style={{ pointerEvents: 'auto' }}
    >
      <div 
        className="flex max-h-[90vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl border border-[var(--e-border-primary)] bg-[var(--e-bg-elevated)] shadow-[0_20px_60px_oklch(0.2_0.01_265_/_0.18)]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[var(--e-border-primary)] px-6 py-5">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-6 w-6 animate-pulse text-[var(--e-red-600)]" />
            <h2 className="text-2xl font-semibold tracking-[-0.03em] text-[var(--e-text-primary)]">
              Active Containment Breaches
            </h2>
            <span className="rounded-full border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] px-2.5 py-1 font-mono text-[11px] font-semibold text-[var(--e-red-600)]">
              ({paradoxes.length} total)
            </span>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-[var(--e-text-muted)] transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content - Scrollable */}
        <div className="flex-1 space-y-4 overflow-y-auto bg-[var(--e-bg-app)] px-6 py-6">
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
