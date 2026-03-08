/**
 * CertificatesPage — Document ledger for settlement and verification certificates.
 *
 * Design ref: output/design_reference/echelon_certificates_v1.html
 *
 * Character: Trustworthy, archival, clean, official.
 * Like a notary's ledger or bond certificate registry.
 *
 * Implementation truth:
 *   useCertificateGallery currently surfaces theatre certificates only.
 *   Verification-source rows are deferred until the hook is extended.
 *   Fields like market title, outcome, and dispute reason are not yet
 *   available from the backend — columns show available data honestly.
 */

import { useState, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Award, Loader2, ExternalLink, ShieldCheck } from 'lucide-react';
import { useCertificateGallery, type UnifiedCertificate } from '../hooks/useCertificateGallery';
import { EmptyState } from '../components/empty-states/EmptyState';

type StatusFilter = 'all' | 'deployable' | 'not-deployable';

/** Routing hint badge — PRIMARY visual signal per design reference */
function RoutingBadge({ hint }: { hint: string | null | undefined }) {
  if (!hint) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-bold bg-terminal-panel text-terminal-text-muted border border-terminal-border">
        <span className="w-1.5 h-1.5 rounded-full bg-terminal-text-muted/40" />
        PENDING
      </span>
    );
  }
  const styles: Record<string, { bg: string; text: string; dot: string }> = {
    ALLOWED: {
      bg: 'bg-status-success/8 border-status-success/20',
      text: 'text-status-success',
      dot: 'bg-status-success',
    },
    REVIEW_REQUIRED: {
      bg: 'bg-status-warning/8 border-status-warning/20',
      text: 'text-status-warning',
      dot: 'bg-status-warning',
    },
    BLOCKED: {
      bg: 'bg-status-failure/8 border-status-failure/20',
      text: 'text-status-failure',
      dot: 'bg-status-failure',
    },
  };
  const s = styles[hint] ?? styles.ALLOWED;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-bold border ${s.bg} ${s.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`} />
      {hint.replace(/_/g, ' ')}
    </span>
  );
}

/** Verification tier badge */
function TierBadge({ tier }: { tier: string }) {
  const isEnhanced = tier.toLowerCase() === 'enhanced';
  return (
    <span
      className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${
        isEnhanced
          ? 'bg-purple-500/8 text-purple-500 border-purple-500/20'
          : 'bg-terminal-panel text-terminal-text-secondary border-terminal-border'
      }`}
    >
      {tier}
    </span>
  );
}

/** Coherence gate status badge */
function GateBadge({ status }: { status: string | null | undefined }) {
  if (!status) return null;
  const config: Record<string, string> = {
    PASSED: 'bg-status-success/10 text-status-success border-status-success/20',
    PENDING: 'bg-status-warning/10 text-status-warning border-status-warning/20',
    FAILED: 'bg-status-failure/10 text-status-failure border-status-failure/20',
  };
  return (
    <span className={`text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded border ${config[status] ?? config.PENDING}`}>
      {status}
    </span>
  );
}

/** Source badge (theatre vs verification) */
function SourceBadge({ source }: { source: string }) {
  return (
    <span
      className={`text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded border ${
        source === 'theatre'
          ? 'bg-purple-500/8 text-purple-500 border-purple-500/20'
          : 'bg-echelon-cyan/8 text-echelon-cyan border-echelon-cyan/20'
      }`}
    >
      {source}
    </span>
  );
}

