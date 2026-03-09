import { clsx } from 'clsx';
import type { EvidenceEnvelopeManifest, EvidenceItem } from '../../types/investigation';

const PROVENANCE_CLASSES: Record<string, string> = {
  public_primary: 'border-[color:oklch(0.545_0.170_152_/_0.18)] bg-[var(--e-green-50)] text-[var(--e-green-600)]',
  public_secondary: 'border-[color:oklch(0.623_0.188_259_/_0.18)] bg-[color:oklch(0.623_0.188_259_/_0.10)] text-[color:oklch(0.623_0.188_259)]',
  private_leak: 'border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] text-[var(--e-red-600)]',
  analyst_derived: 'border-[color:oklch(0.708_0.136_62_/_0.20)] bg-[color:oklch(0.708_0.136_62_/_0.10)] text-[var(--e-orange-600)]',
  third_party_tool_output: 'border-[var(--e-purple-200)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)]',
};

function ProvenanceBadge({ value }: { value: string }) {
  return (
    <span
      className={clsx(
        'rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em]',
        PROVENANCE_CLASSES[value] ?? 'border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] text-[var(--e-text-muted)]',
      )}
    >
      {value.replace(/_/g, ' ')}
    </span>
  );
}

function EvidenceCard({
  item,
  redacted,
}: {
  item: EvidenceItem;
  redacted: boolean;
}) {
  return (
    <div
      className={clsx(
        'rounded-lg border bg-[var(--e-bg-card)] px-4 py-4 shadow-[var(--e-shadow-xs)]',
        redacted
          ? 'border-[color:oklch(0.545_0.185_25_/_0.18)]'
          : 'border-[var(--e-border-primary)]',
      )}
    >
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-mono text-[11px] text-[var(--e-text-muted)]">{item.evidence_id}</span>
          <ProvenanceBadge value={item.provenance_class} />
          {redacted ? (
            <span className="rounded-full border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-red-600)]">
              Redacted
            </span>
          ) : null}
        </div>
        <span className="font-mono text-[11px] text-[var(--e-text-muted)]">
          {new Date(item.submitted_at).toLocaleString()}
        </span>
      </div>

      <div className="grid grid-cols-[80px_1fr] gap-x-3 gap-y-1 text-[13px]">
        <div className="text-[var(--e-text-muted)]">Hash</div>
        <div className="font-mono text-[var(--e-text-primary)]">{item.content_hash}</div>
        <div className="text-[var(--e-text-muted)]">Type</div>
        <div className="text-[var(--e-text-primary)]">{item.content_type}</div>
        {item.source_description ? (
          <>
            <div className="text-[var(--e-text-muted)]">Source</div>
            <div className="text-[var(--e-text-primary)]">{item.source_description}</div>
          </>
        ) : null}
        {item.references.length > 0 ? (
          <>
            <div className="text-[var(--e-text-muted)]">Refs</div>
            <div className="font-mono text-[var(--e-text-primary)]">{item.references.join(', ')}</div>
          </>
        ) : null}
      </div>
    </div>
  );
}

export function EvidenceEnvelopePanel({ evidence }: { evidence: EvidenceEnvelopeManifest }) {
  const redactedIds = new Set(evidence.redactions.map((event) => event.evidence_id));

  if (evidence.items.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-8 text-center text-[13px] text-[var(--e-text-muted)]">
        No evidence items submitted yet.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-4 shadow-[var(--e-shadow-xs)]">
        <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
          Envelope Hash
        </div>
        <div className="font-mono text-[12px] text-[var(--e-text-primary)]">{evidence.envelope_hash || '—'}</div>
      </div>

      <div className="flex flex-wrap gap-2">
        {Object.entries(evidence.provenance_summary).map(([key, count]) => (
          <div key={key} className="inline-flex items-center gap-2 rounded-full border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 py-1 shadow-[var(--e-shadow-xs)]">
            <ProvenanceBadge value={key} />
            <span className="text-[11px] text-[var(--e-text-muted)]">{count}</span>
          </div>
        ))}
      </div>

      <div className="space-y-3">
        {evidence.items.map((item) => (
          <EvidenceCard key={item.evidence_id} item={item} redacted={redactedIds.has(item.evidence_id)} />
        ))}
      </div>
    </div>
  );
}

export default EvidenceEnvelopePanel;
