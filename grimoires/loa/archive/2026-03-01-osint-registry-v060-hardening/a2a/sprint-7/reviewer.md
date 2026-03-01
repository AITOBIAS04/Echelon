# Sprint 7 (Cycle-003 Sprint-1) Implementation Report

## Summary

Registry v0.6.0 merge + pipeline hardening. All 8 tasks (T1.1-T1.8) completed. 239 tests passing.

## Tasks Completed

### T1.1: Merge v0.6.0 Registry Fixture
- **File**: `theatre/fixtures/two_rail_theatres_v0_1/datasets/echelon_osint_source_registry_v0_6_0.json`
- Merged v0.4.0 base (57 sources) + expansion (9 sources) = 65 unique sources
- `uk_parliament_api` existed in both: expansion entry updates the base entry (source_group: official_gov → government_registry)
- Added 3 new committed source_groups: `court_record`, `financial_regulator`, `government_registry`
- Added `proposed_source_groups` and `mapped_source_group` per-source field
- Updated summary totals (by_jurisdiction, settlement_eligible_count)

### T1.2: RegistryLoader Version Pin + mapped_source_group
- **File**: `osint_pipeline/models/registry.py`
- Changed `SUPPORTED_VERSION` from `"0.4.0"` to `"0.6.0"`
- Added `mapped_source_group: str | None = None` field to `RegistrySource`
- Updated docstrings

### T1.3: Test Version/Count Assertions
- **Files**: `tests/osint_pipeline/test_registry.py`, `test_fixtures_regression.py`, `test_cli.py`, `test_config.py`, `conftest.py`
- Updated all version assertions from `"0.4.0"` to `"0.6.0"`
- Updated source count assertions to 65 (accounting for uk_parliament_api dedup)
- Updated registry path references from `v0_4_0` to `v0_6_0`
- Updated config default path reference

### T1.4: Source Group Taxonomy Drift Tests (E1)
- **File**: `tests/osint_pipeline/test_registry.py` — `TestSourceGroupTaxonomy` class
- `test_non_committed_groups_have_mapping`: every source with a non-committed group has `mapped_source_group`
- `test_mapped_groups_are_valid`: all `mapped_source_group` values are in proposed or committed set

### T1.5: Settlement Safe Guard (E2)
- **File**: `osint_pipeline/models/oracle_output.py` — added `settlement_safe: bool = False`
- **File**: `osint_pipeline/engine/scorer.py` — computes `settlement_safe = any(b.resolution_role == "primary_evidence" ...)`
- **File**: `tests/osint_pipeline/test_scorer.py` — `TestSettlementSafe` class (3 tests)

### T1.6: Auth Redaction Regression Tests (E3)
- **File**: `tests/osint_pipeline/test_canonical.py` — `TestAuthRedaction` class
- `test_auth_headers_stripped_from_canonical`: with/without auth headers produce identical canonical form
- `test_secret_material_absent`: secret values never appear in output
- `test_receipt_hash_identical_with_without_auth`: receipt hashes match regardless of auth

### T1.7: Independence Field Completeness Tests (E4)
- **File**: `tests/osint_pipeline/test_fixtures_regression.py` — `TestIndependenceFieldCompleteness`
- `test_settlement_sources_have_upstream_id`: all settlement-eligible sources have non-blank `independence_upstream_id`
- **File**: `tests/osint_pipeline/test_fixtures_regression.py` — `TestExpansionSourcesPresent`
- Verifies all 9 expansion source_ids present and queryable

### T1.8: requirements-dev.txt
- **File**: `requirements-dev.txt` — pytest>=7.0,<9, pydantic>=2.0,<3, httpx>=0.24,<1

## Test Results

```
239 passed in 20.22s
```

All existing tests pass. No regressions.

## Design Decisions

1. **65 not 66 sources**: `uk_parliament_api` exists in both v0.4.0 (official_gov) and expansion (government_registry). The merge script updates the existing entry rather than creating a duplicate. RegistryLoader deduplicates by source_id dict anyway.

2. **settlement_safe is advisory**: Does not affect composite score. Just flags whether at least one primary_evidence bundle exists.

3. **mapped_source_group**: Optional field (None for sources already in committed groups). Only set for expansion sources with new groups (court_record, financial_regulator, government_registry).

## Files Changed

| File | Change |
|------|--------|
| `osint_pipeline/models/registry.py` | Version pin, mapped_source_group field |
| `osint_pipeline/models/oracle_output.py` | settlement_safe field |
| `osint_pipeline/engine/scorer.py` | settlement_safe computation |
| `osint_pipeline/config.py` | Default registry path v0.6.0 |
| `tests/osint_pipeline/conftest.py` | Registry path v0.6.0 |
| `tests/osint_pipeline/test_registry.py` | Count fixes, taxonomy tests |
| `tests/osint_pipeline/test_fixtures_regression.py` | Expansion + independence tests |
| `tests/osint_pipeline/test_canonical.py` | Auth redaction tests |
| `tests/osint_pipeline/test_scorer.py` | Settlement safe tests |
| `tests/osint_pipeline/test_cli.py` | Registry path v0.6.0 |
| `tests/osint_pipeline/test_config.py` | Registry path v0.6.0 |
| `theatre/fixtures/.../echelon_osint_source_registry_v0_6_0.json` | New merged fixture |
| `requirements-dev.txt` | New test dependencies |
