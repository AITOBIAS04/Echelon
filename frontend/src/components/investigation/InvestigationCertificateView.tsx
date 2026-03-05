/**
 * Investigation Certificate Explorer
 *
 * Displays all 30+ certificate fields grouped by section:
 * Header, Evidence, Claims, Counter-Signals, Drift, Anchoring, Hashes, Stop Condition.
 */

import type { InvestigationCertificate } from '../../types/investigation';

function RoutingHintBadge({ decision }: { decision: string }) {
  const isAllowed = decision === 'ALLOWED' || decision === 'PROCEED';
  return (
    <span
      className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase ${
        isAllowed
          ? 'bg-emerald-500/20 text-emerald-400'
          : 'bg-amber-500/20 text-amber-400'
      }`}
    >
      {decision}
    </span>
  );
}

function AnchoringBadge({ status }: { status: string }) {
  const isAnchored = status === 'anchored';
  return (
    <span
      className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase ${
        isAnchored
          ? 'bg-emerald-500/20 text-emerald-400'
          : 'bg-zinc-500/20 text-zinc-400'
      }`}
    >
      {status}
    </span>
  );
}

function CertificateFieldGroup({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-terminal-surface rounded-lg p-4 border border-terminal-border">
      <h3 className="text-xs font-semibold text-terminal-text uppercase tracking-wider mb-3">
        {title}
      </h3>
      <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">{children}</dl>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <>
      <dt className="text-terminal-text-muted">{label}</dt>
      <dd className="font-mono text-terminal-text break-all">{children}</dd>
    </>
  );
}

export function InvestigationCertificateView({
  certificate,
}: {
  certificate: InvestigationCertificate;
}) {
  return (
    <div className="space-y-4">
      {/* Header */}
      <CertificateFieldGroup title="Certificate Identity">
        <Field label="Certificate ID">{certificate.certificate_id}</Field>
        <Field label="Theatre ID">{certificate.theatre_id || '—'}</Field>
        <Field label="Construct ID">{certificate.construct_id || '—'}</Field>
        <Field label="Inquiry Class">{certificate.inquiry_class}</Field>
        <Field label="Issued At">
          {new Date(certificate.issued_at).toLocaleString()}
        </Field>
        <Field label="Methodology">{certificate.methodology_version}</Field>
        <Field label="Toolset">{certificate.toolset_version}</Field>
      </CertificateFieldGroup>

      {/* Stop Condition */}
      <CertificateFieldGroup title="Stop Condition">
        <Field label="Condition">{certificate.stop_condition}</Field>
        <Field label="Config">
          {Object.keys(certificate.stop_config).length > 0
            ? JSON.stringify(certificate.stop_config)
            : '—'}
        </Field>
      </CertificateFieldGroup>

      {/* Timestamps */}
      <CertificateFieldGroup title="Investigation Timeline">
        <Field label="Started">
          {new Date(certificate.investigation_started_at).toLocaleString()}
        </Field>
        <Field label="Completed">
          {new Date(certificate.investigation_completed_at).toLocaleString()}
        </Field>
      </CertificateFieldGroup>

      {/* Evidence Summary */}
      <CertificateFieldGroup title="Evidence Envelope">
        <Field label="Items">{certificate.evidence_item_count}</Field>
        <Field label="Redactions">{certificate.evidence_redaction_count}</Field>
        <Field label="Envelope Hash">
          {certificate.evidence_envelope_hash.substring(0, 20)}...
        </Field>
        <Field label="Provenance">
          {Object.entries(certificate.provenance_summary)
            .map(([k, v]) => `${k}: ${v}`)
            .join(', ') || '—'}
        </Field>
      </CertificateFieldGroup>

      {/* Claims Summary */}
      <CertificateFieldGroup title="Claim Graph">
        <Field label="Claims">{certificate.claim_count}</Field>
        <Field label="Root Hash">
          {certificate.claim_graph_root_hash.substring(0, 20)}...
        </Field>
        <Field label="Status Summary">
          {Object.entries(certificate.claim_status_summary)
            .map(([k, v]) => `${k}: ${v}`)
            .join(', ') || '—'}
        </Field>
      </CertificateFieldGroup>

      {/* Counter-Signals */}
      <CertificateFieldGroup title="Counter-Signals">
        <Field label="Checked">{certificate.counter_signals_checked}</Field>
        <Field label="Gaps">{certificate.counter_signals_gaps}</Field>
        <Field label="Material">{certificate.counter_signals_material}</Field>
      </CertificateFieldGroup>

      {/* Drift */}
      <CertificateFieldGroup title="Drift Assessment">
        <Field label="Events">{certificate.drift_event_count}</Field>
        <Field label="Material Drift">
          <span className={certificate.has_material_drift ? 'text-red-400' : 'text-emerald-400'}>
            {certificate.has_material_drift ? 'YES' : 'NO'}
          </span>
        </Field>
      </CertificateFieldGroup>

      {/* Routing */}
      <CertificateFieldGroup title="Routing Decision">
        <Field label="Decision">
          <RoutingHintBadge decision={certificate.routing_decision} />
        </Field>
        <Field label="Reason">{certificate.routing_reason}</Field>
      </CertificateFieldGroup>

      {/* Anchoring */}
      <CertificateFieldGroup title="Anchoring">
        <Field label="Status">
          <AnchoringBadge status={certificate.anchoring_status} />
        </Field>
        <Field label="TX Hash">{certificate.anchoring_tx_hash ?? '—'}</Field>
      </CertificateFieldGroup>

      {/* Hashes */}
      <CertificateFieldGroup title="Certificate Hash">
        <Field label="Hash">{certificate.certificate_hash}</Field>
      </CertificateFieldGroup>
    </div>
  );
}
