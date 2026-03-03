# Security Audit: Sprint 23 (Cycle-012, Sprint 1) -- Theatre Creation + Sponsor Onboarding + LMSR Wiring

> Auditor: Paranoid Cypherpunk | Date: 2026-03-03
> Decision: **APPROVED**

## Audit Summary

10 source files + 3 test files audited line-by-line. 53 sprint tests pass, 369 regression tests pass. All 12 security categories PASS. No secrets, no injection surfaces, no auth bypass, no state machine violations found.

## Test Results

- Sprint tests: **53 passed, 0 failed**
- Scoped regression (market + engines + osint): **369 passed, 0 failed**
- Total: **422 passed, 0 failed**

## Security Checklist (12 Categories)

| # | Category | Status | Analysis |
|---|----------|--------|----------|
| 1 | Secrets / Hardcoded Credentials | **PASS** | No API keys, tokens, passwords, or private keys in any source file. MockSepoliaClient is purely in-memory. BaseSepoliaClient takes credentials at runtime via constructor -- never stored in code. |
| 2 | Code Injection (eval/exec/subprocess) | **PASS** | Zero instances of `eval()`, `exec()`, `subprocess`, `os.system()`, `__import__()`, or `compile()` in any sprint file. |
| 3 | Input Validation | **PASS** | Pydantic v2 field constraints: `question` (min 10, max 500), `outcome_labels` (min 2, max 10, uniqueness enforced), `committed_sources` (min 1), `liquidity_b` (gt 0), `sponsor_id` (min 1). Source IDs validated against registry. `@field_validator` for uniqueness and max cap. |
| 4 | Auth / Access Control | **PASS** | No authentication implemented (expected -- in-memory MVP). Service injection via `set_service()` with 503 guard if unconfigured. State transitions enforced by MarketLifecycle (forward-only, exception on invalid). Double-commit blocked by `record.committed` flag + `ParameterMutationAfterCommit`. |
| 5 | Data Privacy / PII | **PASS** | `sponsor_metadata` is freeform dict but never logged, persisted, or transmitted. No PII collection. In-memory only. |
| 6 | Error Handling / Info Disclosure | **PASS** | FastAPI routes catch `ValueError` (400), `KeyError` (404), `ParameterMutationAfterCommit` (409). Error messages use `str(e)` which contains controlled strings from service layer, not stack traces. No raw exception propagation to client. |
| 7 | Dependency Safety | **PASS** | No new runtime dependencies. Uses only existing: Pydantic v2, FastAPI, stdlib (hashlib, uuid, random, dataclasses, json, math, enum, typing). |
| 8 | Path Traversal / File I/O | **PASS** | RegistryLoader takes a file path but is constructed at startup, not from user input. Source manifest builder receives source IDs (strings), not file paths. No user-controlled file paths anywhere in the sprint. |
| 9 | Integer Overflow / Float Safety | **PASS** | LMSR uses log-sum-exp trick preventing overflow. `math.fsum()` for precision. `canonical_json` rejects NaN/Infinity via `allow_nan=False` and explicit check. `Decimal` used for sponsor-facing `liquidity_b`, converted to `float` only at LMSR boundary. Trade shares validated non-zero. |
| 10 | Race Conditions | **PASS** | In-memory dict storage (`self._theatres`) is not thread-safe, but this is an in-memory MVP with no async/threaded access patterns. FastAPI default is synchronous endpoint handlers. No persistent state to corrupt. Acceptable for current architecture. |
| 11 | Supply Chain | **PASS** | No new packages. No external HTTP calls. No CDN dependencies. MockSepoliaClient is self-contained. |
| 12 | API Security | **PASS** | FastAPI router with proper prefix (`/api/v1/sponsored-theatres`). Pydantic v2 request body validation (automatic via FastAPI). Status codes correct (201/200/400/404/409/503). No SQL (in-memory only). `theatre_id` is a path parameter validated as string -- UUID-based generation prevents injection. |

## Specific Security Concerns -- Detailed Analysis

### 1. Pydantic Validation Bypass

**VERDICT: NOT EXPLOITABLE**

