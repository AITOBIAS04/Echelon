/**
 * User Preferences Library
 * 
 * Manages user preferences stored in localStorage.
 */

const HOME_PREF_KEY = 'echelon.homePref.v1';

export type HomePreference = 'markets' | 'launchpad' | null;

/**
 * Get user's home preference
 * 
 * @returns Home preference ('markets', 'launchpad', or null for default)
 */
export function getHomePreference(): HomePreference {
  try {
    const stored = localStorage.getItem(HOME_PREF_KEY);
    if (!stored) return null;
    
    const pref = stored as HomePreference;
    // Validate stored value
    if (pref === 'markets' || pref === 'launchpad') {
      return pref;
    }
    
    // Invalid value, reset to null
    localStorage.removeItem(HOME_PREF_KEY);
    return null;
  } catch {
    return null;
  }
}

/**
 * Set user's home preference
 * 
 * @param pref Home preference ('markets', 'launchpad', or null to clear)
 */
export function setHomePreference(pref: HomePreference): void {
  try {
    if (pref === null) {
      localStorage.removeItem(HOME_PREF_KEY);
    } else {
      localStorage.setItem(HOME_PREF_KEY, pref);
    }
  } catch (error) {
    console.error('Failed to save home preference:', error);
  }
}
