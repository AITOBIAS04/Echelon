import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { OpsBoard } from '../components/home/OpsBoard';
import { QuickActionsToolbar } from '../components/home/QuickActionsToolbar';
import { getHomePreference, setHomePreference, type HomePreference } from '../lib/userPrefs';
import { ErrorBoundary } from '../components/system/ErrorBoundary';

/**
 * HomePage Component
 * 
 * High-density 3-column BullX-style grid layout:
 * - LEFT: New Creations (Sandbox and Pilot)
 * - CENTER: Active Alpha (Fork Soon < 10m, Disclosure Active)
 * - RIGHT: Risk & Results (At Risk on top, Recently Graduated on bottom)
 */
export function HomePage() {
  console.log('HomePage Rendered');
  
  const navigate = useNavigate();
  const [homePref, setHomePref] = useState<HomePreference>(getHomePreference());

  const handleCreateTimeline = () => {
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
    <div className="h-full min-h-0 flex flex-col overflow-hidden">
      {/* Header area always visible */}
      <div className="flex-shrink-0 px-4 pt-4 pb-3 flex flex-col gap-3">
        {/* Slim Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-lg md:text-xl font-bold text-terminal-text uppercase tracking-wide">
            OPS BOARD
          </h1>
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

        {/* Quick Actions Toolbar - Slim horizontal toolbar */}
        <QuickActionsToolbar />
      </div>

      {/* Scroll container */}
      <div className="flex-1 min-h-0 overflow-y-auto">
        <div className="px-4 pb-4">
          <ErrorBoundary>
            <OpsBoard />
          </ErrorBoundary>
        </div>
      </div>
    </div>
  );
}
