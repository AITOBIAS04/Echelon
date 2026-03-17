# Implementation Report — Sprint 81 (cycle-025/sprint-0)

**Sprint:** Schema + Migration
**Status:** IMPLEMENTED
**Date:** 2026-03-17
**Commit:** `6d65caea` feat(cycle-025/sprint-0): Schema + Migration — MeasureType 7→14, osint_signals table

---

## Tasks Completed

### Task 1: Extend MeasureType enum ✅

**File:** `backend/schemas/worldmonitor_api_contract.py:46-62`

Added 7 new values after `DARK_FLEET_PROBABILITY`:
- `FORECAST_SCORE`
- `FORECAST_WEIGHT`
- `CORRIDOR_RISK`
- `SHIPPING_RATE_INDEX`
- `SUPPLY_CHAIN_SEVERITY`
- `SANCTIONS_EXPOSURE`
- `CROSS_DOMAIN_CONVERGENCE`

Total enum members: 14 (was 7).

**Tests:**
- `test_all_14_values_present` — verifies all 14 string values exist
- `test_string_serialisation_roundtrip` — verifies `MeasureType(m.value) == m` for all members

### Task 2: Add nullable fields to response schemas ✅

**File:** `backend/schemas/worldmonitor_api_contract.py`

| Response Model | New Fields | Lines |
|---|---|---|
| `CIIResponse` | `forecast_score: Optional[float]`, `forecast_weight: Optional[float]`, `sanctions_exposure: Optional[float]` | 178–180 |
| `MarketSnapshotResponse` | `supply_chain_severity: Optional[float]` | 206 |
| `MaritimeAnomalyResponse` | `corridor: Optional[str]`, `corridor_risk: Optional[float]`, `shipping_rate_index: Optional[float]` | 236–238 |

All fields default to `None` — backward compatible with existing payloads.

**Tests:**
- `test_backward_compat_old_payloads_parse` — old payloads without new fields still parse
- `test_new_fields_serialize_with_values` — new fields serialize correctly when populated
- `test_new_fields_serialize_as_null` — new fields serialize as null when not provided

### Task 3: Add OsintSignal model ✅

**File:** `backend/database/models.py:1327-1349`

```
OsintSignal(Base)
  __tablename__ = "osint_signals"
  id: String(36), PK, default=uuid4
  source_id: String(128), NOT NULL, indexed
  source_group: String(64), NOT NULL
  signal_type: String(64), NOT NULL
  geo_region: String(128), nullable
  entity_ref: String(256), nullable
  content_hash: String(128), NOT NULL, indexed
  normalised_data: JSON, NOT NULL
  investigation_id: String(36), FK→investigations.id, nullable
  collected_at: DateTime, NOT NULL
  created_at: DateTime, NOT NULL, default=utcnow
```

Composite indexes:
1. `ix_osint_signals_source_group_collected` — (source_group, collected_at)
2. `ix_osint_signals_investigation_collected` — (investigation_id, collected_at)
3. `ix_osint_signals_geo_collected` — (geo_region, collected_at)

**Test:**
- `test_model_instantiation` — verifies tablename and all column names present

### Task 4: Create Alembic migration ✅

**File:** `backend/alembic/versions/c025_osint_signals.py`

- Revision: `c025_osint_signals`
- Revises: `c024_construct_verification`
- `upgrade()`: CREATE TABLE osint_signals + 2 single-column indexes (source_id, content_hash) + 3 composite indexes
- `downgrade()`: DROP TABLE osint_signals

Migration applied successfully to local PostgreSQL.

### Task 5: Create response schemas ✅

**File:** `backend/schemas/osint_schemas.py` (new)

| Schema | Fields |
|---|---|
| `OsintSignalResponse` | id, source_id, source_group, signal_type, geo_region, entity_ref, content_hash, normalised_data, investigation_id, collected_at. Config: `from_attributes = True` |
| `PaginatedSignalsResponse` | signals: list[OsintSignalResponse], limit: int, offset: int |
| `OsintHealthResponse` | feeds_online, feeds_total, signal_latency_sec, escalation_queue_depth, replay_workers_active |
| `SignalSummaryResponse` | total_signals, by_source_group: dict[str, int], counter_signals, certificate_candidates, convergence_cells |

**Tests:**
- `test_paginated_signals_response` — PaginatedSignalsResponse instantiation
- `test_health_response` — OsintHealthResponse instantiation
- `test_summary_response` — SignalSummaryResponse instantiation

---

## Test Summary

| Test Class | Tests | Status |
|---|---|---|
| TestMeasureTypeEnum | 2 | ✅ |
| TestResponseSchemaAdditions | 3 | ✅ |
| TestOsintSignalModel | 1 | ✅ |
| TestOsintResponseSchemas | 3 | ✅ |
| **Total** | **9** | **All passing** |

---

## Files Changed

| File | Change |
|---|---|
| `backend/schemas/worldmonitor_api_contract.py` | +7 MeasureType values, +7 nullable fields across 3 response models |
| `backend/database/models.py` | +OsintSignal model (23 lines) |
| `backend/alembic/versions/c025_osint_signals.py` | New migration file |
| `backend/schemas/osint_schemas.py` | New file: 4 response schemas |
| `backend/tests/test_cycle025_sprint0.py` | New test file: 9 tests |

---

## Exit Criteria Verification

- [x] 9 tests pass (exceeds target of 6)
- [x] `alembic upgrade head` succeeds
- [x] MeasureType has 14 values
- [x] Path 2 files untouched (signal_detector.py, osint_registry.py)
