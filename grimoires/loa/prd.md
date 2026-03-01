# PRD: OSINT Registry v0.6.0 Merge & Pipeline Hardening

**Cycle:** 003
**Type:** Hardening (no new features)
**Date:** 2026-03-01
**Predecessor:** Cycle-002 (OSINT Pipeline — Live Collection & Evidence Bundles)

---

## 1. Problem Statement

Cycle-002 shipped the OSINT Pipeline with 6 collectors, a 3-stage composed oracle engine, and 263 passing tests against a v0.4.0 registry (57 sources). The Cycle-035 architectural fixes (GapKind, upstream dedupe, receipt header allowlist, URL normalisation, timeout→gaps, receipt-mode enforcement, confidence caps) are implemented and tested.

Two gaps remain before the pipeline is production-ready:

1. **Registry Expansion**: A v0.6.0 expansion file (`docs/registries/registry_v060_expansion.json`) adds 9 new sources across 3 new source groups. These must be merged and validated against enforcement logic.

2. **Enforcement Compatibility**: The new sources must not introduce taxonomy drift, settlement-policy ambiguity, or receipt-redaction violations against the hardened pipeline.

> Source: User scope definition, Cycle-002 engineer/auditor feedback, `registry_v060_expansion.json`, Valyu reverse-engineering analysis

---

## 2. Goals & Success Criteria

| # | Goal | Measurable Criterion |
|---|------|---------------------|
| G1 | Merge 9 new sources into registry | v0.6.0 fixture loads with 66 sources; RegistryLoader accepts v0.6.0 |
| G2 | Taxonomy mapping without drift | `mapped_source_group` field on RegistrySource; test asserts coverage |
| G3 | Settlement policy safety | Guard: settlement requires >= 1 primary_evidence source; test with secondary-only |
| G4 | Auth redaction invariant | Test: api_key material never appears in canonical receipts |
| G5 | Independence field completeness | Test: all settlement_eligible sources have non-blank `independence_upstream_id` |
| G6 | Full regression green | All existing 263 + new hardening tests pass |
| G7 | Dev dependency pinning | `requirements-dev.txt` exists with pinned versions |

---

## 3. Scope

### 3.1 In Scope

**Registry Merge (R1-R4)**

- **R1**: Create merged v0.6.0 registry fixture by appending 9 expansion sources to existing v0.4.0 fixture (57 + 9 = 66 sources)
- **R2**: Update `source_group_enum.committed_values` to include 3 new groups
- **R3**: Update `RegistryLoader.SUPPORTED_VERSION` from `"0.4.0"` to `"0.6.0"`, version + summary in fixture
- **R4**: Update all hardcoded version/count assertions in tests

**Enforcement Compatibility (E1-E4)**

- **E1 — Source Group Taxonomy Drift**: The registry's `proposed_source_groups` are `["judicial_record", "legislative_record", "political_record", "sovereign_financial"]` but the actual `source_group` values used by the 9 new sources are `court_record`, `government_registry`, `financial_regulator`. Add `mapped_source_group` optional field to `RegistrySource` (v2 taxonomy mapping) so templates can reference proposed groups without changing existing `source_group` values. Add test: every source either has `mapped_source_group` when in a new group, or its `source_group` is in the committed enum.

- **E2 — Settlement Eligibility Policy Safety**: `uk_parliament_api` has `resolution_role="secondary_corroboration"` and `settlement_eligible=true`. The scorer (`scorer.py`) does not currently distinguish resolution roles — it scores all bundles equally. Add a guard: settlement resolution requires at least one `primary_evidence` bundle (unless template explicitly overrides). Add test: secondary-only collection fails settlement check; primary+secondary passes.

- **E3 — Auth + Receipt Redaction**: For sources with `auth_methods: ["api_key"]` (e.g. `bls_api`), the canonical header allowlist (`canonical.py:28-32`) already strips `Authorization`. Add an explicit regression test: create a request with `Authorization: Bearer xxx` and `X-Api-Key: yyy` headers → canonical form contains neither; receipt hash is identical with or without auth headers.

- **E4 — Independence Field Completeness**: Load the full merged v0.6.0 registry. Add a test: every `settlement_eligible` source MUST have a non-empty `independence_upstream_id`. Blank/missing values cause false dedupe collisions in the corroboration engine.

**Housekeeping (H1)**

- **H1**: Create `requirements-dev.txt` with pinned dev dependencies

### 3.2 Out of Scope

- New collectors for the 9 new sources (future cycle)
- Changes to the composed oracle scoring algorithm weights
- Deployment infrastructure or frontend changes
- Registry v0.5.0 intermediate step (jumping directly v0.4.0 → v0.6.0)

### 3.3 Source Count Discrepancy

