# Sprint Plan: Verifier MCP Server + Loa Construct Calibration Pilot

**Cycle:** 008
**Sprints:** 2
**Total Tasks:** 12

---

## Sprint 1 — Verifier MCP Server v1.0

**Goal:** Wrap existing Python verifier in an MCP server with five stateless tools over stdio transport.

**Global Sprint ID:** 12

### Task 1: MCP SDK Installation + Server Scaffold

Install `mcp` Python SDK. Create `mcp/` package structure: `__init__.py`, `server.py`, `tools/__init__.py`, `models/__init__.py`, `tests/__init__.py`. Implement `server.py` with stdio transport, `list_tools()` returning 5 tool definitions, and `call_tool()` dispatch.

**Acceptance Criteria:**
- [ ] `mcp` SDK installed and importable
- [ ] `python3 -m mcp.server` starts without error (empty tool list)
- [ ] Server scaffolding matches SDD §2.2

### Task 2: _meta Envelope + Error Models

Implement `mcp/models/meta.py` (_meta envelope with engine_version, schema_versions, timestamp), `mcp/models/errors.py` (4 error codes + standardised format), `mcp/models/inputs.py` (InlineInput mode object).

**Acceptance Criteria:**
- [ ] `Meta` dataclass serialises correctly
- [ ] Error response format matches SDD §2.4
- [ ] InlineInput validates `mode: "inline"` and rejects unknown modes

### Task 3: echelon_verify Tool

Implement `mcp/tools/verify.py`. Accepts certificate JSON (inline) + evidence_bundle_path. Delegates to existing `echelon_verify.py` verification logic. Returns `{ overall_verdict, checks[], _meta }`.

**Acceptance Criteria:**
- [ ] Cycle-007 escrow certificate returns PASS via MCP verify
- [ ] Tampered certificate returns FAIL
- [ ] Missing evidence directory returns ERROR with `INPUT_MALFORMED`
- [ ] 3-4 tests in `mcp/tests/test_verify.py`

### Task 4: echelon_inspect + echelon_hash Tools

Implement `mcp/tools/inspect.py` (certificate summary, no verification) and `mcp/tools/hash.py` (canonical hash, imports from `osint_pipeline/engine/canonical.py` — no new implementation).

**Acceptance Criteria:**
- [ ] inspect returns certificate_id, template_id, composite_score, verification_tier
- [ ] hash produces identical output to existing `canonical_hash()` utility
- [ ] hash output format: `{ hash: "sha256:...", _meta }` (note `sha256:` prefix)
- [ ] Errata: code references "Echelon Canonical JSON v0" (not RFC 8785)
- [ ] 5-7 tests across `test_inspect.py` and `test_hash.py`

### Task 5: echelon_schema_check + echelon_replay Tools

Implement `mcp/tools/schema_check.py` (schema validation) and `mcp/tools/replay.py` (structural consistency check for template + fixtures).

**Acceptance Criteria:**
- [ ] schema_check detects missing required fields
- [ ] replay detects dataset hash mismatch
- [ ] replay detects criteria weight sum != 1.0
- [ ] 4-6 tests across `test_schema_check.py` and `test_replay.py`

### Task 6: Errata Application + Integration Verification

Apply errata: replace all "RFC 8785" references with "Echelon Canonical JSON v0", ensure `resolved_inputs` sorted by `(param, id)`. Verify all existing Cycle-007 certificates (escrow, waterfall, reconciliation, arrears) through MCP `echelon_verify`.

**Acceptance Criteria:**
- [ ] All 4 Cycle-007 certificates PASS via MCP verify
- [ ] No "RFC 8785" string in any `mcp/` file
- [ ] `resolved_inputs` sorting applied where relevant
- [ ] All existing 447+ tests pass
- [ ] 2-3 tests in `test_errors.py` for standardised error format
- [ ] Total new tests: 15-20

---

## Sprint 2 — Loa Construct Calibration Pilot

**Goal:** Re-certify community_oracle_v1 through hardened pipeline, producing evidence bundle with MCP Verifier PASS.

**Global Sprint ID:** 13

### Task 1: CONSTRUCT_CALIBRATION_V1 Template

Create `theatre/fixtures/construct_calibration/templates/CONSTRUCT_CALIBRATION_V1.template.json`. Product family template with precision (0.40), recall (0.40), reply_accuracy (0.20). Fields match SDD §3.1.

**Acceptance Criteria:**
- [ ] Template JSON matches schema used by other theatre templates
- [ ] `criteria.weights` sum to 1.0
- [ ] `template_family: "PRODUCT"`, `execution_path: "replay"`, `inquiry_class: "INSPECTION"`
- [ ] `dataset_hash` field present (populated after fixture creation)

### Task 2: Construct Calibration Scorer

