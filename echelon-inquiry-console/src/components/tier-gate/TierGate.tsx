import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useInquiryFlow } from '../../hooks/useInquiryFlow';
import { ModelPoolMap } from './ModelPoolMap';
import { ConstraintYieldingIndicator } from './ConstraintYieldingIndicator';

export function TierGate() {
  const navigate = useNavigate();
  const [state, dispatch] = useInquiryFlow();

  // Navigation guard
  useEffect(() => {
    if (!state.certificate) {
      navigate('/signal-feed', { replace: true });
    }
  }, [state.certificate, navigate]);

  const cert = state.certificate;
  if (!cert) return null;

  const currentTier = cert.verification_tier;
  const replayCount = cert.replay_count;
  const remainingForBacktested = Math.max(0, 50 - replayCount);

  return (
    <div className="animate-fade-slide-up">
      <h2 className="mb-6 text-lg font-semibold text-echelon-navy">
        Tier Assignment
      </h2>

      {/* Model Pool Map */}
      <div className="mb-8">
        <ModelPoolMap currentTier={currentTier} />
      </div>

      {/* Journey Indicator */}
      <div className="mb-8 rounded-lg border border-echelon-border bg-white p-5">
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-echelon-navy">
          Promotion Journey
        </h3>
        <div className="flex items-center gap-2 text-sm">
          <span className="rounded bg-amber-100 px-2 py-1 font-semibold text-amber-800">
            {currentTier}
          </span>
          <span className="font-mono text-xs text-slate-400">
            &mdash; {remainingForBacktested} more replays needed &mdash;&gt;
          </span>
          <span className="rounded bg-blue-100 px-2 py-1 font-semibold text-blue-800">
            BACKTESTED
          </span>
          <span className="font-mono text-xs text-slate-400">
            &mdash; 3 months + telemetry &mdash;&gt;
          </span>
          <span className="rounded bg-emerald-100 px-2 py-1 font-semibold text-emerald-800">
            PROVEN
          </span>
        </div>
      </div>

      {/* Constraint Yielding */}
      <div className="mb-8">
        <ConstraintYieldingIndicator
          declaredReview="skip"
          effectiveReview="full"
          tier={currentTier}
        />
      </div>

      {/* Restart Demo */}
      <div className="text-centre">
        <button
          onClick={() => {
            dispatch({ type: 'RESET' });
            navigate('/signal-feed');
          }}
          className="rounded-md border border-echelon-border px-6 py-2.5 font-medium text-slate-600 transition-colors hover:bg-slate-50"
        >
          Restart Demo
        </button>
      </div>
    </div>
  );
}
