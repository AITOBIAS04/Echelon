import { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import type {
  WatchlistSavedView,
  WatchlistSortKey,
  WatchlistSortDir,
  WatchlistFilterConfig,
} from '../../types/presets';

export interface SavedViewEditorModalProps {
  view: WatchlistSavedView | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (view: WatchlistSavedView) => void;
}

const SORT_KEYS: { value: WatchlistSortKey; label: string }[] = [
  { value: 'stability', label: 'Stability' },
  { value: 'logic_gap', label: 'Logic Gap' },
  { value: 'paradox_proximity', label: 'Paradox Proximity' },
  { value: 'entropy_rate', label: 'Entropy Rate' },
  { value: 'sabotage_heat', label: 'Sabotage Heat' },
  { value: 'next_fork_eta', label: 'Next Fork ETA' },
];

export function SavedViewEditorModal({
  view,
  isOpen,
  onClose,
  onSave,
}: SavedViewEditorModalProps) {
  const [name, setName] = useState('');
  const [sortKey, setSortKey] = useState<WatchlistSortKey>('stability');
  const [sortDir, setSortDir] = useState<WatchlistSortDir>('desc');
  const [filter, setFilter] = useState<WatchlistFilterConfig>({});

  useEffect(() => {
    if (view) {
      setName(view.name);
      setSortKey(view.sort.key);
      setSortDir(view.sort.dir);
      setFilter(view.filter || {});
    } else {
      // Reset for new view
      setName('');
      setSortKey('stability');
      setSortDir('desc');
      setFilter({});
    }
  }, [view, isOpen]);

  if (!isOpen) return null;

  const handleSave = () => {
    if (!name.trim()) {
      alert('Please enter a name for the view');
      return;
    }

    const updatedView: WatchlistSavedView = {
      ...(view || {
        id: `view_${Date.now()}`,
        createdAt: new Date().toISOString(),
        alertRules: [],
      }),
      name: name.trim(),
      updatedAt: new Date().toISOString(),
      sort: {
        key: sortKey,
        dir: sortDir,
      },
      filter,
    };

    onSave(updatedView);
    onClose();
  };

  return (
    <div
      className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-[#0D0D0D] border border-terminal-border rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-terminal-border">
          <h3 className="text-lg font-semibold text-terminal-text uppercase tracking-wide">
            {view ? 'Edit View' : 'New View'}
          </h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-terminal-panel rounded transition"
          >
            <X className="w-5 h-5 text-terminal-muted" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-6">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-terminal-text mb-2">
              Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 bg-terminal-bg border border-terminal-border rounded text-terminal-text focus:border-echelon-cyan focus:outline-none"
              placeholder="Enter view name"
            />
          </div>

          {/* Sort */}
          <div>
            <label className="block text-sm font-medium text-terminal-text mb-2">
              Sort
            </label>
            <div className="flex gap-4">
              <select
                value={sortKey}
                onChange={(e) => setSortKey(e.target.value as WatchlistSortKey)}
                className="flex-1 px-3 py-2 bg-terminal-bg border border-terminal-border rounded text-terminal-text focus:border-echelon-cyan focus:outline-none"
              >
                {SORT_KEYS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <select
                value={sortDir}
                onChange={(e) => setSortDir(e.target.value as WatchlistSortDir)}
                className="px-3 py-2 bg-terminal-bg border border-terminal-border rounded text-terminal-text focus:border-echelon-cyan focus:outline-none"
              >
                <option value="asc">Ascending</option>
                <option value="desc">Descending</option>
              </select>
            </div>
          </div>

          {/* Filters */}
          <div>
            <label className="block text-sm font-medium text-terminal-text mb-3">
              Filters
            </label>
            <div className="space-y-4">
              {/* Query */}
              <div>
                <label className="block text-xs text-terminal-muted mb-1">
                  Search Query
                </label>
                <input
                  type="text"
                  value={filter.query || ''}
                  onChange={(e) => setFilter({ ...filter, query: e.target.value || undefined })}
                  className="w-full px-3 py-1.5 bg-terminal-bg border border-terminal-border rounded text-sm text-terminal-text focus:border-echelon-cyan focus:outline-none"
                  placeholder="Search timeline names or IDs"
                />
              </div>

              {/* Stability Range */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-terminal-muted mb-1">
                    Min Stability
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={filter.minStability ?? ''}
                    onChange={(e) => setFilter({ ...filter, minStability: e.target.value ? Number(e.target.value) : undefined })}
                    className="w-full px-3 py-1.5 bg-terminal-bg border border-terminal-border rounded text-sm text-terminal-text focus:border-echelon-cyan focus:outline-none"
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="block text-xs text-terminal-muted mb-1">
                    Max Stability
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={filter.maxStability ?? ''}
                    onChange={(e) => setFilter({ ...filter, maxStability: e.target.value ? Number(e.target.value) : undefined })}
                    className="w-full px-3 py-1.5 bg-terminal-bg border border-terminal-border rounded text-sm text-terminal-text focus:border-echelon-cyan focus:outline-none"
                    placeholder="100"
                  />
                </div>
              </div>

              {/* Logic Gap Range */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-terminal-muted mb-1">
                    Min Logic Gap
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={filter.minLogicGap ?? ''}
                    onChange={(e) => setFilter({ ...filter, minLogicGap: e.target.value ? Number(e.target.value) : undefined })}
                    className="w-full px-3 py-1.5 bg-terminal-bg border border-terminal-border rounded text-sm text-terminal-text focus:border-echelon-cyan focus:outline-none"
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="block text-xs text-terminal-muted mb-1">
                    Max Logic Gap
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={filter.maxLogicGap ?? ''}
                    onChange={(e) => setFilter({ ...filter, maxLogicGap: e.target.value ? Number(e.target.value) : undefined })}
                    className="w-full px-3 py-1.5 bg-terminal-bg border border-terminal-border rounded text-sm text-terminal-text focus:border-echelon-cyan focus:outline-none"
                    placeholder="100"
                  />
                </div>
              </div>

              {/* Toggles */}
              <div className="space-y-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={filter.paradoxOnly || false}
                    onChange={(e) => setFilter({ ...filter, paradoxOnly: e.target.checked || undefined })}
                    className="w-4 h-4 rounded border-terminal-border bg-terminal-bg text-echelon-cyan focus:ring-echelon-cyan"
                  />
                  <span className="text-sm text-terminal-text">Paradox Only</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={filter.brittleOnly || false}
                    onChange={(e) => setFilter({ ...filter, brittleOnly: e.target.checked || undefined })}
                    className="w-4 h-4 rounded border-terminal-border bg-terminal-bg text-echelon-cyan focus:ring-echelon-cyan"
                  />
                  <span className="text-sm text-terminal-text">Brittle Only (Logic Gap 40-60)</span>
                </label>
              </div>

              {/* Sabotage Heat */}
              <div>
                <label className="block text-xs text-terminal-muted mb-1">
                  Min Sabotage Heat (24h)
                </label>
                <input
                  type="number"
                  min="0"
                  value={filter.sabotageHeatMin ?? ''}
                  onChange={(e) => setFilter({ ...filter, sabotageHeatMin: e.target.value ? Number(e.target.value) : undefined })}
                  className="w-full px-3 py-1.5 bg-terminal-bg border border-terminal-border rounded text-sm text-terminal-text focus:border-echelon-cyan focus:outline-none"
                  placeholder="0"
                />
              </div>

              {/* Max Next Fork ETA */}
              <div>
                <label className="block text-xs text-terminal-muted mb-1">
                  Max Next Fork ETA (seconds)
                </label>
                <input
                  type="number"
                  min="0"
                  value={filter.maxNextForkEtaSec ?? ''}
                  onChange={(e) => setFilter({ ...filter, maxNextForkEtaSec: e.target.value ? Number(e.target.value) : undefined })}
                  className="w-full px-3 py-1.5 bg-terminal-bg border border-terminal-border rounded text-sm text-terminal-text focus:border-echelon-cyan focus:outline-none"
                  placeholder="e.g. 600 for 10 minutes"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 p-4 border-t border-terminal-border">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm bg-terminal-bg border border-terminal-border rounded hover:border-terminal-border/70 transition"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 text-sm bg-echelon-cyan/20 border border-echelon-cyan rounded text-echelon-cyan hover:bg-echelon-cyan/30 transition"
          >
            Save View
          </button>
        </div>
      </div>
    </div>
  );
}
