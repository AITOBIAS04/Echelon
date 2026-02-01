import { useEffect, useMemo } from "react";
import { AlertTriangle, Shield, UserPlus, Gavel } from "lucide-react";
import { useDemoEnabled, useDemoBreaches } from "../demo/hooks";
import { demoStore } from "../demo/demoStore";

type Severity = "CRITICAL" | "HIGH" | "MEDIUM";

const STATIC_ACTIVE = [
  {
    id: "b_static_1",
    type: "PARADOX" as const,
    timeline: "ORB_SALVAGE_F7",
    severity: "CRITICAL" as const,
    ts: Date.now() - 4 * 60 * 1000,
    logicGap: 68,
    stability: 22,
    carrier: "VIPER",
    sanity: 18,
    status: "ACTIVE" as const,
  },
  {
    id: "b_static_2",
    type: "STABILITY" as const,
    timeline: "VEN_OIL_TANKER",
    severity: "HIGH" as const,
    ts: Date.now() - 11 * 60 * 1000,
    logicGap: 31,
    stability: 44,
    carrier: "SENTINEL",
    sanity: 62,
    status: "ACTIVE" as const,
  },
];

const STATIC_HISTORY = [
  { id: "h1", time: "14:28:45", type: "STABILITY" as const, timeline: "VEN_OIL_TANKER", severity: "HIGH" as const, resolution: "Shield injected", impact: "-8% stability" },
  { id: "h2", time: "14:11:03", type: "ORACLE" as const, timeline: "L2_SEQUENCER", severity: "MEDIUM" as const, resolution: "Oracle failover", impact: "-2% stability" },
];

function severityClasses(sev: Severity) {
  if (sev === "CRITICAL") return { border: "border-status-danger/30", text: "text-status-danger", badge: "bg-status-danger/10 border-status-danger/30 text-status-danger" };
  if (sev === "HIGH") return { border: "border-status-warning/30", text: "text-status-warning", badge: "bg-status-warning/10 border-status-warning/30 text-status-warning" };
  return { border: "border-status-paradox/25", text: "text-status-paradox", badge: "bg-status-paradox/10 border-status-paradox/25 text-status-paradox" };
}

function timeAgo(ts: number) {
  const s = Math.max(0, Math.floor((Date.now() - ts) / 1000));
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  return `${h}h ago`;
}

