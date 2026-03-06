/**
 * useRealtimeChannel — Thin wrapper over useWebSocket that subscribes to
 * a named channel and merges events into React Query cache.
 *
 * Gated on WEBSOCKET_REALTIME feature flag. When flag is off, this is a no-op.
 *
 * Usage:
 *   useRealtimeChannel('timeline:tl_001', ['theatres', 'list']);
 *   // Events on channel 'timeline:tl_001' will invalidate the ['theatres', 'list'] query.
 */

import { useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { isEnabled } from '../lib/featureFlags';
import { useWebSocket } from './useWebSocket';

export interface RealtimeChannelOptions {
  /** React Query key(s) to invalidate when events arrive */
  invalidateKeys?: unknown[][];

  /** Optional callback for each incoming event */
  onEvent?: (event: unknown) => void;

  /** Whether this channel should be active (in addition to feature flag) */
  enabled?: boolean;
}

export function useRealtimeChannel(
  channel: string,
  options: RealtimeChannelOptions = {},
) {
  const { invalidateKeys = [], onEvent, enabled = true } = options;
  const queryClient = useQueryClient();
  const wsEnabled = isEnabled('WEBSOCKET_REALTIME') && enabled;

  // Only connect when feature flag is on
  const { isConnected, lastMessage } = useWebSocket(wsEnabled ? channel : undefined);

  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  const invalidateKeysRef = useRef(invalidateKeys);
  invalidateKeysRef.current = invalidateKeys;

  // Handle incoming messages
  useEffect(() => {
    if (!lastMessage || !wsEnabled) return;

    // Call event handler if provided
    onEventRef.current?.(lastMessage);

    // Invalidate specified query keys
    for (const key of invalidateKeysRef.current) {
      queryClient.invalidateQueries({ queryKey: key });
    }
  }, [lastMessage, wsEnabled, queryClient]);

  return {
    isConnected: wsEnabled && isConnected,
    isEnabled: wsEnabled,
  };
}
