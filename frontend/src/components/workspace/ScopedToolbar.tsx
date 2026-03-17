import { useRef, useState } from 'react';
import { ArrowLeft, Layers } from 'lucide-react';
import { LayerPopover } from './LayerPopover';
import type { LayerKey, LayerState } from '../../hooks/useLayerState';

interface ScopedToolbarProps {
  layers: LayerState;
  enabledCount: number;
  onToggleLayer: (key: LayerKey) => void;
  onBackToGlobal: () => void;
}

export function ScopedToolbar({ layers, enabledCount, onToggleLayer, onBackToGlobal }: ScopedToolbarProps) {
  const [popoverOpen, setPopoverOpen] = useState(false);
  const layerBtnRef = useRef<HTMLButtonElement>(null);

  return (
    <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 flex items-center gap-2">
      <button
        ref={layerBtnRef}
        onClick={() => setPopoverOpen((v) => !v)}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-mono
          bg-[var(--e-bg-elevated)] border border-[var(--e-border-secondary)]
          text-[var(--e-text-secondary)] hover:text-[var(--e-text-primary)]
          hover:border-[var(--e-border-primary)] transition-colors cursor-pointer"
        aria-expanded={popoverOpen}
      >
        <Layers size={13} />
        Layers &middot; {enabledCount}
      </button>

      <LayerPopover
        open={popoverOpen}
        onClose={() => setPopoverOpen(false)}
        layers={layers}
        onToggle={onToggleLayer}
        anchorRef={layerBtnRef}
      />

      <button
        onClick={onBackToGlobal}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-mono
          bg-[var(--e-bg-elevated)] border border-[var(--e-border-secondary)]
          text-[var(--e-text-secondary)] hover:text-[var(--e-text-primary)]
          hover:border-[var(--e-border-primary)] transition-colors cursor-pointer"
      >
        <ArrowLeft size={13} />
        Back to global view
      </button>
    </div>
  );
}
