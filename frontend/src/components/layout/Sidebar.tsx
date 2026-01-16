import { Activity, AlertTriangle, Briefcase } from 'lucide-react';
import { clsx } from 'clsx';

interface SidebarProps {
  activePanel: 'sigint' | 'paradox' | 'field-kit';
  onPanelChange: (panel: 'sigint' | 'paradox' | 'field-kit') => void;
}

const Sidebar = ({ activePanel, onPanelChange }: SidebarProps) => {
  const panels = [
    { id: 'sigint' as const, label: 'SIGINT', icon: Activity },
    { id: 'paradox' as const, label: 'Paradox', icon: AlertTriangle },
    { id: 'field-kit' as const, label: 'Field Kit', icon: Briefcase },
  ];

  return (
    <aside className="w-48 border-r border-terminal-border bg-terminal-panel p-4 relative z-10">
      <nav className="space-y-2">
        {panels.map((panel) => {
          const Icon = panel.icon;
          const isActive = activePanel === panel.id;
          
          return (
            <button
              key={panel.id}
              onClick={() => {
                console.log('[Sidebar] Clicked panel:', panel.id);
                onPanelChange(panel.id);
              }}
              className={clsx(
                'w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors relative z-10',
                isActive
                  ? 'bg-terminal-border text-echelon-cyan'
                  : 'text-terminal-muted hover:text-terminal-text hover:bg-terminal-border/50'
              )}
              style={{ pointerEvents: 'auto' }}
            >
              <Icon size={18} />
              <span className="text-sm font-medium">{panel.label}</span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
};

export default Sidebar;


