# Security Audit: Sprint 24 (Cycle-012, Sprint 2) -- Resolution + Settlement + Certificate Delivery

> Auditor: Paranoid Cypherpunk | Date: 2026-03-03
> Decision: **APPROVED**

## Pre-flight Verification

| Check | Status | Detail |
|-------|--------|--------|
| Ledger mapping | PASS | sprint-2 (local) = global sprint-24, cycle-012 "Sponsored Theatre End-to-End" |
| Engineer feedback | PASS | Senior Technical Lead: "All good" -- 452 tests passing |
| Reviewer report | PASS | 10 tasks, 30 new tests, 6 new source + 1 modified + 3 test files |

**NOTE**: A COMPLETED marker and stale auditor-sprint-feedback.md existed from a different sprint (sprint-3 of a prior cycle, dated 2026-02-19). Both were incorrect and have been replaced by this proper audit.

## Test Results (Independently Verified)

```
Sprint 2 + all services/schemas:   83 passed, 0 failed
Scoped regression (market/engines/osint): 369 passed, 0 failed
Total:                              452 passed, 0 failed
```

## Files Audited (10 total)

| File | Lines | Verdict |
|------|-------|---------|
| `backend/services/theatre_evidence.py` (NEW) | 113 | CLEAN |
| `backend/services/theatre_resolution.py` (NEW) | 189 | CLEAN |
| `backend/services/certificate_pipeline.py` (NEW) | 335 | CLEAN |
| `backend/services/rlmf_export.py` (NEW) | 227 | CLEAN |
| `backend/services/sponsor_delivery.py` (NEW) | 141 | CLEAN |
| `backend/services/theatre_status.py` (NEW) | 137 | CLEAN |
| `backend/engines/paradox.py` (MODIFIED) | 246 | CLEAN (MEDIUM-1 fix only) |
| `backend/services/tests/test_theatre_resolution.py` (NEW) | 378 | CLEAN |
| `backend/services/tests/test_certificate_pipeline.py` (NEW) | 295 | CLEAN |
| `backend/services/tests/test_sponsored_theatre_e2e.py` (NEW) | 799 | CLEAN |

## Security Checklist (12 Categories)

### 1. Secrets / Hardcoded Credentials

**PASS** -- No secrets, API keys, tokens, passwords, or credentials found in any Sprint 2 file. Grep for `password|secret|api_key|token|private_key|credential` across `backend/services/*.py` returned zero hits in Sprint 2 files (one hit in pre-existing `verification_bridge.py` which handles `github_token` at runtime, not persisted -- outside Sprint 2 scope).

### 2. Code Injection (eval/exec/subprocess)

**PASS** -- No `eval()`, `exec()`, `subprocess`, `os.system()`, `__import__()`, or `compile()` calls in any Sprint 2 file. The only `re.compile()` hit is a benign regex pattern for oracle_output_id validation (line 137, `certificate_pipeline.py`).

### 3. Input Validation

**PASS** -- `theatre_resolution.py` validates `n_outcomes`, `outcome_labels`, and `composite_score` ranges. Certificate pipeline runs 21 validation checks. The `_determine_winning_outcome()` method handles edge cases: `score >= 1.0 -> 0`, `score = 0.0 -> n-1`, and `min(idx, n_outcomes-1)` prevents index overflow. Division by zero guarded in `compute_coverage_pct()` (line 101) and `compute_brier_score()` (line 172).

### 4. Auth / Access Control

**N/A** -- In-memory MVP with no authentication layer. All operations are local function calls. The `echelon://status/{theatre_id}` URL is a protocol identifier, not a live endpoint. No HTTP listeners or network access in Sprint 2 code.

### 5. Data Privacy / PII

**PASS** -- No personal data processed. `sponsor_id` and `sponsor_metadata` are opaque identifiers. Agent IDs are synthetic (`stub_agent_0` through `stub_agent_5`). No logging of user data.

### 6. Error Handling / Info Disclosure

**PASS** -- Errors raise standard Python exceptions (`ValueError`, `TypeError`). No stack traces exposed to external callers. No debug logging with sensitive context. The `build_theatre_status()` function raises `ValueError` for unknown theatre_id (line 71) -- appropriate for an internal API.

### 7. Dependency Safety

**PASS** -- All imports are from existing project modules (`backend.osint`, `backend.market`, `backend.engines`, `backend.services`, `theatre.engine`) or Python stdlib (`hashlib`, `json`, `re`, `math`, `datetime`, `dataclasses`). No new third-party dependencies introduced.

### 8. Path Traversal / File I/O

**PASS** -- Zero file I/O in any Sprint 2 source file. No `open()`, `os.path`, `pathlib`, or `Path()` usage. All data is in-memory. Test files use `tempfile.mkstemp()` for temporary registry files, which are properly cleaned up via `os.unlink()` in fixtures.

### 9. Integer Overflow / Float Safety

