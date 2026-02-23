Echelon Quant-Grade LMSR Builds (v0.2)
Generated: 2026-02-23T18:22:19Z

Fixes applied vs v0.1:
- API fidelity fixtures now have real coverage diversity (vary b, n_outcomes, non-uniform x, zero-delta, large size, resolve-phase, missing field, incorrect quote).
- Perturbation fixtures labels now match content; added saboteur-only cases and included heartbeat_schedule_committed + vrf_execution_window_modelled verdicts.

Includes:
1) Deterministic LMSR trade ledger output spec
   - ledger_schema.json
   - example_ledger.jsonl

Parent hygiene package:
- quant_market_hygiene_v0_1/QUANT_MARKET_HYGIENE_V1.template.json + dataset

Suites:
- api_fidelity_suite_v0_1/QUANT_MARKET_API_FIDELITY_V1.template.json + api_fidelity_fixtures_10.json
- perturbation_suite_v0_1/QUANT_MARKET_PERTURBATION_HARNESS_V1.template.json + perturbation_fixtures_10.json
- b_sensitivity_suite_v0_1/LMSR_B_SENSITIVITY_SUITE_V1.template.json + b_sensitivity_fixtures_5.json (unchanged; already solid)

All files are canonical-JSON hashable (RFC8785 subset assumption) and intended for replay-only product theatres.
