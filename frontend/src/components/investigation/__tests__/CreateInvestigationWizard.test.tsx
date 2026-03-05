import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { CreateInvestigationWizard } from '../CreateInvestigationWizard';

vi.mock('../../../api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

vi.mock('../../../api/investigation', () => ({
  createInvestigation: vi.fn(),
  fetchInvestigations: vi.fn().mockResolvedValue({ investigations: [], total: 0 }),
}));

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
    vi.clearAllMocks();
  });

  it('renders step 1 with inquiry question input', () => {
    renderWithProviders(<CreateInvestigationWizard />);

    expect(screen.getByText('Step 1: Inquiry Question')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/What are you investigating/)).toBeInTheDocument();
    expect(screen.getByText('Investigative')).toBeInTheDocument();
    expect(screen.getByText('Monitoring')).toBeInTheDocument();
    expect(screen.getByText('Verification')).toBeInTheDocument();
  });

  it('navigates forward and backward through steps', () => {
    renderWithProviders(<CreateInvestigationWizard />);

    // Step 1: fill inquiry question to enable Next
    const textarea = screen.getByPlaceholderText(/What are you investigating/);
    fireEvent.change(textarea, { target: { value: 'Test inquiry' } });

    // Go to step 2
    fireEvent.click(screen.getByText('Next'));
    expect(screen.getByText('Step 2: Template')).toBeInTheDocument();

    // Go back
    fireEvent.click(screen.getByText('Back'));
    expect(screen.getByText('Step 1: Inquiry Question')).toBeInTheDocument();
  });

  it('shows cancel button on step 1', () => {
    const onCancel = vi.fn();
    renderWithProviders(<CreateInvestigationWizard onCancel={onCancel} />);

    fireEvent.click(screen.getByText('Cancel'));
    expect(onCancel).toHaveBeenCalled();
  });

  it('shows immutability warning on review step', () => {
    renderWithProviders(<CreateInvestigationWizard />);

    // Navigate to step 5 (review)
    const textarea = screen.getByPlaceholderText(/What are you investigating/);
    fireEvent.change(textarea, { target: { value: 'Test inquiry' } });
    fireEvent.click(screen.getByText('Next')); // → step 2

    fireEvent.click(screen.getByText('Next')); // → step 3

    // Select a domain filter
    fireEvent.click(screen.getByText('Financial Filings'));
    fireEvent.click(screen.getByText('Next')); // → step 4

    fireEvent.click(screen.getByText('Next')); // → step 5

    expect(screen.getByText('Immutability Warning')).toBeInTheDocument();
    expect(screen.getByText(/Once committed, the investigation parameters cannot be changed/)).toBeInTheDocument();
    expect(screen.getByText('Commit Investigation')).toBeInTheDocument();
  });

  it('shows domain filter selector on step 3 with 9 categories', () => {
    renderWithProviders(<CreateInvestigationWizard />);

    // Navigate to step 3
    const textarea = screen.getByPlaceholderText(/What are you investigating/);
    fireEvent.change(textarea, { target: { value: 'Test inquiry' } });
    fireEvent.click(screen.getByText('Next')); // → step 2
    fireEvent.click(screen.getByText('Next')); // → step 3

    expect(screen.getByText('Step 3: Domain Filters')).toBeInTheDocument();
    expect(screen.getByText('Financial Filings')).toBeInTheDocument();
    expect(screen.getByText('Regulatory')).toBeInTheDocument();
    expect(screen.getByText('Corporate Registry')).toBeInTheDocument();
    expect(screen.getByText('Litigation')).toBeInTheDocument();
    expect(screen.getByText('Media & News')).toBeInTheDocument();
    expect(screen.getByText('Social Sentiment')).toBeInTheDocument();
    expect(screen.getByText('Supply Chain')).toBeInTheDocument();
    expect(screen.getByText('Geopolitical')).toBeInTheDocument();
    expect(screen.getByText('Technical')).toBeInTheDocument();
    expect(screen.getByText('0 of 9 categories selected')).toBeInTheDocument();
  });

  it('shows stop condition configurator on step 4 with 3 types', () => {
    renderWithProviders(<CreateInvestigationWizard />);

    // Navigate to step 4
    const textarea = screen.getByPlaceholderText(/What are you investigating/);
    fireEvent.change(textarea, { target: { value: 'Test inquiry' } });
    fireEvent.click(screen.getByText('Next')); // → step 2
    fireEvent.click(screen.getByText('Next')); // → step 3
    fireEvent.click(screen.getByText('Financial Filings'));
    fireEvent.click(screen.getByText('Next')); // → step 4

    expect(screen.getByText('Step 4: Stop Condition')).toBeInTheDocument();
    expect(screen.getByText('Outcome Resolution')).toBeInTheDocument();
    expect(screen.getByText('Evidence Threshold')).toBeInTheDocument();
    expect(screen.getByText('Sponsor Defined')).toBeInTheDocument();
  });
});
