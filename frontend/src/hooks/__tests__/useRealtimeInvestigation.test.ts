import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';

// Mock useWebSocket before importing the hook
const mockUseWebSocket = vi.fn().mockReturnValue({ isConnected: false, lastMessage: null });
vi.mock('../useWebSocket', () => ({
  useWebSocket: (...args: unknown[]) => mockUseWebSocket(...args),
}));

// Mock TanStack Query
const mockInvalidateQueries = vi.fn();
vi.mock('@tanstack/react-query', () => ({
  useQueryClient: () => ({
    invalidateQueries: mockInvalidateQueries,
  }),
}));

import { useRealtimeInvalidation } from '../useRealtimeInvestigation';

describe('useRealtimeInvalidation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseWebSocket.mockReturnValue({ isConnected: true, lastMessage: null });
  });

  it('subscribes to platform channel by default', () => {
    renderHook(() => useRealtimeInvalidation());
    expect(mockUseWebSocket).toHaveBeenCalledWith('platform');
  });

  it('invalidates correct query keys for WING_FLAP events (uppercase from backend)', () => {
    // Backend sends UPPERCASE type with `data` field
    const message = { type: 'WING_FLAP', data: {} };
    mockUseWebSocket.mockReturnValue({ isConnected: true, lastMessage: message });

    renderHook(() => useRealtimeInvalidation());

    expect(mockInvalidateQueries).toHaveBeenCalledWith({ queryKey: ['butterfly', 'timelines'] });
    expect(mockInvalidateQueries).toHaveBeenCalledWith({ queryKey: ['wingFlaps'] });
    expect(mockInvalidateQueries).toHaveBeenCalledWith({ queryKey: ['opsDashboard'] });
  });

  it('invalidates correct query keys for investigation_event with specific ID', () => {
    const message = { type: 'INVESTIGATION_EVENT', data: { investigation_id: 'INV-001' } };
    mockUseWebSocket.mockReturnValue({ isConnected: true, lastMessage: message });

    renderHook(() => useRealtimeInvalidation());

    expect(mockInvalidateQueries).toHaveBeenCalledWith({ queryKey: ['investigations'] });
    expect(mockInvalidateQueries).toHaveBeenCalledWith({ queryKey: ['investigation', 'INV-001'] });
  });

  it('invalidates position keys for POSITION_UPDATE', () => {
    const message = { type: 'POSITION_UPDATE', data: {} };
    mockUseWebSocket.mockReturnValue({ isConnected: true, lastMessage: message });

    renderHook(() => useRealtimeInvalidation());

    expect(mockInvalidateQueries).toHaveBeenCalledWith({ queryKey: ['user', 'positions'] });
    expect(mockInvalidateQueries).toHaveBeenCalledWith({ queryKey: ['user', 'portfolio', 'summary'] });
  });

  it('invalidates paradox keys for PARADOX_SPAWN', () => {
    const message = { type: 'PARADOX_SPAWN', data: {} };
    mockUseWebSocket.mockReturnValue({ isConnected: true, lastMessage: message });

    renderHook(() => useRealtimeInvalidation());

    expect(mockInvalidateQueries).toHaveBeenCalledWith({ queryKey: ['paradoxes', 'active'] });
    expect(mockInvalidateQueries).toHaveBeenCalledWith({ queryKey: ['paradox', 'active'] });
  });

  it('ignores unknown event types', () => {
    const message = { type: 'UNKNOWN_EVENT', data: {} };
    mockUseWebSocket.mockReturnValue({ isConnected: true, lastMessage: message });

    renderHook(() => useRealtimeInvalidation());

    expect(mockInvalidateQueries).not.toHaveBeenCalled();
  });

  it('does not re-process the same message', () => {
    const message = { type: 'WING_FLAP', data: {} };
    mockUseWebSocket.mockReturnValue({ isConnected: true, lastMessage: message });

    const { rerender } = renderHook(() => useRealtimeInvalidation());

    const firstCallCount = mockInvalidateQueries.mock.calls.length;
    expect(firstCallCount).toBeGreaterThan(0);

    // Re-render with same message reference
    rerender();

    // Should not process again
    expect(mockInvalidateQueries.mock.calls.length).toBe(firstCallCount);
  });
});
