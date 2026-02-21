# SDD: Two-Rail Deterministic Product Theatres (Cycle-033)

> **Version**: 1.0
> **Date**: 2026-02-21
> **PRD**: `grimoires/loa/prd.md` (Cycle-033)

---

## 1. Executive Summary

Build three deterministic scorer functions and a runner script that produce CalibrationCertificates for the Two-Rail marketplace financial verification domains. All scoring is pure arithmetic/policy binary checks — no LLM, no API calls, no network. Reuses the existing Cycle-031 ReplayEngine, CommitmentProtocol, EvidenceBundleBuilder, TierAssigner, and TheatreCalibrationCertificate.

---

## 2. Architecture

### Component Diagram

```
theatre/fixtures/two_rail_theatres_v0_1/
  ├── templates/   (3 template JSONs)
  └── datasets/    (3 fixture JSONs, 10 records each)
          │
          ▼
scripts/run_two_rail_theatres.py        ← NEW (runner)
          │
          ├── Loads templates + datasets
          ├── Converts records → GroundTruthEpisode[]
          ├── Creates DeterministicOracleAdapter  ← NEW
          │     └── Recomputes expected output from inputs + policy
          ├── Creates scorer (ScoringFunction)    ← NEW
          │     └── WaterfallScorer / EscrowScorer / ReconciliationScorer
          ├── TheatreScoringProvider(criteria, scorer)  ← EXISTING
          ├── ReplayEngine.run(episodes)                ← EXISTING
          ├── EvidenceBundleBuilder                     ← EXISTING
          ├── TierAssigner                              ← EXISTING
          └── TheatreCalibrationCertificate             ← EXISTING
                │
                ▼
          output/certificates/{template_id}.json
          output/evidence_bundle_{template_id}/
```

### Key Insight: Oracle Adapter vs Scorer

The ReplayEngine has two extension points:
1. **OracleAdapter** — `invoke(input_data) → output_data` — the "construct under test"
2. **ScoringFunction** — `score(criteria_id, ground_truth, oracle_output) → float` — the "judge"

For deterministic theatres, the oracle adapter **recomputes the expected output** from inputs + policy (it IS the construct). The scorer then **compares** oracle output against expected output using binary checks.

This means:
- `DeterministicOracleAdapter`: takes fixture record, extracts inputs, returns them as-is (the fixture already contains the correct outputs in `expected_outputs`)
- `WaterfallScorer` / `EscrowScorer` / `ReconciliationScorer`: each implements 5 binary checks comparing `oracle_output` (the recomputed/passthrough data) against the expected assertions

**Simplification**: Since the fixture `expected_outputs` are the known-correct outputs and the fixture `inputs` contain all data needed for verification, the oracle adapter passes through the record's `inputs` and `expected_outputs` together. The scorer independently recomputes each check from `inputs` and verifies against `expected_outputs`.

---

## 3. Data Flow

### Fixture Record → GroundTruthEpisode Mapping

Each fixture record maps to a `GroundTruthEpisode`:

```python
GroundTruthEpisode(
    episode_id=record["record_id"],
    input_data=record["inputs"],
    expected_output=record["expected_outputs"],
    metadata={"asset_id": record["asset_id"], ...},
)
```

### Oracle Adapter: Passthrough

```python
class DeterministicOracleAdapter:
    """Passes fixture inputs through — the scorer does the real work."""
    async def invoke(self, input_data: dict) -> dict:
        return input_data  # inputs are what the scorer needs
```

The `ReplayEngine` calls `invoke(input_data)` where `input_data` = the episode's `input_data` dict. The scorer then receives both `ground_truth` (with `expected_output`) and `oracle_output` (the input data), giving it everything needed for binary checks.

### Scorer: Binary Check Pattern

Each scorer implements `ScoringFunction.score()`:

```python
async def score(self, criteria_id: str, ground_truth: dict, oracle_output: dict) -> float:
    inputs = oracle_output          # raw fixture inputs
    expected = ground_truth["expected_output"]

    if criteria_id == "waterfall_arithmetic":
        return self._check_waterfall_arithmetic(inputs, expected)
    # ... dispatch to per-criteria check methods

def _check_waterfall_arithmetic(self, inputs: dict, expected: dict) -> float:
    # Pure arithmetic: returns 1.0 or 0.0
    ...
```

