import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BreachConsolePage } from '../BreachConsolePage';

vi.mock('../../api/client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

import { apiClient } from '../../api/client';

const mockGet = vi.mocked(apiClient.get);

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>,
  );
}

describe('BreachConsolePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders paradox data from real API (no demoStore)', async () => {
    const mockParadoxes = {
      paradoxes: [
        {
          id: 'pdx-1',
          timeline_id: 'tl-1',
          timeline_name: 'BTC_100K',
          status: 'ACTIVE',
          severity_class: 'CLASS_1_CRITICAL',
          logic_gap: 0.68,
          spawned_at: '2026-03-01T12:00:00Z',
          detonation_time: '2026-03-01T13:00:00Z',
          time_remaining_seconds: 1800,
          decay_multiplier: 5.0,
          extraction_cost_usdc: 500,
          extraction_cost_echelon: 100,
          carrier_sanity_cost: 30,
          carrier_agent_id: null,
          carrier_agent_name: null,
          carrier_agent_sanity: null,
          connected_timelines: ['tl-2'],
        },
      ],
      total_active: 1,
    };

    mockGet.mockResolvedValue({ data: mockParadoxes } as any);

    renderWithProviders(<BreachConsolePage />);

    // Should show loading initially then data
    expect(await screen.findByText('BTC_100K')).toBeInTheDocument();
    expect(screen.getByText('CRITICAL')).toBeInTheDocument();
    expect(screen.getByText(/68%/)).toBeInTheDocument(); // logic gap

    // Should show Active Paradoxes header (multiple matches: header + analytics)
    expect(screen.getAllByText(/Active Paradoxes/).length).toBeGreaterThanOrEqual(1);

    // Verify no demo/mock imports — this is structural (see source file imports)
    // The component imports from ../hooks/useBreaches, not from ../demo/*
  });

  it('renders empty state when no paradoxes', async () => {
    mockGet.mockResolvedValue({ data: { paradoxes: [], total_active: 0 } } as any);

    renderWithProviders(<BreachConsolePage />);

    expect(await screen.findByText('No active paradoxes detected')).toBeInTheDocument();
  });

  it('shows extracting status badge', async () => {
    const mockParadoxes = {
      paradoxes: [
        {
          id: 'pdx-2',
          timeline_id: 'tl-2',
          timeline_name: 'ETH_MERGE',
          status: 'EXTRACTING',
          severity_class: 'CLASS_2_SEVERE',
          logic_gap: 0.45,
          spawned_at: '2026-03-01T12:00:00Z',
          detonation_time: '2026-03-01T13:00:00Z',
          time_remaining_seconds: 900,
          decay_multiplier: 3.0,
          extraction_cost_usdc: 300,
          extraction_cost_echelon: 50,
          carrier_sanity_cost: 20,
          carrier_agent_id: 'agent-1',
          carrier_agent_name: 'VIPER',
          carrier_agent_sanity: 60,
          connected_timelines: [],
        },
      ],
      total_active: 1,
    };

    mockGet.mockResolvedValue({ data: mockParadoxes } as any);

    renderWithProviders(<BreachConsolePage />);

    expect(await screen.findByText('EXTRACTING')).toBeInTheDocument();
    expect(screen.getByText('ETH_MERGE')).toBeInTheDocument();
    expect(screen.getByText('VIPER', { exact: false })).toBeInTheDocument();
  });

  it('has disabled action buttons', async () => {
    mockGet.mockResolvedValue({
      data: {
        paradoxes: [{
          id: 'pdx-1', timeline_id: 'tl-1', timeline_name: 'TEST',
          status: 'ACTIVE', severity_class: 'CLASS_3_MODERATE',
          logic_gap: 0.3, spawned_at: '2026-03-01T12:00:00Z',
          detonation_time: '2026-03-01T13:00:00Z', time_remaining_seconds: 600,
          decay_multiplier: 2.0, extraction_cost_usdc: 100,
          extraction_cost_echelon: 20, carrier_sanity_cost: 10,
          carrier_agent_id: null, carrier_agent_name: null,
          carrier_agent_sanity: null, connected_timelines: [],
        }],
        total_active: 1,
      },
    } as any);

    renderWithProviders(<BreachConsolePage />);

    await screen.findByText('TEST');

    const extractBtn = screen.getByText('Extract').closest('button');
    expect(extractBtn).toBeDisabled();

    const abandonBtn = screen.getByText('Abandon').closest('button');
    expect(abandonBtn).toBeDisabled();
  });
});
