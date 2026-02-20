# Sprint 25 — Core Engine Foundation: Implementation Report

> Cycle: cycle-031 (Theatre Template Engine)
> Sprint: sprint-25 (global) / sprint-1 (local)
> Status: **COMPLETE**

---

## Summary

All 7 tasks implemented with 113 unit tests passing. The theatre engine foundation is fully operational: state machine enforces irreversible 6-state lifecycle, canonical JSON produces RFC 8785-compliant deterministic output, commitment protocol provides tamper-evident SHA-256 hashing, criteria model validates weight constraints, template validator enforces JSON Schema + 7 runtime rules, and 5 database tables extend the existing SQLAlchemy schema.

---

## Task Completion

### T1.1: Theatre State Machine
**File:** `theatre/engine/state_machine.py`
**Tests:** `tests/theatre/test_state_machine.py` — **43 tests passing**
**Status:** COMPLETE

- `TheatreState` enum with 6 values: DRAFT, COMMITTED, ACTIVE, SETTLING, RESOLVED, ARCHIVED
- `VALID_TRANSITIONS` dict mapping each state to valid successors
- `TheatreStateMachine` class with `transition()` and `can_transition()` methods
- `InvalidTransitionError` with descriptive error messages including theatre_id and state names
- Tests cover: all 5 valid transitions, full lifecycle, 30 parametrized invalid pairs (backward, skip-ahead, self-transitions), ARCHIVED terminal state, error message content

**Acceptance Criteria:**
- [x] `TheatreState` enum with 6 values
- [x] `VALID_TRANSITIONS` mapping each state to its valid successors
- [x] `TheatreStateMachine.transition()` advances state or raises `InvalidTransitionError`
- [x] `TheatreStateMachine.can_transition()` returns bool
- [x] All 5 valid transitions succeed
- [x] All invalid transitions raise `InvalidTransitionError` (test every invalid pair)
- [x] `ARCHIVED` has no valid successors

---

### T1.2: Canonical JSON Utility
**File:** `theatre/engine/canonical_json.py`
**Tests:** `tests/theatre/test_canonical_json.py` — **35 tests passing**
**Status:** COMPLETE

- `canonical_json()` function using `json.dumps` with `sort_keys=True, separators=(",",":")`
- `_normalise_value()` recursive normalisation handling bool-before-int subclass ordering
- `_normalise_float()` strips trailing zeroes (1.0→1), rejects NaN/Infinity
- Tests cover: sorted keys (flat, nested, deep nesting), no whitespace, null inclusion, array order preservation, empty containers, booleans, Unicode, tuple→array coercion, float normalisation edge cases, 8 round-trip determinism cases, unsupported type rejection, bool/int distinction

**Acceptance Criteria:**
- [x] Keys sorted lexicographically at every nesting level
- [x] No whitespace between tokens
- [x] Float normalisation: 1.0 → 1, 0.10 → 0.1, no trailing zeroes
- [x] `NaN` and `Infinity` raise `ValueError`
- [x] `null` values included (not omitted)
- [x] Arrays preserve insertion order
- [x] Round-trip determinism: `canonical_json(x) == canonical_json(json.loads(canonical_json(x)))`
- [x] UTF-8 encoding, minimal escaping

---

### T1.3: Commitment Protocol
**File:** `theatre/engine/commitment.py`
**Tests:** `tests/theatre/test_commitment.py` — **12 tests passing**
**Status:** COMPLETE

- `CommitmentProtocol` class with static methods: `compute_hash()`, `verify_hash()`, `create_receipt()`
- SHA-256 over canonical JSON of composite `{dataset_hashes, template, version_pins}`
- `CommitmentReceipt` Pydantic model with theatre_id, commitment_hash, committed_at, template_snapshot, version_pins, dataset_hashes
- Tests cover: 64-char hex output, determinism, sensitivity (template/pins/hashes changes → different hash), key order irrelevance, verify valid/tampered/wrong hash, receipt creation, receipt hash consistency, receipt JSON serialisation

**Acceptance Criteria:**
- [x] `compute_hash()` produces SHA-256 hex string (64 chars)
- [x] Composite object has exactly three keys: `dataset_hashes`, `template`, `version_pins`
- [x] Same inputs always produce same hash (deterministic)
- [x] Different inputs produce different hashes
- [x] `verify_hash()` returns True for matching, False for mismatched
- [x] `CommitmentReceipt` Pydantic model with all fields from SDD §4.2

