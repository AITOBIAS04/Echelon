# SDD: Two-Rail Deterministic Theatres — Unified Pipeline (Cycle-007)

**Cycle:** 007
**Type:** Pipeline unification + arrears scorer
**Date:** 2026-03-01
**PRD Reference:** `grimoires/loa/prd.md`

---

## 1. Executive Summary

This cycle eliminates the divergence between Echelon's two certificate pipelines. Today, the OSINT path (`osint/osint_pipeline/`) and the replay path (`theatre/engine/`) produce structurally different certificates using different manifest formats, different hashing implementations, and different certificate models. A certificate from one path cannot be verified by the other path's tooling.

Cycle-007 resolves this by wiring the four existing Two-Rail replay templates through the same proven OSINT pipeline infrastructure: RFC 8785 canonical hashing via `osint/osint_pipeline/engine/canonical.py`, flat `{path: sha256}` manifests via `osint/osint_pipeline/engine/manifest_builder.py`, the unified `CalibrationCertificate` model via `osint/osint_pipeline/models/certificate.py`, and verification via `osint/osint_pipeline/echelon_verify.py`.

Additionally, the missing arrears scorer is implemented, completing the set of four Two-Rail scorers.

After this cycle, a single `echelon_verify.py verify certificate.json evidence/` command works on certificates from either execution path.

---

## 2. System Architecture

### 2.1 Current State (Two Divergent Pipelines)

```
OSINT Path                          Replay Path
-----------                         -----------
Live API collection                 Fixture dataset
        |                                  |
        v                                  v
EvidenceBundle (osint model)        GroundTruthEpisode
        |                                  |
        v                                  v
OracleOutput                        ReplayEngine + Scorer
        |                                  |
        v                                  v
CalibrationCertificate              TheatreCalibrationCertificate
(osint model)                       (theatre model)
        |                                  |
        v                                  v
manifest_builder.py                 EvidenceBundleBuilder
(flat {path: sha256})               (file_inventory dict)
        |                                  |
        v                                  v
echelon_verify.py PASS              No unified verifier
```

### 2.2 Target State (Unified Pipeline)

```
                   +---------------------------+
                   |    Evidence Source         |
                   |  (OSINT API or Fixture)   |
                   +-------------+-------------+
                                 |
                   +-------------v-------------+
                   |  Per-Criterion Scoring     |
                   | (Existing scorers or       |
                   |  new ArrearsScorer)        |
                   +-------------+-------------+
                                 |
              +------------------v------------------+
              |  Evidence Bundle Writer (FR-2)       |
              |  Writes to unified directory layout: |
              |  inputs/ scores/ policy/ expected/   |
              |  receipts/ gaps/                     |
              |  + theatre_template.json             |
              |  + oracle_output.json                |
              +------------------+------------------+
                                 |
              +------------------v------------------+
              |  manifest_builder.build_manifest()   |
              |  (osint/osint_pipeline/engine/)      |
              |  Flat {path: sha256} manifest        |
              |  RFC 8785 canonical JSON             |
              +------------------+------------------+
                                 |
              +------------------v------------------+
              |  CertificateGenerator.generate()     |
              |  (osint/osint_pipeline/engine/)      |
              |  CalibrationCertificate model        |
              |  execution_path="replay"             |
              +------------------+------------------+
                                 |
              +------------------v------------------+
              |  echelon_verify.py verify            |
              |  cert.json evidence/                 |
              |  PASS for both OSINT and replay      |
              +-------------------------------------+
```

### 2.3 Key Design Decision: Import, Don't Copy

The new runner script imports directly from `osint/osint_pipeline/`:

- `osint_pipeline.engine.manifest_builder.build_manifest` / `manifest_hash`
- `osint_pipeline.engine.canonical.canonical_json` / `canonical_hash`
- `osint_pipeline.engine.certificate_generator.CertificateGenerator`
- `osint_pipeline.models.certificate.CalibrationCertificate`
- `osint_pipeline.models.oracle_output.OracleOutput`, `CriterionScore`

The existing `theatre/engine/` and `theatre/scoring/` code is neither modified nor imported by the new runner (except for the scorer classes themselves, which are the domain logic). The existing runner (`scripts/run_two_rail_theatres.py`) and its `TheatreCalibrationCertificate` pipeline remain untouched (SC-10).

---

## 3. Component Design

### 3.1 Arrears Scorer -- `theatre/scoring/arrears_scorer.py`

#### Interface

Follows the identical async scorer interface established by the three existing scorers:

```python
class ArrearsScorer:
    async def score(
        self,
        criteria_id: str,
        ground_truth: dict[str, Any],
        oracle_output: dict[str, Any],
    ) -> float:
        """Return 1.0 (pass) or 0.0 (fail) for the given criterion."""
```

The `ground_truth` dict contains `input_data` (fixture inputs under the key `"inputs"` in the raw record) and `expected_output` (fixture expected outputs under the key `"expected_outputs"` in the raw record). The `oracle_output` dict is the passthrough from `DeterministicOracleAdapter` (identical to `input_data`). The scorer reads from `ground_truth` to compare inputs against expected outputs, matching the pattern in `waterfall_scorer.py` (lines 24-25), `escrow_scorer.py` (lines 24-25), and `reconciliation_scorer.py` (lines 24-25).

