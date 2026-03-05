import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { InvestigationProgressBar } from '../InvestigationProgressBar';
import type { InvestigationDetail } from '../../../types/investigation';

function makeInvestigation(overrides: Partial<InvestigationDetail> = {}): InvestigationDetail {
  return {
    id: 'INV-test',
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
        { evidence_id: 'EV001', content_hash: 'abc', provenance_class: 'public_primary', submitted_at: '2026-03-01T11:00:00Z', content_type: 'text/plain', source_description: 'Test', references: [] },
      ],
      redactions: [],
      provenance_summary: { public_primary: 1 },
      envelope_hash: 'envhash',
    },
    claims: {
      claims: [
        { claim_id: 'CLM001', claim_text: 'Test claim', claim_type: 'fact', evidence_refs: ['EV001'], counter_signals: [], status: 'supported', confidence: 0.8, independence_groups: [] },
        { claim_id: 'CLM002', claim_text: 'Test claim 2', claim_type: 'causal', evidence_refs: [], counter_signals: [], status: 'unconfirmed', confidence: 0.3, independence_groups: [] },
      ],
      root_hash: 'roothash',
      status_summary: { supported: 1, unconfirmed: 1 },
    },
    counter_signals: {
      signals: [
        { counter_signal_id: 'CS001', signal_class: 'market_contradiction', detected_at: '2026-03-01T11:30:00Z', evidence_ref: 'EV001', material: true, resolution_impact: 'high', detection_method: 'automated' },
      ],
      summary: { market_contradiction: 1 },
    },
    drift: {
      events: [],
      has_material_drift: false,
    },
    ...overrides,
  };
}

describe('InvestigationProgressBar', () => {
  it('shows OUTCOME_RESOLUTION progress', () => {
    render(<InvestigationProgressBar investigation={makeInvestigation()} />);

    expect(screen.getByText('OUTCOME_RESOLUTION')).toBeInTheDocument();
    expect(screen.getByText('Stop Condition Progress')).toBeInTheDocument();
  });

  it('shows EVIDENCE_THRESHOLD progress with supported claims bar', () => {
    render(
      <InvestigationProgressBar
        investigation={makeInvestigation({
          stop_condition: 'EVIDENCE_THRESHOLD',
          stop_config: { min_supported_claims: 5, min_corroboration_score: 0.7 },
        })}
      />,
    );

    expect(screen.getByText('EVIDENCE_THRESHOLD')).toBeInTheDocument();
    expect(screen.getByText('Supported Claims')).toBeInTheDocument();
    expect(screen.getByText('1/5')).toBeInTheDocument(); // 1 supported out of 5 required
  });

  it('shows SPONSOR_DEFINED progress with milestone', () => {
    const futureDate = new Date(Date.now() + 86_400_000 * 3).toISOString(); // 3 days ahead
    render(
      <InvestigationProgressBar
        investigation={makeInvestigation({
          stop_condition: 'SPONSOR_DEFINED',
          stop_config: { milestone_timestamp: futureDate },
        })}
      />,
    );

    expect(screen.getByText('SPONSOR_DEFINED')).toBeInTheDocument();
    expect(screen.getByText(/remaining/)).toBeInTheDocument();
  });

  it('shows claim status distribution', () => {
    render(<InvestigationProgressBar investigation={makeInvestigation()} />);

    expect(screen.getByText('Claim Status Distribution')).toBeInTheDocument();
    expect(screen.getByText(/supported \(1\)/)).toBeInTheDocument();
    expect(screen.getByText(/unconfirmed \(1\)/)).toBeInTheDocument();
  });

  it('shows material counter-signal warning', () => {
    render(<InvestigationProgressBar investigation={makeInvestigation()} />);

    expect(
      screen.getByText(/1 material counter-signal detected/),
    ).toBeInTheDocument();
  });
});
