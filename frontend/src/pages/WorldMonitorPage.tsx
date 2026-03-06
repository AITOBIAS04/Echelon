/**
 * WorldMonitorPage — Aggregated world view of all timelines.
 *
 * Shows timeline health, gravity trends, and activity feed.
 * Uses QUIET_MONITORING empty state when all is calm.
 */

import { Activity, Globe } from 'lucide-react';
import { clsx } from 'clsx';
import { useNavigate } from 'react-router-dom';
import { useWorldMonitor } from '../hooks/useWorldMonitor';
import { EmptyState } from '../components/empty-states/EmptyState';

export function WorldMonitorPage() {
  const navigate = useNavigate();
  const { timelines, recentActivity, stats, isLoading, error, isQuiet, isEmpty } =
    useWorldMonitor();

  if (error) {
    return (
      <div className="p-6 text-status-danger text-sm">
        Failed to load world monitor: {error.message}
      </div>
    );
  }

  if (isEmpty) {
    return (
      <EmptyState
        type="ZERO_STATE"
        icon={<Globe className="w-7 h-7" />}
        title="No timelines yet"
        description="Timelines appear here once theatres are running. Create a theatre to begin monitoring."
        actions={[
          {
            label: 'Create Theatre',
            onClick: () => navigate('/theatres/create'),
            variant: 'primary',
          },
        ]}
      />
    );
  }

  if (isQuiet && !isLoading) {
    return (
      <EmptyState
        type="QUIET_MONITORING"
        description="All timelines stable. Monitoring for gravity shifts and paradox activity."
        context={
          <div className="w-full h-full p-6 opacity-60">
            {/* Skeleton map: simplified node grid */}
            <div className="grid grid-cols-4 gap-8 p-8">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="flex flex-col items-center gap-2">
                  <div className="w-12 h-12 rounded-full bg-terminal-panel border border-terminal-border" />
                  <div className="w-16 h-2 rounded bg-terminal-panel" />
                </div>
              ))}
            </div>
          </div>
        }
      />
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Stats strip */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Timelines', value: stats.totalTimelines },
          { label: 'Active Paradoxes', value: stats.activeParadoxes },
          { label: 'Avg Stability', value: `${stats.avgStability.toFixed(1)}%` },
          { label: 'High Gravity', value: stats.highGravityCount },
        ].map((s) => (
          <div
            key={s.label}
            className="bg-terminal-surface border border-terminal-border rounded-lg p-4"
          >
            <div className="text-[10px] font-bold uppercase tracking-wider text-terminal-text-muted mb-1">
              {s.label}
            </div>
            <div className="text-xl font-bold text-terminal-text">{s.value}</div>
          </div>
        ))}
      </div>

      {/* Timeline grid */}
      <div>
        <h2 className="text-sm font-bold text-terminal-text mb-3">All Timelines</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {timelines.map((tl) => (
            <div
              key={tl.id}
              className={clsx(
                'bg-terminal-surface border rounded-lg p-4',
                tl.has_active_paradox
                  ? 'border-status-paradox/30'
                  : 'border-terminal-border',
              )}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-semibold text-terminal-text truncate">
                  {tl.name}
                </span>
                {tl.has_active_paradox && (
                  <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-status-paradox/10 text-status-paradox border border-status-paradox/20">
                    Paradox
                  </span>
                )}
              </div>
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div>
                  <span className="text-terminal-text-muted">Stability</span>
                  <div className="font-mono font-bold text-terminal-text">
                    {tl.stability.toFixed(1)}%
                  </div>
                </div>
                <div>
                  <span className="text-terminal-text-muted">Gravity</span>
                  <div className="font-mono font-bold text-terminal-text">
                    {tl.gravity_score}
                  </div>
                </div>
                <div>
                  <span className="text-terminal-text-muted">Logic Gap</span>
                  <div className="font-mono font-bold text-terminal-text">
                    {(tl.logic_gap * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent activity */}
      {recentActivity.length > 0 && (
        <div>
          <h2 className="text-sm font-bold text-terminal-text mb-3 flex items-center gap-2">
            <Activity className="w-4 h-4 text-terminal-text-muted" />
            Recent Activity
          </h2>
          <div className="space-y-1">
            {recentActivity.slice(0, 10).map((flap) => (
              <div
                key={flap.id}
                className="flex items-center gap-3 px-3 py-2 bg-terminal-surface border border-terminal-border rounded text-xs"
              >
                <span className="font-mono text-terminal-text-muted">
                  {flap.agent_name}
                </span>
                <span className="text-terminal-text-secondary">{flap.action}</span>
                <span className="text-terminal-text-muted truncate">{flap.timeline_name}</span>
                <span className="ml-auto font-mono text-terminal-text-muted">
                  ${flap.volume_usd.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