#### Criteria Dispatch

The scorer uses the same dispatch dict pattern as the existing scorers:

```python
checks = {
    "state_transition_validity": self._check_state_transition_validity,
    "ladder_redirection_arithmetic": self._check_ladder_redirection_arithmetic,
    "reserve_fund_impact": self._check_reserve_fund_impact,
    "distribution_adjustment": self._check_distribution_adjustment,
    "grace_period_enforcement": self._check_grace_period_enforcement,
    "ladder_balance_protection": self._check_ladder_balance_protection,
}
check_fn = checks.get(criteria_id)
if check_fn is None:
    return 0.0
return check_fn(inputs, expected)
```

Note: The criteria IDs used by the scorer (`state_transition_validity`, `ladder_redirection_arithmetic`, etc.) match the `criteria_ids` array in the template JSON and the keys in `expected_outputs.criteria_verdicts` in the fixture records.

#### Criteria Implementation

| Method | Criterion ID | Logic |
|--------|-------------|-------|
| `_check_state_transition_validity` | `state_transition_validity` | Reads `expected.state_transitions` list. For each transition, verifies the `(from, to)` pair exists in the `VALID_TRANSITIONS` set (derived from the template state machine). Returns 0.0 if any transition has no matching rule. Cross-checks against `expected.criteria_verdicts.state_transition_validity`. |
| `_check_ladder_redirection_arithmetic` | `ladder_redirection_arithmetic` | When `ladder_redirection_detail` is present: verifies `applied_to_arrears + remainder_to_equity == total_contribution` using Decimal arithmetic with TOLERANCE. When `ladder_action == "normal_equity_purchase"`: verifies `ladder_equity_purchased == inputs.lease_state.ladder_contribution`. When `ladder_action` is `"no_action_yet"` or `"frozen_pending_dispute"`: verifies `ladder_equity_purchased == 0`. Cross-checks `criteria_verdicts.ladder_redirection_arithmetic`. |
| `_check_reserve_fund_impact` | `reserve_fund_impact` | Reads `expected.reserve_fund_impact` object. For non-zero `drawdown_amount`: verifies `reserve_after_drawdown` is present (not null) and arithmetic is consistent. Checks `minimum_coverage_breached` is consistent with the policy. Cross-checks `criteria_verdicts.reserve_fund_impact`. |
| `_check_distribution_adjustment` | `distribution_adjustment` | Reads `expected.distribution_adjustment`. For `"none"` value, passes. For adjustments with `distribution_adjustment_detail`: verifies the reduction arithmetic using Decimal. Cross-checks `criteria_verdicts.distribution_adjustment`. |
| `_check_grace_period_enforcement` | `grace_period_enforcement` | Reads `inputs.arrears_policy.grace_period_days` and the transition timestamps. Verifies no escalation beyond GRACE_PERIOD occurs before the grace period expires. Cross-checks `criteria_verdicts.grace_period_enforcement`. |
| `_check_ladder_balance_protection` | `ladder_balance_protection` | Reads `inputs.lease_state.accrued_ladder_balance` and `expected.accrued_ladder_balance`. Verifies accrued balance is never reduced (only increased or unchanged). Checks `expected.ladder_balance_protected == true`. Cross-checks `criteria_verdicts.ladder_balance_protection`. |

#### Arithmetic Rules

All monetary comparisons use `decimal.Decimal` with `ROUND_HALF_UP` and a `TOLERANCE` of `Decimal("0.01")`, matching the pattern in `waterfall_scorer.py` (line 12), `escrow_scorer.py` (line 14), and `reconciliation_scorer.py` (line 10):

```python
from decimal import ROUND_HALF_UP, Decimal

TOLERANCE = Decimal("0.01")
```

All numeric values from fixture JSON are converted via `Decimal(str(value))` to avoid float imprecision. This matches `waterfall_scorer.py` lines 49-50: `gross = Decimal(str(payment.get("gross_amount", 0)))`.

#### Verdict-Driven Scoring

Each criterion check uses a two-phase approach:

1. **Structural validation**: Verify the fixture data is internally consistent (e.g., arithmetic sums within tolerance, transition pairs in allowed set).
2. **Verdict cross-check**: Read `expected_outputs.criteria_verdicts.<criterion_name>`. The structural validation result must agree with the verdict. If the verdict is `false`, the structural check should also have found an issue, and the method returns 0.0. If the verdict is `true`, the structural check should pass, and the method returns 1.0.

This design ensures the scorer produces the correct score for both valid records (records 0001-0010, all verdicts `true`) and targeted failure records (records 0011-0016, exactly one verdict `false` each). The structural validation serves as a sanity check that the fixture data itself is well-formed before trusting the verdict.

In practice, the simplest correct implementation reads `criteria_verdicts` and returns the boolean-to-float mapping, with structural checks as guardrails. However, the structural checks are essential for detecting fixture corruption and for future use when the scorer operates on live data rather than fixtures.

#### State Machine Transition Table

The scorer embeds the allowed transitions from the template's `arrears_policy.state_machine.transitions` as a compile-time constant:

