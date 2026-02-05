import { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  CheckCircle,
  XCircle,
  Bot,
  Wallet,
  Plus,
  Minus,
  AlertTriangle,
  Play,
} from 'lucide-react';
import type { Breach } from '../../types/breach';

/**
 * BreachDetail Props
 */
export interface BreachDetailProps {
  /** Breach data to display */
  breach: Breach;
  /** Callback when an action is executed */
  onAction?: (actionId: string) => void;
  /** Callback when breach is marked as resolved */
  onResolve?: () => void;
}

/**
 * Get severity badge styling
 */
function getSeverityStyles(severity: Breach['severity']) {
  switch (severity) {
    case 'critical':
      return {
        bg: 'bg-red-500/20',
        border: 'border-red-500',
        text: 'text-red-500',
        pulse: 'animate-pulse',
      };
    case 'high':
      return {
        bg: 'bg-orange-500/20',
        border: 'border-orange-500',
        text: 'text-orange-500',
        pulse: '',
      };
    case 'medium':
      return {
        bg: 'bg-amber-500/20',
        border: 'border-amber-500',
        text: 'text-amber-500',
        pulse: '',
      };
    case 'low':
      return {
        bg: 'bg-gray-500/20',
        border: 'border-gray-500',
        text: 'text-gray-500',
        pulse: '',
      };
  }
}

/**
 * Get status badge color
 */
function getStatusColor(status: Breach['status']): string {
  switch (status) {
    case 'active':
      return '#FF3B3B'; // red
    case 'investigating':
      return '#FF9500'; // amber
    case 'mitigated':
      return '#22D3EE'; // cyan
    case 'resolved':
      return '#00FF41'; // green
  }
}

/**
 * Format timestamp
 */
function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Collapsible Section Component
 */
