# Sprint Plan — Cycle-038: Cross-Theatre Paradox Detection

**Cycle:** cycle-038
**Date:** 19 March 2026
**Builder:** Loa (backend only)
**Sprints:** 4 (sprint-0 through sprint-3)
**PRD:** `grimoires/loa/prd.md`
**SDD:** `grimoires/loa/sdd.md`

---

## Sprint 0: Schema + Migration

**Goal:** Create all 6 new tables, 3 new enums, WingFlapType extension, and Alembic migration. Validate models with unit tests.

### Tasks

#### T0.1: New Enums
- Add `CrossTheatreParadoxStatus` enum (OPEN, ACKNOWLEDGED, RESOLVED, DISMISSED)
- Add `CrossTheatreParadoxType` enum (SETTLEMENT_DIVERGENCE, ORACLE_INCONSISTENCY, SCOPE_OVERLAP_GAP, TEMPORAL_DRIFT)
- Add `CrossTheatreParadoxSeverity` enum (INFO, WATCH, MATERIAL, CRITICAL)
- Add `CROSS_THEATRE_PARADOX` to existing `WingFlapType` enum
- **File:** `backend/database/models.py`
- **AC:** All 4 enum changes in models.py, importable without error

#### T0.2: FactAnchor + FactAnchorLink Models
- Add `FactAnchor` model with unique constraint on (external_source, external_id), indexes on anchor_type and occurred_at
- Add `FactAnchorLink` model with FK to fact_anchors and theatres, composite index on (fact_anchor_id, theatre_id)
- Add relationship between FactAnchor and FactAnchorLink
- **File:** `backend/database/models.py`
- **AC:** Both models importable, relationships resolve, `__table_args__` define correct indexes

#### T0.3: CoherenceGroup + CoherenceGroupMember Models
- Add `CoherenceGroup` model with unique constraint on name, policy_json field
- Add `CoherenceGroupMember` model with FK to coherence_groups and theatres, role field
- Add relationship between CoherenceGroup and CoherenceGroupMember
- **File:** `backend/database/models.py`
- **AC:** Both models importable, relationships resolve

#### T0.4: CrossTheatreParadox + OracleResponse Models
- Add `CrossTheatreParadox` model with FK to fact_anchors, coherence_groups (nullable), theatres (a + b), 4 indexes
- Add `OracleResponse` model with FK to theatres, composite index on (source, event_id)
- **File:** `backend/database/models.py`
- **AC:** Both models importable, all FK constraints resolve

#### T0.5: Alembic Migration c038
- Create `backend/alembic/versions/c038_cross_theatre_paradox.py`
- Down revision: `c037_evaluation_contracts`
- Creates 6 tables with all constraints and indexes
- ALTER TYPE wingflaptype ADD VALUE 'CROSS_THEATRE_PARADOX'
- **AC:** `alembic upgrade head` succeeds, `alembic downgrade -1` succeeds, all tables created with correct constraints

#### T0.6: Model Unit Tests
- Test FactAnchor creation and unique constraint enforcement
- Test FactAnchorLink FK resolution and composite index
- Test CoherenceGroup creation with policy_json
- Test CrossTheatreParadox enum field storage and retrieval
- Test OracleResponse is_provisional flag
- **AC:** >= 6 tests, all passing

---

## Sprint 1: Core Services

**Goal:** Implement FactAnchorService, CoherenceGroupService, and OracleConsistencyMonitor with full test coverage.

### Tasks

#### T1.1: FactAnchorService — get_or_create + queries
- Implement `FactAnchorService` in `backend/services/fact_anchor_service.py`
- `get_or_create()`: idempotent upsert on (external_source, external_id)
- `get_theatres_for_anchor()`: query links by anchor_id
- `get_anchors_for_theatre()`: query links by theatre_id with optional anchor_type filter
- **AC:** get_or_create returns existing on duplicate, queries return correct results, 4 tests

