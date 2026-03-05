import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConvergenceMap } from '../ConvergenceMap';

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

describe('ConvergenceMap', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders grid cells from API data', async () => {
    mockGet.mockResolvedValue({
      data: {
        cells: [
          { lat: 45, lon: -90, density: 0.8, events: 12, sources: ['WM', 'CH'], theatres: ['FED_RATE'] },
          { lat: 30, lon: 0, density: 0.3, events: 5, sources: ['WM'], theatres: [] },
        ],
        grid_size: 1,
      },
    });

    renderWithProviders(<ConvergenceMap />);

    // Header renders
    expect(await screen.findByText('Convergence Map')).toBeInTheDocument();

    // Legend renders
    expect(screen.getByText('Low')).toBeInTheDocument();
    expect(screen.getByText('Critical')).toBeInTheDocument();

    // Grid cells are buttons (12×8 = 96 cells) — wait for async load
    const buttons = await screen.findAllByRole('button');
    expect(buttons.length).toBe(96);
  });

  it('shows detail panel on cell click', async () => {
    mockGet.mockResolvedValue({
      data: {
        cells: [
          { lat: 45, lon: -90, density: 0.8, events: 12, sources: ['WorldMonitor'], theatres: ['FED_RATE'] },
        ],
        grid_size: 1,
      },
    });

    renderWithProviders(<ConvergenceMap />);

    // Wait for grid to render
    const buttons = await screen.findAllByRole('button');
    fireEvent.click(buttons[0]);

    // Detail panel shows coordinates and data
    expect(screen.getByText(/Events/)).toBeInTheDocument();
    expect(screen.getByText('Sources')).toBeInTheDocument();
    expect(screen.getByText('Matched Theatres')).toBeInTheDocument();
  });
});
