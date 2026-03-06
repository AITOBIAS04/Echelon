# Sprint 47 (Cycle-017 Sprint 5) — WebSocket Policy Events + Frontend Integration + Polish

## Implementation Report

**Status**: COMPLETE — 6/6 tasks implemented, 5/5 tests passing

### Task Summary

| Task | Description | Status |
|------|-------------|--------|
| 5.1 | WebSocket policy event types (3 broadcast methods + hooks) | DONE |
| 5.2 | Remove 017-scoped feature flags (3 removed, 2 retained) | DONE |
| 5.3 | Delete cycle017.ts stubs, extend real types | DONE |
| 5.4 | Frontend polish — null-safe rendering | DONE |
| 5.5 | E2E test — full policy lifecycle | DONE |
| 5.6 | Final grep audit — clean codebase | DONE |

### Files Modified/Created/Deleted

| File | Change |
|------|--------|
| `backend/websockets/realtime_manager.py` | MODIFIED — Added `broadcast_routing_decision`, `broadcast_coherence_gate_transition`, `broadcast_tao_flow_alert` |
| `backend/services/theatre_bridge.py` | MODIFIED — Hooked WS `broadcast_routing_decision` after routing audit event |
| `backend/services/coherence_gate_evaluator.py` | MODIFIED — Hooked WS `broadcast_coherence_gate_transition` on open_gate + resolve_gate |
| `backend/services/tao_flow_aggregator.py` | MODIFIED — Hooked WS `broadcast_tao_flow_alert` on threshold crossing |
| `frontend/src/lib/featureFlags.ts` | MODIFIED — Removed 3 flags, retained CYCLE_017_TAO_FLOW + WEBSOCKET_REALTIME |
| `frontend/src/pages/CertificatesPage.tsx` | MODIFIED — Removed isEnabled gates, render routing/gate badges unconditionally |
| `frontend/src/pages/InvestigationPage.tsx` | MODIFIED — Removed isEnabled gate on legal review warning |
| `frontend/src/components/investigation/EvidenceEnvelopePanel.tsx` | MODIFIED — Removed isEnabled gate on query determinism badge |
| `frontend/src/types/theatre.ts` | MODIFIED — Added `GateStatus` union type |
| `frontend/src/types/index.ts` | MODIFIED — Added `RoutingHint`, `GateStatus` re-exports |
| `frontend/src/types/cycle017.ts` | DELETED — Stubs migrated to canonical type files |
| `backend/tests/test_c017_sprint5_ws_policy_e2e.py` | NEW — 5 tests |

### Implementation Details

**Task 5.1 — WebSocket Policy Event Types**
- `broadcast_routing_decision(certificate_id, decision)` — global broadcast on certificate issuance
- `broadcast_coherence_gate_transition(certificate_id, transition)` — global broadcast on gate open/resolve
- `broadcast_tao_flow_alert(timeline_id, alert)` — global + channel broadcast when |net_inflow_24h| crosses 1000.0 threshold
- All broadcasts are fire-and-forget with try/except (WS failures don't block business logic)
- Hooked into: `theatre_bridge.py` (routing), `coherence_gate_evaluator.py` (gates), `tao_flow_aggregator.py` (flow)

**Task 5.2 — Feature Flag Removal**
- Removed: `CYCLE_017_DEPLOYABILITY_ROUTING`, `CYCLE_017_REGISTRY_SCHEMA`, `CYCLE_017_COHERENCE_GATES`
- Retained: `CYCLE_017_TAO_FLOW` (gates staged Alpamayo behaviour), `WEBSOCKET_REALTIME` (generic realtime gate)
- All gated UI now renders unconditionally: routing badges, coherence gate badges, legal review warnings, query determinism badges

**Task 5.3 — Type Migration**
- Deleted `frontend/src/types/cycle017.ts`
- `RoutingHint` already in `theatre.ts` (from Sprint 1)
- Added `GateStatus` type to `theatre.ts`
- Added `RoutingHint`, `GateStatus` to `index.ts` re-exports
- Zero imports from `cycle017.ts` remain

**Task 5.4 — Frontend Polish**
- `CertificatesPage`: routing hint conditionally rendered (`cert.routing_hint &&`), gate status conditionally rendered (`cert.coherence_gate_status &&`), deployable badge always shown
- `InvestigationPage`: legal review warning conditionally rendered (`investigation.has_legal_review_requirement &&`)
- `EvidenceEnvelopePanel`: query determinism badge conditionally rendered (`item.query_determinism &&`)

**Task 5.5 — E2E Test**
- Full lifecycle: certificate with REVIEW_REQUIRED routing → evaluator confirms review needed → gate opened (PENDING) → gate resolved (PASSED) → is_deployable = true
- Verifies all intermediate states and audit trail

**Task 5.6 — Grep Audit Results**
- Zero `isEnabled('CYCLE_017_DEPLOYABILITY_ROUTING')` in frontend/src: PASS
- Zero `isEnabled('CYCLE_017_REGISTRY_SCHEMA')` in frontend/src: PASS
- Zero `isEnabled('CYCLE_017_COHERENCE_GATES')` in frontend/src: PASS
- Zero imports from `cycle017.ts`: PASS
- `cycle017.ts` deleted: PASS
- `CYCLE_017_TAO_FLOW` retained (3 consumers): PASS
- `WEBSOCKET_REALTIME` retained (1 consumer): PASS

### Test Results

```
tests/test_c017_sprint5_ws_policy_e2e.py::test_routing_decision_broadcast PASSED
tests/test_c017_sprint5_ws_policy_e2e.py::test_coherence_gate_transition_broadcast PASSED
tests/test_c017_sprint5_ws_policy_e2e.py::test_tao_flow_alert_broadcast PASSED
tests/test_c017_sprint5_ws_policy_e2e.py::test_connection_manager_has_policy_methods PASSED
tests/test_c017_sprint5_ws_policy_e2e.py::test_e2e_policy_lifecycle PASSED

5 passed in 0.33s
```

### Acceptance Criteria Verification

- [x] All 3 WS event types broadcast correctly with payloads
- [x] Zero isEnabled calls for 3 removed flags in frontend/src
- [x] All 017 routing/registry/coherence UI renders unconditionally
- [x] CYCLE_017_TAO_FLOW and WEBSOCKET_REALTIME retained with clear comments
- [x] cycle017.ts deleted, all types on canonical files
- [x] Zero imports from cycle017.ts
- [x] Null-safe rendering for optional fields
- [x] Full lifecycle E2E test passes
- [x] Clean grep audit
