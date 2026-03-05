import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createElement } from 'react';
import { useAgentRoster, useArchetypeDistribution } from '../useAgents';

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

describe('useAgentRoster', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls /api/v1/agents and enriches agents with presentation fields', async () => {
    const mockResponse = {
      agents: [
        {
          id: 'agent-1',
          name: 'Moby',
          archetype: 'WHALE',
          tier: 2,
          level: 3,
          sanity: 80,
          max_sanity: 100,
          is_alive: true,
          death_cause: null,
          owner_id: 'user-1',
          total_pnl_usd: 1500.0,
          win_rate: 0.65,
          trades_count: 42,
          genome: {},
          parent_agent_ids: [],
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-03-01T00:00:00Z',
        },
        {
          id: 'agent-2',
          name: 'Spike',
          archetype: 'SHARK',
          tier: 1,
          level: 1,
          sanity: 30,
          max_sanity: 100,
          is_alive: true,
          death_cause: null,
          owner_id: 'user-1',
          total_pnl_usd: -200.0,
          win_rate: 0.35,
          trades_count: 15,
          genome: {},
          parent_agent_ids: ['agent-1', 'agent-3'],
          created_at: '2026-02-01T00:00:00Z',
          updated_at: '2026-03-01T00:00:00Z',
        },
      ],
      total: 2,
    };

    mockGet.mockResolvedValueOnce({ data: mockResponse } as any);

    const { result } = renderHook(() => useAgentRoster(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(mockGet).toHaveBeenCalledWith('/api/v1/agents', { params: { is_alive: true } });
    expect(result.current.agents).toHaveLength(2);

    // Check enrichment: genesis agent
    const whale = result.current.agents[0];
    expect(whale.pnl).toBe(1500.0);
    expect(whale.isGenesis).toBe(true);
    expect(whale.generation).toBe(1);
    expect(whale.lineage).toBe('GENESIS AGENT');
    expect(whale.winRate).toBe(65);
    expect(whale.actions).toBe(42);
    expect(whale.sanityLevel).toBe('stable');
    expect(whale.color).toBe('#3B82F6'); // WHALE color

    // Check enrichment: child agent
    const shark = result.current.agents[1];
    expect(shark.isGenesis).toBe(false);
    expect(shark.generation).toBe(2);
    expect(shark.parents).toContain('agent-1');
    expect(shark.sanityLevel).toBe('critical'); // 30/100 = 0.3, below 0.4 threshold
    expect(shark.pnlDisplay).toContain('-$200');

    // Check stats
    expect(result.current.stats.genesisCount).toBe(1);
    expect(result.current.stats.totalPL).toBe(1300.0); // 1500 + (-200)
  });

  it('handles empty agent list', async () => {
    mockGet.mockResolvedValueOnce({ data: { agents: [], total: 0 } } as any);

    const { result } = renderHook(() => useAgentRoster(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.agents).toHaveLength(0);
    expect(result.current.stats.totalPL).toBe(0);
    expect(result.current.stats.avgWinRate).toBe(0);
    expect(result.current.stats.avgSanity).toBe(0);
    expect(result.current.stats.genesisCount).toBe(0);
  });
});

describe('useArchetypeDistribution', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('groups agents by archetype with correct colors', async () => {
    const mockResponse = {
      agents: [
        { id: '1', name: 'A', archetype: 'WHALE', tier: 1, level: 1, sanity: 100, max_sanity: 100, is_alive: true, death_cause: null, owner_id: 'u', total_pnl_usd: 0, win_rate: 0, trades_count: 0, genome: {}, parent_agent_ids: [], created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' },
        { id: '2', name: 'B', archetype: 'WHALE', tier: 1, level: 1, sanity: 100, max_sanity: 100, is_alive: true, death_cause: null, owner_id: 'u', total_pnl_usd: 0, win_rate: 0, trades_count: 0, genome: {}, parent_agent_ids: [], created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' },
        { id: '3', name: 'C', archetype: 'DEGEN', tier: 1, level: 1, sanity: 100, max_sanity: 100, is_alive: true, death_cause: null, owner_id: 'u', total_pnl_usd: 0, win_rate: 0, trades_count: 0, genome: {}, parent_agent_ids: [], created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' },
      ],
      total: 3,
    };

    mockGet.mockResolvedValueOnce({ data: mockResponse } as any);

    const { result } = renderHook(() => useArchetypeDistribution(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.length).toBeGreaterThan(0));

    const whaleEntry = result.current.find((d) => d.archetype === 'WHALE');
    expect(whaleEntry?.count).toBe(2);
    expect(whaleEntry?.color).toBe('#3B82F6');

    const degenEntry = result.current.find((d) => d.archetype === 'DEGEN');
    expect(degenEntry?.count).toBe(1);
    expect(degenEntry?.color).toBe('#10B981');
  });
});
