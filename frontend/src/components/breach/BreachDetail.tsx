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
        bg: 'bg-echelon-red/20',
        border: 'border-echelon-red',
        text: 'text-echelon-red',
        pulse: 'animate-pulse',
      };
    case 'high':
      return {
        bg: 'bg-agent-degen/20',
        border: 'border-agent-degen',
        text: 'text-agent-degen',
        pulse: '',
      };
    case 'medium':
      return {
        bg: 'bg-echelon-amber/20',
        border: 'border-echelon-amber',
        text: 'text-echelon-amber',
        pulse: '',
      };
    case 'low':
      return {
        bg: 'bg-terminal-text-muted/10',
        border: 'border-terminal-border',
        text: 'text-terminal-text-muted',
        pulse: '',
      };
  }
}

/**
 * Get status badge classes
 */
function getStatusClasses(status: Breach['status']): { bg: string; text: string; border: string } {
  switch (status) {
    case 'active':
      return { bg: 'bg-echelon-red/20', text: 'text-echelon-red', border: 'border-echelon-red' };
    case 'investigating':
      return { bg: 'bg-echelon-amber/20', text: 'text-echelon-amber', border: 'border-echelon-amber' };
    case 'mitigated':
      return { bg: 'bg-echelon-cyan/20', text: 'text-echelon-cyan', border: 'border-echelon-cyan' };
    case 'resolved':
      return { bg: 'bg-echelon-green/20', text: 'text-echelon-green', border: 'border-echelon-green' };
  }
}

/**
 * Get evidence change type classes
 */
