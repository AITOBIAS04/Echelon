import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronDown, LayoutTemplate, Upload, Globe, FileText } from 'lucide-react';

/**
 * Creation Option
 */
interface CreationOption {
  id: string;
  icon: typeof LayoutTemplate;
  title: string;
  subtext: string;
  onClick: () => void;
}

/**
 * CreationRibbon Component
 * 
 * Slim expandable ribbon for timeline creation options.
 * Expands to show 4 creation methods when hovered or clicked.
 */
export function CreationRibbon() {
  const navigate = useNavigate();
  const [isExpanded, setIsExpanded] = useState(false);

  const creationOptions: CreationOption[] = [
    {
      id: 'template',
      icon: LayoutTemplate,
      title: 'From Template',
      subtext: 'Theatres',
      onClick: () => {
        navigate('/launchpad/new?mode=theatre&step=template');
        setIsExpanded(false);
      },
    },
    {
      id: 'incident',
      icon: Upload,
      title: 'Import Incident',
      subtext: 'Real-to-Sim',
      onClick: () => {
        navigate('/launchpad/new?mode=incident');
        setIsExpanded(false);
      },
    },
    {
      id: 'osint',
      icon: Globe,
      title: 'OSINT Feed',
      subtext: 'Live Signal',
      onClick: () => {
        navigate('/launchpad/new?mode=osint');
        setIsExpanded(false);
      },
    },
    {
      id: 'blank',
      icon: FileText,
      title: 'Blank Canvas',
      subtext: 'Custom',
      onClick: () => {
        navigate('/launchpad/new');
        setIsExpanded(false);
      },
    },
  ];

  return (
    <div
      className="relative w-full transition-all duration-300 ease-in-out overflow-hidden"
      style={{ height: isExpanded ? '120px' : '40px' }}
      onMouseEnter={() => setIsExpanded(true)}
      onMouseLeave={() => setIsExpanded(false)}
    >
      {/* Default State: Slim Bar */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full h-10 flex items-center justify-between px-4 bg-black/90 backdrop-blur-sm border-b border-white/10 hover:bg-black/95 transition"
      >
        <span className="text-sm font-semibold text-white/90 uppercase tracking-wide">
          ✨ INITIALIZE NEW TIMELINE
        </span>
        <ChevronDown
          className={`w-4 h-4 text-white/70 transition-transform duration-300 ${
            isExpanded ? 'rotate-180' : ''
          }`}
        />
      </button>

      {/* Expanded State: Creation Options */}
      {isExpanded && (
        <div className="absolute top-10 left-0 right-0 bg-black/90 backdrop-blur-sm border-b border-white/10">
          <div className="px-4 py-4 grid grid-cols-4 gap-4">
            {creationOptions.map((option) => {
              const Icon = option.icon;
              return (
                <button
                  key={option.id}
                  onClick={option.onClick}
                  className="flex flex-col items-center gap-2 p-3 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 transition group"
                >
                  <Icon className="w-6 h-6 text-white/80 group-hover:text-white transition" />
                  <div className="text-center">
                    <div className="text-sm font-semibold text-white group-hover:text-white transition">
                      {option.title}
                    </div>
                    <div className="text-xs text-white/60 group-hover:text-white/80 transition">
                      {option.subtext}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
