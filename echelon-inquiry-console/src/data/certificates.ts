import type { CalibrationCertificate } from '../types/certificate';
import { TEMPLATES, COMMITMENT_TARGETS } from './templates';

function buildCertificate(templateId: string): CalibrationCertificate {
  const template = TEMPLATES.find((t) => t.template_id === templateId)!;
  const target = COMMITMENT_TARGETS[templateId];

  const criteriaScores: Record<string, number> = {};
  for (const cid of template.criteria_ids) {
    criteriaScores[cid] = template.existing_composite;
  }

  return {
    certificate_id: `cert_${templateId.toLowerCase()}_2026_02_28_001`,
    template_id: templateId,
    inquiry_class: template.inquiry_class,
    execution_path: template.execution_path,
    construct_id: template.construct_id,
    construct_version: template.construct_version,
    scorer_version: template.scorer_version,
    issued_at: '2026-02-28T14:32:17Z',
    expires_at: '2026-05-29T14:32:17Z',
    replay_count: template.fixture_count,
    criteria_ids: template.criteria_ids,
    criteria_scores: criteriaScores,
    composite_score: template.existing_composite,
    verification_tier: 'UNVERIFIED',
    dataset_hash: target.dataset_hashes.ground_truth,
    evidence_bundle_hash:
      '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    commitment_hash: template.commitment_hash,
    methodology: target.version_pins.methodology,
  };
}

// Pre-built ESCROW certificate with exact per-criteria scores from spec
const escrowCert: CalibrationCertificate = {
  certificate_id: 'cert_escrow_milestone_release_v1_2026_02_28_001',
  template_id: 'ESCROW_MILESTONE_RELEASE_V1',
  inquiry_class: 'INSPECTION',
  execution_path: 'PRODUCT',
  construct_id: 'product_observer_v1',
  construct_version: '0.3.2',
  scorer_version: 'escrow_milestone_scorer@1.0.0',
  issued_at: '2026-02-28T14:32:17Z',
  expires_at: '2026-05-29T14:32:17Z',
  replay_count: 11,
  criteria_ids: [
    'amount_correct',
    'attestation_chain_complete',
    'evidence_present',
    'signer_policy_satisfied',
    'timing_valid',
  ],
  criteria_scores: {
    evidence_present: 1.0,
    signer_policy_satisfied: 0.818,
    timing_valid: 0.891,
    amount_correct: 0.909,
    attestation_chain_complete: 0.818,
  },
  composite_score: 0.9091,
  verification_tier: 'UNVERIFIED',
  dataset_hash:
    'dcfdbeb08528d2b6ae8dab036e9c13bb4f7ac272e1d9f5a3b8c0d2e4f6a8b0c2',
  evidence_bundle_hash:
    '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
  commitment_hash:
    '7a3f8c1de5b7a9f0c2d4e6f8a1b3c5d7e9f0a2b4c6d8e0f1a3b5c7d9e4b209f1',
  methodology: 'deterministic_state_replay',
};

// Pre-built GLOBAL_CONFLICT certificate
const conflictCert: CalibrationCertificate = {
  certificate_id: 'cert_global_conflict_v1_2026_02_28_001',
  template_id: 'GLOBAL_CONFLICT_V1',
  inquiry_class: 'COUNTERFACTUAL',
  execution_path: 'MARKET',
  construct_id: 'geopolitical_analyst_v1',
  construct_version: '0.1.0',
  scorer_version: 'conflict_scorer@0.1.0',
  issued_at: '2026-02-28T14:32:17Z',
  expires_at: '2026-05-29T14:32:17Z',
  replay_count: 6,
  criteria_ids: [
    'scenario_parameters_committed',
    'lmsr_liquidity_bounded',
    'resolution_source_pinned',
    'settlement_deterministic',
  ],
  criteria_scores: {
    scenario_parameters_committed: 1.0,
    lmsr_liquidity_bounded: 0.75,
    resolution_source_pinned: 1.0,
    settlement_deterministic: 0.75,
  },
  composite_score: 0.875,
  verification_tier: 'UNVERIFIED',
  dataset_hash:
    'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2',
  evidence_bundle_hash:
    'a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3',
  commitment_hash:
    'b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8',
  methodology: 'lmsr_market_resolution',
};

export const CERTIFICATES: Record<string, CalibrationCertificate> = {
  ESCROW_MILESTONE_RELEASE_V1: escrowCert,
  GLOBAL_CONFLICT_V1: conflictCert,
  OSINT_COMPOSED_ORACLE_V1: buildCertificate('OSINT_COMPOSED_ORACLE_V1'),
  DISTRIBUTION_WATERFALL_V1: buildCertificate('DISTRIBUTION_WATERFALL_V1'),
  LEDGER_RECONCILIATION_V1: buildCertificate('LEDGER_RECONCILIATION_V1'),
  PRODUCT_OBSERVER_V1: buildCertificate('PRODUCT_OBSERVER_V1'),
  QUANT_MARKET_HYGIENE_V1: buildCertificate('QUANT_MARKET_HYGIENE_V1'),
  QUANT_MARKET_PERTURBATION_HARNESS_V1: buildCertificate(
    'QUANT_MARKET_PERTURBATION_HARNESS_V1'
  ),
};