function CollapsibleSection({
  title,
  defaultOpen = false,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border-b border-[#1A1A1A]">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between py-3 text-left"
      >
        <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide">
          {title}
        </h3>
        {isOpen ? (
          <ChevronUp className="w-4 h-4 text-terminal-text-muted" />
        ) : (
          <ChevronDown className="w-4 h-4 text-terminal-text-muted" />
        )}
      </button>
      {isOpen && <div className="pb-4">{children}</div>}
    </div>
  );
}

/**
 * BreachDetail Component
 * 
 * Displays comprehensive breach information including affected entities,
 * beneficiaries, evidence changes, and suggested actions.
 */
export function BreachDetail({ breach, onAction, onResolve }: BreachDetailProps) {
  const severityStyles = getSeverityStyles(breach.severity);
  const statusColor = getStatusColor(breach.status);

  // Sort beneficiaries by estimatedGain descending
  const sortedBeneficiaries = [...breach.beneficiaries].sort(
    (a, b) => b.estimatedGain - a.estimatedGain
  );

  return (
    <div className="bg-slate-900 rounded-lg border border-[#1A1A1A] p-4 h-full overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
      {/* Header Section */}
      <div className="border-b border-[#1A1A1A] pb-4 mb-4">
        <div className="flex items-start justify-between gap-4 mb-3">
          <div className="flex items-center gap-3">
            <div
              className={`px-4 py-2 rounded border ${severityStyles.bg} ${severityStyles.border} ${severityStyles.text} ${severityStyles.pulse}`}
            >
              <span className="text-sm font-bold uppercase">{breach.severity}</span>
            </div>
            <div>
              <h2 className="text-xl font-bold text-terminal-text mb-1">{breach.title}</h2>
              <div className="text-xs text-terminal-text-muted">{formatTimestamp(breach.timestamp)}</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span
              className="px-3 py-1 rounded text-xs font-semibold uppercase"
              style={{
                backgroundColor: `${statusColor}20`,
                color: statusColor,
                border: `1px solid ${statusColor}`,
              }}
            >
              {breach.status}
            </span>
            <div className="flex items-center gap-1 text-xs">
              {breach.recoverable ? (
                <>
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span className="text-green-500">Recoverable</span>
                </>
              ) : (
                <>
                  <XCircle className="w-4 h-4 text-red-500" />
                  <span className="text-red-500">Unrecoverable</span>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Description Section */}
      <div className="border-b border-[#1A1A1A] pb-4 mb-4">
        <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide mb-2">
          Description
        </h3>
        <p className="text-sm text-terminal-text mb-4">{breach.description}</p>
        <div>
          <h4 className="text-xs font-semibold text-terminal-text-muted uppercase mb-1">
            Root Cause
          </h4>
          <p className="text-sm text-terminal-text">{breach.rootCause}</p>
        </div>
      </div>

      {/* Affected Timelines Section */}
      <CollapsibleSection title="Affected Timelines" defaultOpen={true}>
        {breach.affectedTimelines.length === 0 ? (
          <p className="text-sm text-terminal-text-muted">No timelines affected</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#1A1A1A]">
                  <th className="text-left py-2 text-terminal-text-muted font-semibold">Timeline</th>
                  <th className="text-left py-2 text-terminal-text-muted font-semibold">
                    Stability
                  </th>
                  <th className="text-left py-2 text-terminal-text-muted font-semibold">
                    Logic Gap
                  </th>
                </tr>
              </thead>
              <tbody>
                {breach.affectedTimelines.map((timeline) => {
                  const stabilityChange =
                    timeline.stabilityAfter - timeline.stabilityBefore;
                  const logicGapChange = timeline.logicGapAfter - timeline.logicGapBefore;

                  return (
                    <tr key={timeline.id} className="border-b border-[#1A1A1A]">
                      <td className="py-2 text-terminal-text font-medium">{timeline.name}</td>
                      <td className="py-2">
                        <span className="text-terminal-text">
                          {timeline.stabilityBefore.toFixed(1)}%
                        </span>
                        <span className="text-terminal-text-muted mx-1">→</span>
                        <span
                          className={
                            stabilityChange >= 0 ? 'text-green-500' : 'text-red-500'
                          }
                        >
                          {timeline.stabilityAfter.toFixed(1)}%
                        </span>
                      </td>
                      <td className="py-2">
                        <span className="text-terminal-text">
                          {timeline.logicGapBefore.toFixed(1)}%
                        </span>
                        <span className="text-terminal-text-muted mx-1">→</span>
                        <span
                          className={logicGapChange <= 0 ? 'text-green-500' : 'text-red-500'}
                        >
                          {timeline.logicGapAfter.toFixed(1)}%
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </CollapsibleSection>

      {/* Affected Agents Section */}
      <CollapsibleSection
        title="Affected Agents"
        defaultOpen={breach.affectedAgents.length > 0}
      >
        {breach.affectedAgents.length === 0 ? (
          <p className="text-sm text-terminal-text-muted">No agents affected</p>
        ) : (
          <div className="space-y-2">
            {breach.affectedAgents.map((agent) => (
              <div
                key={agent.id}
                className="bg-terminal-panel rounded p-3 border border-[#1A1A1A]"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Bot className="w-4 h-4 text-terminal-text-muted" />
                    <span className="text-sm font-medium text-terminal-text">{agent.name}</span>
                    <span
                      className="px-2 py-0.5 rounded text-xs"
                      style={{
                        backgroundColor: '#333',
                        color: '#999',
                      }}
                    >
                      {agent.archetype}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-sm">
                    <div>
                      <span className="text-terminal-text-muted">P&L:</span>{' '}
                      <span
                        className={`font-mono ${
                          agent.pnlImpact >= 0 ? 'text-green-500' : 'text-red-500'
                        }`}
                      >
                        {agent.pnlImpact >= 0 ? '+' : ''}${agent.pnlImpact.toFixed(2)}
                      </span>
                    </div>
                    <div>
                      <span className="text-terminal-text-muted">Sanity:</span>{' '}
                      <span className="font-mono text-red-500">
                        -{agent.sanityImpact} points
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CollapsibleSection>

      {/* Beneficiaries Section */}
      <CollapsibleSection title="Who Benefited" defaultOpen={true}>
        {sortedBeneficiaries.length === 0 ? (
          <p className="text-sm text-terminal-text-muted">No beneficiaries identified</p>
        ) : (
          <div className="space-y-2">
            {sortedBeneficiaries.map((beneficiary, index) => (
              <div
                key={`${beneficiary.type}-${beneficiary.id}-${index}`}
                className="flex items-center gap-3 bg-terminal-panel rounded p-3 border border-[#1A1A1A]"
              >
                {beneficiary.type === 'agent' ? (
                  <Bot className="w-4 h-4 text-terminal-text-muted" />
                ) : (
                  <Wallet className="w-4 h-4 text-terminal-text-muted" />
                )}
                <span className="text-sm text-terminal-text flex-1">{beneficiary.name}</span>
                <span className="text-sm font-mono text-green-500">
                  +${beneficiary.estimatedGain.toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        )}
      </CollapsibleSection>

      {/* Evidence Changes Section */}
      <CollapsibleSection title="Evidence Changes" defaultOpen={true}>
        {breach.evidenceChanges.length === 0 ? (
          <p className="text-sm text-terminal-text-muted">No evidence changes recorded</p>
        ) : (
          <div className="space-y-3">
            {breach.evidenceChanges.map((change, index) => {
              const changeTypeColors = {
                added: { bg: '#00FF41', text: '#00FF41' },
                removed: { bg: '#FF3B3B', text: '#FF3B3B' },
                contradicted: { bg: '#FF9500', text: '#FF9500' },
              };
              const colors = changeTypeColors[change.changeType];

              return (
                <div
                  key={`${change.timestamp}-${index}`}
                  className="flex items-start gap-3 bg-terminal-panel rounded p-3 border border-[#1A1A1A]"
                >
                  <div className="flex-shrink-0">
                    {change.changeType === 'added' ? (
                      <Plus className="w-4 h-4" style={{ color: colors.text }} />
                    ) : change.changeType === 'removed' ? (
                      <Minus className="w-4 h-4" style={{ color: colors.text }} />
                    ) : (
                      <AlertTriangle className="w-4 h-4" style={{ color: colors.text }} />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs text-terminal-text-muted font-mono">
                        {formatTimestamp(change.timestamp)}
                      </span>
                      <span
                        className="px-2 py-0.5 rounded text-xs font-medium"
                        style={{
                          backgroundColor: '#333',
                          color: '#999',
                        }}
                      >
                        {change.source}
                      </span>
                      <span
                        className="px-2 py-0.5 rounded text-xs font-semibold uppercase"
                        style={{
                          backgroundColor: `${colors.bg}20`,
                          color: colors.text,
                        }}
                      >
                        {change.changeType}
                      </span>
                    </div>
                    <p className="text-sm text-terminal-text">{change.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CollapsibleSection>

      {/* Suggested Actions Section */}
      <CollapsibleSection title="Suggested Actions" defaultOpen={true}>
        {breach.suggestedActions.length === 0 ? (
          <p className="text-sm text-terminal-text-muted">No suggested actions</p>
        ) : (
          <div className="space-y-3">
            {breach.suggestedActions.map((action) => {
              const priorityStyles = {
                immediate: {
                  bg: 'bg-red-500/20',
                  border: 'border-red-500',
                  text: 'text-red-500',
                  pulse: 'animate-pulse',
                },
                recommended: {
                  bg: 'bg-amber-500/20',
                  border: 'border-amber-500',
                  text: 'text-amber-500',
                  pulse: '',
                },
                optional: {
                  bg: 'bg-gray-500/20',
                  border: 'border-gray-500',
                  text: 'text-gray-500',
                  pulse: '',
                },
              };
              const styles = priorityStyles[action.priority];

              return (
                <div
                  key={action.id}
                  className="bg-terminal-panel rounded p-3 border border-[#1A1A1A]"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-semibold uppercase ${styles.bg} ${styles.border} ${styles.text} ${styles.pulse}`}
                        >
                          {action.priority}
                        </span>
                      </div>
                      <p className="text-sm text-terminal-text mb-1">{action.action}</p>
                      <p className="text-xs text-terminal-text-muted">
                        Estimated impact: {action.estimatedImpact}
                      </p>
                    </div>
                    {onAction && (
                      <button
                        onClick={() => onAction(action.id)}
                        className="flex items-center gap-1 px-3 py-1.5 bg-[#22D3EE]/20 border border-[#22D3EE] rounded text-xs font-medium text-[#22D3EE] hover:bg-[#22D3EE]/30 transition"
                      >
                        <Play className="w-3 h-3" />
                        Execute
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CollapsibleSection>

      {/* Footer: Resolve Button */}
      {breach.status !== 'resolved' && onResolve && (
        <div className="mt-6 pt-4 border-t border-[#1A1A1A]">
          <button
            onClick={onResolve}
            className="w-full py-3 px-4 bg-green-500/20 border border-green-500 rounded text-sm font-semibold text-green-500 hover:bg-green-500/30 transition"
          >
            Mark as Resolved
          </button>
        </div>
      )}
    </div>
  );
}
