# Sprint 54 (Cycle-019 Sprint 0) — Schema Foundation

## Implementation Report

### Tasks Completed

#### Task 0.1: AgentDeployment + DeploymentAuditEvent Models
- **File**: `backend/database/models.py` (lines 968-1040)
- Added `AgentDeployment` model with: agent_id FK, theatre_id FK, status (ACTIVE|PAUSED|WITHDRAWN), strategy_profile (BALANCED|AGGRESSIVE|DEFENSIVE), routing_hint_snapshot, coherence_gate_status_snapshot, config_json, deployed_by, deployed_at, paused_at, withdrawn_at
- Added `DeploymentAuditEvent` model with: deployment_id FK, event_type, detail_json, created_at
- Composite index on (agent_id, theatre_id, status)

#### Task 0.2: Investigation Persistence Models (7 tables)
- **File**: `backend/database/models.py` (lines 1043-1213)
- `Investigation`: theatre_id, construct_id, inquiry_class, status, domain_filters_json, stop_condition, stop_config_json, relationships to all child tables
- `InvestigationEvidenceItem`: type, source_construct_id, payload_json, weight, submitted_at
- `InvestigationClaimNode`: label, hypothesis, confidence, evidence_ids_json, parent_node_id
- `InvestigationCounterSignal`: signal_type, source, detail_json, severity, detected_at
- `InvestigationDriftEvent`: drift_type, magnitude, detail_json, detected_at
- `InvestigationCertificateRecord`: investigation_id (unique), certificate_hash, certificate_json, routing_decision, issued_at

#### Task 0.3: Paradox Risk Columns on Theatre
- **File**: `backend/database/models.py` (Theatre model)
- Added 3 nullable columns: `paradox_risk_level` (String(10)), `paradox_risk_factors_json` (JSON), `paradox_risk_updated_at` (DateTime)

#### Task 0.5: Pydantic Schemas
- **File**: `backend/schemas/agent_deployment_schemas.py` (created)
- 8 schemas: AgentDeploymentCreate, StrategyUpdateRequest, AgentDeploymentSummaryResponse, AgentDeploymentResponse, DeploymentAuditEventResponse, DeploymentDetailResponse, DeploymentListResponse, ParadoxRiskResponse
- All response models use `ConfigDict(from_attributes=True)` for ORM compatibility

#### Task 0.4: Alembic Migration
- Skipped — project uses SQLAlchemy create_all pattern, no Alembic configured

### Tests

- **File**: `backend/tests/test_c019_sprint0_schema.py` — 4 tests, all passing
  1. `test_all_new_models_create_tables` — verifies all 8 new tables exist
  2. `test_pydantic_schemas_validate` — validates all 8 Pydantic schemas with sample data
  3. `test_theatre_has_paradox_risk_columns` — confirms 3 paradox risk columns on theatres table
  4. `test_investigation_certificate_unique_constraint` — verifies unique constraint on investigation_id

### Issues Resolved
- Removed duplicate index `ix_investigations_status` (column had `index=True` AND explicit Index in `__table_args__`)
- Used `Base.metadata.create_all(eng, tables=_TABLES)` pattern to avoid ARRAY type incompatibility with SQLite test engine (Agent/Timeline models use PG-only ARRAY columns)

### Files Changed
| File | Change |
|------|--------|
| `backend/database/models.py` | Added 8 new model classes + 3 Theatre columns |
| `backend/schemas/agent_deployment_schemas.py` | Created — 8 Pydantic schemas |
| `backend/tests/test_c019_sprint0_schema.py` | Created — 4 tests |