function CertificateRow({ cert }: { cert: UnifiedCertificate }) {
  return (
    <tr className="border-b border-terminal-border/30 last:border-b-0 hover:bg-terminal-panel/50 transition-colors">
      {/* Certificate ID */}
      <td className="py-3.5 px-4">
        <span className="font-mono text-[12px] font-semibold text-purple-500">
          {cert.id.slice(0, 16)}
        </span>
      </td>

      {/* Construct / Source */}
      <td className="py-3.5 px-4">
        <div className="flex flex-col gap-1">
          <span className="text-[13px] font-semibold text-terminal-text leading-[18px]">
            {cert.construct_id}
          </span>
          <div className="flex items-center gap-1.5">
            <SourceBadge source={cert.source} />
            {cert.theatre_id && (
              <Link
                to={`/theatre/${cert.theatre_id}`}
                className="text-[11px] text-terminal-text-muted hover:text-purple-500 transition-colors"
              >
                {cert.theatre_id.slice(0, 12)}
              </Link>
            )}
          </div>
        </div>
      </td>

      {/* Routing / Status — PRIMARY visual signal */}
      <td className="py-3.5 px-4">
        <RoutingBadge hint={cert.routing_hint} />
      </td>

      {/* Score */}
      <td className="py-3.5 px-4 text-right">
        <span className="font-mono text-[13px] font-bold tabular-nums text-terminal-text">
          {cert.composite_score.toFixed(3)}
        </span>
      </td>

      {/* Gate */}
      <td className="py-3.5 px-4">
        <GateBadge status={cert.coherence_gate_status} />
      </td>

      {/* Tier */}
      <td className="py-3.5 px-4">
        <TierBadge tier={cert.verification_tier} />
      </td>

      {/* Issue Date */}
      <td className="py-3.5 px-4">
        <span className="font-mono text-[12px] text-terminal-text-secondary tabular-nums whitespace-nowrap">
          {new Date(cert.issued_at).toLocaleDateString()}
        </span>
      </td>

      {/* Actions */}
      <td className="py-3.5 px-4">
        <div className="flex gap-1.5 justify-end">
          {cert.theatre_id && (
            <Link
              to={`/theatre/${cert.theatre_id}`}
              className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-semibold text-terminal-text-secondary bg-terminal-surface border border-terminal-border rounded hover:border-purple-500/30 hover:text-purple-500 transition-colors"
            >
              <ExternalLink className="w-3 h-3" />
              View
            </Link>
          )}
          <Link
            to="/verify"
            className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-semibold text-status-success bg-terminal-surface border border-status-success/20 rounded hover:bg-status-success/5 transition-colors"
          >
            <ShieldCheck className="w-3 h-3" />
            Verify
          </Link>
        </div>
      </td>
    </tr>
  );
}

/** Right rail — Recent certificates, type distribution */
function RightRail({ certificates }: { certificates: UnifiedCertificate[] }) {
  const recent = certificates.slice(0, 5);
  const deployableCount = certificates.filter((c) => c.is_deployable).length;
  const notDeployable = certificates.length - deployableCount;

  return (
    <div className="flex flex-col gap-4 sticky top-6">
      {/* Recent certificates */}
      <div className="bg-terminal-surface rounded-lg border border-terminal-border overflow-hidden">
        <div className="px-4 py-2.5 border-b border-terminal-border/50 bg-terminal-panel">
          <h3 className="text-[11px] font-bold uppercase tracking-wider text-terminal-text-muted">
            Recent Certificates
          </h3>
        </div>
        <div className="px-4 py-2">
          {recent.map((cert) => (
            <div
              key={cert.id}
              className="flex items-center justify-between py-2 border-b border-terminal-border/30 last:border-b-0"
            >
              <div className="flex flex-col gap-0.5 min-w-0 flex-1">
                <span className="text-[12px] font-semibold text-terminal-text truncate">
                  {cert.construct_id}
                </span>
                <span className="font-mono text-[10px] text-terminal-text-muted">
                  {new Date(cert.issued_at).toLocaleDateString()}
                </span>
              </div>
              <span
                className={`w-2 h-2 rounded-full shrink-0 ml-2 ${
                  cert.routing_hint === 'ALLOWED'
                    ? 'bg-status-success'
                    : cert.routing_hint === 'REVIEW_REQUIRED'
                      ? 'bg-status-warning'
                      : 'bg-terminal-text-muted/40'
                }`}
              />
            </div>
          ))}
          {recent.length === 0 && (
            <div className="py-4 text-center text-[12px] text-terminal-text-muted">
              No certificates yet
            </div>
          )}
        </div>
      </div>

      {/* Deployment readiness */}
      <div className="bg-terminal-surface rounded-lg border border-terminal-border overflow-hidden">
        <div className="px-4 py-2.5 border-b border-terminal-border/50 bg-terminal-panel">
          <h3 className="text-[11px] font-bold uppercase tracking-wider text-terminal-text-muted">
            Deployment Readiness
          </h3>
        </div>
        <div className="px-4 py-3 space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-medium text-terminal-text-secondary w-[80px] shrink-0">
              Deployable
            </span>
            <div className="flex-1 h-1.5 bg-terminal-panel rounded-full overflow-hidden">
              <div
                className="h-full bg-status-success rounded-full"
                style={{
                  width: certificates.length > 0 ? `${(deployableCount / certificates.length) * 100}%` : '0%',
                }}
              />
            </div>
            <span className="font-mono text-[10px] font-semibold text-terminal-text-muted w-[24px] text-right">
              {deployableCount}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-medium text-terminal-text-secondary w-[80px] shrink-0">
              Not Ready
            </span>
            <div className="flex-1 h-1.5 bg-terminal-panel rounded-full overflow-hidden">
              <div
                className="h-full bg-status-warning rounded-full"
                style={{
                  width: certificates.length > 0 ? `${(notDeployable / certificates.length) * 100}%` : '0%',
                }}
              />
            </div>
            <span className="font-mono text-[10px] font-semibold text-terminal-text-muted w-[24px] text-right">
              {notDeployable}
            </span>
          </div>
        </div>
      </div>

      {/* Source note */}
      <div className="bg-terminal-surface rounded-lg border border-terminal-border overflow-hidden">
        <div className="px-4 py-2.5 border-b border-terminal-border/50 bg-terminal-panel">
          <h3 className="text-[11px] font-bold uppercase tracking-wider text-terminal-text-muted">
            Source Coverage
          </h3>
        </div>
        <div className="px-4 py-3">
          <div className="text-[11px] text-terminal-text-muted leading-[18px]">
            Currently showing <strong className="text-terminal-text">theatre certificates</strong> only.
            Verification-source certificates will appear when the gallery hook is extended.
          </div>
          <div className="text-[10px] font-mono text-terminal-text-muted/40 mt-2">
            GET /api/v1/certificates
          </div>
        </div>
      </div>
    </div>
  );
}

