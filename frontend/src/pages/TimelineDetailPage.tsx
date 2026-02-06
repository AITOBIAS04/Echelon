import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, MoreVertical, AlertTriangle } from 'lucide-react';
import { useTimelineDetail } from '../hooks/useTimelineDetail';
import { HealthMetricsPanel } from '../components/timeline/HealthMetricsPanel';
import { ParadoxPanel } from '../components/timeline/ParadoxPanel';
import { ForkTape } from '../components/timeline/ForkTape';
import { SabotageHistoryPanel } from '../components/timeline/SabotageHistoryPanel';
import { EvidenceLedger } from '../components/timeline/EvidenceLedger';
import { ForkCountdownRibbon } from '../components/timeline/ForkCountdownRibbon';
import { useMemo } from 'react';

/**
 * Skeleton Loader Component
 */
function SkeletonPanel({ className = '' }: { className?: string }) {
  return (
    <div className={`bg-terminal-panel rounded-lg p-4 border border-terminal-border animate-pulse ${className}`}>
      <div className="h-4 bg-terminal-card rounded w-1/3 mb-4"></div>
      <div className="space-y-2">
        <div className="h-3 bg-terminal-card rounded w-full"></div>
        <div className="h-3 bg-terminal-card rounded w-5/6"></div>
        <div className="h-3 bg-terminal-card rounded w-4/6"></div>
      </div>
    </div>
  );
}

/**
 * TimelineDetailPage Component
 * 
 * Main page component for displaying detailed timeline information.
 * Assembles all timeline detail components in a responsive layout.
 */