```python
VALID_TRANSITIONS: frozenset[tuple[str, str]] = frozenset({
    ("CURRENT", "GRACE_PERIOD"),
    ("GRACE_PERIOD", "CURRENT"),
    ("GRACE_PERIOD", "LATE"),
    ("GRACE_PERIOD", "PARTIAL_RECEIVED"),
    ("LATE", "CURRENT"),
    ("LATE", "PARTIAL_RECEIVED"),
    ("LATE", "ARREARS"),
    ("PARTIAL_RECEIVED", "CURRENT"),
    ("PARTIAL_RECEIVED", "ARREARS"),
    ("ARREARS", "LADDER_REDIRECTED"),
    ("ARREARS", "DISPUTE_RAISED"),
    ("ARREARS", "PAYMENT_PLAN"),
    ("ARREARS", "RECOVERY"),
    ("ARREARS", "CURRENT"),
    ("LADDER_REDIRECTED", "ARREARS"),
    ("LADDER_REDIRECTED", "CURRENT"),
    ("DISPUTE_RAISED", "ARREARS"),
    ("DISPUTE_RAISED", "RESOLVED"),
    ("PAYMENT_PLAN", "CURRENT"),
    ("PAYMENT_PLAN", "RECOVERY"),
    ("RECOVERY", "EVICTION_PROCESS"),
    ("RECOVERY", "CURRENT"),
    ("EVICTION_PROCESS", "LEASE_TERMINATED"),
    ("EVICTION_PROCESS", "CURRENT"),
})
```

This is derived from the 24 transitions listed in `ARREARS_RESOLUTION_V1.template.json` lines 107-130. It is not loaded at runtime to avoid coupling the scorer to the template file path.

---

### 3.2 Unified Runner -- `scripts/run_two_rail_certificates.py`

#### Responsibility

New script that produces certificates using the `osint/osint_pipeline/` infrastructure for all four Two-Rail templates. The existing runner (`scripts/run_two_rail_theatres.py`) is not modified.

#### CLI Interface

```bash
python scripts/run_two_rail_certificates.py --template escrow_milestone_release_v1
python scripts/run_two_rail_certificates.py --template distribution_waterfall_v1
python scripts/run_two_rail_certificates.py --template ledger_reconciliation_v1
python scripts/run_two_rail_certificates.py --template arrears_resolution_v1
python scripts/run_two_rail_certificates.py --all
python scripts/run_two_rail_certificates.py --all --output-dir output/unified
python scripts/run_two_rail_certificates.py --all --verbose
```

#### Template Registry

```python
TEMPLATE_REGISTRY = {
    "escrow_milestone_release_v1": {
        "template_file": "ESCROW_MILESTONE_RELEASE_V1.template.json",
        "dataset_file": "escrow_fixtures_v02_11.json",
        "scorer_class": EscrowScorer,
    },
    "distribution_waterfall_v1": {
        "template_file": "DISTRIBUTION_WATERFALL_V1.template.json",
        "dataset_file": "waterfall_fixtures_v02_16.json",
        "scorer_class": WaterfallScorer,
    },
    "ledger_reconciliation_v1": {
        "template_file": "LEDGER_RECONCILIATION_V1.template.json",
        "dataset_file": "reconciliation_fixtures_v02_16.json",
        "scorer_class": ReconciliationScorer,
    },
    "arrears_resolution_v1": {
        "template_file": "ARREARS_RESOLUTION_V1.template.json",
        "dataset_file": "arrears_fixtures_v02_18.json",
        "scorer_class": ArrearsScorer,
    },
}
```

Note: The registry uses the v0.2 dataset filenames (the updated fixtures), not the v0.1 filenames referenced in the template JSON `dataset_hashes` keys.

#### Pipeline Steps

The runner executes these steps for each template:

**Step 1 -- Load template and dataset**

```python
template_path = FIXTURE_BASE / "templates" / config["template_file"]
dataset_path = FIXTURE_BASE / "datasets" / config["dataset_file"]
raw_template = json.loads(template_path.read_text())
dataset = json.loads(dataset_path.read_text())
records = dataset["records"]
```

**Step 2 -- Run scorer on each record**

For each record, run all criteria through the scorer. The scorer is async (matching the existing interface), so the runner uses `asyncio.run()` at the top level:

```python
scorer = config["scorer_class"]()
criteria_ids = raw_template["criteria"]["criteria_ids"]
weights = raw_template["criteria"]["weights"]

all_record_scores = []
for record in records:
    ground_truth = {
        "input_data": record["inputs"],
        "expected_output": record["expected_outputs"],
    }
    record_scores = {}
    for cid in criteria_ids:
        score = await scorer.score(cid, ground_truth, oracle_output={})
        record_scores[cid] = score
    all_record_scores.append({
        "record_id": record["record_id"],
        "scores": record_scores,
    })
```

**Step 3 -- Compute per-criterion aggregate scores and composite**

Per-criterion aggregate: mean across all records. Composite: weighted sum using template weights.

```python
per_criterion_agg = {}
for cid in criteria_ids:
    values = [rs["scores"][cid] for rs in all_record_scores]
    per_criterion_agg[cid] = sum(values) / len(values)

composite = sum(
    per_criterion_agg[cid] * weights[cid]
    for cid in criteria_ids
)
```

**Step 4 -- Build OracleOutput**

Construct an `OracleOutput` that adapts replay results into the OSINT pipeline's expected model. The `OracleOutput` requires an `OracleCollectionSummary` for its `collection` field:

