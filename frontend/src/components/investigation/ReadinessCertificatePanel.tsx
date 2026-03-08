/**
 * Readiness & Certificate Lifecycle Panel
 *
 * Shows stop-condition readiness status, certificate build action,
 * and certificate lifecycle stepper (READY -> ANCHORED -> ISSUED).
 *
 * Backend truth:
 * - GET  /api/v1/investigations/{id}/readiness  → ReadinessResponse
 * - GET  /api/v1/investigations/{id}/certificate → CertificateRecordResponse (404 if none)
 * - POST /api/v1/investigations/{id}/certificate/build → 201 (409 if exists or not READY)
 * - POST /api/v1/investigations/certificates/anchor-batch → batch READY→ANCHORED→ISSUED
 *
 * Certificate lifecycle: READY → ANCHORED → ISSUED
 * ANCHORED is transient: run_batch_anchor collapses READY→ANCHORED→ISSUED in one pass.
 * Both anchored_at and issued_at receive the same batch_timestamp (00:00 UTC).
 * Routing decision (ALLOWED | REVIEW_REQUIRED) is recorded but does NOT gate batch-anchor.
 *
 * Design ref: output/design_reference/echelon_readiness_certificate_v2.html
 */

import { Loader2, ShieldCheck, AlertTriangle, CheckCircle2, Clock, Circle } from 'lucide-react';
import { useReadiness, useBuildCertificate, useCertificate } from '../../hooks/useInvestigation';
import type { CertificateLifecycleStatus } from '../../types/investigation';

/** Humanized stop-condition labels */
const STOP_LABELS: Record<string, string> = {
  OUTCOME_RESOLUTION: 'Outcome Resolution',
  EVIDENCE_THRESHOLD: 'Evidence Threshold',
  SPONSOR_DEFINED: 'Sponsor Defined',
};

/**
 * Determine step state from current certificate status.
 *
 * Note: ANCHORED is transient — run_batch_anchor collapses READY→ANCHORED→ISSUED
 * in one pass, so ANCHORED is effectively the same as ISSUED for display purposes.
 * READY is the only durable pre-terminal state (waiting for batch).
 */
function getStepStates(certStatus: CertificateLifecycleStatus | null): {
  ready: 'reached' | 'active' | 'pending';
  anchored: 'reached' | 'active' | 'pending';
  issued: 'reached' | 'active' | 'pending';
} {
  if (!certStatus) return { ready: 'pending', anchored: 'pending', issued: 'pending' };
  switch (certStatus) {
    case 'ISSUED':
    case 'ANCHORED':
      // ANCHORED collapses into ISSUED in the same batch pass
      return { ready: 'reached', anchored: 'reached', issued: 'reached' };
    case 'READY':
      return { ready: 'reached', anchored: 'active', issued: 'pending' };
    default:
      return { ready: 'pending', anchored: 'pending', issued: 'pending' };
  }
}

function StepCircle({ state }: { state: 'reached' | 'active' | 'pending' }) {
  if (state === 'reached') {
    return (
      <div className="w-10 h-10 rounded-full flex items-center justify-center bg-status-success/10 border-2 border-status-success">
        <CheckCircle2 className="w-5 h-5 text-status-success" />
      </div>
    );
  }
  if (state === 'active') {
    return (
      <div className="w-10 h-10 rounded-full flex items-center justify-center bg-echelon-cyan/10 border-2 border-echelon-cyan animate-pulse">
        <Clock className="w-4 h-4 text-echelon-cyan" />
      </div>
    );
  }
  return (
    <div className="w-10 h-10 rounded-full flex items-center justify-center bg-terminal-panel border-2 border-terminal-border">
      <Circle className="w-4 h-4 text-terminal-text-muted/40" />
    </div>
  );
}

function LifecycleStep({
  label,
  state,
  timestamp,
}: {
  label: string;
  state: 'reached' | 'active' | 'pending';
  timestamp: string | null;
}) {
  const labelColor =
    state === 'reached'
      ? 'text-status-success'
      : state === 'active'
        ? 'text-echelon-cyan'
        : 'text-terminal-text-muted/50';

  return (
    <div className="flex flex-col items-center gap-2 min-w-[100px]">
      <StepCircle state={state} />
      <div className={`text-[12px] font-semibold font-mono ${labelColor}`}>{label}</div>
      <div className="text-[10px] font-mono text-terminal-text-muted tabular-nums min-h-[14px]">
        {timestamp ? new Date(timestamp).toLocaleString() : '\u2014'}
      </div>
    </div>
  );
}

