# PRD — Cycle 037: Contract-Backed Verification Infrastructure

**Cycle:** 037
**Date:** 2026-03-18
**Status:** Draft
**Previous:** Cycles 024 (Construct Verification V1), 026a-c (Evidence Anchoring + Domain Anchors)

---

## 1. Problem Statement

### 1.1 Verification Is Currently "Score Some Outputs"

Construct verification works as: register → run episodes → rubric score → PASS/FAIL. There is no canonical declaration of what a construct claims, what checks are planned vs. executed, or what exactly failed. Certificates are unauditable — a PASS tells you nothing about what was tested, and a FAIL gives no machine-readable remediation path.

### 1.2 The Trust Gap

- No formal contract between construct declaration and verification checks
- No distinction between planned checks and executed checks
- No explicit refusal tracking (what a construct declares it will NOT do)
- Vague domain claims pass through unchallenged
- Certificate provenance doesn't include the spec or contract hash
- PASS/FAIL binary — no DEFERRED state when some checks can't run

### 1.3 What 037 Fixes

This cycle turns construct verification into contract-backed verification infrastructure. Every evaluation run is grounded in a declared, hashed contract. Every certificate says exactly what was planned, what was executed, and what's missing. The substrate is ready for later cycles to add multi-scorer judging and domain packs without redesigning the foundation.

---

## 2. Product Contracts

### 2.1 EvaluationContract — Persisted, Hash-Addressed

New `evaluation_contracts` table. One ACTIVE contract per registration. Creating a new contract SUPERSEDES the previous one.

| Field | Type | Purpose |
|-------|------|---------|
| `id` | UUID PK | |
| `construct_registration_id` | FK | Links to construct_registrations |
| `spec_hash` | SHA-256 | Hash of normalized construct.yaml content |
| `contract_hash` | SHA-256 | Hash of full contract including check plan |
| `normalized_claims` | JSON | Parsed domain claims with vagueness flags |
| `explicit_refusals` | JSON | Things the construct declares it will NOT do |
| `planned_checks` | JSON | Deterministic check plan derived from claims |
| `tier_cap` | nullable string | Max achievable tier if vague claims detected |
| `status` | enum | ACTIVE / SUPERSEDED |
| `created_at`, `updated_at` | timestamps | |

### 2.2 Issuance Semantics — READY / DEFERRED / REJECTED

| State | Meaning | Condition |
|-------|---------|-----------|
| READY | All planned checks executed, verdict PASS | `executed == planned` and `verdict == PASS` |
| DEFERRED | Some planned checks couldn't execute | `executed < planned` — missing dataset, dependency unavailable |
| REJECTED | Verdict FAIL or critical check failed | `verdict == FAIL` or critical planned check failed |

DEFERRED certificates carry a machine-readable remediation payload:

```json
{
  "status": "DEFERRED",
  "reason": "checks_unavailable",
  "missing_checks": [
    {"check_id": "bench-humaneval", "reason": "dataset_not_available"},
    {"check_id": "bench-swe-verified", "reason": "r2_manifest_missing"}
  ],
  "executed_count": 8,
  "planned_count": 10,
  "recommendation": "Upload missing datasets and re-run"
}
```

### 2.3 PolicyNormalizer — Accept + Downgrade

Vague domain claims are accepted at registration but flagged. Tier cap limits the maximum achievable certificate tier:

- Precise claims (e.g., "Design Systems", "Motion Design") → no tier cap
- Vague claims (e.g., "security", "AI", "general") → tier capped at UNVERIFIED
- Explicit refusals extracted from construct.yaml `refusals:` field and stored on contract

### 2.4 Planned vs Executed — Certificate Transparency

Every certificate gains `check_plan` section:

```json
{
  "check_plan": {
    "total_planned": 10,
    "total_executed": 8,
    "checks": [
      {"id": "rubric-design-systems", "type": "RUBRIC", "status": "EXECUTED", "score": 0.82},
      {"id": "bench-humaneval", "type": "BENCHMARK", "status": "NOT_EXECUTED", "reason": "dataset_not_available"}
    ]
  },
  "contract_hash": "sha256:...",
  "spec_hash": "sha256:..."
}
```

### 2.5 Hash Invalidation Rules

