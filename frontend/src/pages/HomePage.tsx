/**
 * HomePage — Aggregation Dashboard
 *
 * 4 summary cards + activity feed from real endpoints.
 * Sources: timelines, paradoxes, investigations, agents, recent wing flaps.
 */

import { useOpsBoard } from '../hooks/useOpsBoard';
import { EmptyState } from '../components/empty-states/EmptyState';

function SummaryCard({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: string | number;
  sub?: string;
  accent?: string;
}) {
  return (
    <div className="bg-terminal-panel border border-terminal-border rounded-xl p-4">
      <div className="text-[10px] text-terminal-text-muted uppercase tracking-wider font-semibold mb-2">
        {label}
      </div>
      <div className={`text-2xl font-mono font-bold ${accent ?? 'text-terminal-text'}`}>
        {value}
      </div>
      {sub && <div className="text-xs text-terminal-text-muted mt-1">{sub}</div>}
    </div>
  );
}

function formatTimeAgo(isoTimestamp: string): string {
  const diff = Date.now() - new Date(isoTimestamp).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return 'now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export function HomePage() {
  const { data, loading, error } = useOpsBoard();

  if (loading) {
    return (
      <div className="p-6 text-terminal-text-muted text-xs">
        Loading dashboard...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 text-status-danger text-xs">
        Failed to load dashboard: {error}
      </div>
    );
  }

  if (!data) return null;

  const stabilityPct = Math.round(data.timelines.avgStability * 100);
  const stabilityColor =
    stabilityPct >= 70
      ? 'text-status-success'
      : stabilityPct >= 40
        ? 'text-status-warning'
        : 'text-status-danger';

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard
          label="Active Timelines"
          value={data.timelines.active}
          sub={`${data.timelines.total} total · ${data.timelines.withParadox} with paradox`}
        />
        <SummaryCard
          label="Avg Stability"
          value={`${stabilityPct}%`}
          sub="Across active timelines"
          accent={stabilityColor}
        />
        <SummaryCard
          label="Active Paradoxes"
          value={data.paradoxes.totalActive}
          sub={`${data.agents.alive} agents alive`}
          accent={data.paradoxes.totalActive > 0 ? 'text-status-danger' : 'text-status-success'}
        />
        <SummaryCard
          label="Investigations"
          value={data.investigations.total}
          sub="Active investigations"
        />
      </div>

      {/* Activity Feed */}
      <div className="bg-terminal-panel border border-terminal-border rounded-xl overflow-hidden">
        <div className="px-4 py-3 bg-terminal-bg/50 border-b border-terminal-border">
          <span className="text-xs font-semibold text-terminal-text uppercase tracking-wider">
            Recent Activity
          </span>
        </div>
        <div className="divide-y divide-terminal-border/50">
          {data.recentFlaps.length === 0 ? (
            data.paradoxes.totalActive === 0 ? (
              <EmptyState
                type="ALL_CLEAR"
                description="All systems nominal. No active paradoxes or recent agent activity."
                timestamp={new Date().toLocaleTimeString()}
              />
            ) : (
              <div className="px-4 py-8 text-center text-xs text-terminal-text-muted">
                No recent activity.
              </div>
            )
          ) : (
            data.recentFlaps.map((flap) => (
              <div
                key={flap.id ?? `${flap.timeline_id}-${flap.timestamp}`}
                className="px-4 py-3 flex items-center gap-3 hover:bg-terminal-bg/30 transition-colors"
              >
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-echelon-cyan/10 text-echelon-cyan uppercase">
                  {flap.flap_type}
                </span>
                <span className="text-xs text-terminal-text flex-1 truncate">
                  {flap.action}
                </span>
                <span className="text-[10px] text-terminal-text-muted font-mono">
                  {flap.timeline_name}
                </span>
                <span className="text-[10px] text-terminal-text-muted font-mono whitespace-nowrap">
                  {formatTimeAgo(flap.timestamp)}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
