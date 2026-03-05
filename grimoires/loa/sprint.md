# Sprint Plan — Cycle-014c: Investigation Toolset Implementation

**Cycle:** cycle-014c
**Date:** 5 March 2026
**PRD:** grimoires/loa/prd.md
**SDD:** grimoires/loa/sdd.md
**Sprints:** 3
**Baseline:** ≥942 passed, 15 skipped, 13 pre-existing collection errors

---

## Sprint 1: Evidence Envelope + Claim Graph (Core Data Layer)

The two foundational models — everything else in sprints 2 and 3 depends on them.

### Task 1.1: Package Init + ProvenanceClass + EvidenceItem Model

**New files:**
- `backend/investigation/__init__.py`
- `backend/investigation/models.py`
- `backend/investigation/tests/__init__.py`

**Implementation:**
1. Create `backend/investigation/` package with `__init__.py`
2. Create `backend/investigation/tests/` package with `__init__.py`
3. Implement `ProvenanceClass` enum (5 values: PUBLIC_PRIMARY, PUBLIC_SECONDARY, PRIVATE_LEAK, ANALYST_DERIVED, THIRD_PARTY_TOOL_OUTPUT)
4. Implement `EvidenceItem` frozen Pydantic model (evidence_id, content_hash, provenance_class, submitted_at, content_type, source_description, references)

**Acceptance Criteria:**
- [ ] ProvenanceClass has exactly 5 values
- [ ] EvidenceItem is frozen (immutable)
- [ ] SHA-256 content_hash field is str type
- [ ] references defaults to empty list

### Task 1.2: Evidence Envelope Service

**New file:** `backend/investigation/evidence_envelope.py`

**Implementation:**
1. `RedactionEvent` frozen Pydantic model (redaction_id, evidence_id, reason_class, redacted_at)
2. `EvidenceEnvelope` class with:
   - `submit()` — append-only, sequential IDs (E001, E002, ...), SHA-256 content hash
   - `redact()` — log redaction event, does NOT alter envelope hash
   - `get_item()`, `get_manifest()`, `compute_envelope_hash()`
   - Properties: `items`, `redactions`, `provenance_summary`
3. Envelope hash = SHA-256 of pipe-separated content_hashes in submission order

**Acceptance Criteria:**
- [ ] submit() is append-only — no delete method exists
- [ ] Sequential IDs: E001, E002, E003, ...
- [ ] redact() adds RedactionEvent but envelope hash unchanged
- [ ] compute_envelope_hash() deterministic for same content in same order
- [ ] provenance_summary returns {class_name: count} dict

### Task 1.3: Evidence Envelope Tests

**New file:** `backend/investigation/tests/test_evidence_envelope.py`

8 tests:
1. `test_submit_and_retrieve` — submit item, retrieve by ID, verify hash
2. `test_append_only` — submit 3 items, verify sequential IDs (E001, E002, E003)
3. `test_provenance_summary` — submit mixed provenance classes, verify counts
4. `test_envelope_hash_deterministic` — same content in same order → same hash
5. `test_envelope_hash_changes_on_new_item` — hash changes after new submission
6. `test_redaction_preserves_hash` — redacting item doesn't change envelope hash
7. `test_redaction_logged` — redaction event recorded with reason and timestamp
8. `test_manifest_format` — verify manifest matches expected JSON structure

**Acceptance Criteria:**
- [ ] All 8 tests pass
- [ ] Tests use no external dependencies (pure unit tests)

### Task 1.4: Claim Graph Model + Merkle Hashing

**New file:** `backend/investigation/claim_graph.py`

**Implementation:**
1. `ClaimType` enum (FACT, CAUSAL, ATTRIBUTION)
2. `ClaimStatus` enum (SUPPORTED, PARTIALLY_SUPPORTED, UNCONFIRMED, CONTRADICTED)
3. `CorroborationCheck` frozen Pydantic model (for forward reference; also defined in corroboration_checker.py)
4. `ClaimNode` frozen Pydantic model (claim_id, claim_text, claim_type, evidence_refs, osint_checks, counter_signals, status, confidence, independence_groups)
5. `ClaimGraph` class with:
   - `add_claim()` — sequential IDs (C001, C002, ...)
   - `update_claim_status()` — replace claim with updated status (returns new frozen node)
   - `link_counter_signal()` — add counter-signal ID to claim
   - `compute_root_hash()` — Merkle root per §3.7 spec
   - `get_status_summary()` — {status: count} dict
   - Property: `claims`
6. Merkle hashing: canonical_json per claim → SHA-256 leaf → pairwise merge → odd leaf duplicated

