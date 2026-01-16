import { useState } from 'react';
import { Plus, Edit2, Trash2, Bell, AlertTriangle, Info } from 'lucide-react';
import type { AlertRule, WatchlistSavedView } from '../../types/presets';

export interface AlertRulesPanelProps {
  view: WatchlistSavedView | null;
  onUpdateView: (view: WatchlistSavedView) => void;
}

export function AlertRulesPanel({ view, onUpdateView }: AlertRulesPanelProps) {
  const [editingRuleId, setEditingRuleId] = useState<string | null>(null);

  if (!view) {
    return (
      <div className="bg-[#111111] rounded-lg border border-[#1A1A1A] p-4 text-center text-terminal-muted">
        <Bell className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p className="text-sm">Select a view to manage alert rules</p>
      </div>
    );
  }

  const handleToggleEnabled = (ruleId: string) => {
    const updatedRules = view.alertRules.map((rule) =>
      rule.id === ruleId ? { ...rule, enabled: !rule.enabled } : rule
    );
    onUpdateView({ ...view, alertRules: updatedRules });
  };

  const handleDelete = (ruleId: string) => {
    if (window.confirm('Delete this alert rule?')) {
      const updatedRules = view.alertRules.filter((rule) => rule.id !== ruleId);
      onUpdateView({ ...view, alertRules: updatedRules });
    }
  };

  const handleAddRule = () => {
    const newRule: AlertRule = {
      id: `alert_${Date.now()}`,
      name: 'New Alert Rule',
      enabled: false,
      severity: 'info',
      condition: {
        type: 'threshold',
        metric: 'logic_gap',
        op: '>=',
        value: 50,
      },
      scope: {
        scopeType: 'watchlist',
      },
    };
    const updatedRules = [...view.alertRules, newRule];
    onUpdateView({ ...view, alertRules: updatedRules });
    setEditingRuleId(newRule.id);
  };

  const formatCondition = (rule: AlertRule): string => {
    const { condition } = rule;
    
    if (condition.type === 'event') {
      return `Event: ${condition.eventType?.replace('_', ' ') || 'Unknown'}`;
    }
    
    if (condition.type === 'threshold') {
      const metric = condition.metric?.replace('_', ' ') || 'Unknown';
      const op = condition.op || '>=';
      const value = condition.value ?? 0;
      return `${metric} ${op} ${value}`;
    }
    
    if (condition.type === 'rate_of_change') {
      const metric = condition.metric?.replace('_', ' ') || 'Unknown';
      const op = condition.op || '>=';
      const value = condition.value ?? 0;
      const window = condition.windowMinutes ?? 0;
      return `${metric} ${op} ${value} in ${window}min`;
    }
    
    return 'Unknown condition';
  };

  const getSeverityIcon = (severity: AlertRule['severity']) => {
    switch (severity) {
      case 'critical':
        return <AlertTriangle className="w-4 h-4 text-red-500" />;
      case 'warn':
        return <AlertTriangle className="w-4 h-4 text-amber-500" />;
      case 'info':
        return <Info className="w-4 h-4 text-cyan-500" />;
    }
  };

  const getSeverityColor = (severity: AlertRule['severity']): string => {
    switch (severity) {
      case 'critical':
        return 'text-red-500 bg-red-500/20 border-red-500/50';
      case 'warn':
        return 'text-amber-500 bg-amber-500/20 border-amber-500/50';
      case 'info':
        return 'text-cyan-500 bg-cyan-500/20 border-cyan-500/50';
    }
  };

  return (
    <div className="bg-[#111111] rounded-lg border border-[#1A1A1A] p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide flex items-center gap-2">
          <Bell className="w-4 h-4" />
          Alert Rules ({view.alertRules.length})
        </h3>
        <button
          onClick={handleAddRule}
          className="flex items-center gap-1.5 px-2 py-1 text-xs bg-terminal-bg border border-terminal-border rounded hover:border-echelon-cyan transition"
        >
          <Plus className="w-3 h-3" />
          Add Rule
        </button>
      </div>

      {view.alertRules.length === 0 ? (
        <div className="text-center py-8 text-terminal-muted text-sm">
          <Bell className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p>No alert rules configured</p>
        </div>
      ) : (
        <div className="space-y-2">
          {view.alertRules.map((rule) => (
            <div
              key={rule.id}
              className="bg-[#0D0D0D] border border-[#1A1A1A] rounded p-3"
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    {getSeverityIcon(rule.severity)}
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded border ${getSeverityColor(rule.severity)}`}>
                      {rule.severity.toUpperCase()}
                    </span>
                    <label className="flex items-center gap-1.5 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={rule.enabled}
                        onChange={() => handleToggleEnabled(rule.id)}
                        className="w-3 h-3 rounded border-terminal-border bg-terminal-bg text-echelon-cyan focus:ring-echelon-cyan"
                      />
                      <span className="text-xs text-terminal-text">Enabled</span>
                    </label>
                  </div>
                  <div className="text-sm font-medium text-terminal-text mb-1">
                    {rule.name}
                  </div>
                  <div className="text-xs text-terminal-muted font-mono">
                    {formatCondition(rule)}
                  </div>
                  <div className="text-xs text-terminal-muted mt-1">
                    Scope: {rule.scope.scopeType}
                    {rule.scope.timelineId && ` • ${rule.scope.timelineId}`}
                  </div>
                </div>
                <div className="flex items-center gap-1 flex-shrink-0">
                  <button
                    onClick={() => setEditingRuleId(editingRuleId === rule.id ? null : rule.id)}
                    className="p-1 hover:bg-terminal-panel rounded transition"
                    title="Edit rule"
                  >
                    <Edit2 className="w-3 h-3 text-terminal-muted" />
                  </button>
                  <button
                    onClick={() => handleDelete(rule.id)}
                    className="p-1 hover:bg-red-500/20 rounded transition"
                    title="Delete rule"
                  >
                    <Trash2 className="w-3 h-3 text-red-400" />
                  </button>
                </div>
              </div>
              
              {editingRuleId === rule.id && (
                <div className="mt-3 pt-3 border-t border-[#1A1A1A] text-xs">
                  <p className="text-terminal-muted mb-2">Alert rule editing UI (stubbed)</p>
                  <p className="text-terminal-muted">
                    Full editing interface would allow modification of condition, severity, and scope.
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
