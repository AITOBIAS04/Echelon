# Sprint 26 — Execution Engine: Implementation Report

> Sprint: sprint-26 (global) | sprint-2 (local)
> Cycle: cycle-031 — Theatre Template Engine
> Status: **COMPLETE** — All 6 tasks implemented, 212 tests passing (99 new + 113 from sprint-25)

---

## Task Summary

| Task | Title | Status | Tests |
|------|-------|--------|-------|
| T2.1 | Oracle Invocation Contract | Done | 15 |
| T2.2 | Theatre Scoring Provider | Done | 11 |
| T2.3 | Replay Engine | Done | 9 |
| T2.4 | Resolution State Machine | Done | 11 |
| T2.5 | Evidence Bundle Builder | Done | 16 |
| T2.6 | Certificate + Tier + Gate | Done | 38 |
| **Total** | | **6/6** | **99 new (212 total)** |

---

## T2.1: Oracle Invocation Contract

**File:** `theatre/engine/oracle_contract.py`
**Tests:** `tests/theatre/test_oracle_contract.py` (15 tests)

### What was built

- `OracleInvocationRequest` — standardised request envelope with auto-generated `invocation_id`, theatre/episode/construct identifiers, input data, and configurable metadata
- `OracleInvocationResponse` — response envelope with status enum (SUCCESS/TIMEOUT/ERROR/REFUSED), latency tracking, error detail
- `OracleInvocationMetadata` — timeout (30s default), retry count (2 default), exponential backoff (5s default), deterministic flag, sanitise flag
- `OracleAdapter` Protocol — matches existing echelon-verify contract
- `MockOracleAdapter` — configurable responses, fail/timeout/refuse per-episode
- `invoke_oracle()` async function — full retry loop with exponential backoff, timeout via `asyncio.wait_for()`, REFUSED bypasses retry, structured status reporting

### Acceptance Criteria

- [x] `OracleInvocationRequest` with all fields from SDD §4.5
- [x] `OracleInvocationResponse` with status enum: SUCCESS, TIMEOUT, ERROR, REFUSED
- [x] `OracleInvocationMetadata` with timeout, retry, deterministic, sanitise_input defaults
- [x] Adapter wrapper function: takes request, calls adapter, returns response
- [x] Retry logic with configurable backoff
- [x] Timeout handling returns `TIMEOUT` status
- [x] Error handling returns `ERROR` status with detail

---

## T2.2: Theatre Scoring Provider

**File:** `theatre/engine/scoring.py`
**Tests:** `tests/theatre/test_scoring.py` (11 tests)

### What was built

- `ScoringFunction` Protocol — pluggable scoring interface
- `SimpleScoringFunction` — exact-match scoring for testing
- `TheatreScoringProvider` — scores construct outputs per committed criteria_ids
  - `score_episode()` — invokes scoring function per criterion, clamps to [0.0, 1.0]
  - `compute_composite()` — weighted aggregate using `TheatreCriteria.weights`, equal weight fallback when weights dict is empty

### Acceptance Criteria

- [x] `score_episode()` returns `dict[str, float]` mapping criteria_id → score (0.0–1.0)
- [x] `compute_composite()` produces weighted aggregate using `TheatreCriteria.weights`
- [x] Equal weight fallback when `weights` dict is empty
- [x] Handles missing criteria gracefully (score = 0.0 for missing)

---

## T2.3: Replay Engine

**File:** `theatre/engine/replay.py`
**Tests:** `tests/theatre/test_replay_engine.py` (9 tests)

### What was built

- `EpisodeResult` — per-episode outcome with status, scores, oracle response reference
- `ReplayResult` — aggregate with all episode results, composite score, failure rate, dataset hash
- `DatasetHashMismatchError` — raised when dataset hash doesn't match commitment
- `ReplayEngine` class:
  - Dataset hash verification before first episode (computed via `canonical_json` + SHA-256)
  - Sequential episode processing: invoke → score → record
  - TIMEOUT/ERROR episodes scored as zero (affect failure rate)
  - REFUSED episodes excluded from scoring (logged as excluded)
  - Failure rate tracking: >20% caps at UNVERIFIED
  - Progress callback invoked after each episode
  - Returns structured `ReplayResult`

### Acceptance Criteria

- [x] Verifies dataset hash matches commitment before first episode
- [x] Processes episodes sequentially
- [x] For each episode: build request → invoke → record invocation → score → record score
- [x] Progress callback called after each episode
- [x] Failure rate tracked: >20% failures → cap at UNVERIFIED
- [x] TIMEOUT/ERROR episodes scored as missing
- [x] REFUSED episodes excluded from scoring, logged
- [x] Returns `ReplayResult` with all episode scores + aggregate + failure rate
- [x] Dataset hash mismatch → immediate failure

---

## T2.4: Resolution State Machine