export function BreachConsolePage() {
  const demoEnabled = useDemoEnabled();
  const demo = useDemoBreaches();

  // Optional: seed demo data once if your engine does not seed breaches automatically.
  useEffect(() => {
    if (!demoEnabled) return;
    if (demo.active.length > 0 || demo.history.length > 0) return;

    // Minimal seed using the static samples.
    // If you seed inside DemoEngine, remove this effect.
    demoStore.setBreaches(STATIC_ACTIVE, STATIC_HISTORY);
  }, [demoEnabled, demo.active.length, demo.history.length]);

  const active = demoEnabled ? demo.active : STATIC_ACTIVE;
  const history = demoEnabled ? demo.history : STATIC_HISTORY;

  const metrics = useMemo(() => {
    // Lightweight, "credible" metrics without backend.
    const breaches24h = 27;
    const avgResolution = "8m 24s";
    const containment = "84%";
    return { breaches24h, avgResolution, containment };
  }, []);

  const onInjectShield = (id: string) => {
    if (!demoEnabled) return;
    demoStore.updateBreach(id, (b) => ({
      ...b,
      stability: Math.min(100, b.stability + 14),
      logicGap: Math.max(0, b.logicGap - 12),
      sanity: Math.min(100, b.sanity + 6),
    }));
    demoStore.pushToast("Shield injected", "Containment stabilising");
  };

  const onDeployDiplomat = (id: string) => {
    if (!demoEnabled) return;
    // Cosmetic action + toast
    demoStore.pushToast("Diplomat deployed", "Negotiation channel opened");
    // Optionally reduce severity slightly
    demoStore.updateBreach(id, (b) => ({
      ...b,
      severity: b.severity === "CRITICAL" ? "HIGH" : b.severity,
    }));
  };

  const onForceSettlement = (id: string) => {
    if (!demoEnabled) return;
    demoStore.moveBreachToHistory(id, "Force settlement", "-5% stability (contained)");
    demoStore.pushToast("Settlement forced", "Breach moved to history");
  };

  return (
    <div className="h-full flex flex-col gap-4">
      <div className="flex items-center justify-between flex-shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-terminal-text uppercase tracking-wide">Breach Console</h1>
          <p className="text-sm text-terminal-text-secondary mt-1">
            Monitor and respond to active breaches across all theatres
          </p>
        </div>
      </div>

      {/* Active + metrics */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 min-h-0">
        {/* Active breaches */}
        <div className="xl:col-span-2 bg-terminal-panel border border-terminal-border rounded-lg p-4 min-h-0 flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-status-warning" />
              <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide">
                Active Breaches ({active.length})
              </h3>
            </div>
          </div>

          <div className="flex-1 min-h-0 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent space-y-3 pr-1">
            {active.map((b: any) => {
              const s = severityClasses(b.severity);
              return (
                <div key={b.id} className={`bg-terminal-card border ${s.border} rounded-lg p-3`}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${s.badge}`}>{b.type}</span>
                        <span className="text-sm font-semibold text-terminal-text">{b.timeline}</span>
                        <span className={`text-xs font-semibold ${s.text}`}>{b.severity}</span>
                        <span className="text-xs text-terminal-text-muted">{timeAgo(b.ts)}</span>
                      </div>
                      <div className="mt-2 text-xs text-terminal-text-secondary">
                        Logic gap: <span className="text-terminal-text tabular-nums">{b.logicGap}%</span>
                        {"  "}•{"  "}
                        Stability: <span className="text-terminal-text tabular-nums">{b.stability}%</span>
                        {"  "}•{"  "}
                        Carrier: <span className="text-terminal-text">{b.carrier}</span> (Sanity{" "}
                        <span className="text-terminal-text tabular-nums">{b.sanity}%</span>)
                      </div>
                    </div>

                    <div className="flex items-center gap-2 flex-shrink-0">
                      <button
                        onClick={() => onInjectShield(b.id)}
                        className="px-2.5 py-1.5 text-xs rounded border border-terminal-border hover:border-status-entropy/60 hover:text-status-entropy transition flex items-center gap-1"
                        title="Inject Shield"
                      >
                        <Shield className="w-3.5 h-3.5" />
                        Inject Shield
                      </button>
                      <button
                        onClick={() => onDeployDiplomat(b.id)}
                        className="px-2.5 py-1.5 text-xs rounded border border-terminal-border hover:border-status-info/60 hover:text-status-info transition flex items-center gap-1"
                        title="Deploy Diplomat"
                      >
                        <UserPlus className="w-3.5 h-3.5" />
                        Deploy
                      </button>
                      <button
                        onClick={() => onForceSettlement(b.id)}
                        className="px-2.5 py-1.5 text-xs rounded border border-terminal-border hover:border-status-danger/60 hover:text-status-danger transition flex items-center gap-1"
                        title="Force Settlement"
                      >
                        <Gavel className="w-3.5 h-3.5" />
                        Settle
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}

            {active.length === 0 ? (
              <div className="text-xs text-terminal-text-muted py-8 text-center">
                No active breaches detected
              </div>
            ) : null}
          </div>
        </div>

        {/* Metrics */}
        <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
          <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide mb-3">Breach Analytics</h3>
          <div className="space-y-3">
            <div className="bg-terminal-card border border-terminal-border rounded-lg p-3">
              <div className="text-xs text-terminal-text-muted">Breaches (24h)</div>
              <div className="mt-1 text-lg font-semibold text-terminal-text tabular-nums">{metrics.breaches24h}</div>
              <div className="text-xs text-status-success">↓ 12%</div>
            </div>
            <div className="bg-terminal-card border border-terminal-border rounded-lg p-3">
              <div className="text-xs text-terminal-text-muted">Avg Resolution Time</div>
              <div className="mt-1 text-lg font-semibold text-terminal-text tabular-nums">{metrics.avgResolution}</div>
              <div className="text-xs text-status-success">↓ 22%</div>
            </div>
            <div className="bg-terminal-card border border-terminal-border rounded-lg p-3">
              <div className="text-xs text-terminal-text-muted">Containment Rate</div>
              <div className="mt-1 text-lg font-semibold text-terminal-text tabular-nums">{metrics.containment}</div>
              <div className="text-xs text-status-success">↑ 5%</div>
            </div>
          </div>
        </div>
      </div>

      {/* History */}
      <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4 min-h-0">
        <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide mb-3">Breach History</h3>
        <div className="max-h-[260px] overflow-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
          <table className="w-full text-xs">
            <thead className="text-terminal-text-muted">
              <tr className="border-b border-terminal-border">
                <th className="text-left py-2 pr-3 font-medium">Time</th>
                <th className="text-left py-2 pr-3 font-medium">Type</th>
                <th className="text-left py-2 pr-3 font-medium">Timeline</th>
                <th className="text-left py-2 pr-3 font-medium">Severity</th>
                <th className="text-left py-2 pr-3 font-medium">Resolution</th>
                <th className="text-left py-2 pr-3 font-medium">Impact</th>
              </tr>
            </thead>
            <tbody>
              {history.map((row: any) => {
                const s = severityClasses(row.severity);
                return (
                  <tr key={row.id} className="border-b border-terminal-border/60">
                    <td className="py-2 pr-3 text-terminal-text-muted tabular-nums">{row.time}</td>
                    <td className="py-2 pr-3 text-terminal-text">{row.type}</td>
                    <td className="py-2 pr-3 text-terminal-text">{row.timeline}</td>
                    <td className={`py-2 pr-3 font-semibold ${s.text}`}>{row.severity}</td>
                    <td className="py-2 pr-3 text-terminal-text-secondary">{row.resolution}</td>
                    <td className="py-2 pr-3 text-terminal-text-secondary">{row.impact}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {history.length === 0 ? (
            <div className="text-xs text-terminal-text-muted py-6 text-center">No history available</div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
