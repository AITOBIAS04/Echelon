import { useEffect, useRef, useCallback } from 'react';
import type { MarketPhase } from '../types/execution';
import { useInquiryFlow } from './useInquiryFlow';

export function useMarketSimulator(
  phases: MarketPhase[],
  isCommitted: boolean,
  onComplete: () => void
) {
  const [, dispatch] = useInquiryFlow();
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const indexRef = useRef(0);
  const completedRef = useRef(false);

  useEffect(() => {
    if (!isCommitted || phases.length === 0 || completedRef.current) return;

    indexRef.current = 0;

    intervalRef.current = setInterval(() => {
      if (indexRef.current >= phases.length) {
        if (intervalRef.current) clearInterval(intervalRef.current);
        if (!completedRef.current) {
          completedRef.current = true;
          onComplete();
        }
        return;
      }

      dispatch({ type: 'ADVANCE_PHASE', payload: phases[indexRef.current] });
      indexRef.current += 1;
    }, 1500);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isCommitted, phases, dispatch, onComplete]);

  const skip = useCallback(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);

    for (let i = indexRef.current; i < phases.length; i++) {
      dispatch({ type: 'ADVANCE_PHASE', payload: phases[i] });
    }
    indexRef.current = phases.length;

    if (!completedRef.current) {
      completedRef.current = true;
      onComplete();
    }
  }, [phases, dispatch, onComplete]);

  return { skip };
}
