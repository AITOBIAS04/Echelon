# Sprint Plan — Cycle-037d: Theatre Construct Verification

**Cycle:** cycle-037d
**Date:** 19 March 2026
**Builder:** Loa (backend only)
**Sprints:** 4 (0–3)

> Sources: prd.md, sdd.md, context_037d.md, codebase validation

---

## Sprint 0 — Foundation: Construct Class + Theatre Domains

**Goal:** Add `construct_class` to `ConstructSpec` and register theatre precise domains so the policy normalizer classifies theatre domain claims correctly. Parse `construct.json` into structured metadata.

**Scope:** MEDIUM (4 tasks)

### Deliverables

- [ ] Modified `backend/services/spec_loader.py` — `construct_class` field on `ConstructSpec`
- [ ] `backend/services/theatre_policy_rules.py` — domain registration + construct.json parser + data models
- [ ] `backend/tests/test_spec_loader_construct_class.py` — 4 tests
- [ ] `backend/tests/test_theatre_policy_rules.py` — 4 tests

### Acceptance Criteria

- [ ] `ConstructSpec` has `construct_class: str = "skill"` field
- [ ] `load()` parses `construct_class` from YAML; absent or unrecognized defaults to `"skill"`
- [ ] 10 theatre precise domains registered in `KNOWN_PRECISE_DOMAINS` at import time
- [ ] `normalize()` classifies `seismic_intelligence`, `space_weather`, etc. as precise
- [ ] `parse_construct_json()` handles TREMOR-style (`echelon.*` nested) and CORONA-style (root-level) layouts
- [ ] Derived booleans: `has_brier_scoring`, `has_cross_validation`, `oracle_names`
- [ ] `ValueError` raised on invalid JSON input

### Technical Tasks

- [ ] **T0.1** Add `construct_class: str = "skill"` to `ConstructSpec` dataclass and update `load()` to parse it from YAML with validation (`"skill"`, `"theatre"`, `"bridge"` accepted; else default `"skill"`) → **[G-1]**
- [ ] **T0.2** Create `theatre_policy_rules.py` with `THEATRE_PRECISE_DOMAINS` (10 domains), `register_theatre_domains()`, and import-time `_REGISTERED_COUNT` following `security_policy_rules.py` pattern → **[G-6]**
- [ ] **T0.3** Implement `TheatreTemplate`, `OsintSource`, `VerificationCheck`, `TheatreConstructMeta` frozen dataclasses and `parse_construct_json()` with TREMOR/CORONA fallback chains → **[G-2]**
- [ ] **T0.4** Write 8 tests: 4 construct_class tests (theatre, skill explicit, absent default, unknown default) + 4 theatre policy tests (domain registration count, precise classification, TREMOR parsing, minimal fixture parsing) → **[G-1, G-2, G-6, G-8]**

### Dependencies

- None. This is the foundation sprint.

### Risks & Mitigation

- **Risk:** Import-time set mutation leaks between tests. **Mitigation:** Tests snapshot and restore `KNOWN_PRECISE_DOMAINS` in setUp/tearDown (same pattern as 037c).
- **Risk:** construct.json format divergence. **Mitigation:** Parser uses fallback chains with sensible defaults for missing fields.

**Exit:** 8 tests pass, `ConstructSpec.construct_class` and `parse_construct_json()` are importable.

---

## Sprint 1 — Theatre Check Planner

**Goal:** Create `theatre_check_planner.py` with 4 check types (`SETTLEMENT_ACCURACY`, `ORACLE_CONSISTENCY`, `CALIBRATION_VALIDITY`, `FUNCTIONAL_CORRECTNESS`) and merge logic, following the `security_check_planner.py` pattern.

**Scope:** MEDIUM (3 tasks)

### Deliverables

- [ ] `backend/services/theatre_check_planner.py` — `plan_theatre_checks()` + `merge_theatre_checks()`
- [ ] `backend/tests/test_theatre_check_planner.py` — 8 tests

### Acceptance Criteria

- [ ] `THEATRE_CHECK_TYPES` maps 4 check types to anchor classes (SETTLEMENT_ACCURACY/ORACLE_CONSISTENCY → LIVE_EXTERNAL_EVIDENCE, CALIBRATION_VALIDITY/FUNCTIONAL_CORRECTNESS → DETERMINISTIC_CHECK)
- [ ] `plan_theatre_checks()` generates correct cardinality: 1 SETTLEMENT_ACCURACY per template, 1 ORACLE_CONSISTENCY per cross-validation source, 1 CALIBRATION_VALIDITY total (if Brier), 1 FUNCTIONAL_CORRECTNESS per template
- [ ] check_id format: `theatre:{check_type_lower}:{entity_id}`
- [ ] SETTLEMENT_ACCURACY and ORACLE_CONSISTENCY are `critical=True`; CALIBRATION_VALIDITY and FUNCTIONAL_CORRECTNESS are `critical=False`
- [ ] Sort order: `(check_type, domain, check_id)` for determinism
- [ ] `merge_theatre_checks()` deduplicates by `check_id`, preserves sort order

