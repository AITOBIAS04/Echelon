import { useEffect, useMemo } from "react";
import { Download, Database, Settings2, Activity } from "lucide-react";
import { useDemoEnabled, useDemoExports } from "../demo/hooks";
import { demoStore } from "../demo/demoStore";

const STATIC_EXPORTS = [
  {
    id: "e1",
    partner: "Boston Dynamics",
    status: "PROCESSING" as const,
    theatre: "orbital_salvage_v1",
    episodes: 1247,
    samplingRate: 0.5,
    format: "PyTorch (.pt)" as const,
    sizeGb: 2.4,
    progress: 68,
    etaSec: 192,
  },
  {
    id: "e2",
    partner: "Agility Robotics",
    status: "QUEUED" as const,
    theatre: "warehouse_pick_v3",
    episodes: 802,
    samplingRate: 0.4,
    format: "ROS Bag (.bag)" as const,
    sizeGb: 1.1,
    progress: 0,
    etaSec: 0,
  },
  {
    id: "e3",
    partner: "Covariant.ai",
    status: "PROCESSING" as const,
    theatre: "dock_sort_v2",
    episodes: 2150,
    samplingRate: 0.6,
    format: "TFRecord (.tfrecord)" as const,
    sizeGb: 3.7,
    progress: 41,
    etaSec: 420,
  },
];

const STATIC_PARTNERS = [
  { name: "Boston Dynamics", access: "Premium" as const, exports30d: 124, dataVolumeGb: 84, status: "Active" as const },
  { name: "Agility Robotics", access: "Standard" as const, exports30d: 87, dataVolumeGb: 52, status: "Active" as const },
  { name: "Covariant.ai", access: "Premium" as const, exports30d: 215, dataVolumeGb: 128, status: "Active" as const },
];

