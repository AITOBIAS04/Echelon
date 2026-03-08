/**
 * Drift Events Panel
 *
 * Displays commitment drift events and provides drift submission form.
 * Drift is a real live mutation path: POST /api/v1/investigations/{id}/drift
 * triggers stop-condition evaluation after persisting the event.
 *
 * Backend DriftType enum (commitment_monitor.py):
 *   entity_restructure | contract_amendment | market_rule_change
 *   regulatory_status_change | jurisdiction_change
 *
 * Backend DriftImpact enum:
 *   material | non_material
 *
 * Design ref: output/design_reference/echelon_drift_submission_v1.html
 */

import { useState } from 'react';
import { Plus, AlertTriangle, Loader2, X } from 'lucide-react';
import type { DriftEvent, DriftType, ImpactAssessment } from '../../types/investigation';
import { useSubmitDrift } from '../../hooks/useInvestigation';

/** Backend-aligned drift type options with human labels */
const DRIFT_TYPES: { value: DriftType; label: string }[] = [
  { value: 'entity_restructure', label: 'Entity Restructure' },
  { value: 'contract_amendment', label: 'Contract Amendment' },
  { value: 'market_rule_change', label: 'Market Rule Change' },
  { value: 'regulatory_status_change', label: 'Regulatory Status Change' },
  { value: 'jurisdiction_change', label: 'Jurisdiction Change' },
];

const DRIFT_TYPE_LABELS: Record<string, string> = Object.fromEntries(
  DRIFT_TYPES.map((t) => [t.value, t.label]),
);

const IMPACT_STYLES: Record<string, { bg: string; text: string }> = {
  material: { bg: 'bg-status-failure/15', text: 'text-status-failure' },
  MATERIAL: { bg: 'bg-status-failure/15', text: 'text-status-failure' },
  non_material: { bg: 'bg-terminal-panel', text: 'text-terminal-text-muted' },
  NON_MATERIAL: { bg: 'bg-terminal-panel', text: 'text-terminal-text-muted' },
};