---

## 4. Component Design

### 4.1 `theatre/scoring/__init__.py`

Package exports for three scorers + the oracle adapter.

### 4.2 `theatre/scoring/waterfall_scorer.py`

**Class**: `WaterfallScorer(ScoringFunction)`

| Method | Check | Logic |
|--------|-------|-------|
| `_check_waterfall_arithmetic` | Bucket amounts match | `sum(splits) == gross_amount` and each split matches expected |
| `_check_noi_pool_conservation` | NOI outflows == NOI | `abs(sum(noi_allocations) - noi_pool) <= tolerance` |
| `_check_rounding_policy_compliance` | Consistent rounding | Every amount equals `Decimal(str(amount)).quantize(Decimal('0.01'), ROUND_HALF_UP)` |
| `_check_cap_table_consistency` | Token math | `abs(per_token * supply - distributions) <= tolerance` |
| `_check_ledger_reconciliation` | Splits == gross | `abs(sum(split_amounts) - gross_amount) <= tolerance` |

**Rounding tolerance**: `Decimal('0.01')` (£0.01)

### 4.3 `theatre/scoring/escrow_scorer.py`

**Class**: `EscrowScorer(ScoringFunction)`

| Method | Check | Logic |
|--------|-------|-------|
| `_check_required_evidence_present` | All evidence present | `required_types ⊆ provided_types` |
| `_check_signature_policy_satisfied` | All signers present | `required_roles ⊆ attestation_roles` |
| `_check_validity_window_respected` | Timestamp valid | `evidence_timestamp` is parseable ISO-8601 (v0.1: always passes) |
| `_check_release_amount_correct` | Amount matches | `abs(release_pct * balance - expected_amount) <= tolerance` |
| `_check_idempotency` | No duplicates | Stateless per-episode: check that milestone_id appears exactly once in schedule |

**Idempotency note**: v0.1 fixtures have unique milestone IDs per record. The check verifies the milestone appears exactly once in the record's schedule.

### 4.4 `theatre/scoring/reconciliation_scorer.py`

**Class**: `ReconciliationScorer(ScoringFunction)`

| Method | Check | Logic |
|--------|-------|-------|
| `_check_bank_ref_match` | Bank ref exists | `payment.settlement_reference` found in bank statement transactions |
| `_check_bucket_sum_matches_gross` | Splits == gross | `abs(sum(split_amounts) - gross_amount) <= tolerance` |
| `_check_bucket_destination_valid` | Destinations allowed | Each split's `destination_ref` in `allowed_destinations` for its bucket |
| `_check_event_log_complete` | 1 event per split | `len(event_log) == len(splits)` and each split has a matching event |
| `_check_exceptions_correct` | Exceptions match | `expected.exceptions == computed_exceptions` (empty list for happy path) |

### 4.5 `theatre/scoring/deterministic_oracle.py`

**Class**: `DeterministicOracleAdapter(OracleAdapter)`

Simple passthrough — returns `input_data` as `output_data`. This gives the scorer access to the raw inputs for independent recomputation.

### 4.6 `scripts/run_two_rail_theatres.py`

CLI runner. Mirrors `scripts/run_observer_theatre.py` structure.

**Arguments**:
- `--all`: Run all three theatres (default)
- `--theatre <id>`: Run single theatre (`distribution_waterfall_v1`, `escrow_milestone_release_v1`, `ledger_reconciliation_v1`)
- `--output-dir`: Output directory (default: `output`)
- `--verbose`: Debug logging

**Theatre registry** (dict mapping `template_id` → config):

```python
THEATRES = {
    "distribution_waterfall_v1": {
        "template": "DISTRIBUTION_WATERFALL_V1.template.json",
        "dataset": "waterfall_fixtures_10.json",
        "scorer": WaterfallScorer,
    },
    "escrow_milestone_release_v1": {
        "template": "ESCROW_MILESTONE_RELEASE_V1.template.json",
        "dataset": "escrow_fixtures_10.json",
        "scorer": EscrowScorer,
    },
    "ledger_reconciliation_v1": {
        "template": "LEDGER_RECONCILIATION_V1.template.json",
        "dataset": "reconciliation_fixtures_10.json",
        "scorer": ReconciliationScorer,
    },
}
```

