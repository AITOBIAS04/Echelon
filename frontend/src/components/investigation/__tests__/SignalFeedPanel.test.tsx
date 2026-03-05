import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { SignalFeedPanel } from '../SignalFeedPanel';

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
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>
        {ui}
      </QueryClientProvider>
    </MemoryRouter>,
  );
}

describe('SignalFeedPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders signals with source badges', async () => {
    mockGet.mockImplementation((url: string) => {
      if (url.endsWith('/investigations/')) {
        return Promise.resolve({
          data: {
            investigations: [
              {
                id: 'INV-001',
                theatre_id: 'TH_TEST',
                construct_id: 'CON_TEST',
                inquiry_class: 'INVESTIGATIVE',
                status: 'active',
                evidence_count: 1,
                claim_count: 1,
                counter_signal_count: 2,
                drift_event_count: 0,
                created_at: '2026-03-01T10:00:00Z',
                updated_at: '2026-03-01T12:00:00Z',
              },
            ],
            total: 1,
          },
        });
      }
      if (url.includes('/investigations/INV-001')) {
        return Promise.resolve({
          data: {
            id: 'INV-001',
            theatre_id: 'TH_TEST',
            construct_id: 'CON_TEST',
            inquiry_class: 'INVESTIGATIVE',
            status: 'active',
            stop_condition: 'OUTCOME_RESOLUTION',
            stop_config: {},
            created_at: '2026-03-01T10:00:00Z',
            updated_at: '2026-03-01T12:00:00Z',
            evidence: { items: [], redactions: [], provenance_summary: {}, envelope_hash: 'hash' },
            claims: { claims: [], root_hash: 'hash', status_summary: {} },
            counter_signals: {
              signals: [
                {
                  counter_signal_id: 'CS001',
                  signal_class: 'official_denial',
                  detected_at: '2026-03-01T11:00:00Z',
                  evidence_ref: 'EV001',
                  material: true,
                  resolution_impact: 'high',
                  detection_method: 'automated',
                },
                {
                  counter_signal_id: 'CS002',
                  signal_class: 'market_contradiction',
                  detected_at: '2026-03-01T11:30:00Z',
                  evidence_ref: null,
                  material: false,
                  resolution_impact: 'low',
                  detection_method: 'manual',
                },
              ],
              summary: { official_denial: 1, market_contradiction: 1 },
            },
            drift: { events: [], has_material_drift: false },
          },
        });
      }
      return Promise.resolve({ data: {} });
    });

    renderWithProviders(<SignalFeedPanel />);

    // Should show signal class badges
    expect(await screen.findByText('official denial')).toBeInTheDocument();
    expect(screen.getByText('market contradiction')).toBeInTheDocument();

    // Should show material badge
    expect(screen.getByText('Material')).toBeInTheDocument();

    // Should show "Create Investigation from Signal" buttons
    expect(screen.getAllByText('Create Investigation from Signal').length).toBe(2);
  });

  it('shows empty state when no signals', async () => {
    mockGet.mockImplementation((url: string) => {
      if (url.endsWith('/investigations/')) {
        return Promise.resolve({
          data: {
            investigations: [
              {
                id: 'INV-001',
                theatre_id: 'TH_TEST',
                construct_id: 'CON_TEST',
                inquiry_class: 'INVESTIGATIVE',
                status: 'active',
                evidence_count: 0,
                claim_count: 0,
                counter_signal_count: 0,
                drift_event_count: 0,
                created_at: '2026-03-01T10:00:00Z',
                updated_at: '2026-03-01T12:00:00Z',
              },
            ],
            total: 1,
          },
        });
      }
      if (url.includes('/investigations/INV-001')) {
        return Promise.resolve({
          data: {
            id: 'INV-001',
            theatre_id: 'TH_TEST',
            construct_id: 'CON_TEST',
            inquiry_class: 'INVESTIGATIVE',
            status: 'active',
            stop_condition: 'OUTCOME_RESOLUTION',
            stop_config: {},
            created_at: '2026-03-01T10:00:00Z',
            updated_at: '2026-03-01T12:00:00Z',
            evidence: { items: [], redactions: [], provenance_summary: {}, envelope_hash: 'hash' },
            claims: { claims: [], root_hash: 'hash', status_summary: {} },
            counter_signals: { signals: [], summary: {} },
            drift: { events: [], has_material_drift: false },
          },
        });
      }
      return Promise.resolve({ data: {} });
    });

    renderWithProviders(<SignalFeedPanel />);

    expect(await screen.findByText('No counter-signals detected yet.')).toBeInTheDocument();
  });
});
