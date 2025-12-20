import { useEffect, useRef, useState } from 'react';

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';

export const useWebSocket = (channel?: string) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const wsUrl = channel 
      ? `${WS_BASE_URL}/ws?channel=${channel}`
      : `${WS_BASE_URL}/ws`;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setIsConnected(true);
      if (channel) {
        ws.send(JSON.stringify({ type: 'subscribe', channel }));
      }
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLastMessage(data);
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      setIsConnected(false);
      // Attempt to reconnect after 3 seconds
      setTimeout(() => {
        if (wsRef.current?.readyState === WebSocket.CLOSED) {
          // Reconnect logic handled by useEffect
        }
      }, 3000);
    };

    wsRef.current = ws;

    return () => {
      if (channel) {
        ws.send(JSON.stringify({ type: 'unsubscribe', channel }));
      }
      ws.close();
    };
  }, [channel]);

  return { isConnected, lastMessage };
};


