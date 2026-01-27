import { useState, useEffect, useRef } from 'react';
import { X, BarChart3, Clock } from 'lucide-react';
import { clsx } from 'clsx';
import type { Market } from '../../types/marketplace';

interface CompareSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  markets?: Market[];
}

// Mock comparison theatres
const comparisonTheatres = [
  { id: 'orb_salvage_f7', name: 'ORB_SALVAGE_F7', price: 3.82, change: '+12.4%', stability: 72, gap: 12, volume: '$2.4M', probability: 68, forkIn: '45s' },
  { id: 'ven_oil_tanker', name: 'VEN_OIL_TANKER', price: 2.15, change: '-3.2%', stability: 45, gap: 28, volume: '$890K', probability: 52, forkIn: '2m' },
  { id: 'fed_rate', name: 'FED_RATE_DECISION', price: 3.45, change: '+8.7%', stability: 58, gap: 18, volume: '$1.2M', probability: 61, forkIn: '30s' },
  { id: 'taiwan_strait', name: 'TAIWAN_STRAIT', price: 4.20, change: '-1.5%', stability: 33, gap: 42, volume: '$3.1M', probability: 74, forkIn: '15s' },
  { id: 'putin_health', name: 'PUTIN_HEALTH_RUMORS', price: 1.85, change: '+22.1%', stability: 28, gap: 55, volume: '$567K', probability: 41, forkIn: '5m' },
  { id: 'spacex_launch', name: 'SPACEX_LAUNCH', price: 2.90, change: '+5.3%', stability: 81, gap: 8, volume: '$1.8M', probability: 55, forkIn: '1h' },
];

type ComparisonTheatre = typeof comparisonTheatres[0];

/**
 * Generate random mini chart bars
 */
function generateMiniBars(): string {
  let bars = '';
  for (let i = 0; i < 10; i++) {
    const height = 20 + Math.random() * 60;
    bars += `<div class="mini-bar" style="height: ${height}%;"></div>`;
  }
  return bars;
}

/**
 * Get change color class
 */
function getChangeClass(change: string): string {
  return change.includes('+') ? 'text-status-success' : 'text-status-danger';
}

/**
 * Get stability color class
 */
function getStabilityColorClass(stability: number): string {
  if (stability > 60) return 'text-status-success';
  if (stability > 40) return 'text-status-warning';
  return 'text-status-danger';
}

/**
 * Get gap color class
 */
function getGapColorClass(gap: number): string {
  if (gap > 40) return 'text-status-danger';
  if (gap > 25) return 'text-status-warning';
  return 'text-status-success';
}

/**
 * CompareSidebar Component
 * 
 * Slide-out panel for comparing multiple markets:
 * - 4 comparison slots
 * - Mini charts for each slot
 * - Side-by-side metrics comparison
 * - Visual comparison bars
 */