**File:** `theatre/engine/resolution.py`
**Tests:** `tests/theatre/test_resolution.py` (11 tests)

### What was built

- `ResolutionStep` — step definition with type, construct_id, escalation_path
- `StepOutcome` — per-step result with status, output, error, timing
- `ResolutionResult` — aggregate with final status, all outcomes, audit events
- `ResolutionContext` — theatre context with version pins
- `VersionPinError` — raised on missing construct version pin
- `ResolutionStateMachine`:
  - Executes steps in committed order
  - `construct_invocation` — invokes construct via oracle contract with version pin validation
  - `deterministic_computation` — executes without oracle (SUCCESS)
  - `hitl_rubric` — produces PENDING_HITL status
  - `aggregation` — combines previous step outputs (SUCCESS)
  - Escalation paths on step failure (jumps to named step)
  - Failure without escalation → terminates entire resolution
  - Audit events generated per step

### Acceptance Criteria

- [x] Executes steps in committed order
- [x] `construct_invocation` steps invoke construct via oracle contract
- [x] `deterministic_computation` steps execute without oracle
- [x] `hitl_rubric` steps produce `PENDING_HITL` status
- [x] `aggregation` steps combine previous step outputs
- [x] `escalation_path` followed on step failure
- [x] Version pin validation: every `construct_id` has matching pin
- [x] Returns `ResolutionResult` with outcomes + audit trail

---

## T2.5: Evidence Bundle Builder

**File:** `theatre/engine/evidence_bundle.py`
**Tests:** `tests/theatre/test_evidence_bundle.py` (16 tests)

### What was built

- `EvidenceBundleBuilder` — creates auditable evidence directory structure:
  - `evidence_bundle_{theatre_id}/` base directory
  - Subdirectories: `ground_truth/`, `invocations/`, `scores/`
  - `write_manifest()` — BundleManifest → manifest.json
  - `write_template()` — template snapshot → template.json
  - `write_commitment_receipt()` — CommitmentReceipt → commitment_receipt.json
  - `write_ground_truth()` — dataset → JSONL file
  - `write_invocation()` — per-episode request/response → JSON
  - `write_episode_score()` — append to per_episode.jsonl
  - `write_aggregate_scores()` — aggregate.json
  - `write_certificate()` — certificate.json
  - `append_audit_event()` — append to audit_trail.jsonl
  - `compute_bundle_hash()` — SHA-256 over manifest.json bytes
  - `validate_minimum_files()` — returns list of missing required files

### Acceptance Criteria

- [x] Creates directory structure per SDD §4.10
- [x] `write_manifest()`, `write_template()`, `write_commitment_receipt()` produce valid JSON files
- [x] `write_ground_truth()` writes JSONL
- [x] `write_invocation()` writes per-episode JSON
- [x] `write_episode_score()` appends to per_episode.jsonl
- [x] `write_aggregate_scores()` writes aggregate.json
- [x] `write_certificate()` writes certificate.json
- [x] `append_audit_event()` appends to audit_trail.jsonl
- [x] `compute_bundle_hash()` produces deterministic SHA-256 over manifest
- [x] `validate_minimum_files()` returns missing required files (empty = valid)

---

## T2.6: Calibration Certificate + Tier Assigner + Constraint Gate

**Files:**
- `theatre/engine/certificate.py`
- `theatre/engine/tier_assigner.py`
- `theatre/engine/constraint_gate.py`

**Tests:**
- `tests/theatre/test_certificate.py` (10 tests)
- `tests/theatre/test_tier_assigner.py` (22 tests)
- `tests/theatre/test_constraint_gate.py` (6 tests)

### What was built

**TheatreCalibrationCertificate** — Pydantic model with all fields from SDD §4.8:
- Core: certificate_id, theatre_id, template_id, construct_id, criteria, scores, composite_score
- Evidence: replay_count, evidence_bundle_hash, ground_truth_hash, construct_version, scorer_version
- Versioning: methodology_version, dataset_hash, construct_chain_versions
- Tier: verification_tier (UNVERIFIED/BACKTESTED/PROVEN)
- Provenance: commitment_hash, theatre_committed_at, theatre_resolved_at, ground_truth_source, execution_path
- Optional: precision, recall, brier_score, ece, expires_at

**TierAssigner** — deterministic tier assignment with boundary rules:
- `assign()` — UNVERIFIED (<50 replays, >20% failure, missing pins/scores/hash, disputes), BACKTESTED (≥50 + full evidence), PROVEN (3+ months + telemetry + attestation)
- `compute_expiry()` — 90 days BACKTESTED, 180 days PROVEN, None UNVERIFIED
- `TierHistory` — model tracking consecutive months, telemetry, attestation

**ConstraintYieldingGate** — review preference resolution:
- UNVERIFIED + skip → full (forced upgrade)
- UNVERIFIED + full → full
- BACKTESTED/PROVEN + any → passthrough

