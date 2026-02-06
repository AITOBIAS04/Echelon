import { Sparkles, FileText } from 'lucide-react';
import { useLaunchpadFeed } from '../../hooks/useLaunchpadFeed';
import { CreateTimelineCard } from './CreateTimelineCard';
import { LaunchCardMini } from './LaunchCardMini';

/**
 * LaunchpadRail Props
 */
export interface LaunchpadRailProps {
  /** Hide the Create Timeline card */
  hideCreateCard?: boolean;
}

/**
 * LaunchpadRail Component
 * 
 * Displays launchpad feed with sections for:
 * - Create Timeline CTA (optional)
 * - Trending Launches
 * - Your Drafts
 * - Recently Graduated
 */
export function LaunchpadRail({ hideCreateCard = false }: LaunchpadRailProps) {
  const { feed, loading, error } = useLaunchpadFeed();

  if (loading) {
    return (
      <div className="w-full py-8">
        <div className="flex items-center justify-center">
          <div className="text-terminal-text-muted animate-pulse">Loading launchpad...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full py-8">
        <div className="flex flex-col items-center justify-center text-center">
          <Sparkles className="w-12 h-12 text-red-500 mb-4 opacity-50" />
          <p className="text-lg font-semibold text-terminal-text mb-2">Error loading launchpad</p>
          <p className="text-sm text-terminal-text-muted">{error}</p>
        </div>
      </div>
    );
  }

  if (!feed) {
    return null;
  }

  return (
    <div className="w-full space-y-8">
      {/* Create Timeline Card (optional) */}
      {!hideCreateCard && (
        <section>
          <h2 className="text-sm font-semibold text-terminal-text-muted uppercase tracking-wide mb-4">
            Quick Actions
          </h2>
          <CreateTimelineCard />
        </section>
      )}

      {/* Trending Launches */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="w-4 h-4 text-echelon-cyan" />
          <h2 className="text-sm font-semibold text-terminal-text uppercase tracking-wide">
            Trending Launches
          </h2>
        </div>
        {feed.trending.length === 0 ? (
          <div className="text-center py-8 text-terminal-text-muted text-sm">
            No trending launches
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
            {feed.trending.slice(0, 5).map((launch) => (
              <LaunchCardMini key={launch.id} launch={launch} />
            ))}
          </div>
        )}
      </section>

      {/* Your Drafts */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <FileText className="w-4 h-4 text-terminal-text-muted" />
          <h2 className="text-sm font-semibold text-terminal-text uppercase tracking-wide">
            Your Drafts
          </h2>
        </div>
        {feed.drafts.length === 0 ? (
          <div className="bg-terminal-panel border border-terminal-border rounded-lg p-8 text-center">
            <FileText className="w-12 h-12 text-terminal-text-muted mx-auto mb-3 opacity-50" />
            <p className="text-sm text-terminal-text-muted mb-2">No drafts yet</p>
            <p className="text-xs text-terminal-text-muted">
              Create your first timeline launch to get started
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {feed.drafts.map((launch) => (
              <LaunchCardMini key={launch.id} launch={launch} />
            ))}
          </div>
        )}
      </section>

      {/* Recently Graduated */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <div className="w-4 h-4 rounded-full bg-status-success opacity-50" />
          <h2 className="text-sm font-semibold text-terminal-text uppercase tracking-wide">
            Recently Graduated
          </h2>
        </div>
        {feed.recentlyGraduated.length === 0 ? (
          <div className="text-center py-8 text-terminal-text-muted text-sm">
            No recently graduated launches
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {feed.recentlyGraduated.slice(0, 3).map((launch) => (
              <LaunchCardMini key={launch.id} launch={launch} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
