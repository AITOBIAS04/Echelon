import { useCallback, useRef, useState } from 'react';

export type CanvasMode = 'global' | 'scoped';
export type DockTab = 'none' | 'evidence' | 'markets' | 'sources';

export interface ViewState {
  center: [number, number]; // [lng, lat]
  zoom: number;
}

const DEFAULT_SCOPE_CENTER: [number, number] = [43.0, 15.0];
const DEFAULT_SCOPE_ZOOM = 5;

export const GLOBE_DEFAULT_VIEW = { lat: 18, lng: 10, altitude: 1.95 };
export const GLOBE_SCOPE_VIEW = { lat: 15, lng: 43, altitude: 0.98 };
export const GLOBE_TO_SCOPED_ALTITUDE = 0.62;
export const SCOPED_TO_GLOBAL_ZOOM = 2.45;

export function useWorkspaceState() {
  const [mode, setModeRaw] = useState<CanvasMode>('global');
  const [leftOpen, setLeftOpen] = useState(false);
  const [rightOpen, setRightOpen] = useState(false);
  const [activeDock, setActiveDock] = useState<DockTab>('none');
  const [scopeView, setScopeView] = useState<'map' | 'satellite'>('map');

  const transitionLock = useRef(false);

  const transitionToScoped = useCallback((viewState?: ViewState) => {
    if (transitionLock.current) return;
    transitionLock.current = true;

    const next = viewState ?? { center: DEFAULT_SCOPE_CENTER, zoom: DEFAULT_SCOPE_ZOOM };
    setModeRaw('scoped');
    setLeftOpen(true);
    setRightOpen(true);
    setActiveDock('none');

    setTimeout(() => {
      transitionLock.current = false;
    }, 420);

    return next;
  }, []);

  const transitionToGlobal = useCallback(() => {
    if (transitionLock.current) return;
    transitionLock.current = true;

    setModeRaw('global');
    setLeftOpen(false);
    setRightOpen(false);
    setActiveDock('none');

    setTimeout(() => {
      transitionLock.current = false;
    }, 760);
  }, []);

  const toggleDock = useCallback((tab: DockTab) => {
    if (mode === 'scoped') return;
    setActiveDock((current) => (current === tab ? 'none' : tab));
  }, [mode]);

  const toggleLeft = useCallback(() => {
    if (mode === 'scoped') return; // always open in scoped
    setLeftOpen((v) => !v);
  }, [mode]);

  const toggleRight = useCallback(() => {
    if (mode === 'scoped') return; // always open in scoped
    setRightOpen((v) => !v);
  }, [mode]);

  return {
    mode,
    leftOpen,
    rightOpen,
    activeDock,
    scopeView,
    setScopeView,
    setLeftOpen,
    setRightOpen,
    transitionToScoped,
    transitionToGlobal,
    toggleDock,
    toggleLeft,
    toggleRight,
    transitionLock,
  };
}
