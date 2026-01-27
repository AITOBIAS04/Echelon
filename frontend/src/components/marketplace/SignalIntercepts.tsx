import { useState } from 'react';
import { Activity } from 'lucide-react';
import { clsx } from 'clsx';
import type { Intercept } from '../../types/marketplace';

interface SignalInterceptsProps {
  intercepts: Intercept[];
  onViewAll?: () => void;
  onInterceptClick?: (intercept: Intercept) => void;
}

/**
 * Get agent icon
 */
function getAgentIcon(agent: string): string {
  const icons: Record<string, string> = {
    CARDINAL: '🕵️',
    MEGALODON: '🦈',
    CHAMELEON: '🎭',
    VULTURE: '🎯',
    MEDUSA: '🐍',
    ATLAS: '🌍',
    PHANTOM: '👻',
    NEXUS: '🔮',
  };

  return icons[agent] || '🤖';
}

/**
 * Get action button style
 */
function getActionStyle(action: string): string {
  const styles: Record<string, string> = {
    Theatre: 'text-status-info hover:bg-status-info/10 border-status-info/30',
    Trade: 'text-status-success hover:bg-status-success/10 border-status-success/30',
    Shield: 'text-status-warning hover:bg-status-warning/10 border-status-warning/30',
    Adjust: 'text-status-paradox hover:bg-status-paradox/10 border-status-paradox/30',
    Verify: 'text-cyan-400 hover:bg-cyan-400/10 border-cyan-400/30',
    Monitor: 'text-terminal-muted hover:bg-terminal-bg border-terminal-border',
  };

  return styles[action] || styles.Monitor;
}

/**
 * SignalIntercepts Component
 * 
 * Sidebar panel showing real-time signal intercepts from AI agents:
 * - Agent name and icon
 * - Timestamp
 * - Theatre and content
 * - Action buttons
 */
export function SignalIntercepts({ intercepts, onViewAll, onInterceptClick }: SignalInterceptsProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (intercepts.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-col border-b border-terminal-border">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-terminal-panel/95 backdrop-blur-sm px-4 py-3 border-b border-terminal-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-status-success animate-pulse" />
            <span className="text-xs font-bold text-terminal-text uppercase tracking-wider">
              Signal Intercepts
            </span>
            <span className="flex items-center gap-1 px-1.5 py-0.5 bg-status-danger/20 border border-status-danger/30 rounded text-[9px] font-bold text-status-danger uppercase">
              <span className="w-1 h-1 bg-status-danger rounded-full animate-pulse" />
              LIVE
            </span>
          </div>
          {onViewAll && (
            <button
              onClick={onViewAll}
              className="text-[10px] text-status-info hover:underline"
            >
              Full Feed →
            </button>
          )}
        </div>
      </div>

      {/* Intercepts List */}
      <div className="flex-1 overflow-y-auto">
        {intercepts.map((intercept, index) => {
          const isExpanded = expandedId === intercept.id;
          const agentIcon = getAgentIcon(intercept.agent);

          return (
            <div
              key={intercept.id || index}
              className={clsx(
                'border-b border-terminal-border last:border-b-0',
                'transition-colors hover:bg-terminal-card/50 cursor-pointer',
                isExpanded && 'bg-terminal-card/50'
              )}
              onClick={() => {
                setExpandedId(isExpanded ? null : (intercept.id || String(index)));
                onInterceptClick?.(intercept);
              }}
            >
              <div className="p-3">
                {/* Header: Agent + Time */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm">{agentIcon}</span>
                    <span className="text-xs font-bold font-mono text-terminal-text">
                      {intercept.agent}
                    </span>
                    <span className="text-[10px] text-terminal-muted px-1.5 py-0.5 bg-terminal-bg rounded border border-terminal-border">
                      {intercept.theatre}
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-terminal-muted">
                    {intercept.time}
                  </span>
                </div>

                {/* Content */}
                <p className="text-xs text-terminal-secondary leading-relaxed mb-3">
                  {intercept.content}
                </p>

                {/* Actions */}
                <div className="flex items-center gap-1.5">
                  {intercept.actions.map((action, actionIndex) => (
                    <button
                      key={actionIndex}
                      onClick={(e) => {
                        e.stopPropagation();
                        // Handle action click
                      }}
                      className={clsx(
                        'px-2 py-1 text-[10px] font-medium uppercase tracking-wider rounded border transition-all',
                        getActionStyle(action)
                      )}
                    >
                      {action}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Source Footer */}
      <div className="px-4 py-2 bg-terminal-bg border-t border-terminal-border">
        <p className="text-[10px] text-center font-mono text-terminal-muted">
          SRC: OSINT / SENSORS / ON-CHAIN
        </p>
      </div>
    </div>
  );
}
