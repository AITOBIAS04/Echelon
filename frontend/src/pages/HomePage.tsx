import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { OpsBoard } from '../components/home/OpsBoard';
import { LaunchpadRail } from '../components/home/LaunchpadRail';
import { QuickActionsLauncher } from '../components/home/QuickActionsLauncher';
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
    <div className="h-full flex flex-col gap-4">
      {/* Header Section */}
      <div className="flex items-center justify-between flex-shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-terminal-text uppercase tracking-wide">
            OPS BOARD
          </h1>
          <p className="text-sm text-terminal-muted mt-1">
            New creations • About to happen • At risk • Graduation
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

      {/* Quick Actions Launcher */}
      <div className="flex-shrink-0">
        <QuickActionsLauncher />
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
  );
}
