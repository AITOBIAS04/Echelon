import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DeltaBriefPanel } from '../DeltaBriefPanel';

const mockBrief = {
  brief_id: 'DB001',
  domain_filters: ['corporate_and_entity', 'finance_and_markets'],
  generated_at: '2026-03-01T12:00:00Z',
  source_queries: [
    {
      source_id: 'SRC001',
      source_group: 'official_gov',
      query: 'Entity X',
      result_count: 3,
      access_tier: 'A',
      skipped: false,
      skip_reason: null,
    },
    {
      source_id: 'SRC002',
      source_group: 'satellite_imagery',
      query: 'Entity X',
      result_count: 0,
      access_tier: 'B',
      skipped: true,
      skip_reason: 'access_tier_b_not_authorized',
    },
  ],
  anomalies: [
    {
      anomaly_id: 'ANM001',
      source_id: 'SRC001',
      description: 'Unusual filing pattern detected',
      severity: 0.75,
      detected_at: '2026-03-01T12:05:00Z',
    },
  ],
  content_hash: 'briefhashabc123def456',
};

describe('DeltaBriefPanel', () => {
  it('renders domain filter chips', () => {
    render(<DeltaBriefPanel brief={mockBrief} />);

    expect(screen.getByText('corporate_and_entity')).toBeInTheDocument();
    expect(screen.getByText('finance_and_markets')).toBeInTheDocument();
  });

  it('displays access tier badges', () => {
    render(<DeltaBriefPanel brief={mockBrief} />);

    expect(screen.getByText('Tier A')).toBeInTheDocument();
    expect(screen.getByText('Tier B')).toBeInTheDocument();
  });

  it('shows skipped indicator for restricted sources', () => {
    render(<DeltaBriefPanel brief={mockBrief} />);

    expect(screen.getByText('SKIPPED')).toBeInTheDocument();
    expect(screen.getByText('access_tier_b_not_authorized')).toBeInTheDocument();
  });

  it('renders anomaly cards', () => {
    render(<DeltaBriefPanel brief={mockBrief} />);

    expect(screen.getByText('ANM001')).toBeInTheDocument();
    expect(screen.getByText('Unusual filing pattern detected')).toBeInTheDocument();
    expect(screen.getByText('75% severity')).toBeInTheDocument();
  });

  it('shows empty state when no brief', () => {
    render(<DeltaBriefPanel brief={null} />);

    expect(screen.getByText(/No scan results available/)).toBeInTheDocument();
  });
});