### Technical Tasks

- [ ] **T1.1** Create `theatre_check_planner.py` with `THEATRE_CHECK_TYPES` constant and `plan_theatre_checks(spec_slug, meta)` implementing all 4 check generation rules with `seen_ids` dedup → **[G-2, G-3]**
- [ ] **T1.2** Implement `merge_theatre_checks(base_checks, theatre_checks)` following `merge_security_checks()` pattern: dedup by check_id, sort by `(check_type, domain, check_id)` → **[G-3]**
- [ ] **T1.3** Write 8 tests: SETTLEMENT_ACCURACY per template, ORACLE_CONSISTENCY only when cross-validation, CALIBRATION_VALIDITY only when Brier, FUNCTIONAL_CORRECTNESS per template, sort determinism, dedup on duplicate template ids, merge preserves both sets, merge dedup on overlapping check_ids → **[G-2, G-3, G-8]**

### Dependencies

- Sprint 0 (`TheatreConstructMeta` dataclass, `TheatreTemplate`, `OsintSource`)

### Risks & Mitigation

- **Risk:** check_type strings inflate contract model. **Mitigation:** `PlannedCheck.check_type` is already a free string field — no schema change needed.

**Exit:** 8 tests pass, `plan_theatre_checks()` and `merge_theatre_checks()` produce correct output.

---

## Sprint 2 — Contract Pipeline Integration

**Goal:** Wire theatre checks into the contract pipeline: add `construct_json` to API schema and route, merge theatre checks in `contract_service.py`, extend anchor mapper with 4 theatre-specific rules.

**Scope:** MEDIUM (4 tasks)

### Deliverables

- [ ] Modified `backend/schemas/construct_schemas.py` — `construct_json` on `CreateContractRequest`
- [ ] Modified `backend/api/construct_routes.py` — pass `construct_json` kwarg
- [ ] Modified `backend/services/contract_service.py` — theatre merge block
- [ ] Modified `backend/services/construct_anchor_mapper.py` — 4 theatre mapping rules
- [ ] Additional tests in `backend/tests/test_theatre_check_planner.py` — 8 tests

### Acceptance Criteria

- [ ] `CreateContractRequest` has `construct_json: Optional[str] = None`
- [ ] Route handler passes `construct_json=body.construct_json` to `create_contract()`
- [ ] `contract_service.create_contract()` accepts `construct_json: Optional[str]` parameter
- [ ] Theatre merge runs after security merge, before `checks_to_dicts`, guarded by `construct_json and spec.construct_class == "theatre"`
- [ ] Malformed `construct_json` logs warning, does not crash pipeline
- [ ] 4 new `_MAPPING_RULES` entries: `theatre_oracle_settlement` (LIVE_EXTERNAL_EVIDENCE), `theatre_calibration` (DETERMINISTIC_CHECK), `theatre_state_machine` (DETERMINISTIC_CHECK), `theatre_named_oracle` (LIVE_EXTERNAL_EVIDENCE)
- [ ] Existing 037c anchor mapping rules unchanged

### Technical Tasks

- [ ] **T2.1** Add `construct_json: Optional[str] = Field(None, ...)` to `CreateContractRequest` in `construct_schemas.py` → **[G-4]**
- [ ] **T2.2** Pass `construct_json=body.construct_json` in `construct_routes.py` create_contract call; add `construct_json: Optional[str] = None` parameter to `contract_service.create_contract()` with imports and theatre merge block (try/except ValueError) → **[G-4, G-5]**
- [ ] **T2.3** Append 4 theatre mapping rules to `construct_anchor_mapper.py` `_MAPPING_RULES`: settlement/oracle keywords, brier/calibration keywords, position_history keywords, named oracle keywords (USGS/EMSC/SWPC/DONKI/NOAA/IRIS_DMC/GFZ) → **[G-5]**
- [ ] **T2.4** Write 8 tests: contract service creates theatre checks for theatre construct, ignores construct_json for skill construct, anchor mapper settlement→LIVE_EXTERNAL, brier→DETERMINISTIC, USGS→LIVE_EXTERNAL, unrecognized keyword no match, hash changes with theatre checks, backward compat skill construct unchanged → **[G-4, G-5, G-7, G-8]**

### Dependencies

- Sprint 0 (`ConstructSpec.construct_class`, `parse_construct_json`)
- Sprint 1 (`plan_theatre_checks`, `merge_theatre_checks`)

