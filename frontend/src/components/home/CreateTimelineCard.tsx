import { useNavigate } from 'react-router-dom';
import { Plus, Sparkles } from 'lucide-react';
import { setHomePreference } from '../../lib/userPrefs';

/**
 * CreateTimelineCard Component
 * 
 * CTA card for creating a new timeline launch.
 * Navigates to /launchpad/new when clicked.
 * Sets home preference to 'launchpad' when clicked.
 */
export function CreateTimelineCard() {
  const navigate = useNavigate();

  const handleClick = () => {
    // Set preference to launchpad when user clicks CREATE TIMELINE
    setHomePreference('launchpad');
    navigate('/launchpad/new');
  };

  return (
    <button
      onClick={handleClick}
      className="w-full bg-slate-900 border-2 border-dashed border-terminal-border rounded-lg p-6 hover:border-status-info hover:bg-[#0D0D0D] transition-all group"
    >
      <div className="flex flex-col items-center justify-center text-center">
        <div className="relative mb-4">
          <div className="w-16 h-16 bg-status-info/10 rounded-full flex items-center justify-center group-hover:bg-status-info/20 transition">
            <Plus className="w-8 h-8 text-status-info" />
          </div>
          <Sparkles className="w-5 h-5 text-status-info absolute -top-1 -right-1 opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>
        <h3 className="text-lg font-bold text-terminal-text uppercase tracking-wide mb-2">
          Create New Timeline
        </h3>
        <p className="text-sm text-terminal-text-secondary max-w-xs">
          Launch a new theatre simulation or OSINT feed. Start from scratch or use a template.
        </p>
      </div>
    </button>
  );
}