function DriftEventRow({ event }: { event: DriftEvent }) {
  const impact = IMPACT_STYLES[event.impact_assessment] ?? IMPACT_STYLES.non_material;
  const typeLabel = DRIFT_TYPE_LABELS[event.drift_type] ?? event.drift_type.replace(/_/g, ' ');

  return (
    <div className="grid grid-cols-[1fr_auto] items-start gap-4 py-3 border-b border-terminal-border/30 last:border-b-0">
      <div className="min-w-0">
        {/* Type + impact row */}
        <div className="flex items-center gap-2 mb-1">
          <span className="text-[11px] font-mono font-semibold text-terminal-text-muted">
            {event.drift_id.slice(0, 12)}
          </span>
          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono uppercase bg-echelon-cyan/10 text-echelon-cyan border border-echelon-cyan/20">
            {typeLabel}
          </span>
          <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono uppercase ${impact.bg} ${impact.text}`}>
            {event.impact_assessment === 'material' || event.impact_assessment === 'MATERIAL'
              ? 'Material'
              : 'Non-material'}
          </span>
        </div>

        {/* Values */}
        <div className="grid grid-cols-2 gap-x-4 text-[12px]">
          <div>
            <span className="text-terminal-text-muted">Original: </span>
            <span className="font-mono text-terminal-text">{event.original_value || '\u2014'}</span>
          </div>
          <div>
            <span className="text-terminal-text-muted">New: </span>
            <span className="font-mono text-terminal-text">{event.new_value || '\u2014'}</span>
          </div>
        </div>

        {/* Evidence ref */}
        {event.evidence_ref && (
          <div className="mt-1 text-[10px] text-terminal-text-muted">
            Evidence ref: <span className="font-mono text-echelon-cyan">{event.evidence_ref}</span>
          </div>
        )}
      </div>

      {/* Timestamp */}
      <span className="text-[10px] font-mono text-terminal-text-muted whitespace-nowrap pt-0.5">
        {new Date(event.detected_at).toLocaleString()}
      </span>
    </div>
  );
}

function DriftSubmitForm({
  investigationId,
  onClose,
}: {
  investigationId: string;
  onClose: () => void;
}) {
  const [driftType, setDriftType] = useState<DriftType>('market_rule_change');
  const [originalValue, setOriginalValue] = useState('');
  const [newValue, setNewValue] = useState('');
  const [impact, setImpact] = useState<ImpactAssessment>('non_material');
  const [evidenceRef, setEvidenceRef] = useState('');

  const submitDrift = useSubmitDrift(investigationId);

  const handleSubmit = () => {
    submitDrift.mutate(
      {
        drift_type: driftType,
        original_value: originalValue,
        new_value: newValue,
        impact_assessment: impact,
        evidence_ref: evidenceRef || undefined,
      },
      {
        onSuccess: () => {
          onClose();
        },
      },
    );
  };

  return (
    <div className="bg-terminal-surface rounded-lg border border-terminal-border overflow-hidden">
      <div className="px-5 py-2.5 border-b border-terminal-border/50 bg-terminal-panel flex items-center justify-between">
        <h3 className="text-[11px] font-bold uppercase tracking-wider text-terminal-text-muted">
          Report Drift Event
        </h3>
        <button
          onClick={onClose}
          className="p-0.5 text-terminal-text-muted hover:text-terminal-text transition-colors"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
      <div className="p-5 space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-[10px] text-terminal-text-muted uppercase tracking-wider block mb-1">
              Drift Type
            </label>
            <select
              value={driftType}
              onChange={(e) => setDriftType(e.target.value as DriftType)}
              className="w-full bg-terminal-bg border border-terminal-border rounded px-2 py-1.5 text-xs text-terminal-text font-mono focus:outline-none focus:border-echelon-cyan/50"
            >
              {DRIFT_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-[10px] text-terminal-text-muted uppercase tracking-wider block mb-1">
              Impact Assessment
            </label>
            <select
              value={impact}
              onChange={(e) => setImpact(e.target.value as ImpactAssessment)}
              className="w-full bg-terminal-bg border border-terminal-border rounded px-2 py-1.5 text-xs text-terminal-text font-mono focus:outline-none focus:border-echelon-cyan/50"
            >
              <option value="non_material">Non-material</option>
              <option value="material">Material</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-[10px] text-terminal-text-muted uppercase tracking-wider block mb-1">
              Original Value
            </label>
            <input
              value={originalValue}
              onChange={(e) => setOriginalValue(e.target.value)}
              className="w-full bg-terminal-bg border border-terminal-border rounded px-2 py-1.5 text-xs text-terminal-text font-mono placeholder:text-terminal-text-muted/50 focus:outline-none focus:border-echelon-cyan/50"
              placeholder="Value before drift"
            />
          </div>
          <div>
            <label className="text-[10px] text-terminal-text-muted uppercase tracking-wider block mb-1">
              New Value
            </label>
            <input
              value={newValue}
              onChange={(e) => setNewValue(e.target.value)}
              className="w-full bg-terminal-bg border border-terminal-border rounded px-2 py-1.5 text-xs text-terminal-text font-mono placeholder:text-terminal-text-muted/50 focus:outline-none focus:border-echelon-cyan/50"
              placeholder="Value after drift"
            />
          </div>
        </div>

        <div>
          <label className="text-[10px] text-terminal-text-muted uppercase tracking-wider block mb-1">
            Evidence Reference <span className="text-terminal-text-muted/50">(optional)</span>
          </label>
          <input
            value={evidenceRef}
            onChange={(e) => setEvidenceRef(e.target.value)}
            className="w-full bg-terminal-bg border border-terminal-border rounded px-2 py-1.5 text-xs text-terminal-text font-mono placeholder:text-terminal-text-muted/50 focus:outline-none focus:border-echelon-cyan/50"
            placeholder="E001, E002..."
          />
        </div>

        {submitDrift.isError && (
          <div className="text-xs text-status-failure bg-status-failure/10 border border-status-failure/30 rounded px-3 py-2">
            {(submitDrift.error as Error)?.message ?? 'Drift submission failed'}
          </div>
        )}

        <div className="flex gap-2 justify-end pt-1">
          <button
            onClick={onClose}
            className="px-3 py-1.5 text-xs text-terminal-text-muted hover:text-terminal-text transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitDrift.isPending}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-echelon-cyan bg-echelon-cyan/10 border border-echelon-cyan/30 rounded hover:bg-echelon-cyan/20 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {submitDrift.isPending && <Loader2 className="w-3 h-3 animate-spin" />}
            Submit Drift
          </button>
        </div>
      </div>
    </div>
  );
}

export function DriftEventsPanel({
  events,
  hasMaterialDrift,
  investigationId,
}: {
  events: DriftEvent[];
  hasMaterialDrift: boolean;
  investigationId?: string;
}) {
  const [showForm, setShowForm] = useState(false);

  return (
    <div className="space-y-4">
      {/* Material drift banner */}
      {hasMaterialDrift && (
        <div className="bg-status-failure/10 border border-status-failure/30 rounded-lg p-3 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-status-failure shrink-0" />
          <span className="text-xs text-status-failure">
            Material drift detected — stop-condition reevaluation triggered. Routing may change to REVIEW_REQUIRED.
          </span>
        </div>
      )}

      {/* Drift events section — sunken header, padded body */}
      <div className="bg-terminal-surface rounded-lg border border-terminal-border overflow-hidden">
        <div className="px-5 py-2.5 border-b border-terminal-border/50 bg-terminal-panel flex items-center gap-2">
          <h3 className="text-[11px] font-bold uppercase tracking-wider text-terminal-text-muted">
            Drift Events
          </h3>
          <span className="font-mono text-[11px] text-terminal-text-muted">
            {events.length} recorded
          </span>
          <span className="font-mono text-[11px] text-terminal-text-muted ml-auto">
            commitment monitor
          </span>
        </div>
        <div className="px-5">
          {events.length === 0 ? (
            <div className="py-8 text-center">
              <div className="text-[13px] text-terminal-text-muted mb-1">
                No drift events detected
              </div>
              <div className="text-[11px] text-terminal-text-muted/60">
                Drift events are logged when commitment parameters change during an active investigation.
              </div>
              <div className="text-[10px] font-mono text-terminal-text-muted/40 mt-2">
                GET /api/v1/investigations/{'{id}'}/drift
              </div>
            </div>
          ) : (
            <div>
              {events.map((event) => (
                <DriftEventRow key={event.drift_id} event={event} />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Submit form or trigger */}
      {investigationId && (
        showForm ? (
          <DriftSubmitForm
            investigationId={investigationId}
            onClose={() => setShowForm(false)}
          />
        ) : (
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-echelon-cyan border border-echelon-cyan/30 rounded-lg hover:bg-echelon-cyan/10 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            Report Drift
          </button>
        )
      )}
    </div>
  );
}
