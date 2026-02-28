import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useInquiryFlow } from '../../hooks/useInquiryFlow';
import { TierBadge } from './TierBadge';
import { CriteriaBreakdown } from './CriteriaBreakdown';
import { ReproducibilityPins } from './ReproducibilityPins';
import { HashVerificationPanel } from './HashVerificationPanel';
import { COMMITMENT_TARGETS } from '../../data/templates';

export function CertificateView() {
  const navigate = useNavigate();
  const [state, dispatch] = useInquiryFlow();
  const [displayScore, setDisplayScore] = useState(0);
  const [showRawJson, setShowRawJson] = useState(false);
  const animRef = useRef<number | null>(null);

  // Navigation guard
  useEffect(() => {
    if (!state.certificate) {
      navigate('/signal-feed', { replace: true });
    }
  }, [state.certificate, navigate]);

  const cert = state.certificate;

  // Animated score count-up
  useEffect(() => {
    if (!cert) return;
    const target = cert.composite_score;
    const startTime = performance.now();
    const duration = 1000;

    function animate(now: number) {
      const elapsed = now - startTime;
      const t = Math.min(elapsed / duration, 1);
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplayScore(target * eased);

      if (t < 1) {
        animRef.current = requestAnimationFrame(animate);
      }
    }

    animRef.current = requestAnimationFrame(animate);
    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };
  }, [cert]);

  if (!cert) return null;

  const commitmentTarget = COMMITMENT_TARGETS[cert.template_id];

  return (
    <div className="animate-fade-slide-up mx-auto max-w-3xl">
      <div className="rounded-lg border border-echelon-border bg-white p-8 shadow-sm">
        {/* Header */}
        <div className="mb-6 text-centre">
          <h2 className="text-sm font-semibold uppercase tracking-widest text-echelon-navy">
            Calibration Certificate
          </h2>
          <p className="mt-1 font-mono text-xs text-slate-500">
            {cert.certificate_id}
          </p>
          <p className="mt-0.5 text-xs text-slate-400">
            Issued: {new Date(cert.issued_at).toLocaleDateString('en-GB')}
          </p>
        </div>

        {/* Composite Score */}
        <div className="mb-6 flex items-center justify-center gap-4">
          <span className="font-mono text-5xl font-bold text-echelon-navy">
            {displayScore.toFixed(4)}
          </span>
          <TierBadge tier={cert.verification_tier} size="lg" />
        </div>

        <p className="mb-8 text-centre text-sm text-slate-500">
          {cert.replay_count} episodes scored across {cert.criteria_ids.length}{' '}
          criteria
        </p>

        {/* Criteria Breakdown */}
        <div className="mb-8">
          <CriteriaBreakdown criteriaScores={cert.criteria_scores} />
        </div>

        {/* Reproducibility Pins */}
        <div className="mb-8">
          <ReproducibilityPins
            constructVersion={cert.construct_version}
            scorerVersion={cert.scorer_version}
            methodology={cert.methodology}
            datasetHashes={
              commitmentTarget
                ? commitmentTarget.dataset_hashes
                : { ground_truth: cert.dataset_hash }
            }
            evidenceBundleHash={cert.evidence_bundle_hash}
            commitmentHash={cert.commitment_hash}
          />
        </div>

        {/* Hash Verification */}
        <div className="mb-8">
          <HashVerificationPanel
            commitmentHashFromConfig={
              state.selectedTemplate?.commitment_hash ?? ''
            }
            commitmentHashFromCert={cert.commitment_hash}
            merkleRoot={cert.evidence_bundle_hash}
            datasetHashMatch={true}
          />
        </div>

        {/* Raw JSON Toggle */}
        <div className="mb-6">
          <button
            onClick={() => setShowRawJson((v) => !v)}
            className="text-sm font-medium text-echelon-blue hover:underline"
          >
            {showRawJson ? 'Hide Raw JSON' : 'View Raw JSON'}
          </button>
          {showRawJson && (
            <pre className="mt-3 max-h-96 overflow-auto rounded-md bg-echelon-data-bg p-4 font-mono text-xs text-echelon-data-text">
              {JSON.stringify(cert, null, 2)}
            </pre>
          )}
        </div>

        {/* Navigate to Tier Gate */}
        <div className="text-centre">
          <button
            onClick={() => {
              dispatch({ type: 'GO_TO_STEP', payload: 5 });
              navigate('/tier-gate');
            }}
            className="rounded-md bg-echelon-navy px-6 py-2.5 font-medium text-white transition-colors hover:bg-opacity-90"
          >
            View Tier Assignment
          </button>
        </div>
      </div>
    </div>
  );
}