**Acceptance Criteria:**
- [ ] Uses `canonical_json()` from `theatre.engine.canonical_json`
- [ ] Merkle: single claim → root = SHA-256(canonical_json(claim))
- [ ] Merkle: two claims → root = SHA-256(hash(c1) + hash(c2))
- [ ] Merkle: odd count → last leaf duplicated before merging
- [ ] Claims sorted by claim_id (lexicographic) before hashing
- [ ] update_claim_status returns new ClaimNode (frozen immutability)

### Task 1.5: Claim Graph Tests

**New file:** `backend/investigation/tests/test_claim_graph.py`

9 tests:
1. `test_add_claim` — add claim, verify fields
2. `test_status_update` — update from UNCONFIRMED to SUPPORTED
3. `test_merkle_root_deterministic` — same claims → same root hash
4. `test_merkle_root_single_claim` — single claim: root = hash(canonical_json(claim))
5. `test_merkle_root_two_claims` — two claims: root = SHA-256(hash(c1) + hash(c2))
6. `test_merkle_root_odd_count` — 3 claims: last leaf duplicated
7. `test_merkle_root_uses_canonical_json` — verify canonical_json is used (not json.dumps)
8. `test_status_summary` — verify {SUPPORTED: N, ...} counts
9. `test_link_counter_signal` — link CS to claim, verify it appears in claim's list

**Acceptance Criteria:**
- [ ] All 9 tests pass
- [ ] Merkle tests verify exact hash values (not just "different from X")

---

## Sprint 2: Counter-Signals + Monitor + Scanner + Resolver + Checker

### Task 2.1: Investigation Counter-Signal Classes + Feed

**New file:** `backend/investigation/counter_signals.py`

**Implementation:**
1. `InvestigationCounterSignalClass` enum — 11 values (separate from pipeline counter-signals)
2. `InvestigationCounterSignal` frozen Pydantic model
3. `InvestigationCounterSignalFeed` class:
   - `log_counter_signal()` — sequential IDs (CS001, CS002, ...)
   - `get_summary()` — {checked, gaps, material_contradictions}
   - `get_detail()` — per-signal detail for certificate
   - Property: `signals`
4. Classes 10+11 (MARKET_DIVERGENCE, WITNESS_SOURCE_RECANTATION) only count toward `checked` when explicitly logged

**Acceptance Criteria:**
- [ ] 11 investigation-specific counter-signal classes
- [ ] Separate enum from pipeline COUNTER_SIGNAL_CLASSES
- [ ] MARKET_DIVERGENCE and WITNESS_SOURCE_RECANTATION are event-driven only
- [ ] get_summary() returns correct checked/gaps/material counts

### Task 2.2: Commitment Monitor

**New file:** `backend/investigation/commitment_monitor.py`

**Implementation:**
1. `DriftType` enum (5 values)
2. `DriftImpact` enum (MATERIAL, NON_MATERIAL)
3. `DriftEvent` frozen Pydantic model
4. `CommitmentMonitor` class:
   - `log_drift()` — sequential IDs (D001, D002, ...)
   - `has_material_drift()` — True if any event has MATERIAL impact
   - Property: `events`

**Acceptance Criteria:**
- [ ] has_material_drift() returns False when no material events
- [ ] has_material_drift() returns True when any event has MATERIAL impact
- [ ] DriftEvent includes evidence_ref (optional) for provenance

### Task 2.3: Signal Scanner

**New file:** `backend/investigation/signal_scanner.py`

**Implementation:**
1. `DomainFilter` enum (9 values)
2. `DOMAIN_FILTER_SOURCE_GROUPS` mapping
3. `SourceQuery`, `Anomaly` frozen Pydantic models
4. `DeltaBrief` frozen Pydantic model with content_hash
5. `SignalScanner` class:
   - `__init__(domain_filters)` — store filters
   - `scan(subject)` — mock scan returning stub DeltaBrief
   - `active_source_groups` property
   - Access-tier policy: only tier A; B/C skipped with reason
   - Scanner manifest format

**Acceptance Criteria:**
- [ ] Domain filter → source group mapping resolves correctly
- [ ] Multiple filters merge source groups (no duplicates)
- [ ] DeltaBrief content_hash is SHA-256 of canonical JSON
- [ ] Tier B/C sources recorded as skipped with reason
- [ ] Scanner manifest includes requested/resolved/skipped/access_tier_policy

### Task 2.4: Entity Resolver

**New file:** `backend/investigation/entity_resolver.py`