- construct.yaml content changes → new `spec_hash` → existing contract SUPERSEDED
- Check plan changes (new datasets available, new rubrics) → new `contract_hash`
- Certificate references both hashes immutably — verifier checks if contract is still ACTIVE

---

## 3. What This Cycle Does NOT Do

- **No multi-scorer orchestration** (future cycle)
- **No domain-specific security/pack logic** (future cycle)
- **No frontend work**
- **No R2 upload integration** (evidence anchoring pipeline from 026a-c is separate)
- **No changes to ConstructScorer** (rubric scoring engine stays as-is)
- **No changes to existing rubric definitions**

---

## 4. Existing Surface Being Extended

| Component | Current | 037 Change |
|-----------|---------|------------|
| `ConstructRegistration` model | slug, version, skill_manifest, domain_claims | FK to evaluation_contracts |
| `ConstructRegistry` service | Register, list, get, update_status | Trigger contract creation after registration |
| `ConstructAdapter` service | Create runs, capture episodes, complete runs | Thread contract_hash into run config |
| `ConstructScorer` service | Rubric scoring + verdict | **No change** |
| `ConstructCertificateBuilder` | Build + persist certificates | Add check_plan, hashes, issuance status, remediation |
| `construct_routes.py` | API endpoints | Add contract endpoints, update certificate response |
| `eval_asset_policy.py` | Asset classification | Used by CheckPlanner to determine feasible benchmark checks |
| `construct_anchor_mapper.py` | Maps dimensions to anchors | Used by CheckPlanner for anchor-based checks |

---

## 5. New Components

| Component | File | Purpose |
|-----------|------|---------|
| `SpecLoader` | `backend/services/spec_loader.py` | Parse construct.yaml → normalized ConstructSpec dataclass |
| `PolicyNormalizer` | `backend/services/policy_normalizer.py` | Validate claims, extract refusals, flag vagueness, compute tier_cap |
| `CheckPlanner` | `backend/services/check_planner.py` | Contract + available assets → deterministic list of planned checks |
| `ContractService` | `backend/services/contract_service.py` | CRUD for contracts, hash computation, supersession logic |
| `EvaluationContract` model | `backend/database/models.py` | SQLAlchemy model |
| Alembic migration | `c037_evaluation_contracts` | New table + FK on investigations |

---

## 6. Acceptance Criteria

1. Every new evaluation run references an ACTIVE contract via `contract_hash`
2. Every certificate includes `contract_hash`, `spec_hash`, and `check_plan` with planned-vs-executed status
3. DEFERRED certificates include machine-readable remediation payload listing missing checks
4. Vague domain claims produce tier-capped contracts (not registration failures)
5. Explicit refusals are extracted from construct.yaml and stored on the contract
6. Contract hash changes when spec changes → old contract SUPERSEDED, new one ACTIVE
7. Runs against a SUPERSEDED contract are rejected (must create new contract first)
8. All existing construct verification tests pass (regression)
9. New tests cover: contract creation, check planning, READY/DEFERRED/REJECTED paths, hash invalidation, vague claim detection, refusal extraction

---

## 7. Test Plan

| Area | Tests | Coverage |
|------|-------|---------|
| SpecLoader | 6 | Parse valid yaml, reject malformed, hash stability, refusals extraction |
| PolicyNormalizer | 8 | Precise claims pass, vague claims flagged, tier cap computed, refusals normalized |
| CheckPlanner | 8 | Deterministic plan from contract, benchmark availability check, anchor-based checks, missing dataset handling |
| ContractService | 6 | Create, supersede, hash computation, FK integrity, duplicate prevention |
| Certificate integration | 6 | READY/DEFERRED/REJECTED paths, remediation payload, check_plan in output |
| Hash invalidation | 4 | Spec change → supersede, contract_hash change detection, run rejection on superseded |
| Regression | 4 | Existing V1 registration+run+certificate flow unchanged |
| **Total** | **~42** | |

---

## 8. Risks

| Risk | Mitigation |
|------|------------|
| construct.yaml format varies across packs | SpecLoader validates against strict schema; reject malformed with clear errors |
| CheckPlanner depends on R2 manifest availability | Graceful degradation → DEFERRED issuance, not crash |
| Hash invalidation cascading | Only ACTIVE contracts affected; historical certificates immutably reference their contract_hash |
| Vague claim detection false positives | Conservative — only flag known-vague terms (configurable allowlist) |
