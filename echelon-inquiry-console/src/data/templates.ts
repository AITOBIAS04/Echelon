import type { TheatreTemplate, CommitmentTarget } from '../types/inquiry';
import type { Episode, MarketPhase } from '../types/execution';

export const TEMPLATES: TheatreTemplate[] = [
  {
    template_id: 'GLOBAL_CONFLICT_V1',
    name: 'Global Conflict Escalation Scenario',
    inquiry_class: 'COUNTERFACTUAL',
    execution_path: 'MARKET',
    criteria_ids: [
      'scenario_parameters_committed',
      'lmsr_liquidity_bounded',
      'resolution_source_pinned',
      'settlement_deterministic',
    ],
    fixture_count: 6,
    pass_count: 4,
    fail_count: 2,
    existing_composite: 0.875,
    construct_id: 'geopolitical_analyst_v1',
    construct_version: '0.1.0',
    scorer_version: 'conflict_scorer@0.1.0',
    commitment_hash:
      'b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8',
  },
  {
    template_id: 'OSINT_COMPOSED_ORACLE_V1',
    name: 'OSINT Composed Oracle',
    inquiry_class: 'INVESTIGATIVE',
    execution_path: 'PRODUCT',
    criteria_ids: [
      'source_corroboration',
      'temporal_consistency',
      'entity_resolution',
      'confidence_calibration',
      'counter_signal_integration',
      'provenance_chain',
    ],
    fixture_count: 10,
    pass_count: 6,
    fail_count: 4,
    existing_composite: 0.8333,
    construct_id: 'osint_oracle_v1',
    construct_version: '0.4.1',
    scorer_version: 'osint_scorer@1.2.0',
    commitment_hash:
      'c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5',
  },
  {
    template_id: 'ESCROW_MILESTONE_RELEASE_V1',
    name: 'Escrow Milestone Release Verification',
    inquiry_class: 'INSPECTION',
    execution_path: 'PRODUCT',
    criteria_ids: [
      'amount_correct',
      'attestation_chain_complete',
      'evidence_present',
      'signer_policy_satisfied',
      'timing_valid',
    ],
    fixture_count: 11,
    pass_count: 6,
    fail_count: 5,
    existing_composite: 0.9091,
    construct_id: 'product_observer_v1',
    construct_version: '0.3.2',
    scorer_version: 'escrow_milestone_scorer@1.0.0',
    commitment_hash:
      '7a3f8c1de5b7a9f0c2d4e6f8a1b3c5d7e9f0a2b4c6d8e0f1a3b5c7d9e4b209f1',
  },
  {
    template_id: 'DISTRIBUTION_WATERFALL_V1',
    name: 'Distribution Waterfall Audit',
    inquiry_class: 'INSPECTION',
    execution_path: 'PRODUCT',
    criteria_ids: [
      'tranche_ordering',
      'amount_allocation',
      'priority_enforcement',
      'residual_calculation',
      'covenant_compliance',
    ],
    fixture_count: 10,
    pass_count: 10,
    fail_count: 0,
    existing_composite: 1.0,
    construct_id: 'waterfall_inspector_v1',
    construct_version: '0.2.0',
    scorer_version: 'waterfall_scorer@1.0.0',
    commitment_hash:
      'd5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6',
    template_tags: ['audit'],
  },
  {
    template_id: 'LEDGER_RECONCILIATION_V1',
    name: 'Ledger Reconciliation Audit',
    inquiry_class: 'INSPECTION',
    execution_path: 'PRODUCT',
    criteria_ids: [
      'balance_match',
      'transaction_completeness',
      'temporal_ordering',
      'cross_reference_integrity',
      'variance_threshold',
    ],
    fixture_count: 10,
    pass_count: 10,
    fail_count: 0,
    existing_composite: 1.0,
    construct_id: 'ledger_reconciler_v1',
    construct_version: '0.1.5',
    scorer_version: 'ledger_scorer@1.0.0',
    commitment_hash:
      'e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7',
    template_tags: ['audit'],
  },
  {
    template_id: 'PRODUCT_OBSERVER_V1',
    name: 'Product Observer Calibration',
    inquiry_class: 'SURVEY',
    execution_path: 'PRODUCT',
    criteria_ids: [
      'accuracy_baseline',
      'confidence_calibration',
      'response_latency',
      'format_compliance',
      'edge_case_handling',
    ],
    fixture_count: 1,
    pass_count: 1,
    fail_count: 0,
    existing_composite: 0.92,
    construct_id: 'product_observer_v1',
    construct_version: '0.3.2',
    scorer_version: 'observer_scorer@1.0.0',
    commitment_hash:
      'f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8',
  },
  {
    template_id: 'QUANT_MARKET_HYGIENE_V1',
    name: 'Quantitative Market Hygiene',
    inquiry_class: 'SCRUTINY',
    execution_path: 'PRODUCT',
    criteria_ids: [
      'bid_ask_spread',
      'volume_anomaly',
      'price_manipulation',
      'wash_trading',
      'front_running',
      'spoofing_detection',
      'circuit_breaker_compliance',
      'tick_size_adherence',
      'order_book_integrity',
      'latency_fairness',
      'market_maker_obligation',
      'position_limit_compliance',
      'reporting_timeliness',
      'settlement_accuracy',
      'counterparty_exposure',
      'margin_adequacy',
      'stress_test_pass',
      'liquidity_resilience',
      'regulatory_flag_response',
    ],
    fixture_count: 10,
    pass_count: 3,
    fail_count: 7,
    existing_composite: 0.4211,
    construct_id: 'market_hygiene_v1',
    construct_version: '0.5.0',
    scorer_version: 'hygiene_scorer@2.0.0',
    commitment_hash:
      'a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9',
    template_tags: ['adversarial'],
  },
  {
    template_id: 'QUANT_MARKET_PERTURBATION_HARNESS_V1',
    name: 'Quantitative Market Perturbation Harness',
    inquiry_class: 'SCRUTINY',
    execution_path: 'PRODUCT',
    criteria_ids: [
      'perturbation_detection',
      'recovery_speed',
      'cascade_prevention',
      'state_consistency',
      'rollback_integrity',
      'alert_accuracy',
      'impact_containment',
    ],
    fixture_count: 10,
    pass_count: 9,
    fail_count: 1,
    existing_composite: 0.9286,
    construct_id: 'perturbation_harness_v1',
    construct_version: '0.2.1',
    scorer_version: 'perturbation_scorer@1.0.0',
    commitment_hash:
      'b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0',
    template_tags: ['adversarial'],
  },
];