export function CompareSidebar({ isOpen, onClose }: CompareSidebarProps) {
  const [compareSlots, setCompareSlots] = useState<Record<number, ComparisonTheatre | null>>({
    1: null,
    2: null,
    3: null,
    4: null,
  });
  const sidebarRef = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (sidebarRef.current && !sidebarRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  const addTheatreToSlot = (theatreId: string, slotId: number) => {
    const theatre = comparisonTheatres.find(t => t.id === theatreId);
    if (theatre) {
      setCompareSlots(prev => ({ ...prev, [slotId]: theatre }));
    }
  };

  const removeFromSlot = (slotId: number) => {
    setCompareSlots(prev => ({ ...prev, [slotId]: null }));
  };

  const clearAllSlots = () => {
    setCompareSlots({ 1: null, 2: null, 3: null, 4: null });
  };

  const selectedTheatres = Object.values(compareSlots).filter((t): t is ComparisonTheatre => t !== null);

  // Calculate comparison bar widths
  const maxStability = Math.max(...selectedTheatres.map(t => t.stability), 1);
  const maxGap = Math.max(...selectedTheatres.map(t => t.gap), 1);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-[9998]"
        onClick={onClose}
      />

      {/* Sidebar */}
      <div
        ref={sidebarRef}
        className="fixed top-0 right-0 h-full w-[480px] max-w-[90vw] bg-terminal-panel border-l border-terminal-border shadow-2xl z-[9999] flex flex-col transition-transform duration-300"
        style={{ transform: isOpen ? 'translateX(0)' : 'translateX(100%)' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-terminal-border bg-terminal-bg/50">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-status-info" />
            <span className="text-sm font-semibold text-terminal-text">Compare Theatres</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-terminal-muted hover:text-terminal-text transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Comparison Grid */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="grid grid-cols-2 gap-3">
            {[1, 2, 3, 4].map(slotId => {
              const theatre = compareSlots[slotId];

              return (
                <div
                  key={slotId}
                  className={clsx(
                    'relative rounded-lg border transition-all',
                    theatre
                      ? 'bg-terminal-bg border-terminal-border'
                      : 'bg-terminal-card/50 border-terminal-border/50 border-dashed'
                  )}
                >
                  {theatre ? (
                    <>
                      {/* Theatre Name */}
                      <div className="flex items-center justify-between p-3 border-b border-terminal-border">
                        <span className="text-xs font-bold font-mono text-terminal-text">
                          {theatre.name}
                        </span>
                        <button
                          onClick={() => removeFromSlot(slotId)}
                          className="p-0.5 text-terminal-muted hover:text-terminal-text transition-colors"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>

                      {/* Mini Chart */}
                      <div
                        className="h-12 flex items-end gap-0.5 p-2"
                        dangerouslySetInnerHTML={{ __html: generateMiniBars() }}
                      />

                      {/* Metrics */}
                      <div className="p-3 space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-[10px] text-terminal-muted uppercase">Price</span>
                          <span className="text-xs font-mono font-semibold text-terminal-text">
                            ${theatre.price.toFixed(2)}
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-[10px] text-terminal-muted uppercase">24h</span>
                          <span className={clsx('text-xs font-mono font-semibold', getChangeClass(theatre.change))}>
                            {theatre.change}
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-[10px] text-terminal-muted uppercase">Stability</span>
                          <span className={clsx('text-xs font-mono font-semibold', getStabilityColorClass(theatre.stability))}>
                            {theatre.stability}%
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-[10px] text-terminal-muted uppercase">Logic Gap</span>
                          <span className={clsx('text-xs font-mono font-semibold', getGapColorClass(theatre.gap))}>
                            {theatre.gap}%
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-[10px] text-terminal-muted uppercase">Prob.</span>
                          <span className="text-xs font-mono font-semibold text-terminal-text">
                            {theatre.probability}%
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-[10px] text-terminal-muted uppercase">Volume</span>
                          <span className="text-xs font-mono font-semibold text-terminal-text">
                            {theatre.volume}
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-[10px] text-terminal-muted uppercase">Fork In</span>
                          <span className="text-xs font-mono font-semibold text-terminal-text flex items-center gap-1">
                            <Clock className="w-3 h-3 text-terminal-muted" />
                            {theatre.forkIn}
                          </span>
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className="absolute inset-0 flex flex-col items-center justify-center p-4">
                      <select
                        onChange={(e) => addTheatreToSlot(e.target.value, slotId)}
                        className="w-full px-2 py-1.5 text-xs bg-terminal-panel border border-terminal-border rounded text-terminal-text focus:outline-none focus:border-status-info transition-colors cursor-pointer"
                        value=""
                      >
                        <option value="">Select Theatre...</option>
                        {comparisonTheatres.filter(t => !Object.values(compareSlots).some(slot => slot?.id === t.id)).map(t => (
                          <option key={t.id} value={t.id}>{t.name}</option>
                        ))}
                      </select>
                      <span className="text-[10px] text-terminal-muted mt-2">Click to add</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Comparison Charts */}
          {selectedTheatres.length >= 2 && (
            <div className="mt-4 p-3 bg-terminal-bg rounded-lg border border-terminal-border">
              <h4 className="text-[10px] font-bold text-terminal-muted uppercase tracking-wider mb-3">
                Stability Comparison
              </h4>
              {selectedTheatres.map(theatre => (
                <div key={theatre.id} className="flex items-center gap-2 mb-2">
                  <span className="text-[10px] font-mono text-terminal-secondary w-20 truncate">
                    {theatre.name.replace('_', ' ')}
                  </span>
                  <div className="flex-1 h-3 bg-terminal-panel rounded overflow-hidden">
                    <div
                      className={clsx(
                        'h-full rounded transition-all',
                        theatre.stability > 60 ? 'bg-status-success' : theatre.stability > 40 ? 'bg-status-warning' : 'bg-status-danger'
                      )}
                      style={{ width: `${(theatre.stability / maxStability) * 100}%` }}
                    />
                  </div>
                  <span className="text-[10px] font-mono font-semibold text-terminal-text w-8 text-right">
                    {theatre.stability}%
                  </span>
                </div>
              ))}

              <h4 className="text-[10px] font-bold text-terminal-muted uppercase tracking-wider mt-4 mb-3">
                Logic Gap Comparison
              </h4>
              {selectedTheatres.map(theatre => (
                <div key={theatre.id} className="flex items-center gap-2 mb-2">
                  <span className="text-[10px] font-mono text-terminal-secondary w-20 truncate">
                    {theatre.name.replace('_', ' ')}
                  </span>
                  <div className="flex-1 h-3 bg-terminal-panel rounded overflow-hidden">
                    <div
                      className={clsx(
                        'h-full rounded transition-all',
                        theatre.gap > 40 ? 'bg-status-danger' : theatre.gap > 25 ? 'bg-status-warning' : 'bg-status-success'
                      )}
                      style={{ width: `${(theatre.gap / maxGap) * 100}%` }}
                    />
                  </div>
                  <span className="text-[10px] font-mono font-semibold text-terminal-text w-8 text-right">
                    {theatre.gap}%
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

{/* Footer Actions */}
        <div className="px-4 py-3 border-t border-terminal-border bg-terminal-bg/50">
          <div className="flex items-center gap-2">
            <button
              onClick={clearAllSlots}
              className="flex-1 px-3 py-2 text-xs font-medium text-terminal-muted border border-terminal-border rounded hover:border-status-warning hover:text-status-warning transition-colors"
            >
              Clear All
            </button>
            <button
              onClick={() => {
                // Export comparison data
                const data = selectedTheatres.map(t => `${t.name}: $${t.price.toFixed(2)} (${t.change})`).join('\n');
                alert('Comparison exported:\n\n' + data);
              }}
              disabled={selectedTheatres.length === 0}
              className="flex-1 px-3 py-2 text-xs font-medium bg-status-info/10 border border-status-info/30 text-status-info rounded hover:bg-status-info/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Export Comparison
            </button>
          </div>
        </div>

        <style>{`
          .mini-bar {
            flex: 1;
            background: var(--status-info);
            border-radius: 2px 2px 0 0;
            opacity: 0.7;
            transition: height 0.3s ease;
          }
        `}</style>
      </div>
    </>
  );
}