```python
from osint_pipeline.models.oracle_output import CriterionScore, OracleOutput
from osint_pipeline.models.evidence import OracleCollectionSummary

criterion_scores = []
for cid in criteria_ids:
    agg = per_criterion_agg[cid]
    criterion_scores.append(CriterionScore(
        criterion_id=cid,
        score=agg,
        passed=agg >= 0.5,
        detail=f"{cid}: {agg:.4f} across {len(records)} records",
    ))

# Deterministic oracle_id and timestamp for manifest reproducibility
oracle_output = OracleOutput(
    oracle_id=f"replay_{template_key}",
    theatre_id=raw_template.get("theatre_id", "product_replay_engine_v1"),
    evaluated_at=DETERMINISTIC_EPOCH,  # fixed timestamp for reproducibility
    collection=OracleCollectionSummary(
        theatre_id=raw_template.get("theatre_id"),
        total_sources_attempted=len(records),
        total_sources_succeeded=len(records),
        total_sources_failed=0,
    ),
    criterion_scores=criterion_scores,
    composite_score=composite,
)
```

For replay, `corroboration_results` and `counter_signal_results` are empty lists (the defaults), which correctly produces `corroboration_met=False`, `counter_signals_checked=0`, `counter_signals_found=0` in the certificate.

**Step 5 -- Build evidence bundle directory (FR-2 layout)**

```python
evidence_dir = output_dir / f"evidence_{template_key}"
# Clean and recreate for determinism
if evidence_dir.exists():
    shutil.rmtree(evidence_dir)
evidence_dir.mkdir(parents=True)

for subdir in ("inputs", "receipts", "gaps", "scores", "policy", "expected"):
    (evidence_dir / subdir).mkdir()
```

Write files:

| File | Content | Deterministic |
|------|---------|---------------|
| `inputs/<record_id>.json` | `record["inputs"]` | Yes (sort_keys=True) |
| `expected/<record_id>.json` | `record["expected_outputs"]` | Yes (sort_keys=True) |
| `scores/per_record.json` | `all_record_scores` list | Yes (sort_keys=True) |
| `scores/aggregate.json` | `per_criterion_agg` + `composite` | Yes (sort_keys=True) |
| `policy/<policy_key>.json` | Template-specific policy section | Yes (sort_keys=True) |
| `theatre_template.json` | `raw_template` (original, unmutated) | Yes (sort_keys=True) |
| `oracle_output.json` | Deterministic OracleOutput (fixed timestamps) | Yes (sort_keys=True) |

The `receipts/` and `gaps/` directories are created but left empty for replay (no HTTP layer, no collection failures). Empty directories contribute no entries to the manifest.

Policy file mapping per template:

| Template | Policy Key | Policy Content |
|----------|-----------|----------------|
| arrears_resolution_v1 | `arrears_policy.json` | `raw_template["arrears_policy"]` |
| distribution_waterfall_v1 | `waterfall_policy.json` | Waterfall rules from template if present, else empty `{}` |
| escrow_milestone_release_v1 | `escrow_policy.json` | Escrow terms from template if present, else empty `{}` |
| ledger_reconciliation_v1 | `reconciliation_policy.json` | Reconciliation rules from template if present, else empty `{}` |

**Step 6 -- Build manifest and hash**

```python
from osint_pipeline.engine.manifest_builder import build_manifest, manifest_hash

manifest = build_manifest(evidence_dir)
mhash = manifest_hash(manifest)

# Write manifest.json (excluded from its own hash by MANIFEST_EXCLUDES)
manifest_path = evidence_dir / "manifest.json"
manifest_path.write_text(json.dumps(manifest, sort_keys=True, indent=2))
```

The `build_manifest()` function from `osint/osint_pipeline/engine/manifest_builder.py` walks the evidence directory, hashes every file (excluding `manifest.json` and `certificate.json` per `MANIFEST_EXCLUDES` on line 23), and returns a sorted `{posix_path: sha256_hex}` dict. The `manifest_hash()` function computes `canonical_hash(manifest)` -- the SHA-256 of the RFC 8785 canonical JSON of the manifest dict.

**Step 7 -- Compute commitment hash**

```python
from osint_pipeline.engine.canonical import canonical_hash

commitment = canonical_hash(raw_template)
```

The commitment hash is the SHA-256 of the RFC 8785 canonical JSON of the original, unmutated template. This binds the certificate to the specific template version. The verifier independently recomputes this hash from `theatre_template.json` in the evidence bundle.

**Step 8 -- Generate certificate**

```python
from osint_pipeline.engine.certificate_generator import CertificateGenerator

generator = CertificateGenerator()
certificate = generator.generate(
    oracle_output=oracle_output,
    manifest_hash=mhash,
    commitment_hash=commitment,
    target_entity={
        "template_id": raw_template.get("template_id", template_key),
        "construct_id": raw_template["product_theatre_config"]
            ["construct_under_test"]["construct_id"],
        "dataset_id": dataset.get("dataset_id", "unknown"),
        "record_count": len(records),
    },
    theatre_id=raw_template.get("template_id", template_key),
    inquiry_class="INSPECTION",
    execution_path="replay",
    pipeline_version="0.7.0",
)
```

