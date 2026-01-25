import { useNavigate } from 'react-router-dom';
import { Plus, Play, Globe } from 'lucide-react';

/**
 * QuickActionsToolbar Component
 * 
 * A slim single-line toolbar with quick action buttons.
 * Height: ~40px, minimal styling for maximum density.
 */
export function QuickActionsToolbar() {
  const navigate = useNavigate();

  const actions = [
    {
      id: 'template',
      label: 'Template',
      icon: Plus,
      iconChar: '＋',
      onClick: () => navigate('/launchpad/new?mode=theatre&step=template'),
    },
    {
      id: 'replay',
      label: 'Replay',
      icon: Play,
      iconChar: '▶',
      onClick: () => navigate('/launchpad/new?mode=incident'),
    },
    {
      id: 'osint',
      label: 'OSINT',
      icon: Globe,
      iconChar: '🌐',
      onClick: () => navigate('/launchpad/new?mode=osint'),
    },
  ];

  return (
    <div className="flex items-center gap-4 h-10">
      {actions.map((action) => {
        return (
          <button
            key={action.id}
            onClick={action.onClick}
            className="flex items-center gap-1.5 text-sm text-terminal-text-secondary hover:text-status-info transition"
          >
            <span>{action.iconChar}</span>
            <span>{action.label}</span>
          </button>
        );
      })}
    </div>
  );
}
