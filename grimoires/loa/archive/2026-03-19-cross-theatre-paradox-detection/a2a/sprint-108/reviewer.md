# Sprint 108 (sprint-0) Implementation Report

**Cycle:** 038 — Cross-Theatre Paradox Detection
**Sprint:** Sprint 0 — Schema + Migration
**Global ID:** 108
**Date:** 2026-03-19

---

## Summary

All 6 tasks completed. 3 new enums, 1 enum extension, 6 new SQLAlchemy models, 1 Alembic migration, 18 unit tests — all passing.

---

## Task Completion

### T0.1: New Enums ✅
- Added `CrossTheatreParadoxStatus` (OPEN, ACKNOWLEDGED, RESOLVED, DISMISSED)
- Added `CrossTheatreParadoxType` (SETTLEMENT_DIVERGENCE, ORACLE_INCONSISTENCY, SCOPE_OVERLAP_GAP, TEMPORAL_DRIFT)
- Added `CrossTheatreParadoxSeverity` (INFO, WATCH, MATERIAL, CRITICAL)
- Added `CROSS_THEATRE_PARADOX` to `WingFlapType`
- **File:** `backend/database/models.py` (lines 1397–1412)

### T0.2: FactAnchor + FactAnchorLink Models ✅
- `FactAnchor`: unique constraint on (external_source, external_id), indexes on anchor_type, occurred_at, composite type+time
- `FactAnchorLink`: FK to fact_anchors and theatres, composite index on (fact_anchor_id, theatre_id)
- Relationship: FactAnchor.links ↔ FactAnchorLink.fact_anchor
- **File:** `backend/database/models.py` (lines 1415–1461)

### T0.3: CoherenceGroup + CoherenceGroupMember Models ✅
- `CoherenceGroup`: unique constraint on name, policy_json field
- `CoherenceGroupMember`: FK to coherence_groups and theatres, role field
- Relationship: CoherenceGroup.members ↔ CoherenceGroupMember.group
- **File:** `backend/database/models.py` (lines 1464–1499)

### T0.4: CrossTheatreParadox + OracleResponse Models ✅
- `CrossTheatreParadox`: FK to fact_anchors, coherence_groups (nullable), theatres (a + b), 4 indexes
- `OracleResponse`: FK to theatres, composite index on (source, event_id), is_provisional flag
- **File:** `backend/database/models.py` (lines 1502–1562)

### T0.5: Alembic Migration c038 ✅
- Down revision: `c037_evaluation_contracts`
- Creates all 6 tables with constraints and indexes
- Creates 3 PostgreSQL enum types
- `ALTER TYPE wingflaptype ADD VALUE IF NOT EXISTS 'CROSS_THEATRE_PARADOX'`
- Downgrade drops all 6 tables and 3 enums
- **File:** `backend/alembic/versions/c038_cross_theatre_paradox.py`

### T0.6: Model Unit Tests ✅
- 18 tests total (exceeds AC of >= 6)
- 4 enum tests (values, WingFlapType extension)
- 3 FactAnchor tests (creation, unique index, type+time index)
- 2 FactAnchorLink tests (creation, composite index)
- 3 CoherenceGroup tests (creation, member creation, member indexes)
- 3 CrossTheatreParadox tests (creation with enums, indexes, theatre ordering)
- 3 OracleResponse tests (creation, is_provisional, indexes)
- **File:** `backend/tests/test_038_sprint0_models.py`

---

## Test Results

```
18 passed in 0.24s
```

Existing regression tests: 8 passed (test_037d_sprint3_fixtures.py)

---

## Files Changed

| File | Action | Lines |
|------|--------|-------|
| `backend/database/models.py` | Modified | +170 |
| `backend/alembic/versions/c038_cross_theatre_paradox.py` | Created | 168 |
| `backend/tests/test_038_sprint0_models.py` | Created | 235 |

---

## Design Decisions

1. **Mock connection for tests**: `connection.py` creates async engine at import time. Tests mock `sys.modules` to provide a real `declarative_base` without requiring asyncpg.
2. **`_generate_uuid` default**: All models use existing `_generate_uuid` helper for primary keys, consistent with rest of codebase.
3. **Theatre ordering convention**: `theatre_a_id < theatre_b_id` lexicographic enforced at application level (tested), not DB constraint.
4. **Migration enum handling**: `create_type=False` in cross_theatre_paradoxes columns since enums are created explicitly before table creation.
