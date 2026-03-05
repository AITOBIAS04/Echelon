import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ClaimGraphPanel } from '../ClaimGraphPanel';
import type { ClaimGraphSummary } from '../../../types/investigation';

const mockClaims: ClaimGraphSummary = {
  claims: [
    {
      claim_id: 'CLM001',
      claim_text: 'Entity X filed for insolvency',
      claim_type: 'fact',
      evidence_refs: ['EV001', 'EV002'],
      counter_signals: [],
      status: 'supported',
      confidence: 0.85,
      independence_groups: ['group_a'],
    },
    {
      claim_id: 'CLM002',
      claim_text: 'Filing caused market disruption',
      claim_type: 'causal',
      evidence_refs: ['EV003'],
      counter_signals: ['CS001'],
      status: 'partially_supported',
      confidence: 0.45,
      independence_groups: [],
    },
    {
      claim_id: 'CLM003',
      claim_text: 'Director Y orchestrated the filing',
      claim_type: 'attribution',
      evidence_refs: [],
      counter_signals: [],
      status: 'contradicted',
      confidence: 0.1,
      independence_groups: [],
    },
  ],
  root_hash: 'roothashabc123def456',
  status_summary: { supported: 1, partially_supported: 1, contradicted: 1 },
};

describe('ClaimGraphPanel', () => {
  it('renders all claim nodes', () => {
    render(<ClaimGraphPanel claims={mockClaims} />);

    expect(screen.getByText('CLM001')).toBeInTheDocument();
    expect(screen.getByText('CLM002')).toBeInTheDocument();
    expect(screen.getByText('CLM003')).toBeInTheDocument();
  });

  it('displays status badges matching status values', () => {
    render(<ClaimGraphPanel claims={mockClaims} />);

    // Status badges for each claim
    expect(screen.getAllByText('supported')).toHaveLength(2); // badge + summary
    expect(screen.getAllByText('partially_supported')).toHaveLength(2);
    expect(screen.getAllByText('contradicted')).toHaveLength(2);
  });

  it('shows claim type badges', () => {
    render(<ClaimGraphPanel claims={mockClaims} />);

    expect(screen.getByText('fact')).toBeInTheDocument();
    expect(screen.getByText('causal')).toBeInTheDocument();
    expect(screen.getByText('attribution')).toBeInTheDocument();
  });

  it('displays root hash', () => {
    render(<ClaimGraphPanel claims={mockClaims} />);

    expect(screen.getByText('roothashabc123de...')).toBeInTheDocument();
  });

  it('shows empty state when no claims', () => {
    const empty: ClaimGraphSummary = {
      claims: [],
      root_hash: '',
      status_summary: {},
    };
    render(<ClaimGraphPanel claims={empty} />);

    expect(screen.getByText(/No claims registered/)).toBeInTheDocument();
  });
});
