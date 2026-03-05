# Engineer Feedback — Sprint 35 (local sprint-3)

**Reviewer**: Senior Technical Lead
**Date**: 2026-03-05
**Verdict**: All good

## Summary

### Task 3.1: Stop Condition Schema + Persistence + Commitment Hash

Verified in `backend/schemas/theatre.py` (lines 29-36): `stop_condition: Optional[str]` with `max_length=30` and `stop_config: Optional[dict]` added to `TheatreCreate`. Also present in `TheatreResponse` (lines 147-148). Database model in `backend/database/models.py` (lines 536-537) adds `String(30)` and `JSON` nullable columns to `Theatre`. The `create_theatre` route (lines 123-124) stores both fields. The `commit_theatre` route (lines 185-202) includes stop fields in the commitment hash via `SHA-256(base_hash + json.dumps(stop_fields, sort_keys=True))`, preserving backward compatibility when no stop fields are set. Alembic migration applies both columns idempotently. Post-COMMITTED immutability enforced by design — no mutation endpoint exists and the commitment hash seals the values.

All 5 acceptance criteria met.

### Task 3.2: Investigation Certificate + Builder

Verified in `backend/investigation/certificate.py`. `InvestigationCertificate` is a frozen Pydantic model with exactly 30 fields (counted: certificate_id through toolset_version). `StopCondition` enum has 3 values. `RoutingDecision` enum has 2 values. The `InvestigationCertificateBuilder._compute_routing()` (lines 216-243) implements the priority cascade:

1. Material drift -> REVIEW_REQUIRED ("drift_event_material")
2. Material counter-signal -> REVIEW_REQUIRED ("counter_signal_material")
3. Single provenance class -> REVIEW_REQUIRED ("single_provenance_class")
4. Default -> ALLOWED ("all_checks_passed")

Note: The "anchoring_pending" routing (priority 4 in spec) is intentionally not triggered because anchoring is always "pending" at build time — this is documented in the code comment at line 239 and is architecturally sound since anchoring status is set post-build.

Certificate hash uses `canonical_json()` from `theatre.engine.canonical_json` for deterministic hashing. Hash payload excludes `certificate_hash` itself and anchoring fields.

All 7 acceptance criteria met.

### Task 3.3: Stop Condition Evaluator

Verified in `backend/investigation/stop_conditions.py`. `InvestigationStopConditionEvaluator.evaluate()` dispatches to three private methods:

- `OUTCOME_RESOLUTION`: returns `(True, "time_window_expired")` when `time_remaining <= 0`
- `EVIDENCE_THRESHOLD`: reads `min_supported_claims` and `min_corroboration_score` from committed `stop_config`, counts SUPPORTED claims via `get_status_summary()`, handles zero-claims edge case
- `SPONSOR_DEFINED`: parses `milestone_timestamp` as ISO 8601, handles timezone-aware comparison

No runtime override mechanism exists — the evaluator only reads the dict passed to it.

All 4 acceptance criteria met.

### Task 3.4: Investigation Toolset Orchestrator

Verified in `backend/investigation/toolset.py`. `InvestigationConfig` Pydantic model with `domain_filters`, `stop_condition`, `stop_config`. `InvestigationToolset.__init__` instantiates all 8 tools: EvidenceEnvelope, ClaimGraph, InvestigationCounterSignalFeed, CommitmentMonitor, SignalScanner, EntityResolver, InvestigationCorroborationChecker, InvestigationCertificateBuilder. Six delegation methods pass through correctly. `build_certificate()` assembles the terminal artefact from all tool state.

All 3 acceptance criteria met.

### Task 3.5: Deterministic Artefact Writers

Verified in `backend/investigation/artifacts.py`. `ARTEFACT_TYPES` frozenset contains all 9 types. `write_artifact()` uses `canonical_json()` for deterministic serialisation, returns `(json_string, sha256_hash)`, validates artefact type. Same inputs produce byte-identical output.

All 3 acceptance criteria met.

### Task 3.6: Sprint 3 Tests (25 tests)

Verified all 25 tests across 5 test files:

| File | Tests | Verified |
|------|-------|----------|
| `test_certificate.py` | 8 | All present, correct assertions |
| `test_stop_conditions.py` | 5 | All 3 condition types tested (ready + not-ready) |
| `test_stop_condition_commitment.py` | 4 | Uses actual `TheatreCreate` schema, hash comparison |
| `test_artifacts.py` | 5 | Determinism + hash parity across tools |
| `test_toolset_e2e.py` | 3 | Full lifecycle hash chaining verified |

E2E hash chaining: `test_e2e_investigation_lifecycle` explicitly verifies `cert.evidence_envelope_hash == toolset.evidence_envelope.compute_envelope_hash()` and `cert.claim_graph_root_hash == toolset.claim_graph.compute_root_hash()`. The drift E2E test verifies material drift routing. The threshold E2E test verifies early resolution with `InvestigationStopConditionEvaluator`.

Pattern consistency with Sprint 1+2: frozen models (`model_config = {"frozen": True}`), sequential IDs, SHA-256 via hashlib, `canonical_json()` from `theatre.engine.canonical_json`, properties return copies via `list()`, no delete methods, append-only semantics.

All test acceptance criteria met.

## Approval

All good.