#### T1.2: FactAnchorService — link_theatre
- Implement `link_theatre()` on FactAnchorService
- Creates FactAnchorLink record
- After linking, counts distinct theatre_ids for the anchor
- If >= 2 distinct theatres linked, returns a flag indicating cross-theatre scan should trigger
- **Note:** The actual scanner call is wired in Sprint 2; this sprint returns the trigger signal only
- **AC:** Link created correctly, trigger flag true when >= 2 theatres, false otherwise, 3 tests

#### T1.3: CoherenceGroupService
- Implement `CoherenceGroupService` in `backend/services/coherence_group_service.py`
- `create_group()`: create with name, group_type, policy_json
- `add_member()`: add theatre with role
- `get_groups_for_theatre()`: query groups by theatre_id
- `get_group_members()`: query members by group_id
- **AC:** CRUD operations work, multi-group membership works, 4 tests

#### T1.4: OracleConsistencyMonitor
- Implement `OracleConsistencyMonitor` in `backend/services/oracle_consistency_monitor.py`
- Implement `ConsistencyResult` and `DivergenceRecord` dataclasses
- `record_response()`: idempotent upsert on (theatre_id, source, event_id)
- `check_consistency()`: compare all responses for (source, event_id), return ConsistencyResult
- `get_divergence_history()`: query divergent responses within time window
- **AC:** Recording is idempotent, consistency check detects divergence, provisional flag preserved, 5 tests

#### T1.5: Pydantic Schemas
- Create `backend/schemas/fact_anchor_schemas.py` with request/response models
- Create `backend/schemas/coherence_group_schemas.py` with request/response models
- Create `backend/schemas/cross_theatre_paradox_schemas.py` with request/response models
- Create `backend/schemas/oracle_consistency_schemas.py` with request/response models
- **AC:** All schema files importable, validation works on sample data, 2 tests

---

## Sprint 2: Scanner + Integration

**Goal:** Implement CrossTheatreParadoxScanner with 4 detection patterns, wire into ParadoxRiskOrchestrator, WingFlap, and WebSocket.

### Tasks

#### T2.1: CrossTheatreParadoxScanner — Settlement Divergence
- Implement `CrossTheatreParadoxScanner` in `backend/services/cross_theatre_paradox_scanner.py`
- Implement `scan_fact_anchor()` orchestration method
- Implement `evaluate_settlement_divergence()`: compare theatre outcomes for same anchor
- Severity: MATERIAL if both ACTIVE, WATCH if one superseded, None if same outcome
- Deduplication: check existing OPEN record with same (anchor, theatre_a < theatre_b, type)
- **AC:** Detects opposite outcomes, skips same outcomes, respects theatre state, dedup works, 5 tests

#### T2.2: CrossTheatreParadoxScanner — Oracle Inconsistency + Provisional Rule
- Implement `evaluate_oracle_inconsistency()`: compare OracleResponse records for same (source, event_id)
- Implement `_classify_provisional_revision()`: provisional → reviewed = INFO per context_038 rule
- Severity: MATERIAL if same source delta > threshold, WATCH if cross-source, INFO if provisional revision
- **AC:** Detects value divergence, respects tolerance, provisional downgrade works, cross-source is WATCH, 4 tests

#### T2.3: CrossTheatreParadoxScanner — Scope Overlap + Temporal Drift
- Implement `scan_coherence_group()` orchestration method
- Implement `evaluate_scope_overlap()`: detect missing anchor links for group members
- Implement `evaluate_temporal_drift()`: detect settlement timing divergence
- Scope overlap severity: WATCH (absence is suspicious, not contradictory)
- Temporal drift severity: INFO if > window, WATCH if > 2x window
- **AC:** Scope gap detected when primary member missing link, temporal drift classified correctly, 4 tests

