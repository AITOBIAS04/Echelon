# Security Audit — Sprint 26 (Execution Engine)

> Auditor: Paranoid Cypherpunk Auditor
> Sprint: sprint-26 (global) | sprint-2 (local)
> Cycle: cycle-031 — Theatre Template Engine
> Date: 2026-02-20

## Verdict: APPROVED - LETS FUCKING GO

---

## Security Checklist

### 1. Secrets & Credentials
| Check | Status | Notes |
|-------|--------|-------|
| No hardcoded secrets | PASS | Zero matches for password/secret/api_key/token/credential patterns |
| No API keys in code | PASS | |
| No private keys | PASS | |
| No .env references | PASS | |

### 2. Dangerous Imports & Code Execution
| Check | Status | Notes |
|-------|--------|-------|
| No `eval()` / `exec()` | PASS | |
| No `subprocess` | PASS | |
| No `pickle` / `marshal` | PASS | |
| No `os.system` | PASS | |
| No `__import__` | PASS | |
| No `compile()` | PASS | |

### 3. Input Validation
| Check | Status | Notes |
|-------|--------|-------|
| Pydantic models validate all inputs | PASS | All external data enters through Pydantic BaseModel |
| Status fields use Literal types | PASS | No arbitrary strings in status enums |
| OracleInvocationMetadata has sane defaults | PASS | timeout=30, retry=2, backoff=5.0 |
| TheatreCriteria weight validation | PASS | Sum-to-1.0 check, keys-subset check (from sprint-1) |

### 4. Injection Vulnerabilities
| Check | Status | Notes |
|-------|--------|-------|
| No SQL in engine code | PASS | Engine is pure Python — no database queries |
| No raw string interpolation in queries | PASS | N/A — no DB access in sprint-2 |
| No template rendering | PASS | |
| JSON serialisation via `json.dumps` | PASS | Safe — no injection vector |

### 5. File I/O Security
| Check | Status | Notes |
|-------|--------|-------|
| EvidenceBundleBuilder path construction | INFO | See finding F-001 |
| All paths relative to `base_dir` | PASS | Paths built via `self._base_dir / subdir / filename` |
| No user-controlled absolute paths | PASS | `output_dir` is passed programmatically, not from HTTP |
| JSONL append mode (`"a"`) | PASS | Correct for audit trail and per-episode scores |

### 6. Cryptographic Integrity
| Check | Status | Notes |
|-------|--------|-------|
| SHA-256 for all hashes | PASS | commitment, dataset, bundle — all hashlib.sha256 |
| No MD5 or SHA-1 | PASS | |
| Canonical JSON for determinism | PASS | All hash inputs go through canonical_json() |
| No HMAC needed (no shared secrets) | PASS | Commitment is hash-based, not signature-based |

### 7. Error Handling
| Check | Status | Notes |
|-------|--------|-------|
| No stack traces leaked to responses | PASS | Errors captured as strings in `error_detail` |
| Broad `except Exception` in invoke_oracle | INFO | See finding F-002 |
| Custom exceptions well-scoped | PASS | VersionPinError, DatasetHashMismatchError, InvalidTransitionError |
| FileNotFoundError in bundle hash | PASS | Descriptive message, no path leakage |

### 8. Async Safety
| Check | Status | Notes |
|-------|--------|-------|
| `asyncio.wait_for` for timeout | PASS | Correctly cancels hung adapters |
| No shared mutable state between coroutines | PASS | Each invocation is independent |
| Backoff uses `asyncio.sleep` (not `time.sleep`) | PASS | Non-blocking backoff |
| MockOracleAdapter timeout uses `asyncio.sleep(100)` | PASS | Will be cancelled by `wait_for` |

### 9. Data Privacy
| Check | Status | Notes |
|-------|--------|-------|
| No PII in models | PASS | All data is construct/episode identifiers |
| Evidence bundle writes to local filesystem only | PASS | No network exfiltration |
| No logging of input_data contents | PASS | |

### 10. Code Quality
| Check | Status | Notes |
|-------|--------|-------|
| All error paths tested | PASS | 99 tests across 8 files |
| Boundary conditions covered | PASS | 22 tier assigner tests |
| No dead code | PASS | |
| Consistent patterns with sprint-1 | PASS | Same Pydantic BaseModel, Protocol, canonical_json patterns |

---

## Findings

### F-001: EvidenceBundleBuilder accepts unsanitised filenames [LOW / INFORMATIONAL]

**Location:** `theatre/engine/evidence_bundle.py:60,69`

`write_ground_truth(filename)` and `write_invocation(episode_id)` use caller-provided strings in path construction:
```python
path = self._base_dir / "ground_truth" / filename
path = self._base_dir / "invocations" / f"{episode_id}.json"
```

If `filename` or `episode_id` contained `../`, this could write outside the intended directory.

**Risk:** LOW — These values come from Pydantic-validated `GroundTruthEpisode.episode_id` and internal caller code, not from HTTP input. The bridge service (sprint-3) will be the external boundary.

**Recommendation:** When sprint-3 wires HTTP routes, validate that episode_id and filenames contain only `[a-zA-Z0-9_-]`. No action needed in sprint-2.

### F-002: Broad `except Exception` in invoke_oracle [INFORMATIONAL]

**Location:** `theatre/engine/oracle_contract.py:149`

The catch-all `except Exception` in the retry loop captures all exceptions including potentially `KeyboardInterrupt` (via `BaseException`, which this doesn't catch) and `SystemExit`. The current code is correct — `Exception` does NOT catch `KeyboardInterrupt` or `SystemExit` in Python.

**Risk:** NONE — Python's exception hierarchy ensures `Exception` does not swallow `BaseException` subclasses. The catch-all is appropriate for an adapter invocation that may raise arbitrary errors.

### F-003: datetime.utcnow() deprecation [INFORMATIONAL]

**Location:** `theatre/engine/certificate.py:55`, `theatre/engine/oracle_contract.py:50`

Same observation as sprint-1 audit. `datetime.utcnow()` is deprecated in Python 3.12+. Functional, not a security issue.

---

## Summary

| Severity | Count | Details |
|----------|-------|---------|
| CRITICAL | 0 | |
| HIGH | 0 | |
| MEDIUM | 0 | |
| LOW | 1 | F-001: Unsanitised filenames (mitigated by internal-only caller) |
| INFORMATIONAL | 2 | F-002: Broad except (correct), F-003: datetime deprecation |

No blocking issues. All security checks pass. Implementation is clean, well-tested, and architecturally aligned.

**APPROVED - LETS FUCKING GO**
