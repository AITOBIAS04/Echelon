import { useEffect, useMemo, useState } from 'react';
import {
  createAnalyticsView,
  deleteAnalyticsView,
  getSelectedAnalyticsViewId,
  listAnalyticsViews,
  setSelectedAnalyticsViewId,
  updateAnalyticsView,
  type AnalyticsSavedTab,
  type AnalyticsSavedView,
} from '../api/analyticsPresets';
import type { AnalyticsBreakdownFilters } from '../api/analytics';

export function useAnalyticsPresets() {
  const [views, setViews] = useState<AnalyticsSavedView[]>([]);
  const [selectedViewId, setSelectedViewIdState] = useState<string | null>(null);

  const refresh = () => {
    setViews(listAnalyticsViews());
    setSelectedViewIdState(getSelectedAnalyticsViewId());
  };

  useEffect(() => {
    refresh();
  }, []);

  const selectedView = useMemo(
    () => views.find((view) => view.id === selectedViewId) ?? null,
    [views, selectedViewId],
  );

  const selectView = (id: string | null) => {
    setSelectedAnalyticsViewId(id);
    setSelectedViewIdState(id);
  };

  const createView = (input: {
    name: string;
    tab: AnalyticsSavedTab;
    filters: AnalyticsBreakdownFilters;
    selectedPlatformBucket?: string;
    selectedRiskBucket?: string;
  }) => {
    const view = createAnalyticsView(input);
    refresh();
    selectView(view.id);
    return view;
  };

  const saveIntoView = (
    id: string,
    patch: {
      tab: AnalyticsSavedTab;
      filters: AnalyticsBreakdownFilters;
      selectedPlatformBucket?: string;
      selectedRiskBucket?: string;
    },
  ) => {
    const updated = updateAnalyticsView(id, patch);
    refresh();
    return updated;
  };

  const removeView = (id: string) => {
    const deleted = deleteAnalyticsView(id);
    refresh();
    return deleted;
  };

  return {
    views,
    selectedViewId,
    selectedView,
    selectView,
    createView,
    saveIntoView,
    removeView,
    refresh,
  };
}
