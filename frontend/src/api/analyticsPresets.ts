import type { AnalyticsBreakdownFilters } from './analytics';

export type AnalyticsSavedTab = 'platform' | 'portfolio';

export interface AnalyticsSavedView {
  id: string;
  name: string;
  createdAt: string;
  updatedAt: string;
  tab: AnalyticsSavedTab;
  filters: AnalyticsBreakdownFilters;
  selectedPlatformBucket?: string;
  selectedRiskBucket?: string;
}

const STORAGE_KEY = 'echelon.analytics.savedViews.v1';
const SELECTED_STORAGE_KEY = 'echelon.analytics.selectedViewId.v1';

function storage(): Storage | null {
  if (typeof window === 'undefined') {
    return null;
  }
  const candidate = window.localStorage;
  if (!candidate || typeof candidate.getItem !== 'function' || typeof candidate.setItem !== 'function') {
    return null;
  }
  return candidate;
}

function readViews(): AnalyticsSavedView[] {
  try {
    const store = storage();
    if (!store) {
      return [];
    }
    const stored = store.getItem(STORAGE_KEY);
    if (!stored) {
      return [];
    }
    return JSON.parse(stored) as AnalyticsSavedView[];
  } catch (error) {
    console.error('Error loading analytics views:', error);
    return [];
  }
}

function writeViews(views: AnalyticsSavedView[]) {
  try {
    const store = storage();
    if (!store) {
      return;
    }
    store.setItem(STORAGE_KEY, JSON.stringify(views));
  } catch (error) {
    console.error('Error saving analytics views:', error);
  }
}

export function listAnalyticsViews(): AnalyticsSavedView[] {
  return readViews();
}

export function getSelectedAnalyticsViewId(): string | null {
  try {
    const store = storage();
    return store ? store.getItem(SELECTED_STORAGE_KEY) : null;
  } catch (error) {
    console.error('Error loading selected analytics view id:', error);
    return null;
  }
}

export function setSelectedAnalyticsViewId(id: string | null) {
  try {
    const store = storage();
    if (!store) {
      return;
    }
    if (id) {
      store.setItem(SELECTED_STORAGE_KEY, id);
    } else {
      store.removeItem(SELECTED_STORAGE_KEY);
    }
  } catch (error) {
    console.error('Error saving selected analytics view id:', error);
  }
}

export function createAnalyticsView(input: {
  name: string;
  tab: AnalyticsSavedTab;
  filters: AnalyticsBreakdownFilters;
  selectedPlatformBucket?: string;
  selectedRiskBucket?: string;
}): AnalyticsSavedView {
  const now = new Date().toISOString();
  const next: AnalyticsSavedView = {
    id: `analytics_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    name: input.name,
    createdAt: now,
    updatedAt: now,
    tab: input.tab,
    filters: input.filters,
    selectedPlatformBucket: input.selectedPlatformBucket,
    selectedRiskBucket: input.selectedRiskBucket,
  };
  const views = readViews();
  views.push(next);
  writeViews(views);
  return next;
}

export function updateAnalyticsView(
  id: string,
  patch: Partial<Omit<AnalyticsSavedView, 'id' | 'createdAt'>>,
): AnalyticsSavedView | null {
  const views = readViews();
  const index = views.findIndex((view) => view.id === id);
  if (index === -1) {
    return null;
  }
  const updated: AnalyticsSavedView = {
    ...views[index],
    ...patch,
    updatedAt: new Date().toISOString(),
  };
  views[index] = updated;
  writeViews(views);
  return updated;
}

export function deleteAnalyticsView(id: string): boolean {
  const views = readViews();
  const filtered = views.filter((view) => view.id !== id);
  if (filtered.length === views.length) {
    return false;
  }
  writeViews(filtered);
  const selected = getSelectedAnalyticsViewId();
  if (selected === id) {
    setSelectedAnalyticsViewId(filtered[0]?.id ?? null);
  }
  return true;
}
