import { useState } from 'react';
import { AlertTriangle, Loader2, Plus, X } from 'lucide-react';
import { clsx } from 'clsx';
import type { DriftEvent, DriftType, ImpactAssessment } from '../../types/investigation';
import { useSubmitDrift } from '../../hooks/useInvestigation';

const DRIFT_TYPES: Array<{ value: DriftType; label: string }> = [
  { value: 'entity_restructure', label: 'Entity Restructure' },
  { value: 'contract_amendment', label: 'Contract Amendment' },
  { value: 'market_rule_change', label: 'Market Rule Change' },
  { value: 'regulatory_status_change', label: 'Regulatory Status Change' },
  { value: 'jurisdiction_change', label: 'Jurisdiction Change' },
];

const DRIFT_TYPE_LABELS: Record<string, string> = Object.fromEntries(
  DRIFT_TYPES.map((type) => [type.value, type.label]),
);

function impactClasses(impact: string): string {
  if (impact === 'material' || impact === 'MATERIAL') {
    return 'border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] text-[var(--e-red-600)]';
  }
  return 'border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] text-[var(--e-text-muted)]';
}

function DriftEventRow({ event }: { event: DriftEvent }) {
  return (
    <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-4 shadow-[var(--e-shadow-xs)]">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-mono text-[11px] text-[var(--e-text-muted)]">
            {event.drift_id.slice(0, 12)}
          </span>
          <span className="rounded-full border border-[var(--e-purple-200)] bg-[var(--e-purple-50)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-purple-700)]">
            {DRIFT_TYPE_LABELS[event.drift_type] ?? event.drift_type.replace(/_/g, ' ')}
          </span>
          <span
            className={clsx(
              'rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em]',
              impactClasses(event.impact_assessment),
            )}
          >
            {event.impact_assessment === 'material' || event.impact_assessment === 'MATERIAL'
              ? 'Material'
              : 'Non-material'}
          </span>
        </div>
        <span className="font-mono text-[11px] text-[var(--e-text-muted)]">
          {new Date(event.detected_at).toLocaleString()}
        </span>
      </div>

      <div className="grid grid-cols-1 gap-2 text-[13px] text-[var(--e-text-secondary)] sm:grid-cols-2">
        <div>
          <span className="text-[var(--e-text-muted)]">Original:</span>{' '}
          <span className="font-mono text-[var(--e-text-primary)]">{event.original_value || '—'}</span>
        </div>
        <div>
          <span className="text-[var(--e-text-muted)]">New:</span>{' '}
          <span className="font-mono text-[var(--e-text-primary)]">{event.new_value || '—'}</span>
        </div>
      </div>

      {event.evidence_ref ? (
        <div className="mt-2 text-[12px] text-[var(--e-text-muted)]">
          Evidence ref:{' '}
          <span className="font-mono text-[var(--e-purple-700)]">{event.evidence_ref}</span>
        </div>
      ) : null}
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
        onSuccess: () => onClose(),
      },
    );
  };

  return (
    <div className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
      <div className="flex items-center justify-between border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-3">
        <h3 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
          Report Drift Event
        </h3>
        <button
          type="button"
          onClick={onClose}
          className="text-[var(--e-text-muted)] transition hover:text-[var(--e-text-primary)]"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="space-y-4 px-5 py-5">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              Drift Type
            </label>
            <select
              value={driftType}
              onChange={(event) => setDriftType(event.target.value as DriftType)}
              className="h-10 w-full rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 text-[13px] text-[var(--e-text-primary)] outline-none focus:border-[var(--e-border-focus)]"
            >
              {DRIFT_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              Impact Assessment
            </label>
            <select
              value={impact}
              onChange={(event) => setImpact(event.target.value as ImpactAssessment)}
              className="h-10 w-full rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 text-[13px] text-[var(--e-text-primary)] outline-none focus:border-[var(--e-border-focus)]"
            >
              <option value="non_material">Non-material</option>
              <option value="material">Material</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              Original Value
            </label>
            <input
              value={originalValue}
              onChange={(event) => setOriginalValue(event.target.value)}
              className="h-10 w-full rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 text-[13px] text-[var(--e-text-primary)] outline-none placeholder:text-[var(--e-text-muted)] focus:border-[var(--e-border-focus)]"
              placeholder="Value before drift"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              New Value
            </label>
            <input
              value={newValue}
              onChange={(event) => setNewValue(event.target.value)}
              className="h-10 w-full rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 text-[13px] text-[var(--e-text-primary)] outline-none placeholder:text-[var(--e-text-muted)] focus:border-[var(--e-border-focus)]"
              placeholder="Value after drift"
            />
          </div>
        </div>

        <div>
          <label className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
            Evidence Reference <span className="text-[var(--e-text-muted)]">(optional)</span>
          </label>
          <input
            value={evidenceRef}
            onChange={(event) => setEvidenceRef(event.target.value)}
            className="h-10 w-full rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 text-[13px] text-[var(--e-text-primary)] outline-none placeholder:text-[var(--e-text-muted)] focus:border-[var(--e-border-focus)]"
            placeholder="E001, E002…"
          />
        </div>

        {submitDrift.isError ? (
          <div className="rounded-md border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] px-4 py-3 text-[12px] text-[var(--e-red-600)]">
            {(submitDrift.error as Error)?.message ?? 'Drift submission failed'}
          </div>
        ) : null}

        <div className="flex items-center justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-md px-3 py-2 text-[12px] font-medium text-[var(--e-text-muted)] transition hover:text-[var(--e-text-primary)]"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={submitDrift.isPending}
            className="inline-flex items-center gap-2 rounded-md bg-[var(--e-purple-500)] px-4 py-2 text-[12px] font-semibold text-[var(--e-text-inverse)] transition hover:bg-[var(--e-purple-600)] disabled:cursor-not-allowed disabled:bg-[var(--e-purple-200)] disabled:text-[var(--e-text-disabled)]"
          >
            {submitDrift.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
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
      {hasMaterialDrift ? (
        <div className="flex items-center gap-3 rounded-lg border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] px-4 py-3 text-[13px] text-[var(--e-red-600)]">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          Material drift detected — stop-condition reevaluation triggered. Routing may change to REVIEW_REQUIRED.
        </div>
      ) : null}

      <div className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
        <div className="flex items-center gap-2 border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-3">
          <h3 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
            Drift Events
          </h3>
          <span className="font-mono text-[11px] text-[var(--e-text-muted)]">{events.length} recorded</span>
          <span className="ml-auto text-[11px] text-[var(--e-text-muted)]">commitment monitor</span>
        </div>
        <div className="space-y-3 px-5 py-5">
          {events.length > 0 ? (
            events.map((event) => <DriftEventRow key={event.drift_id} event={event} />)
          ) : (
            <div className="rounded-md border border-dashed border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-8 text-center">
              <div className="text-[13px] font-medium text-[var(--e-text-primary)]">No drift events detected</div>
              <div className="mt-1 text-[12px] leading-5 text-[var(--e-text-muted)]">
                Drift events appear here when committed investigation parameters change.
              </div>
            </div>
          )}
        </div>
      </div>

      {investigationId ? (
        showForm ? (
          <DriftSubmitForm investigationId={investigationId} onClose={() => setShowForm(false)} />
        ) : (
          <button
            type="button"
            onClick={() => setShowForm(true)}
            className="inline-flex items-center gap-2 rounded-md border border-[var(--e-purple-200)] bg-[var(--e-purple-50)] px-3 py-2 text-[12px] font-semibold text-[var(--e-purple-700)] transition hover:bg-[var(--e-purple-100)]"
          >
            <Plus className="h-4 w-4" />
            Report Drift
          </button>
        )
      ) : null}
    </div>
  );
}

export default DriftEventsPanel;
