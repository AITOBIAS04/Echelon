import { clsx } from 'clsx';
import type { ClaimGraphSummary, ClaimNode } from '../../types/investigation';

const STATUS_STYLES: Record<string, string> = {
  supported: 'border-[color:oklch(0.545_0.170_152_/_0.18)] bg-[var(--e-green-50)] text-[var(--e-green-600)]',
  partially_supported: 'border-[color:oklch(0.708_0.136_62_/_0.20)] bg-[color:oklch(0.708_0.136_62_/_0.10)] text-[var(--e-orange-600)]',
  unconfirmed: 'border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] text-[var(--e-text-muted)]',
  contradicted: 'border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] text-[var(--e-red-600)]',
};

const TYPE_STYLES: Record<string, string> = {
  fact: 'border-[color:oklch(0.623_0.188_259_/_0.18)] bg-[color:oklch(0.623_0.188_259_/_0.10)] text-[color:oklch(0.623_0.188_259)]',
  causal: 'border-[var(--e-purple-200)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)]',
  attribution: 'border-[color:oklch(0.708_0.136_62_/_0.20)] bg-[color:oklch(0.708_0.136_62_/_0.10)] text-[var(--e-orange-600)]',
};

function ClaimPill({ value, kind }: { value: string; kind: 'status' | 'type' }) {
  const classes = kind === 'status' ? STATUS_STYLES[value] : TYPE_STYLES[value];
  return (
    <span className={clsx('rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em]', classes)}>
      {value.replace(/_/g, ' ')}
    </span>
  );
}

function ConfidenceBar({ confidence }: { confidence: number }) {
  const percent = Math.round(confidence * 100);
  const color =
    percent >= 70 ? 'bg-[var(--e-green-600)]' : percent >= 40 ? 'bg-[var(--e-orange-600)]' : 'bg-[var(--e-red-600)]';

  return (
    <div className="flex items-center gap-2">
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-[var(--e-bg-sunken)]">
        <div className={clsx('h-full rounded-full', color)} style={{ width: `${percent}%` }} />
      </div>
      <span className="w-10 text-right font-mono text-[11px] text-[var(--e-text-muted)]">{percent}%</span>
    </div>
  );
}

function ClaimCard({ claim }: { claim: ClaimNode }) {
  return (
    <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-4 shadow-[var(--e-shadow-xs)]">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <span className="font-mono text-[11px] text-[var(--e-text-muted)]">{claim.claim_id}</span>
        <ClaimPill value={claim.claim_type} kind="type" />
        <ClaimPill value={claim.status} kind="status" />
      </div>

      <div className="mb-3 text-[14px] leading-6 text-[var(--e-text-primary)]">{claim.claim_text}</div>

      <ConfidenceBar confidence={claim.confidence} />

      {claim.evidence_refs.length > 0 ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {claim.evidence_refs.map((reference) => (
            <span
              key={reference}
              className="rounded-full border border-[var(--e-purple-200)] bg-[var(--e-purple-50)] px-2 py-0.5 font-mono text-[10px] text-[var(--e-purple-700)]"
            >
              {reference}
            </span>
          ))}
        </div>
      ) : null}

      {claim.counter_signals.length > 0 ? (
        <div className="mt-2 flex flex-wrap gap-2">
          {claim.counter_signals.map((signal) => (
            <span
              key={signal}
              className="rounded-full border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] px-2 py-0.5 font-mono text-[10px] text-[var(--e-red-600)]"
            >
              {signal}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}

export function ClaimGraphPanel({ claims }: { claims: ClaimGraphSummary }) {
  if (claims.claims.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-8 text-center text-[13px] text-[var(--e-text-muted)]">
        No claims registered yet.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-4 shadow-[var(--e-shadow-xs)]">
        <div className="mb-2 flex items-center justify-between">
          <span className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
            Root Hash
          </span>
          <span className="font-mono text-[12px] text-[var(--e-text-primary)]">{claims.root_hash}</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {Object.entries(claims.status_summary).map(([status, count]) => (
            <div key={status} className="inline-flex items-center gap-2">
              <ClaimPill value={status} kind="status" />
              <span className="text-[11px] text-[var(--e-text-muted)]">{count}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="space-y-3">
        {claims.claims.map((claim) => (
          <ClaimCard key={claim.claim_id} claim={claim} />
        ))}
      </div>
    </div>
  );
}

export default ClaimGraphPanel;
