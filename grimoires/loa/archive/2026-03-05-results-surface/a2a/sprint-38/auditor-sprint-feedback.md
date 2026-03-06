# Sprint 2 (sprint-38) — Security & Quality Audit

## Verdict: APPROVED

**Auditor**: Paranoid Cypherpunk Auditor
**Date**: 2026-03-05
**Files Reviewed**: 17 implementation files + 1 test file + 2 modified files (all read in full)

---

## Security Checklist Results

### 1. Secrets — PASS

No hardcoded API keys, tokens, credentials, or secrets found in any file. The API client (`frontend/src/api/client.ts`) uses environment variable `VITE_API_URL` for the base URL and retrieves auth tokens from `localStorage` at runtime — no secrets baked into source.

### 2. Injection — PASS

- **SQL Injection**: Not applicable — in-memory `dict` store, no database queries in investigation routes.
- **Command Injection**: No subprocess calls, no `os.system`, no `exec`/`eval` anywhere in the new code.
- **Template Injection**: No string formatting used in dangerous contexts. FastAPI's Pydantic models handle serialization.

### 3. Input Validation — PASS

All backend endpoints use Pydantic `BaseModel` request schemas (`InvestigationCreateRequest`, `EvidenceSubmitRequest`, `ClaimCreateRequest`, `CounterSignalCreateRequest`). Fields are typed with defaults. Enum conversion via `ProvenanceClass(request.provenance_class)`, `ClaimType(request.claim_type)`, `InvestigationCounterSignalClass(request.signal_class)` will raise `ValueError` on invalid values, which FastAPI converts to 422 Unprocessable Entity — no raw user input passes through unvalidated.

### 4. Auth/Authz — NOTED (Acceptable)

No authentication decorators or dependency injection on the investigation endpoints. The frontend `apiClient` does attach Bearer tokens, and the backend has OAuth2 infrastructure in `main.py`. However, the investigation routes do not enforce auth. This is **acceptable for the current stage**: the implementation report explicitly states this is an in-memory prototype with no persistence. Auth gating is a future production concern, not a sprint-38 blocker.

**Recommendation for future**: Add `Depends(get_current_user)` before these routes go to production.

### 5. Data Privacy — PASS

No PII handling in investigation data. Content is submitted as base64-encoded bytes and stored as hashes — the actual content is hashed by `submit_evidence()`, not stored raw. Entity profiles display jurisdiction and registration numbers which could be sensitive, but the `EntityProfilePanel` is a read-only display component with no export/logging of data.

### 6. Error Handling — PASS (with minor note)

- 404 errors use `HTTPException(status_code=404, detail=f"Investigation {investigation_id} not found")`. This echoes the user-supplied investigation ID back in the error message. This is **LOW severity** — it's the same ID the client sent, so no information disclosure beyond what the caller already knows.
- No stack traces leaked. FastAPI's default error handling converts unhandled exceptions to 500 with generic JSON.
- The `base64.b64decode()` on line 248 of `investigation_routes.py` could raise `binascii.Error` on malformed base64 input. FastAPI will convert this to a 500 Internal Server Error. **INFO-level concern** — ideally this would be wrapped in a try/except returning 422, but it is not exploitable.

### 7. XSS — PASS

- **No `dangerouslySetInnerHTML`** found in any investigation component (verified via grep).
- All user-supplied text (claim text, resolution impact, source descriptions, entity names) is rendered via React's default JSX escaping — `{variable}` in JSX automatically escapes HTML entities.
- Hash values are truncated via `.substring()` — safe string operation.
- `JSON.stringify()` is used for `stop_config` display in `InvestigationCertificateView.tsx` and `profile.data` in `EntityProfilePanel.tsx` — both safe as React escapes the output.

### 8. SSRF — PASS

The frontend API client constructs URLs via template literals with `investigationId` parameters (e.g., `` `/api/v1/investigations/${investigationId}` ``). The `investigationId` is selected from a server-returned list (`inv.id` from the investigations list response), not from arbitrary user input like URL params or form fields. The `apiClient` uses a fixed `baseURL` from environment. No SSRF risk.

### 9. Information Disclosure — PASS

- Error responses use FastAPI's standard error format — no internal paths, stack traces, or system info leaked.
- The `main.py` router wiring uses try/except with `traceback.print_exc()` — this prints to server stdout/stderr only, not to HTTP responses.
- Development console logging in `client.ts` is gated behind `import.meta.env.DEV`.

---

## Quality Findings

### Q1: Defensive Coding — GOOD

- All frontend components handle empty/null states gracefully (empty array checks, null profile checks).
- React Query hooks use `enabled: !!investigationId` to prevent null-dereference API calls.
- `staleTime` and `refetchInterval` are sensibly configured — no excessive polling.

### Q2: Type Safety — GOOD

- Frontend types in `investigation.ts` are fully typed with no `any` usage.
- Backend Pydantic models enforce types on both request and response paths.
- Enum `.value` is used consistently to serialize Python enums to string values.

### Q3: Test Coverage — ADEQUATE

- 10 backend tests covering all 11 endpoints plus 404 error cases.
- 27 frontend tests across 6 test files.
- Backend tests cannot run (known blocker: python3.14 venv broken) — structurally correct per code review.

### Q4: Router Integration — CORRECT

- `backend/main.py` lines 360-368: Investigation router wired with try/except guard — consistent with existing router pattern.
- `frontend/src/router.tsx` line 77-83: Route wrapped in `ErrorBoundary` — consistent with all other routes.

---

## Informational Notes (Not Blocking)

| ID | Severity | File | Note |
|----|----------|------|------|
| I-1 | INFO | `investigation_routes.py:248` | `base64.b64decode()` could raise `binascii.Error` on malformed input, resulting in 500 instead of 422. Recommend wrapping in try/except. |
| I-2 | INFO | `investigation_routes.py:50` | 404 detail echoes user-supplied ID back. Benign since it is the same ID the caller sent. |
| I-3 | INFO | `investigation_routes.py:224` | Accesses private attribute `toolset._config`. Acceptable for in-memory prototype but would be a code smell in production. |
| I-4 | INFO | `EvidenceEnvelopePanel.tsx:95` | The `.replace('/20', '/60')` string manipulation for dynamic color intensity is clever but fragile — would break if Tailwind class format changes. |
| I-5 | INFO | All routes | No authentication enforcement. Acceptable for prototype; must be added before production deployment. |

---

## Final Assessment

The implementation is **clean, well-structured, and free of exploitable security vulnerabilities**. All 17 new files and 2 modified files pass the 9-point security checklist. The code follows consistent patterns established in prior sprints. The 5 informational notes are quality improvements for future hardening, none of which block approval.

**APPROVED** — No changes required.