function fmtEta(sec: number) {
  if (!sec) return "—";
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m}m ${s}s`;
}

export function ExportConsolePage() {
  const demoEnabled = useDemoEnabled();
  const demo = useDemoExports();

  // Optional: seed exports once if engine does not seed.
  useEffect(() => {
    if (!demoEnabled) return;
    if (demo.active.length > 0 || demo.partners.length > 0) return;

    demoStore.setExports(STATIC_EXPORTS);
  }, [demoEnabled, demo.active.length, demo.partners.length]);

  const active = demoEnabled && demo.active.length ? demo.active : STATIC_EXPORTS;
  const partners = demoEnabled && demo.partners.length ? demo.partners : STATIC_PARTNERS;
  const config = demoEnabled ? demo.config : { samplingRate: 0.5, format: "PyTorch (.pt)", compression: "GZIP" as const };

  const metrics = useMemo(() => {
    return {
      totalExports: 1847,
      dataVolume: "428GB",
      partnerCount: 7,
      successRate: "98.2%",
    };
  }, []);

  return (
    <div className="h-full flex flex-col gap-4">
      <div className="flex items-center justify-between flex-shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-terminal-text uppercase tracking-wide">Export Console</h1>
          <p className="text-sm text-terminal-text-secondary mt-1">
            Manage RLMF exports, partner access, and pipeline configuration
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 min-h-0">
        {/* Active exports */}
        <div className="xl:col-span-2 bg-terminal-panel border border-terminal-border rounded-lg p-4 min-h-0 flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Download className="w-4 h-4 text-status-entropy" />
              <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide">
                Active Exports ({active.length})
              </h3>
            </div>
          </div>

          <div className="flex-1 min-h-0 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent space-y-3 pr-1">
            {active.map((x: any) => (
              <div key={x.id} className="bg-terminal-card border border-terminal-border rounded-lg p-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-semibold text-terminal-text">{x.partner}</span>
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                        x.status === "PROCESSING"
                          ? "bg-status-info/10 border-status-info/25 text-status-info"
                          : x.status === "QUEUED"
                          ? "bg-terminal-bg border-terminal-border text-terminal-text-muted"
                          : x.status === "COMPLETED"
                          ? "bg-status-success/10 border-status-success/25 text-status-success"
                          : "bg-status-danger/10 border-status-danger/25 text-status-danger"
                      }`}>
                        {x.status}
                      </span>
                    </div>

                    <div className="mt-2 text-xs text-terminal-text-secondary space-y-0.5">
                      <div>Theatre: <span className="text-terminal-text">{x.theatre}</span></div>
                      <div>Episodes: <span className="text-terminal-text tabular-nums">{x.episodes.toLocaleString("en-GB")}</span> (Sampling: <span className="text-terminal-text tabular-nums">{Math.round(x.samplingRate * 100)}%</span>)</div>
                      <div>Format: <span className="text-terminal-text">{x.format}</span></div>
                      <div>Size: <span className="text-terminal-text tabular-nums">{x.sizeGb.toFixed(1)}GB</span> • ETA: <span className="text-terminal-text tabular-nums">{fmtEta(x.etaSec)}</span></div>
                    </div>
                  </div>

                  <div className="w-[220px] flex-shrink-0">
                    <div className="flex items-center justify-between text-xs text-terminal-text-muted">
                      <span className="flex items-center gap-1">
                        <Activity className="w-3.5 h-3.5" />
                        Progress
                      </span>
                      <span className="tabular-nums">{x.progress}%</span>
                    </div>
                    <div className="mt-1 h-2 rounded bg-terminal-bg border border-terminal-border overflow-hidden">
                      <div
                        className="h-full bg-status-entropy/70"
                        style={{ width: `${Math.max(0, Math.min(100, x.progress))}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Metrics + Config */}
        <div className="space-y-4">
          <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <Database className="w-4 h-4 text-status-info" />
              <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide">Export Metrics</h3>
            </div>

            <div className="grid grid-cols-2 gap-3">
              {[
                { label: "Total Exports", value: metrics.totalExports.toLocaleString("en-GB") },
                { label: "Data Volume", value: metrics.dataVolume },
                { label: "Partner Count", value: String(metrics.partnerCount) },
                { label: "Success Rate", value: metrics.successRate, accent: "text-status-success" },
              ].map((m) => (
                <div key={m.label} className="bg-terminal-card border border-terminal-border rounded-lg p-3">
                  <div className="text-xs text-terminal-text-muted">{m.label}</div>
                  <div className={`mt-1 text-base font-semibold tabular-nums ${m.accent ?? "text-terminal-text"}`}>
                    {m.value}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <Settings2 className="w-4 h-4 text-terminal-text-muted" />
              <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide">Export Configuration</h3>
            </div>

            <div className="space-y-3">
              <div className="bg-terminal-card border border-terminal-border rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <div className="text-xs text-terminal-text-muted">Default sampling rate</div>
                  <div className="text-xs text-terminal-text tabular-nums">{Math.round(config.samplingRate * 100)}%</div>
                </div>
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.1}
                  value={config.samplingRate}
                  onChange={(e) => {
                    if (!demoEnabled) return;
                    const next = Number(e.target.value);
                    // @ts-expect-error after store extension
                    demoStore.setExportConfig({ ...config, samplingRate: next });
                  }}
                  className="mt-2 w-full"
                />
              </div>

              <div className="bg-terminal-card border border-terminal-border rounded-lg p-3">
                <div className="text-xs text-terminal-text-muted mb-1">Default format</div>
                <select
                  value={config.format}
                  onChange={(e) => {
                    if (!demoEnabled) return;
                    demoStore.setExportConfig({ ...config, format: e.target.value as "PyTorch (.pt)" | "ROS Bag (.bag)" | "TFRecord (.tfrecord)" | "JSON (Canonical)" });
                  }}
                  className="w-full bg-terminal-bg border border-terminal-border rounded px-2 py-2 text-xs text-terminal-text"
                >
                  <option>PyTorch (.pt)</option>
                  <option>ROS Bag (.bag)</option>
                  <option>TFRecord (.tfrecord)</option>
                  <option>JSON (Canonical)</option>
                </select>
              </div>

              <div className="bg-terminal-card border border-terminal-border rounded-lg p-3">
                <div className="text-xs text-terminal-text-muted mb-1">Compression</div>
                <select
                  value={config.compression}
                  onChange={(e) => {
                    if (!demoEnabled) return;
                    // @ts-expect-error
                    demoStore.setExportConfig({ ...config, compression: e.target.value as any });
                  }}
                  className="w-full bg-terminal-bg border border-terminal-border rounded px-2 py-2 text-xs text-terminal-text"
                >
                  <option>GZIP</option>
                  <option>None</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Partners */}
      <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4 min-h-0">
        <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide mb-3">Robotics Partners</h3>
        <div className="max-h-[240px] overflow-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
<table className="w-full text-xs">
            <thead className="text-terminal-text-muted">
              <tr className="border-b border-terminal-border">
                <th className="text-left py-2 pr-3 font-medium">Partner</th>
                <th className="text-left py-2 pr-3 font-medium">Access</th>
                <th className="text-left py-2 pr-3 font-medium">Exports (30d)</th>
                <th className="text-left py-2 pr-3 font-medium">Data volume</th>
                <th className="text-left py-2 pr-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {partners.map((p: any) => (
                <tr key={p.name} className="border-b border-terminal-border/60">
                  <td className="py-2 pr-3 text-terminal-text">{p.name}</td>
                  <td className="py-2 pr-3 text-terminal-text-secondary">{p.access}</td>
                  <td className="py-2 pr-3 text-terminal-text-secondary tabular-nums">{p.exports30d}</td>
                  <td className="py-2 pr-3 text-terminal-text-secondary tabular-nums">{p.dataVolumeGb}GB</td>
                  <td className={`py-2 pr-3 font-semibold ${p.status === "Active" ? "text-status-success" : "text-terminal-text-muted"}`}>
                    {p.status}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
