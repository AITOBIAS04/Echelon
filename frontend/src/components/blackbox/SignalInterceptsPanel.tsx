// Signal Intercepts Panel Component
// Real-time signal intelligence display

import type { Intercept } from '../../types/blackbox';

interface SignalInterceptsPanelProps {
  intercepts: Intercept[];
}

const SEVERITY_STYLES = {
  critical: { bg: 'rgba(251, 113, 133, 0.15)', border: '#FB7185', text: '#FB7185' },
  warning: { bg: 'rgba(251, 191, 36, 0.15)', border: '#FBBF24', text: '#FBBF24' },
  info: { bg: 'rgba(59, 130, 246, 0.15)', border: '#3B82F6', text: '#3B82F6' },
  success: { bg: 'rgba(74, 222, 128, 0.15)', border: '#4ADE80', text: '#4ADE80' },
};

export function SignalInterceptsPanel({ intercepts }: SignalInterceptsPanelProps) {
  const formatTime = (date: Date) => {
    return date.toISOString().substr(11, 8);
  };

  return (
    <div className="terminal-panel rounded-2xl flex flex-col min-h-0">
      {/* Card Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-terminal-border">
        <span className="text-sm font-semibold text-terminal-text">SIGNAL INTERCEPTS</span>
        <span className="px-1.5 py-0.5 text-[9px] font-semibold bg-echelon-red/15 text-echelon-red rounded">
          LIVE
        </span>
      </div>

      {/* Intercepts List */}
      <div className="flex-1 min-h-0 overflow-y-auto pr-1">
        <div className="p-2 space-y-2">
          {intercepts.map((intercept) => {
            const style = SEVERITY_STYLES[intercept.severity];

            return (
              <div
                key={intercept.id}
                className="flex items-start gap-2.5 p-2.5 rounded-lg border-l-2 cursor-pointer hover:bg-terminal-hover transition-colors"
                style={{
                  borderLeftColor: style.border,
                  background: style.bg,
                }}
              >
                {/* Icon */}
                <div
                  className="w-7 h-7 rounded flex items-center justify-center text-sm flex-shrink-0"
                  style={{ background: style.bg }}
                >
                  {intercept.icon}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="text-xs font-semibold text-terminal-text">{intercept.title}</span>
                    <span className="text-[10px] font-mono text-terminal-text-muted flex-shrink-0">
                      {formatTime(intercept.timestamp)}
                    </span>
                  </div>
                  <div className="text-[10px] text-terminal-text-secondary mt-0.5">{intercept.details}</div>
                  <div className="flex items-center gap-2 mt-1.5 text-[9px] text-terminal-text-muted">
                    <span>Source: {intercept.source}</span>
                    <span
                      className="px-1 py-0.5 rounded font-semibold uppercase"
                      style={{
                        background: 'rgba(15, 17, 19, 0.5)',
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
    </div>
  );
}
