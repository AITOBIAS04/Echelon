/**
 * useRealtimeInvalidation — WebSocket → TanStack Query bridge.
 *
 * Pattern: WS event → normalise type → identify query keys → invalidate → auto-refetch.
 *
 * Backend emits UPPERCASE event types (WING_FLAP, PARADOX_SPAWN, etc.)
 * with data in a `data` field. This hook normalises to lowercase with
 * underscore separators for the lookup map.
 *
 * Events mapped:
 * - WING_FLAP        → ['butterfly', 'timelines'], ['wingFlaps']
 * - PARADOX_SPAWN     → ['paradoxes', 'active'], ['paradox', 'active']
 * - PARADOX_MOVED     → ['paradoxes', 'active'], ['paradox', 'active']
 * - DETONATION        → ['paradoxes', 'active'], ['butterfly', 'timelines']
 * - POSITION_UPDATE   → ['user', 'positions'], ['user', 'portfolio', 'summary']
 * - RIPPLE            → ['butterfly', 'timelines']
 * - ALERT             → ['opsDashboard']
 */

import { useEffect, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useWebSocket } from './useWebSocket';

interface WsEvent {
  type: string;
  data?: {
    investigation_id?: string;
    timeline_id?: string;
    [key: string]: unknown;
  };
}

/**
 * Maps normalised (lowercase) event types to the TanStack Query keys
 * they should invalidate. Keys match the actual queryKey arrays used
 * in hooks throughout the app.
 */
const EVENT_QUERY_MAP: Record<string, string[][]> = {
  wing_flap: [['butterfly', 'timelines'], ['wingFlaps'], ['opsDashboard']],
  paradox_spawn: [['paradoxes', 'active'], ['paradox', 'active'], ['opsDashboard']],
  paradox_moved: [['paradoxes', 'active'], ['paradox', 'active']],
  detonation: [['paradoxes', 'active'], ['butterfly', 'timelines']],
  ripple: [['butterfly', 'timelines']],
  position_update: [['user', 'positions'], ['user', 'portfolio', 'summary']],
  alert: [['opsDashboard']],
  investigation_event: [['investigations']],
};

export function useRealtimeInvalidation(channel = 'platform') {
  const queryClient = useQueryClient();
  const { lastMessage, isConnected } = useWebSocket(channel);
  const lastProcessedRef = useRef<unknown>(null);

  const invalidateForEvent = useCallback(
    (event: WsEvent) => {
      // Backend emits UPPERCASE types (WING_FLAP) — normalise to lowercase
      const normalisedType = event.type.toLowerCase();

      const queryKeys = EVENT_QUERY_MAP[normalisedType];
      if (!queryKeys) return;

      for (const key of queryKeys) {
        queryClient.invalidateQueries({ queryKey: key });
      }

      // For investigation events, also invalidate the specific investigation
      if (normalisedType === 'investigation_event' && event.data?.investigation_id) {
        queryClient.invalidateQueries({
          queryKey: ['investigation', event.data.investigation_id],
        });
      }
    },
    [queryClient],
  );

  useEffect(() => {
    if (!lastMessage || lastMessage === lastProcessedRef.current) return;
    lastProcessedRef.current = lastMessage;
    invalidateForEvent(lastMessage as WsEvent);
  }, [lastMessage, invalidateForEvent]);

  return { isConnected };
}
