/**
 * Demo Store - Central State Management
 * 
 * Manages demo mode state for:
 * - Market outcomes (prices, stability, volume)
 * - Demo positions (user bets)
 * - Agent activity feed
 * - Toast notifications
 * - Launch feed (Launchpad)
 * - Breaches (Breach Console)
 * - Exports (Export Console)
 */

type OutcomeKey = string; // `${marketId}:${outcomeId}`
type Listener = () => void;

export type DemoOutcomeSnapshot = {
  price: number;       // 0..1
  prevPrice: number;
  stability: number;   // 0..100
  volume: number;
  updatedAt: number;
};

export type DemoPosition = {
  id: string;
  openedAt: number;
  marketId: string;
  marketTitle: string;
  outcomeId: "YES" | "NO";
  stake: number;
  entryPrice: number; // 0..1 (for the chosen side)
  shares: number;     // stake / entryPrice
};

export type DemoAgentEvent = {
  id: string;
  ts: number;
  text: string;
};

// --- New types for Launchpad, Breach Console, Export Console ---

export type DemoLaunchFeedItem = {
  id: string;
  ts: number;
  kind: "launch" | "milestone" | "warning";
  actor: string;
  message: string;
  accent: "success" | "warning" | "danger" | "info";
  cta?: { label: string; action: "inject_shield" };
};

export type DemoBreach = {
  id: string;
  type: "PARADOX" | "STABILITY" | "ORACLE" | "SENSOR";
  timeline: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM";
  ts: number; // opened time
  logicGap: number; // %
  stability: number; // %
  carrier: string;
  sanity: number; // %
  status: "ACTIVE" | "CONTAINED";
};

export type DemoBreachHistoryRow = {
  id: string;
  time: string;
  type: DemoBreach["type"];
  timeline: string;
  severity: DemoBreach["severity"];
  resolution: string;
  impact: string;
};

export type DemoExportJob = {
  id: string;
  partner: string;
  status: "PROCESSING" | "QUEUED" | "COMPLETED" | "FAILED";
  theatre: string;
  episodes: number;
  samplingRate: number; // 0..1
  format: "PyTorch (.pt)" | "ROS Bag (.bag)" | "TFRecord (.tfrecord)" | "JSON (Canonical)";
  sizeGb: number;
  progress: number; // 0..100
  etaSec: number;
};

export type DemoExportPartner = {
  name: string;
  access: "Premium" | "Standard";
  exports30d: number;
  dataVolumeGb: number;
  status: "Active" | "Paused";
};

export type DemoExportConfig = {
  samplingRate: number; // 0..1
  format: DemoExportJob["format"];
  compression: "GZIP" | "None";
};

type StoreState = {
  outcomes: Map<OutcomeKey, DemoOutcomeSnapshot>;
  positions: DemoPosition[];
  agentFeed: DemoAgentEvent[];
  toasts: { id: string; ts: number; title: string; detail?: string }[];
  // New slices
  launchFeed: DemoLaunchFeedItem[];
  breachesActive: DemoBreach[];
  breachesHistory: DemoBreachHistoryRow[];
  exportsActive: DemoExportJob[];
  exportPartners: DemoExportPartner[];
  exportConfig: DemoExportConfig;
};

const state: StoreState = {
  outcomes: new Map(),
  positions: [],
  agentFeed: [],
  toasts: [],
  // New slices
  launchFeed: [],
  breachesActive: [],
  breachesHistory: [],
  exportsActive: [],
  exportPartners: [],
  exportConfig: { samplingRate: 0.5, format: "PyTorch (.pt)", compression: "GZIP" },
};

const outcomeListeners = new Map<OutcomeKey, Set<Listener>>();
const positionsListeners = new Set<Listener>();
const agentFeedListeners = new Set<Listener>();
const toastListeners = new Set<Listener>();
// New listener sets
const launchFeedListeners = new Set<Listener>();
const breachListeners = new Set<Listener>();
const exportListeners = new Set<Listener>();

function emit(set: Set<Listener>) {
  set.forEach((l) => l());
}

function keyOf(marketId: string | number, outcomeId: string): OutcomeKey {
  return `${String(marketId)}:${outcomeId}`;
}

function clamp(n: number, min: number, max: number) {
  return Math.min(max, Math.max(min, n));
}

