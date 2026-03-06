# Sprint 1 (Global 43) — Deployability Routing

**Cycle:** cycle-017 (Policy Surface)
**Status:** COMPLETE
**Date:** 2026-03-06

---

## Tasks Completed

### Task 1.1: RoutingEvaluator Service
**New file:** `backend/services/routing_evaluator.py`

- `RoutingEvaluator` with `RoutingPolicy` dataclass for configurable thresholds
- `evaluate()` returns `RoutingDecision(hint, reason_code, rule_name)`
- 6 priority-ordered rules: blocked_tier > block_threshold > review_tier > review_threshold > always_review_inquiry_class > default
- All types are frozen dataclasses/enums for immutability

### Task 1.2: Certificate Pipeline Integration
**Modified:** `backend/services/theatre_bridge.py`

- Imported `RoutingEvaluator` and hooked it after certificate creation (line ~249)
- Sets `routing_hint` and `review_reason_code` on the `TheatreCertificate` before persistence
- Creates `TheatreAuditEvent` with `event_type="ROUTING_DECISION"` containing certificate_id, routing_hint, reason_code, rule_name

### Task 1.3: API Filter — Certificates by Routing Hint
**Modified:** `backend/api/theatre_routes.py`

- Added `routing_hint: Optional[str] = Query(None)` parameter to `GET /api/v1/certificates`
- Filters with `.upper()` normalization
- Invalid values return empty list (not error)

### Task 1.4: Frontend — Routing Hint Badge (Behind Flag)
**Modified:**
- `frontend/src/types/theatre.ts` — Extended `TheatreCertificateResponse` with routing_hint, review_reason_code, coherence_review_required, coherence_gate_status, coherence_reviewed_at, is_deployable; Extended `TheatreCertificateSummaryResponse` with routing_hint, coherence_gate_status, is_deployable
- `frontend/src/hooks/useCertificateGallery.ts` — Extended `UnifiedCertificate` with routing_hint, coherence_gate_status, is_deployable; passes through from summary response
- `frontend/src/pages/CertificatesPage.tsx` — Added `RoutingHintBadge` component (ALLOWED=green, REVIEW_REQUIRED=amber, BLOCKED=red); renders behind `isEnabled('CYCLE_017_DEPLOYABILITY_ROUTING')` flag

---

## Test Summary

| # | Test | Result |
|---|------|--------|
| 1 | Score below block threshold -> BLOCKED + reason code | PASS |
| 2 | INVESTIGATIVE + good score -> REVIEW_REQUIRED | PASS |
| 3 | REJECTED tier -> BLOCKED regardless of score | PASS |
| 4 | Good score + COUNTERFACTUAL -> ALLOWED | PASS |
| 5 | Certificate routing_hint persisted to DB | PASS |
| 6 | ROUTING_DECISION audit event with correct detail_json | PASS |
| 7 | Routing hint filter query works (DB-level) | PASS |
| 8 | DRAFT tier -> REVIEW_REQUIRED | PASS |

**8/8 tests passing**

---

## Regression Check

- Backend: 62 passed, 3 failed (pre-existing investigation_routes failures)
- Frontend: Build passes clean
- Sprint 0 tests: All 4 still passing

---

## Files Changed

| File | Change |
|------|--------|
| `backend/services/routing_evaluator.py` | NEW — RoutingEvaluator service |
| `backend/services/theatre_bridge.py` | MODIFIED — routing hook + audit event |
| `backend/api/theatre_routes.py` | MODIFIED — routing_hint query param |
| `backend/tests/test_c017_sprint1_routing.py` | NEW — 8 tests |
| `frontend/src/types/theatre.ts` | MODIFIED — 017 fields on cert types |
| `frontend/src/hooks/useCertificateGallery.ts` | MODIFIED — pass routing fields |
| `frontend/src/pages/CertificatesPage.tsx` | MODIFIED — RoutingHintBadge |
