import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { EvidenceEnvelopePanel } from '../EvidenceEnvelopePanel';
import type { EvidenceEnvelopeManifest } from '../../../types/investigation';

const mockEvidence: EvidenceEnvelopeManifest = {
  items: [
    {
      evidence_id: 'EV001',
      content_hash: 'abc123def456789012345678901234567890',
      provenance_class: 'PRIMARY',
      submitted_at: '2026-03-01T12:00:00Z',
      content_type: 'text/plain',
      source_description: 'Test source',
      references: ['REF001'],
    },
    {
      evidence_id: 'EV002',
      content_hash: 'def456abc123789012345678901234567890',
      provenance_class: 'SECONDARY',
      submitted_at: '2026-03-01T13:00:00Z',
      content_type: 'application/json',
      source_description: 'Second source',
      references: [],
    },
  ],
  redactions: [
    {
      redaction_id: 'RED001',
      evidence_id: 'EV002',
      reason_class: 'pii_exposure',
      redacted_at: '2026-03-01T14:00:00Z',
    },
  ],
  provenance_summary: { PRIMARY: 1, SECONDARY: 1 },
  envelope_hash: 'envelope_hash_abc123',
};

describe('EvidenceEnvelopePanel', () => {
  it('renders evidence items with provenance badges', () => {
    render(<EvidenceEnvelopePanel evidence={mockEvidence} />);

    expect(screen.getByText('EV001')).toBeInTheDocument();
    expect(screen.getByText('EV002')).toBeInTheDocument();
    // PRIMARY appears twice: once in item badge, once in summary
    expect(screen.getAllByText('PRIMARY').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('SECONDARY').length).toBeGreaterThanOrEqual(1);
  });

  it('shows redaction indicator for redacted evidence', () => {
    render(<EvidenceEnvelopePanel evidence={mockEvidence} />);

    // EV002 is redacted
    expect(screen.getByText('REDACTED')).toBeInTheDocument();
  });

  it('displays envelope hash', () => {
    render(<EvidenceEnvelopePanel evidence={mockEvidence} />);

    expect(screen.getByText('envelope_hash_abc123')).toBeInTheDocument();
  });

  it('shows empty state when no items', () => {
    const empty: EvidenceEnvelopeManifest = {
      items: [],
      redactions: [],
      provenance_summary: {},
      envelope_hash: '',
    };
    render(<EvidenceEnvelopePanel evidence={empty} />);

    expect(screen.getByText(/No evidence items/)).toBeInTheDocument();
  });
});
