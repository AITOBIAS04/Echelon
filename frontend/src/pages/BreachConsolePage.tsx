import { useMemo } from "react";
import { AlertTriangle, Shield, UserPlus, Gavel } from "lucide-react";
import { useParadoxes, type Paradox } from "../hooks/useBreaches";

type Severity = "CRITICAL" | "HIGH" | "MEDIUM";

function severityFromClass(cls: string): Severity {
  if (cls === "CLASS_1_CRITICAL") return "CRITICAL";
  if (cls === "CLASS_2_SEVERE") return "HIGH";
  return "MEDIUM";
}

function severityClasses(sev: Severity) {
  if (sev === "CRITICAL") return { border: "border-status-danger/30", text: "text-status-danger", badge: "bg-status-danger/10 border-status-danger/30 text-status-danger" };
  if (sev === "HIGH") return { border: "border-status-warning/30", text: "text-status-warning", badge: "bg-status-warning/10 border-status-warning/30 text-status-warning" };
  return { border: "border-status-paradox/25", text: "text-status-paradox", badge: "bg-status-paradox/10 border-status-paradox/25 text-status-paradox" };
}

function timeAgo(isoTimestamp: string) {
  const s = Math.max(0, Math.floor((Date.now() - new Date(isoTimestamp).getTime()) / 1000));
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  return `${h}h ago`;
}

function formatCountdown(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}m ${s}s`;
}

export function BreachConsolePage() {
  const { paradoxes, isLoading } = useParadoxes();

  const active = useMemo(
    () => paradoxes.filter((p: Paradox) => p.status === "ACTIVE" || p.status === "EXTRACTING"),
    [paradoxes],
  );

  const metrics = useMemo(() => ({
    activeCount: active.length,
    criticalCount: active.filter((p: Paradox) => p.severity_class === "CLASS_1_CRITICAL").length,
    extracting: active.filter((p: Paradox) => p.status === "EXTRACTING").length,
  }), [active]);

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-terminal-text-muted text-sm">Loading paradox data...</div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col gap-4 pt-4">
      {/* Active + metrics */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 min-h-0">
        {/* Active paradoxes */}
        <div className="xl:col-span-2 bg-terminal-panel border border-terminal-border rounded-lg p-4 min-h-0 flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-status-warning" />
              <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide">
                Active Paradoxes ({active.length})
              </h3>
            </div>
          </div>

          <div className="flex-1 min-h-0 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent space-y-3 pr-1">
            {active.map((p: Paradox) => {
              const sev = severityFromClass(p.severity_class);
              const s = severityClasses(sev);
              const gapPct = Math.round(p.logic_gap * 100);
              return (
                <div key={p.id} className={`bg-terminal-card border ${s.border} rounded-lg p-3`}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${s.badge}`}>
                          {p.status === "EXTRACTING" ? "EXTRACTING" : "PARADOX"}
                        </span>
                        <span className="text-sm font-semibold text-terminal-text">{p.timeline_name}</span>
                        <span className={`text-xs font-semibold ${s.text}`}>{sev}</span>
                        <span className="text-xs text-terminal-text-muted">{timeAgo(p.spawned_at)}</span>
                      </div>
                      <div className="mt-2 text-xs text-terminal-text-secondary">
                        Logic gap: <span className="text-terminal-text tabular-nums">{gapPct}%</span>
                        {"  "}•{"  "}
                        Decay: <span className="text-terminal-text tabular-nums">{p.decay_multiplier}x</span>
                        {"  "}•{"  "}
                        Detonation: <span className="text-terminal-text tabular-nums">{formatCountdown(p.time_remaining_seconds)}</span>
                        {p.carrier_agent_name && (
                          <>
                            {"  "}•{"  "}
                            Carrier: <span className="text-terminal-text">{p.carrier_agent_name}</span> (Sanity{" "}
                            <span className="text-terminal-text tabular-nums">{p.carrier_agent_sanity ?? 0}</span>)
                          </>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 flex-shrink-0">
                      <button
                        disabled
                        className="px-2.5 py-1.5 text-xs rounded border border-terminal-border opacity-50 cursor-not-allowed flex items-center gap-1"
                        title="Extraction not yet connected"
                      >
                        <Shield className="w-3.5 h-3.5" />
                        Extract
                      </button>
                      <button
                        disabled
                        className="px-2.5 py-1.5 text-xs rounded border border-terminal-border opacity-50 cursor-not-allowed flex items-center gap-1"
                        title="Not yet connected"
                      >
                        <UserPlus className="w-3.5 h-3.5" />
                        Deploy
                      </button>
                      <button
                        disabled
                        className="px-2.5 py-1.5 text-xs rounded border border-terminal-border opacity-50 cursor-not-allowed flex items-center gap-1"
                        title="Abandonment not yet connected"
                      >
                        <Gavel className="w-3.5 h-3.5" />
                        Abandon
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}

            {active.length === 0 && (
              <div className="text-xs text-terminal-text-muted py-8 text-center">
                No active paradoxes detected
              </div>
            )}
          </div>
        </div>

        {/* Metrics */}
        <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
          <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide mb-3">Paradox Analytics</h3>
          <div className="space-y-3">
            <div className="bg-terminal-card border border-terminal-border rounded-lg p-3">
              <div className="text-xs text-terminal-text-muted">Active Paradoxes</div>
              <div className="mt-1 text-lg font-semibold text-terminal-text tabular-nums">{metrics.activeCount}</div>
            </div>
            <div className="bg-terminal-card border border-terminal-border rounded-lg p-3">
              <div className="text-xs text-terminal-text-muted">Critical</div>
              <div className="mt-1 text-lg font-semibold text-status-danger tabular-nums">{metrics.criticalCount}</div>
            </div>
            <div className="bg-terminal-card border border-terminal-border rounded-lg p-3">
              <div className="text-xs text-terminal-text-muted">Extracting</div>
              <div className="mt-1 text-lg font-semibold text-terminal-text tabular-nums">{metrics.extracting}</div>
            </div>
          </div>
        </div>
      </div>

      {/* History */}
      <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4 min-h-0">
        <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide mb-3">Paradox History</h3>
        <div className="text-xs text-terminal-text-muted py-6 text-center">
          No history available — resolved paradox tracking coming soon
        </div>
      </div>
    </div>
  );
}
