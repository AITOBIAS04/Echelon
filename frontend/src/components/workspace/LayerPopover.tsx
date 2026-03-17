import { useRef, useEffect, useCallback } from 'react';
import {
  ALL_LAYERS,
  LAYER_LABELS,
  LAYER_COLOURS,
  type LayerKey,
  type LayerState,
} from '../../hooks/useLayerState';

interface LayerPopoverProps {
  open: boolean;
  onClose: () => void;
  layers: LayerState;
  onToggle: (key: LayerKey) => void;
  anchorRef: React.RefObject<HTMLButtonElement | null>;
}

export function LayerPopover({ open, onClose, layers, onToggle, anchorRef }: LayerPopoverProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  // Position relative to anchor
  useEffect(() => {
    if (!open || !anchorRef.current || !panelRef.current) return;
    const rect = anchorRef.current.getBoundingClientRect();
    const panel = panelRef.current;
    panel.style.top = `${rect.bottom + 10}px`;
    panel.style.left = `${rect.left}px`;
  }, [open, anchorRef]);

  // Click outside to close
  const handleClickOutside = useCallback((e: MouseEvent) => {
    if (panelRef.current && !panelRef.current.contains(e.target as Node) &&
        anchorRef.current && !anchorRef.current.contains(e.target as Node)) {
      onClose();
    }
  }, [onClose, anchorRef]);

  useEffect(() => {
    if (!open) return;
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [open, handleClickOutside]);

  if (!open) return null;

  return (
    <div
      ref={panelRef}
      className="fixed z-50 w-56 rounded-xl p-3
        bg-[var(--e-bg-card)]/90 backdrop-blur-xl
        border border-[var(--e-border-secondary)]
        shadow-lg shadow-black/20"
      role="menu"
    >
      <div className="text-[10px] font-mono uppercase tracking-wider
        text-[var(--e-text-muted)] mb-2 px-1">
        Map layers
      </div>
      <div className="flex flex-col gap-1">
        {ALL_LAYERS.map((key) => (
          <button
            key={key}
            role="menuitemcheckbox"
            aria-checked={layers[key]}
            onClick={() => onToggle(key)}
            className="flex items-center gap-2.5 px-2 py-1.5 rounded-lg
              text-xs text-[var(--e-text-primary)] transition-colors
              hover:bg-[var(--e-bg-elevated)]"
          >
            {/* Colour indicator + checkbox */}
            <span
              className="w-3 h-3 rounded-sm border transition-all flex items-center justify-center"
              style={{
                backgroundColor: layers[key] ? LAYER_COLOURS[key] : 'transparent',
                borderColor: layers[key] ? LAYER_COLOURS[key] : 'var(--e-border-secondary)',
              }}
            >
              {layers[key] && (
                <svg width="8" height="8" viewBox="0 0 8 8" fill="none">
                  <path d="M1.5 4L3.2 5.8L6.5 2.2" stroke="white" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              )}
            </span>
            <span className="font-medium">{LAYER_LABELS[key]}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
