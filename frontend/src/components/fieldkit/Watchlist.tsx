import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye, Plus, AlertCircle, ChevronRight, ChevronLeft } from 'lucide-react';
import { useWatchlist, getFilteredCount } from '../../hooks/useWatchlist';
import { usePresets } from '../../hooks/usePresets';
import type { WatchlistFilter } from '../../types/watchlist';
import type { WatchlistSavedView } from '../../types/presets';
import { WatchlistFilterBar } from './WatchlistFilterBar';
import { WatchlistRow } from './WatchlistRow';
import { SavedViewsBar } from '../watchlist/SavedViewsBar';
import { SavedViewEditorModal } from '../watchlist/SavedViewEditorModal';
import { AlertRulesPanel } from '../watchlist/AlertRulesPanel';
import { applyFilter, applySort } from '../../utils/watchlistFilters';
import { evaluateAlerts, type AlertTrigger } from '../../utils/alertEvaluator';

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
  const [showAlertPanel, setShowAlertPanel] = useState(false);
  const [alerts, setAlerts] = useState<AlertTrigger[]>([]);
  const [editingView, setEditingView] = useState<WatchlistSavedView | null>(null);
  const [isEditorOpen, setIsEditorOpen] = useState(false);

  // Presets hook
  const {
    views,
    selectedView,
    selectedViewId,
    selectView,
    createView: createPresetView,
    updateView: updatePresetView,
    deleteView: deletePresetView,
    isInitialized,
  } = usePresets();

  // Fetch all timelines (we'll apply filters/sorting client-side)
  const { 
    data: allTimelines, 
    isLoading, 
    isError, 
    error,
    refetch 
  } = useWatchlist('all');

  // Apply view filter and sort if a view is selected
  const processedTimelines = useMemo(() => {
    if (!allTimelines || !isInitialized) return allTimelines || [];

    let result = [...allTimelines];

    // Apply saved view filter if selected
    if (selectedView) {
      result = applyFilter(result, selectedView.filter);
      result = applySort(result, selectedView.sort.key, selectedView.sort.dir);
    } else {
      // Fall back to legacy filter
      result = result.filter((t) => {
        switch (activeFilter) {
          case 'all': return true;
          case 'brittle': return t.logicGap >= 40 && t.logicGap < 60;
          case 'paradox-watch': return t.logicGap >= 60 || t.logicGapTrend === 'widening';
          case 'high-entropy': return t.entropyRate < -3;
          case 'under-attack': return t.sabotageCount1h >= 3;
          default: return true;
        }
      });
    }

    return result;
  }, [allTimelines, selectedView, activeFilter, isInitialized]);

  // Calculate counts for each filter
  const counts = {
    'all': allTimelines?.length || 0,
    'brittle': getFilteredCount(allTimelines || [], 'brittle'),
    'paradox-watch': getFilteredCount(allTimelines || [], 'paradox-watch'),
    'high-entropy': getFilteredCount(allTimelines || [], 'high-entropy'),
    'under-attack': getFilteredCount(allTimelines || [], 'under-attack'),
  };

  // Evaluate alerts every 10 seconds
  useEffect(() => {
    if (!allTimelines || !selectedView || !isInitialized) return;

    const evaluate = () => {
      const triggers = evaluateAlerts(allTimelines, selectedView.alertRules);
      setAlerts(triggers);

      // Log to console
      triggers.forEach((trigger) => {
        console.log(`ALERT: ${trigger.ruleName} triggered on ${trigger.timelineName}`);
      });
    };

    evaluate();
    const interval = setInterval(evaluate, 10000); // 10 seconds
    return () => clearInterval(interval);
  }, [allTimelines, selectedView, isInitialized]);

  const handleRemove = (id: string) => {
    // TODO: Implement remove from watchlist API call
    console.log('Remove timeline:', id);
  };

  const handleNavigate = (id: string) => {
    navigate(`/timeline/${id}`);
  };

  const handleNewView = () => {
    setEditingView(null);
    setIsEditorOpen(true);
  };

  const handleEditView = (id: string) => {
    const view = views.find((v) => v.id === id);
    if (view) {
      setEditingView(view);
      setIsEditorOpen(true);
    }
  };

  const handleSaveView = (view: WatchlistSavedView) => {
    if (view.id.startsWith('view_') && !views.find((v) => v.id === view.id)) {
      // New view
      createPresetView({
        name: view.name,
        sort: view.sort,
        filter: view.filter,
        alertRules: view.alertRules,
      });
    } else {
      // Update existing
      updatePresetView(view.id, {
        name: view.name,
        sort: view.sort,
        filter: view.filter,
        alertRules: view.alertRules,
        updatedAt: view.updatedAt,
      });
    }
    setIsEditorOpen(false);
    setEditingView(null);
  };

  const handleDeleteView = (id: string) => {
    deletePresetView(id);
  };

  const handleUpdateView = (updatedView: WatchlistSavedView) => {
    updatePresetView(updatedView.id, {
      name: updatedView.name,
      sort: updatedView.sort,
      filter: updatedView.filter,
      alertRules: updatedView.alertRules,
      updatedAt: updatedView.updatedAt,
    });
  };

  return (
    <div className="h-full flex flex-col p-4 gap-4 relative">
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
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowAlertPanel(!showAlertPanel)}
            className="flex items-center gap-2 px-3 py-1.5 text-xs bg-terminal-bg border border-terminal-border rounded hover:border-echelon-cyan transition"
          >
            {showAlertPanel ? <ChevronRight className="w-3 h-3" /> : <ChevronLeft className="w-3 h-3" />}
            Alerts {alerts.length > 0 && `(${alerts.length})`}
          </button>
          <button className="flex items-center gap-2 px-3 py-1.5 text-xs bg-terminal-bg border border-terminal-border rounded hover:border-echelon-cyan transition">
            <Plus className="w-3 h-3" />
            Add Timeline
          </button>
        </div>
      </div>

      {/* Saved Views Bar */}
      {isInitialized && (
        <div>
          <SavedViewsBar
            views={views}
            selectedViewId={selectedViewId}
            onSelectView={selectView}
            onNewView={handleNewView}
            onEditView={handleEditView}
            onDeleteView={handleDeleteView}
          />
        </div>
      )}

      {/* Alert Banner */}
      {alerts.length > 0 && (
        <div className="bg-red-500/20 border border-red-500/50 rounded p-3 space-y-1">
          {alerts.slice(0, 3).map((alert) => (
            <div key={`${alert.ruleId}-${alert.timelineId}`} className="text-sm">
              <span className="text-red-400 font-semibold">ALERT:</span>{' '}
              <span className="text-terminal-text">{alert.ruleName}</span>{' '}
              triggered on{' '}
              <span className="text-terminal-text font-medium">{alert.timelineName}</span>
            </div>
          ))}
          {alerts.length > 3 && (
            <div className="text-xs text-terminal-muted">
              +{alerts.length - 3} more alert{alerts.length - 3 !== 1 ? 's' : ''}
            </div>
          )}
        </div>
      )}

      {/* Filter Bar */}
      {!selectedView && (
        <div>
          <WatchlistFilterBar
            activeFilter={activeFilter}
            onFilterChange={setActiveFilter}
            counts={counts}
          />
        </div>
      )}

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
      {!isLoading && !isError && (!processedTimelines || processedTimelines.length === 0) && (
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

      {/* Main Content Area */}
      <div className="flex-1 min-h-0 flex gap-4">
        {/* Timeline List */}
        <div className={`flex-1 min-w-0 ${showAlertPanel ? 'lg:w-2/3' : ''}`}>
          {!isLoading && !isError && processedTimelines && processedTimelines.length > 0 && (
            <div className="h-full overflow-y-auto space-y-2 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
              {processedTimelines.map((timeline) => (
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

        {/* Alert Rules Panel (Drawer) */}
        {showAlertPanel && (
          <div className="hidden lg:block w-1/3 flex-shrink-0 border-l border-terminal-border pl-4">
            <AlertRulesPanel
              view={selectedView}
              onUpdateView={handleUpdateView}
            />
          </div>
        )}
      </div>

      {/* Alert Rules Panel (Mobile - Collapsible) */}
      {showAlertPanel && (
        <div className="lg:hidden">
          <AlertRulesPanel
            view={selectedView}
            onUpdateView={handleUpdateView}
          />
        </div>
      )}

      {/* Saved View Editor Modal */}
      <SavedViewEditorModal
        view={editingView}
        isOpen={isEditorOpen}
        onClose={() => {
          setIsEditorOpen(false);
          setEditingView(null);
        }}
        onSave={handleSaveView}
      />
    </div>
  );
}
