import { useState } from 'react';
import { Eye, Plus } from 'lucide-react';
import { useWatchlist, getFilteredCount } from '../../hooks/useWatchlist';
import type { WatchlistFilter } from '../../types/watchlist';
import { WatchlistFilterBar } from './WatchlistFilterBar';
import { WatchlistRow } from './WatchlistRow';

/**
 * Watchlist Component
 * 
 * Enhanced Watchlist view with filtering, telemetry metrics, and real-time updates.
 * Displays timelines with comprehensive risk indicators including logic gap,
 * paradox proximity, entropy trends, and sabotage activity.
 */
export function Watchlist() {
  const [activeFilter, setActiveFilter] = useState<WatchlistFilter>('all');
  
  // Fetch filtered watchlist data
  const { data: filteredTimelines, isLoading, error } = useWatchlist(activeFilter);
  
  // Fetch all timelines for filter counts
  const { data: allTimelines } = useWatchlist('all');
  
  // Calculate counts for each filter
  const counts = {
    'all': allTimelines?.length || 0,
    'brittle': getFilteredCount(allTimelines || [], 'brittle'),
    'paradox-watch': getFilteredCount(allTimelines || [], 'paradox-watch'),
    'high-entropy': getFilteredCount(allTimelines || [], 'high-entropy'),
    'under-attack': getFilteredCount(allTimelines || [], 'under-attack'),
  };

  const handleRemove = (id: string) => {
    // TODO: Implement remove from watchlist API call
    console.log('Remove timeline:', id);
  };

  const handleNavigate = (id: string) => {
    // TODO: Implement navigation to timeline detail page
    console.log('Navigate to timeline:', id);
    // Example: navigate(`/timeline/${id}`);
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Eye className="w-4 h-4 text-echelon-cyan" />
          <span className="text-sm text-terminal-text">
            {isLoading ? 'Loading...' : `Watching ${filteredTimelines?.length || 0} timelines`}
          </span>
        </div>
        <button className="flex items-center gap-2 px-3 py-1.5 text-xs bg-terminal-bg border border-terminal-border rounded hover:border-echelon-cyan transition">
          <Plus className="w-3 h-3" />
          Add Timeline
        </button>
      </div>

      {/* Filter Bar */}
      <div className="mb-4">
        <WatchlistFilterBar
          activeFilter={activeFilter}
          onFilterChange={setActiveFilter}
          counts={counts}
        />
      </div>

      {/* Error State */}
      {error && (
        <div className="terminal-panel p-4 text-sm text-echelon-red">
          Error loading watchlist: {error.message}
        </div>
      )}

      {/* Loading State */}
      {isLoading && !filteredTimelines && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-terminal-muted text-sm">Loading timelines...</div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && (!filteredTimelines || filteredTimelines.length === 0) && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Eye className="w-12 h-12 text-terminal-muted mx-auto mb-2 opacity-50" />
            <p className="text-terminal-muted text-sm">
              {activeFilter === 'all' 
                ? 'No timelines in watchlist yet'
                : `No timelines match the "${activeFilter}" filter`
              }
            </p>
          </div>
        </div>
      )}

      {/* Watchlist Items */}
      {!isLoading && !error && filteredTimelines && filteredTimelines.length > 0 && (
        <div className="flex-1 overflow-y-auto space-y-3 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
          {filteredTimelines.map((timeline) => (
            <WatchlistRow
              key={timeline.id}
              timeline={timeline}
              onRemove={handleRemove}
              onNavigate={handleNavigate}
            />
          ))}
        </div>
      )}
    </div>
  );
}