`SponsoredTheatreConfig` uses Pydantic v2 `BaseModel` with `Field()` constraints. FastAPI auto-validates request bodies via Pydantic. Malformed JSON produces a 422 Unprocessable Entity with field-level errors (standard Pydantic behavior). I verified:
- `min_length` / `max_length` on `question`: enforced
- `gt=Decimal("0")` on `liquidity_b`: enforced, rejects 0 and negatives
- `min_length=1` on `committed_sources`: enforced, rejects empty list
- `min_length=2` on `outcome_labels`: enforced, rejects single outcome
- `@field_validator` for uniqueness: raises `ValueError` on duplicates
- `@field_validator` for max 10: raises `ValueError` on >10 outcomes
- Type coercion: Pydantic v2 strict mode is not enabled, but all fields have explicit types. A string where Decimal is expected will raise `ValidationError`.

### 2. State Machine Integrity

**VERDICT: NOT EXPLOITABLE**

Phase transitions are enforced in `MarketLifecycle` with explicit phase checks:
- `commit()`: requires `phase == CREATED`, else `InvalidPhaseTransition`
- `open_trading()`: requires `phase == COMMITTED`, else `InvalidPhaseTransition`
- `begin_resolution()`: requires `phase == TRADING`, else `InvalidPhaseTransition`
- `settle()`: requires `phase == RESOLVING`, else `InvalidPhaseTransition`

The bridge's `transition_market()` only accepts `COMMITTED` and `TRADING` targets, with an explicit `InvalidPhaseTransition` for anything else. Cannot skip states. Cannot reverse. Cannot go CREATED -> TRADING directly (tested and verified in `test_invalid_transition_raises`).

### 3. Commitment Hash Manipulation

**VERDICT: NOT EXPLOITABLE**

Theatre commitment hash uses SHA-256 over canonical JSON (RFC 8785). The `canonical_json()` implementation:
- Sorts keys lexicographically at every depth
- Rejects NaN/Infinity (raises `ValueError`)
- Normalizes floats (1.0 -> 1)
- No whitespace
- `committed_sources` explicitly sorted before hashing

Re-computation at commit time verifies the hash has not drifted. Two different source orderings produce the same hash (verified in `test_committed_sources_sorted_in_hash`). Collision requires SHA-256 preimage attack (computationally infeasible).

One note: the theatre-level hash and the LMSR-level hash cover overlapping but different parameter sets. The theatre hash includes `oracle_config` and `theatre_metadata` that the LMSR hash does not. Both are independently verified. This is correct design.

### 4. Stub Agent Exploitation

**VERDICT: NOT EXPLOITABLE (ACCEPTABLE RISK)**

Stub agents are deterministic with `random.Random(seed + tick)` per-tick RNG. Strategies:
- All use positive share amounts (1-50 range)
- No strategy can produce negative shares (no selling)
- TradingEngine validates non-zero shares, outcome index bounds, balance sufficiency, and phase
- Swallowed exception at line 141-143 means a failed trade is silently skipped -- this is logged as an advisory (the engineer feedback already flagged this). No exploit vector: the exception is from TradingEngine validation (insufficient balance, halted market, etc.), not from security-critical code.

The agents are throwaway code (Cycle-013 replaces them). Acceptable.

### 5. FastAPI Route Injection

**VERDICT: NOT EXPLOITABLE**

- No SQL anywhere (in-memory dict storage)
- `theatre_id` is a path parameter (string). Used as dict key in `self._theatres.get(theatre_id)`. Dict key lookup cannot inject code.
- Theatre IDs are generated server-side as `theatre_{uuid.uuid4().hex[:12]}` -- never from user input during creation.
- The `/{theatre_id}/review` and `/{theatre_id}/commit` endpoints accept arbitrary strings but simply look up in a dict. Nonexistent IDs return 404.
- No path traversal: no file I/O from theatre_id.

### 6. Unbounded Share Amounts

**VERDICT: NOT EXPLOITABLE**

TradingEngine validates:
- `shares == 0.0` rejected
- Balance check: `cost > available` raises `InsufficientBalance`
- Sell check: `held < required` raises `InsufficientShares`