#### T2.4: ParadoxRiskOrchestrator Extension
- Add `cross_theatre_exposure` parameter to `trigger_recompute()` in `backend/services/paradox_risk_orchestrator.py`
- When not provided, auto-query CrossTheatreParadox for OPEN MATERIAL+ records affecting the theatre
- Risk level floor: >= 1 exposure → WATCH minimum, >= 3 → HIGH minimum
- Add `cross_theatre_exposure` to factors dict
- Materiality: exposure change triggers material delta
- **AC:** Exposure feeds into risk, floor logic works, material delta emits correctly, 3 tests

#### T2.5: WingFlap + WebSocket Integration
- Implement `_record_wingflap()` helper in scanner module
- Create WingFlap with type CROSS_THEATRE_PARADOX for each affected theatre on MATERIAL+ paradox
- Add `broadcast_cross_theatre_paradox()` to ConnectionManager in `backend/websockets/realtime_manager.py`
- Broadcast to both theatre channels on MATERIAL or CRITICAL
- Wire scanner to call WingFlap + WebSocket after paradox creation
- **AC:** WingFlap created for both theatres, WebSocket emitted for MATERIAL, not emitted for INFO/WATCH, 3 tests

#### T2.6: FactAnchorService Scanner Wiring
- Wire `link_theatre()` to call `CrossTheatreParadoxScanner.scan_fact_anchor()` when >= 2 theatres detected
- Wire scanner results to trigger `trigger_recompute()` for affected theatres
- **AC:** Full pipeline: link → scan → detect → wingflap → ws → recompute, 2 tests

---

## Sprint 3: API Routes + TREMOR Fixture + Regression

**Goal:** Expose all services via API routes, validate with TREMOR end-to-end fixture, confirm zero regression.

### Tasks

#### T3.1: FactAnchor API Routes
- Create `backend/api/fact_anchor_routes.py` with 5 endpoints
- POST / (create/get anchor), GET / (list), GET /{id} (detail + links), POST /{id}/link (link theatre), GET /{id}/paradoxes
- Register router in app factory
- **AC:** All 5 endpoints respond correctly, auth enforced on mutations, 3 tests

#### T3.2: CoherenceGroup + CrossTheatreParadox + OracleConsistency Routes
- Create `backend/api/coherence_group_routes.py` with 5 endpoints
- Create `backend/api/cross_theatre_paradox_routes.py` with 5 endpoints (list, detail, acknowledge, resolve, dismiss)
- Create `backend/api/oracle_consistency_routes.py` with 3 endpoints
- Register all routers in app factory
- **AC:** All endpoints respond correctly, state transitions enforce valid transitions, 4 tests

#### T3.3: TREMOR End-to-End Fixture
- Create test fixture with two seismic theatres observing the same USGS event (us6000test)
- Test: FactAnchor created from USGS event ID, both theatres linked
- Test: Settlement divergence detected when magnitude classifications differ (M6.2 vs M5.8)
- Test: Oracle consistency check between USGS and EMSC responses for same event
- Test: Provisional USGS automatic response upgraded to reviewed → INFO severity, not MATERIAL
- **AC:** 4 TREMOR fixture tests passing, full pipeline exercised

#### T3.4: Regression Suite
- Test: Per-theatre paradox engine (backend/engines/paradox.py) unchanged — logic gap detection works as before
- Test: Contract pipeline (037/037b/037c/037d) unaffected — all existing contract tests pass
- Test: Evidence freshness computation unchanged
- Run full existing test suite to confirm zero regression
- **AC:** All existing tests pass unchanged, 3 explicit regression tests

---

## Summary

| Sprint | Tasks | Est. Tests | Focus |
|--------|-------|-----------|-------|
| Sprint 0 | 6 | ~6 | Schema, migration, model validation |
| Sprint 1 | 5 | ~18 | Core services (CRUD, linking, oracle monitoring) |
| Sprint 2 | 6 | ~21 | Scanner (4 patterns), orchestrator, WS, WingFlap |
| Sprint 3 | 4 | ~14 | API routes, TREMOR fixture, regression |
| **Total** | **21** | **~59** | |
