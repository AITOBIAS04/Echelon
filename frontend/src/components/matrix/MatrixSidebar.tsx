import { clsx } from 'clsx';
import type { MatrixRow } from '../../hooks/useAgentMatrix';

// ── Strategy Distribution ───────────────────────────────────────────

function StrategyDistribution({ counts }: { counts: { AGGRESSIVE: number; BALANCED: number; DEFENSIVE: number } }) {
  const total = counts.AGGRESSIVE + counts.BALANCED + counts.DEFENSIVE;
  if (total === 0) {
    return (
      <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] p-4 shadow-[var(--e-shadow-xs)]">
        <h3 className="mb-3 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
          Strategy Distribution
        </h3>
        <p className="text-[12px] text-[var(--e-text-disabled)]">No active deployments</p>
      </div>
    );
  }

  const segments: { label: string; count: number; color: string; bgClass: string }[] = [
    { label: 'Aggressive', count: counts.AGGRESSIVE, color: 'bg-[var(--status-danger)]', bgClass: 'bg-[var(--e-red-50)]' },
    { label: 'Balanced', count: counts.BALANCED, color: 'bg-[var(--e-purple-500)]', bgClass: 'bg-[var(--e-purple-50)]' },
    { label: 'Defensive', count: counts.DEFENSIVE, color: 'bg-[var(--e-green-500)]', bgClass: 'bg-[var(--e-green-50)]' },
  ];

  return (
    <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] p-4 shadow-[var(--e-shadow-xs)]">
      <h3 className="mb-3 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
        Strategy Distribution
      </h3>

      {/* Stacked bar */}
      <div className="mb-3 flex h-2 overflow-hidden rounded-full bg-[var(--e-bg-sunken)]">
        {segments.map((s) =>
          s.count > 0 ? (
            <div
              key={s.label}
              className={clsx('h-full transition-all', s.color)}
              style={{ width: `${(s.count / total) * 100}%` }}
            />
          ) : null,
        )}
      </div>

      {/* Legend */}
      <div className="space-y-1.5">
        {segments.map((s) => (
          <div key={s.label} className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className={clsx('inline-block h-2.5 w-2.5 rounded-sm', s.color)} />
              <span className="text-[12px] font-medium text-[var(--e-text-secondary)]">{s.label}</span>
            </div>
            <span className="font-mono text-[12px] font-semibold tabular-nums text-[var(--e-text-primary)]">
              {s.count}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Recent Activity ─────────────────────────────────────────────────

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function RecentActivity({ rows }: { rows: MatrixRow[] }) {
  // Build activity entries from deployment timestamps, most recent first
  const entries = rows
    .flatMap((r) => {
      const items: { label: string; agent: string; time: string }[] = [];
      if (r.deployment.deployed_at) {
        items.push({ label: 'Deployed', agent: r.agentName, time: r.deployment.deployed_at });
      }
      return items;
    })
    .sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime())
    .slice(0, 8);

  if (entries.length === 0) {
    return (
      <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] p-4 shadow-[var(--e-shadow-xs)]">
        <h3 className="mb-3 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
          Recent Activity
        </h3>
        <p className="text-[12px] text-[var(--e-text-disabled)]">No recent events</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] p-4 shadow-[var(--e-shadow-xs)]">
      <h3 className="mb-3 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
        Recent Activity
      </h3>
      <div className="space-y-2">
        {entries.map((e, i) => (
          <div key={i} className="flex items-center justify-between gap-2">
            <div className="min-w-0 flex-1">
              <span className="text-[12px] font-medium text-[var(--e-text-primary)]">{e.agent}</span>
              <span className="ml-1 text-[11px] text-[var(--e-text-muted)]">{e.label.toLowerCase()}</span>
            </div>
            <span className="whitespace-nowrap font-mono text-[10px] text-[var(--e-text-disabled)]">
              {relativeTime(e.time)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Sidebar composite ───────────────────────────────────────────────

export function MatrixSidebar({
  rows,
  strategyDistribution,
}: {
  rows: MatrixRow[];
  strategyDistribution: { AGGRESSIVE: number; BALANCED: number; DEFENSIVE: number };
}) {
  return (
    <div className="space-y-4">
      <StrategyDistribution counts={strategyDistribution} />
      <RecentActivity rows={rows} />
    </div>
  );
}
