/**
 * CertificatesPage — Unified certificate gallery.
 *
 * Shows theatre calibration certificates and verification certificates.
 * Uses NOT_YET_GENERATED empty state when no certificates exist.
 */

import { Award } from 'lucide-react';
import { clsx } from 'clsx';
import { useNavigate } from 'react-router-dom';
import { useCertificateGallery } from '../hooks/useCertificateGallery';
import { EmptyState } from '../components/empty-states/EmptyState';
function GateStatusBadge({ status }: { status: string }) {
  const config = {
    PENDING: { color: 'bg-amber-500/20 text-amber-400 border-amber-500/30', pulse: true },
    PASSED: { color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30', pulse: false },
    FAILED: { color: 'bg-red-500/20 text-red-400 border-red-500/30', pulse: false },
  }[status] ?? { color: 'bg-neutral-500/20 text-neutral-400 border-neutral-500/30', pulse: false };

  return (
    <span className={clsx('px-2 py-0.5 rounded text-[10px] font-mono uppercase border', config.color, config.pulse && 'animate-pulse')}>
      {status}
    </span>
  );
}

function DeployableBadge({ deployable }: { deployable: boolean }) {
  return (
    <span className={clsx(
      'px-2 py-0.5 rounded text-[10px] font-mono uppercase border',
      deployable
        ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
        : 'bg-red-500/20 text-red-400 border-red-500/30',
    )}>
      {deployable ? 'DEPLOYABLE' : 'NOT DEPLOYABLE'}
    </span>
  );
}

function RoutingHintBadge({ hint }: { hint: string }) {
  const colors = {
    ALLOWED: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    REVIEW_REQUIRED: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    BLOCKED: 'bg-red-500/20 text-red-400 border-red-500/30',
  }[hint] ?? 'bg-neutral-500/20 text-neutral-400 border-neutral-500/30';

  return (
    <span className={clsx('px-2 py-0.5 rounded text-[10px] font-mono uppercase border', colors)}>
      {hint}
    </span>
  );
}

export function CertificatesPage() {
  const navigate = useNavigate();
  const { certificates, total, error, isEmpty } = useCertificateGallery();

  if (error) {
    return (
      <div className="p-6 text-status-danger text-sm">
        Failed to load certificates: {error.message}
      </div>
    );
  }

  if (isEmpty) {
    return (
      <EmptyState
        type="NOT_YET_GENERATED"
        icon={<Award className="w-6 h-6" />}
        title="No certificates yet"
        description="Certificates are generated when theatres are settled and verified. Run and settle a theatre to produce your first certificate."
        triggerText="Triggered by: Theatre settlement + verification run"
        actions={[
          {
            label: 'Browse Theatres',
            onClick: () => navigate('/theatres'),
            variant: 'primary',
          },
          {
            label: 'Verify a Certificate',
            onClick: () => navigate('/verify'),
            variant: 'secondary',
          },
        ]}
      />
    );
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <Award className="w-5 h-5 text-status-paradox" />
        <span className="text-sm font-bold text-terminal-text">
          {total} Certificate{total !== 1 ? 's' : ''}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {certificates.map((cert) => (
          <div
            key={cert.id}
            className={clsx(
              'bg-terminal-surface border border-terminal-border rounded-lg p-4',
              'hover:border-status-paradox/30 transition-colors duration-150',
            )}
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-mono text-terminal-text-muted truncate">
                {cert.construct_id}
              </span>
              <span
                className={clsx(
                  'text-[10px] font-bold uppercase px-2 py-0.5 rounded border',
                  cert.source === 'theatre'
                    ? 'bg-status-paradox/10 border-status-paradox/20 text-status-paradox'
                    : 'bg-status-info/10 border-status-info/20 text-status-info',
                )}
              >
                {cert.source}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-terminal-text-muted">Score</span>
                <div className="font-mono font-bold text-terminal-text">
                  {cert.composite_score.toFixed(3)}
                </div>
              </div>
              <div>
                <span className="text-terminal-text-muted">Tier</span>
                <div className="font-semibold text-terminal-text">
                  {cert.verification_tier}
                </div>
              </div>
            </div>

            {cert.routing_hint && (
              <div className="mt-3 flex items-center gap-2">
                <RoutingHintBadge hint={cert.routing_hint} />
              </div>
            )}

            <div className="mt-2 flex items-center gap-2 flex-wrap">
              {cert.coherence_gate_status && (
                <GateStatusBadge status={cert.coherence_gate_status} />
              )}
              <DeployableBadge deployable={cert.is_deployable} />
            </div>

            <div className="mt-3 pt-3 border-t border-terminal-border">
              <span className="text-[10px] text-terminal-text-muted">
                Issued {new Date(cert.issued_at).toLocaleDateString()}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
