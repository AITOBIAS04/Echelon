import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useWebSocket } from '../useWebSocket';

// ---------------------------------------------------------------------------
// Mock WebSocket
// ---------------------------------------------------------------------------

type WsHandler = ((ev: { data: string }) => void) | (() => void) | null;

class MockWebSocket {
  static OPEN = 1;
  static CLOSED = 3;
  static instances: MockWebSocket[] = [];

  readyState = MockWebSocket.OPEN;
  onopen: WsHandler = null;
  onclose: WsHandler = null;
  onmessage: WsHandler = null;
  onerror: WsHandler = null;
  url: string;

  send = vi.fn();
  close = vi.fn().mockImplementation(() => {
    this.readyState = MockWebSocket.CLOSED;
    // Simulate async onclose (browser fires onclose after close())
    queueMicrotask(() => {
      if (this.onclose) (this.onclose as () => void)();
    });
  });

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
    // Simulate async onopen
    queueMicrotask(() => {
      if (this.onopen) (this.onopen as () => void)();
    });
  }
}

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------

let origWebSocket: typeof globalThis.WebSocket;

beforeEach(() => {
  vi.useFakeTimers();
  MockWebSocket.instances = [];
  origWebSocket = globalThis.WebSocket;
  globalThis.WebSocket = MockWebSocket as unknown as typeof WebSocket;
});

afterEach(() => {
  vi.useRealTimers();
  globalThis.WebSocket = origWebSocket;
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('useWebSocket lifecycle', () => {
  it('does not schedule reconnect after unmount', async () => {
    const { unmount } = renderHook(() => useWebSocket());

    // Let onopen fire
    await act(async () => {
      await vi.runAllTimersAsync();
    });

    const ws = MockWebSocket.instances[0];
    expect(ws).toBeDefined();

    // Unmount — triggers cleanup → ws.close() → onclose
    unmount();

    // Let onclose microtask fire
    await act(async () => {
      await vi.runAllTimersAsync();
    });

    // Only 1 WebSocket should have been created (no reconnect)
    expect(MockWebSocket.instances).toHaveLength(1);
  });

  it('reconnects on unexpected close while mounted', async () => {
    renderHook(() => useWebSocket());

    // Let onopen fire
    await act(async () => {
      await vi.runAllTimersAsync();
    });

    const ws = MockWebSocket.instances[0];

    // Simulate server-side close (unexpected)
    await act(async () => {
      ws.readyState = MockWebSocket.CLOSED;
      if (ws.onclose) (ws.onclose as () => void)();
    });

    // Advance past RECONNECT_DELAY_MS (3000ms)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3_500);
    });

    // A second WebSocket should have been created (reconnect)
    expect(MockWebSocket.instances.length).toBeGreaterThanOrEqual(2);
  });

  it('clears pending reconnect timer on unmount', async () => {
    const clearSpy = vi.spyOn(globalThis, 'clearTimeout');

    const { unmount } = renderHook(() => useWebSocket());

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    const ws = MockWebSocket.instances[0];

    // Trigger an unexpected close to arm the reconnect timer
    await act(async () => {
      ws.readyState = MockWebSocket.CLOSED;
      if (ws.onclose) (ws.onclose as () => void)();
    });

    // Timer is now armed but hasn't fired yet — unmount
    unmount();

    // clearTimeout should have been called during cleanup
    expect(clearSpy).toHaveBeenCalled();

    // Advance timers — no new WebSocket should be created
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5_000);
    });

    // Still only the original + no ghost reconnect
    // (onclose from cleanup may create at most 1 extra attempt,
    //  but disposedRef blocks connect())
    const connectAttempts = MockWebSocket.instances.length;
    expect(connectAttempts).toBeLessThanOrEqual(2);

    clearSpy.mockRestore();
  });

  it('respects MAX_RECONNECT_ATTEMPTS for consecutive failures', async () => {
    renderHook(() => useWebSocket());

    // Let initial onopen fire
    await act(async () => {
      await vi.runAllTimersAsync();
    });

    // Simulate 6 consecutive failures: close fires but onopen never does
    // (server is down). Disable auto-onopen for subsequent sockets.
    for (let i = 0; i < 6; i++) {
      const ws = MockWebSocket.instances[MockWebSocket.instances.length - 1];

      // Suppress onopen for reconnect sockets so attempts accumulate
      if (i > 0) ws.onopen = null;

      await act(async () => {
        ws.readyState = MockWebSocket.CLOSED;
        if (ws.onclose) (ws.onclose as () => void)();
      });
      await act(async () => {
        await vi.advanceTimersByTimeAsync(3_500);
      });
    }

    // 1 initial + 5 reconnects = 6 max (6th close doesn't reconnect)
    expect(MockWebSocket.instances.length).toBeLessThanOrEqual(7);
    // The key invariant: no more sockets after MAX attempts exhausted
    const countBefore = MockWebSocket.instances.length;
    await act(async () => {
      await vi.advanceTimersByTimeAsync(10_000);
    });
    expect(MockWebSocket.instances.length).toBe(countBefore);
  });
});
