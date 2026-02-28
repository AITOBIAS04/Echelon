import { useEffect, useState, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useInquiryFlow } from '../../hooks/useInquiryFlow';
import { useExecutionSimulator } from '../../hooks/useExecutionSimulator';
import { useMarketSimulator } from '../../hooks/useMarketSimulator';
import { EpisodeProgress } from './EpisodeProgress';
import { MarketLifecycle } from './MarketLifecycle';
import { ScoreStream } from './ScoreStream';
import { EvidenceBundleBuilder } from './EvidenceBundleBuilder';
import {
  ESCROW_EPISODES,
  OSINT_EPISODES,
  GLOBAL_CONFLICT_PHASES,
  generateMinimalEpisodes,
} from '../../data/templates';
import { CERTIFICATES } from '../../data/certificates';
import { generateBundleFiles } from '../../utils/bundleFiles';
import type { Episode } from '../../types/execution';
import type { MarketPhase } from '../../types/execution';

export function ExecutionView() {
  const navigate = useNavigate();
  const [state, dispatch] = useInquiryFlow();
  const [showBanner, setShowBanner] = useState(false);

  // Navigation guard
  useEffect(() => {
    if (!state.isCommitted || !state.selectedTemplate) {
      navigate('/signal-feed', { replace: true });
    }
  }, [state.isCommitted, state.selectedTemplate, navigate]);

  const template = state.selectedTemplate;
  if (!template) return null;

  const isProduct = template.execution_path === 'PRODUCT';

  // Determine episodes or phases — memoised to prevent re-triggering simulator
  const episodes: Episode[] = useMemo(() => {
    if (!isProduct) return [];
    if (template.template_id === 'ESCROW_MILESTONE_RELEASE_V1') return ESCROW_EPISODES;
    if (template.template_id === 'OSINT_COMPOSED_ORACLE_V1') return OSINT_EPISODES;
    return generateMinimalEpisodes(template);
  }, [isProduct, template]);

  const phases: MarketPhase[] = useMemo(() => {
    if (isProduct) return [];
    if (template.template_id === 'GLOBAL_CONFLICT_V1') return GLOBAL_CONFLICT_PHASES;
    return [];
  }, [isProduct, template]);

  const onComplete = useCallback(() => {
    dispatch({ type: 'COMPLETE_EXECUTION' });
    const cert = CERTIFICATES[template.template_id];
    if (cert) {
      dispatch({ type: 'SET_CERTIFICATE', payload: cert });
    }
    setTimeout(() => setShowBanner(true), 500);
  }, [dispatch, template.template_id]);

  const { skip: skipEpisodes } = useExecutionSimulator(
    episodes,
    isProduct && state.isCommitted,
    onComplete
  );

  const { skip: skipPhases } = useMarketSimulator(
    phases,
    !isProduct && state.isCommitted,
    onComplete
  );

  const handleSkip = isProduct ? skipEpisodes : skipPhases;

  const bundleFiles = generateBundleFiles(template, isProduct ? episodes : phases);

  const totalCount = isProduct ? episodes.length : phases.length;
  const completedCount = isProduct
    ? state.executionProgress.completedEpisodes.length
    : state.executionProgress.completedPhases.length;

  return (
    <div className="animate-fade-slide-up">
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-echelon-navy">
          Construct Execution
        </h2>
        {!state.executionProgress.isComplete && (
          <button
            onClick={handleSkip}
            className="rounded-md border border-echelon-border px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50"
          >
            Skip to Results
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-11">
        <div className="md:col-span-6">
          {isProduct ? (
            <>
              <EpisodeProgress
                episodes={state.executionProgress.completedEpisodes}
                currentIndex={state.executionProgress.completedEpisodes.length}
                totalEpisodes={episodes.length}
                templateName={template.name}
                constructId={template.construct_id}
                constructVersion={template.construct_version}
              />
              <div className="mt-4">
                <ScoreStream
                  completedEpisodes={state.executionProgress.completedEpisodes}
                />
              </div>
            </>
          ) : (
            <MarketLifecycle
              phases={phases}
              currentPhaseIndex={state.executionProgress.completedPhases.length}
              templateName={template.name}
              constructId={template.construct_id}
              constructVersion={template.construct_version}
            />
          )}
        </div>

        <div className="md:col-span-5">
          <EvidenceBundleBuilder
            executionPath={template.execution_path}
            completedCount={completedCount}
            totalCount={totalCount}
            bundleFiles={bundleFiles}
          />
        </div>
      </div>

      {showBanner && (
        <div className="animate-fade-slide-up mt-6 rounded-lg border border-emerald-200 bg-emerald-50 p-6 text-centre">
          <h3 className="text-lg font-semibold text-emerald-800">
            Certificate Ready
          </h3>
          <p className="mt-1 text-sm text-emerald-700">
            All {totalCount} {isProduct ? 'episodes' : 'phases'} scored.
            Calibration certificate has been issued.
          </p>
          <button
            onClick={() => {
              dispatch({ type: 'GO_TO_STEP', payload: 4 });
              navigate('/certificate');
            }}
            className="mt-4 rounded-md bg-echelon-navy px-6 py-2.5 font-medium text-white transition-colors hover:bg-opacity-90"
          >
            View Certificate
          </button>
        </div>
      )}
    </div>
  );
}
