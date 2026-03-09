import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { HomePage } from '../HomePage';

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
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>
        {ui}
      </QueryClientProvider>
    </MemoryRouter>,
  );
}

const mockTimelinesResponse = {
  timelines: [
    {
      id: 'tl-1',
      name: 'BTC_100K',
      is_active: true,
      stability: 0.85,
      has_active_paradox: false,
      price_yes: 0.65,
      total_volume_usd: 5000,
    },
    {
      id: 'tl-2',
      name: 'ETH_MERGE',
      is_active: true,
      stability: 0.55,
      has_active_paradox: true,
      price_yes: 0.4,
      total_volume_usd: 3000,
    },
  ],
};

describe('HomePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders summary cards from real aggregated API data', async () => {
    mockGet.mockImplementation((url: string) => {
      if (url.includes('/timelines/health')) {
        return Promise.resolve({ data: mockTimelinesResponse });
      }
      if (url.includes('/agents')) {
        return Promise.resolve({ data: { agents: [], total: 5 } });
      }
      if (url.includes('/paradox/active')) {
        return Promise.resolve({ data: { paradoxes: [], total_active: 2 } });
      }
      if (url.includes('/investigations')) {
        return Promise.resolve({ data: { investigations: [], total: 3 } });
      }
      if (url.includes('/butterfly/flaps')) {
        return Promise.resolve({
          data: {
            flaps: [
              {
                id: 'flap-1',
                timeline_id: 'tl-1',
                timeline_name: 'BTC_100K',
                flap_type: 'TRADE',
                action: 'Agent bought YES',
                timestamp: new Date().toISOString(),
              },
            ],
          },
        });
      }
      return Promise.resolve({ data: {} });
    });

    renderWithProviders(<HomePage />);

    // Summary cards should appear with real data
    expect(await screen.findByText('Active Theatres')).toBeInTheDocument();
    expect(screen.getByText('Average Stability')).toBeInTheDocument();
    expect(screen.getByText('70%')).toBeInTheDocument(); // avg of 0.85 and 0.55
    expect(screen.getByText('Active Paradoxes')).toBeInTheDocument();
    expect(screen.getAllByText('Investigations').length).toBeGreaterThan(0);

    // Activity feed should show real flaps
    expect(screen.getByText('Recent Activity')).toBeInTheDocument();
    expect(screen.getByText('TRADE')).toBeInTheDocument();
    expect(screen.getByText('Agent bought YES')).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  it('renders loading state', () => {
    mockGet.mockReturnValue(new Promise(() => {})); // never resolves

    renderWithProviders(<HomePage />);

    expect(document.querySelectorAll('.animate-pulse').length).toBeGreaterThan(0);
  });

  it('renders empty activity feed when no flaps', async () => {
    mockGet.mockImplementation((url: string) => {
      if (url.includes('/timelines/health')) {
        return Promise.resolve({ data: { timelines: [] } });
      }
      if (url.includes('/agents')) {
        return Promise.resolve({ data: { agents: [], total: 0 } });
      }
      if (url.includes('/paradox/active')) {
        return Promise.resolve({ data: { paradoxes: [], total_active: 0 } });
      }
      if (url.includes('/investigations')) {
        return Promise.resolve({ data: { investigations: [], total: 0 } });
      }
      if (url.includes('/butterfly/flaps')) {
        return Promise.resolve({ data: { flaps: [] } });
      }
      return Promise.resolve({ data: {} });
    });

    renderWithProviders(<HomePage />);

    expect(await screen.findByText('No recent activity')).toBeInTheDocument();
  });
});
