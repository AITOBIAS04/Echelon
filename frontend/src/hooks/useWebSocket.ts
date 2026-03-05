/**
 * useWebSocket — Low-level WebSocket hook with auto-reconnect.
 * Higher-level integration via useRealtimeInvalidation.
 */

import { useEffect, useRef, useState, useCallback } from 'react';

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';
const RECONNECT_DELAY_MS = 3_000;
const MAX_RECONNECT_ATTEMPTS = 5;

export const useWebSocket = (channel?: string) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<unknown>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimer = useRef<number | null>(null);
  const disposedRef = useRef(false);

  const connect = useCallback(() => {
    if (disposedRef.current) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const wsUrl = channel
      ? `${WS_BASE_URL}/ws?channel=${channel}`
      : `${WS_BASE_URL}/ws`;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setIsConnected(true);
      reconnectAttempts.current = 0;
      if (channel) {
        ws.send(JSON.stringify({ action: 'subscribe', channel }));
      }
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLastMessage(data);
      } catch {
        // Ignore non-JSON messages
      }
    };

    ws.onerror = () => {
      // Error handling — reconnect on close will cover this
    };

    ws.onclose = () => {
      setIsConnected(false);
      wsRef.current = null;

      // Guard: don't reconnect after unmount / disposal
      if (disposedRef.current) return;

      // Auto-reconnect with backoff
      if (reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttempts.current++;
        reconnectTimer.current = window.setTimeout(connect, RECONNECT_DELAY_MS);
      }
    };

    wsRef.current = ws;
  }, [channel]);

  useEffect(() => {
    disposedRef.current = false;
    connect();

    return () => {
      disposedRef.current = true;
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
        reconnectTimer.current = null;
      }
      if (wsRef.current) {
        if (channel && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ action: 'unsubscribe', channel }));
        }
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [channel, connect]);

  return { isConnected, lastMessage };
};
