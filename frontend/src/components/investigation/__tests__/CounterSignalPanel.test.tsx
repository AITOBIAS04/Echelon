import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CounterSignalPanel } from '../CounterSignalPanel';
import type { CounterSignal } from '../../../types/investigation';

const mockSignals: CounterSignal[] = [
  {
    counter_signal_id: 'CS001',
    signal_class: 'filing_contradiction',
    detected_at: '2026-03-01T12:00:00Z',
    evidence_ref: 'EV001',
    material: true,
    resolution_impact: 'Weakens primary claim about insolvency timing',
    detection_method: 'human_submitted',
  },
  {
    counter_signal_id: 'CS002',
    signal_class: 'source_reliability_degradation',
    detected_at: '2026-03-01T13:00:00Z',
    evidence_ref: null,
    material: false,
    resolution_impact: 'Secondary source reliability questioned',
    detection_method: 'automated_scan',
  },
];

describe('CounterSignalPanel', () => {
  it('renders summary counts', () => {
    render(<CounterSignalPanel signals={mockSignals} summary={{ checked: 11, gaps: 2 }} />);

    // Total and material counts
    expect(screen.getByText('2')).toBeInTheDocument(); // total
    expect(screen.getByText('1')).toBeInTheDocument(); // material count
  });

  it('displays material flag on material signals', () => {
    render(<CounterSignalPanel signals={mockSignals} summary={{}} />);

    expect(screen.getByText('MATERIAL')).toBeInTheDocument();
    expect(screen.getByText('CS001')).toBeInTheDocument();
  });

  it('shows signal class badges', () => {
    render(<CounterSignalPanel signals={mockSignals} summary={{}} />);

    expect(screen.getByText('filing_contradiction')).toBeInTheDocument();
    expect(screen.getByText('source_reliability_degradation')).toBeInTheDocument();
  });

  it('shows empty state when no signals', () => {
    render(<CounterSignalPanel signals={[]} summary={{}} />);

    expect(screen.getByText(/No counter-signals detected/)).toBeInTheDocument();
  });
});
