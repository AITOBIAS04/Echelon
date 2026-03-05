/**
 * Evidence Envelope Panel
 *
 * Displays evidence items chronologically with provenance badges,
 * content hashes, redaction indicators, and envelope hash.
 */

import type { EvidenceEnvelopeManifest, EvidenceItem } from '../../types/investigation';

const PROVENANCE_COLORS: Record<string, string> = {
  public_primary: 'bg-emerald-500/20 text-emerald-400',
  public_secondary: 'bg-blue-500/20 text-blue-400',
  private_leak: 'bg-red-500/20 text-red-400',
  analyst_derived: 'bg-amber-500/20 text-amber-400',
  third_party_tool_output: 'bg-purple-500/20 text-purple-400',
  PRIMARY: 'bg-emerald-500/20 text-emerald-400',
  SECONDARY: 'bg-blue-500/20 text-blue-400',
  LEAKED: 'bg-red-500/20 text-red-400',
  DERIVED: 'bg-amber-500/20 text-amber-400',
  TOOL_OUTPUT: 'bg-purple-500/20 text-purple-400',
};

function ProvenanceBadge({ provenance }: { provenance: string }) {
  const color = PROVENANCE_COLORS[provenance] ?? 'bg-zinc-500/20 text-zinc-400';
  return (
    <span className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase ${color}`}>
      {provenance}
    </span>
  );
}

function EvidenceItemCard({ item, isRedacted }: { item: EvidenceItem; isRedacted: boolean }) {
  return (
    <div className={`bg-terminal-surface rounded-lg p-3 border ${
      isRedacted ? 'border-red-500/30' : 'border-terminal-border'
    }`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-terminal-text">{item.evidence_id}</span>
          <ProvenanceBadge provenance={item.provenance_class} />
          {isRedacted && (
            <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-red-500/20 text-red-400">
              REDACTED
            </span>
          )}
        </div>
        <span className="text-[10px] text-terminal-text-muted whitespace-nowrap">
          {new Date(item.submitted_at).toLocaleString()}
        </span>
      </div>

      <div className="mt-2 space-y-1 text-xs">
        <div className="flex gap-2">
          <span className="text-terminal-text-muted">Hash:</span>
          <span className="font-mono text-terminal-text">
            {item.content_hash.substring(0, 16)}...
          </span>
        </div>
        <div className="flex gap-2">
          <span className="text-terminal-text-muted">Type:</span>
          <span className="text-terminal-text">{item.content_type}</span>
        </div>
        {item.source_description && (
          <div className="flex gap-2">
            <span className="text-terminal-text-muted">Source:</span>
            <span className="text-terminal-text">{item.source_description}</span>
          </div>
        )}
        {item.references.length > 0 && (
          <div className="flex gap-2">
            <span className="text-terminal-text-muted">Refs:</span>
            <span className="font-mono text-terminal-text">
              {item.references.join(', ')}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

function ProvenanceSummaryBar({ summary }: { summary: Record<string, number> }) {
  const total = Object.values(summary).reduce((a, b) => a + b, 0);
  if (total === 0) return null;

  return (
    <div className="space-y-1">
      <div className="flex h-2 rounded overflow-hidden">
        {Object.entries(summary).map(([key, count]) => {
          const pct = (count / total) * 100;
          const colorClass = PROVENANCE_COLORS[key]?.split(' ')[0] ?? 'bg-zinc-500/20';
          return (
            <div
              key={key}
              className={colorClass.replace('/20', '/60')}
              style={{ width: `${pct}%` }}
              title={`${key}: ${count}`}
            />
          );
        })}
      </div>
      <div className="flex gap-3 flex-wrap">
        {Object.entries(summary).map(([key, count]) => (
          <div key={key} className="flex items-center gap-1 text-[10px]">
            <ProvenanceBadge provenance={key} />
            <span className="text-terminal-text-muted">{count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function EvidenceEnvelopePanel({ evidence }: { evidence: EvidenceEnvelopeManifest }) {
  const redactedIds = new Set(evidence.redactions.map((r) => r.evidence_id));

  if (evidence.items.length === 0) {
    return (
      <div className="text-terminal-text-muted text-xs p-4">
        No evidence items submitted yet.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Envelope hash */}
      <div className="bg-terminal-surface rounded-lg p-3 border border-terminal-border">
        <div className="flex items-center justify-between text-xs">
          <span className="text-terminal-text-muted">Envelope Hash</span>
          <span className="font-mono text-terminal-text">
            {evidence.envelope_hash || '—'}
          </span>
        </div>
      </div>

      {/* Provenance summary bar */}
      <ProvenanceSummaryBar summary={evidence.provenance_summary} />

      {/* Evidence items (chronological) */}
      <div className="space-y-2">
        {evidence.items.map((item) => (
          <EvidenceItemCard
            key={item.evidence_id}
            item={item}
            isRedacted={redactedIds.has(item.evidence_id)}
          />
        ))}
      </div>
    </div>
  );
}
