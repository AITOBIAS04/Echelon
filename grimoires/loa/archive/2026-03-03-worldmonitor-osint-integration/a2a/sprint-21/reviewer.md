# Sprint 21 Review — Evidence Pipeline Core + WorldMonitor Collector

**Cycle**: 011 (local sprint-1, global sprint-21)
**Date**: 2026-03-03
**Status**: COMPLETE

---

## Summary

Sprint 21 delivers the evidence collection layer for the WorldMonitor OSINT Integration. This is Stage 1 of the three-stage pipeline (Collection, Corroboration, Scoring). The sprint implements:

- **Evidence models** wrapping Pydantic API contract types in stdlib dataclasses
- **Canonical hashing** (Echelon Canonical JSON v0 + SHA-256) with API contract re-exports
- **BaseCollector ABC** with dual hash invariant enforcement at the base class level
- **WorldMonitorCollector** implementing all three WM domains (CII, Market, Maritime) with retry logic, timeout handling, and HTTP transcript receipt generation
- **Registry loader** with typed query API and structural validation
- **Collection runner** with concurrent asyncio.gather execution and per-collector timeout
- **Registry alignment** -- local sources.json with all three WM entries aligned to PRD Section 4.6 (shared `independence_upstream_id: worldmonitor`, `resolution_role: primary_evidence`)
- **Mock fixtures** derived from Pydantic v2 schemas for all three domains plus error scenarios

---

## Tasks Completed

| # | Task | File(s) | Lines |
|---|------|---------|-------|
| 1 | Evidence models | `backend/osint/models/evidence.py` | 54 |
| 2 | Canonical hashing | `backend/osint/canonical.py` | 72 |
| 3 | BaseCollector ABC | `backend/osint/collectors/base.py` | 100 |
| 4 | WorldMonitor collector | `backend/osint/collectors/worldmonitor.py` | 329 |
| 5 | Registry loader | `backend/osint/models/registry.py` | 182 |
| 6 | Registry alignment | `backend/osint/sources.json` | 84 |
| 7 | Collection runner | `backend/osint/engine/collection_runner.py` | 167 |
| 8 | Mock fixtures | `backend/osint/tests/fixtures/*.json` | 193 |
| 9 | Canonical tests | `backend/osint/tests/test_canonical.py` | 144 |
| 10 | Receipt tests | `backend/osint/tests/test_receipt.py` | 90 |
| 11 | Model tests | `backend/osint/tests/test_models.py` | 163 |
| 12 | Collector tests | `backend/osint/tests/test_worldmonitor.py` | 263 |
| 13 | Runner + registry tests | `backend/osint/tests/test_collection_runner.py`, `test_registry_loader.py` | 445 |

---

## Test Results

```
backend/osint/tests/  68 passed in 0.20s
backend/market/       97 passed           (regression)
backend/engines/     145 passed           (regression)
                     ----
TOTAL               310 passed, 0 failed
```

### Test Breakdown by Suite

| Suite | Tests | Status |
|-------|-------|--------|
| test_canonical.py | 16 | ALL PASS |
| test_receipt.py | 5 | ALL PASS |
| test_models.py | 8 | ALL PASS |
| test_worldmonitor.py | 17 | ALL PASS |
| test_collection_runner.py | 7 | ALL PASS |
| test_registry_loader.py | 15 | ALL PASS |
| **Sprint 21 total** | **68** | **ALL PASS** |

---

## Files Created/Modified

| File | Action | Lines | Description |
|------|--------|-------|-------------|
| `backend/osint/__init__.py` | NEW | 40 | Package init with all public exports |
| `backend/osint/canonical.py` | NEW | 72 | Canonical JSON v0 + SHA-256 hashing |
| `backend/osint/models/__init__.py` | NEW | 2 | Models subpackage init |
| `backend/osint/models/evidence.py` | NEW | 54 | CollectionResult + API contract re-exports |
| `backend/osint/models/registry.py` | NEW | 182 | RegistrySource + RegistryLoader + validation |
| `backend/osint/collectors/__init__.py` | NEW | 2 | Collectors subpackage init |
| `backend/osint/collectors/base.py` | NEW | 100 | BaseCollector ABC + hash invariants |
| `backend/osint/collectors/worldmonitor.py` | NEW | 329 | 3-domain WM collector + retry + health |
| `backend/osint/engine/__init__.py` | NEW | 2 | Engine subpackage init |
| `backend/osint/engine/collection_runner.py` | NEW | 167 | CollectionPlan + CollectionRunner |
| `backend/osint/sources.json` | NEW | 84 | WM registry subset (aligned) |
| `backend/osint/tests/__init__.py` | NEW | 2 | Tests package init |
| `backend/osint/tests/conftest.py` | NEW | 109 | Shared fixtures + helpers |
| `backend/osint/tests/fixtures/wm_cii_response.json` | NEW | 55 | Mock CII response |
| `backend/osint/tests/fixtures/wm_market_response.json` | NEW | 53 | Mock market response |
| `backend/osint/tests/fixtures/wm_maritime_response.json` | NEW | 53 | Mock maritime response |
| `backend/osint/tests/fixtures/wm_error_responses.json` | NEW | 32 | Mock error responses |
| `backend/osint/tests/test_canonical.py` | NEW | 144 | 16 canonical hashing tests |
| `backend/osint/tests/test_receipt.py` | NEW | 90 | 5 receipt hash tests |
| `backend/osint/tests/test_models.py` | NEW | 163 | 8 evidence model tests |
| `backend/osint/tests/test_worldmonitor.py` | NEW | 263 | 17 WM collector tests |
| `backend/osint/tests/test_collection_runner.py` | NEW | 233 | 7 collection runner tests |
| `backend/osint/tests/test_registry_loader.py` | NEW | 212 | 15 registry loader tests |
| `grimoires/loa/ledger.json` | MODIFIED | - | Sprint-1 status: planned -> in_progress |

