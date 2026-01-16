import type {
  WatchlistSavedView,
  WatchlistSortKey,
  WatchlistSortDir,
  WatchlistFilterConfig,
  AlertRule,
} from '../types/presets';

const STORAGE_KEY = 'echelon.watchlist.savedViews.v1';

/**
 * Presets API
 * ===========
 * 
 * CRUD operations for WatchlistSavedView using localStorage.
 */

/**
 * List all saved views
 */
export function listViews(): WatchlistSavedView[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      return [];
    }
    return JSON.parse(stored) as WatchlistSavedView[];
  } catch (error) {
    console.error('Error loading views from localStorage:', error);
    return [];
  }
}

/**
 * Get a specific view by ID
 */
export function getView(id: string): WatchlistSavedView | null {
  const views = listViews();
  return views.find((view) => view.id === id) || null;
}

/**
 * Create a new view
 */
export function createView(input: {
  name: string;
  sort: { key: WatchlistSortKey; dir: WatchlistSortDir };
  filter: WatchlistFilterConfig;
  alertRules?: AlertRule[];
}): WatchlistSavedView {
  const views = listViews();
  const now = new Date().toISOString();
  
  const newView: WatchlistSavedView = {
    id: `view_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    name: input.name,
    createdAt: now,
    updatedAt: now,
    sort: input.sort,
    filter: input.filter,
    alertRules: input.alertRules || [],
  };

  views.push(newView);
  saveViews(views);
  
  return newView;
}

/**
 * Update an existing view
 */
export function updateView(
  id: string,
  patch: Partial<Omit<WatchlistSavedView, 'id' | 'createdAt'>>
): WatchlistSavedView | null {
  const views = listViews();
  const index = views.findIndex((view) => view.id === id);
  
  if (index === -1) {
    return null;
  }

  const updatedView: WatchlistSavedView = {
    ...views[index],
    ...patch,
    updatedAt: new Date().toISOString(),
  };

  views[index] = updatedView;
  saveViews(views);
  
  return updatedView;
}

/**
 * Delete a view by ID
 */
export function deleteView(id: string): boolean {
  const views = listViews();
  const filtered = views.filter((view) => view.id !== id);
  
  if (filtered.length === views.length) {
    return false; // View not found
  }

  saveViews(filtered);
  return true;
}

/**
 * Save views to localStorage
 */
function saveViews(views: WatchlistSavedView[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(views));
  } catch (error) {
    console.error('Error saving views to localStorage:', error);
  }
}

/**
 * Seed default views if storage is empty
 */
export function seedDefaultsIfEmpty(): void {
  const views = listViews();
  if (views.length > 0) {
    return; // Already has views
  }

  const now = new Date().toISOString();

  // Default 1: Brittle Timelines
  const brittleView: WatchlistSavedView = {
    id: 'default_brittle',
    name: 'Brittle Timelines',
    createdAt: now,
    updatedAt: now,
    sort: {
      key: 'paradox_proximity',
      dir: 'desc',
    },
    filter: {
      minLogicGap: 40,
      maxLogicGap: 60,
    },
    alertRules: [
      {
        id: 'alert_brittle_gap_spike',
        name: 'Logic Gap Spike',
        enabled: false,
        severity: 'warn',
        condition: {
          type: 'rate_of_change',
          metric: 'logic_gap',
          op: '>=',
          value: 10,
          windowMinutes: 15,
        },
        scope: {
          scopeType: 'watchlist',
        },
      },
    ],
  };

  // Default 2: Paradox Watch
  const paradoxView: WatchlistSavedView = {
    id: 'default_paradox',
    name: 'Paradox Watch',
    createdAt: now,
    updatedAt: now,
    sort: {
      key: 'paradox_proximity',
      dir: 'desc',
    },
    filter: {
      paradoxOnly: true,
      minLogicGap: 60,
    },
    alertRules: [
      {
        id: 'alert_paradox_spawned',
        name: 'Paradox Spawned',
        enabled: false,
        severity: 'critical',
        condition: {
          type: 'event',
          eventType: 'paradox_spawn',
        },
        scope: {
          scopeType: 'all',
        },
      },
      {
        id: 'alert_paradox_proximity',
        name: 'High Paradox Proximity',
        enabled: false,
        severity: 'warn',
        condition: {
          type: 'threshold',
          metric: 'paradox_proximity',
          op: '>=',
          value: 80,
        },
        scope: {
          scopeType: 'watchlist',
        },
      },
    ],
  };

  // Default 3: Fork Soon
  const forkSoonView: WatchlistSavedView = {
    id: 'default_fork_soon',
    name: 'Fork Soon',
    createdAt: now,
    updatedAt: now,
    sort: {
      key: 'next_fork_eta',
      dir: 'asc',
    },
    filter: {
      maxNextForkEtaSec: 600, // 10 minutes
    },
    alertRules: [
      {
        id: 'alert_fork_live',
        name: 'Fork Live',
        enabled: false,
        severity: 'info',
        condition: {
          type: 'event',
          eventType: 'fork_live',
        },
        scope: {
          scopeType: 'watchlist',
        },
      },
    ],
  };

  // Default 4: Sabotage Heat
  const sabotageView: WatchlistSavedView = {
    id: 'default_sabotage',
    name: 'Sabotage Heat',
    createdAt: now,
    updatedAt: now,
    sort: {
      key: 'sabotage_heat',
      dir: 'desc',
    },
    filter: {
      sabotageHeatMin: 2,
    },
    alertRules: [
      {
        id: 'alert_sabotage_disclosed',
        name: 'Sabotage Disclosed',
        enabled: false,
        severity: 'warn',
        condition: {
          type: 'event',
          eventType: 'sabotage_disclosed',
        },
        scope: {
          scopeType: 'watchlist',
        },
      },
      {
        id: 'alert_sabotage_heat_threshold',
        name: 'High Sabotage Heat',
        enabled: false,
        severity: 'warn',
        condition: {
          type: 'threshold',
          metric: 'sabotage_heat',
          op: '>=',
          value: 3,
        },
        scope: {
          scopeType: 'watchlist',
        },
      },
    ],
  };

  saveViews([brittleView, paradoxView, forkSoonView, sabotageView]);
}
