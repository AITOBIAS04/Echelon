import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { CreateInvestigationWizard } from '../CreateInvestigationWizard';

// Mock the API client
vi.mock('../../../api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

// Mock investigation API
vi.mock('../../../api/investigation', () => ({
  createInvestigation: vi.fn().mockResolvedValue({
    id: 'INV-TEST',
    theatre_id: null,
    construct_id: null,
    inquiry_class: 'INVESTIGATIVE',
    status: 'active',
    evidence_count: 0,
    claim_count: 0,
    counter_signal_count: 0,
    drift_event_count: 0,
    created_at: '2026-03-08T00:00:00Z',
  }),
  fetchInvestigations: vi.fn().mockResolvedValue({ investigations: [], total: 0 }),
}));

// Mock investigation templates API
vi.mock('../../../api/investigationTemplates', () => ({
  fetchInvestigationTemplates: vi.fn().mockResolvedValue({
    templates: [
      {
        template_id: 'blank',
        name: 'Blank Investigation',
        description: 'Start with a neutral bounded-inquiry shell and select every constraint directly.',
        inquiry_class: 'INVESTIGATIVE',
        template_status: 'ACTIVE',
        domain_filter_count: 0,
        requires_legal_review: false,
      },
      {
        template_id: 'corporate_due_diligence',
        name: 'Corporate Due Diligence',
        description: 'Bias toward registries, filings, legal coverage, and identity/provenance checks.',
        inquiry_class: 'INSPECTION',
        template_status: 'ACTIVE',
        domain_filter_count: 3,
        requires_legal_review: false,
      },
      {
        template_id: 'market_event',
        name: 'Market Event Analysis',
        description: 'Prepare for event-driven evidence, counter-signals, and fast routing pressure.',
        inquiry_class: 'INVESTIGATIVE',
        template_status: 'ACTIVE',
        domain_filter_count: 2,
        requires_legal_review: false,
      },
      {
        template_id: 'regulatory_action',
        name: 'Regulatory Action Tracking',
        description: 'Center the investigation on policy, regulatory filings, and formal status changes.',
        inquiry_class: 'SCRUTINY',
        template_status: 'ACTIVE',
        domain_filter_count: 2,
        requires_legal_review: false,
      },
    ],
    total: 4,
  }),
  fetchInvestigationTemplate: vi.fn().mockImplementation((id: string) => {
    if (id === 'corporate_due_diligence') {
      return Promise.resolve({
        template_id: 'corporate_due_diligence',
        name: 'Corporate Due Diligence',
        description: 'Bias toward registries, filings, legal coverage, and identity/provenance checks.',
        inquiry_class: 'INSPECTION',
        domain_filters: ['corporate_and_entity', 'court_and_legal', 'property_and_land'],
        default_sources: ['companies_house', 'opencorporates'],
        default_stop_condition: 'EVIDENCE_THRESHOLD',
        default_time_window_days: 90,
        requires_legal_review: false,
        min_corroboration_groups: 3,
        template_status: 'ACTIVE',
        is_seeded: true,
        created_at: '2026-03-08T00:00:00Z',
      });
    }
    if (id === 'regulatory_action') {
      return Promise.resolve({
        template_id: 'regulatory_action',
        name: 'Regulatory Action Tracking',
        description: 'Center the investigation on policy, regulatory filings, and formal status changes.',
        inquiry_class: 'SCRUTINY',
        domain_filters: ['corporate_and_entity', 'court_and_legal'],
        default_sources: [],
        default_stop_condition: 'SPONSOR_DEFINED',
        default_time_window_days: 180,
        requires_legal_review: false,
        min_corroboration_groups: 2,
        template_status: 'ACTIVE',
        is_seeded: true,
        created_at: '2026-03-08T00:00:00Z',
      });
    }
    return Promise.reject(new Error('Not found'));
  }),
}));

import { createInvestigation } from '../../../api/investigation';

const mockCreateInvestigation = vi.mocked(createInvestigation);

function renderWithProviders(ui: React.ReactElement, route = '/investigation/create') {
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

describe('CreateInvestigationWizard', () => {
  beforeEach(() => {
    mockCreateInvestigation.mockClear();
  });

  // Test 1: Wizard renders template list from API (mock)
  it('renders template list from API on step 1', async () => {
    renderWithProviders(<CreateInvestigationWizard />);

    // Step 1 should show API-loaded templates in the select
    await waitFor(() => {
      expect(screen.getByDisplayValue('Blank Investigation')).toBeInTheDocument();
    });
    expect(screen.getByRole('option', { name: 'Corporate Due Diligence' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Market Event Analysis' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Regulatory Action Tracking' })).toBeInTheDocument();
  });

  // Test 2: Template selection populates wizard state with correct defaults
  it('populates wizard state with template defaults on selection', async () => {
    renderWithProviders(<CreateInvestigationWizard />);

    // Select corporate_due_diligence on step 1
    await waitFor(() => {
      expect(screen.getByDisplayValue('Blank Investigation')).toBeInTheDocument();
    });
    fireEvent.change(screen.getByRole('combobox'), {
      target: { value: 'corporate_due_diligence' },
    });
    await waitFor(() => {
      fireEvent.click(screen.getByText('Next'));
    });

    // Step 2 is inquiry question; provide the required question and advance
    const textarea = screen.getByPlaceholderText(/What are you investigating/);
    fireEvent.change(textarea, { target: { value: 'Test inquiry' } });
    fireEvent.click(screen.getByText('Next'));

    // The domain filter step should show 3 pre-selected filters from the template
    await waitFor(() => {
      expect(screen.getByText('3 of 9 categories selected')).toBeInTheDocument();
    });
  });

  // Test 3: Signal-origin URL params prefill correct template from backend list
  it('prefills correct template from signal-origin URL params', async () => {
    renderWithProviders(
      <CreateInvestigationWizard />,
      '/investigation/create?signal_category=regulatory&signal_class=regulatory_clearance&theatre_id=TH_123',
    );

    // Should have pre-selected regulatory_action template in the dropdown
    await waitFor(() => {
      expect(screen.getByDisplayValue('Regulatory Action Tracking')).toBeInTheDocument();
    });
  });

  // Test 4: Domain filter IDs in create payload match backend enum values
  it('sends backend-aligned domain filter IDs and template_id in create payload', async () => {
    renderWithProviders(<CreateInvestigationWizard />);

    // Step 1 — wait for templates, stay on blank (default), advance
    await waitFor(() => {
      expect(screen.getByDisplayValue('Blank Investigation')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText('Next'));

    // Step 2 — inquiry question
    const textarea = screen.getByPlaceholderText(/What are you investigating/);
    fireEvent.change(textarea, { target: { value: 'Domain filter test' } });
    fireEvent.click(screen.getByText('Next'));

    // Step 3 — select domain filters using backend enum labels
    fireEvent.click(screen.getByText('Corporate & Entity'));
    fireEvent.click(screen.getByText('Court & Legal'));
    fireEvent.click(screen.getByText('Next'));

    // Step 4 — stop condition (advance to review)
    fireEvent.click(screen.getByText('Next'));

    // Step 5 — review, commit
    fireEvent.click(screen.getByText('Commit Investigation'));

    await waitFor(() => {
      expect(mockCreateInvestigation).toHaveBeenCalled();
      const callArgs = mockCreateInvestigation.mock.calls[0][0];
      expect(callArgs.domain_filters).toEqual(['corporate_and_entity', 'court_and_legal']);
      expect(callArgs.template_id).toBe('blank');
    });
  });

  // Test 5: Inquiry class options match backend enum (5 values)
  it('shows all 5 backend inquiry class options', () => {
    renderWithProviders(<CreateInvestigationWizard />);

    fireEvent.click(screen.getByText('Next'));

    expect(screen.getByText('Investigative')).toBeInTheDocument();
    expect(screen.getByText('Inspection')).toBeInTheDocument();
    expect(screen.getByText('Scrutiny')).toBeInTheDocument();
    expect(screen.getByText('Survey')).toBeInTheDocument();
    expect(screen.getByText('Counterfactual')).toBeInTheDocument();
  });
});