function LifecycleConnector({ reached }: { reached: boolean }) {
  return (
    <div className="flex-1 flex items-center min-w-[40px]" style={{ marginTop: -28 }}>
      <div
        className={`h-0.5 w-full rounded-full ${
          reached ? 'bg-status-success' : 'bg-terminal-border'
        }`}
      />
    </div>
  );
}

export function ReadinessCertificatePanel({
  investigationId,
}: {
  investigationId: string;
}) {
  const { readiness, isLoading: readinessLoading } = useReadiness(investigationId);
  const { certificate } = useCertificate(investigationId);
  const buildCert = useBuildCertificate(investigationId);

  if (readinessLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-5 h-5 text-terminal-text-muted animate-spin" />
      </div>
    );
  }

  if (!readiness) return null;

  const isReady = readiness.stop_condition_status === 'READY';
  const hasCertificate = readiness.has_certificate;
  const certStatus = certificate?.certificate_status ?? readiness.certificate_status;
  const steps = getStepStates(hasCertificate ? certStatus : null);

  return (
    <div className="space-y-4">
      {/* Stop Condition Readiness — sunken header section */}
      <div className="bg-terminal-surface rounded-lg border border-terminal-border overflow-hidden">
        <div className="px-5 py-2.5 border-b border-terminal-border/50 bg-terminal-panel flex items-center gap-2">
          <h3 className="text-[11px] font-bold uppercase tracking-wider text-terminal-text-muted">
            Stop Condition Readiness
          </h3>
          {readiness.stop_condition_evaluated_at && (
            <span className="font-mono text-[10px] text-terminal-text-muted/60 ml-auto">
              evaluated {new Date(readiness.stop_condition_evaluated_at).toLocaleString()}
            </span>
          )}
        </div>
        <div className="p-5">
          {/* Readiness badge */}
          <div className="mb-4">
            <span
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-[13px] font-bold ${
                isReady
                  ? 'bg-status-success/10 text-status-success border border-status-success/20'
                  : 'bg-terminal-panel text-terminal-text-muted border border-terminal-border'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  isReady ? 'bg-status-success' : 'bg-terminal-text-muted/40'
                }`}
              />
              {readiness.stop_condition_status ?? 'NOT_EVALUATED'}
            </span>
          </div>

          {/* Readiness metadata */}
          <div className="space-y-2">
            <div className="flex items-center gap-3 text-[13px]">
              <span className="text-terminal-text-muted font-semibold min-w-[120px] text-[12px]">
                Stop Condition
              </span>
              <span className="text-terminal-text font-medium">
                {STOP_LABELS[readiness.stop_condition] ?? readiness.stop_condition}
              </span>
            </div>
            <div className="flex items-start gap-3 text-[13px]">
              <span className="text-terminal-text-muted font-semibold min-w-[120px] text-[12px]">
                Detail
              </span>
              <span className="text-terminal-text font-medium">
                {readiness.stop_condition_reason ?? '\u2014'}
              </span>
            </div>
            {readiness.stop_condition_evaluated_at && (
              <div className="flex items-center gap-3 text-[13px]">
                <span className="text-terminal-text-muted font-semibold min-w-[120px] text-[12px]">
                  Last Evaluated
                </span>
                <span className="font-mono text-terminal-text text-[12px] tabular-nums">
                  {new Date(readiness.stop_condition_evaluated_at).toLocaleString()}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Build Certificate CTA — only when READY and no certificate exists */}
      {isReady && !hasCertificate && (
        <div className="flex items-center justify-between p-4 bg-echelon-cyan/5 border border-echelon-cyan/15 rounded-lg">
          <div className="text-[13px] text-terminal-text leading-5">
            <strong>Stop condition met.</strong>{' '}
            This investigation is ready for certificate issuance. The certificate will be queued for the next 00:00 UTC batch-anchor cycle.
          </div>
          <button
            onClick={() => buildCert.mutate()}
            disabled={buildCert.isPending}
            className="flex items-center gap-2 px-4 py-2 text-[13px] font-semibold bg-echelon-cyan text-terminal-bg rounded-lg hover:opacity-90 transition-colors disabled:opacity-50 shrink-0 ml-4"
          >
            {buildCert.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <ShieldCheck className="w-4 h-4" />
            )}
            Build Certificate
          </button>
        </div>
      )}

      {/* Build error */}
      {buildCert.isError && (
        <div className="flex items-center gap-2 p-3 bg-status-failure/10 border border-status-failure/30 rounded-lg">
          <AlertTriangle className="w-4 h-4 text-status-failure shrink-0" />
          <span className="text-xs text-status-failure">
            {(buildCert.error as Error)?.message ?? 'Certificate build failed'}
          </span>
        </div>
      )}

      {/* Build success feedback (transient) */}
      {buildCert.isSuccess && !hasCertificate && (
        <div className="flex items-center gap-2 p-3 bg-status-success/10 border border-status-success/30 rounded-lg">
          <CheckCircle2 className="w-4 h-4 text-status-success shrink-0" />
          <span className="text-xs text-status-success">
            Certificate built — status: {buildCert.data?.certificate_status}
          </span>
        </div>
      )}

      {/* Certificate Lifecycle stepper — always shown */}
      <div className="bg-terminal-surface rounded-lg border border-terminal-border overflow-hidden">
        <div className="px-5 py-2.5 border-b border-terminal-border/50 bg-terminal-panel flex items-center gap-2">
          <h3 className="text-[11px] font-bold uppercase tracking-wider text-terminal-text-muted">
            Certificate Lifecycle
          </h3>
          {certificate ? (
            <span className="font-mono text-[11px] font-semibold text-echelon-cyan ml-auto">
              {certificate.certificate_id.slice(0, 16)}
            </span>
          ) : (
            <span className="text-[11px] text-terminal-text-muted/50 italic ml-auto">
              {isReady ? 'Awaiting build' : 'Awaiting readiness'}
            </span>
          )}
        </div>
        <div className="py-6 px-8">
          {/* Stepper */}
          <div className="flex items-start justify-center">
            <LifecycleStep
              label="READY"
              state={steps.ready}
              timestamp={certificate?.ready_at ?? null}
            />
            <LifecycleConnector reached={steps.anchored === 'reached'} />
            <LifecycleStep
              label="ANCHORED"
              state={steps.anchored}
              timestamp={certificate?.anchored_at ?? null}
            />
            <LifecycleConnector reached={steps.issued === 'reached'} />
            <LifecycleStep
              label="ISSUED"
              state={steps.issued}
              timestamp={certificate?.issued_at ?? null}
            />
          </div>

          {/* Anchoring note when certificate is READY (waiting for batch) */}
          {certStatus === 'READY' && hasCertificate && (
            <div className="mt-4 text-center text-[11px] text-terminal-text-muted">
              Queued for next 00:00 UTC batch-anchor cycle
            </div>
          )}
        </div>

        {/* Routing decision — shown when certificate exists */}
        {certificate && (
          <div className="flex items-center gap-3 px-5 py-3 border-t border-terminal-border/50">
            <span
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-[12px] font-bold ${
                certificate.routing_decision === 'ALLOWED'
                  ? 'bg-status-success/10 text-status-success border border-status-success/20'
                  : 'bg-status-warning/10 text-status-warning border border-status-warning/20'
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  certificate.routing_decision === 'ALLOWED'
                    ? 'bg-status-success'
                    : 'bg-status-warning'
                }`}
              />
              {certificate.routing_decision.replace(/_/g, ' ')}
            </span>
            <span className="text-[12px] text-terminal-text-secondary leading-4">
              {certificate.routing_reason}
            </span>
          </div>
        )}
      </div>

      {/* Certificate hash & metadata — only when certificate exists */}
      {certificate && (
        <div className="bg-terminal-surface rounded-lg border border-terminal-border overflow-hidden">
          <div className="px-5 py-2.5 border-b border-terminal-border/50 bg-terminal-panel">
            <h3 className="text-[11px] font-bold uppercase tracking-wider text-terminal-text-muted">
              Certificate Record
            </h3>
          </div>
          <div className="p-5">
            <dl className="grid grid-cols-[140px_1fr] gap-x-4 gap-y-2 text-[13px]">
              <dt className="text-terminal-text-muted text-[12px] font-semibold">Certificate ID</dt>
              <dd className="font-mono text-terminal-text text-xs">{certificate.certificate_id}</dd>
              <dt className="text-terminal-text-muted text-[12px] font-semibold">Status</dt>
              <dd className="font-mono text-terminal-text text-xs">{certificate.certificate_status}</dd>
              <dt className="text-terminal-text-muted text-[12px] font-semibold">Hash</dt>
              <dd className="font-mono text-terminal-text text-xs break-all">
                {certificate.certificate_hash}
              </dd>
              {certificate.batch_anchor_hash && (
                <>
                  <dt className="text-terminal-text-muted text-[12px] font-semibold">Anchor Hash</dt>
                  <dd className="font-mono text-terminal-text text-xs break-all">
                    {certificate.batch_anchor_hash}
                  </dd>
                </>
              )}
            </dl>
          </div>
        </div>
      )}
    </div>
  );
}
