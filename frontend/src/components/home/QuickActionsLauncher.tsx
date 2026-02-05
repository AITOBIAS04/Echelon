import { useNavigate } from 'react-router-dom';
import { FileText, Upload, Sparkles, Layers } from 'lucide-react';

/**
 * QuickActionsLauncher Component
 * 
 * Provides quick action buttons for common timeline creation workflows.
 */
export function QuickActionsLauncher() {
  const navigate = useNavigate();

  const actions = [
    {
      id: 'template',
      label: 'Create from Template',
      icon: FileText,
      onClick: () => navigate('/launchpad/new?mode=theatre&step=template'),
    },
    {
      id: 'incident',
      label: 'Import Incident Replay',
      icon: Upload,
      onClick: () => navigate('/launchpad/new?mode=incident'),
    },
    {
      id: 'osint',
      label: 'Create OSINT Timeline',
      icon: Sparkles,
      onClick: () => navigate('/launchpad/new?mode=osint'),
    },
    {
      id: 'theatres',
      label: 'Browse Theatres',
      icon: Layers,
      onClick: () => navigate('/blackbox?tab=theatres'),
    },
  ];

  return (
    <div className="bg-slate-900 border border-[#1A1A1A] rounded-lg p-4">
      <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide mb-3">
        Quick Actions
      </h3>
      <div className="grid grid-cols-2 gap-2">
        {actions.map((action) => {
          const Icon = action.icon;
          return (
            <button
              key={action.id}
              onClick={action.onClick}
              className="flex items-center gap-2 px-3 py-2 text-xs bg-terminal-bg border border-terminal-border rounded hover:border-status-info hover:text-status-info transition text-left"
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span className="text-terminal-text">{action.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
