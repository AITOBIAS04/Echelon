# Sprint Plan — Cycle 037: Contract-Backed Verification Infrastructure

**Cycle:** 037
**Date:** 2026-03-18
**Builder:** Loa
**Team:** 1 AI agent (Loa)
**Sprints:** 3

---

## Sprint 1: Foundation — Model, Migration, SpecLoader, PolicyNormalizer

**Goal:** Database layer + pure-logic services with full test coverage. No API changes yet.

### Task 1.1: EvaluationContract Model + Alembic Migration
- [ ] Add `EvaluationContractStatus` enum and `EvaluationContract` model to `backend/database/models.py`
- [ ] Add `contract_hash` column (nullable VARCHAR(128)) to Investigation model
- [ ] Create `backend/alembic/versions/c037_evaluation_contracts.py` migration chaining from `c025_osint_signals`
  - Create `evaluation_contracts` table
  - Partial unique index `uq_active_contract_per_registration` (WHERE status = 'ACTIVE')
  - Index on `contract_hash`
  - Add `contract_hash` column to `investigations`
- [ ] Run migration locally to verify (`alembic upgrade head`)
- **AC:** Migration applies cleanly on existing DB; model matches SDD §3.2; `alembic downgrade` reverses cleanly

### Task 1.2: SpecLoader Service + Tests
- [ ] Create `backend/services/spec_loader.py` with `ConstructSpec` dataclass and `load()` / `compute_spec_hash()` methods
- [ ] Validate required fields: `slug`, `version`, `domain_claims` (non-empty), `skill_manifest` (non-empty)
- [ ] Extract `refusals` field (defaults to `[]`)
- [ ] SHA-256 hash via canonical JSON (sorted_keys, compact separators)
- [ ] Create `backend/tests/test_spec_loader.py` — 6 tests:
  1. Parse valid construct.yaml → correct ConstructSpec fields
  2. Hash stability — same content always produces same spec_hash
  3. Refusals extraction — refusals field parsed into list[dict]
  4. Missing required field → ValueError
  5. Invalid YAML syntax → ValueError
  6. Empty domain_claims → ValueError
- **AC:** All 6 tests pass; hash is deterministic across runs

### Task 1.3: PolicyNormalizer Service + Tests
- [ ] Create `backend/services/policy_normalizer.py` with `NormalizationResult` dataclass and `normalize()` method
- [ ] Implement `KNOWN_PRECISE_DOMAINS` and `KNOWN_VAGUE_TERMS` sets
- [ ] Classification: snake_case normalize → precise match → vague match → unrecognized
- [ ] Tier cap: `None` if all precise, `"UNVERIFIED"` if any vague
- [ ] Create `backend/tests/test_policy_normalizer.py` — 8 tests:
  1. Precise claim ("Design Systems") → `is_vague: false`, `matched_category: "design_systems"`
  2. Vague claim ("security") → `is_vague: true`, `vagueness_reason: "broad_category"`
  3. Unrecognized claim ("quantum_cooking") → `is_vague: true`, `vagueness_reason: "unrecognized_domain"`
  4. Mixed claims → `tier_cap: "UNVERIFIED"`, `has_vague_claims: true`
  5. All precise → `tier_cap: None`, `has_vague_claims: false`
  6. Refusals extracted from spec → correct format
  7. Empty refusals → `explicit_refusals: []`
  8. Multiple vague terms in single claim → correctly flagged
- **AC:** All 8 tests pass; vague detection matches SDD §4.2 algorithm

### Task 1.4: Pydantic Schemas for Contracts
- [ ] Add to `backend/schemas/construct_schemas.py`:
  - `CreateContractRequest`
  - `PlannedCheckSchema`, `NormalizedClaimSchema`, `RefusalSchema`
  - `ContractResponse`, `ContractListResponse`
  - `CheckPlanEntrySchema`, `CheckPlanSchema`, `RemediationSchema`
  - Extend `CertificateResponse` with `contract_hash`, `spec_hash`, `issuance_status`, `check_plan`, `remediation`
- **AC:** All schemas validate correctly; backward-compatible (new fields Optional with defaults)

---

## Sprint 2: CheckPlanner, ContractService, Adapter Integration

**Goal:** Complete the contract pipeline — planning, persistence, and run-time threading. Full test coverage.

### Task 2.1: CheckPlanner Service + Tests
- [ ] Create `backend/services/check_planner.py` with `PlannedCheck` dataclass, `plan_checks()`, `compute_contract_hash()`
- [ ] Rubric checks: query `get_rubrics(slug)` for each precise domain claim
- [ ] Benchmark checks: call `map_dimension_anchors()` → filter `BENCHMARK_DATASET` → check `is_r2_eligible()`
- [ ] Anchor checks: `PUBLIC_STANDARD` and `DETERMINISTIC_CHECK` anchor classes
- [ ] Sort output by `(check_type, domain, check_id)` for determinism
- [ ] Contract hash: SHA-256 of `spec_hash:canonical_checks_json`
- [ ] Create `backend/tests/test_check_planner.py` — 8 tests:
  1. Artisan construct → rubric checks for each domain
  2. Construct with code domain → benchmark check for humaneval
  3. Accessibility claim → anchor check for WCAG
  4. Deterministic output — same input always same plan
  5. Contract hash stability — same spec_hash + checks → same contract_hash
  6. No available rubrics → empty rubric checks (benchmark/anchor only)
  7. Missing dataset not in available_assets → check still planned (NOT_EXECUTED at eval time)
  8. Mixed domains → sorted output order
