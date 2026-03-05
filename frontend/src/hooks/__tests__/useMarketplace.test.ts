import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createElement } from 'react';
import { useMarketData, useMarketStats } from '../useMarketplace';

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

const MOCK_TIMELINES = {
  timelines: [
    {
      id: 'tl-1',
      name: 'Bitcoin 100k',
      slug: 'btc-100k',
      stability: 85,
      price_yes: 0.72,
      price_no: 0.28,
      logic_gap: 0.15,
      liquidity_depth_usd: 50000,
      connected_timeline_ids: [],
      total_volume_usd: 120000,
      active_agent_count: 12,
      has_active_paradox: false,
      last_flap_at: '2026-01-01T00:00:00Z',
      decay_multiplier: 1.0,
      is_anchor: true,
      anchor_timeline_id: null,
      fork_divergence: 0,
      last_sync_at: null,
    },
    {
      id: 'tl-2',
      name: 'ETH Merge',
      slug: 'eth-merge',
      stability: 45,
      price_yes: 0.55,
      price_no: 0.45,
      logic_gap: 0.42,
      liquidity_depth_usd: 30000,
      connected_timeline_ids: ['tl-1'],
      total_volume_usd: 80000,
      active_agent_count: 8,
      has_active_paradox: true,
      last_flap_at: '2026-01-02T00:00:00Z',
      decay_multiplier: 2.0,
      is_anchor: false,
      anchor_timeline_id: 'tl-1',
      fork_divergence: 40,
      last_sync_at: '2026-01-01T12:00:00Z',
    },
  ],
  snapshot_at: '2026-01-01T00:00:00Z',
};

describe('useMarketData', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls /api/v1/butterfly/timelines/health and transforms to Market[]', async () => {
    mockGet.mockResolvedValueOnce({ data: MOCK_TIMELINES } as any);

    const { result } = renderHook(() => useMarketData(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(mockGet).toHaveBeenCalledWith('/api/v1/butterfly/timelines/health');
    expect(result.current.data).toHaveLength(2);

    const market1 = result.current.data[0];
    expect(market1.id).toBe('tl-1');
    expect(market1.title).toBe('Bitcoin 100k');
    expect(market1.yesPrice).toBe(0.72);
    expect(market1.noPrice).toBe(0.28);
    expect(market1.yesProb).toBe(72);
    expect(market1.stability).toBe(85);
    expect(market1.stabilityStatus).toBe('Stable');
    expect(market1.gap).toBeCloseTo(15);
    expect(market1.gapWarning).toBe(false);

    const market2 = result.current.data[1];
    expect(market2.stabilityStatus).toBe('Degraded');
    expect(market2.gap).toBeCloseTo(42);
    expect(market2.gapWarning).toBe(true);
  });

  it('returns empty when API returns no timelines', async () => {
    mockGet.mockResolvedValueOnce({ data: { timelines: [], snapshot_at: '' } } as any);

    const { result } = renderHook(() => useMarketData(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.data).toHaveLength(0);
  });
});

describe('useMarketStats', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('derives stats from timeline health data', async () => {
    mockGet.mockResolvedValueOnce({ data: MOCK_TIMELINES } as any);

    const { result } = renderHook(() => useMarketStats(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.totalMarkets).toBe(2));

    expect(result.current.totalVolume24h).toBe(200000);
    expect(result.current.activeForks).toBe(1); // tl-2 has connected_timeline_ids
    expect(result.current.activeBreaches).toBe(1); // tl-2 has_active_paradox
  });
});