The `CertificateGenerator.generate()` method (from `osint/osint_pipeline/engine/certificate_generator.py`) assembles a `CalibrationCertificate` from the `OracleOutput` and evidence hashes. It already accepts `execution_path` as a parameter (line 33, default `"replay"`), so no modification is needed.

**Step 9 -- Write certificate**

```python
cert_dict = json.loads(certificate.model_dump_json())
cert_path = evidence_dir / "certificate.json"
cert_path.write_text(json.dumps(cert_dict, sort_keys=True, indent=2, default=str))
```

The certificate is excluded from the manifest hash by `MANIFEST_EXCLUDES` in `manifest_builder.py` (line 24).

**Step 10 -- Verify**

```python
from osint_pipeline.echelon_verify import verify

success = verify(cert_path, evidence_dir)
```

The verifier runs 5 checks (lines 49-148 of `echelon_verify.py`): load certificate, check evidence dir exists, rebuild manifest and verify hash, check commitment hash against `theatre_template.json`, and verify all criteria passed.

If the verifier returns `True`, the template produces a PASS. The runner prints results and returns exit code 0 if all requested templates pass.

---

### 3.3 Evidence Bundle Builder Approach

Rather than building a formal adapter class, the runner script writes evidence files directly using `json.dumps()` and `Path.write_text()`. This is a deliberate design choice.

**Why no adapter class**: The OSINT path's `EvidenceBundle` Pydantic model (from `osint/osint_pipeline/models/evidence.py`) is designed for live API collection with HTTP receipts, source groups, independence tracking, and freshness states. The replay path has none of these concepts. An adapter that forced replay data into `EvidenceBundle` objects would produce semantically misleading instances (fake receipts, fake source groups).

Instead, the replay path produces the same **directory layout** (FR-2) and relies on the same **manifest builder** (`build_manifest()`) to hash the directory. The manifest builder is layout-agnostic -- it walks the directory, hashes every file, and produces the flat `{path: sha256}` mapping. It does not care whether the files came from HTTP receipts or fixture records.

The existing theatre `EvidenceBundleBuilder` class (from `theatre/engine/evidence_bundle.py`) is also not used by the new runner. It produces a different directory structure (`ground_truth/`, `invocations/`, `scores/aggregate.json`) and computes hashes using the theatre `canonical_json` (from `theatre/engine/canonical_json.py`) rather than the OSINT `canonical_json` (from `osint/osint_pipeline/engine/canonical.py`). Using it would perpetuate the pipeline divergence that this cycle aims to eliminate.

---

### 3.4 Certificate Generator Adapter

The existing `CertificateGenerator.generate()` already accepts all required parameters without modification. Key parameter mappings for replay:

| Parameter | Replay Value | OSINT Value |
|-----------|-------------|-------------|
| `execution_path` | `"replay"` | `"osint"` |
| `theatre_id` | Template ID (e.g., `"arrears_resolution_v1"`) | Theatre ID from config |
| `inquiry_class` | `"INSPECTION"` | Configured per theatre |
| `pipeline_version` | `"0.7.0"` | `"0.6.0"` (current OSINT) |
| `target_entity` | Template metadata dict | Company/entity dict |

The `OracleOutput.collection` field is an `OracleCollectionSummary` that, for replay, contains:

- `total_sources_attempted = len(records)` (fixture record count)
- `total_sources_succeeded = len(records)` (all records process successfully)
- `total_sources_failed = 0`
- `bundles = []` (no OSINT evidence bundles)
- `gaps = []` (no gap reports)
- `distinct_upstream_count = 0` (computed property, 0 because bundles is empty)

The certificate generator reads corroboration and counter-signal results from the `OracleOutput`. For replay, both lists are empty, producing:

- `corroboration_met = False` (from `any(cr.passed for cr in [])` = False)
- `counter_signals_checked = 0`
- `counter_signals_found = 0`

These are semantically correct for a replay certificate -- corroboration and counter-signals are OSINT-only concepts.

---

## 4. Data Architecture

### 4.1 Evidence Bundle Directory Layout

```
evidence_<template_key>/
    inputs/
        arrears_0001.json
        arrears_0002.json
        ...
    expected/
        arrears_0001.json
        arrears_0002.json
        ...
    scores/
        per_record.json
        aggregate.json
    policy/
        arrears_policy.json
    receipts/             (empty for replay)
    gaps/                 (empty for replay)
    theatre_template.json
    oracle_output.json
    manifest.json
    certificate.json
```

### 4.2 Manifest Format

Flat `{relative_path: sha256_hex}` dict, lexicographically sorted by key. The hash is computed as `SHA-256(canonical_json(manifest))` where `canonical_json` is the RFC 8785 implementation from `osint/osint_pipeline/engine/canonical.py`.

Example manifest structure:

```json
{
  "expected/arrears_0001.json": "a1b2c3...",
  "expected/arrears_0002.json": "d4e5f6...",
  "inputs/arrears_0001.json": "789abc...",
  "inputs/arrears_0002.json": "def012...",
  "oracle_output.json": "345678...",
  "policy/arrears_policy.json": "9abcde...",
  "scores/aggregate.json": "f01234...",
  "scores/per_record.json": "567890...",
  "theatre_template.json": "abcdef..."
}
```

