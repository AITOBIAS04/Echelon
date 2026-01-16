import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * SigintRedirect Component
 * 
 * Redirects /sigint to / (HOME) since SIGINT functionality
 * is now merged into the HOME page (Ops Board).
 * Preserves deep links by checking for query params.
 */
export function SigintRedirect() {
  const navigate = useNavigate();

  useEffect(() => {
    // Check if there are query params that should go to blackbox
    const urlParams = new URLSearchParams(window.location.search);
    const tab = urlParams.get('tab');
    const filter = urlParams.get('filter');

    if (tab === 'live_tape' || filter) {
      // Redirect to blackbox with params
      navigate(`/blackbox?${urlParams.toString()}`, { replace: true });
    } else {
      // Default redirect to home
      navigate('/', { replace: true });
    }
  }, [navigate]);

  return null;
}
