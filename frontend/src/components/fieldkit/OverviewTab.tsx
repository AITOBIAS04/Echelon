import { useNavigate } from 'react-router-dom';
import { AlertTriangle, ChevronRight } from 'lucide-react';
import { PortfolioRiskPanel } from '../risk/PortfolioRiskPanel';
import { useWatchlist } from '../../hooks/useWatchlist';
import { useBreaches } from '../../hooks/useBreaches';

/**
 * Active Breaches Widget
 * 
 * Compact widget showing active breaches count and top severity.
 */
function ActiveBreachesWidget() {
  const { data: breaches, isLoading } = useBreaches();

  if (isLoading) {
    return (
      <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
        <div className="animate-pulse">
          <div className="h-4 bg-terminal-card rounded w-32 mb-2"></div>
          <div className="h-6 bg-terminal-card rounded w-16"></div>
        </div>
      </div>
    );
  }

  const activeBreaches = breaches?.filter((b) => b.status === 'active') || [];
  const criticalCount = activeBreaches.filter((b) => b.severity === 'critical').length;
  const highCount = activeBreaches.filter((b) => b.severity === 'high').length;

  return (
    <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-500" />
          Active Breaches
        </h3>
        <a
          href="/breaches"
          className="text-xs text-echelon-cyan hover:underline flex items-center gap-1"
        >
          View All
          <ChevronRight className="w-3 h-3" />
        </a>
      </div>
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs text-terminal-text-muted">Total Active</span>
          <span className="text-lg font-mono font-bold text-terminal-text">
            {activeBreaches.length}
          </span>
        </div>
        {criticalCount > 0 && (
          <div className="flex items-center justify-between">
            <span className="text-xs text-terminal-text-muted">Critical</span>
            <span className="text-sm font-mono font-semibold text-red-500">
              {criticalCount}
            </span>
          </div>
        )}
        {highCount > 0 && (
          <div className="flex items-center justify-between">
            <span className="text-xs text-terminal-text-muted">High</span>
            <span className="text-sm font-mono font-semibold text-amber-500">
              {highCount}
            </span>
          </div>
        )}
        {activeBreaches.length === 0 && (
          <div className="text-xs text-terminal-text-muted text-center py-2">
            No active breaches
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Brittle Timelines Widget
 * 
 * Compact list of brittle timelines (logic gap 40-60).
 */
function BrittleTimelinesWidget() {
  const navigate = useNavigate();
  const { data: timelines, isLoading } = useWatchlist('all');

  if (isLoading) {
    return (
      <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
        <div className="animate-pulse space-y-2">
          <div className="h-4 bg-terminal-card rounded w-32 mb-3"></div>
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-8 bg-terminal-card rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  // Filter brittle timelines (logic gap 40-60)
  const brittleTimelines = (timelines || []).filter(
    (t) => t.logicGap >= 40 && t.logicGap < 60
  );

  return (
    <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide">
          Brittle Timelines
        </h3>
        <a
          href="/fieldkit?tab=watchlist"
          className="text-xs text-echelon-cyan hover:underline flex items-center gap-1"
        >
          View All
          <ChevronRight className="w-3 h-3" />
        </a>
      </div>
      {brittleTimelines.length === 0 ? (
        <div className="text-xs text-terminal-text-muted text-center py-4">
          No brittle timelines
        </div>
      ) : (
        <div className="space-y-2">
          {brittleTimelines.slice(0, 5).map((timeline) => (
            <button
              key={timeline.id}
              onClick={() => navigate(`/timeline/${timeline.id}`)}
              className="w-full text-left p-2 bg-terminal-panel border border-terminal-border rounded hover:border-echelon-cyan transition"
            >
              <div className="flex items-center justify-between">
                <span className="text-sm text-terminal-text truncate flex-1">
                  {timeline.name}
                </span>
                <span className="text-xs font-mono text-amber-500 ml-2">
                  {timeline.logicGap.toFixed(0)}%
                </span>
              </div>
              <div className="text-xs text-terminal-text-muted mt-1">
                Stability: {timeline.stability.toFixed(1)}% • Paradox: {timeline.paradoxProximity.toFixed(0)}%
              </div>
            </button>
          ))}
          {brittleTimelines.length > 5 && (
            <div className="text-xs text-terminal-text-muted text-center pt-2">
              +{brittleTimelines.length - 5} more
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Overview Tab Component
 * 
 * Main overview tab showing portfolio risk, active breaches, and brittle timelines.
 */
export function OverviewTab() {
  return (
    <div className="h-full flex flex-col gap-4">
      {/* Portfolio Risk Panel */}
      <div className="flex-1 min-h-0">
        <PortfolioRiskPanel />
      </div>

      {/* Bottom Row: Breaches and Brittle Timelines */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 flex-shrink-0">
        <ActiveBreachesWidget />
        <BrittleTimelinesWidget />
      </div>
    </div>
  );
}