**PASS** -- Brier score: `(1/n) * sum((p_i - o_i)^2)` -- values bounded to [0.0, 2.0] for each term, guarded against n=0 (returns 1.0). ECE: `bin_idx = min(int(p * n_bins), n_bins - 1)` prevents index overflow. Composite score explicitly validated in range [0.0, 1.0] by check 3. No integer arithmetic that could overflow on 64-bit Python.

### 10. Race Conditions

**N/A** -- Single-threaded in-memory execution. No shared mutable state accessed from concurrent threads or processes. The `_snapshots` list in `TheatreEvidenceCollector` is only accessed sequentially within the same execution path.

### 11. Supply Chain

**PASS** -- No new runtime dependencies. No dynamic imports. No code downloaded or executed at runtime. All modules are local project code.

### 12. Certificate Integrity

**PASS with ADVISORY** -- See detailed analysis below.

## Specific Security Concern Analysis

### Concern 1: Certificate Forgery -- Can the 21 echelon_verify checks be bypassed?

**VERDICT: LOW RISK (acceptable for v1.0.0)**

All 21 checks are implemented and run within `CertificatePipeline.verify()`. The checks validate:
- Structural integrity (checks 1-9, 12-14, 16, 20): field presence, types, cardinalities
- Cryptographic integrity (checks 4-5, 17-18): SHA-256 hex validation
- Semantic integrity (checks 3, 10-11, 15, 19): score ranges, ISO 8601, index validity
- Deterministic serialisation (check 21): canonical JSON roundtrip

**ADVISORY SEC-1**: Check 5 ("evidence_bundle_hash recomputable") degrades to the same hex validity check as Check 4. True recomputation requires access to original evidence bundles, which the verifier does not have. This is documented in the code (line 152 comment). A standalone verifier or third-party auditor would need the original bundles to verify the hash independently. Acceptable for in-memory MVP; should be addressed when evidence bundles are persisted.

**ADVISORY SEC-2**: Check 19 ("winning_outcome is valid index") only validates `>= 0`, not `< n_outcomes`. The certificate schema does not carry `n_outcomes`, so the upper bound cannot be validated without external context. The `winning_outcome_label` serves as an implicit sanity check. Low risk -- an attacker would also need to forge the `winning_outcome_label` to be consistent.

### Concern 2: Resolution Manipulation -- Can scoring thresholds be gamed?

**VERDICT: LOW RISK**

The `_determine_winning_outcome()` method uses hardcoded thresholds for the 3-outcome Companies House Theatre:
- `>= 0.7` -> outcome 0 ("Filed on time")
- `>= 0.3` -> outcome 1 ("Filed late")
- `< 0.3` -> outcome 2 ("Not filed")

These thresholds are NOT configurable at runtime and NOT derived from user input. They are compiled into the static method. To manipulate the outcome, an attacker would need to:
1. Alter the composite_score output from the Scorer (which is derived from evidence bundles and corroboration), OR
2. Modify the threshold constants in source code

The corroboration penalty (0.7x) is also hardcoded. The Scorer's output depends on real evidence bundle data. No external API accepts user-specified scores.

Boundary tests confirm: `score=0.7 -> outcome 0` and `score=0.3 -> outcome 1` (inclusive at lower bounds).

### Concern 3: RLMF Data Poisoning

**VERDICT: LOW RISK**

RLMF export captures agent decision traces, epoch prices, and calibration metrics from the in-memory Theatre lifecycle. The data flows are:
- `MarketEpoch` captures `prices` and `x_vector` directly from `LMSREngine.prices()` -- no user input
- `AgentTrace` captures decisions from `StubAgentSpawner.execute_tick()` -- deterministic with seed
- `CalibrationMetrics` computed from final prices and known winning outcome
- `agent_pnl` derived from `SettlementReport.agent_settlements`

No external input enters the RLMF export pipeline. All data originates from the internal market state. An attacker would need to compromise the LMSR engine itself.

### Concern 4: MEDIUM-1 Fix Completeness

**VERDICT: COMPLETE AND CORRECT**

The fix adds a 3-line guard (lines 102-107 of `paradox.py`):
```python
if signal.p_reality is None:
    return None
```

Analysis of the call chain:
1. `ParadoxEngine.scan()` calls `reality_provider.get_signal(theatre_id)` (line 100)
2. `RealitySignal.p_reality` is typed as `float | None` (confirmed in `reality_signal.py` line 24)
3. `LiveOSINTRealityProvider.get_signal()` returns `p_reality=None` when evidence is stale (line 223)
4. Without the guard, `LogicGapCalculator.compute(theatre_id, signal.p_reality)` would call `abs(p_market - None)` -> `TypeError`
5. The guard returns `None`, which is semantically correct: `scan()` already returns `None` for disabled mode (line 91) and ungated state (line 97)

**No remaining crash vectors**: `p_reality` is only consumed at line 110. The guard at line 106 intercepts all `None` values before they reach `compute()`. The `LogicGapCalculator.compute()` method itself is NOT modified -- the fix is placed at the caller, which is the correct location.

All 369 existing engine/market/osint tests pass, confirming zero regression.

### Concern 5: Settlement Integrity -- Can winning outcome be changed after commitment?

**VERDICT: SECURE**