export const demoStore = {
  // --- Outcomes ---
  ensureOutcome(
    marketId: string | number,
    outcomeId: "YES" | "NO",
    initial: Partial<DemoOutcomeSnapshot>
  ) {
    const key = keyOf(marketId, outcomeId);
    if (state.outcomes.has(key)) return;

    const now = Date.now();
    state.outcomes.set(key, {
      price: clamp(initial.price ?? 0.5, 0.02, 0.98),
      prevPrice: clamp(initial.prevPrice ?? initial.price ?? 0.5, 0.02, 0.98),
      stability: clamp(initial.stability ?? 80, 0, 100),
      volume: Math.max(0, initial.volume ?? 100_000),
      updatedAt: initial.updatedAt ?? now,
    });

    const set = outcomeListeners.get(key);
    if (set) emit(set);
  },

  updateOutcome(
    marketId: string | number,
    outcomeId: "YES" | "NO",
    updater: (prev: DemoOutcomeSnapshot) => DemoOutcomeSnapshot
  ) {
    const key = keyOf(marketId, outcomeId);
    const prev = state.outcomes.get(key);
    if (!prev) return;

    state.outcomes.set(key, updater(prev));
    const set = outcomeListeners.get(key);
    if (set) emit(set);
  },

  readOutcome(marketId: string | number, outcomeId: "YES" | "NO") {
    return state.outcomes.get(keyOf(marketId, outcomeId));
  },

  listOutcomeKeys(): string[] {
    return Array.from(state.outcomes.keys());
  },

  subscribeOutcome(marketId: string | number, outcomeId: "YES" | "NO", listener: Listener) {
    const key = keyOf(marketId, outcomeId);
    let set = outcomeListeners.get(key);
    if (!set) {
      set = new Set();
      outcomeListeners.set(key, set);
    }
    set.add(listener);
    return () => {
      set!.delete(listener);
      if (set!.size === 0) outcomeListeners.delete(key);
    };
  },

  // --- Positions ---
  getPositions() {
    return state.positions;
  },

  setPositions(next: DemoPosition[]) {
    state.positions = next;
    emit(positionsListeners);
  },

  subscribePositions(listener: Listener) {
    positionsListeners.add(listener);
    return () => positionsListeners.delete(listener);
  },

  // --- Agent feed ---
  getAgentFeed() {
    return state.agentFeed;
  },

  pushAgentEvent(ev: DemoAgentEvent, max = 20) {
    state.agentFeed = [ev, ...state.agentFeed].slice(0, max);
    emit(agentFeedListeners);
  },

  subscribeAgentFeed(listener: Listener) {
    agentFeedListeners.add(listener);
    return () => agentFeedListeners.delete(listener);
  },

  // --- Toasts ---
  getToasts() {
    return state.toasts;
  },

  pushToast(title: string, detail?: string, ttlMs = 3200) {
    if (typeof window === "undefined") return;
    const id = `t_${Math.random().toString(16).slice(2)}`;
    const ts = Date.now();

    state.toasts = [{ id, ts, title, detail }, ...state.toasts].slice(0, 3);
    emit(toastListeners);

    window.setTimeout(() => {
      state.toasts = state.toasts.filter((t) => t.id !== id);
      emit(toastListeners);
    }, ttlMs);
  },

  subscribeToasts(listener: Listener) {
    toastListeners.add(listener);
    return () => toastListeners.delete(listener);
  },

  // --- Launch Feed ---
  getLaunchFeed() {
    return state.launchFeed;
  },

  pushLaunchFeed(item: DemoLaunchFeedItem, max = 20) {
    state.launchFeed = [item, ...state.launchFeed].slice(0, max);
    emit(launchFeedListeners);
  },

  subscribeLaunchFeed(listener: Listener) {
    launchFeedListeners.add(listener);
    return () => launchFeedListeners.delete(listener);
  },

  // --- Breaches ---
  getBreaches() {
    return { active: state.breachesActive, history: state.breachesHistory };
  },

  setBreaches(active: DemoBreach[], history: DemoBreachHistoryRow[]) {
    state.breachesActive = active;
    state.breachesHistory = history;
    emit(breachListeners);
  },

  updateBreach(id: string, updater: (b: DemoBreach) => DemoBreach) {
    state.breachesActive = state.breachesActive.map((b) => (b.id === id ? updater(b) : b));
    emit(breachListeners);
  },

  moveBreachToHistory(id: string, resolution: string, impact: string) {
    const b = state.breachesActive.find((x) => x.id === id);
    if (!b) return;
    state.breachesActive = state.breachesActive.filter((x) => x.id !== id);
    const time = new Date().toLocaleTimeString("en-GB", { hour12: false });
    state.breachesHistory = [
      { id: `h_${id}`, time, type: b.type, timeline: b.timeline, severity: b.severity, resolution, impact },
      ...state.breachesHistory,
    ].slice(0, 50);
    emit(breachListeners);
  },

  subscribeBreaches(listener: Listener) {
    breachListeners.add(listener);
    return () => breachListeners.delete(listener);
  },

  // --- Exports ---
  getExports() {
    return { active: state.exportsActive, partners: state.exportPartners, config: state.exportConfig };
  },

  setExports(active: DemoExportJob[]) {
    state.exportsActive = active;
    emit(exportListeners);
  },

  setExportConfig(next: DemoExportConfig) {
    state.exportConfig = next;
    emit(exportListeners);
  },

  subscribeExports(listener: Listener) {
    exportListeners.add(listener);
    return () => exportListeners.delete(listener);
  },
};
