import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RLMFPage } from '../RLMFPage';

vi.mock('../../api/client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

vi.mock('../../api/exports', () => ({
  listExportJobs: vi.fn(),
  createExportJob: vi.fn(),
  getDatasetPreview: vi.fn(),
}));

import { listExportJobs } from '../../api/exports';

const mockListJobs = vi.mocked(listExportJobs);

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

describe('RLMFPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders export viewer with job list', async () => {
    mockListJobs.mockResolvedValue([
      {
        id: 'export-1',
        kind: 'rlmf' as const,
        status: 'completed' as const,
        createdAt: '2026-03-01T10:00:00Z',
        completedAt: '2026-03-01T10:05:00Z',
        scope: { scope: 'global' as const },
        filter: { kind: 'rlmf' as const },
        rowCount: 1500,
        byteSize: 524288,
      },
    ]);

    renderWithProviders(<RLMFPage />);

    expect(await screen.findByText('RLMF Export Viewer')).toBeInTheDocument();
    // Wait for query data to load — 'completed' status badge appears after data resolves
    expect(await screen.findByText('completed')).toBeInTheDocument();
    expect(screen.getAllByText('RLMF Training Data').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('1,500')).toBeInTheDocument(); // rowCount
  });

  it('renders empty state when no export jobs', async () => {
    mockListJobs.mockResolvedValue([]);

    renderWithProviders(<RLMFPage />);

    expect(
      await screen.findByText('No export jobs found. Use the API to create exports.'),
    ).toBeInTheDocument();
  });

  it('shows dataset kind cards', async () => {
    mockListJobs.mockResolvedValue([]);

    renderWithProviders(<RLMFPage />);

    expect(await screen.findByText('RLMF Training Data')).toBeInTheDocument();
    expect(screen.getByText('Human Judgement')).toBeInTheDocument();
    expect(screen.getByText('Audit Trace')).toBeInTheDocument();
  });
});