**Pipeline per theatre** (async):
1. Load template JSON, load dataset JSON
2. Validate template against `echelon_theatre_schema_v2.json`
3. Extract `TheatreCriteria` from template
4. Convert dataset records → `GroundTruthEpisode[]`
5. Compute dataset hash via `ReplayEngine._compute_dataset_hash()`
6. Populate template runtime fields (version_pins, dataset_hashes)
7. Create `CommitmentReceipt`
8. Build `ReplayEngine(oracle=DeterministicOracleAdapter(), scorer=TheatreScoringProvider(criteria, ScorerClass()))`
9. `await engine.run(episodes)`
10. Assign tier, build evidence bundle
11. Issue `TheatreCalibrationCertificate`
12. Validate against `echelon_certificate_schema.json`
13. Write to `output/certificates/{template_id}.json`

---

## 5. Technology Stack

| Layer | Technology | Justification |
|-------|-----------|---------------|
| Language | Python 3.14 | Matches existing codebase |
| Models | Pydantic v2 | Existing model layer |
| Decimal math | `decimal.Decimal` (stdlib) | Exact arithmetic for financial checks |
| JSON | stdlib `json` + `canonical_json()` | Deterministic hashing |
| Schema validation | `jsonschema` | Existing gate pattern |
| Testing | `pytest` + `pytest-asyncio` | Existing test framework |

**No new dependencies.** Everything uses stdlib + existing project packages.

---

## 6. Testing Strategy

### Unit Tests (per scorer)

Each scorer gets a test file with:

1. **Happy path**: all 5 checks pass on known-good fixture data
2. **Individual check failures**: synthetic records that fail exactly one check
3. **Rounding boundary**: amounts at tolerance boundary (e.g., £0.005 → rounds to £0.01)

| Test File | Covers |
|-----------|--------|
| `tests/theatre/test_waterfall_scorer.py` | 5 check methods + dispatch + edge cases |
| `tests/theatre/test_escrow_scorer.py` | 5 check methods + dispatch + edge cases |
| `tests/theatre/test_reconciliation_scorer.py` | 5 check methods + dispatch + edge cases |

### Integration Tests

`tests/theatre/test_two_rail_integration.py`:

1. **Full pipeline**: Run all 3 theatres → 3 certificates → all validate against schema
2. **Determinism**: Run twice → identical certificate hashes
3. **Score correctness**: All 30 records (10 per theatre) score 1.0 on all criteria (fixture data is happy path)
4. **Composite scores**: Each theatre's composite == 1.0 (all binary checks pass, weighted sum = 1.0)

---

## 7. File Plan

| File | Action | Lines (est.) |
|------|--------|-------------|
| `theatre/scoring/__init__.py` | Create | ~15 |
| `theatre/scoring/deterministic_oracle.py` | Create | ~20 |
| `theatre/scoring/waterfall_scorer.py` | Create | ~120 |
| `theatre/scoring/escrow_scorer.py` | Create | ~110 |
| `theatre/scoring/reconciliation_scorer.py` | Create | ~120 |
| `scripts/run_two_rail_theatres.py` | Create | ~250 |
| `tests/theatre/test_waterfall_scorer.py` | Create | ~150 |
| `tests/theatre/test_escrow_scorer.py` | Create | ~150 |
| `tests/theatre/test_reconciliation_scorer.py` | Create | ~150 |
| `tests/theatre/test_two_rail_integration.py` | Create | ~100 |

**Total**: ~1,185 lines across 10 new files. Zero modifications to existing files.

---

## 8. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Template `construct_under_test` is an object but schema may expect string | Extract `construct_id` string for certificate; pass object for template validation |
| All fixtures are happy path → scorers untested on failure cases | Unit tests include synthetic failing records |
| `dataset_hashes` in templates are pre-computed → may not match canonical hash | Runner recomputes and populates at runtime (same as Observer pattern) |
| Tier will always be UNVERIFIED (10 replays < 50 minimum) | Expected and correct — document in output |
