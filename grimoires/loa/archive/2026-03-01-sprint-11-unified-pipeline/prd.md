# PRD: Two-Rail Deterministic Theatres — Unified Pipeline (Cycle-007)

**Cycle:** 007
**Type:** Pipeline unification + arrears scorer
**Date:** 2026-03-01
**Predecessor:** Cycle-006 (First Live OSINT-Settled Certificate)

---

## 1. Problem Statement

Echelon has two separate certificate pipelines that produce structurally different outputs:

1. **OSINT path** (`osint/osint_pipeline/`): Live API collection → evidence bundles → `CalibrationCertificate` → Verifier CLI PASS. Built in cycles 002–006.
2. **Replay path** (`theatre/engine/`): Deterministic fixtures → scorer → `TheatreCalibrationCertificate`. Built in cycle-031 (pre-Loa).

These pipelines share the same conceptual purpose (produce verifiable certificates from evidence) but use different models, different manifest formats, and different hashing approaches. A certificate from the replay path cannot be verified by the Verifier CLI from the OSINT path, and vice versa.

Additionally, the ARREARS_RESOLUTION_V1 template has 18 fixtures and 6 criteria but no scorer implementation — it is the only Two-Rail template without a working scorer.

> Source: `grimoires/loa/context/echelon_cycle_007_context.md`

---

## 2. Objective

Wire the four existing Two-Rail templates through the same proven pipeline infrastructure that Cycle-006 validates against live OSINT data. After this cycle:

- Both execution paths (`replay` and `osint`) produce certificates using identical infrastructure: RFC 8785 canonical hashing, flat `{path: sha256}` manifests, the same certificate schema, the same Verifier CLI.
- All four Two-Rail templates produce Verifier CLI PASS.
- Evidence bundle hashes are deterministic (re-run produces identical hash).

---

## 3. Users & Stakeholders

- **Sponsor** (future): Commissions either an OSINT-settled or replay-settled Theatre — both produce the same independently verifiable certificate.
- **Verifier**: Runs `echelon_verify.py verify certificate.json evidence/` on any certificate, regardless of execution path.
- **Developer**: Uses a single certificate model and manifest format across all paths.

---

## 4. Functional Requirements

### FR-1: Arrears Scorer

Build `theatre/scoring/arrears_scorer.py` implementing 6 criteria from the ARREARS_RESOLUTION_V1 template:

| Criterion | What It Checks |
|-----------|----------------|
| `state_transition_valid` | Every transition follows the 12-state state machine. No illegal state jumps. |
| `ladder_redirect_arithmetic` | Ladder contribution correctly redirected from equity accrual to arrears reduction. |
| `reserve_fund_impact` | Reserve fund draws/contributions calculated correctly per policy. |
| `distribution_adjustment` | Investor distributions adjusted correctly when arrears affect NOI pool. |
| `grace_period_enforcement` | Grace period timing enforced (5 calendar days default). No premature escalation. |
| `ladder_balance_protection` | Previously accrued ladder equity never touched by arrears. Only future contributions redirect. |

Must use `decimal.Decimal` with `ROUND_HALF_UP` and +/-£0.01 tolerance, matching existing scorers.

### FR-2: Unified Evidence Bundle Builder

The replay path must produce evidence bundles with the same structure as the OSINT path:

| Directory | OSINT Content | Replay Content |
|-----------|---------------|----------------|
| `inputs/` | Raw API responses | Fixture record inputs |
| `receipts/` | HTTP transcript receipts | Not applicable (empty dir) |
| `gaps/` | GapReports if source failed | Not applicable (empty dir) |
| `scores/` | Per-criterion scores | Per-criterion scores from scorer |
| `policy/` | Not present | Committed policy (waterfall rules, escrow terms) |
| `expected/` | Not present | Ground truth expected outputs |

Plus `theatre_template.json`, `oracle_output.json`, `manifest.json`, `certificate.json`.

The manifest builder from `osint/osint_pipeline/engine/manifest_builder.py` must be shared. The replay path calls the same `build_manifest()` and `manifest_hash()` functions.

### FR-3: Unified Certificate Generator

The `CalibrationCertificate` model from `osint/osint_pipeline/models/certificate.py` must work for both execution paths. The replay path sets:

- `execution_path: "replay"` (OSINT path sets `"osint"`)
- `verification_tier: "UNVERIFIED"` (same as OSINT)
- `oracle_id`: scorer identifier
- `target_entity`: template metadata (template_id, construct_id)

The certificate generator from `osint/osint_pipeline/engine/certificate_generator.py` must accept both OSINT and replay inputs.

### FR-4: Replay-to-Certificate Pipeline Script

Build `scripts/run_two_rail_certificates.py` that:

1. Loads a Two-Rail template JSON
2. Loads the corresponding fixture dataset
3. Runs each fixture record through the appropriate scorer
4. Computes per-criterion scores and composite score
5. Builds the evidence bundle (FR-2 layout)
6. Computes manifest hash (RFC 8785 canonical JSON of flat `{path: sha256}`)
7. Generates the `CalibrationCertificate`
8. Writes certificate + evidence bundle to output directory
9. Runs the Verifier CLI and reports PASS/FAIL