The `commitment_hash` is generated during `SponsoredTheatreService.create()` and verified during `commit()`. After commitment:
- The market parameters (b, n_outcomes, outcome_labels, fee_schedule) are frozen in the `Market` dataclass
- `SettlementReport.commitment_hash` is carried through to the certificate
- `SettlementReport.settlement_hash` is computed from canonical JSON of the settlement composite
- Both hashes are SHA-256 and validated by certificate checks 17 and 18
- The `winning_outcome` flows through: `resolution_result.winning_outcome_index` -> `ResolutionEngine.settle()` -> `SettlementReport.winning_outcome` -> `CalibrationCertificate.winning_outcome`

There is no API to modify `winning_outcome` after `resolve()` returns. The settlement is a one-shot operation.

### Concern 6: Delivery Package Tampering

**VERDICT: LOW RISK**

The `SponsorDeliveryPackage` is assembled from:
- `certificate`: serialised via `CertificatePipeline.certificate_to_dict()` -- deterministic
- `evidence_bundle`: built from `EvidenceSnapshot` list -- in-memory, no external modification
- `rlmf_export`: serialised via `_rlmf_to_dict()` -- deterministic
- `commitment_hash`: passed through from settlement

The package is assembled in a single function call with no intermediate persistence. There is no API to modify individual fields after assembly. The package contains the `commitment_hash` which ties it back to the committed parameters, and the certificate contains `settlement_hash` which ties it to the settlement outcome.

For production use, the delivery package should be signed or its hash recorded on-chain. Currently it is in-memory only, so tampering requires code-level access.

## Additional Observations

### OBS-1: Private Attribute Access in `theatre_evidence.py`

Line 63: `cached = getattr(self._reality_provider, '_last_output', {})` accesses a private attribute of the reality provider. This is fragile -- if the provider implementation changes the attribute name, the evidence collector silently degrades (returns empty evidence). The `getattr` with default `{}` prevents a crash but could mask bugs.

Similarly, `theatre_status.py` line 92 accesses `evidence_collector._committed_sources` (private attribute).

**Risk**: Low. Both are acceptable for in-memory MVP. Should be replaced with proper public interfaces when the code evolves.

### OBS-2: Counter-Signal Padding in `certificate_pipeline.py`

Lines 324-334: `_build_counter_signal_results()` pads to exactly 11 entries using `COUNTER_SIGNAL_CLASSES`. If `COUNTER_SIGNAL_CLASSES` is ever extended beyond 11, the `results[:11]` truncation would silently drop counter-signal results. Conversely, if reduced below 11, the certificate would have fewer than 11 entries and check 12 would fail.

**Risk**: Low. The `COUNTER_SIGNAL_CLASSES` list has exactly 11 entries and is unlikely to change without a schema version bump.

### OBS-3: ECE Single-Event Degenerate Case

`rlmf_export.py` lines 196-226: The ECE computation treats every epoch as observing the same resolved event (actual_freq = 1.0 always). This is a known limitation of single-market ECE. The code comment (not visible in exported RLMF) documents this. True calibration requires aggregation across multiple markets. The raw epoch data is exported so downstream systems can compute multi-market ECE.

**Risk**: None. This is a documented limitation, not a security concern.

### OBS-4: Unused Imports (Cosmetic)

Carried from Sprint 1. Four files have unused imports:
- `theatre_evidence.py`: `import time`, `Optional`
- `theatre_resolution.py`: `import hashlib`, `import time`, `Optional`
- `rlmf_export.py`: `Optional`
- `theatre_status.py`: `Optional`

All `Optional` imports are unnecessary because `from __future__ import annotations` enables `X | None` syntax.

**Risk**: None. Cosmetic only.

## Constraint Compliance

| Constraint | Status | Evidence |
|-----------|--------|----------|
| Zero modifications to `backend/market/` | PASS | No Sprint 2 files in `backend/market/` |
| Zero modifications to `backend/osint/` | PASS | No Sprint 2 files in `backend/osint/` |
| Zero modifications to `backend/chain/` | PASS | No Sprint 2 files in `backend/chain/` |
| Only `backend/engines/paradox.py` modified in engines | PASS | MEDIUM-1 fix only |
| `from __future__ import annotations` in all files | PASS | All 6 new source files verified |
| No new runtime dependencies | PASS | Only stdlib + existing deps |
| In-memory only | PASS | No database tables or persistent storage |
| Mock-only OSINT testing | PASS | No real HTTP calls in any test |
| Python 3.9.6 compatibility | PASS | `from __future__ import annotations` enables `X | None` syntax |

## Verdict

**APPROVED.** All 10 tasks meet acceptance criteria. 83 service/schema tests pass. 369 scoped regression tests pass (452 total). No security findings above LOW risk. The certificate pipeline implements all 21 echelon_verify checks. The MEDIUM-1 fix is minimal, correct, and complete. Two advisory notes on certificate verification depth (SEC-1, SEC-2) are acceptable for v1.0.0 in-memory MVP. Four observational notes (OBS-1 through OBS-4) are non-blocking.
