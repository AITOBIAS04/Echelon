import { useNavigate } from 'react-router-dom';
import { LayoutTemplate, PlayCircle, Globe, Box } from 'lucide-react';

/**
 * QuickActionsToolbar Component
 * 
 * A slim single-line toolbar with quick action buttons.
 * Designed to consume minimal vertical space (max 50px height).
 */
export function QuickActionsToolbar() {
  const navigate = useNavigate();

  const actions = [
    {
      id: 'template',
      label: 'Template',
      icon: LayoutTemplate,
      onClick: () => navigate('/launchpad/new?mode=theatre&step=template'),
    },
    {
      id: 'replay',
      label: 'Replay',
      icon: PlayCircle,
      onClick: () => navigate('/launchpad/new?mode=incident'),
    },
    {
      id: 'osint',
      label: 'OSINT',
      icon: Globe,
      onClick: () => navigate('/launchpad/new?mode=osint'),
    },
    {
      id: 'theatres',
      label: 'Theatres',
      icon: Box,
      onClick: () => navigate('/blackbox?tab=theatres'),
    },
  ];

  return (
    <div className="flex items-center gap-2 h-9">
      {actions.map((action) => {
        const Icon = action.icon;
        return (
          <button
            key={action.id}
            onClick={action.onClick}
            className="flex items-center gap-1.5 px-3 py-1.5 h-8 md:h-9 text-xs bg-transparent border border-terminal-border rounded-full hover:border-[#00D4FF] hover:text-[#00D4FF] hover:bg-[#00D4FF]/5 transition text-terminal-text"
          >
            <Icon className="w-3.5 h-3.5 flex-shrink-0" />
            <span className="text-[12px] font-medium">{action.label}</span>
          </button>
        );
      })}
    </div>
  );
}
