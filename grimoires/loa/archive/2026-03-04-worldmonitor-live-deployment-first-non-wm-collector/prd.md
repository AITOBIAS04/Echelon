# PRD — Cycle-015: WorldMonitor Live Deployment + First Non-WM Collector

**Cycle:** cycle-015
**Date:** 4 March 2026
**Predecessor:** cycle-014 (Bounded Inquiry Markets) + cycle-014b (Genome Runtime Integration)
**Sprints:** 2
**Baseline:** 932 passed (full suite), 4 skipped, 13 pre-existing collection errors

---

## 1. Problem Statement

Cycle-011 built the full three-stage OSINT pipeline (collection -> corroboration -> scoring) but everything runs against mock fixtures. No live HTTP calls, no real evidence, no independent corroboration.

Two critical limitations:

1. **No live evidence.** The `WorldMonitorCollector` has never been tested against a running WorldMonitor instance. All tests use JSON fixtures from `backend/osint/tests/fixtures/`. The mock-to-live code path has never been formally verified.

2. **Single-source corroboration trap.** All three WM sources share `independence_upstream_id: "worldmonitor"`. The `CorroborationEngine` deduplicates by upstream ID, so three WM bundles collapse to 1 distinct group. `corroboration_minimum` (default 2) is never met. Every pipeline run produces `corroboration_met: false` and the scoring composite eats a permanent 0.7 penalty factor.

> Sources: echelon_cycle_015.md:10-18, echelon_platform_roadmap.md:153-159

## 2. Objective

Two deliverables:

1. **Sprint 1 — WM Live:** Deploy WorldMonitor locally, create live tests gated behind `@pytest.mark.live_wm`, verify that live HTTP responses produce structurally identical output to mock fixtures. Prove the mock-to-live transition is seamless.

2. **Sprint 2 — Companies House:** Port the existing Companies House collector from `osint_pipeline/` to `backend/osint/`, add it to the runtime registry with a distinct `independence_upstream_id: "uk_companies_house_backend"`, and verify that WM + Companies House produces `corroboration_minimum_met: true`. The 0.7 penalty lifts to 1.0 for UK corporate Theatres.

## 3. Success Criteria

1. `WorldMonitorCollector` hits live `/health`, `/api/v1/intelligence/cii`, `/api/v1/market/snapshot`, `/api/v1/maritime/anomaly` endpoints — all produce valid `EvidenceBundle` with correct hash invariants
2. Mock-to-live parity: same Python types, same field set on `EvidenceBundle`, same hash computation method, same receipt structure
3. Live tests are **skipped by default** — require `--live-wm` flag or `ECHELON_LIVE_WM=1` env var
4. Companies House collector implements `BaseCollector` interface with `HTTPTranscriptReceipt`
5. Runtime registry bumped to `0.4.0-wm-ch` with 4 sources (3 WM + 1 CH)
6. `CorroborationEngine` produces `corroboration_minimum_met: true` when WM + CH bundles are present (no code changes to engine — just data)
7. Scoring composite uses 1.0 corroboration factor (not 0.7) when both source groups present
8. Full pipeline E2E test: collect -> corroborate -> score with both sources -> `p_reality` not penalised
9. Zero new test failures vs baseline
10. All new CH mock tests pass by default; live CH tests gated behind `--live-ch` flag

## 4. Prerequisites

### P0: WorldMonitor Deployment

Before Sprint 1 code work begins:
- WM instance reachable at configured base URL (default `http://localhost:8080`)
- `GET /health` returns per-domain status (HEALTHY or DEGRADED accepted; UNAVAILABLE = not ready)
- Setup documentation present at `grimoires/loa/context/WM_LOCAL_SETUP.md` or `docs/`

### P1: Companies House API Key

Before Sprint 2 live tests:
- Free registration at Companies House Developer Hub
- API key stored in `ECHELON_COMPANIES_HOUSE_API_KEY` env var
- Mock tests do NOT require the key

## 5. Codebase Grounding

### 5.1 Current State

| Component | File | Version | State |
|-----------|------|---------|-------|
| WM Collector | `backend/osint/collectors/worldmonitor.py` | v0.1.0 | Mock-only. Base URL: `http://localhost:8080` via `WorldMonitorConfig` |
| BaseCollector | `backend/osint/collectors/base.py` | — | ABC with `_fetch()` template, 2 hash invariant enforcement |
| Corroboration | `backend/osint/engine/corroboration.py` | — | Groups by `independence_upstream_id`, counts distinct groups vs `corroboration_minimum` |
| Runtime Registry | `backend/osint/sources.json` | v0.3.2-wm | 3 WM sources, all `independence_upstream_id: "worldmonitor"` |
| Source Manifest | `backend/osint/source_manifest.py` | — | `build_manifest()` reads registry, flags provisional sources |
| Reality Provider | `backend/engines/reality_signal.py` | v011.1 | `LiveOSINTRealityProvider` — 4-stage pipeline, 300s staleness |
| Test Fixtures | `backend/osint/tests/conftest.py` | — | 3 mock response fixtures (CII, Market, Maritime) |
| CH Collector (legacy) | `osint_pipeline/collectors/companies_house.py` | v0.6.0 | Standalone package, NOT wired to `backend/osint/` |

