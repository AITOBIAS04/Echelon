import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AgentPerformanceDashboard } from '../AgentPerformanceDashboard';

vi.mock('../../../api/client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

import { apiClient } from '../../../api/client';

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

const MOCK_AGENT = {
  id: 'agent-001',
  name: 'ALPHA-SHARK',
  archetype: 'SHARK',
  tier: 2,
  level: 5,
  sanity: 75,
  max_sanity: 100,
  is_alive: true,
  death_cause: null,
  owner_id: 'user-001',
  total_pnl_usd: 1234.56,
  win_rate: 0.65,
  trades_count: 42,
  genome: { aggression: 0.8, risk_tolerance: 0.6 },
  parent_agent_ids: [],
  created_at: '2026-03-01T10:00:00Z',
  updated_at: '2026-03-05T12:00:00Z',
};

describe('AgentPerformanceDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders agent header with trade history', async () => {
    mockGet.mockImplementation((url: string) => {
      if (url.includes('/agents/agent-001')) {
        return Promise.resolve({ data: MOCK_AGENT });
      }
      // Roster for archetype comparison
      return Promise.resolve({ data: { agents: [MOCK_AGENT], total: 1 } });
    });

    renderWithProviders(<AgentPerformanceDashboard agentId="agent-001" />);

    // Agent name and archetype
    expect(await screen.findByText('ALPHA-SHARK')).toBeInTheDocument();
    expect(screen.getByText('SHARK')).toBeInTheDocument();

    // Trade history renders
    expect(await screen.findByText('Trade History')).toBeInTheDocument();
    expect(screen.getByText('Total Trades')).toBeInTheDocument();

    // Genome renders
    expect(screen.getByText('Genome')).toBeInTheDocument();
  });

  it('shows loading skeletons while fetching', () => {
    mockGet.mockReturnValue(new Promise(() => {})); // Never resolves

    renderWithProviders(<AgentPerformanceDashboard agentId="agent-001" />);

    // Should show skeleton animation (animate-pulse class)
    const skeletons = document.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThan(0);
  });
});