- **AC:** All 8 tests pass; plan is deterministic; contract_hash stable

### Task 2.2: ContractService + Tests
- [ ] Create `backend/services/contract_service.py` with `create_contract()`, `get_active_contract()`, `get_by_hash()`, `supersede()`, `validate_contract_active()`
- [ ] Supersession: creating new contract for same registration supersedes existing ACTIVE
- [ ] Idempotency: same `spec_hash` on ACTIVE contract → return existing (no duplicate)
- [ ] Create `backend/tests/test_contract_service.py` — 6 tests:
  1. Create contract → persisted with ACTIVE status
  2. Create second contract for same registration → first SUPERSEDED
  3. `get_active_contract` returns only ACTIVE
  4. `get_by_hash` returns correct contract
  5. `validate_contract_active` returns False for SUPERSEDED hash
  6. Idempotent creation — same spec_hash returns existing contract
- **AC:** All 6 tests pass; partial unique index enforced

### Task 2.3: ConstructAdapter Integration
- [ ] Modify `backend/services/construct_adapter.py`:
  - `create_run()` accepts `contract_hash` parameter
  - Validate contract is ACTIVE via `ContractService.validate_contract_active()`
  - Set `investigation.contract_hash = contract_hash`
  - Include `contract_hash` in `stop_config_json`
  - Raise `ValueError` if contract SUPERSEDED or not found
- [ ] Backward compat: if no contract_hash passed (pre-037 caller), skip validation
- **AC:** Runs created with contract_hash; SUPERSEDED contract rejected with clear error

### Task 2.4: Hash Invalidation Tests
- [ ] Create `backend/tests/test_hash_invalidation.py` — 4 tests:
  1. Spec content change → new `spec_hash` → old contract SUPERSEDED, new ACTIVE
  2. Check plan change (new asset available) → new `contract_hash`
  3. Run against SUPERSEDED contract → `ValueError`
  4. Certificate references immutable `contract_hash` even after supersession
- **AC:** All 4 tests pass; hash invalidation chain works end-to-end

---

## Sprint 3: API Routes, Certificate Integration, Regression

**Goal:** Wire everything into API layer. Certificate issuance produces check_plan + issuance status. V1 regression passes.

### Task 3.1: Contract API Endpoints
- [ ] Add to `backend/api/construct_routes.py`:
  - `POST /{slug}/{version}/contract` — create/refresh contract from yaml_content
  - `GET /{slug}/{version}/contract` — get ACTIVE contract
  - `GET /{slug}/{version}/contracts` — list all contracts
- [ ] Error handling: 404 (registration not found), 400 (invalid YAML), 409 (duplicate spec_hash)
- [ ] Wire SpecLoader → PolicyNormalizer → CheckPlanner → ContractService in POST handler
- **AC:** All 3 endpoints return correct responses per SDD §5.1

### Task 3.2: Modify create_run Endpoint
- [ ] Update `POST /{slug}/{version}/runs` to:
  - Fetch ACTIVE contract for registration
  - Return 409 if no ACTIVE contract exists
  - Thread `contract_hash` into `ConstructAdapter.create_run()`
- **AC:** Run creation requires ACTIVE contract; contract_hash stored on investigation

### Task 3.3: Certificate Builder Extensions + Issuance Logic
- [ ] Extend `backend/services/construct_certificate_builder.py`:
  - Add `contract_hash`, `spec_hash`, `check_plan`, `issuance_status`, `remediation` to `ConstructCertificate`
  - Add `compute_issuance_status()` method
  - Update `build()` to accept `contract` parameter
  - Update `to_certificate_json()` to include new fields
- [ ] Modify `POST /{slug}/{version}/certificate` route:
  - Fetch contract via investigation's `contract_hash`
  - Build `check_plan` comparing planned vs executed
  - Compute issuance status (READY / DEFERRED / REJECTED)
  - Apply `tier_cap` from contract
  - Include all in certificate response
- [ ] Backward compat: pre-037 runs (contract_hash = NULL) → skip contract fields
- [ ] Create `backend/tests/test_certificate_integration.py` — 6 tests:
  1. All checks executed + PASS → issuance_status = READY
  2. Some checks missing + PASS → DEFERRED with remediation payload
  3. FAIL verdict → REJECTED
  4. Remediation payload includes missing check IDs and reasons
  5. check_plan in certificate shows EXECUTED/NOT_EXECUTED per check
  6. Pre-037 run (no contract_hash) → certificate omits contract fields
- **AC:** All 6 tests pass; READY/DEFERRED/REJECTED paths all work

### Task 3.4: V1 Regression Tests
- [ ] Create `backend/tests/test_regression_v1.py` — 4 tests:
  1. Register construct (V1 flow, no contract) → still works
  2. Create run → capture episodes → complete run → existing flow unchanged
  3. Issue certificate (pre-037 run) → existing fields present, new fields null
  4. List constructs → existing response shape unchanged
- **AC:** All 4 tests pass; no regression in V1 flow

---

## Summary

| Sprint | Tasks | Tests | Focus |
|--------|-------|-------|-------|
| 1 | 4 | 14 | DB layer + pure-logic services |
| 2 | 4 | 18 | Contract pipeline + integration |
| 3 | 4 | 10 | API + certificate + regression |
| **Total** | **12** | **~42** | |

**Dependencies:**
- Sprint 2 depends on Sprint 1 (model + services must exist)
- Sprint 3 depends on Sprint 2 (ContractService + CheckPlanner needed for routes)

**Risk buffer:** Sprint 3 has natural slack — regression tests catch any integration issues before they compound.
