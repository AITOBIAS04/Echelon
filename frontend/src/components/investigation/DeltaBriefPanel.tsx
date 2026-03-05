/**
 * DeltaBrief Panel
 *
 * Displays signal scan results: domain filter chips,
 * source query cards with access tier, anomaly alerts.
 */

interface SourceQuery {
  source_id: string;
  source_group: string;
  query: string;
  result_count: number;
  access_tier: string;
  skipped: boolean;
  skip_reason: string | null;
}

interface Anomaly {
  anomaly_id: string;
  source_id: string;
  description: string;
  severity: number;
  detected_at: string;
}

interface DeltaBrief {
  brief_id: string;
  domain_filters: string[];
  generated_at: string;
  source_queries: SourceQuery[];
  anomalies: Anomaly[];
  content_hash: string;
}

const TIER_COLORS: Record<string, string> = {
  A: 'bg-emerald-500/20 text-emerald-400',
  B: 'bg-amber-500/20 text-amber-400',
  C: 'bg-red-500/20 text-red-400',
};

function DomainFilterChip({ domain }: { domain: string }) {
  return (
    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-echelon-cyan/10 text-echelon-cyan">
      {domain}
    </span>
  );
}

function AccessTierBadge({ tier }: { tier: string }) {
  const color = TIER_COLORS[tier] ?? 'bg-zinc-500/20 text-zinc-400';
  return (
    <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono uppercase ${color}`}>
      Tier {tier}
    </span>
  );
}

function SourceQueryCard({ sq }: { sq: SourceQuery }) {
  return (
    <div className={`bg-terminal-surface rounded p-2 border ${
      sq.skipped ? 'border-amber-500/20 opacity-60' : 'border-terminal-border'
    }`}>
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] text-terminal-text">{sq.source_id}</span>
          <span className="text-[10px] text-terminal-text-muted">{sq.source_group}</span>
          <AccessTierBadge tier={sq.access_tier} />
        </div>
        <span className="text-[10px] text-terminal-text-muted">
          {sq.skipped ? 'SKIPPED' : `${sq.result_count} results`}
        </span>
      </div>
      {sq.skip_reason && (
        <div className="mt-1 text-[10px] text-amber-400">{sq.skip_reason}</div>
      )}
    </div>
  );
}

function AnomalyCard({ anomaly }: { anomaly: Anomaly }) {
  const severityPct = Math.round(anomaly.severity * 100);
  return (
    <div className="bg-terminal-surface rounded p-2 border border-red-500/20">
      <div className="flex items-center justify-between">
        <span className="font-mono text-[10px] text-terminal-text">{anomaly.anomaly_id}</span>
        <span className="text-[10px] font-mono text-red-400">{severityPct}% severity</span>
      </div>
      <p className="mt-1 text-xs text-terminal-text">{anomaly.description}</p>
      <div className="mt-1 text-[10px] text-terminal-text-muted">
        Source: {anomaly.source_id} | {new Date(anomaly.detected_at).toLocaleString()}
      </div>
    </div>
  );
}

export function DeltaBriefPanel({ brief }: { brief: DeltaBrief | null }) {
  if (!brief) {
    return (
      <div className="text-terminal-text-muted text-xs p-4">
        No scan results available. Run a signal scan first.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-terminal-surface rounded-lg p-3 border border-terminal-border">
        <div className="flex items-center justify-between text-xs mb-2">
          <span className="font-mono text-terminal-text">{brief.brief_id}</span>
          <span className="text-terminal-text-muted">
            {new Date(brief.generated_at).toLocaleString()}
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs mb-2">
          <span className="text-terminal-text-muted">Hash:</span>
          <span className="font-mono text-terminal-text">
            {brief.content_hash.substring(0, 16)}...
          </span>
        </div>
        {/* Domain filter chips */}
        <div className="flex gap-1 flex-wrap">
          {brief.domain_filters.map((df) => (
            <DomainFilterChip key={df} domain={df} />
          ))}
        </div>
      </div>

      {/* Anomalies */}
      {brief.anomalies.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-red-400 uppercase">
            Anomalies ({brief.anomalies.length})
          </h4>
          {brief.anomalies.map((a) => (
            <AnomalyCard key={a.anomaly_id} anomaly={a} />
          ))}
        </div>
      )}

      {/* Source queries */}
      <div className="space-y-1">
        <h4 className="text-xs font-semibold text-terminal-text-muted uppercase">
          Source Queries ({brief.source_queries.length})
        </h4>
        {brief.source_queries.map((sq) => (
          <SourceQueryCard key={sq.source_id} sq={sq} />
        ))}
      </div>
    </div>
  );
}
