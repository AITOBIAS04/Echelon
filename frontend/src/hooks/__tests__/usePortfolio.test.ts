import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createElement } from 'react';
import { usePositions, usePortfolioSummary } from '../usePortfolio';

// Mock apiClient
vi.mock('../../api/client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

import { apiClient } from '../../api/client';

const mockGet = vi.mocked(apiClient.get);

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children);
}

describe('usePositions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls /api/v1/user/positions and transforms response', async () => {
    const mockPositions = {
      positions: [
        {
          id: 'pos-1',
          timeline_id: 'tl-1',
          timeline_name: 'Test Timeline',
          side: 'YES',
          shards_held: 100,
          average_entry_price: 0.5,
          current_price: 0.7,
          unrealised_pnl_usd: 20.0,
          unrealised_pnl_percent: 40.0,
          timeline_stability: 85.0,
          has_active_paradox: false,
          is_founder: true,
          opened_at: '2026-01-01T00:00:00Z',
        },
        {
          id: 'pos-2',
          timeline_id: 'tl-2',
          timeline_name: 'Another Timeline',
          side: 'NO',
          shards_held: 50,
          average_entry_price: 0.3,
          current_price: 0.4,
          unrealised_pnl_usd: 5.0,
          unrealised_pnl_percent: 33.3,
          timeline_stability: 60.0,
          has_active_paradox: true,
          is_founder: false,
          opened_at: '2026-02-01T00:00:00Z',
        },
      ],
    };

    mockGet.mockResolvedValueOnce({ data: mockPositions } as any);

    const { result } = renderHook(() => usePositions(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(mockGet).toHaveBeenCalledWith('/api/v1/user/positions');
    expect(result.current.positions).toHaveLength(2);
    expect(result.current.positions[0].timeline_name).toBe('Test Timeline');
    expect(result.current.positions[0].side).toBe('YES');

    // Check totals computation
    const { totals } = result.current;
    expect(totals.totalPL).toBe(25.0); // 20 + 5
    expect(totals.yesNotional).toBeCloseTo(70); // 100 * 0.7
    expect(totals.noNotional).toBeCloseTo(20); // 50 * 0.4
  });

  it('returns empty positions when API returns none', async () => {
    mockGet.mockResolvedValueOnce({ data: { positions: [] } } as any);

    const { result } = renderHook(() => usePositions(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.positions).toHaveLength(0);
    expect(result.current.totals.totalPL).toBe(0);
    expect(result.current.totals.winRate).toBe(0);
  });
});

describe('usePortfolioSummary', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls /api/v1/user/portfolio/summary', async () => {
    const mockSummary = {
      total_value_usd: 1000.0,
      total_unrealised_pnl_usd: 50.0,
      total_unrealised_pnl_percent: 5.0,
      active_position_count: 5,
      timelines_at_risk: 1,
      total_founder_yield_earned_usd: 150.0,
      active_founder_positions: 2,
      highest_risk_timeline_id: 'TL_RISKY',
      highest_risk_timeline_name: 'Risky Timeline',
      highest_risk_stability: 35.0,
    };

    mockGet.mockResolvedValueOnce({ data: mockSummary } as any);

    const { result } = renderHook(() => usePortfolioSummary(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(mockGet).toHaveBeenCalledWith('/api/v1/user/portfolio/summary');
    expect(result.current.summary?.total_value_usd).toBe(1000.0);
    expect(result.current.summary?.active_founder_positions).toBe(2);
  });
});
