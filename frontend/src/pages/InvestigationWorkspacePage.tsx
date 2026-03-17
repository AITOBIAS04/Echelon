import { useCallback, useEffect, useState } from 'react';
import { Globe2, Map } from 'lucide-react';
import { GlobeCanvas } from '../components/workspace/GlobeCanvas';
import { ScopedMap } from '../components/workspace/ScopedMap';
import { GlobalToolbar } from '../components/workspace/GlobalToolbar';
import { ScopedToolbar } from '../components/workspace/ScopedToolbar';
import { LeftPanel } from '../components/workspace/LeftPanel';
import { RightPanel } from '../components/workspace/RightPanel';
import { BottomDock } from '../components/workspace/BottomDock';
import { useWorkspaceState, type ViewState } from '../hooks/useWorkspaceState';
import { useLayerState } from '../hooks/useLayerState';
import { useOsintHealth, useOsintSummary } from '../hooks/useOsint';

export function InvestigationWorkspacePage() {
  const workspace = useWorkspaceState();
  const layerState = useLayerState();
  const { data: summary, isLoading: summaryLoading } = useOsintSummary();
  const { data: health, isLoading: healthLoading } = useOsintHealth();

  const [scopeViewState, setScopeViewState] = useState<ViewState | undefined>();

  const handleScopeTransition = useCallback((viewState: ViewState) => {
    setScopeViewState(viewState);
    workspace.transitionToScoped(viewState);
  }, [workspace]);

  const handleGlobeTransition = useCallback(() => {
    workspace.transitionToGlobal();
  }, [workspace]);

  const handleMapReady = useCallback((map: maplibregl.Map) => {
    layerState.setMapRef(map);
  }, [layerState]);

  const handleLaunchInvestigation = useCallback(() => {
    // Transition to scoped view when an investigation is selected
    handleScopeTransition({ center: [43.0, 15.0], zoom: 3 });
  }, [handleScopeTransition]);

  return (
    <div
      className="relative w-full h-[calc(100vh-3.5rem)] overflow-hidden bg-[var(--e-bg-primary)]"
      data-mode={workspace.mode}
    >
      {/* ── Canvas stage ───────────────────────────────────────── */}
      <div className="absolute inset-0">
        <GlobeCanvas
          mode={workspace.mode}
          onScopeTransition={handleScopeTransition}
        />
        <ScopedMap
          mode={workspace.mode}
          viewState={scopeViewState}
          layers={layerState.layers}
          onGlobeTransition={handleGlobeTransition}
          onMapReady={handleMapReady}
        />
      </div>

      {/* ── Mode toggle (bottom-right, above zoom controls) ───── */}
      <div className="absolute bottom-24 right-4 z-40 flex items-center gap-1
        bg-[var(--e-bg-card)]/80 backdrop-blur-md rounded-full p-0.5
        border border-[var(--e-border-secondary)]">
        <ModeButton
          icon={Globe2}
          label="Global"
          active={workspace.mode === 'global'}
          onClick={handleGlobeTransition}
        />
        <ModeButton
          icon={Map}
          label="Scoped"
          active={workspace.mode === 'scoped'}
          onClick={() => handleScopeTransition(scopeViewState ?? { center: [43.0, 15.0], zoom: 3 })}
        />
      </div>

      {/* ── Toolbars ───────────────────────────────────────────── */}
      {workspace.mode === 'global' && (
        <GlobalToolbar summary={summary} isLoading={summaryLoading} />
      )}
      {workspace.mode === 'scoped' && (
        <ScopedToolbar
          layers={layerState.layers}
          enabledCount={layerState.enabledCount}
          onToggleLayer={layerState.toggleLayer}
          onBackToGlobal={handleGlobeTransition}
        />
      )}

      {/* ── Floating panels ────────────────────────────────────── */}
      <LeftPanel
        mode={workspace.mode}
        isOpen={workspace.leftOpen}
        onClose={() => workspace.setLeftOpen(false)}
        onOpen={() => workspace.setLeftOpen(true)}
        onLaunchInvestigation={handleLaunchInvestigation}
      />
      <RightPanel
        mode={workspace.mode}
        isOpen={workspace.rightOpen}
        onClose={() => workspace.setRightOpen(false)}
        onOpen={() => workspace.setRightOpen(true)}
        health={health}
        isLoading={healthLoading}
      />

      {/* ── Bottom dock ────────────────────────────────────────── */}
      <BottomDock
        mode={workspace.mode}
        activeDock={workspace.activeDock}
        onToggleDock={workspace.toggleDock}
      />

      {/* ── Keyboard handler ───────────────────────────────────── */}
      <KeyboardHandler
        onEscape={() => {
          if (workspace.mode === 'scoped') {
            handleGlobeTransition();
          }
          workspace.setLeftOpen(false);
          workspace.setRightOpen(false);
        }}
      />
    </div>
  );
}

// ── Sub-components ──────────────────────────────────────────────────

function ModeButton({
  icon: Icon,
  label,
  active,
  onClick,
}: {
  icon: typeof Globe2;
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-mono transition-all cursor-pointer
        ${active
          ? 'bg-[var(--e-bg-elevated)] text-[var(--e-text-primary)] shadow-sm'
          : 'text-[var(--e-text-muted)] hover:text-[var(--e-text-secondary)]'
        }`}
    >
      <Icon size={12} />
      {label}
    </button>
  );
}

function KeyboardHandler({ onEscape }: { onEscape: () => void }) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onEscape();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onEscape]);

  return null;
}
