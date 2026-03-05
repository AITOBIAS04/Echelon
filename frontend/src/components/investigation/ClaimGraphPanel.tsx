/**
 * Claim Graph Panel
 *
 * Displays claims with status badges, evidence refs,
 * confidence scores, and a status summary.
 */

import type { ClaimGraphSummary, ClaimNode } from '../../types/investigation';

const STATUS_COLORS: Record<string, string> = {
  supported: 'bg-emerald-500/20 text-emerald-400',
  partially_supported: 'bg-amber-500/20 text-amber-400',
  unconfirmed: 'bg-zinc-500/20 text-zinc-400',
  contradicted: 'bg-red-500/20 text-red-400',
};

const TYPE_COLORS: Record<string, string> = {
  fact: 'bg-blue-500/20 text-blue-400',
  causal: 'bg-purple-500/20 text-purple-400',
  attribution: 'bg-amber-500/20 text-amber-400',
};

function ClaimStatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] ?? 'bg-zinc-500/20 text-zinc-400';
  return (
    <span className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase ${color}`}>
      {status}
    </span>
  );
}

function ClaimTypeBadge({ type }: { type: string }) {
  const color = TYPE_COLORS[type] ?? 'bg-zinc-500/20 text-zinc-400';
  return (
    <span className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase ${color}`}>
      {type}
    </span>
  );
}

function ConfidenceBar({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const color = pct >= 70 ? 'bg-emerald-500' : pct >= 40 ? 'bg-amber-500' : 'bg-red-500';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-terminal-border rounded overflow-hidden">
        <div className={`h-full ${color} rounded`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[10px] font-mono text-terminal-text-muted w-8 text-right">
        {pct}%
      </span>
    </div>
  );
}

function ClaimNodeCard({ claim }: { claim: ClaimNode }) {
  return (
    <div className="bg-terminal-surface rounded-lg p-3 border border-terminal-border">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-terminal-text">{claim.claim_id}</span>
          <ClaimTypeBadge type={claim.claim_type} />
          <ClaimStatusBadge status={claim.status} />
        </div>
      </div>

      <p className="mt-2 text-xs text-terminal-text">{claim.claim_text}</p>

      <div className="mt-2">
        <ConfidenceBar confidence={claim.confidence} />
      </div>

      {claim.evidence_refs.length > 0 && (
        <div className="mt-2 flex gap-1 flex-wrap">
          {claim.evidence_refs.map((ref) => (
            <span
              key={ref}
              className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-echelon-cyan/10 text-echelon-cyan"
            >
              {ref}
            </span>
          ))}
        </div>
      )}

      {claim.counter_signals.length > 0 && (
        <div className="mt-2 flex gap-1 flex-wrap">
          {claim.counter_signals.map((cs) => (
            <span
              key={cs}
              className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-red-500/10 text-red-400"
            >
              {cs}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function StatusSummary({ summary }: { summary: Record<string, number> }) {
  const total = Object.values(summary).reduce((a, b) => a + b, 0);
  if (total === 0) return null;

  return (
    <div className="flex gap-3 flex-wrap">
      {Object.entries(summary).map(([status, count]) => (
        <div key={status} className="flex items-center gap-1">
          <ClaimStatusBadge status={status} />
          <span className="text-[10px] text-terminal-text-muted">{count}</span>
        </div>
      ))}
    </div>
  );
}

export function ClaimGraphPanel({ claims }: { claims: ClaimGraphSummary }) {
  if (claims.claims.length === 0) {
    return (
      <div className="text-terminal-text-muted text-xs p-4">
        No claims registered yet.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Root hash + summary */}
      <div className="bg-terminal-surface rounded-lg p-3 border border-terminal-border">
        <div className="flex items-center justify-between text-xs mb-2">
          <span className="text-terminal-text-muted">Root Hash</span>
          <span className="font-mono text-terminal-text">
            {claims.root_hash.substring(0, 16)}...
          </span>
        </div>
        <StatusSummary summary={claims.status_summary} />
      </div>

      {/* Claim nodes */}
      <div className="space-y-2">
        {claims.claims.map((claim) => (
          <ClaimNodeCard key={claim.claim_id} claim={claim} />
        ))}
      </div>
    </div>
  );
}
