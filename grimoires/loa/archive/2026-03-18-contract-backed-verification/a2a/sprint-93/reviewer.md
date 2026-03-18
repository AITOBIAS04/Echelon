# Sprint 85 (Cycle 037, Sprint 1) — Implementation Report

## Sprint: Foundation — Model, Migration, SpecLoader, PolicyNormalizer, Schemas

**Status:** COMPLETE
**Tests:** 14/14 passing
**Files Changed:** 6 new, 2 modified

---

## Task 1.1: EvaluationContract Model + Migration

**Status:** COMPLETE

### Implementation

- **`backend/database/models.py`** — Added `EvaluationContractStatus` enum (ACTIVE, SUPERSEDED) and `EvaluationContract` model with:
  - 11 columns (id, construct_registration_id, spec_hash, contract_hash, normalized_claims, explicit_refusals, planned_checks, tier_cap, status, created_at, updated_at)
  - Partial unique index: `uq_active_contract_per_registration` — ensures one ACTIVE contract per registration using `postgresql_where=text("status = 'ACTIVE'")`
  - FK to `construct_registrations.id`
  - `contract_hash` indexed for lookup
- **`backend/database/models.py`** — Added nullable `contract_hash` column (VARCHAR(128)) to `Investigation` model for backward compatibility
- **`backend/alembic/versions/c037_evaluation_contracts.py`** — New migration chained from `c025_osint_signals`:
  - Creates `evaluation_contracts` table
  - Creates partial unique index and contract_hash index
  - Adds `contract_hash` column to `investigations`

### Acceptance Criteria

- [x] EvaluationContract model with all SDD-specified columns
- [x] Partial unique index (one ACTIVE per registration)
- [x] contract_hash column on Investigation (nullable)
- [x] Alembic migration chains correctly from c025

---

## Task 1.2: SpecLoader Service + Tests

**Status:** COMPLETE

### Implementation

- **`backend/services/spec_loader.py`** — New service:
  - `ConstructSpec` frozen dataclass with 7 fields (slug, version, domain_claims, refusals, skill_manifest, raw_yaml, spec_hash)
  - `compute_spec_hash(yaml_content)` — deterministic SHA-256 via canonical JSON (`json.dumps(parsed, sort_keys=True, separators=(",",":"))`)
  - `load(yaml_content)` — YAML parsing with validation for required fields (slug, version, domain_claims, skill_manifest), non-empty lists, optional refusals
- **`backend/tests/test_spec_loader.py`** — 6 tests:
  - `test_parse_valid_yaml` — Full round-trip parsing
  - `test_hash_stability` — Same input → same hash
  - `test_refusals_extraction` — Optional field handling
  - `test_missing_required_field` — ValueError on missing slug
  - `test_invalid_yaml_syntax` — ValueError on bad YAML
  - `test_empty_domain_claims` — ValueError on empty list

### Acceptance Criteria

- [x] Parses construct.yaml into ConstructSpec dataclass
- [x] Deterministic SHA-256 spec_hash (canonical JSON)
- [x] Validates required fields with clear error messages
- [x] 6 tests covering happy path and error cases

---

## Task 1.3: PolicyNormalizer Service + Tests

**Status:** COMPLETE

### Implementation

- **`backend/services/policy_normalizer.py`** — New service:
  - `KNOWN_PRECISE_DOMAINS` — 19 recognized precise domains (snake_case)
  - `KNOWN_VAGUE_TERMS` — 12 known vague terms (security, ai, general, etc.)
  - `NormalizationResult` frozen dataclass (normalized_claims, explicit_refusals, tier_cap, has_vague_claims)
  - `_to_snake_case(s)` — Regex-based normalization
  - `_classify_claim(domain)` — Three-tier classification: precise (in allowlist) → vague (tokens match vague terms) → unrecognized
  - `normalize(spec)` — Full normalization with tier_cap="UNVERIFIED" if any vague claims
- **`backend/tests/test_policy_normalizer.py`** — 8 tests:
  - `test_precise_claim` — "Design Systems" → not vague, matched_category="design_systems"
  - `test_vague_claim_broad_category` — "security" → vague, reason="broad_category"
  - `test_unrecognized_domain` — "quantum_cooking" → vague, reason="unrecognized_domain"
  - `test_mixed_claims_tier_cap` — Mix of precise+vague → tier_cap="UNVERIFIED"
  - `test_all_precise_no_tier_cap` — All precise → tier_cap=None
  - `test_refusals_extracted` — Refusals passthrough from spec
  - `test_empty_refusals` — Empty list handling
  - `test_vague_term_in_compound_claim` — "AI Engineering" → vague (contains "ai" token)

