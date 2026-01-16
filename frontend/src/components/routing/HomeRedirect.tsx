import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getHomePreference } from '../../lib/userPrefs';

/**
 * HomeRedirect Component
 * 
 * Redirects to the user's preferred home page based on their preference.
 * Only redirects if visiting the root path '/' and preference is 'launchpad'.
 * Otherwise, shows HomePage (markets + launchpad rail).
 */
export function HomeRedirect() {
  const navigate = useNavigate();

  useEffect(() => {
    const preference = getHomePreference();
    
    // Only redirect if preference is 'launchpad'
    // If preference is null or 'markets', show HomePage (default behavior)
    if (preference === 'launchpad') {
      navigate('/launchpad', { replace: true });
    }
  }, [navigate]);

  // Return null since this is just a redirect component
  return null;
}