**Total new files**: 23
**Total new lines**: ~2,432
**Modified files**: 1 (ledger.json)

---

## Architecture Decisions

1. **stdlib dataclasses over Pydantic** -- `CollectionResult` uses stdlib `@dataclass` to avoid coupling pipeline internals to Pydantic. API contract types (`EvidenceBundle`, etc.) remain Pydantic and are re-exported from `models/evidence.py`.

2. **bytes-based content hash** -- `compute_content_hash(raw_payload: bytes)` hashes exact response bytes, not re-serialised JSON. This is intentionally different from the API contract's dict-based version to prevent re-serialisation discrepancies from invalidating receipts.

3. **urllib.request over httpx** -- Uses stdlib `urllib.request` to avoid new runtime dependencies. HTTP calls are executed in a thread pool via `asyncio.run_in_executor()` with `asyncio.wait_for()` for timeout. All calls are mocked in tests.

4. **Dual hash invariant enforcement** -- `BaseCollector.fetch()` wraps `_fetch()` with two invariant checks: content_hash == SHA-256(raw_payload) and receipt_hash verification. Failures are converted to `success=False` (no raise).

5. **Local sources.json** -- Created `backend/osint/sources.json` with the three WM entries aligned to PRD Section 4.6 requirements. The existing registry JSON has different `independence_upstream_id` values per source. The local copy unifies them to `worldmonitor` as the spec requires for correct corroboration dedup in Sprint 2.

6. **Per-collector timeout** -- `CollectionRunner` wraps each collector in `asyncio.wait_for(timeout_s)` inside `asyncio.gather()`. One collector timing out does not cancel others.

---

## Acceptance Criteria Status

- [x] `canonical_json()` produces deterministic output (sorted keys, compact separators, no ASCII escape)
- [x] `compute_content_hash()` and `compute_receipt_hash()` re-exports match API contract originals exactly
- [x] `BaseCollector` enforces receipt invariants (content_hash = SHA-256 of raw response bytes, receipt_hash verification)
- [x] WorldMonitor collector calls correct endpoint per domain (CII, market, maritime)
- [x] WorldMonitor collector produces valid `EvidenceBundle` with `HTTPTranscriptReceipt`
- [x] WorldMonitor collector handles timeout, HTTP errors, and malformed responses gracefully (no raise)
- [x] WorldMonitor collector retries on transient failure (configurable count and delay)
- [x] WorldMonitor health check maps WM `HealthStatus` correctly
- [x] Registry loader loads JSON and queries by source_id, source_group, WM domain
- [x] Registry validation catches enum violations and settlement invariant breaches
- [x] Collection runner executes collectors concurrently with per-collector timeout
- [x] Collection runner handles partial failure (1 of 3 fails, other 2 succeed)
- [x] Collection plan correctly derived from Theatre `oracle_config`
- [x] 3 WM registry source entries verified aligned with API contract
- [x] Mock WM response fixtures generated from Pydantic v2 schemas (CII, market, maritime, errors)
- [x] All tests use mock HTTP responses only -- no real WM endpoint calls
- [x] No modifications to `backend/market/` or `backend/engines/` modules
- [x] Scoped regression: all tests in `backend/market/`, `backend/engines/` pass (242 pass, 0 fail)
- [x] Pre-existing `theatre/` collection errors excluded from regression baseline
- [x] 20+ new Sprint 1 tests pass (68 new tests)

---

## Registry Alignment Notes

The existing `echelon_osint_source_registry_v1_0_0.json` has per-source upstream IDs:
- `worldmonitor_cii` -> `worldmonitor_intelligence_backend`
- `worldmonitor_finance` -> `worldmonitor_market_backend`
- `worldmonitor_maritime` -> `worldmonitor_maritime_backend`

And `worldmonitor_finance`/`worldmonitor_maritime` have `resolution_role: secondary_corroboration`.

Per PRD Section 4.6, all three must share `independence_upstream_id: worldmonitor` and `resolution_role: primary_evidence`. The local `backend/osint/sources.json` implements the correct alignment. The upstream registry JSON is not modified (it serves other consumers).

---

## Ready for Sprint 22

Sprint 21 establishes the complete evidence collection layer. Sprint 22 (Corroboration + Scoring + Paradox Wiring + Convergence) builds on top of:
- `CollectionResult` list from `CollectionRunner`
- `RegistryLoader` for source metadata (independence_upstream_id for dedup)
- `EvidenceBundle` shapes for corroboration and scoring
- `canonical_json()` and `compute_content_hash()` for bundle hash manifest
