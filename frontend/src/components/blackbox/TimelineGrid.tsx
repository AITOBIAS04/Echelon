// Timeline Health Grid Component
// Display timeline events with health status

import type { TimelineEvent } from '../../types/blackbox';

interface TimelineGridProps {
  timelines: TimelineEvent[];
}

const TYPE_STYLES: Record<string, { bg: string; text: string; icon: string }> = {
  fork: { bg: 'var(--status-paradox-bg)', text: 'var(--status-paradox)', icon: '🔀' },
  market: { bg: 'var(--status-info-bg)', text: 'var(--status-info)', icon: '📈' },
  sabotage: { bg: 'var(--status-danger-bg)', text: 'var(--status-danger)', icon: '💀' },
  shield: { bg: 'var(--status-success-bg)', text: 'var(--status-success)', icon: '🛡️' },
};

const STATUS_STYLES: Record<string, { bg: string; text: string }> = {
  active: { bg: 'var(--status-success-bg)', text: 'var(--status-success)' },
  warning: { bg: 'var(--status-warning-bg)', text: '#854d0e' },
  collapsed: { bg: 'var(--status-danger-bg)', text: 'var(--status-danger)' },
  settled: { bg: 'var(--status-info-bg)', text: 'var(--status-info)' },
};

export function TimelineGrid({ timelines }: TimelineGridProps) {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
        gap: 16,
        overflow: 'auto',
        padding: 16,
      }}
    >
      {timelines.map((timeline) => {
        const typeStyle = TYPE_STYLES[timeline.type] || TYPE_STYLES.market;
        const statusStyle = STATUS_STYLES[timeline.status] || STATUS_STYLES.active;
        const probColor = timeline.probability > 0.5 ? 'var(--status-success)' : 'var(--text-secondary)';

        return (
          <div
            key={timeline.id}
            className="panel"
            style={{ cursor: 'pointer' }}
          >
            <div className="panel-header" style={{ padding: '12px 16px' }}>
              <span className="panel-title" style={{ fontSize: 11 }}>{timeline.id}</span>
              <span
                style={{
                  fontSize: 9,
                  padding: '2px 6px',
                  background: statusStyle.bg,
                  color: statusStyle.text,
                  borderRadius: 4,
                  fontWeight: 600,
                  textTransform: 'uppercase',
                }}
              >
                {timeline.status}
              </span>
            </div>
            <div style={{ padding: 16 }}>
              <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>{timeline.title}</div>
              <div
                style={{
                  display: 'flex',
                  gap: 16,
                  fontSize: 11,
                  color: 'var(--text-secondary)',
                  marginBottom: 12,
                }}
              >
                <span>
                  Prob: <span style={{ color: probColor, fontWeight: 500 }}>{(timeline.probability * 100).toFixed(0)}%</span>
                </span>
                <span>ETA: {timeline.timeRemaining}</span>
                <span>{timeline.forks} forks</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 20 }}>{typeStyle.icon}</span>
                <span
                  style={{
                    fontSize: 10,
                    padding: '3px 8px',
                    background: typeStyle.bg,
                    color: typeStyle.text,
                    borderRadius: 4,
                    fontWeight: 600,
                    textTransform: 'uppercase',
                  }}
                >
                  {timeline.type}
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