Key properties:
- `manifest.json` and `certificate.json` are excluded (per `MANIFEST_EXCLUDES` in `manifest_builder.py`, line 23)
- Empty directories (`receipts/`, `gaps/`) contribute no entries (only files are hashed, `manifest_builder.py` line 41: `if not file_path.is_file(): continue`)
- POSIX forward-slash path separators (per `manifest_builder.py` line 45: `relative.as_posix()`)

### 4.3 Certificate Schema

The `CalibrationCertificate` model (from `osint/osint_pipeline/models/certificate.py`) with replay-specific values:

```json
{
  "certificate_id": "<uuid-v4>",
  "certificate_version": "1.0.0",
  "theatre_id": "arrears_resolution_v1",
  "inquiry_class": "INSPECTION",
  "execution_path": "replay",
  "verification_tier": "UNVERIFIED",
  "composite_score": 0.9375,
  "all_criteria_passed": true,
  "criterion_scores": [
    {
      "criterion_id": "state_transition_validity",
      "score": 0.9375,
      "passed": true,
      "detail": "state_transition_validity: 0.9375 across 16 records",
      "evidence_bundle_ids": []
    }
  ],
  "evidence_bundle_hash": "<sha256-of-manifest-canonical-json>",
  "commitment_hash": "<sha256-of-template-canonical-json>",
  "sources_queried": 16,
  "sources_succeeded": 16,
  "sources_failed": 0,
  "distinct_upstream_count": 0,
  "corroboration_met": false,
  "counter_signals_checked": 0,
  "counter_signals_found": 0,
  "issued_at": "<iso-datetime>",
  "oracle_id": "replay_arrears_resolution_v1",
  "target_entity": {
    "template_id": "arrears_resolution_v1",
    "construct_id": "two_rail_marketplace_core",
    "dataset_id": "arrears_v0_2_18",
    "record_count": 16
  },
  "pipeline_version": "0.7.0"
}
```

### 4.4 Composite Score Computation

Per-criterion aggregate = `(number of records where score == 1.0) / (total records)`. Since each score is binary (1.0 or 0.0), this is equivalent to the pass rate. Composite = weighted sum of per-criterion aggregates using template weights.

Example for arrears_resolution_v1 (16 records, 10 all-pass + 6 targeted single-criterion failures):

| Criterion | Pass Count | Aggregate | Weight |
|-----------|-----------|-----------|--------|
| `state_transition_validity` | 15/16 | 0.9375 | 0.25 |
| `ladder_redirection_arithmetic` | 15/16 | 0.9375 | 0.25 |
| `reserve_fund_impact` | 15/16 | 0.9375 | 0.15 |
| `distribution_adjustment` | 15/16 | 0.9375 | 0.15 |
| `grace_period_enforcement` | 15/16 | 0.9375 | 0.10 |
| `ladder_balance_protection` | 15/16 | 0.9375 | 0.10 |

Composite = 0.9375 * (0.25 + 0.25 + 0.15 + 0.15 + 0.10 + 0.10) = 0.9375 * 1.00 = **0.9375**

The `all_criteria_passed` field is `true` when every `CriterionScore.passed` is `true`. The `passed` threshold is `score >= 0.5`, which holds for all criteria across all four templates (the lowest aggregate is well above 0.5 since at most 1 out of N records fails per criterion).

---

## 5. Integration Points

### 5.1 Shared from `osint/osint_pipeline/`

| Module | Function / Class | Used By Runner For |
|--------|------------------|-------------------|
| `engine/canonical.py` | `canonical_json()`, `canonical_hash()`, `sha256_hex()` | Commitment hash (template canonical JSON), manifest hash |
| `engine/manifest_builder.py` | `build_manifest()`, `manifest_hash()` | Evidence directory file inventory and SHA-256 hash |
| `engine/certificate_generator.py` | `CertificateGenerator.generate()` | Assembling `CalibrationCertificate` from `OracleOutput` |
| `models/certificate.py` | `CalibrationCertificate` | Certificate model (shared across both execution paths) |
| `models/oracle_output.py` | `OracleOutput`, `CriterionScore` | Adapting replay scorer results to pipeline model |
| `models/evidence.py` | `OracleCollectionSummary` | Collection metadata stub for replay path |
| `echelon_verify.py` | `verify()` | Post-generation Verifier CLI pass/fail check |

### 5.2 Shared from `theatre/scoring/`

| Module | Class | Used By Runner For |
|--------|-------|-------------------|
| `waterfall_scorer.py` | `WaterfallScorer` | Scoring waterfall template fixtures |
| `escrow_scorer.py` | `EscrowScorer` | Scoring escrow template fixtures |
| `reconciliation_scorer.py` | `ReconciliationScorer` | Scoring reconciliation template fixtures |
| `arrears_scorer.py` (NEW) | `ArrearsScorer` | Scoring arrears template fixtures |

### 5.3 Not Modified (SC-10 Compliance)

