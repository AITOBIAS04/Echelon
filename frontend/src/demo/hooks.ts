/**
 * Demo Mode React Hooks
 * 
 * Provides React hooks for accessing demo mode state
 * using useSyncExternalStore for efficient subscriptions.
 */

import { useEffect, useMemo, useSyncExternalStore } from "react";
import { isDemoModeEnabled } from "./demoMode";
import { demoStore } from "./demoStore";
import type { DemoExportConfig } from "./demoStore";

export function useDemoEnabled(): boolean {
  return isDemoModeEnabled();
}

// Constants for stable snapshots when demo is OFF
const EMPTY_ARRAY: never[] = [];
const EMPTY_CONFIG: DemoExportConfig = { samplingRate: 0.5, format: "PyTorch (.pt)", compression: "GZIP" };

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

  const subscribe = useMemo(() => {
    if (!enabled) return () => () => {};
    return (listener: () => void) => demoStore.subscribePositions(listener);
  }, [enabled]);

  const getSnapshot = useMemo(() => {
    if (!enabled) return () => EMPTY_ARRAY;
    return () => demoStore.getPositions();
  }, [enabled]);

  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}

export function useDemoAgentFeed() {
  const enabled = useDemoEnabled();

  const subscribe = useMemo(() => {
    if (!enabled) return () => () => {};
    return (listener: () => void) => demoStore.subscribeAgentFeed(listener);
  }, [enabled]);

  const getSnapshot = useMemo(() => {
    if (!enabled) return () => EMPTY_ARRAY;
    return () => demoStore.getAgentFeed();
  }, [enabled]);

  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}

export function useDemoToasts() {
  const enabled = useDemoEnabled();

  const subscribe = useMemo(() => {
    if (!enabled) return () => () => {};
    return (listener: () => void) => demoStore.subscribeToasts(listener);
  }, [enabled]);

  const getSnapshot = useMemo(() => {
    if (!enabled) return () => EMPTY_ARRAY;
    return () => demoStore.getToasts();
  }, [enabled]);

  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}

// --- New hooks for Launchpad, Breach Console, Export Console ---

export function useDemoLaunchFeed() {
  const enabled = useDemoEnabled();

  const subscribe = useMemo(() => {
    if (!enabled) return () => () => {};
    return (listener: () => void) => demoStore.subscribeLaunchFeed(listener);
  }, [enabled]);

  const getSnapshot = useMemo(() => {
    if (!enabled) return () => EMPTY_ARRAY;
    return () => demoStore.getLaunchFeed();
  }, [enabled]);

  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}

export function useDemoBreaches() {
  const enabled = useDemoEnabled();

  const subscribe = useMemo(() => {
    if (!enabled) return () => () => {};
return (listener: () => void) => demoStore.subscribeBreaches(listener);
  }, [enabled]);

  const getSnapshotActive = useMemo(() => {
    if (!enabled) return () => EMPTY_ARRAY;
    return () => demoStore.getBreachesActive();
  }, [enabled]);

  const getSnapshotHistory = useMemo(() => {
    if (!enabled) return () => EMPTY_ARRAY;
    return () => demoStore.getBreachesHistory();
  }, [enabled]);

  const active = useSyncExternalStore(subscribe, getSnapshotActive, getSnapshotActive);
  const history = useSyncExternalStore(subscribe, getSnapshotHistory, getSnapshotHistory);

  return { active, history };
}

export function useDemoExports() {
  const enabled = useDemoEnabled();

  const subscribe = useMemo(() => {
    if (!enabled) return () => () => {};
    return (listener: () => void) => demoStore.subscribeExports(listener);
  }, [enabled]);

  const getSnapshotActive = useMemo(() => {
    if (!enabled) return () => EMPTY_ARRAY;
    return () => demoStore.getExportsActive();
  }, [enabled]);

  const getSnapshotPartners = useMemo(() => {
    if (!enabled) return () => EMPTY_ARRAY;
    return () => demoStore.getExportPartners();
  }, [enabled]);

  const getSnapshotConfig = useMemo(() => {
    if (!enabled) return () => EMPTY_CONFIG;
    return () => demoStore.getExportConfig();
  }, [enabled]);

  const active = useSyncExternalStore(subscribe, getSnapshotActive, getSnapshotActive);
  const partners = useSyncExternalStore(subscribe, getSnapshotPartners, getSnapshotPartners);
  const config = useSyncExternalStore(subscribe, getSnapshotConfig, getSnapshotConfig);

  return { active, partners, config };
}