---

### T1.4: Structured Criteria Model
**File:** `theatre/engine/models.py`
**Tests:** `tests/theatre/test_criteria.py` — **10 tests passing**
**Status:** COMPLETE

- `TheatreCriteria(BaseModel)` with `criteria_ids`, `criteria_human`, `weights`
- `model_validator` checking: weight keys ⊆ criteria_ids, weight sum = 1.0 within 1e-6 tolerance
- Additional models: `GroundTruthEpisode`, `AuditEvent`, `BundleManifest`
- Tests cover: valid criteria with weights, empty weights, default weights, extra key rejection, weight sum rejection, tolerance (3-way split), single criterion, empty criteria_ids rejection, three criteria, partial weights rejection

**Acceptance Criteria:**
- [x] `criteria_ids: list[str]` — non-empty, unique
- [x] `criteria_human: str` — freeform rubric
- [x] `weights: dict[str, float]` — keys must be subset of `criteria_ids`, values must sum to 1.0 (within 1e-6 tolerance)
- [x] Validation raises on extra weight keys
- [x] Validation raises on weight sum ≠ 1.0
- [x] Empty weights dict is valid (equal weight fallback computed at scoring time)

---

### T1.5: Template Validator
**File:** `theatre/engine/template_validator.py`
**Tests:** `tests/theatre/test_template_validator.py` — **13 tests passing**
**Status:** COMPLETE

- `TemplateValidator` class with `validate()` returning `list[str]` errors
- Phase 1: JSON Schema validation against `docs/schemas/echelon_theatre_schema_v2.json`
- Phase 2: Runtime rules 1–5, 7 (weight keys ⊆ criteria_ids, weight sum, construct pin linkage, chain pins, HITL step linkage, dataset hash presence)
- Phase 3: Certificate-run rule 6 (mock adapter rejection)
- Tests cover: valid Product and Market templates pass, missing required field, invalid execution_path, invalid template_family, each runtime rule violation caught individually, mock adapter allowed for non-certificate runs

**Acceptance Criteria:**
- [x] Loads schema from `docs/schemas/echelon_theatre_schema_v2.json`
- [x] Validates template structure against JSON Schema
- [x] Runtime rule 1: `criteria.weights` keys ⊆ `criteria.criteria_ids`
- [x] Runtime rule 2: `criteria.weights` values sum to 1.0
- [x] Runtime rule 3: Every `construct_id` in `resolution_programme` has `version_pins.constructs` entry
- [x] Runtime rule 4: Every construct in `construct_chain` has version pin
- [x] Runtime rule 5: Every `hitl_steps[].step_id` matches a resolution step
- [x] Runtime rule 6: `adapter_type: "mock"` rejected when `is_certificate_run=True`
- [x] Runtime rule 7: `dataset_hashes[replay_dataset_id]` must be present
- [x] Returns list of error strings (empty = valid)

---

### T1.6: Database Tables
**File:** `backend/database/models.py` (appended)
**Status:** COMPLETE (tables defined, Alembic migration deferred)

5 new tables added following existing `Mapped[]` pattern:
- `TheatreTemplate` — id, template_family, execution_path, display_name, description, schema_version, template_json, timestamps
- `Theatre` — id, user_id, template_id, state, construct_id, commitment_hash, committed_at, version_pins, dataset_hashes, progress, total_episodes, failure_count, error, resolved_at, certificate_id, timestamps
- `TheatreCertificate` — id, theatre_id, template_id, construct_id, criteria_json, scores_json, composite_score, calibration fields, evidence fields, reproducibility fields, trust fields, timestamps, integration fields
- `TheatreEpisodeScore` — id, theatre_id, certificate_id, episode_id, invocation_status, latency_ms, scores_json, composite_score, timestamps
- `TheatreAuditEvent` — id, theatre_id, event_type, from_state, to_state, detail_json, timestamp

All with proper ForeignKeys, Indexes, and `back_populates` relationships. Reuses existing `_generate_uuid` for primary key defaults.