Create `theatre/scoring/construct_calibration_scorer.py`. Three criteria scored against pre-annotated fixtures. Deterministic: no LLM call at scoring time. Uses float comparison (not Decimal arithmetic).

**Acceptance Criteria:**
- [ ] Implements `ScoringFunction` protocol (`score(criteria_id, ground_truth, oracle_output) → float`)
- [ ] precision = supported_claims / total_claims
- [ ] recall = surfaced_changes / total_important_changes
- [ ] reply_accuracy = grounded_answers / total_answers
- [ ] All three criteria return values in [0.0, 1.0]
- [ ] Tests in `tests/theatre/test_construct_calibration.py`

### Task 3: Fixture Dataset

Create `theatre/fixtures/construct_calibration/datasets/community_oracle_v1_fixtures.json`. Convert first-run certificate replay data into annotated fixture format. 10+ records, each with `input_data` (PR diff, construct summary, Q&A) and `expected_output` (per-criterion annotations).

**Acceptance Criteria:**
- [ ] 10+ records in fixture dataset
- [ ] Each record has `record_id`, `input_data`, `expected_output`
- [ ] `expected_output` contains `precision_annotations`, `recall_annotations`, `reply_accuracy_annotations`
- [ ] Annotations are binary (supported/unsupported, surfaced/missed, grounded/ungrounded)
- [ ] Dataset hash committed in CONSTRUCT_CALIBRATION_V1 template
- [ ] Score distributions approximate first-run results (precision ~0.8, recall ~0.55, reply_accuracy ~0.8)
- [ ] Fixture JSON is valid canonical JSON (deterministic hash)

### Task 4: Dedicated Construct Calibration Runner

Create `scripts/run_construct_calibration.py` — dedicated entrypoint, separate from `run_two_rail_certificates.py`.

**MUST:**
1. Accept `--construct community_oracle_v1` (extensible to other constructs)
2. Accept `--construct-source` override (default: `/Users/tobiasharber/Developer/construct-observer`)
3. Load CONSTRUCT_CALIBRATION_V1 template from `theatre/fixtures/construct_calibration/templates/`
4. Load fixture dataset from `theatre/fixtures/construct_calibration/datasets/`
5. Score each record via `construct_calibration_scorer.py` (N=10+, UNVERIFIED tier)
6. Build evidence bundle: `inputs/`, `expected/`, `scores/` (per_record.json + aggregate.json), `manifest.json`
7. Compute evidence bundle hash (SHA-256 of canonical manifest)
8. Generate CalibrationCertificate with all required fields
9. Verify certificate via MCP `echelon_verify` tool
10. Write outputs to `output/construct_calibration/community_oracle_v1/`
11. Produce `output/construct_calibration/index.json` for batch runs
12. Exit 0 on success

**MUST NOT:**
- Import from or call `run_two_rail_certificates.py`
- Assume Decimal arithmetic scoring (uses float-safe comparison)
- Hardcode construct-observer paths

**Acceptance Criteria:**
- [ ] `python3 scripts/run_construct_calibration.py --construct community_oracle_v1` exits 0
- [ ] Certificate JSON written to output directory
- [ ] Evidence bundle written with valid manifest (`inputs/`, `expected/`, `scores/`, `manifest.json`)
- [ ] `echelon_verify` returns PASS for the generated certificate
- [ ] Re-run produces identical evidence bundle hash (determinism check)
- [ ] No import path touches `run_two_rail_certificates.py`
- [ ] Shared utility logic extracted to `scripts/_certificate_pipeline.py` only if duplication exceeds ~30 lines

### Task 5: MCP Verification Loop + Integration Tests

Create `tests/mcp/test_mcp_integration.py`. End-to-end integration test: generate certificate → verify via MCP → assert PASS. Also test tamper detection.

**Acceptance Criteria:**
- [ ] Test generates certificate via `run_construct_calibration.py` flow
- [ ] Test calls MCP `echelon_verify` programmatically
- [ ] PASS assertion succeeds
- [ ] Tampered certificate → FAIL assertion succeeds
- [ ] Determinism test: two runs produce identical evidence bundle hash
- [ ] All existing 447+ tests still pass

### Task 6: Results Summary for Soju

Produce `reports/construct_calibration_pilot.md` — one-page summary:

- Construct: community_oracle_v1
- Template: CONSTRUCT_CALIBRATION_V1
- Criteria: precision (0.40), recall (0.40), reply_accuracy (0.20)
- Per-criterion and composite scores
- Evidence bundle hash
- Verifier verdict: PASS (via MCP `echelon_verify`)
- Verification tier: UNVERIFIED (10 replays; needs 50+ for BACKTESTED)
- How to verify independently: `echelon_verify verify certificate.json evidence/`

**Acceptance Criteria:**
- [ ] Report contains all fields listed above
- [ ] Scores match actual pipeline output
- [ ] Verification command is copy-pasteable and works
