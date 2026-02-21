# PRD: Observer End-to-End Integration (Cycle-032)

> **Version**: 1.0
> **Date**: 2026-02-20
> **Cycle**: cycle-032
> **Depends on**: Cycle-027 (Community Oracle Verification Pipeline), Cycle-031 (Theatre Template Engine)

---

## 1. Problem Statement

The Echelon platform has two independently built and tested systems:

1. **Cycle-027**: Community Oracle Verification Pipeline — ingests GitHub PRs, invokes oracle constructs, scores precision/recall/reply_accuracy via LLM judges
2. **Cycle-031**: Theatre Template Engine — provides a structured lifecycle (commit → replay → certify) with cryptographic commitment, evidence bundles, and verification tiers

These systems use **different data models and adapter interfaces**. Neither can produce a real `CalibrationCertificate` (validated against `echelon_certificate_schema.json`) end-to-end. The verification pipeline generates its own certificate format, while the Theatre engine runs with mock adapters and stub scores.

**This cycle bridges the gap** — wiring real GitHub PR ground truth from Cycle-027 into the Theatre engine's ReplayEngine from Cycle-031 to produce a real, schema-validated calibration certificate for Observer.

> Sources: `loa-grimoire/context/echelon_cycle_032.md`

---

## 2. Goals & Success Criteria

### Primary Goal

Produce one real `CalibrationCertificate` JSON file for `community_oracle_v1` against the `AITOBIAS04/Echelon` repository, with real scores from real PRs.

### Success Criteria

| # | Criterion | Measurable |
|---|-----------|------------|
| 1 | Runner executes end-to-end without manual intervention | Single command produces certificate |
| 2 | Each PR produces an `OracleInvocationResponse` with SUCCESS status | ≥80% success rate across 10 PRs |
| 3 | Per-episode scores (precision, recall, reply_accuracy) computed and stored | All 3 criteria present per episode |
| 4 | Certificate JSON validates against `echelon_certificate_schema.json` | jsonschema validates with 0 errors |
| 5 | Evidence bundle directory created with all required files | `validate_minimum_files()` returns empty list |
| 6 | Commitment hash is reproducible | Same inputs → identical hash across runs |
| 7 | Certificate written to `output/certificates/product_observer_v1.json` | File exists with all required fields |

### Non-Goals

- No new engine work — Cycle-031 is the engine
- No new pipeline work — Cycle-027 is the pipeline
- No schema changes — schemas are v2.0.1 (theatre) and v1.0.0 (certificate)
- No production deployment — local integration run only
- No HTTP adapter — local Python adapter only (PythonOracleAdapter)
- No scale target beyond 10 PRs for initial run

---

## 3. Integration Architecture

### Data Flow

```
GitHub API (AITOBIAS04/Echelon)
    ↓ Cycle-027 GitHubIngester
GroundTruthRecord[]
    ↓ Adapter Bridge (NEW)
GroundTruthEpisode[]
    ↓ Cycle-031 ReplayEngine
    ├─ OracleInvocationRequest → Adapter Bridge → Cycle-027 OracleAdapter → LLM
    ├─ OracleInvocationResponse ← Adapter Bridge ← OracleOutput
    └─ ScoringBridge → Cycle-027 AnthropicScorer
         ↓
    ReplayResult (real scores)
         ↓
    CalibrationCertificate (validated against schema)
         ↓
    EvidenceBundle (full audit trail)
```

### Three Integration Seams

#### Seam 1: Ground Truth Mapping
- **From**: Cycle-027 `GroundTruthRecord` (PR-specific: title, description, diff_content, files_changed, url, author, labels)
- **To**: Cycle-031 `GroundTruthEpisode` (generic: episode_id, input_data, expected_output, labels, metadata)
- **Mapping**: Pack PR fields into `input_data` dict; use PR number as `episode_id`

#### Seam 2: Oracle Adapter Bridge
- **From**: Cycle-031 `OracleAdapter` protocol (`invoke(input_data: dict) -> dict`)
- **To**: Cycle-027 `OracleAdapter` ABC (`invoke(ground_truth: GroundTruthRecord, follow_up_question: str) -> OracleOutput`)
- **Bridge**: Unpack `input_data` → reconstruct `GroundTruthRecord` → invoke Cycle-027 adapter → pack `OracleOutput` into response dict

#### Seam 3: Scoring Bridge
- **From**: Cycle-031 `ScoringFunction` protocol (`score(criteria, input_data, output_data, expected_output) -> dict[str, float]`)
- **To**: Cycle-027 `ScoringProvider` (`score_precision()`, `score_recall()`, `score_reply_accuracy()`)
- **Bridge**: Map Theatre scoring protocol to verification pipeline's per-dimension scoring

---

## 4. Functional Requirements

### FR-1: Observer Theatre Template

A concrete Product Theatre template JSON for Observer verification with:
- `theatre_id`: `product_observer_v1`
- `criteria_ids`: `["precision", "recall", "reply_accuracy"]`
- `weights`: `{precision: 0.4, recall: 0.4, reply_accuracy: 0.2}`
- `adapter_type`: `local`
- `ground_truth_source`: `GITHUB_API`
- Must pass `TemplateValidator` (schema + 8 runtime rules)

