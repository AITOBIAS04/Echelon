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
