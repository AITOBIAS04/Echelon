import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
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
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>
        {ui}
      </QueryClientProvider>
    </MemoryRouter>,
  );
}

describe('BlackboxPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders platform analytics from live aggregates', async () => {
    mockGet.mockImplementation((url: string) => {
      if (url.includes('/api/v1/analytics/platform')) {
        return Promise.resolve({
          data: {
            updated_at: new Date().toISOString(),
            range: '30d',
            bucket_size: 'day',
            current: {
              active_theatres: 12,
              completed_theatres: 4,
              active_investigations: 5,
              ready_investigations: 2,
              issued_certificates: 9,
              active_paradoxes: 3,
              active_signals: 19,
              critical_signals: 6,
              convergence_cells: 8,
            },
            timeseries: {
              theatres_created: [{ timestamp: new Date().toISOString(), value: 2 }],
              investigations_created: [{ timestamp: new Date().toISOString(), value: 1 }],
              certificates_issued: [{ timestamp: new Date().toISOString(), value: 1 }],
              deployments_created: [{ timestamp: new Date().toISOString(), value: 0 }],
              active_paradoxes: [{ timestamp: new Date().toISOString(), value: 3 }],
            },
            comparisons: {
              theatres_created: { current_period: 2, previous_period: 1, delta: 1, change_pct: 100 },
              investigations_created: { current_period: 1, previous_period: 2, delta: -1, change_pct: -50 },
              certificates_issued: { current_period: 1, previous_period: 0, delta: 1, change_pct: null },
              deployments_created: { current_period: 0, previous_period: 1, delta: -1, change_pct: -100 },
            },
            explanations: {
              theatres_created: [
                {
                  id: 'theatre-1',
                  kind: 'theatre',
                  timestamp: new Date().toISOString(),
                  title: 'Macro Inflation Pulse',
                  summary: 'Investigative theatre created.',
                  tone: 'info',
                  provenance: 'persisted_lifecycle',
                  theatre_id: 'theatre-1',
                },
              ],
              investigations_created: [],
              certificates_issued: [],
              deployments_created: [],
              deployment_lifecycle: [],
              certificate_ready: [],
              wing_flaps: [],
            },
          },
        } as any);
      }
      if (url.includes('/api/v1/analytics/breakdowns')) {
        return Promise.resolve({
          data: {
            updated_at: new Date().toISOString(),
            applied_filters: {},
            signal_categories: { finance_markets: 7, geopolitical_conflict: 5 },
            signal_sources: { worldmonitor: 9, companies_house: 3 },
            signal_severities: { critical: 2, high: 4, moderate: 6 },
            theatre_states: { ACTIVE: 12, COMPLETED: 4 },
            theatre_families: { macro: 4, election: 2 },
            theatre_inquiry_classes: { COUNTERFACTUAL: 6, INVESTIGATIVE: 4 },
            investigation_statuses: { ACTIVE: 5, CERTIFICATE_READY: 2 },
            investigation_classes: { INVESTIGATIVE: 5 },
            investigation_routing_decisions: { ALLOWED: 2, REVIEW_REQUIRED: 1 },
            theatre_routing_hints: { ALLOWED: 3 },
            theatre_gate_statuses: { PASSED: 3 },
            agent_archetypes: { SHARK: 4, SPY: 3 },
          },
        } as any);
      }
      if (url.includes('/api/v1/analytics/risk-trend')) {
        return Promise.resolve({
          data: {
            updated_at: new Date().toISOString(),
            range: '30d',
            bucket_size: 'day',
            timeseries: {
              active_paradoxes: [{ timestamp: new Date().toISOString(), value: 3 }],
              material_drift_events: [{ timestamp: new Date().toISOString(), value: 1 }],
              review_required_certificates: [{ timestamp: new Date().toISOString(), value: 1 }],
              readiness_met: [{ timestamp: new Date().toISOString(), value: 2 }],
            },
            comparisons: {
              active_paradoxes: { current_period: 3, previous_period: 2, delta: 1, change_pct: 50 },
              material_drift_events: { current_period: 1, previous_period: 0, delta: 1, change_pct: null },
              readiness_met: { current_period: 2, previous_period: 1, delta: 1, change_pct: 100 },
              review_required_certificates: { current_period: 1, previous_period: 1, delta: 0, change_pct: 0 },
            },
            explanations: {
              active_paradoxes: [
                {
                  id: 'paradox-1',
                  kind: 'paradox',
                  timestamp: new Date().toISOString(),
                  title: 'Energy Corridor',
                  summary: 'Critical paradox active.',
                  tone: 'danger',
                  provenance: 'persisted_operational_context',
                  timeline_id: 'timeline-1',
                },
              ],
              material_drift_events: [],
              readiness_met: [],
              review_required_certificates: [],
              routing_transitions: [],
            },
          },
        } as any);
      }
      if (url.includes('/api/v1/analytics/portfolio')) {
        return Promise.resolve({
          data: {
            updated_at: new Date().toISOString(),
            range: '30d',
            history_status: 'current_snapshot_only',
            current: {
              total_notional: 0,
              total_unrealised_pnl: 0,
              position_count: 0,
              winning_positions: 0,
              losing_positions: 0,
              at_risk_positions: 0,
            },
            top_positions: [],
            timeseries: [],
          },
        } as any);
      }
      return Promise.resolve({ data: {} } as any);
    });

    renderWithProviders(<BlackboxPage />);

    expect(await screen.findByText('Analytics')).toBeInTheDocument();
    expect(await screen.findByText('Active Theatres')).toBeInTheDocument();
    expect(await screen.findByText('Operational distribution')).toBeInTheDocument();
    expect(await screen.findByText('Trend window')).toBeInTheDocument();
    expect(await screen.findByText('Lifecycle volume')).toBeInTheDocument();
    expect(await screen.findByText('Event-linked explanations')).toBeInTheDocument();
  });

  it('shows sparse portfolio state when positions and risk feeds are absent', async () => {
    mockGet.mockImplementation((url: string) => {
      if (url.includes('/api/v1/analytics/platform')) {
        return Promise.resolve({
          data: {
            updated_at: new Date().toISOString(),
            range: '30d',
            bucket_size: 'day',
            current: {
              active_theatres: 0,
              completed_theatres: 0,
              active_investigations: 0,
              ready_investigations: 0,
              issued_certificates: 0,
              active_paradoxes: 0,
              active_signals: 0,
              critical_signals: 0,
              convergence_cells: 0,
            },
            timeseries: {},
            comparisons: {},
            explanations: {
              theatres_created: [],
              investigations_created: [],
              certificates_issued: [],
              deployments_created: [],
              deployment_lifecycle: [],
              certificate_ready: [],
              wing_flaps: [],
            },
          },
        } as any);
      }
      if (url.includes('/api/v1/analytics/breakdowns')) {
        return Promise.resolve({
          data: {
            updated_at: new Date().toISOString(),
            applied_filters: {},
            signal_categories: {},
            signal_sources: {},
            signal_severities: {},
            theatre_states: {},
            theatre_families: {},
            theatre_inquiry_classes: {},
            investigation_statuses: {},
            investigation_classes: {},
            investigation_routing_decisions: {},
            theatre_routing_hints: {},
            theatre_gate_statuses: {},
            agent_archetypes: {},
          },
        } as any);
      }
      if (url.includes('/api/v1/analytics/risk-trend')) {
        return Promise.resolve({
          data: {
            updated_at: new Date().toISOString(),
            range: '30d',
            bucket_size: 'day',
            timeseries: {},
            comparisons: {},
            explanations: {
              active_paradoxes: [],
              material_drift_events: [],
              readiness_met: [],
              review_required_certificates: [],
              routing_transitions: [],
            },
          },
        } as any);
      }
      if (url.includes('/api/v1/analytics/portfolio')) {
        return Promise.resolve({
          data: {
            updated_at: new Date().toISOString(),
            range: '30d',
            history_status: 'current_snapshot_only',
            current: {
              total_notional: 0,
              total_unrealised_pnl: 0,
              position_count: 0,
              winning_positions: 0,
              losing_positions: 0,
              at_risk_positions: 0,
            },
            top_positions: [],
            timeseries: [],
          },
        } as any);
      }
      return Promise.resolve({ data: {} } as any);
    });

    renderWithProviders(<BlackboxPage />);

    fireEvent.click(await screen.findByRole('button', { name: 'Portfolio' }));

    expect(await screen.findByText('No portfolio analytics yet')).toBeInTheDocument();
    expect(screen.getByText(/truthful current snapshot only/i)).toBeInTheDocument();
  });
});
