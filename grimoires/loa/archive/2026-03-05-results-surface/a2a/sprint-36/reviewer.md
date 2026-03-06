# Sprint-36 Review — Cycle-014c Codex Remediation

**Reviewer:** Senior Technical Lead
**Date:** 2026-03-05
**Sprint:** Global Sprint-36 (Codex Remediation — 5 Findings)
**Test Gate:** 399 passed, 0 failed, 1 warning (pre-existing Pydantic deprecation)

---

## Scope

Post-014c codex review identified 5 findings in the investigation toolset. Implementation addressed all 5 findings plus two follow-up passes (F1b production wiring, F1c INVESTIGATIVE scoping).

## Files Reviewed

### Source Files (7)

| File | Finding | Verdict |
|------|---------|---------|
| `backend/alembic/versions/c014c_add_stop_condition_columns.py` | F4 | PASS |
| `backend/investigation/certificate.py` | F5 | PASS |
| `backend/investigation/entity_resolver.py` | F2 | PASS |
| `backend/schemas/theatre.py` | F3 + F1c | PASS |
| `backend/market/resolution.py` | F1 + F1b + F1c | PASS |
| `backend/services/market_theatre_bridge.py` | F1 | PASS |
| `backend/api/theatre_routes.py` | F1 | PASS |

### Test Files (6)

| File | Finding | Tests |
|------|---------|-------|
| `backend/investigation/tests/test_entity_resolver.py` | F2 | 7 tests |
| `backend/investigation/tests/test_stop_condition_commitment.py` | F1 | 4 tests |
| `backend/schemas/tests/test_stop_condition_validation.py` | F3 + F1c | 19 tests |
| `backend/market/tests/test_resolution_stop_condition.py` | F1 + F1b + F1c | 24 tests |
| `backend/market/tests/test_resolution_inquiry.py` | F1 | Updated assertion |
| `backend/investigation/tests/test_toolset_e2e.py` | F2 | Updated assertion |

---

## Finding-by-Finding Assessment

### F4 — Alembic Migration Hardening [P2]

**Change:** Replaced `try/except Exception: pass` with `sa.inspect()` column checks.

**Assessment:** Clean. Inspector-based idempotency is the correct Alembic pattern. Both upgrade and downgrade check column existence before acting. No behavioral change to migration outcome, just removes silent failure masking.

### F5 — Certificate Routing Docstring [P2]

**Change:** Removed phantom "Anchoring pending" from priority list (lines 104-110). Renumbered default to priority 4. Added architectural note at line 239-240 clarifying anchoring is post-build.

**Assessment:** Accurate docstring now matches `_compute_routing()` logic exactly. The 4-priority cascade (drift → counter-signal → single provenance → allowed) is clearly documented. No behavior change.

### F2 — EntityProfile Deterministic Hash [P1]

**Change:** Counter-based `ENT001` → content-addressed `ENT-{sha256[:12]}` using canonical JSON of query fields.

**Assessment:** Correct fix for non-idempotent entity ID generation. The hash input includes `entity_name`, `jurisdiction`, and `registration_number` — the same triple that defines entity identity. Tests verify: idempotency (same query → same ID), uniqueness (different query → different ID), format (`^ENT-[0-9a-f]{12}$`). Counter retained for ordering but not in ID.

### F3 — Stop-Condition Schema Validation [P2]

**Change:** Added `field_validator("stop_condition")` for enum normalization and `model_validator("validate_stop_config_shape")` for config shape validation on `TheatreCreate`.

**Assessment:** Thorough validation:
- Enum normalization: case-insensitive, rejects unknowns
- `stop_config` without `stop_condition` → rejected
- SPONSOR_DEFINED: requires `milestone_timestamp` (valid ISO 8601, handles Z suffix for Py3.9)
- EVIDENCE_THRESHOLD: validates `min_supported_claims` (int >= 1) and `min_corroboration_score` (float 0-1)
- Inquiry class scoping: stop fields only for INVESTIGATIVE

19 tests cover all validation paths including parametrized non-INVESTIGATIVE rejection.

### F1 — Stop-Condition Settlement Wiring [P1]

**Change:** Three-pass implementation:
1. **Pass 1:** Added `STOP_CONDITION_MET` to enum, extended `check_resolution_ready()` signature, threaded through bridge and routes
2. **Pass 2 (F1b):** Added `_evaluate_stop_condition_scalar()` for production settle flows (no ClaimGraph/EvidenceEnvelope required)
3. **Pass 3 (F1c):** Gated stop-condition evaluation to INVESTIGATIVE only

**Assessment:**
- **Dual-path design** is architecturally sound: object-graph path for unit tests with full investigation runtime, scalar path for production settle flows using `evidence_state` dict.
- **INVESTIGATIVE scoping** consistently enforced at runtime (`ic == "INVESTIGATIVE"` guard) and schema level (model_validator rejects stop fields for other classes).
- **Scalar evaluator** handles all 3 stop condition types with proper fail-safe (unknown → `False`). SPONSOR_DEFINED milestone comparison allows test override via `evidence_state["current_time"]`.
- **Theatre routes** correctly pass only `stop_condition` and `stop_config` (not claim_graph/evidence_envelope which aren't available in API path). This is correct by design.
- **Bridge** accepts optional stop params with `object | None` typing to avoid circular imports.
- 24 tests cover: met/unmet for all paths, scalar evaluation for all 3 types, non-INVESTIGATIVE exclusion (parametrized), bridge-level integration.

---

## Minor Observations (Non-Blocking)

1. `test_resolution_inquiry.py` line 13: docstring says "exactly 6 values" but assertion checks `== 7`. Cosmetic inconsistency.
2. `_evaluate_stop_condition_scalar` uses `datetime.now(timezone.utc)` for SPONSOR_DEFINED when no test override — correct but worth noting this introduces non-determinism in production. The test override pattern mitigates this for testing.

---

## Verdict

**APPROVED** — All 5 findings remediated. Code quality is high, test coverage is comprehensive (54+ new/modified tests), no security issues, no regressions. The dual-path stop-condition design is well-motivated and correctly scoped to INVESTIGATIVE.