**Implementation:**
1. `SourceQueryRecord`, `EntityQuery` frozen Pydantic models
2. `EntityProfile` frozen Pydantic model with profile_hash
3. `EntityResolver` class:
   - `resolve(query)` — stub returning mock Companies House + London Gazette profile
   - Profile hash = SHA-256 of canonical_json(profile_dict excluding profile_hash)

**Acceptance Criteria:**
- [ ] Profile hash deterministic for same data
- [ ] Source query records include provenance per source
- [ ] Unknown entity handled gracefully (returns empty/minimal profile)

### Task 2.5: Investigation Corroboration Checker

**New file:** `backend/investigation/corroboration_checker.py`

**Implementation:**
1. `CorroborationCheck` frozen Pydantic model (claim_id, source_id, upstream_group, status, confidence)
2. `InvestigationCorroborationChecker` class:
   - `evaluate_claim(claim, checks)` → `ClaimStatus`
   - Hard invariant: SUPPORTED requires ≥2 distinct upstream_group with status='confirmed'
   - PRIVATE_LEAK-only evidence cannot achieve SUPPORTED
   - Single upstream group → PARTIALLY_SUPPORTED at best

**Acceptance Criteria:**
- [ ] SUPPORTED requires ≥2 distinct upstream_group values with 'confirmed'
- [ ] Single upstream group yields PARTIALLY_SUPPORTED max
- [ ] No override mechanism, no admin bypass
- [ ] Deterministic output for same inputs

### Task 2.6: Sprint 2 Tests

**New files:**
- `backend/investigation/tests/test_counter_signals.py` (6 tests)
- `backend/investigation/tests/test_commitment_monitor.py` (5 tests)
- `backend/investigation/tests/test_signal_scanner.py` (5 tests)
- `backend/investigation/tests/test_entity_resolver.py` (4 tests)
- `backend/investigation/tests/test_corroboration_checker.py` (5 tests)

Counter-signal tests (6):
1. `test_log_counter_signal` — log and retrieve
2. `test_summary_counts` — checked/gaps/material counts correct
3. `test_market_divergence_only_counted_when_logged` — class 10 event-driven
4. `test_witness_recantation_only_counted_when_logged` — class 11 event-driven
5. `test_detail_format` — per-signal detail matches certificate schema
6. `test_material_vs_non_material` — material flag correctly tracked

Commitment monitor tests (5):
1. `test_log_drift_event` — log and retrieve
2. `test_has_material_drift_false` — no material → False
3. `test_has_material_drift_true` — material event → True
4. `test_drift_event_fields` — all fields populated
5. `test_multiple_drift_events` — accumulates correctly

Signal scanner tests (5):
1. `test_domain_filter_to_source_groups` — mapping resolves correctly
2. `test_combined_filters` — multiple filters merge source groups
3. `test_deltabrief_hash_deterministic` — same input → same hash
4. `test_scan_with_mock_sources` — scan produces DeltaBrief
5. `test_scanner_manifest_format` — manifest JSON structure correct

Entity resolver tests (4):
1. `test_resolve_companies_house` — mock CH → valid EntityProfile
2. `test_profile_hash_deterministic` — same data → same hash
3. `test_source_query_record` — provenance metadata per source correct
4. `test_unknown_entity` — graceful failure for unknown entity

Corroboration checker tests (5):
1. `test_supported_requires_two_independent_upstreams` — one upstream cannot SUPPORTED
2. `test_supported_with_two_independent_upstreams` — two groups → SUPPORTED
3. `test_private_leak_only_remains_unconfirmed` — PRIVATE_LEAK-only stays UNCONFIRMED
4. `test_partial_status_with_single_upstream` — single → PARTIALLY_SUPPORTED
5. `test_checker_output_deterministic` — same inputs → same output

**Acceptance Criteria:**
- [ ] All 25 tests pass
- [ ] No external dependencies (pure unit tests)

---

## Sprint 3: Certificate Extension + Stop Conditions + E2E

### Task 3.1: Stop Condition Schema + Persistence + Commitment Hash

**Modified files:**
- `backend/schemas/theatre.py` — add stop_condition, stop_config to TheatreCreate
- `backend/database/models.py` — add stop_condition, stop_config columns to Theatre
- `backend/api/theatre_routes.py` — store on create, include in commitment hash, reject mutation post-COMMITTED
- New Alembic migration

**Implementation:**
1. Add `stop_condition: str | None = None` and `stop_config: dict | None = None` to TheatreCreate schema
2. Add `stop_condition = Column(String(30), nullable=True)` and `stop_config = Column(JSON, nullable=True)` to Theatre model
3. Create Alembic migration adding both columns
4. In `create_theatre`: store stop fields from request
5. In `commit_theatre`: include stop_condition and stop_config in commitment hash payload
6. Post-COMMITTED: reject changes to stop fields with 400 response

