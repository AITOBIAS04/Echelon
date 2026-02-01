/**
 * Demo Mode React Hooks
 * 
 * Provides React hooks for accessing demo mode state
 * using useSyncExternalStore for efficient subscriptions.
 */

import { useEffect, useMemo, useSyncExternalStore } from "react";
import { isDemoModeEnabled } from "./demoMode";
import { demoStore } from "./demoStore";

export function useDemoEnabled(): boolean {
  return isDemoModeEnabled();
}

export function useDemoOutcome(
  marketId: string | number,
  outcomeId: "YES" | "NO",
  initial: { price: number; stability?: number; volume?: number }
) {
  const enabled = useDemoEnabled();

  useEffect(() => {
    if (!enabled) return;
    demoStore.ensureOutcome(marketId, outcomeId, {
      price: initial.price,
      stability: initial.stability,
      volume: initial.volume,
    });
  }, [enabled, marketId, outcomeId, initial.price, initial.stability, initial.volume]);

  const subscribe = useMemo(
    () => (listener: () => void) => demoStore.subscribeOutcome(marketId, outcomeId, listener),
    [marketId, outcomeId]
  );

  const getSnapshot = useMemo(
    () => () => demoStore.readOutcome(marketId, outcomeId),
    [marketId, outcomeId]
  );

  const snap = useSyncExternalStore(subscribe, getSnapshot, getSnapshot);

  if (!enabled || !snap) {
    return {
      price: initial.price,
      prevPrice: initial.price,
      stability: initial.stability ?? 80,
      volume: initial.volume ?? 100_000,
      updatedAt: 0,
    };
  }

  return snap;
}

export function useDemoPositions() {
  const enabled = useDemoEnabled();

  const subscribe = useMemo(() => (l: () => void) => demoStore.subscribePositions(l), []);
  const getSnapshot = useMemo(() => () => demoStore.getPositions(), []);
  const positions = useSyncExternalStore(subscribe, getSnapshot, getSnapshot);

  return enabled ? positions : [];
}

export function useDemoAgentFeed() {
  const enabled = useDemoEnabled();

  const subscribe = useMemo(() => (l: () => void) => demoStore.subscribeAgentFeed(l), []);
  const getSnapshot = useMemo(() => () => demoStore.getAgentFeed(), []);
  const feed = useSyncExternalStore(subscribe, getSnapshot, getSnapshot);

  return enabled ? feed : [];
}

export function useDemoToasts() {
  const enabled = useDemoEnabled();

  const subscribe = useMemo(() => (l: () => void) => demoStore.subscribeToasts(l), []);
  const getSnapshot = useMemo(() => () => demoStore.getToasts(), []);
  const toasts = useSyncExternalStore(subscribe, getSnapshot, getSnapshot);

  return enabled ? toasts : [];
}

// --- New hooks for Launchpad, Breach Console, Export Console ---

export function useDemoLaunchFeed() {
  const enabled = useDemoEnabled();
  const subscribe = useMemo(() => (l: () => void) => demoStore.subscribeLaunchFeed(l), []);
  const getSnapshot = useMemo(() => () => demoStore.getLaunchFeed(), []);
  const feed = useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
  return enabled ? feed : [];
}

export function useDemoBreaches() {
  const enabled = useDemoEnabled();
  const subscribe = useMemo(() => (l: () => void) => demoStore.subscribeBreaches(l), []);
  const getSnapshot = useMemo(() => () => demoStore.getBreaches(), []);
  const data = useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
  return enabled ? data : { active: [], history: [] };
}

export function useDemoExports() {
  const enabled = useDemoEnabled();
  const subscribe = useMemo(() => (l: () => void) => demoStore.subscribeExports(l), []);
  const getSnapshot = useMemo(() => () => demoStore.getExports(), []);
  const data = useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
  return enabled
    ? data
    : { active: [], partners: [], config: { samplingRate: 0.5, format: "PyTorch (.pt)", compression: "GZIP" as const } };
}
