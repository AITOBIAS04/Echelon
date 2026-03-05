import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { InvestigationCertificateView } from '../InvestigationCertificateView';
import type { InvestigationCertificate } from '../../../types/investigation';

const mockCertificate: InvestigationCertificate = {
  certificate_id: 'CERT-abc123',
  theatre_id: 'TH_TEST',
  construct_id: 'CON_TEST',
  inquiry_class: 'INVESTIGATIVE',
  stop_condition: 'OUTCOME_RESOLUTION',
  stop_config: {},
  investigation_started_at: '2026-03-01T10:00:00Z',
  investigation_completed_at: '2026-03-01T14:00:00Z',
  evidence_item_count: 5,
  evidence_redaction_count: 1,
  evidence_envelope_hash: 'envhash1234567890abcdef',
  provenance_summary: { PRIMARY: 3, SECONDARY: 2 },
  claim_count: 3,
  claim_status_summary: { supported: 2, contradicted: 1 },
  claim_graph_root_hash: 'roothash1234567890abcdef',
  counter_signals_checked: 11,
  counter_signals_gaps: 2,
  counter_signals_material: 1,
  counter_signal_detail: [],
  drift_event_count: 0,
  has_material_drift: false,
  drift_events: [],
  routing_decision: 'ALLOWED',
  routing_reason: 'No material concerns',
  certificate_hash: 'certhashfullvalue',
  anchoring_status: 'pending',
  anchoring_tx_hash: null,
  issued_at: '2026-03-01T14:00:00Z',
  methodology_version: '1.0.0',
  toolset_version: '0.1.0',
};

describe('InvestigationCertificateView', () => {
  it('renders all field groups', () => {
    render(<InvestigationCertificateView certificate={mockCertificate} />);

    // Section headers
    expect(screen.getByText('Certificate Identity')).toBeInTheDocument();
    expect(screen.getByText('Stop Condition')).toBeInTheDocument();
    expect(screen.getByText('Investigation Timeline')).toBeInTheDocument();
    expect(screen.getByText('Evidence Envelope')).toBeInTheDocument();
    expect(screen.getByText('Claim Graph')).toBeInTheDocument();
    expect(screen.getByText('Counter-Signals')).toBeInTheDocument();
    expect(screen.getByText('Drift Assessment')).toBeInTheDocument();
    expect(screen.getByText('Routing Decision')).toBeInTheDocument();
    expect(screen.getByText('Anchoring')).toBeInTheDocument();
    expect(screen.getByText('Certificate Hash')).toBeInTheDocument();
  });

  it('displays routing hint badge with correct colour for ALLOWED', () => {
    render(<InvestigationCertificateView certificate={mockCertificate} />);

    const badge = screen.getByText('ALLOWED');
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain('emerald');
  });

  it('displays REVIEW_REQUIRED routing with amber colour', () => {
    const reviewCert = { ...mockCertificate, routing_decision: 'REVIEW_REQUIRED' as const };
    render(<InvestigationCertificateView certificate={reviewCert} />);

    const badge = screen.getByText('REVIEW_REQUIRED');
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain('amber');
  });

  it('displays anchoring status badge', () => {
    render(<InvestigationCertificateView certificate={mockCertificate} />);

    const badge = screen.getByText('pending');
    expect(badge).toBeInTheDocument();
  });

  it('shows certificate identity fields', () => {
    render(<InvestigationCertificateView certificate={mockCertificate} />);

    expect(screen.getByText('CERT-abc123')).toBeInTheDocument();
    expect(screen.getByText('TH_TEST')).toBeInTheDocument();
    expect(screen.getByText('CON_TEST')).toBeInTheDocument();
    expect(screen.getByText('INVESTIGATIVE')).toBeInTheDocument();
  });

  it('shows evidence counts', () => {
    render(<InvestigationCertificateView certificate={mockCertificate} />);

    // Evidence item count of 5 appears in the Evidence Envelope section
    expect(screen.getAllByText('5').length).toBeGreaterThanOrEqual(1);
    // Redaction count and other "1" values exist (counter_signals_material, etc.)
    expect(screen.getAllByText('1').length).toBeGreaterThanOrEqual(1);
  });
});