| Module | Why Untouched |
|--------|---------------|
| `theatre/engine/certificate.py` | `TheatreCalibrationCertificate` remains for existing runner |
| `theatre/engine/evidence_bundle.py` | `EvidenceBundleBuilder` remains for existing runner |
| `theatre/engine/canonical_json.py` | Theatre-specific canonical JSON remains for existing runner |
| `theatre/scoring/waterfall_scorer.py` | No changes needed |
| `theatre/scoring/escrow_scorer.py` | No changes needed |
| `theatre/scoring/reconciliation_scorer.py` | No changes needed |
| `scripts/run_two_rail_theatres.py` | Existing runner preserved as-is |
| `osint/osint_pipeline/echelon_verify.py` | Already path-agnostic (checks hashes and schema only) |
| `osint/osint_pipeline/engine/manifest_builder.py` | Already supports the required interface |
| `osint/osint_pipeline/engine/canonical.py` | Already supports RFC 8785 |
| `osint/osint_pipeline/engine/certificate_generator.py` | Already supports `execution_path="replay"` |
| `osint/osint_pipeline/models/certificate.py` | Already supports replay-compatible fields |

### 5.4 Import Path Setup

The runner adds the project root and `osint/` directory to `sys.path`, matching the pattern already used by `echelon_verify.py` (lines 30-32):

```python
_ROOT = Path(__file__).resolve().parents[1]
_OSINT = _ROOT / "osint"
for p in (str(_ROOT), str(_OSINT)):
    if p not in sys.path:
        sys.path.insert(0, p)
```

This allows both `from osint_pipeline.engine.manifest_builder import build_manifest` and `from theatre.scoring.arrears_scorer import ArrearsScorer` to resolve correctly.

---

## 6. Testing Strategy

### 6.1 Unit Tests -- `tests/test_arrears_scorer.py`

Tests `ArrearsScorer` against all 16 fixture records.

| Test | What It Validates |
|------|-------------------|
| `test_all_valid_records_pass_all_criteria` | Records arrears_0001 through arrears_0010: all 6 criteria return 1.0 |
| `test_state_transition_failure` | Record arrears_0011: `state_transition_validity` returns 0.0, other 5 return 1.0 |
| `test_ladder_redirection_failure` | Record arrears_0012: `ladder_redirection_arithmetic` returns 0.0, other 5 return 1.0 |
| `test_reserve_fund_failure` | Record arrears_0013: `reserve_fund_impact` returns 0.0, other 5 return 1.0 |
| `test_distribution_adjustment_failure` | Record arrears_0014: `distribution_adjustment` returns 0.0, other 5 return 1.0 |
| `test_grace_period_failure` | Record arrears_0015: `grace_period_enforcement` returns 0.0, other 5 return 1.0 |
| `test_ladder_balance_protection_failure` | Record arrears_0016: `ladder_balance_protection` returns 0.0, other 5 return 1.0 |
| `test_unknown_criterion_returns_zero` | Unknown criterion ID returns 0.0 |
| `test_decimal_arithmetic_precision` | Verify Decimal usage: no float imprecision in ladder redirection sums |

### 6.2 Integration Test -- `tests/test_unified_pipeline.py`

Full pipeline for one template (escrow as canonical reference).

| Test | What It Validates |
|------|-------------------|
| `test_escrow_pipeline_produces_pass` | Run full pipeline for escrow, verify `echelon_verify.verify()` returns True |
| `test_evidence_bundle_directory_layout` | FR-2 subdirectories exist: `inputs/`, `scores/`, `receipts/`, `gaps/`, `policy/`, `expected/` |
| `test_manifest_contains_all_files` | Manifest has entries for every non-excluded file in evidence directory |
| `test_certificate_has_replay_fields` | `execution_path == "replay"`, `verification_tier == "UNVERIFIED"` |
| `test_certificate_model_matches_osint` | Certificate dict validates against `CalibrationCertificate(**data)` |

### 6.3 Determinism Test -- `tests/test_determinism.py`

Verifies re-run produces identical evidence bundle hash.

| Test | What It Validates |
|------|-------------------|
| `test_deterministic_manifest_hash` | Run pipeline for escrow twice (to two different temp dirs), assert `manifest_hash` is identical |
| `test_deterministic_commitment_hash` | Commitment hash is identical across runs |
| `test_deterministic_file_contents` | Every file in the evidence bundle has identical SHA-256 across runs |

### 6.4 Cross-Path Schema Test -- `tests/test_cross_path_schema.py`

Verifies replay certificate has the same Pydantic model as an OSINT certificate.

| Test | What It Validates |
|------|-------------------|
| `test_replay_certificate_validates_as_calibration_certificate` | Load replay certificate JSON, validate with `CalibrationCertificate(**data)` |
| `test_certificate_required_fields_present` | All required `CalibrationCertificate` fields exist in replay output |

### 6.5 All-Templates Test -- `tests/test_all_templates.py`

Verifies all four templates produce Verifier CLI PASS.

| Test | What It Validates |
|------|-------------------|
| `test_all_four_templates_pass_verifier` | Run pipeline for each of the 4 templates, verify `echelon_verify.verify()` returns True |
| `test_composite_scores_in_expected_range` | Assert composite scores are within 0.01 of expected values |

### 6.6 Existing Tests Remain Green

SC-08 requires that all existing tests (70+ osint + theatre tests) continue to pass. Since SC-10 prohibits modifications to existing files (only additive changes to `theatre/scoring/__init__.py`), no existing test should break.

---

## 7. File Inventory

### 7.1 New Files

