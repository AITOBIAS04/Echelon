# Sprint Plan: Observer End-to-End Integration (Cycle-032)

> **Cycle**: cycle-032
> **PRD**: grimoires/loa/prd.md
> **SDD**: grimoires/loa/sdd.md
> **Sprints**: 2
> **Developer**: 1 (AI)

---

## Sprint 1: Integration Bridges + Template

> Global ID: TBD | Local ID: sprint-1
> Goal: Build the three bridge adapters (ground truth, oracle, scoring) and the real Observer Theatre template. All bridges unit-tested.
> Depends on: Cycle-027 + Cycle-031 (frozen, already complete)

### Tasks

#### T1.1: Ground Truth Adapter
**Description:** Create `theatre/integration/ground_truth_adapter.py` — converts Cycle-027 `GroundTruthRecord` to Cycle-031 `GroundTruthEpisode`.

**Acceptance Criteria:**
- [x] `convert_single_record(record, follow_up_question) -> GroundTruthEpisode`
- [x] `convert_records_to_episodes(records, follow_up_questions) -> list[GroundTruthEpisode]`
- [x] `episode_id` = `record.id` (PR number)
- [x] `input_data` includes: title, description, diff_content, files_changed, follow_up_question
- [x] `labels` includes: author, url, repo, github_labels
- [x] `metadata` includes: timestamp (ISO string)
- [x] `expected_output` = None
- [x] Handles empty fields gracefully (empty diff, no labels)

**Tests:** `tests/theatre/test_observer_integration.py` — field mapping, batch conversion, edge cases.

---

#### T1.2: Oracle Adapter Bridge
**Description:** Create `theatre/integration/oracle_bridge.py` — implements Cycle-031's `OracleAdapter` protocol, delegates to Cycle-027's oracle adapter.

**Acceptance Criteria:**
- [x] `ObserverOracleAdapter` class implementing `OracleAdapter` protocol
- [x] `invoke(input_data: dict) -> dict` method matching Theatre protocol
- [x] Unpacks `input_data` fields (title, description, diff_content, etc.)
- [x] Extracts `follow_up_question` from `input_data`
- [x] Calls Anthropic API to generate summary + key_claims + follow-up response
- [x] Packs output into response dict: `{summary, key_claims, follow_up_response, metadata}`
- [x] Propagates exceptions (no swallowing — ReplayEngine handles retries)

**Tests:** `tests/theatre/test_observer_integration.py` — mock API, field packing/unpacking, error propagation.

**Note:** Renamed from `VerificationOracleBridge` to `ObserverOracleAdapter` — echelon-verify Cycle-027 has only the scoring ABC implemented, so this adapter calls Anthropic directly rather than bridging.

---

#### T1.3: Scoring Bridge
**Description:** Create `theatre/integration/scoring_bridge.py` — implements Cycle-031's `ScoringFunction` protocol, delegates to Cycle-027's `AnthropicScorer`.

**Acceptance Criteria:**
- [x] `ObserverScoringFunction` class implementing `ScoringFunction` protocol
- [x] `score(criteria_id, ground_truth, oracle_output) -> float` matching Theatre protocol
- [x] Extracts PR fields from `ground_truth.input_data`
- [x] Extracts oracle output fields from `oracle_output`
- [x] Maps criteria_ids to scoring methods: precision, recall, reply_accuracy
- [x] Returns float score in [0.0, 1.0] per criterion
- [x] Handles scoring failures gracefully (returns 0.0 for failed criteria with warning log)

**Tests:** `tests/theatre/test_observer_integration.py` — mock API, all 3 criteria, failure handling.

**Note:** Renamed from `VerificationScoringBridge` to `ObserverScoringFunction` — implements `ScoringFunction` protocol directly using Cycle-027's scoring prompt templates.

---

#### T1.4: Observer Theatre Template (Real)
**Description:** Create `theatre/integration/observer_template.json` — production Observer template with real criteria and local adapter config.