Negative shares are handled (sell path). Extremely large positive shares are bounded by agent balance. The LMSR cost function uses log-sum-exp which is numerically stable for large x values. No division by zero possible (`b > 0` enforced at market creation).

Float edge cases: `math.exp()` could overflow for astronomically large `x/b` ratios, but the log-sum-exp trick subtracts the max, keeping exponents near 0. Practically infeasible to trigger overflow through normal trading.

### 7. Double-Commit Attack

**VERDICT: NOT EXPLOITABLE**

`SponsoredTheatreService.commit()` checks `record.committed` flag first. If already committed, raises `ParameterMutationAfterCommit`. Verified in `test_double_commit_raises_mutation_error`. The flag is set atomically (single-threaded in-memory operation). No TOCTOU race possible in the current synchronous architecture.

## Advisory Notes (Non-Blocking)

### ADV-1: Unused Imports (Cosmetic)

6 unused imports across 4 files (already flagged by engineer feedback). Not a security concern.

### ADV-2: Swallowed Exception in stub_agents.py:141-143

```python
except Exception:
    pass
```

Broad `except Exception` catch. In production code this would be a finding. For throwaway stub agents being replaced in Cycle-013, acceptable. The engineer already noted this.

### ADV-3: Global Mutable State in Routes

`_service = None` at module level in `sponsored_theatre_routes.py` is global mutable state. In a multi-worker deployment (e.g., gunicorn with prefork), each worker gets its own copy, which is correct. No security issue, but worth noting for future architecture.

### ADV-4: theatre_id Collision (Theoretical)

`uuid.uuid4().hex[:12]` gives 48 bits of entropy (~281 trillion possible values). Birthday paradox: collision probability is negligible at expected scale. Not a practical concern.

### ADV-5: sponsor_metadata Unbounded Size

`sponsor_metadata: dict[str, Any]` has no size limit. A malicious sponsor could submit a very large dict. In production, add a max size constraint. For in-memory MVP, acceptable.

## Files Audited

| File | Lines | Verdict |
|------|-------|---------|
| `backend/schemas/sponsored_theatre.py` | 93 | CLEAN |
| `backend/osint/source_manifest.py` | 162 | CLEAN |
| `backend/services/sponsored_theatre.py` | 327 | CLEAN |
| `backend/services/market_theatre_bridge.py` | 181 | CLEAN |
| `backend/services/stub_agents.py` | 325 | CLEAN (1 advisory) |
| `backend/api/sponsored_theatre_routes.py` | 99 | CLEAN |
| `backend/services/__init__.py` | 1 | CLEAN |
| `backend/services/tests/__init__.py` | 1 | CLEAN |
| `backend/api/__init__.py` | 4 | CLEAN |
| `backend/services/tests/test_sponsored_theatre.py` | 437 | CLEAN |
| `backend/services/tests/test_market_theatre_bridge.py` | 172 | CLEAN |
| `backend/services/tests/test_stub_agents.py` | 397 | CLEAN |

## Dependency Files Reviewed (Not Modified by Sprint)

| File | Purpose |
|------|---------|
| `backend/market/lifecycle.py` | Phase transitions -- verified forward-only |
| `backend/market/commitment.py` | LMSR commitment hash -- verified SHA-256 + canonical JSON |
| `backend/market/state.py` | MarketState/MarketPhase -- verified enum integrity |
| `backend/market/trading.py` | TradingEngine -- verified validation chain |
| `backend/market/lmsr.py` | LMSR cost function -- verified log-sum-exp stability |
| `backend/market/exceptions.py` | Exception types -- verified no info leakage |
| `backend/chain/sepolia.py` | MockSepoliaClient -- verified no real chain interaction |
| `backend/osint/models/registry.py` | RegistryLoader -- verified no path traversal |
| `theatre/engine/canonical_json.py` | RFC 8785 canonical JSON -- verified NaN/Inf rejection |

## Verdict

**APPROVED.** Zero security findings. Five non-blocking advisory notes, all pre-existing or acceptable for in-memory MVP architecture. State machine is sound. Commitment protocol is deterministic and collision-resistant. Input validation is comprehensive. No injection surfaces.
