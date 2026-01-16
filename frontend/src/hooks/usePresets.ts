import { useState, useEffect, useMemo } from 'react';
import {
  listViews,
  createView as apiCreateView,
  updateView as apiUpdateView,
  deleteView as apiDeleteView,
  seedDefaultsIfEmpty,
} from '../api/presets';
import type {
  WatchlistSavedView,
  WatchlistSortKey,
  WatchlistSortDir,
  WatchlistFilterConfig,
  AlertRule,
} from '../types/presets';

const SELECTED_VIEW_STORAGE_KEY = 'echelon.watchlist.selectedViewId.v1';

/**
 * usePresets Hook
 * ===============
 * 
 * React hook for managing watchlist saved views and presets.
 * Handles loading, selection, CRUD operations, and persistence.
 */
export function usePresets() {
  const [views, setViews] = useState<WatchlistSavedView[]>([]);
  const [selectedViewId, setSelectedViewIdState] = useState<string | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);

  // Load views and selected view ID from localStorage
  const loadViews = () => {
    const loadedViews = listViews();
    setViews(loadedViews);
    return loadedViews;
  };

  // Load selected view ID from localStorage
  const loadSelectedViewId = (): string | null => {
    try {
      const stored = localStorage.getItem(SELECTED_VIEW_STORAGE_KEY);
      return stored || null;
    } catch (error) {
      console.error('Error loading selected view ID from localStorage:', error);
      return null;
    }
  };

  // Save selected view ID to localStorage
  const saveSelectedViewId = (id: string | null) => {
    try {
      if (id) {
        localStorage.setItem(SELECTED_VIEW_STORAGE_KEY, id);
      } else {
        localStorage.removeItem(SELECTED_VIEW_STORAGE_KEY);
      }
    } catch (error) {
      console.error('Error saving selected view ID to localStorage:', error);
    }
  };

  // Initialize on mount
  useEffect(() => {
    // Seed defaults if empty
    seedDefaultsIfEmpty();
    
    // Load views
    const loadedViews = loadViews();
    
    // Load selected view ID
    let selectedId = loadSelectedViewId();
    
    // If no selected view ID persisted, select first view
    if (!selectedId && loadedViews.length > 0) {
      selectedId = loadedViews[0].id;
      saveSelectedViewId(selectedId);
    }
    
    setSelectedViewIdState(selectedId);
    setIsInitialized(true);
  }, []);

  // Get selected view
  const selectedView = useMemo(() => {
    if (!selectedViewId) {
      return null;
    }
    return views.find((view) => view.id === selectedViewId) || null;
  }, [views, selectedViewId]);

  // Select a view
  const selectView = (id: string | null) => {
    setSelectedViewIdState(id);
    saveSelectedViewId(id);
  };

  // Create a new view
  const createView = (input: {
    name: string;
    sort: { key: WatchlistSortKey; dir: WatchlistSortDir };
    filter: WatchlistFilterConfig;
    alertRules?: AlertRule[];
  }): WatchlistSavedView => {
    const newView = apiCreateView(input);
    const updatedViews = listViews();
    setViews(updatedViews);
    
    // Auto-select newly created view
    selectView(newView.id);
    
    return newView;
  };

  // Update an existing view
  const updateView = (
    id: string,
    patch: Partial<Omit<WatchlistSavedView, 'id' | 'createdAt'>>
  ): WatchlistSavedView | null => {
    const updated = apiUpdateView(id, patch);
    if (updated) {
      const updatedViews = listViews();
      setViews(updatedViews);
    }
    return updated;
  };

  // Delete a view
  const deleteView = (id: string): boolean => {
    const deleted = apiDeleteView(id);
    if (deleted) {
      const updatedViews = listViews();
      setViews(updatedViews);
      
      // If deleted view was selected, select first available view or null
      if (selectedViewId === id) {
        if (updatedViews.length > 0) {
          selectView(updatedViews[0].id);
        } else {
          selectView(null);
        }
      }
    }
    return deleted;
  };

  // Refresh views from storage
  const refresh = () => {
    loadViews();
  };

  return {
    views,
    selectedViewId,
    selectedView,
    selectView,
    createView,
    updateView,
    deleteView,
    refresh,
    isInitialized,
  };
}