export function CertificatesPage() {
  const navigate = useNavigate();
  const { certificates, total, isLoading, error, isEmpty } = useCertificateGallery();
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');

  const filtered = useMemo(() => {
    if (statusFilter === 'all') return certificates;
    if (statusFilter === 'deployable') return certificates.filter((c) => c.is_deployable);
    return certificates.filter((c) => !c.is_deployable);
  }, [certificates, statusFilter]);

  const deployableCount = useMemo(
    () => certificates.filter((c) => c.is_deployable).length,
    [certificates],
  );
  const notDeployableCount = certificates.length - deployableCount;
  const allowedCount = useMemo(
    () => certificates.filter((c) => c.routing_hint === 'ALLOWED').length,
    [certificates],
  );
  const reviewCount = useMemo(
    () => certificates.filter((c) => c.routing_hint === 'REVIEW_REQUIRED').length,
    [certificates],
  );

  if (error) {
    return (
      <div className="p-6 max-w-[1100px] mx-auto">
        <div className="flex items-center gap-2 p-3 bg-status-failure/10 border border-status-failure/30 rounded-lg">
          <span className="text-xs text-status-failure">
            Failed to load certificates: {error.message}
          </span>
        </div>
      </div>
    );
  }

  if (isEmpty) {
    return (
      <div className="p-6 max-w-[1100px] mx-auto">
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
      </div>
    );
  }

  return (
    <div className="p-6 max-w-[1100px] mx-auto space-y-5">
      {/* Page header */}
      <div>
        <div className="text-[11px] font-mono text-terminal-text-muted mb-0.5 uppercase tracking-wider">
          Verification / Certificates
        </div>
        <h1 className="text-2xl font-bold text-terminal-text">Certificates</h1>
        <p className="text-[13px] text-terminal-text-secondary mt-0.5">
          Settlement and verification artifacts from your markets and investigations
        </p>
      </div>

      {/* Stats bar */}
      <div className="flex gap-4 p-3 px-5 bg-terminal-surface rounded-lg border border-terminal-border flex-wrap">
        {[
          { label: 'Total\nCertificates', value: isLoading ? '...' : String(total) },
          { label: 'Routing\nAllowed', value: isLoading ? '...' : String(allowedCount), color: 'text-status-success' },
          { label: 'Review\nRequired', value: isLoading ? '...' : String(reviewCount), color: reviewCount > 0 ? 'text-status-warning' : undefined },
          { label: 'Deployable', value: isLoading ? '...' : String(deployableCount), color: 'text-status-success' },
          { label: 'Not\nDeployable', value: isLoading ? '...' : String(notDeployableCount) },
        ].map((stat) => (
          <div
            key={stat.label}
            className="flex items-center gap-2 pr-4 border-r border-terminal-border/50 last:border-r-0 last:pr-0"
          >
            <span className={`font-mono text-[17px] font-bold tabular-nums ${stat.color ?? 'text-terminal-text'}`}>
              {stat.value}
            </span>
            <span className="text-[11px] font-medium text-terminal-text-muted leading-[14px] whitespace-pre-line">
              {stat.label}
            </span>
          </div>
        ))}
      </div>

      {/* Filter bar */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex gap-0.5 bg-terminal-panel rounded-lg p-[3px] border border-terminal-border/50">
          {[
            { label: 'All', value: 'all' as StatusFilter, count: total },
            { label: 'Deployable', value: 'deployable' as StatusFilter, count: deployableCount },
            { label: 'Not Deployable', value: 'not-deployable' as StatusFilter, count: notDeployableCount },
          ].map((tab) => (
            <button
              key={tab.label}
              onClick={() => setStatusFilter(tab.value)}
              className={`flex items-center gap-[5px] px-3 py-[5px] rounded-md text-xs font-medium whitespace-nowrap transition-colors ${
                statusFilter === tab.value
                  ? 'bg-terminal-surface text-terminal-text font-semibold shadow-sm'
                  : 'text-terminal-text-secondary hover:text-terminal-text'
              }`}
            >
              {tab.label}
              <span
                className={`font-mono text-[10px] font-semibold ${
                  statusFilter === tab.value ? 'text-purple-500' : 'text-terminal-text-muted'
                }`}
              >
                {isLoading ? '...' : tab.count}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-5 h-5 text-terminal-text-muted animate-spin" />
        </div>
      )}

      {/* Content: 1fr 300px grid — ledger table + right rail */}
      {!isLoading && (
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-5 items-start">
          {/* Document ledger table */}
          <div className="bg-terminal-surface border border-terminal-border rounded-lg overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="bg-terminal-panel border-b border-terminal-border">
                  <th className="py-2.5 px-4 text-left text-[10px] font-bold uppercase tracking-wider text-terminal-text-muted whitespace-nowrap">
                    Certificate ID
                  </th>
                  <th className="py-2.5 px-4 text-left text-[10px] font-bold uppercase tracking-wider text-terminal-text-muted whitespace-nowrap">
                    Construct / Source
                  </th>
                  <th className="py-2.5 px-4 text-left text-[10px] font-bold uppercase tracking-wider text-terminal-text-muted whitespace-nowrap">
                    Routing
                  </th>
                  <th className="py-2.5 px-4 text-right text-[10px] font-bold uppercase tracking-wider text-terminal-text-muted whitespace-nowrap">
                    Score
                  </th>
                  <th className="py-2.5 px-4 text-left text-[10px] font-bold uppercase tracking-wider text-terminal-text-muted whitespace-nowrap">
                    Gate
                  </th>
                  <th className="py-2.5 px-4 text-left text-[10px] font-bold uppercase tracking-wider text-terminal-text-muted whitespace-nowrap">
                    Tier
                  </th>
                  <th className="py-2.5 px-4 text-left text-[10px] font-bold uppercase tracking-wider text-terminal-text-muted whitespace-nowrap">
                    Issued
                  </th>
                  <th className="py-2.5 px-4 text-right text-[10px] font-bold uppercase tracking-wider text-terminal-text-muted whitespace-nowrap">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((cert) => (
                  <CertificateRow key={cert.id} cert={cert} />
                ))}
              </tbody>
            </table>
            {/* Table footer */}
            <div className="flex items-center justify-between px-4 py-2.5 border-t border-terminal-border/50 bg-terminal-panel">
              <span className="text-[12px] text-terminal-text-muted">
                Showing <strong className="text-terminal-text-secondary font-semibold">{filtered.length}</strong> of{' '}
                <strong className="text-terminal-text-secondary font-semibold">{total}</strong> certificates
              </span>
              <span className="text-[10px] font-mono text-terminal-text-muted/40">
                theatre source only
              </span>
            </div>
          </div>

          {/* Right rail */}
          <div className="hidden lg:block">
            <RightRail certificates={certificates} />
          </div>
        </div>
      )}
    </div>
  );
}