**Acceptance Criteria:**
- [ ] stop_condition and stop_config stored on theatre creation
- [ ] Commitment hash includes stop fields (changes when stop_config changes pre-commit)
- [ ] Mutation rejected post-COMMITTED (400/422 response)
- [ ] Existing theatres without stop conditions work unchanged
- [ ] Alembic migration applies cleanly

### Task 3.2: Investigation Certificate + Builder

**New file:** `backend/investigation/certificate.py`

**Implementation:**
1. `StopCondition` enum (OUTCOME_RESOLUTION, EVIDENCE_THRESHOLD, SPONSOR_DEFINED)
2. `InvestigationCertificate` frozen Pydantic model with 30+ fields
3. `InvestigationCertificateBuilder` class:
   - `build()` — assembles certificate from all toolset artefacts
   - Routing logic: material drift → counter-signal → single provenance → anchoring pending → ALLOWED
   - Populates all hash fields from envelope/claim_graph
   - Populates all summary fields from counter-signals/drift/redactions

**Acceptance Criteria:**
- [ ] All 30+ fields present in InvestigationCertificate
- [ ] Routing: material drift → REVIEW_REQUIRED with "drift_event_material"
- [ ] Routing: material counter-signal → REVIEW_REQUIRED with "counter_signal_material"
- [ ] Routing: single provenance class → REVIEW_REQUIRED with "single_provenance_class"
- [ ] Routing: anchoring pending → REVIEW_REQUIRED with "anchoring_pending"
- [ ] Routing: normal case → ALLOWED
- [ ] Certificate hash fields match envelope/claim_graph computed values

### Task 3.3: Stop Condition Evaluator

**New file:** `backend/investigation/stop_conditions.py`

**Implementation:**
1. `InvestigationStopConditionEvaluator` class:
   - `evaluate(stop_condition, stop_config, claim_graph, evidence_envelope, time_remaining)` → `(bool, str)`
   - OUTCOME_RESOLUTION: ready when time_remaining <= 0
   - EVIDENCE_THRESHOLD: ready when claim graph meets stop_config thresholds (min_supported_claims, min_corroboration_score)
   - SPONSOR_DEFINED: ready when milestone_timestamp reached
2. Reads stop_config keys only — no runtime overrides accepted

**Acceptance Criteria:**
- [ ] OUTCOME_RESOLUTION: ready when time runs out
- [ ] EVIDENCE_THRESHOLD: ready when N claims SUPPORTED
- [ ] SPONSOR_DEFINED: ready when milestone date reached
- [ ] Only reads committed stop_config (no mutable runtime overrides)

### Task 3.4: Investigation Toolset Orchestrator

**New file:** `backend/investigation/toolset.py`

**Implementation:**
1. `InvestigationConfig` Pydantic model (domain_filters, stop_condition, stop_config)
2. `InvestigationToolset` class:
   - `__init__(config)` — instantiate all 8 tools
   - Delegation methods: submit_evidence, register_claim, log_counter_signal, log_drift, run_scan, resolve_entity
   - `build_certificate()` — delegates to InvestigationCertificateBuilder

**Acceptance Criteria:**
- [ ] All 8 tools instantiated and wired
- [ ] Delegation methods pass through to underlying tools
- [ ] build_certificate() produces valid InvestigationCertificate

### Task 3.5: Deterministic Artefact Writers

**New file:** `backend/investigation/artifacts.py`

**Implementation:**
1. `write_artifact(name, data)` → `(json_string, sha256_hash)`
2. Uses `canonical_json()` for deterministic serialisation
3. Supports all 9 artefact types: deltabrief, scanner_manifest, entity_profile, evidence_manifest, corroboration_results, counter_signals, claim_graph, drift_events, market_summary

**Acceptance Criteria:**
- [ ] Same inputs → byte-identical output
- [ ] Uses canonical_json() (sorted keys, no whitespace)
- [ ] Hash preimages match certificate fields

### Task 3.6: Sprint 3 Tests

**New files:**
- `backend/investigation/tests/test_certificate.py` (8 tests)
- `backend/investigation/tests/test_stop_conditions.py` (5 tests)
- `backend/investigation/tests/test_stop_condition_commitment.py` (4 tests)
- `backend/investigation/tests/test_artifacts.py` (5 tests)
- `backend/investigation/tests/test_toolset_e2e.py` (3 tests)