```bash
python scripts/run_two_rail_certificates.py --template escrow_milestone_release_v1
python scripts/run_two_rail_certificates.py --template distribution_waterfall_v1
python scripts/run_two_rail_certificates.py --template ledger_reconciliation_v1
python scripts/run_two_rail_certificates.py --template arrears_resolution_v1
```

### FR-5: Verifier CLI Compatibility

The Verifier CLI (`osint/osint_pipeline/echelon_verify.py`) must handle both OSINT and replay certificates without modification. It checks:

- Manifest hash match (SHA-256 of canonical JSON)
- Commitment hash match (template commitment)
- All criteria passed

If the verifier is already path-agnostic (it checks hashes and schema only), this is a verification pass, not new code.

### FR-6: Re-generate All Four Certificates

Run the pipeline for all four templates and verify:

- All four produce Verifier CLI PASS
- Evidence bundle hashes are deterministic (re-run produces identical hash)
- Composite scores match existing values (0.9091, 0.9333, 0.9333, 0.9375 approximately)
- Dataset hashes match committed hashes in template JSONs

### FR-7: Tests

- Unit tests for `arrears_scorer.py` (6 criteria, all 18 fixture records)
- Integration test: full pipeline for one template (escrow as canonical)
- Determinism test: run same template twice, assert identical evidence bundle hash
- Cross-path test: verify that a replay certificate has the same schema as an OSINT certificate

---

## 5. Existing Assets

### Templates (4 + 1 OSINT)

All in `theatre/fixtures/two_rail_theatres_v0_1/templates/`:

| Template | Criteria | Fixtures |
|----------|----------|----------|
| ESCROW_MILESTONE_RELEASE_V1 | 5 | 11 (v0.2) |
| DISTRIBUTION_WATERFALL_V1 | 5 | 16 (v0.2) |
| LEDGER_RECONCILIATION_V1 | 5 | 16 (v0.2) |
| ARREARS_RESOLUTION_V1 | 6 | 18 (v0.2) |

### Scorers (3 existing, 1 missing)

In `theatre/scoring/`:

- `waterfall_scorer.py` — 5 checks, Decimal arithmetic
- `escrow_scorer.py` — 5 checks, Decimal arithmetic
- `reconciliation_scorer.py` — 5 checks, Decimal arithmetic
- **`arrears_scorer.py` — MISSING** (this cycle builds it)

### Datasets

In `theatre/fixtures/two_rail_theatres_v0_1/datasets/`:

- `arrears_fixtures_v02_18.json` — 18 records
- `waterfall_fixtures_v02_16.json` — 16 records
- `escrow_fixtures_v02_11.json` — 11 records
- `reconciliation_fixtures_v02_16.json` — 16 records

### Existing Runner

`scripts/run_two_rail_theatres.py` (498 lines) handles 3 theatres using the `theatre/engine/` pipeline. This cycle builds a NEW runner that uses the `osint/` pipeline infrastructure instead.

### OSINT Pipeline (shared infrastructure)

In `osint/osint_pipeline/`:

- `engine/manifest_builder.py` — `build_manifest()`, `manifest_hash()`
- `engine/canonical.py` — RFC 8785 canonical JSON, `canonical_hash()`
- `engine/certificate_generator.py` — `CertificateGenerator.generate()`
- `models/certificate.py` — `CalibrationCertificate`
- `echelon_verify.py` — Verifier CLI

---

## 6. Success Criteria

| ID | Criterion |
|----|-----------|
| SC-01 | `arrears_scorer.py` exists and correctly scores all 18 fixture records |
| SC-02 | Evidence bundle builder is shared between OSINT and replay paths |
| SC-03 | Certificate generator works for both execution paths |
| SC-04 | `run_two_rail_certificates.py` produces certificates for all four templates |
| SC-05 | All four certificates pass Verifier CLI |
| SC-06 | Evidence bundle hashes are deterministic across runs |
| SC-07 | Manifest uses RFC 8785 canonical JSON (same as OSINT path) |
| SC-08 | All existing tests pass (70 osint + theatre tests) |
| SC-09 | New tests pass (arrears scorer + integration + determinism) |
| SC-10 | No modifications to existing `theatre/engine/` or `theatre/scoring/` files |

---

## 7. Out of Scope

- No new templates
- No new fixtures
- No OSINT integration for Two-Rail (future cycle — live HMLR/Companies House data)
- No LMSR market engine
- No Base chain deployment
- No frontend

---

## 8. Risks

| Risk | Mitigation |
|------|------------|
| Arrears fixture format differs from other scorers | Read existing scorers first, match interface |
| Certificate model missing replay-specific fields | Add optional fields (e.g. `replay_count`) with defaults |
| Existing theatre tests break | SC-10 requires zero changes to existing files |
