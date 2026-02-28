import { useEffect, useRef, useCallback } from 'react';
import type { Episode } from '../types/execution';
import { useInquiryFlow } from './useInquiryFlow';

export function useExecutionSimulator(
  episodes: Episode[],
  isCommitted: boolean,
  onComplete: () => void
) {
  const [, dispatch] = useInquiryFlow();
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const indexRef = useRef(0);
  const completedRef = useRef(false);

  useEffect(() => {
    if (!isCommitted || episodes.length === 0 || completedRef.current) return;

    indexRef.current = 0;

    intervalRef.current = setInterval(() => {
      if (indexRef.current >= episodes.length) {
        if (intervalRef.current) clearInterval(intervalRef.current);
        if (!completedRef.current) {
          completedRef.current = true;
          onComplete();
        }
        return;
      }

      dispatch({ type: 'ADVANCE_EPISODE', payload: episodes[indexRef.current] });
      indexRef.current += 1;
    }, 1500);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isCommitted, episodes, dispatch, onComplete]);

  const skip = useCallback(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);

    // Advance all remaining episodes
    for (let i = indexRef.current; i < episodes.length; i++) {
      dispatch({ type: 'ADVANCE_EPISODE', payload: episodes[i] });
    }
    indexRef.current = episodes.length;

    if (!completedRef.current) {
      completedRef.current = true;
      onComplete();
    }
  }, [episodes, dispatch, onComplete]);

  return { skip };
}
