import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, GitBranch, AlertTriangle, Zap } from 'lucide-react';
import { Watchlist } from '../components/fieldkit/Watchlist';
import { LaunchpadRail } from '../components/home/LaunchpadRail';
import { useParadoxes } from '../hooks/useParadoxes';
import { useBreaches } from '../hooks/useBreaches';
import { getHomePreference, setHomePreference, type HomePreference } from '../lib/userPrefs';

/**
 * Live Now Ribbon Component
 * 
 * Compact ribbon showing live activity metrics:
 * - Fork Live count
 * - Paradox Active count
 * - Breaches count
 */
function LiveNowRibbon() {
  const { data: paradoxData } = useParadoxes();
  const { data: breaches } = useBreaches();
  
  // Mock fork live count (would come from API in production)
  const forkLiveCount = 12;
  const paradoxActiveCount = paradoxData?.total_active || 0;
  const breachesActiveCount = breaches?.filter((b) => b.status === 'active').length || 0;

  return (
    <div className="bg-[#111111] border border-[#1A1A1A] rounded-lg p-3 mb-4">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
        <span className="text-xs font-semibold text-terminal-text uppercase tracking-wide">
          Live Now
        </span>
      </div>
      <div className="flex items-center gap-4 flex-wrap">
        {/* Fork Live */}
        <div className="flex items-center gap-2">
          <GitBranch className="w-4 h-4 text-[#00D4FF]" />
          <div className="flex flex-col">
            <span className="text-xs text-terminal-muted">Forks Live</span>
            <span className="text-sm font-mono font-bold text-terminal-text">
              {forkLiveCount}
            </span>
          </div>
        </div>

        {/* Paradox Active */}
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-[#FF3B3B]" />
          <div className="flex flex-col">
            <span className="text-xs text-terminal-muted">Paradox Active</span>
            <span className="text-sm font-mono font-bold text-terminal-text">
              {paradoxActiveCount}
            </span>
          </div>
        </div>

        {/* Breaches */}
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-500" />
          <div className="flex flex-col">
            <span className="text-xs text-terminal-muted">Breaches</span>
            <span className="text-sm font-mono font-bold text-terminal-text">
              {breachesActiveCount}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * HomePage Component
 * 
 * Main home page with two-column layout:
 * - Left: Markets (Watchlist with Live Now ribbon)
 * - Right: LaunchpadRail
 */
export function HomePage() {
  const navigate = useNavigate();
  const [homePref, setHomePref] = useState<HomePreference>(getHomePreference());

  const handleCreateTimeline = () => {
    // Set preference to launchpad when user clicks CREATE TIMELINE
    setHomePreference('launchpad');
    setHomePref('launchpad');
    navigate('/launchpad/new');
  };

  const handleToggleHomePref = () => {
    const newPref: HomePreference = homePref === 'launchpad' ? 'markets' : 'launchpad';
    setHomePreference(newPref);
    setHomePref(newPref);
  };

  return (
    <div className="h-full flex flex-col gap-4">
      {/* Header Section */}
      <div className="flex items-center justify-between flex-shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-terminal-text uppercase tracking-wide">
            Home
          </h1>
          <p className="text-sm text-terminal-muted mt-1">
            Monitor markets and discover new launches
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Home Preference Toggle */}
          <button
            onClick={handleToggleHomePref}
            className="flex items-center gap-2 px-3 py-1.5 text-xs bg-terminal-bg border border-terminal-border rounded hover:border-[#00D4FF] transition"
            title="Toggle default start page"
          >
            <span className="text-terminal-muted">Default start:</span>
            <span className="text-terminal-text font-semibold">
              {homePref === 'launchpad' ? 'Launches' : 'Markets'}
            </span>
          </button>
          <button
            onClick={handleCreateTimeline}
            className="flex items-center gap-2 px-4 py-2 text-sm bg-terminal-bg border border-terminal-border rounded hover:border-[#00D4FF] hover:text-[#00D4FF] transition"
          >
            <Plus className="w-4 h-4" />
            CREATE TIMELINE
          </button>
        </div>
      </div>

      {/* Two-Column Layout */}
      <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Left Column: Markets */}
        <div className="flex flex-col min-h-0">
          <div className="flex-shrink-0 mb-4">
            <LiveNowRibbon />
          </div>
          <div className="flex-1 min-h-0 overflow-hidden">
            <div className="h-full overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
              <Watchlist />
            </div>
          </div>
        </div>

        {/* Right Column: Launchpad */}
        <div className="flex flex-col min-h-0">
          <div className="flex-1 min-h-0 overflow-hidden">
            <div className="h-full overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
              <LaunchpadRail />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