### 5.2 Files That Need Creation

| File | Purpose |
|------|---------|
| `backend/osint/tests/test_worldmonitor_live.py` | Live WM tests (gated `@pytest.mark.live_wm`) |
| `backend/osint/tests/test_mock_live_parity.py` | Formal parity verification (gated `@pytest.mark.live_wm`) |
| `backend/osint/collectors/companies_house.py` | CH collector implementing `BaseCollector` |
| `backend/osint/tests/test_companies_house.py` | CH mock + live tests |
| `backend/osint/tests/test_corroboration_with_ch.py` | Corroboration engine with multi-source verification |
| `backend/osint/tests/test_e2e_corroboration.py` | Full pipeline E2E with WM + CH |
| `backend/osint/tests/fixtures/ch_company_profile.json` | Mock CH API response |

### 5.3 Files That Need Modification

| File | Change |
|------|--------|
| `backend/osint/tests/conftest.py` | Add `live_wm` and `live_ch` pytest markers |
| `backend/osint/collectors/worldmonitor.py` | Ensure base URL configurable via env var `ECHELON_WM_BASE_URL` |
| `backend/osint/sources.json` | Add Companies House entry, bump to v0.4.0-wm-ch |
| `backend/osint/source_manifest.py` | Verify `build_manifest()` picks up CH with `ELIGIBLE` status |

## 6. Inquiry Class Interaction

Companies House is `settlement_eligible: true` with `jurisdiction: "GB"`. It naturally serves INVESTIGATIVE and INSPECTION inquiry classes (UK corporate due diligence, company status verification). The inquiry-class affinity is informational — the pipeline collects from all configured sources regardless of inquiry class. What changes is the *weight* assigned during scoring, which is already handled by the existing `oracle_config` mechanism.

## 7. Constraints

- **Local WM only.** Production WM deployment is out of scope. Sprint 1 proves mock-to-live parity against a local instance.
- **No counter-signal wiring.** All 11 counter-signal classes remain `UNAVAILABLE` with `allow_gap=True`. Needs independent counter-signal sources (future cycle).
- **No convergence persistence.** In-process logging only for geographic convergence alerts.
- **Single CH endpoint.** Only `/company/{company_number}` (profile lookup). Additional endpoints (filing-history, officers, PSC, charges, insolvency) deferred to Cycle-017.
- **No additional non-WM collectors.** Only Companies House in this cycle. SEC EDGAR, UK Gazette, Bank of England follow in 017.
- **Consumption surface reconciliation deferred.** Intelligence DB says 7 surfaces; research notes reference an 8th `deployability_routing` — reconcile during 017.

## 8. Sprint Structure

### Sprint 1: WorldMonitor Live Tests

**Prerequisite:** P0 (WM deployed locally, /health reachable)

Tasks:
1. Add `@pytest.mark.live_wm` marker to conftest
2. WM base URL env var configuration (`ECHELON_WM_BASE_URL`)
3. Live WM tests (6 tests: CII collection, market collection, maritime collection, health check, hash invariants, receipt structure)
4. Mock-to-live parity verification (structural equality of EvidenceBundle, hash computation, receipt fields)

### Sprint 2: Companies House Collector Integration

Tasks:
1. Port CH collector to `backend/osint/` implementing `BaseCollector`
2. Update runtime registry to v0.4.0-wm-ch (add CH entry)
3. Mock fixtures for CH API responses
4. CH tests (5 mock + 2 live behind `@pytest.mark.live_ch`)
5. Corroboration engine multi-source verification tests
6. Source manifest validation (CH picks up as ELIGIBLE)
7. E2E pipeline test: WM (mock) + CH (mock) -> corroboration_met=true -> scoring factor 1.0

## 9. Regression Target

**Baseline:** 932 passed, 4 skipped, 13 pre-existing collection errors
**Gate rule:** >=932 passed. Zero new failures. All new WM live tests skipped by default. All new CH mock tests pass. Existing OSINT pipeline tests unchanged.

## 10. What 015 Unlocks

- **Real evidence flowing into Theatres** — first time the pipeline processes live HTTP responses, not fixtures
- **Independent corroboration** — WM + Companies House produces genuine multi-source corroboration for UK corporate Theatres
- **Settlement-eligible evidence** — Companies House is `settlement_eligible: true`, meaning its evidence can drive resolution
- **Foundation for 017 (Registry Expansion)** — proves the pattern for adding non-WM collectors. Next candidates: SEC EDGAR, UK Gazette, Bank of England
- **Confidence in mock fidelity** — formal parity tests prove the mocks accurately represent live behaviour
