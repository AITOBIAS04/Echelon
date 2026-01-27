// Signal Intercepts Panel Component
// Real-time signal intelligence display

import type { Intercept } from '../../types/blackbox';

interface SignalInterceptsPanelProps {
  intercepts: Intercept[];
}

const SEVERITY_STYLES = {
  critical: { bg: 'var(--status-danger-bg)', border: 'var(--status-danger)', text: 'var(--status-danger)' },
  warning: { bg: 'var(--status-warning-bg)', border: 'var(--status-warning)', text: 'var(--status-warning)' },
  info: { bg: 'var(--status-info-bg)', border: 'var(--status-info)', text: 'var(--status-info)' },
  success: { bg: 'var(--status-success-bg)', border: 'var(--status-success)', text: 'var(--status-success)' },
};

export function SignalInterceptsPanel({ intercepts }: SignalInterceptsPanelProps) {
  const formatTime = (date: Date) => {
    return date.toISOString().substr(11, 8);
  };

  return (
    <div className="panel" style={{ flex: 1, minHeight: 0 }}>
      <div className="panel-header">
        <span className="panel-title">SIGNAL INTERCEPTS</span>
        <span
          style={{
            fontSize: 9,
            padding: '2px 6px',
            background: 'var(--status-danger-bg)',
            color: 'var(--status-danger)',
            borderRadius: 4,
            fontWeight: 600,
          }}
        >
          LIVE
        </span>
      </div>
      <div className="intercepts-panel" style={{ flex: 1, overflow: 'auto', padding: 8 }}>
        {intercepts.map((intercept) => {
          const style = SEVERITY_STYLES[intercept.severity];
          const iconBg = style.bg;

          return (
            <div
              key={intercept.id}
              className="intercept-item"
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: 10,
                padding: 10,
                borderRadius: 'var(--radius-md)',
                marginBottom: 4,
                borderLeft: `3px solid ${style.border}`,
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
            >
              <div
                className="intercept-icon"
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: 6,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 14,
                  flexShrink: 0,
                  background: iconBg,
                }}
              >
                {intercept.icon}
              </div>
              <div className="intercept-content" style={{ flex: 1, minWidth: 0 }}>
                <div
                  className="intercept-header"
                  style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 2 }}
                >
                  <span className="intercept-title" style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-primary)' }}>
                    {intercept.title}
                  </span>
                  <span className="intercept-time mono" style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                    {formatTime(intercept.timestamp)}
                  </span>
                </div>
                <div className="intercept-details" style={{ fontSize: 10, color: 'var(--text-secondary)', marginTop: 2 }}>
                  {intercept.details}
                </div>
                <div className="intercept-meta" style={{ display: 'flex', gap: 8, marginTop: 4, fontSize: 9, color: 'var(--text-muted)' }}>
                  <span>Source: {intercept.source}</span>
                  <span
                    className="intercept-tag"
                    style={{
                      padding: '1px 5px',
                      background: 'var(--bg-app)',
                      borderRadius: 3,
                      textTransform: 'uppercase',
                      fontWeight: 600,
                      color: style.text,
                    }}
                  >
                    {intercept.severity}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