**Acceptance Criteria:**
- [x] `schema_version`: `"2.0.1"`
- [x] `theatre_id`: `"product_observer_v1"`
- [x] `template_family`: `"PRODUCT"`
- [x] `execution_path`: `"replay"`
- [x] `criteria.criteria_ids`: `["precision", "recall", "reply_accuracy"]`
- [x] `criteria.weights`: `{precision: 0.4, recall: 0.4, reply_accuracy: 0.2}`
- [x] `product_theatre_config.adapter_type`: `"local"`
- [x] `product_theatre_config.ground_truth_source`: `"GITHUB_API"`
- [x] `product_theatre_config.construct_under_test`: `"community_oracle_v1"`
- [x] Passes `TemplateValidator` (schema + 8 runtime rules)

**Tests:** Template validation test in `tests/theatre/test_observer_integration.py`.

---

#### T1.5: Package Init + Imports
**Description:** Create `theatre/integration/__init__.py` with public API exports. Ensure both cycles' code is importable from the integration module.

**Acceptance Criteria:**
- [x] `theatre/integration/__init__.py` exports: `GroundTruthAdapter`, `ObserverOracleAdapter`, `ObserverScoringFunction`, `load_observer_template`
- [x] `load_observer_template()` loads and returns the template JSON
- [x] Verify imports work: `from theatre.integration import ObserverOracleAdapter`
- [x] Verify all public exports importable (6 import smoke tests pass)

**Tests:** Import smoke test in `tests/theatre/test_observer_integration.py`.

---

### Sprint 1 Success Criteria

- All 3 bridge adapters implemented with correct interface compliance
- Observer Theatre template passes TemplateValidator
- GroundTruthRecord → GroundTruthEpisode mapping preserves all fields
- Oracle bridge correctly delegates to Cycle-027 adapter
- Scoring bridge correctly delegates to AnthropicScorer
- All unit tests passing

---

## Sprint 2: Runner + Evidence + Validation

> Global ID: TBD | Local ID: sprint-2
> Goal: Build the runner script, evidence bundle generation, certificate schema validation, and integration tests.
> Depends on: Sprint 1 (bridges + template)

### Tasks

#### T2.1: Runner Script
**Description:** Create `scripts/run_observer_theatre.py` — single entry point for end-to-end Observer Theatre execution.

**Acceptance Criteria:**
- [x] `async def main(repo_url, limit, output_dir, github_token, anthropic_api_key) -> Path`
- [x] Step 0: Generate `certificate_id = str(uuid.uuid4())` at run start (before any scoring)
- [x] Step 1: Ingests PRs via `GitHubIngester` (Cycle-027)
- [x] Step 2: Generates follow-up questions via `AnthropicScorer.generate_follow_up_question()`
- [x] Step 3: Converts to `GroundTruthEpisode[]` via `GroundTruthAdapter`
- [x] Step 4: Computes dataset hash via `canonical_json()` + SHA-256
- [x] Step 4.5: Populates template `version_pins` (real construct version) and `dataset_hashes` (computed hash) — replaces placeholders
- [x] Step 5: Loads + validates Observer template via `TemplateValidator`
- [x] Step 5.5: Generates `template_id` distinct from `theatre_id` (SHA-256 of canonical_json(template) — content-addressed)
- [x] Step 6: Creates `CommitmentReceipt` via `CommitmentProtocol` (using populated template with real version_pins + dataset_hashes)
- [x] Step 7: Builds `ReplayEngine` with oracle + scoring bridges
- [x] Step 8: Runs replay with progress callback (prints progress)
- [x] Step 9: Assigns tier via `TierAssigner`
- [x] Step 10: Builds `TheatreCalibrationCertificate` with `certificate_id` from Step 0, `template_id` from Step 5.5, all other fields
- [x] Step 11: Validates certificate against `echelon_certificate_schema.json`
- [x] Step 12: Writes certificate to `{output_dir}/certificates/product_observer_v1.json`
- [x] CLI interface via `argparse`: `--repo`, `--limit`, `--output-dir`, `--verbose`
- [x] Reads `GITHUB_TOKEN` and `ANTHROPIC_API_KEY` from environment
- [x] Handles errors with clear messages (missing API keys, GitHub failures)
- [x] All hashing uses `canonical_json()` (RFC 8785) — verified for commitment, dataset, and template_id

