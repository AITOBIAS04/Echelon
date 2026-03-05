import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { InvestigationPage } from '../InvestigationPage';

vi.mock('../../api/client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

import { apiClient } from '../../api/client';

const mockGet = vi.mocked(apiClient.get);

const mockListResponse = {
  investigations: [
    {
      id: 'INV-abc123',
      theatre_id: 'TH_TEST',
      construct_id: 'CON_TEST',
      inquiry_class: 'INVESTIGATIVE',
      status: 'active',
      evidence_count: 2,
      claim_count: 1,
      counter_signal_count: 1,
      drift_event_count: 0,
      created_at: '2026-03-01T10:00:00Z',
      updated_at: '2026-03-01T12:00:00Z',
    },
  ],
  total: 1,
};

const mockDetailResponse = {
  id: 'INV-abc123',
  theatre_id: 'TH_TEST',
  construct_id: 'CON_TEST',
  inquiry_class: 'INVESTIGATIVE',
  status: 'active',
  stop_condition: 'OUTCOME_RESOLUTION',
  stop_config: {},
  created_at: '2026-03-01T10:00:00Z',
  updated_at: '2026-03-01T12:00:00Z',
  evidence: {
    items: [
      {
        evidence_id: 'EV001',
        content_hash: 'abc123',
        provenance_class: 'PRIMARY',
        submitted_at: '2026-03-01T11:00:00Z',
        content_type: 'text/plain',
        source_description: 'Test',
        references: [],
      },
    ],
    redactions: [],
    provenance_summary: { PRIMARY: 1 },
    envelope_hash: 'envhash',
  },
  claims: {
    claims: [
      {
        claim_id: 'CLM001',
        claim_text: 'Test claim',
        claim_type: 'fact',
        evidence_refs: ['EV001'],
        counter_signals: [],
        status: 'unconfirmed',
        confidence: 0.5,
        independence_groups: [],
      },
    ],
    root_hash: 'roothash',
    status_summary: { unconfirmed: 1 },
  },
  counter_signals: {
    signals: [],
    summary: {},
  },
  drift: {
    events: [],
    has_material_drift: false,
  },
};

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

describe('InvestigationPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders investigation list from API', async () => {
    mockGet.mockImplementation((url: string) => {
      if (url.endsWith('/investigations/')) {
        return Promise.resolve({ data: mockListResponse });
      }
      return Promise.resolve({ data: {} });
    });

    renderWithProviders(<InvestigationPage />);

    expect(await screen.findByText('INV-abc123')).toBeInTheDocument();
    expect(screen.getByText('active')).toBeInTheDocument();
  });

  it('shows detail and tab navigation after selecting investigation', async () => {
    mockGet.mockImplementation((url: string) => {
      if (url.endsWith('/investigations/')) {
        return Promise.resolve({ data: mockListResponse });
      }
      if (url.includes('/investigations/INV-abc123')) {
        return Promise.resolve({ data: mockDetailResponse });
      }
      return Promise.resolve({ data: {} });
    });

    renderWithProviders(<InvestigationPage />);

    // Click on investigation
    const invButton = await screen.findByText('INV-abc123');
    fireEvent.click(invButton);

    // Overview tab should be active (wait for detail to load)
    expect(await screen.findByText('OUTCOME_RESOLUTION')).toBeInTheDocument();

    // Tab buttons should be visible — tabs now use role="tab"
    const tabs = screen.getAllByRole('tab');
    const tabLabels = tabs.map((t) => t.textContent);
    expect(tabLabels).toEqual(expect.arrayContaining(['Overview', 'Evidence', 'Claims', 'Signals', 'Drift']));

    // Switch to Evidence tab
    const evidenceTab = tabs.find((t) => t.textContent === 'Evidence')!;
    fireEvent.click(evidenceTab);
    expect(await screen.findByText('EV001')).toBeInTheDocument();

    // Switch to Claims tab
    const claimsTab = tabs.find((t) => t.textContent === 'Claims')!;
    fireEvent.click(claimsTab);
    expect(await screen.findByText('CLM001')).toBeInTheDocument();
  });

  it('shows empty state when no investigations', async () => {
    mockGet.mockResolvedValue({
      data: { investigations: [], total: 0 },
    } as any);

    renderWithProviders(<InvestigationPage />);

    expect(await screen.findByText(/No investigations found/)).toBeInTheDocument();
  });
});
