# Sprint 109 (sprint-1) Implementation Report

**Cycle:** 038 — Cross-Theatre Paradox Detection
**Sprint:** Sprint 1 — Core Services
**Global ID:** 109
**Date:** 2026-03-19

---

## Summary

All 5 tasks completed. 3 new services, 4 new schema files, 18 unit tests — all passing. Zero regression (sprint-0 tests: 18 passed).

---

## Task Completion

### T1.1: FactAnchorService — get_or_create + queries ✅
- `get_or_create()`: idempotent upsert on (external_source, external_id), returns existing on duplicate
- `get_theatres_for_anchor()`: queries FactAnchorLinks by anchor_id
- `get_anchors_for_theatre()`: queries FactAnchorLinks by theatre_id with optional anchor_type filter (joins FactAnchor for type filter)
- **File:** `backend/services/fact_anchor_service.py`
- **Tests:** 4 (create new, return existing, get_theatres, get_anchors)

### T1.2: FactAnchorService — link_theatre ✅
- `link_theatre()`: creates FactAnchorLink, counts distinct theatre_ids for anchor
- Returns `tuple[FactAnchorLink, bool]` — bool is True when >= 2 distinct theatres linked
- Scanner call deferred to Sprint 2 — this sprint returns trigger signal only
- **File:** `backend/services/fact_anchor_service.py`
- **Tests:** 3 (link creates record, scan trigger at 2 theatres, no trigger for 1)

### T1.3: CoherenceGroupService ✅
- `create_group()`: creates CoherenceGroup with name, group_type, policy_json
- `add_member()`: adds CoherenceGroupMember with role
- `get_groups_for_theatre()`: joins CoherenceGroupMember to find groups by theatre_id
- `get_group_members()`: queries members by group_id
- **File:** `backend/services/coherence_group_service.py`
- **Tests:** 4 (create, add_member, get_groups, get_members)

### T1.4: OracleConsistencyMonitor ✅
- `ConsistencyResult` and `DivergenceRecord` dataclasses (frozen=True)
- `record_response()`: idempotent on (theatre_id, source, event_id) — updates existing on re-record
- `check_consistency()`: compares all value_json for (source, event_id), computes max_delta from numeric fields
- `get_divergence_history()`: groups by event_id within time window, identifies divergent events
- **File:** `backend/services/oracle_consistency_monitor.py`
- **Tests:** 5 (record new, idempotent update, consistency identical, consistency divergent, provisional preserved)

### T1.5: Pydantic Schemas ✅
- `backend/schemas/fact_anchor_schemas.py`: CreateFactAnchorRequest, LinkTheatreRequest, FactAnchorResponse, FactAnchorLinkResponse, FactAnchorDetailResponse
- `backend/schemas/coherence_group_schemas.py`: CreateCoherenceGroupRequest, AddMemberRequest, CoherenceGroupMemberResponse, CoherenceGroupResponse, CoherenceGroupDetailResponse
- `backend/schemas/cross_theatre_paradox_schemas.py`: ParadoxTypeEnum, ParadoxSeverityEnum, ParadoxStatusEnum, CrossTheatreParadoxResponse, CrossTheatreParadoxListResponse, ResolveParadoxRequest
- `backend/schemas/oracle_consistency_schemas.py`: RecordOracleResponseRequest, OracleResponseResponse, ConsistencyCheckResponse, DivergenceRecordResponse
- Uses `model_config = ConfigDict(from_attributes=True)` (Pydantic v2 pattern)
- **Tests:** 2 (import + validation, all files importable)

---

## Test Results

```
18 passed in 0.35s (sprint-1)
18 passed (sprint-0 regression)
36 total, 0 failures
```

---

## Files Changed

| File | Action | Lines |
|------|--------|-------|
| `backend/services/fact_anchor_service.py` | Created | 108 |
| `backend/services/coherence_group_service.py` | Created | 72 |
| `backend/services/oracle_consistency_monitor.py` | Created | 183 |
| `backend/schemas/fact_anchor_schemas.py` | Created | 58 |
| `backend/schemas/coherence_group_schemas.py` | Created | 48 |
| `backend/schemas/cross_theatre_paradox_schemas.py` | Created | 57 |
| `backend/schemas/oracle_consistency_schemas.py` | Created | 43 |
| `backend/tests/test_038_sprint1_services.py` | Created | 326 |

---

## Design Decisions

1. **Mock AsyncSession pattern**: Tests use a minimal `MockAsyncSession` class with queued responses to avoid asyncpg dependency while testing service logic.
2. **link_theatre return type**: Returns `tuple[link, should_scan]` instead of calling scanner directly — scanner wiring happens in Sprint 2.
3. **OracleResponse upsert**: On re-record for same (theatre_id, source, event_id), updates value_json, queried_at, and is_provisional fields rather than creating a new row. This handles the USGS automatic → reviewed lifecycle.
4. **Numeric delta computation**: `_compute_max_delta` scans all numeric fields in value_json to find the largest divergence — generic enough for magnitude, Kp index, flare class, etc.
5. **Pydantic v2 ConfigDict**: Used `model_config = ConfigDict(from_attributes=True)` pattern matching existing codebase (e.g., sponsored_theatre.py, verification.py).