**Acceptance Criteria:**
- [x] All 5 tables follow existing `Mapped[]` pattern
- [x] `_generate_uuid` reused for primary key defaults
- [x] Foreign keys configured correctly
- [x] Indexes match SDD §5.1
- [x] Relationships with `back_populates` configured
- [ ] Alembic migration creates all tables — **Deferred**: Migration generation requires database connection. Tables are defined correctly and ready for migration.
- [x] No modification to existing tables

---

### T1.7: Package Scaffolding
**Files:** `theatre/__init__.py`, `theatre/engine/__init__.py`, `theatre/fixtures/__init__.py`
**Status:** COMPLETE

**Acceptance Criteria:**
- [x] `theatre/__init__.py` exists
- [x] `theatre/engine/__init__.py` exists
- [x] `theatre/fixtures/__init__.py` exists
- [x] All modules from T1.1–T1.5 importable from the package

---

## Test Summary

| Module | Test File | Tests | Status |
|--------|-----------|-------|--------|
| State Machine | `tests/theatre/test_state_machine.py` | 43 | PASS |
| Canonical JSON | `tests/theatre/test_canonical_json.py` | 35 | PASS |
| Commitment | `tests/theatre/test_commitment.py` | 12 | PASS |
| Criteria Model | `tests/theatre/test_criteria.py` | 10 | PASS |
| Template Validator | `tests/theatre/test_template_validator.py` | 13 | PASS |
| **Total** | | **113** | **ALL PASS** |

Run command: `backend/.venv/bin/python -m pytest tests/theatre/ -v`

---

## Technical Decisions

1. **Import resolution**: `pyproject.toml` with `[tool.pytest.ini_options] pythonpath = ["."]` ensures `theatre` package is importable. Removed `tests/theatre/__init__.py` to prevent package shadowing.

2. **Bool/int ordering in canonical JSON**: Python `bool` subclasses `int`, so `_normalise_value()` checks `isinstance(v, bool)` before `isinstance(v, int)` to preserve type fidelity.

3. **Template validator two-phase design**: Schema validation runs first (structural), runtime rules second (semantic). Early return on schema errors avoids confusing downstream rule failures on malformed data.

4. **DB tables — Alembic deferred**: Table definitions follow existing `Mapped[]` pattern exactly. Alembic migration deferred because it requires a database connection (`alembic revision --autogenerate`). Table code is ready; migration is a one-command step when database is available.

5. **datetime.utcnow() deprecation**: 3 warnings from `commitment.py` using `datetime.utcnow()`. Kept for consistency with existing `verification_bridge.py` pattern — not refactored to avoid scope creep.

---

## Files Created

| File | Purpose |
|------|---------|
| `theatre/__init__.py` | Package root |
| `theatre/engine/__init__.py` | Engine subpackage |
| `theatre/engine/state_machine.py` | State machine (T1.1) |
| `theatre/engine/canonical_json.py` | Canonical JSON (T1.2) |
| `theatre/engine/commitment.py` | Commitment protocol (T1.3) |
| `theatre/engine/models.py` | Criteria + domain models (T1.4) |
| `theatre/engine/template_validator.py` | Template validator (T1.5) |
| `theatre/fixtures/__init__.py` | Fixtures subpackage |
| `tests/conftest.py` | Root test config |
| `tests/theatre/conftest.py` | Theatre test config |
| `tests/theatre/test_state_machine.py` | State machine tests |
| `tests/theatre/test_canonical_json.py` | Canonical JSON tests |
| `tests/theatre/test_commitment.py` | Commitment tests |
| `tests/theatre/test_criteria.py` | Criteria tests |
| `tests/theatre/test_template_validator.py` | Template validator tests |
| `pyproject.toml` | pytest configuration |

## Files Modified

| File | Change |
|------|--------|
| `backend/database/models.py` | Appended 5 new table classes (T1.6) |

---

## Known Issues

1. **Alembic migration not generated** — Requires database connection. Table definitions are complete and correct.
2. **`datetime.utcnow()` deprecation** — 3 warnings in `commitment.py`. Matches existing codebase pattern.
3. **No runtime rule 8** — SDD §8.2 lists 8 rules; rule 8 (holdout_split range) is enforced by JSON Schema `minimum`/`maximum` constraints, not by a runtime rule.