Certificate tests (8):
1. `test_build_minimal_certificate` — envelope + claim graph → valid certificate
2. `test_certificate_includes_all_fields` — all 30+ fields present
3. `test_routing_hint_material_drift` — material drift → REVIEW_REQUIRED
4. `test_routing_hint_material_counter_signal` — material CS → REVIEW_REQUIRED
5. `test_routing_hint_single_provenance` — all PUBLIC_PRIMARY → REVIEW_REQUIRED
6. `test_routing_hint_allowed` — normal case → ALLOWED
7. `test_certificate_hash_deterministic` — same inputs → same hashes
8. `test_provenance_summary_in_certificate` — counts match envelope

Stop condition tests (5):
1. `test_outcome_resolution_time_expired` — ready when time runs out
2. `test_outcome_resolution_time_remaining` — not ready while time left
3. `test_evidence_threshold_met` — N SUPPORTED claims → ready
4. `test_evidence_threshold_not_met` — insufficient → not ready
5. `test_sponsor_defined_milestone` — milestone reached → ready

Stop condition commitment tests (4):
1. `test_stop_condition_persisted_on_create` — stored on theatre
2. `test_stop_config_included_in_commitment_hash` — hash changes with stop_config
3. `test_stop_condition_immutable_post_commit` — mutation rejected post-COMMITTED
4. `test_resolution_uses_committed_stop_config_only` — runtime override rejected

Artefact tests (5):
1. `test_artifact_writer_deterministic` — same inputs → byte-identical
2. `test_manifest_contains_access_tier_policy` — scanner manifest correct
3. `test_claim_graph_json_matches_root_hash` — root hash recomputes
4. `test_evidence_manifest_hash_matches_certificate_field` — bundle hash matches
5. `test_counter_signal_artifact_matches_certificate_detail` — detail parity

E2E tests (3):
1. `test_e2e_investigation_lifecycle` — full lifecycle: submit evidence → register claims → corroborate → counter-signals → build certificate → verify all hashes chain
2. `test_e2e_with_drift_event` — same + material drift → REVIEW_REQUIRED
3. `test_e2e_evidence_threshold_resolution` — early resolution via evidence threshold

**Acceptance Criteria:**
- [ ] All 25 tests pass
- [ ] E2E tests verify hash chaining across all tools
- [ ] Stop condition commitment tests use actual theatre schema/routes

---

## Gate Rule

≥942 passed (current baseline), 15 skipped, 13 pre-existing collection errors (same node IDs). Zero new failures. All 67 new investigation toolset tests pass. Post-014c expected: ≥1009 passed.

---

## Files Created/Modified Summary

| Sprint | File | Action |
|--------|------|--------|
| 1 | `backend/investigation/__init__.py` | NEW |
| 1 | `backend/investigation/models.py` | NEW |
| 1 | `backend/investigation/evidence_envelope.py` | NEW |
| 1 | `backend/investigation/claim_graph.py` | NEW |
| 1 | `backend/investigation/tests/__init__.py` | NEW |
| 1 | `backend/investigation/tests/test_evidence_envelope.py` | NEW |
| 1 | `backend/investigation/tests/test_claim_graph.py` | NEW |
| 2 | `backend/investigation/counter_signals.py` | NEW |
| 2 | `backend/investigation/commitment_monitor.py` | NEW |
| 2 | `backend/investigation/signal_scanner.py` | NEW |
| 2 | `backend/investigation/entity_resolver.py` | NEW |
| 2 | `backend/investigation/corroboration_checker.py` | NEW |
| 2 | `backend/investigation/tests/test_counter_signals.py` | NEW |
| 2 | `backend/investigation/tests/test_commitment_monitor.py` | NEW |
| 2 | `backend/investigation/tests/test_signal_scanner.py` | NEW |
| 2 | `backend/investigation/tests/test_entity_resolver.py` | NEW |
| 2 | `backend/investigation/tests/test_corroboration_checker.py` | NEW |
| 3 | `backend/schemas/theatre.py` | MODIFY |
| 3 | `backend/database/models.py` | MODIFY |
| 3 | `backend/api/theatre_routes.py` | MODIFY |
| 3 | Alembic migration | NEW |
| 3 | `backend/investigation/certificate.py` | NEW |
| 3 | `backend/investigation/stop_conditions.py` | NEW |
| 3 | `backend/investigation/toolset.py` | NEW |
| 3 | `backend/investigation/artifacts.py` | NEW |
| 3 | `backend/investigation/tests/test_certificate.py` | NEW |
| 3 | `backend/investigation/tests/test_stop_conditions.py` | NEW |
| 3 | `backend/investigation/tests/test_stop_condition_commitment.py` | NEW |
| 3 | `backend/investigation/tests/test_artifacts.py` | NEW |
| 3 | `backend/investigation/tests/test_toolset_e2e.py` | NEW |