export const COMMITMENT_TARGETS: Record<string, CommitmentTarget> = {
  ESCROW_MILESTONE_RELEASE_V1: {
    dataset_hashes: {
      ground_truth: 'dcfdbeb08528d2b6ae8dab036e9c13bb4f7ac272e1d9f5a3b8c0d2e4f6a8b0c2',
      fixtures: '588e6f4b747e9cbd53450d7777540958aa3b1c2d4e5f6a7b8c9d0e1f2a3b4c5d',
    },
    template: {
      template_id: 'ESCROW_MILESTONE_RELEASE_V1',
      version: '1.0.0',
      criteria_ids: [
        'amount_correct',
        'attestation_chain_complete',
        'evidence_present',
        'signer_policy_satisfied',
        'timing_valid',
      ],
      scoring_thresholds: {
        amount_correct: 1.0,
        attestation_chain_complete: 1.0,
        evidence_present: 1.0,
        signer_policy_satisfied: 1.0,
        timing_valid: 1.0,
      },
    },
    version_pins: {
      construct: 'product_observer_v1@0.3.2',
      scorer: 'escrow_milestone_scorer@1.0.0',
      methodology: 'deterministic_state_replay',
    },
  },
  GLOBAL_CONFLICT_V1: {
    dataset_hashes: {
      ground_truth: 'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2',
      fixtures: 'b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3',
    },
    template: {
      template_id: 'GLOBAL_CONFLICT_V1',
      version: '1.0.0',
      criteria_ids: [
        'lmsr_liquidity_bounded',
        'resolution_source_pinned',
        'scenario_parameters_committed',
        'settlement_deterministic',
      ],
      scoring_thresholds: {
        lmsr_liquidity_bounded: 1.0,
        resolution_source_pinned: 1.0,
        scenario_parameters_committed: 1.0,
        settlement_deterministic: 1.0,
      },
    },
    version_pins: {
      construct: 'geopolitical_analyst_v1@0.1.0',
      scorer: 'conflict_scorer@0.1.0',
      methodology: 'lmsr_market_resolution',
    },
  },
  OSINT_COMPOSED_ORACLE_V1: {
    dataset_hashes: {
      ground_truth: 'c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4',
      fixtures: 'd4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5',
    },
    template: {
      template_id: 'OSINT_COMPOSED_ORACLE_V1',
      version: '1.0.0',
      criteria_ids: [
        'confidence_calibration',
        'counter_signal_integration',
        'entity_resolution',
        'provenance_chain',
        'source_corroboration',
        'temporal_consistency',
      ],
      scoring_thresholds: {
        confidence_calibration: 1.0,
        counter_signal_integration: 1.0,
        entity_resolution: 1.0,
        provenance_chain: 1.0,
        source_corroboration: 1.0,
        temporal_consistency: 1.0,
      },
    },
    version_pins: {
      construct: 'osint_oracle_v1@0.4.1',
      scorer: 'osint_scorer@1.2.0',
      methodology: 'deterministic_state_replay',
    },
  },
  DISTRIBUTION_WATERFALL_V1: {
    dataset_hashes: {
      ground_truth: 'e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6',
      fixtures: 'f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7',
    },
    template: {
      template_id: 'DISTRIBUTION_WATERFALL_V1',
      version: '1.0.0',
      criteria_ids: [
        'amount_allocation',
        'covenant_compliance',
        'priority_enforcement',
        'residual_calculation',
        'tranche_ordering',
      ],
      scoring_thresholds: {
        amount_allocation: 1.0,
        covenant_compliance: 1.0,
        priority_enforcement: 1.0,
        residual_calculation: 1.0,
        tranche_ordering: 1.0,
      },
    },
    version_pins: {
      construct: 'waterfall_inspector_v1@0.2.0',
      scorer: 'waterfall_scorer@1.0.0',
      methodology: 'deterministic_state_replay',
    },
  },
  LEDGER_RECONCILIATION_V1: {
    dataset_hashes: {
      ground_truth: 'a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8',
      fixtures: 'b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9',
    },
    template: {
      template_id: 'LEDGER_RECONCILIATION_V1',
      version: '1.0.0',
      criteria_ids: [
        'balance_match',
        'cross_reference_integrity',
        'temporal_ordering',
        'transaction_completeness',
        'variance_threshold',
      ],
      scoring_thresholds: {
        balance_match: 1.0,
        cross_reference_integrity: 1.0,
        temporal_ordering: 1.0,
        transaction_completeness: 1.0,
        variance_threshold: 1.0,
      },
    },
    version_pins: {
      construct: 'ledger_reconciler_v1@0.1.5',
      scorer: 'ledger_scorer@1.0.0',
      methodology: 'deterministic_state_replay',
    },
  },
  PRODUCT_OBSERVER_V1: {
    dataset_hashes: {
      ground_truth: 'c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0',
      fixtures: 'd0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1',
    },
    template: {
      template_id: 'PRODUCT_OBSERVER_V1',
      version: '1.0.0',
      criteria_ids: [
        'accuracy_baseline',
        'confidence_calibration',
        'edge_case_handling',
        'format_compliance',
        'response_latency',
      ],
      scoring_thresholds: {
        accuracy_baseline: 1.0,
        confidence_calibration: 1.0,
        edge_case_handling: 1.0,
        format_compliance: 1.0,
        response_latency: 1.0,
      },
    },
    version_pins: {
      construct: 'product_observer_v1@0.3.2',
      scorer: 'observer_scorer@1.0.0',
      methodology: 'deterministic_state_replay',
    },
  },
  QUANT_MARKET_HYGIENE_V1: {
    dataset_hashes: {
      ground_truth: 'e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2',
      fixtures: 'f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3',
    },
    template: {
      template_id: 'QUANT_MARKET_HYGIENE_V1',
      version: '1.0.0',
      criteria_ids: [
        'bid_ask_spread',
        'circuit_breaker_compliance',
        'counterparty_exposure',
        'front_running',
        'latency_fairness',
        'liquidity_resilience',
        'margin_adequacy',
        'market_maker_obligation',
        'order_book_integrity',
        'position_limit_compliance',
        'price_manipulation',
        'regulatory_flag_response',
        'reporting_timeliness',
        'settlement_accuracy',
        'spoofing_detection',
        'stress_test_pass',
        'tick_size_adherence',
        'volume_anomaly',
        'wash_trading',
      ],
      scoring_thresholds: {
        bid_ask_spread: 1.0,
        circuit_breaker_compliance: 1.0,
        counterparty_exposure: 1.0,
        front_running: 1.0,
        latency_fairness: 1.0,
        liquidity_resilience: 1.0,
        margin_adequacy: 1.0,
        market_maker_obligation: 1.0,
        order_book_integrity: 1.0,
        position_limit_compliance: 1.0,
        price_manipulation: 1.0,
        regulatory_flag_response: 1.0,
        reporting_timeliness: 1.0,
        settlement_accuracy: 1.0,
        spoofing_detection: 1.0,
        stress_test_pass: 1.0,
        tick_size_adherence: 1.0,
        volume_anomaly: 1.0,
        wash_trading: 1.0,
      },
    },
    version_pins: {
      construct: 'market_hygiene_v1@0.5.0',
      scorer: 'hygiene_scorer@2.0.0',
      methodology: 'deterministic_state_replay',
    },
  },
  QUANT_MARKET_PERTURBATION_HARNESS_V1: {
    dataset_hashes: {
      ground_truth: 'a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4',
      fixtures: 'b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5',
    },
    template: {
      template_id: 'QUANT_MARKET_PERTURBATION_HARNESS_V1',
      version: '1.0.0',
      criteria_ids: [
        'alert_accuracy',
        'cascade_prevention',
        'impact_containment',
        'perturbation_detection',
        'recovery_speed',
        'rollback_integrity',
        'state_consistency',
      ],
      scoring_thresholds: {
        alert_accuracy: 1.0,
        cascade_prevention: 1.0,
        impact_containment: 1.0,
        perturbation_detection: 1.0,
        recovery_speed: 1.0,
        rollback_integrity: 1.0,
        state_consistency: 1.0,
      },
    },
    version_pins: {
      construct: 'perturbation_harness_v1@0.2.1',
      scorer: 'perturbation_scorer@1.0.0',
      methodology: 'deterministic_state_replay',
    },
  },
};

