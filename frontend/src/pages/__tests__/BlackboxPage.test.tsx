import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BlackboxPage } from '../BlackboxPage';

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

describe('BlackboxPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders agent leaderboard from real API', async () => {
    mockGet.mockImplementation((url: string) => {
      if (url.includes('/agents')) {
        return Promise.resolve({
          data: {
            agents: [
              {
                id: 'agent-1',
                name: 'VIPER',
                archetype: 'Contrarian',
                total_pnl_usd: 1200,
                win_rate: 0.72,
                trades_count: 15,
                is_alive: true,
              },
            ],
          },
        });
      }
      if (url.includes('/timelines/health')) {
        return Promise.resolve({
          data: {
            timelines: [
              {
                id: 'tl-1',
                name: 'BTC_100K',
                is_active: true,
                stability: 0.8,
                has_active_paradox: false,
                price_yes: 0.65,
                total_volume_usd: 5000,
              },
            ],
          },
        });
      }
      return Promise.resolve({ data: {} });
    });

    renderWithProviders(<BlackboxPage />);

    // Agent leaderboard should show real data
    expect(await screen.findByText('VIPER')).toBeInTheDocument();
  });

  it('shows Coming Soon panels for unavailable features', async () => {
    mockGet.mockResolvedValue({ data: { agents: [], timelines: [] } } as any);

    renderWithProviders(<BlackboxPage />);

    // These features are honestly marked as not yet available
    expect(await screen.findByText('Time & Sales')).toBeInTheDocument();
    expect(screen.getByText('Signal Intercepts')).toBeInTheDocument();
  });
});