The expansion file states `expansion_from: "0.5.0"` and `total_sources_after: 77`, implying a v0.5.0 base with 68 sources. Our actual base is v0.4.0 with 57 sources. We merge directly: 57 + 9 = **66 sources** at v0.6.0. Expansion file summary metadata will be corrected.

---

## 4. Technical Context

### 4.1 Current State

| Component | Location | State |
|-----------|----------|-------|
| Registry fixture | `theatre/fixtures/two_rail_theatres_v0_1/datasets/echelon_osint_source_registry_v0_4_0.json` | v0.4.0, 57 sources |
| Expansion file | `docs/registries/registry_v060_expansion.json` | 9 new sources |
| RegistryLoader | `osint_pipeline/models/registry.py:63` | `SUPPORTED_VERSION = "0.4.0"` |
| RegistrySource | `osint_pipeline/models/registry.py:16-49` | 26 fields, all expansion fields have defaults |
| Scorer | `osint_pipeline/engine/scorer.py` | No resolution_role awareness; scores all bundles equally |
| Canonical | `osint_pipeline/engine/canonical.py:28-32` | `CANONICAL_HEADER_ALLOWLIST = {"accept", "content-type", "user-agent"}` |
| Tests | `tests/osint_pipeline/` | 14 test files, 263 passing |

### 4.2 Expansion Sources

| source_id | jurisdiction | source_group | resolution_role | auth | upstream_id |
|-----------|-------------|--------------|-----------------|------|-------------|
| `uk_caselaw_tna` | GB | `court_record` | primary_evidence | none | `gb_tna_caselaw` |
| `uk_legislation_gov` | GB | `government_registry` | primary_evidence | none | `gb_tna_legislation` |
| `uk_parliament_api` | GB | `government_registry` | secondary_corroboration | none | `gb_parliament_data` |
| `imf_sdmx_api` | GLOBAL | `financial_regulator` | primary_evidence | none | `global_imf_sdmx` |
| `usa_spending_api` | US | `government_registry` | primary_evidence | none | `us_treasury_usaspending` |
| `bls_api` | US | `government_registry` | primary_evidence | api_key | `us_bls_statistics` |
| `worldbank_api` | GLOBAL | `financial_regulator` | primary_evidence | none | `global_worldbank_indicators` |
| `nih_reporter_api` | US | `government_registry` | primary_evidence | none | `us_nih_reporter` |
| `npi_registry_cms` | US | `government_registry` | primary_evidence | none | `us_cms_npi` |

### 4.3 Taxonomy Mapping

| Actual source_group | Proposed v2 group | Mapping rationale |
|---------------------|-------------------|-------------------|
| `court_record` | `judicial_record` | Court judgments → judicial records |
| `government_registry` (legislation) | `legislative_record` | legislation.gov.uk |
| `government_registry` (parliament) | `political_record` | Parliamentary APIs |
| `government_registry` (spending/stats) | (no proposed match) | General gov data registries |
| `financial_regulator` | `sovereign_financial` | IMF/World Bank → sovereign financial data |

### 4.4 Key Code Paths

**E2 — Settlement guard location**: `Scorer.score()` at `scorer.py:56`. Currently processes `collection.bundles` without checking `resolution_role`. The guard should check that at least one bundle has `resolution_role == "primary_evidence"` before allowing a passing composite score to be flagged as settlement-eligible. The check belongs on `OracleOutput` or as a scorer post-condition — NOT by filtering bundles from the score itself.

**E3 — Canonical header filtering**: `canonical.py:99-107`. The allowlist filter `if k.lower().strip() in CANONICAL_HEADER_ALLOWLIST` already excludes `Authorization`, `X-Api-Key`, `Cookie`, etc. Test confirms hash identity with/without these headers.

---

## 5. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Existing tests break on version bump | Medium | Update all version/count assertions atomically |
| `mapped_source_group` adds nullable field complexity | Low | Optional with default None; backward-compatible |
| Settlement guard false-rejects valid configurations | Medium | Template override mechanism; guard is advisory by default |
| `conftest.py` hardcoded path to v0.4.0 filename | Medium | Rename fixture file; update all path references |

---

## 6. Acceptance Criteria Summary

1. Merged v0.6.0 registry fixture with 66 sources and 3 new committed source groups
2. `RegistryLoader.from_file()` accepts v0.6.0, rejects v0.4.0
3. All 9 new sources queryable via `registry.get(source_id)`
4. `mapped_source_group` field on RegistrySource; taxonomy consistency test passes
5. Settlement guard rejects secondary-only collections; passes with primary+secondary
6. Auth header regression test: `Authorization`/`X-Api-Key` stripped from canonical form
7. Independence completeness test: all settlement-eligible sources have non-blank upstream IDs
8. `requirements-dev.txt` exists with pinned versions
9. Full test suite green (existing 263 + new hardening tests)