export const ESCROW_EPISODES: Episode[] = [
  {
    episode_id: 'ep_001',
    ground_truth_summary:
      'Milestone 1: Foundations complete. QS attestation present. Amount: GBP 125,000. Within 30-day window.',
    expected_class: 'PASS',
    construct_output_class: 'PASS',
    criteria_scores: {
      evidence_present: 1.0,
      signer_policy_satisfied: 1.0,
      timing_valid: 1.0,
      amount_correct: 1.0,
      attestation_chain_complete: 1.0,
    },
    composite_score: 1.0,
    ground_truth_hash:
      '4f2a8c1d3e5b7a9f0c2d4e6f8a1b3c5d7e9f0a2b4c6d8e0f1a3b5c7d9e1f2a3b',
    invocation_hash:
      'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2',
  },
  {
    episode_id: 'ep_002',
    ground_truth_summary:
      'Milestone 2: Superstructure. QS attestation MISSING. Amount: GBP 200,000.',
    expected_class: 'FAIL',
    construct_output_class: 'FAIL',
    criteria_scores: {
      evidence_present: 0.0,
      signer_policy_satisfied: 0.0,
      timing_valid: 1.0,
      amount_correct: 1.0,
      attestation_chain_complete: 0.0,
    },
    composite_score: 0.4,
    ground_truth_hash:
      '8c1d3e5b7a9f0c2d4e6f8a1b3c5d7e9f0a2b4c6d8e0f1a3b5c7d9e1f2a3b4c5d',
    invocation_hash:
      'b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3',
  },
  {
    episode_id: 'ep_003',
    ground_truth_summary:
      'Milestone 3: Roofing complete. QS attestation present. Amount: GBP 310,000 (exceeds 25% threshold — dual attestor required).',
    expected_class: 'FAIL',
    construct_output_class: 'FAIL',
    criteria_scores: {
      evidence_present: 1.0,
      signer_policy_satisfied: 0.0,
      timing_valid: 1.0,
      amount_correct: 1.0,
      attestation_chain_complete: 0.0,
    },
    composite_score: 0.6,
    ground_truth_hash:
      '3e5b7a9f0c2d4e6f8a1b3c5d7e9f0a2b4c6d8e0f1a3b5c7d9e1f2a3b4c5d6e7f',
    invocation_hash:
      'c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4',
  },
  {
    episode_id: 'ep_004',
    ground_truth_summary:
      'Milestone 4: First fix (electrical, plumbing). QS attestation present. Amount: GBP 95,000. On time.',
    expected_class: 'PASS',
    construct_output_class: 'PASS',
    criteria_scores: {
      evidence_present: 1.0,
      signer_policy_satisfied: 1.0,
      timing_valid: 1.0,
      amount_correct: 1.0,
      attestation_chain_complete: 1.0,
    },
    composite_score: 1.0,
    ground_truth_hash:
      '5b7a9f0c2d4e6f8a1b3c5d7e9f0a2b4c6d8e0f1a3b5c7d9e1f2a3b4c5d6e7f8a',
    invocation_hash:
      'd4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5',
  },
  {
    episode_id: 'ep_005',
    ground_truth_summary:
      'Milestone 5: Second fix (plastering, insulation). QS attestation present. Amount: GBP 88,000. 3 days late.',
    expected_class: 'PASS',
    construct_output_class: 'PASS',
    criteria_scores: {
      evidence_present: 1.0,
      signer_policy_satisfied: 1.0,
      timing_valid: 0.8,
      amount_correct: 1.0,
      attestation_chain_complete: 1.0,
    },
    composite_score: 0.96,
    ground_truth_hash:
      '7a9f0c2d4e6f8a1b3c5d7e9f0a2b4c6d8e0f1a3b5c7d9e1f2a3b4c5d6e7f8a1b',
    invocation_hash:
      'e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6',
  },
  {
    episode_id: 'ep_006',
    ground_truth_summary:
      'Milestone 6: Kitchen and bathroom fit-out. QS attestation present. Amount: GBP 145,000. On time.',
    expected_class: 'PASS',
    construct_output_class: 'PASS',
    criteria_scores: {
      evidence_present: 1.0,
      signer_policy_satisfied: 1.0,
      timing_valid: 1.0,
      amount_correct: 1.0,
      attestation_chain_complete: 1.0,
    },
    composite_score: 1.0,
    ground_truth_hash:
      '9f0c2d4e6f8a1b3c5d7e9f0a2b4c6d8e0f1a3b5c7d9e1f2a3b4c5d6e7f8a1b3c',
    invocation_hash:
      'f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7',
  },
  {
    episode_id: 'ep_007',
    ground_truth_summary:
      'Milestone 7: External works. QS attestation present but expired (signed 45 days ago, 30-day validity window).',
    expected_class: 'FAIL',
    construct_output_class: 'FAIL',
    criteria_scores: {
      evidence_present: 1.0,
      signer_policy_satisfied: 1.0,
      timing_valid: 0.0,
      amount_correct: 1.0,
      attestation_chain_complete: 0.0,
    },
    composite_score: 0.6,
    ground_truth_hash:
      '0c2d4e6f8a1b3c5d7e9f0a2b4c6d8e0f1a3b5c7d9e1f2a3b4c5d6e7f8a1b3c5d',
    invocation_hash:
      'a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8',
  },
  {
    episode_id: 'ep_008',
    ground_truth_summary:
      'Milestone 8: Landscaping. QS attestation present. Amount: GBP 62,000. On time.',
    expected_class: 'PASS',
    construct_output_class: 'PASS',
    criteria_scores: {
      evidence_present: 1.0,
      signer_policy_satisfied: 1.0,
      timing_valid: 1.0,
      amount_correct: 1.0,
      attestation_chain_complete: 1.0,
    },
    composite_score: 1.0,
    ground_truth_hash:
      '2d4e6f8a1b3c5d7e9f0a2b4c6d8e0f1a3b5c7d9e1f2a3b4c5d6e7f8a1b3c5d7e',
    invocation_hash:
      'b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9',
  },
  {
    episode_id: 'ep_009',
    ground_truth_summary:
      'Milestone 9: Snagging and defects. QS attestation present. Amount: GBP 35,000. On time.',
    expected_class: 'PASS',
    construct_output_class: 'PASS',
    criteria_scores: {
      evidence_present: 1.0,
      signer_policy_satisfied: 1.0,
      timing_valid: 1.0,
      amount_correct: 1.0,
      attestation_chain_complete: 1.0,
    },
    composite_score: 1.0,
    ground_truth_hash:
      '4e6f8a1b3c5d7e9f0a2b4c6d8e0f1a3b5c7d9e1f2a3b4c5d6e7f8a1b3c5d7e9f',
    invocation_hash:
      'c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0',
  },
  {
    episode_id: 'ep_010',
    ground_truth_summary:
      'Milestone 10: Practical completion. QS attestation present. Final retention release: GBP 180,000. Amount incorrect (should be GBP 175,000).',
    expected_class: 'FAIL',
    construct_output_class: 'FAIL',
    criteria_scores: {
      evidence_present: 1.0,
      signer_policy_satisfied: 1.0,
      timing_valid: 1.0,
      amount_correct: 0.0,
      attestation_chain_complete: 1.0,
    },
    composite_score: 0.8,
    ground_truth_hash:
      '6f8a1b3c5d7e9f0a2b4c6d8e0f1a3b5c7d9e1f2a3b4c5d6e7f8a1b3c5d7e9f0a',
    invocation_hash:
      'd0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1',
  },
  {
    episode_id: 'ep_011',
    ground_truth_summary:
      'Milestone 11: Final account and retention release. QS attestation present. Dual attestor confirmed. Amount: GBP 50,000. On time.',
    expected_class: 'PASS',
    construct_output_class: 'PASS',
    criteria_scores: {
      evidence_present: 1.0,
      signer_policy_satisfied: 1.0,
      timing_valid: 1.0,
      amount_correct: 1.0,
      attestation_chain_complete: 1.0,
    },
    composite_score: 1.0,
    ground_truth_hash:
      '8a1b3c5d7e9f0a2b4c6d8e0f1a3b5c7d9e1f2a3b4c5d6e7f8a1b3c5d7e9f0a2b',
    invocation_hash:
      'e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2',
  },
];

