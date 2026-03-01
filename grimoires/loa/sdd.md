# SDD: OSINT Registry v0.6.0 Merge & Pipeline Hardening

**Cycle:** 003
**Date:** 2026-03-01
**PRD:** `grimoires/loa/prd.md`

---

## 1. Overview

Hardening cycle — no new architecture. All changes are additive fields, guard conditions, and tests against the existing pipeline from Cycle-002.

---

## 2. Changes

### 2.1 Registry Fixture Merge (R1-R4)

**File**: `theatre/fixtures/two_rail_theatres_v0_1/datasets/echelon_osint_source_registry_v0_6_0.json` (new, replaces v0.4.0)

Procedure:
1. Load the v0.4.0 JSON (57 sources)
2. Append 9 sources from `docs/registries/registry_v060_expansion.json`
3. Extend `source_group_enum.committed_values` with `court_record`, `financial_regulator`, `government_registry`
4. Update top-level `version` to `"0.6.0"`
5. Update `summary.total_sources` to `66`
6. Update `summary.by_jurisdiction` counts
7. Update `summary.settlement_eligible_count`
8. Write as `echelon_osint_source_registry_v0_6_0.json`

**File**: `osint_pipeline/models/registry.py`
- Change `SUPPORTED_VERSION = "0.4.0"` → `"0.6.0"`
- Update module docstring version reference

**Files**: `tests/osint_pipeline/conftest.py`, `test_registry.py`, `test_fixtures_regression.py`, `test_cli.py`, `test_config.py`
- Update `REGISTRY_PATH` to point to v0.6.0 filename
- Update version assertions (`"0.4.0"` → `"0.6.0"`)
- Update source count assertions (`57` → `66`)

### 2.2 E1 — Source Group Taxonomy Mapping

**File**: `osint_pipeline/models/registry.py`

Add to `RegistrySource`:
```python
mapped_source_group: str | None = None
```

This is a non-breaking additive field. Default `None` means no mapping needed (source_group is already in committed enum). The 9 new sources set this field to their proposed v2 group name in the fixture.

**Fixture entries** for expansion sources get `mapped_source_group`:
- `uk_caselaw_tna`: `"judicial_record"`
- `uk_legislation_gov`: `"legislative_record"`
- `uk_parliament_api`: `"political_record"`
- `imf_sdmx_api`: `"sovereign_financial"`
- `usa_spending_api`: `None` (no proposed mapping — general gov registry)
- `bls_api`: `None`
- `worldbank_api`: `"sovereign_financial"`
- `nih_reporter_api`: `None`
- `npi_registry_cms`: `None`

**Test**: Load registry. For every source: if `source_group` is NOT in `source_group_enum.committed_values`, then `mapped_source_group` MUST be non-None. This catches taxonomy drift — new groups without mapping are test failures.

### 2.3 E2 — Settlement Policy Guard

**File**: `osint_pipeline/engine/scorer.py`

The `Scorer.score()` method sets a new field on OracleOutput:
```python
settlement_safe = any(
    b.resolution_role == "primary_evidence"
    for b in collection.bundles
)
```

This is advisory — the composite score is unchanged. Consumers check `oracle_output.settlement_safe` before allowing settlement resolution.

**File**: `osint_pipeline/models/oracle_output.py`
- Add `settlement_safe: bool = False` to `OracleOutput`

**Test**: Create collection with only `secondary_corroboration` bundles → `settlement_safe == False`. Add one `primary_evidence` bundle → `settlement_safe == True`.

### 2.4 E3 — Auth Redaction Regression Test

**File**: `tests/osint_pipeline/test_canonical.py` (extend existing)

New test class `TestAuthRedaction`:
- Build two canonical forms: one with `{"Authorization": "Bearer secret", "X-Api-Key": "key123", "Accept": "application/json"}`, one with `{"Accept": "application/json"}` only
- Assert canonical forms are identical
- Assert `"secret"` not in canonical form
- Assert `"key123"` not in canonical form
- Assert receipt hashes are identical

### 2.5 E4 — Independence Field Completeness

**File**: `tests/osint_pipeline/test_fixtures_regression.py` (extend existing)

New test: load merged v0.6.0 registry. For every source where `settlement_eligible == True`, assert `independence_upstream_id` is non-empty. Blank `independence_upstream_id` on a settlement source would cause the corroboration engine's `upstream_dedup_map` to lump unrelated sources together.

### 2.6 H1 — Dev Dependency Pinning

**File**: `requirements-dev.txt` (new)

```
pytest>=7.0,<9
pydantic>=2.0,<3
httpx>=0.24,<1
```

---

## 3. Files Changed

| File | Change Type | Concern |
|------|-------------|---------|
| `theatre/fixtures/.../echelon_osint_source_registry_v0_6_0.json` | New | R1-R4 |
| `osint_pipeline/models/registry.py` | Edit | R3, E1 |
| `osint_pipeline/engine/scorer.py` | Edit | E2 |
| `osint_pipeline/models/oracle_output.py` | Edit | E2 |
| `tests/osint_pipeline/conftest.py` | Edit | R4 |
| `tests/osint_pipeline/test_registry.py` | Edit | R4 |
| `tests/osint_pipeline/test_fixtures_regression.py` | Edit | R4, E4 |
| `tests/osint_pipeline/test_cli.py` | Edit | R4 |
| `tests/osint_pipeline/test_config.py` | Edit | R4 |
| `tests/osint_pipeline/test_canonical.py` | Edit | E3 |
| `tests/osint_pipeline/test_scorer.py` | Edit | E2 |
| `requirements-dev.txt` | New | H1 |

---

## 4. Test Strategy

All new tests added to existing test files (no new test file needed). Test count increase: ~8-10 new tests.

| Test | File | Asserts |
|------|------|---------|
| Taxonomy consistency | `test_registry.py` | Every source with non-committed group has `mapped_source_group` |
| All 9 expansion sources present | `test_fixtures_regression.py` | `registry.get(id)` returns non-None for each |
| Settlement guard — secondary only | `test_scorer.py` | `settlement_safe == False` |
| Settlement guard — primary + secondary | `test_scorer.py` | `settlement_safe == True` |
| Auth header stripping | `test_canonical.py` | Identical hash with/without auth headers |
| Auth key material absent | `test_canonical.py` | `"secret"` and `"key123"` not in canonical form |
| Independence completeness | `test_fixtures_regression.py` | All settlement sources have non-blank `independence_upstream_id` |
| Registry loads v0.6.0 | `test_registry.py` | version == "0.6.0", total_sources == 66 |
| Registry rejects v0.4.0 | `test_registry.py` | ValueError on version mismatch |