### Acceptance Criteria

- [x] Classifies claims as precise or vague using allowlists
- [x] Tier caps at UNVERIFIED when any vague claims present
- [x] Extracts and passes through refusals
- [x] 8 tests covering classification logic and edge cases

---

## Task 1.4: Pydantic Schemas

**Status:** COMPLETE

### Implementation

- **`backend/schemas/construct_schemas.py`** — Extended with cycle-037 schemas:
  - `CreateContractRequest` — POST body with yaml_content field
  - `NormalizedClaimSchema` — Classified domain claim (domain, original, is_vague, matched_category, vagueness_reason)
  - `RefusalSchema` — Explicit refusal (scope, reason)
  - `PlannedCheckSchema` — Planned evaluation check (check_id, check_type, domain, source, critical, asset_id, anchor_class)
  - `ContractResponse` — Full contract response with all fields
  - `ContractListResponse` — Paginated list wrapper
  - `CheckPlanEntrySchema` — Individual check in plan (id, type, status, score, reason)
  - `CheckPlanSchema` — Planned-vs-executed check plan
  - `RemediationSchema` — Machine-readable remediation payload for DEFERRED certificates
  - Extended `CertificateResponse` with: contract_hash, spec_hash, issuance_status, check_plan, remediation (all nullable for backward compat)

### Acceptance Criteria

- [x] All 9 new/extended schemas defined per SDD
- [x] CertificateResponse backward compatible (nullable contract fields)
- [x] Forward references resolved (CheckPlanSchema, RemediationSchema)

---

## Test Results

```
14 passed in 0.07s

backend/tests/test_spec_loader.py::TestSpecLoaderParsing::test_parse_valid_yaml PASSED
backend/tests/test_spec_loader.py::TestSpecLoaderParsing::test_hash_stability PASSED
backend/tests/test_spec_loader.py::TestSpecLoaderParsing::test_refusals_extraction PASSED
backend/tests/test_spec_loader.py::TestSpecLoaderParsing::test_missing_required_field PASSED
backend/tests/test_spec_loader.py::TestSpecLoaderParsing::test_invalid_yaml_syntax PASSED
backend/tests/test_spec_loader.py::TestSpecLoaderParsing::test_empty_domain_claims PASSED
backend/tests/test_policy_normalizer.py::TestPolicyNormalizer::test_precise_claim PASSED
backend/tests/test_policy_normalizer.py::TestPolicyNormalizer::test_vague_claim_broad_category PASSED
backend/tests/test_policy_normalizer.py::TestPolicyNormalizer::test_unrecognized_domain PASSED
backend/tests/test_policy_normalizer.py::TestPolicyNormalizer::test_mixed_claims_tier_cap PASSED
backend/tests/test_policy_normalizer.py::TestPolicyNormalizer::test_all_precise_no_tier_cap PASSED
backend/tests/test_policy_normalizer.py::TestPolicyNormalizer::test_refusals_extracted PASSED
backend/tests/test_policy_normalizer.py::TestPolicyNormalizer::test_empty_refusals PASSED
backend/tests/test_policy_normalizer.py::TestPolicyNormalizer::test_vague_term_in_compound_claim PASSED
```

---

## Files Summary

### New Files (6)
| File | Lines | Purpose |
|------|-------|---------|
| `backend/services/spec_loader.py` | 77 | YAML→ConstructSpec parser with hash |
| `backend/services/policy_normalizer.py` | 131 | Domain claim classifier + normalizer |
| `backend/tests/test_spec_loader.py` | 90 | 6 SpecLoader tests |
| `backend/tests/test_policy_normalizer.py` | 79 | 8 PolicyNormalizer tests |
| `backend/alembic/versions/c037_evaluation_contracts.py` | ~65 | Migration: contracts table + investigation column |
| `grimoires/loa/a2a/sprint-85/reviewer.md` | this file | Implementation report |

### Modified Files (2)
| File | Changes |
|------|---------|
| `backend/database/models.py` | +EvaluationContractStatus enum, +EvaluationContract model, +Investigation.contract_hash column |
| `backend/schemas/construct_schemas.py` | +9 schemas, extended CertificateResponse |