export const GLOBAL_CONFLICT_PHASES: MarketPhase[] = [
  {
    phase_number: 1,
    label: 'Commitment Published',
    detail: 'hash: b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2...',
    hash: 'b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8',
    status: 'pending',
  },
  {
    phase_number: 2,
    label: 'Market Open',
    detail: 'LMSR cost function active (b = 40, worst-case loss: GBP 110.90)',
    status: 'pending',
  },
  {
    phase_number: 3,
    label: 'Trading Window',
    detail: '247 trades across 14 agents over 6-hour window',
    status: 'pending',
  },
  {
    phase_number: 4,
    label: 'Resolution Trigger',
    detail: 'Evidence bundle submitted — 3 corroborating sources, 1 counter-signal',
    status: 'pending',
  },
  {
    phase_number: 5,
    label: 'Deterministic Settlement',
    detail: 'Resolution state machine executed — outcome: ESCALATION (p = 0.73)',
    status: 'pending',
  },
  {
    phase_number: 6,
    label: 'Certificate Issued',
    detail: 'Composite score: 0.8750 across 4 criteria',
    status: 'pending',
  },
];

/**
 * Generate minimal episodes for templates that don't have full mock data.
 * These are used when executing templates other than ESCROW or GLOBAL_CONFLICT.
 */
export function generateMinimalEpisodes(
  template: TheatreTemplate
): Episode[] {
  const count = Math.min(template.fixture_count, 5);
  const episodes: Episode[] = [];

  for (let i = 0; i < count; i++) {
    const isPass = i < template.pass_count;
    const scores: Record<string, number> = {};
    for (const cid of template.criteria_ids) {
      scores[cid] = isPass ? 1.0 : Math.random() > 0.5 ? 1.0 : 0.0;
    }
    const total = Object.values(scores).reduce((a, b) => a + b, 0);
    const composite = total / Object.keys(scores).length;

    episodes.push({
      episode_id: `ep_${String(i + 1).padStart(3, '0')}`,
      ground_truth_summary: `Episode ${i + 1}: ${isPass ? 'Standard pass scenario' : 'Failure condition detected'}`,
      expected_class: isPass ? 'PASS' : 'FAIL',
      construct_output_class: isPass ? 'PASS' : 'FAIL',
      criteria_scores: scores,
      composite_score: parseFloat(composite.toFixed(4)),
      ground_truth_hash: `${String(i).repeat(4)}a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8`,
      invocation_hash: `${String(i).repeat(4)}b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9`,
    });
  }

  return episodes;
}
