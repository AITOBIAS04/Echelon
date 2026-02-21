# Echelon Cycle-032: Observer End-to-End Integration

> **Goal**: Wire Cycle-027 (Community Oracle Verification Pipeline) to Cycle-031 (Theatre Template Engine) and produce a real calibration certificate for Observer against a live GitHub repository.
> **Scope**: Integration only — no new engine work. Both cycles shipped with tests passing.
> **Expected output**: One `CalibrationCertificate` JSON file with real scores for a real construct.

---

## What already exists

### Cycle-027: Community Oracle Verification Pipeline
- Ingests a GitHub repository via REST API
- Extracts N historical PRs as ground truth records (`GroundTruthRecord`)
- Passes each PR to an oracle construct via `OracleAdapter`
- Captures `OracleOutput` (summary, key_claims, follow_up_response)
- Scores precision, recall, reply accuracy per episode

### Cycle-031: Theatre Template Engine
- Theatre Template lifecycle (DRAFT → COMMITTED → ACTIVE → SETTLING → RESOLVED → ARCHIVED)
- `ReplayEngine` executes Product Theatres: commit → invoke → score → certify
- `OracleAdapter` interface with HTTP, local, and mock implementations
- `OracleInvocationRequest` / `OracleInvocationResponse` standardised envelope
- Structured `TheatreCriteria` with `criteria_ids`, `criteria_human`, `weights`
- `CommitmentReceipt` with canonical JSON (RFC 8785) commitment hash
- `CalibrationCertificate` issuance with evidence bundle
- `TierAssigner` with v0 verification tier rules
- `canonical_json()` utility

### Oracle adapter code (existing, from Cycle-027)
Located at: `verification/src/echelon_verify/oracle/`
- `base.py` — `OracleAdapter` ABC with `invoke()` + `from_config()` factory
- `http_adapter.py` — `HttpOracleAdapter` (HTTP POST via httpx)
- `python_adapter.py` — `PythonOracleAdapter` (dynamic import, local callable)

---

## What this cycle builds

### 1. Observer Theatre Template (JSON)
A concrete Product Theatre template for Observer verification:

```json
{
  "schema_version": "2.0.1",
  "theatre_id": "product_observer_v1",
  "template_family": "PRODUCT",
  "execution_path": "replay",
  "display_name": "Observer — Community Oracle Verification",
  "criteria": {
    "criteria_ids": ["precision", "recall", "reply_accuracy"],
    "criteria_human": "Measures whether the oracle's PR summary is faithful to the actual diff (precision), covers all significant changes (recall), and answers follow-up questions accurately (reply_accuracy).",
    "weights": {
      "precision": 0.4,
      "recall": 0.4,
      "reply_accuracy": 0.2
    }
  },
  "product_theatre_config": {
    "ground_truth_source": "GITHUB_API",
    "construct_under_test": "community_oracle_v1",
    "adapter_type": "local",
    "adapter_endpoint": "echelon_verify.oracle.python_adapter:PythonOracleAdapter",
    "replay_data_path": "ground_truth/observer_prs.jsonl",
    "replay_dataset_id": "observer_github_prs"
  }
}
```

### 2. Integration glue
Wire the Cycle-027 ground truth ingestion (`GroundTruthRecord` from GitHub API) into the Cycle-031 `ReplayEngine`'s `OracleInvocationRequest.input_data` format. This is the key integration point — mapping the PR-specific payload (title, description, diff_content, files_changed) into the generic `input_data: dict` that the engine expects.

### 3. Runner script / CLI command
A single entry point that:
1. Fetches N PRs from a target GitHub repo (using existing Cycle-027 ingestion)
2. Creates and commits the Observer Theatre Template
3. Runs the ReplayEngine across all episodes
4. Collects per-episode scores (precision, recall, reply_accuracy)
5. Issues a `CalibrationCertificate` with real aggregate scores
6. Assigns a verification tier
7. Writes the certificate to `output/certificates/product_observer_v1.json`

### 4. Evidence bundle
Generate the evidence bundle directory:
```
evidence_bundle_product_observer_v1/
├── manifest.json
├── template.json
├── commitment_receipt.json
├── ground_truth/
├── invocations/
├── scores/
├── certificate.json
└── audit_trail.jsonl
```

---

## Target repository for ground truth

Use `AITOBIAS04/Echelon` (this repo) as the target. It has real PRs and real diffs. Start with 10 PRs for the first run, scale to 50+ for BACKTESTED tier.

---

## Success criteria

1. Runner executes end-to-end without manual intervention
2. Each PR produces an `OracleInvocationResponse` with SUCCESS status
3. Per-episode scores computed and stored
4. `CalibrationCertificate` JSON written with all required fields per `echelon_certificate_schema.json`
5. Certificate validates against the schema
6. Evidence bundle directory created with all required files
7. Commitment hash is reproducible (same inputs → same hash)

---

## What this is NOT

- Not a new engine — Cycle-031 is the engine
- Not a new pipeline — Cycle-027 is the pipeline
- Not a schema change — schemas are v2.0.1
- Not production deployment — this is a local integration run
- Minimum viable: 10 PRs, local adapter, single construct