export function TimelineDetailPage() {
  const { timelineId } = useParams<{ timelineId: string }>();
  const navigate = useNavigate();
  const { data, isLoading, isError, error, refetch } = useTimelineDetail(timelineId);

  const handleExtract = () => {
    // TODO: Implement paradox extraction API call
    console.log('Extract paradox for timeline:', timelineId);
  };

  const handleForkClick = (forkId: string) => {
    // TODO: Navigate to fork detail or show modal
    console.log('Fork clicked:', forkId);
  };

  const handleEvidenceClick = (entryId: string) => {
    // TODO: Show evidence detail or highlight contradiction
    console.log('Evidence clicked:', entryId);
  };

  // Determine activeFork and nextFork from timeline data
  const { activeFork, nextFork } = useMemo(() => {
    if (!data) return { activeFork: undefined, nextFork: undefined };

    const now = new Date().getTime();
    
    // Find active fork (open, locked, or executing)
    const active = data.forkTape.find(
      (fork) => fork.status === 'open' || fork.status === 'locked' || fork.status === 'executing'
    );

    let activeForkData = undefined;
    if (active) {
      let remainingSeconds = 0;
      if (active.status === 'open' && active.lockedAt) {
        remainingSeconds = Math.max(0, Math.floor((new Date(active.lockedAt).getTime() - now) / 1000));
      } else if ((active.status === 'locked' || active.status === 'executing') && active.settledAt) {
        remainingSeconds = Math.max(0, Math.floor((new Date(active.settledAt).getTime() - now) / 1000));
      }
      
      activeForkData = {
        forkId: active.id,
        question: active.question,
        remainingSeconds,
      };
    }

    // Find next fork (settled forks sorted by timestamp, or estimate next)
    // For mock purposes, we'll use the most recent settled fork's timestamp + some time
    const settledForks = data.forkTape.filter((f) => f.status === 'settled');
    let nextForkData = undefined;
    
    if (settledForks.length > 0 && !active) {
      // Estimate next fork will open in 30 minutes
      const mostRecentSettled = settledForks.sort(
        (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      )[0];
      const etaSeconds = 30 * 60; // 30 minutes
      
      nextForkData = {
        forkId: `next_${mostRecentSettled.id}`,
        question: 'Next fork question will appear here',
        etaSeconds,
      };
    }

    return { activeFork: activeForkData, nextFork: nextForkData };
  }, [data]);

  return (
    <div className="h-full overflow-y-auto bg-terminal-panel p-6 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/fieldkit')}
              className="flex items-center gap-2 text-sm text-terminal-text-muted hover:text-terminal-text transition"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Watchlist
            </button>
            {isLoading ? (
              <div className="h-8 bg-terminal-card rounded w-64 animate-pulse"></div>
            ) : (
              <h1 className="text-2xl font-bold text-terminal-text">
                {data?.name || 'Timeline'}
              </h1>
            )}
          </div>
          <button className="p-2 text-terminal-text-muted hover:text-terminal-text transition">
            <MoreVertical className="w-5 h-5" />
          </button>
        </div>

        {/* Error State */}
        {isError && (
          <div className="bg-terminal-panel border border-echelon-red rounded-lg p-6 text-center">
            <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-terminal-text mb-2">
              Failed to load timeline
            </h3>
            <p className="text-sm text-terminal-text-muted mb-4">
              {error instanceof Error ? error.message : 'An unknown error occurred'}
            </p>
            <button
              onClick={() => refetch()}
              className="px-4 py-2 bg-terminal-panel border border-terminal-border rounded hover:border-echelon-cyan transition text-sm"
            >
              Retry
            </button>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="space-y-6">
            {/* Row 1 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <SkeletonPanel />
              <SkeletonPanel />
            </div>
            {/* Row 2 */}
            <SkeletonPanel />
            {/* Row 3 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <SkeletonPanel />
              <SkeletonPanel />
            </div>
          </div>
        )}

        {/* Content */}
        {!isLoading && !isError && data && (
          <>
            {/* Fork Countdown Ribbon */}
            <ForkCountdownRibbon activeFork={activeFork} nextFork={nextFork} />

            {/* Row 1: Health Metrics + Paradox Panel */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <HealthMetricsPanel
                history={data.healthHistory}
                currentStability={data.stability}
                currentLogicGap={data.logicGap}
                currentEntropyRate={data.entropyRate}
              />
              <ParadoxPanel
                paradoxStatus={data.paradoxStatus}
                currentLogicGap={data.logicGap}
                onExtract={handleExtract}
              />
            </div>

            {/* Row 2: Fork Tape */}
            <ForkTape timelineId={data.id} forks={data.forkTape} onForkClick={handleForkClick} />

            {/* Row 3: Sabotage History + Evidence Ledger */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <SabotageHistoryPanel events={data.sabotageHistory} />
              <EvidenceLedger entries={data.evidenceLedger} onEntryClick={handleEvidenceClick} />
            </div>

            {/* Optional Row: User Position */}
            {data.userPosition && (
              <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
                <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide mb-4">
                  Your Position
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div>
                    <div className="text-xs text-terminal-text-muted mb-1">Side</div>
                    <div
                      className={`text-lg font-mono font-bold ${
                        data.userPosition.side === 'YES' ? 'text-green-500' : 'text-red-500'
                      }`}
                    >
                      {data.userPosition.side}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-terminal-text-muted mb-1">Shares</div>
                    <div className="text-lg font-mono font-bold text-terminal-text">
                      {data.userPosition.shares.toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-terminal-text-muted mb-1">Avg Price</div>
                    <div className="text-lg font-mono font-bold text-terminal-text">
                      ${data.userPosition.avgPrice.toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-terminal-text-muted mb-1">P&L</div>
                    <div
                      className={`text-lg font-mono font-bold ${
                        data.userPosition.unrealisedPnl >= 0 ? 'text-green-500' : 'text-red-500'
                      }`}
                    >
                      {data.userPosition.unrealisedPnl >= 0 ? '+' : ''}
                      ${data.userPosition.unrealisedPnl.toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-terminal-text-muted mb-1">Burn Risk</div>
                    <div className="text-lg font-mono font-bold text-red-500">
                      ${data.userPosition.burnAtCollapse.toFixed(2)}
                    </div>
                  </div>
                </div>
                <div className="mt-4 p-3 bg-echelon-red/10 border border-echelon-red/50 rounded text-xs text-red-500">
                  <AlertTriangle className="w-4 h-4 inline mr-2" />
                  If this timeline collapses, you will lose ${data.userPosition.burnAtCollapse.toFixed(2)}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