| File | Description |
|------|-------------|
| `theatre/scoring/arrears_scorer.py` | Arrears Resolution scorer: 6 criteria, Decimal arithmetic, async `score()` interface matching existing scorers |
| `scripts/run_two_rail_certificates.py` | Unified pipeline runner: loads template + dataset, scores via existing scorers, builds FR-2 evidence bundle, generates `CalibrationCertificate` via OSINT infrastructure, runs Verifier CLI |
| `tests/test_arrears_scorer.py` | Unit tests for `ArrearsScorer`: all 16 records, all 6 criteria, failure targeting, Decimal precision |
| `tests/test_unified_pipeline.py` | Integration test: full pipeline for escrow template, FR-2 layout validation, certificate model check |
| `tests/test_determinism.py` | Determinism test: dual-run identical hash assertion for manifest, commitment, and file contents |
| `tests/test_cross_path_schema.py` | Cross-path schema test: replay certificate validates as `CalibrationCertificate` Pydantic model |
| `tests/test_all_templates.py` | All-templates test: 4 templates produce Verifier CLI PASS, composite scores in expected range |

### 7.2 Modified Files

| File | Modification |
|------|-------------|
| `theatre/scoring/__init__.py` | Add `ArrearsScorer` to imports and `__all__` list (additive only, 2 lines changed) |

### 7.3 Files NOT Modified (SC-10)

| File | Reason |
|------|--------|
| `theatre/engine/certificate.py` | SC-10: no modifications to existing theatre/engine/ files |
| `theatre/engine/evidence_bundle.py` | SC-10 |
| `theatre/engine/canonical_json.py` | SC-10 |
| `theatre/scoring/waterfall_scorer.py` | SC-10: no modifications to existing theatre/scoring/ files |
| `theatre/scoring/escrow_scorer.py` | SC-10 |
| `theatre/scoring/reconciliation_scorer.py` | SC-10 |
| `scripts/run_two_rail_theatres.py` | SC-10 (existing runner preserved) |
| All `osint/osint_pipeline/` files | Already support the required interfaces |

---

## 8. Constraints

### C-1: SC-10 -- No Modifications to Existing Files

No changes to any file in `theatre/engine/` or `theatre/scoring/` (except adding `ArrearsScorer` to `theatre/scoring/__init__.py`, which is an additive-only change -- inserting one import and one name into `__all__`). No changes to `scripts/run_two_rail_theatres.py`. No changes to any `osint/osint_pipeline/` file.

**Rationale**: The existing pipeline and its 70+ tests must continue to work identically. The unified pipeline is strictly additive infrastructure.

### C-2: Decimal Arithmetic

All monetary comparisons in `ArrearsScorer` must use `decimal.Decimal`:
- Rounding: `ROUND_HALF_UP`
- Tolerance: `TOLERANCE = Decimal("0.01")` (+/- one penny)
- Conversion: All numeric values from JSON converted via `Decimal(str(value))` to avoid float imprecision

This matches the established pattern across the three existing scorers.

### C-3: Determinism

Every run of the pipeline with identical inputs must produce identical outputs:
- Identical file contents in every evidence bundle file
- Identical manifest hash
- Identical commitment hash

Requirements:
- All `json.dumps()` calls use `sort_keys=True`
- No timestamps in evidence files (except `oracle_output.json`, which uses a fixed deterministic epoch, and `certificate.json`, which is excluded from the manifest)
- No random values in evidence files (UUIDs only in the certificate, which is excluded from the manifest)
- The `oracle_id` in `oracle_output.json` is derived from the template key (deterministic), not from a UUID

**Key determinism invariant**: `oracle_output.json` IS included in the manifest hash (it is not in `MANIFEST_EXCLUDES`). Therefore it must contain only deterministic content. The `evaluated_at` timestamp is set to a fixed epoch value. The `oracle_id` is `"replay_<template_key>"` with no run-specific suffix.

### C-4: Verifier Compatibility

The Verifier CLI (`echelon_verify.py`) performs 5 checks (lines 49-148):
1. Certificate loads as `CalibrationCertificate` (Pydantic validation)
2. Evidence directory exists and is non-empty
3. Manifest hash matches (rebuild manifest from evidence dir, compare)
4. Commitment hash matches (canonical_hash of `theatre_template.json`, compare)
5. All criteria passed (`all_criteria_passed == True`)

Checks 3 and 4 are the critical integration points. They depend on the replay pipeline using the exact same `build_manifest()` and `canonical_hash()` functions that the verifier imports. Since the runner imports from the same modules, hash agreement is guaranteed by construction.

### C-5: Async Interface Compliance

The `ArrearsScorer.score()` method must be `async def` matching the signature of existing scorers (`WaterfallScorer.score()` on line 18, `EscrowScorer.score()` on line 19, `ReconciliationScorer.score()` on line 19). Although the new unified runner calls scorers with `await` in an `asyncio.run()` context, the async interface is also required for compatibility with the existing `ReplayEngine` and `TheatreScoringProvider` should the arrears scorer ever be used with the old runner.

### C-6: Template Integrity

The `theatre_template.json` written to the evidence bundle must be the **original, unmutated** template JSON (as loaded from disk). The commitment hash is computed from this original template via `canonical_hash(raw_template)`. The verifier independently recomputes the hash from the template file in the evidence bundle.

The normalization logic in the existing runner (`_normalize_template_for_schema` in `scripts/run_two_rail_theatres.py`, lines 74-140) must NOT be applied to the template written to the evidence bundle. Schema normalization is only relevant for the theatre engine's internal validation, not for the certificate commitment chain.
