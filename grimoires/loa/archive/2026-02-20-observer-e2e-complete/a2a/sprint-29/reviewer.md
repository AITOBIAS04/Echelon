# Sprint-29 Implementation Report

> **Cycle**: cycle-032 (Observer End-to-End Integration)
> **Sprint**: sprint-2 (global: sprint-29)
> **Goal**: Runner + Evidence + Validation
> **Status**: Implementation complete — awaiting review

---

## Summary

Implemented the full Observer Theatre runner script, evidence bundle generation, certificate schema validation, RLMF export with schema validation, determinism smoke tests, and hashing invariant tests. All 346 tests pass.

## Tasks Completed

### T2.1: Runner Script (`scripts/run_observer_theatre.py`)

Full end-to-end runner with 12-step lifecycle:

- **Identity layer**: `THEATRE_ID = "product_replay_engine_v1"` (stable engine type), `template_id = "product_observer_v1"` (from template), `certificate_id = uuid4()` (per-run)
- **Steps 0-12**: certificate_id generation → ingestion → follow-up questions → episode conversion → dataset hash → template population → template validation → commitment → replay → tier assignment → evidence bundle → certificate → schema validation → write output
- **RLMF export** (Step 9.6-9.7): Builds per-episode RLMF v2.0.1 records with deterministic UUID5 episode IDs, validates against `echelon_rlmf_schema_v2.json`
- **File inventory** (Step 9.8): Lexicographically sorted file inventory with SHA-256 per file, excludes manifest.json and certificate.json
- **CLI**: argparse with `--repo`, `--limit`, `--output-dir`, `--verbose`

**Key functions:**
- `populate_template_runtime_fields()` — deep-copies template, populates version_pins and dataset_hashes
- `certificate_to_schema_dict()` — serialises certificate to JSON Schema-compatible dict
- `build_rlmf_record()` — builds RLMF v2.0.1 record per episode with deterministic UUID5, lowercase status

### T2.2: Evidence Bundle Generation

Wired `EvidenceBundleBuilder` (Cycle-031) into runner:

- Evidence bundle at `{output_dir}/evidence_bundle_product_observer_v1/`
- All required files: manifest.json, template.json, commitment_receipt.json, ground_truth/observer_prs.jsonl, invocations/*.json, scores/per_episode.jsonl, scores/aggregate.json, certificate.json, rlmf_export.jsonl
- `validate_minimum_files()` returns empty list
- `compute_file_inventory()` — returns sorted `dict[str, str]` (relative_path → SHA-256), excludes manifest.json and certificate.json
- `compute_bundle_hash()` — `SHA-256(canonical_json(sorted_file_inventory))`
- `write_manifest()` — uses `json.dumps(data, sort_keys=True, indent=2)` for deterministic key ordering
- `write_rlmf_export()` — writes RLMF records as JSONL with sorted keys

### T2.3: Certificate Schema Validation

- Validates certificate dict against `echelon_certificate_schema.json` (20 required fields)
- All hash fields are 64-char hex
- `theatre_id` matches `^[a-z_]+_v\d+$` pattern
- Timestamps serialised as ISO 8601
- Handles `expires_at=None` for UNVERIFIED tier (far-future fallback)

### T2.4: Integration Tests

93 tests in `tests/theatre/test_observer_integration.py`:

| Test Class | Tests | Description |
|------------|-------|-------------|
| TestIdentityLayer | 4 | theatre_id/template_id/certificate_id semantics |
| TestRunnerHelpers | 4 | populate_template_runtime_fields |
| TestCertificateToSchemaDict | 4 | Serialisation + schema validation |
| TestRlmfExport | 5 | RLMF record building, UUID IDs, schema validation |
| TestEvidenceBundleGeneration | 6 | Bundle structure, hash determinism, inventory sorting |
| TestCertificateSchemaValidation | 7 | Schema field requirements |
| TestFullLifecycle | 11 | End-to-end with mock oracle + scorer |
| TestDeterminismSmokeTest | 2 | Hash identity across two runs |
| TestHashingInvariants | 7 | RFC 8785 canonical_json properties |

Plus 40 tests from sprint-28 (T1.1-T1.5) and 13 model tests.

## Additional Requirements Addressed

### Requirement 1: Identity Layer Rename
- `THEATRE_ID = "product_replay_engine_v1"` — stable engine type constant
- `template_id = populated_template["theatre_id"]` → `"product_observer_v1"` — stable template name from template file
- `certificate_id = str(uuid.uuid4())` — per-run UUID generated at Step 0

### Requirement 2: RLMF Schema Exit Gate
- `build_rlmf_record()` creates per-episode RLMF v2.0.1 records
- Runner validates all records against `echelon_rlmf_schema_v2.json` at Step 9.7
- `RLMF_NAMESPACE` UUID for deterministic UUID5 episode IDs
- `invocation_status` lowercased per schema enum

### Requirement 3: Determinism Smoke Test
- `TestDeterminismSmokeTest.test_determinism_commitment_and_dataset_hash` — runs twice, asserts identical hashes
- `TestDeterminismSmokeTest.test_determinism_evidence_bundle_hash` — pins non-deterministic sources (uuid4, committed_at) via mock patches, asserts identical evidence_bundle_hash

### Requirement 4: Hashing Invariants
- All hashes use RFC 8785 `canonical_json()` — verified in `TestHashingInvariants`
- File inventory keys lexicographically sorted — verified in `test_file_inventory_keys_are_sorted`
- Bundle hash: `SHA-256(canonical_json(sorted_file_inventory))` — verified in `test_evidence_bundle_hash_uses_canonical_json`
- Manifest file_inventory keys sorted in written JSON — verified in `test_manifest_has_sorted_keys`

## Engine Changes (Cycle-031)

### `theatre/engine/replay.py`
- Added `oracle_output: dict[str, Any] | None = None` to `EpisodeResult` — stores raw construct response for RLMF export
- Populated from `response.output_data` in all three status cases (REFUSED, ERROR, SUCCESS)

### `theatre/engine/evidence_bundle.py`
- `write_manifest()` — uses `json.dumps(data, sort_keys=True, indent=2)` for deterministic key ordering
- `write_rlmf_export()` — new method for RLMF JSONL output
- `compute_file_inventory()` — returns sorted dict, excludes manifest.json and certificate.json
- `compute_bundle_hash()` — uses `canonical_json(inventory)` for deterministic hashing

### `tests/theatre/test_evidence_bundle.py`
- Updated `test_hash_requires_manifest` → `test_hash_on_empty_bundle` — new compute_bundle_hash no longer requires manifest.json (computes from file inventory)

## Files Modified

| File | Changes |
|------|---------|
| `scripts/run_observer_theatre.py` | Major rewrite: identity layer, RLMF export, file inventory, schema validation |
| `theatre/engine/replay.py` | Added `oracle_output` field to `EpisodeResult` |
| `theatre/engine/evidence_bundle.py` | Added `write_rlmf_export`, `compute_file_inventory`, updated `compute_bundle_hash` and `write_manifest` |
| `tests/theatre/test_observer_integration.py` | Added 50+ new tests for identity layer, RLMF, determinism, hashing invariants |
| `tests/theatre/test_evidence_bundle.py` | Fixed `test_hash_on_empty_bundle` for new bundle hash implementation |

## Test Results

```
346 passed, 0 failures
```

All tests run without API keys using mock oracle + mock scorer.
