/**
 * Tracking Library
 * 
 * Manages tracked timeline IDs (watchlist backing) in localStorage.
 */

const TRACKED_KEY = 'echelon.trackedTimelines.v1';

/**
 * Get tracked timeline IDs from localStorage
 */
function getTrackedIds(): string[] {
  try {
    const stored = localStorage.getItem(TRACKED_KEY);
    if (!stored) return [];
    const ids = JSON.parse(stored);
    if (Array.isArray(ids) && ids.every((id) => typeof id === 'string')) {
      return ids;
    }
    // Invalid data, reset
    localStorage.removeItem(TRACKED_KEY);
    return [];
  } catch {
    return [];
  }
}

/**
 * Save tracked timeline IDs to localStorage
 */
function saveTrackedIds(ids: string[]): void {
  try {
    localStorage.setItem(TRACKED_KEY, JSON.stringify(ids));
  } catch (error) {
    console.error('Failed to save tracked timelines:', error);
  }
}

/**
 * List all tracked timeline IDs
 * 
 * @returns Array of tracked timeline IDs
 */
export function listTracked(): string[] {
  return getTrackedIds();
}

/**
 * Check if a timeline ID is tracked
 * 
 * @param id Timeline ID to check
 * @returns True if the timeline is tracked
 */
export function isTracked(id: string): boolean {
  const tracked = getTrackedIds();
  return tracked.includes(id);
}

/**
 * Track a timeline ID
 * 
 * @param id Timeline ID to track
 */
export function track(id: string): void {
  const tracked = getTrackedIds();
  if (!tracked.includes(id)) {
    tracked.push(id);
    saveTrackedIds(tracked);
  }
}

/**
 * Untrack a timeline ID
 * 
 * @param id Timeline ID to untrack
 */
export function untrack(id: string): void {
  const tracked = getTrackedIds();
  const filtered = tracked.filter((trackedId) => trackedId !== id);
  if (filtered.length !== tracked.length) {
    saveTrackedIds(filtered);
  }
}

/**
 * Toggle tracking for a timeline ID
 * 
 * @param id Timeline ID to toggle
 * @returns True if the timeline is now tracked, false if untracked
 */
export function toggleTrack(id: string): boolean {
  const tracked = getTrackedIds();
  const isCurrentlyTracked = tracked.includes(id);
  
  if (isCurrentlyTracked) {
    untrack(id);
    return false;
  } else {
    track(id);
    return true;
  }
}
