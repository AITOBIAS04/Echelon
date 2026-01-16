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
      className="w-full bg-[#111111] border-2 border-dashed border-[#333] rounded-lg p-6 hover:border-[#00D4FF] hover:bg-[#0D0D0D] transition-all group"
    >
      <div className="flex flex-col items-center justify-center text-center">
        <div className="relative mb-4">
          <div className="w-16 h-16 bg-[#00D4FF]/10 rounded-full flex items-center justify-center group-hover:bg-[#00D4FF]/20 transition">
            <Plus className="w-8 h-8 text-[#00D4FF]" />
          </div>
          <Sparkles className="w-5 h-5 text-[#00D4FF] absolute -top-1 -right-1 opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>
        <h3 className="text-lg font-bold text-terminal-text uppercase tracking-wide mb-2">
          Create New Timeline
        </h3>
        <p className="text-sm text-terminal-muted max-w-xs">
          Launch a new theatre simulation or OSINT feed. Start from scratch or use a template.
        </p>
      </div>
    </button>
  );
}
