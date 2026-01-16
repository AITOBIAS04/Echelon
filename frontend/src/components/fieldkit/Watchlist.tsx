import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye, Plus, AlertCircle } from 'lucide-react';
import { useWatchlist, getFilteredCount } from '../../hooks/useWatchlist';
import type { WatchlistFilter } from '../../types/watchlist';
import { WatchlistFilterBar } from './WatchlistFilterBar';
import { WatchlistRow } from './WatchlistRow';

/**
 * Skeleton Row Component
 * Loading placeholder for watchlist rows
 */
function SkeletonRow() {
  return (
    <div className="bg-[#111111] border border-[#1A1A1A] rounded-lg p-3 animate-pulse">
      <div className="flex justify-between items-center mb-3">
        <div className="h-5 bg-[#1A1A1A] rounded w-48"></div>
        <div className="flex items-center gap-2">
          <div className="h-6 bg-[#1A1A1A] rounded w-16"></div>
          <div className="h-6 bg-[#1A1A1A] rounded w-20"></div>
        </div>
      </div>
      <div className="flex items-center gap-4 mb-3">
        <div className="h-4 bg-[#1A1A1A] rounded w-32"></div>
        <div className="flex-1 h-1 bg-[#1A1A1A] rounded"></div>
      </div>
      <div className="flex justify-between items-center">
        <div className="h-5 bg-[#1A1A1A] rounded w-16"></div>
        <div className="h-4 bg-[#1A1A1A] rounded w-20"></div>
        <div className="flex gap-2">
          <div className="h-6 w-6 bg-[#1A1A1A] rounded"></div>
          <div className="h-6 w-6 bg-[#1A1A1A] rounded"></div>
        </div>
      </div>
    </div>
  );
}

/**
 * Watchlist Component
 * 
 * Enhanced Watchlist 2.0 view with filtering, telemetry metrics, and real-time updates.
 * Displays timelines with comprehensive risk indicators including logic gap,
 * paradox proximity, entropy trends, and sabotage activity.
 */
export function Watchlist() {
  const navigate = useNavigate();
  const [activeFilter, setActiveFilter] = useState<WatchlistFilter>('all');
  
  // Fetch filtered watchlist data
  const { 
    data: filteredTimelines, 
    isLoading, 
    isError, 
    error,
    refetch 
  } = useWatchlist(activeFilter);
  
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
    navigate(`/timeline/${id}`);
  };

  return (
    <div className="h-full flex flex-col p-4 gap-4">
      {/* Header Section */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-terminal-text uppercase tracking-wide">
            WATCHLIST
          </h2>
          <p className="text-sm text-terminal-muted mt-1">
            {isLoading 
              ? 'Loading...' 
              : `${counts.all} timeline${counts.all !== 1 ? 's' : ''} tracked`
            }
          </p>
        </div>
        <button className="flex items-center gap-2 px-3 py-1.5 text-xs bg-terminal-bg border border-terminal-border rounded hover:border-echelon-cyan transition">
          <Plus className="w-3 h-3" />
          Add Timeline
        </button>
      </div>

      {/* Filter Bar */}
      <div>
        <WatchlistFilterBar
          activeFilter={activeFilter}
          onFilterChange={setActiveFilter}
          counts={counts}
        />
      </div>

      {/* Error State */}
      {isError && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center max-w-md">
            <AlertCircle className="w-12 h-12 text-echelon-red mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-terminal-text mb-2">
              Failed to load watchlist
            </h3>
            <p className="text-sm text-terminal-muted mb-4">
              {error instanceof Error ? error.message : 'An unknown error occurred'}
            </p>
            <button
              onClick={() => refetch()}
              className="px-4 py-2 bg-terminal-panel border border-terminal-border rounded hover:border-echelon-cyan transition text-sm"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Loading State */}
      {isLoading && !isError && (
        <div className="flex-1 overflow-y-auto space-y-2 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
          {Array.from({ length: 5 }).map((_, i) => (
            <SkeletonRow key={i} />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !isError && (!filteredTimelines || filteredTimelines.length === 0) && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center max-w-md">
            <Eye className="w-16 h-16 text-terminal-muted mx-auto mb-4 opacity-50" />
            <h3 className="text-lg font-semibold text-terminal-text mb-2">
              {activeFilter === 'all' 
                ? 'Your watchlist is empty'
                : `No timelines match "${activeFilter}" filter`
              }
            </h3>
            <p className="text-sm text-terminal-muted mb-4">
              {activeFilter === 'all' 
                ? 'Start tracking timelines to monitor their stability, paradox proximity, and risk metrics.'
                : 'Try selecting a different filter or add more timelines to your watchlist.'
              }
            </p>
            {activeFilter === 'all' && (
              <a
                href="/sigint"
                className="inline-flex items-center gap-2 px-4 py-2 bg-terminal-panel border border-terminal-border rounded hover:border-echelon-cyan transition text-sm text-terminal-text"
              >
                Browse timelines
              </a>
            )}
          </div>
        </div>
      )}

      {/* Timeline List */}
      {!isLoading && !isError && filteredTimelines && filteredTimelines.length > 0 && (
        <div className="flex-1 overflow-y-auto space-y-2 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
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
