import { Edit2, Trash2, Plus } from 'lucide-react';
import type { WatchlistSavedView } from '../../types/presets';

export interface SavedViewsBarProps {
  views: WatchlistSavedView[];
  selectedViewId: string | null;
  onSelectView: (id: string) => void;
  onNewView: () => void;
  onEditView: (id: string) => void;
  onDeleteView: (id: string) => void;
}

export function SavedViewsBar({
  views,
  selectedViewId,
  onSelectView,
  onNewView,
  onEditView,
  onDeleteView,
}: SavedViewsBarProps) {
  const handleDelete = (id: string, name: string) => {
    if (window.confirm(`Delete saved view "${name}"?`)) {
      onDeleteView(id);
    }
  };

  return (
    <div className="flex items-center gap-2 overflow-x-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent pb-2">
      {/* New View Button */}
      <button
        onClick={onNewView}
        className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-terminal-bg border border-terminal-border rounded hover:border-echelon-cyan transition whitespace-nowrap flex-shrink-0"
      >
        <Plus className="w-3 h-3" />
        New View
      </button>

      {/* View Chips */}
      {views.map((view) => {
        const isSelected = selectedViewId === view.id;
        
        return (
          <div
            key={view.id}
            className={`
              flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition whitespace-nowrap flex-shrink-0
              ${isSelected
                ? 'bg-echelon-cyan/20 border border-echelon-cyan text-echelon-cyan'
                : 'bg-terminal-panel border border-terminal-border text-terminal-muted hover:text-terminal-text hover:border-terminal-border/70'
              }
            `}
          >
            <button
              onClick={() => onSelectView(view.id)}
              className="flex-1 text-left"
            >
              {view.name}
            </button>
            
            {isSelected && (
              <>
                <button
                  onClick={() => onEditView(view.id)}
                  className="p-0.5 hover:bg-echelon-cyan/20 rounded transition"
                  title="Edit view"
                >
                  <Edit2 className="w-3 h-3" />
                </button>
                <button
                  onClick={() => handleDelete(view.id, view.name)}
                  className="p-0.5 hover:bg-red-500/20 rounded transition text-red-400"
                  title="Delete view"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </>
            )}
          </div>
        );
      })}
    </div>
  );
}