### FR-2: Ground Truth Adapter

Function/class that converts `GroundTruthRecord[]` from Cycle-027 into `GroundTruthEpisode[]` for Cycle-031:
- `episode_id` = PR number (string)
- `input_data` = `{title, description, diff_content, files_changed, follow_up_question}`
- `expected_output` = None (no ground truth labels for open-ended scoring)
- `labels` = `{author, url, repo, github_labels}`
- `metadata` = `{timestamp, ingested_at}`

### FR-3: Oracle Adapter Bridge

An adapter implementing Cycle-031's `OracleAdapter` protocol that internally delegates to Cycle-027's pipeline:
- Accepts `input_data: dict` from ReplayEngine
- Reconstructs `GroundTruthRecord` from input_data
- Calls Cycle-027's oracle construct (via `PythonOracleAdapter` or `HttpOracleAdapter`)
- Returns `output_data: dict` containing `{summary, key_claims, follow_up_response}`

### FR-4: Scoring Bridge

A `ScoringFunction` implementation that delegates to Cycle-027's `AnthropicScorer`:
- Maps Theatre's `score(criteria, input_data, output_data, expected_output)` to verification pipeline's `score_precision()`, `score_recall()`, `score_reply_accuracy()`
- Returns `dict[str, float]` with keys matching `criteria_ids`

### FR-5: Runner Script

A single entry point (`scripts/run_observer_theatre.py` or CLI command) that:
1. Fetches N PRs from GitHub via Cycle-027's `GitHubIngester`
2. Generates follow-up questions via Cycle-027's `AnthropicScorer.generate_follow_up_question()`
3. Converts records to `GroundTruthEpisode[]`
4. Computes dataset hash and creates `CommitmentReceipt`
5. Runs `ReplayEngine` with oracle + scoring bridges
6. Assigns verification tier via `TierAssigner`
7. Issues `TheatreCalibrationCertificate`
8. Validates certificate against `echelon_certificate_schema.json`
9. Generates evidence bundle via `EvidenceBundleBuilder`
10. Writes certificate to `output/certificates/product_observer_v1.json`

### FR-6: Evidence Bundle

Generate the full evidence bundle with:
- `manifest.json` — bundle metadata
- `template.json` — Observer template snapshot
- `commitment_receipt.json` — cryptographic commitment
- `ground_truth/observer_prs.jsonl` — ingested PR records
- `invocations/{episode_id}.json` — per-PR oracle invocation request/response
- `scores/per_episode.jsonl` — per-PR scores
- `scores/aggregate.json` — mean scores
- `certificate.json` — issued certificate

### FR-7: Certificate Schema Validation

The output certificate must validate against `docs/schemas/echelon_certificate_schema.json`:
- All required fields present
- `theatre_id` matches pattern `^[a-z_]+_v\d+$`
- All hashes are 64-char hex strings
- `verification_tier` in `[UNVERIFIED, BACKTESTED, PROVEN]`
- Timestamps in ISO 8601 format

---

## 5. Technical Constraints

| Constraint | Detail |
|------------|--------|
| Python version | 3.12+ (matches both cycles) |
| No new engine code | Use Cycle-031 Theatre engine as-is |
| No new pipeline code | Use Cycle-027 verification pipeline as-is |
| Local adapter only | Use `PythonOracleAdapter` (no HTTP deployment) |
| Minimum PRs | 10 for initial run |
| ANTHROPIC_API_KEY required | Scoring uses Claude via Anthropic SDK |
| GITHUB_TOKEN recommended | For rate-limited GitHub API access |
| Certificate schema | `docs/schemas/echelon_certificate_schema.json` v1.0.0 |
| Theatre schema | `docs/schemas/echelon_theatre_schema_v2.json` v2.0.1 |

---

## 6. Scope & Prioritisation

### MVP (This Cycle)

- Ground truth adapter (GroundTruthRecord → GroundTruthEpisode)
- Oracle adapter bridge (Theatre protocol → Verification pipeline)
- Scoring bridge (Theatre ScoringFunction → AnthropicScorer)
- Observer Theatre template (real, validated)
- Runner script (end-to-end)
- Evidence bundle generation
- Certificate schema validation
- Tests for all integration glue

### Out of Scope

- HTTP adapter deployment
- Frontend integration
- Database persistence (local files only)
- Scale beyond 10 PRs
- Market Theatre support
- Multi-construct chains
- CI/CD pipeline
- Production deployment

---

## 7. Risks & Dependencies

| Risk | Severity | Mitigation |
|------|----------|------------|
| GitHub API rate limiting | MEDIUM | Use GITHUB_TOKEN; cache ground truth |
| Anthropic API cost for 10 PRs × 3 scoring calls | LOW | ~30 API calls, well within free tier |
| Diff truncation affecting scoring | LOW | Cycle-027 already handles 100KB cap |
| Oracle invocation timeouts | MEDIUM | Use existing retry logic (3 attempts, 30s timeout) |
| Cycle-027/031 interface drift | LOW | Both cycles tested and archived; interfaces frozen |