function getChangeTypeClasses(changeType: 'added' | 'removed' | 'contradicted'): { bg: string; text: string; icon: string } {
  switch (changeType) {
    case 'added':
      return { bg: 'bg-echelon-green/15', text: 'text-echelon-green', icon: 'text-echelon-green' };
    case 'removed':
      return { bg: 'bg-echelon-red/15', text: 'text-echelon-red', icon: 'text-echelon-red' };
    case 'contradicted':
      return { bg: 'bg-echelon-amber/15', text: 'text-echelon-amber', icon: 'text-echelon-amber' };
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
    <div className="border-b border-terminal-border">
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
  const statusClasses = getStatusClasses(breach.status);

  // Sort beneficiaries by estimatedGain descending
  const sortedBeneficiaries = [...breach.beneficiaries].sort(
    (a, b) => b.estimatedGain - a.estimatedGain
  );

  return (
    <div className="bg-terminal-panel rounded-lg border border-terminal-border p-4 h-full overflow-y-auto scrollbar-thin scrollbar-thumb-terminal-border scrollbar-track-transparent">
      {/* Header Section */}
      <div className="border-b border-terminal-border pb-4 mb-4">
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
              className={`px-3 py-1 rounded border text-xs font-semibold uppercase ${statusClasses.bg} ${statusClasses.text} ${statusClasses.border}`}
            >
              {breach.status}
            </span>
            <div className="flex items-center gap-1 text-xs">
              {breach.recoverable ? (
                <>
                  <CheckCircle className="w-4 h-4 text-echelon-green" />
                  <span className="text-echelon-green">Recoverable</span>
                </>
              ) : (
                <>
                  <XCircle className="w-4 h-4 text-echelon-red" />
                  <span className="text-echelon-red">Unrecoverable</span>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Description Section */}
      <div className="border-b border-terminal-border pb-4 mb-4">
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
                <tr className="border-b border-terminal-border">
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
                    <tr key={timeline.id} className="border-b border-terminal-border">
                      <td className="py-2 text-terminal-text font-medium">{timeline.name}</td>
                      <td className="py-2">
                        <span className="text-terminal-text">
                          {timeline.stabilityBefore.toFixed(1)}%
                        </span>
                        <span className="text-terminal-text-muted mx-1">→</span>
                        <span
                          className={
                            stabilityChange >= 0 ? 'text-echelon-green' : 'text-echelon-red'
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
                          className={logicGapChange <= 0 ? 'text-echelon-green' : 'text-echelon-red'}
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
                className="bg-terminal-panel rounded p-3 border border-terminal-border"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Bot className="w-4 h-4 text-terminal-text-muted" />
                    <span className="text-sm font-medium text-terminal-text">{agent.name}</span>
                    <span className="px-2 py-0.5 rounded text-xs bg-terminal-bg border border-terminal-border text-terminal-text-muted">
                      {agent.archetype}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-sm">
                    <div>
                      <span className="text-terminal-text-muted">P&L:</span>{' '}
                      <span
                        className={`font-mono ${
                          agent.pnlImpact >= 0 ? 'text-echelon-green' : 'text-echelon-red'
                        }`}
                      >
                        {agent.pnlImpact >= 0 ? '+' : ''}${agent.pnlImpact.toFixed(2)}
                      </span>
                    </div>
                    <div>
                      <span className="text-terminal-text-muted">Sanity:</span>{' '}
                      <span className="font-mono text-echelon-red">
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
                className="flex items-center gap-3 bg-terminal-panel rounded p-3 border border-terminal-border"
              >
                {beneficiary.type === 'agent' ? (
                  <Bot className="w-4 h-4 text-terminal-text-muted" />
                ) : (
                  <Wallet className="w-4 h-4 text-terminal-text-muted" />
                )}
                <span className="text-sm text-terminal-text flex-1">{beneficiary.name}</span>
                <span className="text-sm font-mono text-echelon-green">
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
              const changeClasses = getChangeTypeClasses(change.changeType);

              return (
                <div
                  key={`${change.timestamp}-${index}`}
                  className="flex items-start gap-3 bg-terminal-panel rounded p-3 border border-terminal-border"
                >
                  <div className="flex-shrink-0">
                    {change.changeType === 'added' ? (
                      <Plus className={`w-4 h-4 ${changeClasses.icon}`} />
                    ) : change.changeType === 'removed' ? (
                      <Minus className={`w-4 h-4 ${changeClasses.icon}`} />
                    ) : (
                      <AlertTriangle className={`w-4 h-4 ${changeClasses.icon}`} />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs text-terminal-text-muted font-mono">
                        {formatTimestamp(change.timestamp)}
                      </span>
                      <span className="px-2 py-0.5 rounded text-xs font-medium bg-terminal-bg border border-terminal-border text-terminal-text-muted">
                        {change.source}
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-semibold uppercase ${changeClasses.bg} ${changeClasses.text}`}
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
                  bg: 'bg-echelon-red/20',
                  border: 'border-echelon-red',
                  text: 'text-echelon-red',
                  pulse: 'animate-pulse',
                },
                recommended: {
                  bg: 'bg-echelon-amber/20',
                  border: 'border-echelon-amber',
                  text: 'text-echelon-amber',
                  pulse: '',
                },
                optional: {
                  bg: 'bg-terminal-text-muted/10',
                  border: 'border-terminal-border',
                  text: 'text-terminal-text-muted',
                  pulse: '',
                },
              };
              const styles = priorityStyles[action.priority];

              return (
                <div
                  key={action.id}
                  className="bg-terminal-panel rounded p-3 border border-terminal-border"
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
                        className="flex items-center gap-1 px-3 py-1.5 bg-echelon-cyan/20 border border-echelon-cyan rounded text-xs font-medium text-echelon-cyan hover:bg-echelon-cyan/30 transition"
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
        <div className="mt-6 pt-4 border-t border-terminal-border">
          <button
            onClick={onResolve}
            className="w-full py-3 px-4 bg-echelon-green/20 border border-echelon-green rounded text-sm font-semibold text-echelon-green hover:bg-echelon-green/30 transition"
          >
            Mark as Resolved
          </button>
        </div>
      )}
    </div>
  );
}
