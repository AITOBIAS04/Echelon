# Codex Baseline Remediation 013 — v2

**Date:** 3 March 2026  
**Cycle status:** Cycle-013 currently in Sprint 2  
**Replaces:** v1 (archived)  
**Scope:** Tracked baseline only (post-012, cycle-013 in progress excluded)

---

## Corrections Applied vs v1

1. Cycle-005 expansion target corrected to **160+ sources (v1.0.0)**, not 57.
2. Planning metadata inconsistency moved from "resolved" to **open baseline drift**.
3. Commitment mismatch guidance tightened: **do not lower standards by hardcoding 1**; source commitment parameters from config.
4. MCP drift expanded: includes **transport contract mismatch** (not just missing auth/scope/rate-limit).
5. Added explicit release gates for 013 Sprint 3 certificate-validity requirements.

---

## 013 Release Gates

## Gate A — Must Fix Before End of 013 Sprint 2

### A1) Commitment hash/runtime parameter parity
**Files:** `backend/services/sponsored_theatre.py`, `backend/services/tests/test_sponsored_theatre_e2e.py`, `backend/services/tests/test_theatre_resolution.py`  
**Issue:** Commitment encodes `corroboration_minimum=1` while runtime/tests use `2`.  
**Risk:** Committed parameters differ from resolved parameters; certificate/audit integrity breaks.  
**Required fix:** Remove hardcoded value and derive commitment oracle params from the same theatre config object used by resolution.

### A2) Commit semantics consistency
**Files:** `backend/services/sponsored_theatre.py`  
**Issue:** `commit()` transitions to `TRADING` but returns status `COMMITTED`.  
**Risk:** Agent/runtime orchestration cannot reliably distinguish pre-trade vs live-trade state.  
**Required fix:** Either:
- Implement true two-step transition (`COMMITTED` then explicit open-trading), or
- Keep atomic transition and return/emit `TRADING` consistently with docs/tests.

---

## Gate B — Must Fix Before 013 Sprint 3 E2E/Certificate Sign-off

### B1) Settlement audit transition integrity
**Files:** `backend/api/theatre_routes.py`  
**Issue:** `from_state` captured after mutation (`RESOLVED` -> `RESOLVED`).  
**Risk:** Audit trail invalid for state transition verification.  
**Required fix:** Capture `from_state` before mutating state.

### B2) Tier enum canonicalization
**Files:** `backend/services/certificate_pipeline.py`, `docs/schemas/echelon_certificate_schema.json`  
**Issue:** Verifier allows `VERIFIED`; schema/system model uses `PROVEN`.  
**Risk:** Inconsistent tier semantics across cert generation, validation, and consumers.  
**Required fix:** Canonical enum = `UNVERIFIED | BACKTESTED | PROVEN` everywhere.

### B3) Mock-adapter certificate bypass
**Files:** `theatre/engine/template_validator.py`, `backend/api/theatre_routes.py`, `backend/services/theatre_bridge.py`  
**Issue:** Rule exists (`mock` blocked for certificate runs) but API path validates with non-certificate mode and runtime defaults to mock anyway.  
**Risk:** Certificate generated from mock path without explicit policy acknowledgment.  
**Required fix:** Enforce certificate-run validation at run-time boundary OR add explicit local-mode policy flag that marks outputs as non-promotable.

---

## Gate C — Must Fix Before Public MCP Exposure

### C1) MCP auth/scope/rate-limit not implemented
**Files:** `mcp/server.py`; missing `mcp/auth.py` / security layer  
**Issue:** Tool dispatch has no bearer/scope enforcement.

### C2) MCP HTTP transport contract drift
**Files:** `mcp/http.py`, `mcp/tools/status.py`  
**Issue:** HTTP currently uses JSON-RPC via `POST /mcp`; expected contract is plain JSON tool input endpoint shape from cycle context.

**Risk (C1+C2):** External consumers integrate against unstable/incomplete surface; security and contract breakage.

---

## Open Baseline Drift (Non-Blocking for 013 Sprint 2)

### D1) `/theatres/{id}/run` not executing real Product Theatre flow
**Files:** `backend/api/theatre_routes.py`, `backend/services/theatre_bridge.py`  
**Issue:** Falls back to mock adapter and empty ground-truth list.

### D2) Runtime registry scope remains WM-only
**Files:** `backend/osint/sources.json`, `backend/osint/tests/test_registry_loader.py`  
**Issue:** Runtime loader/tests intentionally pinned to 3 WM sources; broader cycle-005 registry (160+) not active in this path.

### D3) Planning metadata inconsistency
**Files:** `grimoires/loa/context/echelon_platform_roadmap.md`, `grimoires/loa/ledger.json`, `grimoires/loa/context/README.md`  
**Issue:** Active-cycle/state-of-truth documentation remains inconsistent in tracked baseline.

---

## Corrected Context Notes

- **Cycle-005 target:** Intelligence DB expansion to **160+ sources (v1.0.0)**.
- **Current baseline test run:** `513 passed` (excluding `mcp/tests/test_http.py` in restricted environment).

---

## Recommended Execution Order (013)

1. Fix A1 (commitment parameter parity).  
2. Decide and implement A2 semantics (or document atomic model and align all outputs).  
3. Apply B1 + B2 (fast correctness fixes).  
4. Resolve B3 policy/enforcement before certificate sign-off.  
5. Defer D1/D2 unless 013 scope requires Product Theatre `/run` path or non-WM expansion.  
6. Track C1/C2 under explicit MCP hardening ticket before public exposure.

---

## Archive

v1 moved to:  
`echelon core arch/implement/archive/codex_baseline_remediation_013_v1_2026-03-03.md`