### Acceptance Criteria

- [x] `TheatreCalibrationCertificate` Pydantic model with all fields from SDD §4.8
- [x] `TierAssigner.assign()` returns correct tier for all boundary conditions
- [x] `TierAssigner.compute_expiry()` returns correct expiry dates
- [x] `ConstraintYieldingGate.resolve_review_preference()` correct for all combinations

---

## Test Results

```
212 passed, 0 failed in 166.37s
```

| Test File | Count | Coverage |
|-----------|-------|----------|
| test_oracle_contract.py | 15 | Models, mock adapter, invoke with retry/timeout/refused |
| test_scoring.py | 11 | Score episode, composite weighted/equal, clamping, simple scorer |
| test_replay_engine.py | 9 | Full lifecycle, hash verification, failure rate, callbacks |
| test_resolution.py | 11 | Linear exec, construct invocation, escalation, HITL, audit |
| test_evidence_bundle.py | 16 | All writers, hash, minimum file validation |
| test_tier_assigner.py | 22 | All boundary conditions, expiry, TierHistory |
| test_certificate.py | 10 | Model creation, serialisation, round-trip, all tiers |
| test_constraint_gate.py | 6 | All tier + preference combinations |
| *(Sprint 1 tests)* | 113 | No regressions |

---

## Technical Decisions

1. **`OracleInvocationMetadata.timeout_seconds: int`** — Integer seconds (not float) for Pydantic v2 strict validation. Backoff uses float for sub-second granularity.

2. **MockOracleAdapter per-episode control** — `fail_episodes`, `timeout_episodes`, `refuse_episodes` sets allow targeted failure simulation per episode ID. Timeout simulation sleeps 100s (always exceeds any test timeout).

3. **ReplayEngine dataset hash** — Computed via `canonical_json()` + SHA-256 over the entire ground truth list. Verifies against commitment before first episode.

4. **ResolutionStateMachine escalation** — On step failure with `escalation_path`, marks step as ESCALATED and jumps to named step. If no escalation path, terminates with FAILED.

5. **EvidenceBundleBuilder hash scope** — `compute_bundle_hash()` hashes only `manifest.json` bytes (not entire directory). The manifest contains the file inventory for downstream verification.

6. **TierAssigner boundary precision** — Exactly 20% failure rate is still allowed (≤ 0.20). Exactly 50 replays is BACKTESTED threshold (≥ 50).

---

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `theatre/engine/oracle_contract.py` | 173 | Oracle invocation contract |
| `theatre/engine/scoring.py` | ~100 | Scoring provider |
| `theatre/engine/replay.py` | ~160 | Replay engine |
| `theatre/engine/resolution.py` | ~180 | Resolution state machine |
| `theatre/engine/evidence_bundle.py` | ~170 | Evidence bundle builder |
| `theatre/engine/certificate.py` | ~60 | Calibration certificate model |
| `theatre/engine/tier_assigner.py` | ~80 | Tier assignment logic |
| `theatre/engine/constraint_gate.py` | ~25 | Constraint yielding gate |
| `tests/theatre/test_oracle_contract.py` | 177 | Oracle contract tests |
| `tests/theatre/test_scoring.py` | ~120 | Scoring tests |
| `tests/theatre/test_replay_engine.py` | ~180 | Replay engine tests |
| `tests/theatre/test_resolution.py` | 220 | Resolution SM tests |
| `tests/theatre/test_evidence_bundle.py` | 178 | Evidence bundle tests |
| `tests/theatre/test_tier_assigner.py` | 241 | Tier assigner tests |
| `tests/theatre/test_certificate.py` | 99 | Certificate tests |
| `tests/theatre/test_constraint_gate.py` | 32 | Constraint gate tests |

## Files Modified

None. All sprint-2 work is new files.

---

## Known Issues

1. **`datetime.utcnow()` deprecation** — Used in `OracleInvocationResponse.responded_at` and `CommitmentProtocol.create_receipt()`. Python 3.12+ warns; should migrate to `datetime.now(UTC)`. Non-blocking.

2. **Test suite duration (166s)** — Primarily from actual `asyncio.sleep()` waits in retry and timeout tests. Could be reduced with mock time but tests are integration-honest as-is.

---

## Sprint 2 Success Criteria Verification

- [x] ReplayEngine completes full lifecycle with mock adapter
- [x] Dataset hash mismatch correctly halts execution
- [x] >20% failure rate caps certificate at UNVERIFIED
- [x] Resolution state machine follows escalation paths
- [x] Evidence bundle passes minimum-file validation
- [x] Tier assignment correct at all boundary conditions
- [x] Constraint yielding gate blocks UNVERIFIED + skip
- [x] All unit tests passing (212/212)
