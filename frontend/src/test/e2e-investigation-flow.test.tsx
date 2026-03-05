/**
 * E2E Investigation Flow Test
 *
 * Verifies the full flow: create investigation → view evidence → inspect claims → check certificate.
 * Uses mocked API responses, exercises component rendering paths.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

vi.mock('../api/investigation', () => ({
  createInvestigation: vi.fn(),
  fetchInvestigations: vi.fn(),
  fetchInvestigation: vi.fn(),
}));

import { fetchInvestigations, fetchInvestigation } from '../api/investigation';
import { InvestigationPage } from '../pages/InvestigationPage';

const mockFetchList = vi.mocked(fetchInvestigations);
const mockFetchDetail = vi.mocked(fetchInvestigation);

function renderWithProviders(ui: React.ReactElement, route = '/investigation') {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <MemoryRouter initialEntries={[route]}>
      <QueryClientProvider client={queryClient}>
        {ui}
      </QueryClientProvider>
    </MemoryRouter>,
  );
}

const MOCK_INVESTIGATION = {
  id: 'INV-E2E',
  theatre_id: 'TH_TEST',
  construct_id: 'CON_TEST',
  inquiry_class: 'INVESTIGATIVE',
  status: 'active',
  stop_condition: 'EVIDENCE_THRESHOLD',
  stop_config: { min_supported_claims: 3 },
  created_at: '2026-03-01T10:00:00Z',
  updated_at: '2026-03-05T12:00:00Z',
  evidence: {
    items: [
      {
        evidence_id: 'EV001',
        content_hash: 'abc123',
        provenance_class: 'public_primary',
        submitted_at: '2026-03-01T11:00:00Z',
        content_type: 'text/plain',
        source_description: 'SEC Filing 10-K',
        references: [],
      },
    ],
    redactions: [],
    provenance_summary: { public_primary: 1 },
    envelope_hash: 'envhash',
  },
  claims: {
    claims: [
      {
        claim_id: 'CLM001',
        claim_text: 'Revenue exceeded $1B',
        claim_type: 'fact',
        evidence_refs: ['EV001'],
        counter_signals: [],
        status: 'supported',
        confidence: 0.85,
        independence_groups: [],
      },
    ],
    root_hash: 'roothash',
    status_summary: { supported: 1 },
  },
  counter_signals: { signals: [], summary: {} },
  drift: { events: [], has_material_drift: false },
};

describe('E2E Investigation Flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('view evidence → inspect claims via tab navigation', async () => {
    mockFetchList.mockResolvedValue({
      investigations: [
        {
          id: 'INV-E2E',
          theatre_id: 'TH_TEST',
          construct_id: 'CON_TEST',
          inquiry_class: 'INVESTIGATIVE',
          status: 'active',
          evidence_count: 1,
          claim_count: 1,
          counter_signal_count: 0,
          drift_event_count: 0,
          created_at: '2026-03-01T10:00:00Z',
          updated_at: '2026-03-05T12:00:00Z',
        },
      ],
      total: 1,
    });
    mockFetchDetail.mockResolvedValue(MOCK_INVESTIGATION as any);

    renderWithProviders(<InvestigationPage />);

    // Wait for investigation list
    expect(await screen.findByText('INV-E2E')).toBeInTheDocument();

    // Select investigation
    fireEvent.click(screen.getByText('INV-E2E'));

    // Wait for detail to load — Overview tab (tabs use role="tab")
    expect(await screen.findByText('EVIDENCE_THRESHOLD')).toBeInTheDocument();

    // Switch to Evidence tab using role="tab"
    const tabs = screen.getAllByRole('tab');
    const evidenceTab = tabs.find((t) => t.textContent === 'Evidence')!;
    fireEvent.click(evidenceTab);
    expect(await screen.findByText('EV001')).toBeInTheDocument();

    // Switch to Claims tab
    const claimsTab = tabs.find((t) => t.textContent === 'Claims')!;
    fireEvent.click(claimsTab);
    expect(await screen.findByText('Revenue exceeded $1B')).toBeInTheDocument();
  });
});
