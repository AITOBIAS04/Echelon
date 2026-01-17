import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { OpsBoard } from '../components/home/OpsBoard';
import { LaunchpadRail } from '../components/home/LaunchpadRail';
import { QuickActionsToolbar } from '../components/home/QuickActionsToolbar';
import { CreationRibbon } from '../components/home/CreationRibbon';
import { getHomePreference, setHomePreference, type HomePreference } from '../lib/userPrefs';

/**
 * HomePage Component
 * 
 * Main home page featuring Operations Board with kanban-style lanes:
 * - New Creations
 * - About to Happen
 * - At Risk
 * - Graduation
 * 
 * Also includes optional LaunchpadRail for discovering launches.
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
    <div className="h-full flex flex-col pb-20 md:pb-4">
      {/* Creation Ribbon - Directly under main Nav */}
      <CreationRibbon />
      
      <div className="max-w-[100vw] w-full px-4 flex flex-col gap-4 pt-4 h-full">
        {/* Header Section */}
        <div className="flex flex-col gap-3 flex-shrink-0">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <h1 className="text-lg md:text-xl font-bold text-terminal-text uppercase tracking-wide">
                OPS BOARD
              </h1>
              <p className="text-xs md:text-sm text-terminal-muted mt-1">
                New creations • About to happen • At risk • Graduation
              </p>
            </div>
            <div className="flex items-center gap-2 sm:gap-3">
              {/* Home Preference Toggle - Hide on very small screens */}
              <button
                onClick={handleToggleHomePref}
                className="hidden sm:flex items-center gap-2 px-3 py-1.5 text-xs bg-terminal-bg border border-terminal-border rounded hover:border-[#00D4FF] transition"
                title="Toggle default start page"
              >
                <span className="text-terminal-muted">Default start:</span>
                <span className="text-terminal-text font-semibold">
                  {homePref === 'launchpad' ? 'Launches' : 'Markets'}
                </span>
              </button>
              <button
                onClick={handleCreateTimeline}
                className="flex items-center gap-2 px-3 md:px-4 py-1.5 md:py-2 text-xs md:text-sm bg-terminal-bg border border-terminal-border rounded hover:border-[#00D4FF] hover:text-[#00D4FF] transition whitespace-nowrap"
              >
                <Plus className="w-3.5 h-3.5 md:w-4 md:h-4" />
                <span className="hidden sm:inline">CREATE TIMELINE</span>
                <span className="sm:hidden">CREATE</span>
              </button>
            </div>
          </div>

          {/* Quick Actions Toolbar */}
          <QuickActionsToolbar />
        </div>

        {/* Main Content: Ops Board */}
        <div className="flex-1 min-h-0 overflow-hidden">
          <div className="h-full overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
            <OpsBoard />
          </div>
        </div>

        {/* Optional: Launchpad Rail (without Create Timeline card) */}
        <div className="flex-shrink-0 border-t border-[#1A1A1A] pt-4">
          <div className="h-64 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
            <LaunchpadRail hideCreateCard />
          </div>
        </div>
      </div>
    </div>
  );
}