### Risks & Mitigation

- **Risk:** Importing `theatre_policy_rules` in `contract_service.py` registers domains as side effect. **Mitigation:** This is the established pattern (see `security_policy_rules.py`). Import happens before any normalization runs. Domains are additive only.
- **Risk:** Adding theatre checks changes contract hash for theatre constructs. **Mitigation:** This is correct behavior — a theatre contract with theatre checks is a different contract.

**Exit:** 8 tests pass, full pipeline wired.

---

## Sprint 3 — TREMOR + CORONA Fixtures + Regression

**Goal:** Validate end-to-end with realistic TREMOR and CORONA construct.json fixtures. Confirm zero regression against all 037/037b/037c/037c-fix tests.

**Scope:** SMALL (3 tasks)

### Deliverables

- [ ] `backend/tests/test_theatre_integration.py` — 8 tests (4 TREMOR fixture + 2 CORONA fixture + 2 regression)

### Acceptance Criteria

- [ ] TREMOR fixture with 5 templates, 3 sources (1 primary, 2 cross-validation), Brier scoring → 13 theatre checks (5 SETTLEMENT + 2 ORACLE + 1 CALIBRATION + 5 FUNCTIONAL)
- [ ] CORONA fixture with root-level fields, data_sources, rlmf.exports → expected theatre checks with same 4 check types
- [ ] All existing 037/037b/037c tests pass unchanged
- [ ] Skill construct without construct_class produces identical output to pre-037d
- [ ] Hash determinism: same inputs → same contract hash across runs

### Technical Tasks

- [ ] **T3.1** Build TREMOR fixture (5 templates: magnitude_gate, aftershock_cascade, depth_anomaly, swarm_detection, tsunami_risk; 3 OSINT sources: USGS primary, EMSC cross-validation, IRIS cross-validation; Brier scoring; settlement tiers) and write 4 tests: total count=13, all 4 check types present, check_id format, cross-validation source detection → **[G-7]**
- [ ] **T3.2** Build CORONA fixture (5 templates, root-level layout, data_sources not osint_sources, rlmf.exports with brier_score) and write 2 tests: parser handles root-level layout, Brier inferred from rlmf.exports → **[G-7]**
- [ ] **T3.3** Write 2 regression tests: skill construct without construct_class unchanged, hash determinism across multiple runs → **[G-8]**

### Dependencies

- Sprints 0, 1, 2 (all new services and wiring)

### Risks & Mitigation

- **Risk:** TREMOR/CORONA fixture data does not match real construct.json layout. **Mitigation:** Fixtures derived from actual TREMOR/CORONA BUTTERFREEZONE.md descriptions in the PRD. Parser fallback chains handle layout variations.

**Exit:** 8 tests pass, ≥32 total tests across cycle. Zero regression.

---

## Sprint Summary

| Sprint | Focus | New/Changed Files | Tests | Global ID |
|---|---|---|---|---|
| 0 | Construct class + theatre domains + parser | `spec_loader.py` (edit), `theatre_policy_rules.py` (new) | 8 | 104 |
| 1 | Theatre check planner (4 types + merge) | `theatre_check_planner.py` (new) | 8 | 105 |
| 2 | Pipeline integration (schema + route + service + anchor) | `construct_schemas.py`, `construct_routes.py`, `contract_service.py`, `construct_anchor_mapper.py` (all edits) | 8 | 106 |
| 3 | TREMOR/CORONA fixtures + regression | `test_theatre_integration.py` (new) | 8 | 107 |
| **Total** | | **2 new + 5 edited** | **~32** | |

---

## Appendix A: PRD Goal Mapping

| Goal ID | Goal | Contributing Tasks |
|---|---|---|
| G-1 | `ConstructSpec` supports `construct_class` field; absent defaults to `"skill"` | T0.1, T0.4 |
| G-2 | `plan_theatre_checks()` generates 4 theatre-specific check types from construct.json | T0.3, T1.1, T1.3 |
| G-3 | `merge_theatre_checks()` combines theatre + base checks with sort/dedup | T1.2, T1.3 |
| G-4 | `contract_service.create_contract()` accepts `construct_json` and routes to theatre planner | T2.1, T2.2, T2.4 |
| G-5 | Theatre anchor mapping rules added (settlement, oracle, calibration, named oracles) | T2.2, T2.3, T2.4 |
| G-6 | Theatre precise domains registered, `normalize()` classifies them as precise | T0.2, T0.4 |
| G-7 | TREMOR/CORONA fixtures produce correct check types | T3.1, T3.2 |
| G-8 | All existing 037/037b/037c tests pass unchanged (zero regression) + ≥28 new tests | T0.4, T1.3, T2.4, T3.3 |