**Tests:** Integration test with mock oracle + mock scorer in `tests/theatre/test_observer_integration.py`.

---

#### T2.2: Evidence Bundle Generation
**Description:** Wire `EvidenceBundleBuilder` (Cycle-031) into the runner to generate the full evidence bundle.

**Acceptance Criteria:**
- [x] Evidence bundle directory: `{output_dir}/evidence_bundle_product_observer_v1/`
- [x] `manifest.json` — theatre_id, template_id, construct_id, execution_path, commitment_hash
- [x] `template.json` — Observer template snapshot
- [x] `commitment_receipt.json` — full receipt with hash + pins
- [x] `ground_truth/observer_prs.jsonl` — ingested episodes
- [x] `invocations/{episode_id}.json` — per-episode request/response
- [x] `scores/per_episode.jsonl` — per-episode scores
- [x] `scores/aggregate.json` — mean scores per criterion
- [x] `certificate.json` — issued certificate
- [x] `validate_minimum_files()` returns empty list

**Tests:** Bundle completeness test in `tests/theatre/test_observer_integration.py`.

---

#### T2.3: Certificate Schema Validation
**Description:** Validate the output certificate against `docs/schemas/echelon_certificate_schema.json`.

**Acceptance Criteria:**
- [x] Load schema from `docs/schemas/echelon_certificate_schema.json`
- [x] Validate certificate dict against schema using `jsonschema.validate()`
- [x] All required fields present (20 required fields per schema)
- [x] `theatre_id` matches pattern `^[a-z_]+_v\d+$`
- [x] All hash fields are 64-char hex
- [x] `verification_tier` in `["UNVERIFIED", "BACKTESTED", "PROVEN"]`
- [x] `execution_path` in `["replay", "market"]`
- [x] Timestamps in ISO 8601 format
- [x] Certificate-to-dict serialisation helper for schema validation

**Tests:** Schema validation test in `tests/theatre/test_observer_integration.py`.

---

#### T2.4: Integration Tests
**Description:** End-to-end integration tests covering the full runner lifecycle with mock oracle and mock scorer.

**Acceptance Criteria:**
- [x] Test: full lifecycle produces certificate with all fields
- [x] Test: certificate validates against JSON Schema
- [x] Test: evidence bundle passes minimum-file validation
- [x] Test: commitment hash is reproducible (same inputs → same hash)
- [x] Test: scoring bridge produces scores for all 3 criteria
- [x] Test: runner handles oracle failure gracefully (episode marked as ERROR)
- [x] All tests runnable without API keys (mock oracle + mock scorer)

**Tests:** `tests/theatre/test_observer_integration.py`.

---

### Sprint 2 Success Criteria

- Runner script executes end-to-end (with mocks)
- Certificate validates against `echelon_certificate_schema.json`
- Evidence bundle has all required files
- Commitment hash is reproducible
- All tests passing without API keys
- Runner can be invoked with real keys for live run

---

## Risk Mitigation

| Risk | Sprint | Mitigation |
|------|--------|------------|
| Cycle-027 imports fail | 1 | Test imports early in T1.5; add to Python path if needed |
| AnthropicScorer API differences | 1 | Scoring bridge wraps with try/except; mock tests verify interface |
| Large diffs cause OOM | 2 | Cycle-027 already truncates at 100KB |
| jsonschema not installed | 2 | Add to dev dependencies; conditional import with clear error |
| Certificate schema evolution | 2 | Schema is v1.0.0, frozen; validate at test time |
