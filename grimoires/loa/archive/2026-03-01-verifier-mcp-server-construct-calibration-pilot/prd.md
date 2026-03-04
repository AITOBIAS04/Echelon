# PRD: Verifier MCP Server + Loa Construct Calibration Pilot (Cycle-008)

**Cycle:** 008
**Type:** MCP surface + construct calibration
**Date:** 2026-03-01
**Predecessor:** Cycle-007 (Unified Two-Rail Pipeline, 4 templates PASS, pipeline v0.7.0)

---

## 1. Problem Statement

Echelon's Verifier exists only as a CLI tool (`echelon_verify.py`) and direct Python imports. Downstream integrations (Claude Code, Loa, CI/CD, Soju's Constructs Network) cannot call verification programmatically without importing the full pipeline. The verification surface needs a transport-agnostic wrapper.

Additionally, the first construct certificate (`community_oracle_v1`, composite 0.700) was produced by an early pipeline before Cycle-004 hardening. It has only 10 replays, no evidence bundle with manifest, no independence dedup, no receipt enforcement, and no Verifier CLI compatibility. The construct needs re-certification through the proven Cycle-007 infrastructure.

> Sources: `grimoires/loa/context/echelon_cycle_008_context.md`, `grimoires/loa/context/echelon_platform_roadmap.md`

---

## 2. Objective

Two deliverables in one cycle:

1. **Sprint 1 — Verifier MCP Server v1.0:** Wrap the existing Python verifier in an MCP server (stdio transport). Five stateless tools, no new verification logic. Every tool maps directly to an existing CLI command or library function.

2. **Sprint 2 — Construct Calibration Pilot:** Re-certify `community_oracle_v1` through the Cycle-007 unified pipeline infrastructure, producing proper calibration certificates with evidence bundles, manifests, and Verifier PASS via the MCP server built in Sprint 1.

After this cycle:
- The Verifier is callable externally via MCP (stdio)
- First Loa construct has a pipeline-hardened certificate
- Soju conversation has a concrete artefact with a verification command
- Foundation for `echelon_status` (embeddable endpoint) in Cycle-009

---

## 3. Scope

### In Scope

| Item | Sprint | Description |
|------|--------|-------------|
| MCP server (stdio) | 1 | Five stateless tools: verify, inspect, hash, schema_check, replay |
| _meta envelope | 1 | engine_version, schema_versions, timestamp on every response |
| Standardised errors | 1 | SCHEMA_INVALID, HASH_MISMATCH, INPUT_MALFORMED, INTERNAL_ERROR |
| Errata application | 1 | "Echelon Canonical JSON v0" naming, (param, id) sort for resolved_inputs |
| CONSTRUCT_CALIBRATION_V1 template | 2 | Product family template with precision/recall/reply_accuracy criteria |
| Construct calibration scorer | 2 | Deterministic scorer against pre-annotated fixtures |
| Fixture dataset | 2 | 10+ records from community_oracle_v1 replay data |
| Dedicated calibration runner | 2 | `scripts/run_construct_calibration.py` (separate from Two-Rail runner) |
| MCP verification loop | 2 | Integration test: generate certificate → verify via MCP → assert PASS |
| Results summary | 2 | One-page report for Soju |

### Out of Scope

- `echelon_calibrate` or `echelon_status` tools (stateful — v1.1)
- SSE transport (v1.1)
- Authentication or rate limiting (v1.1)
- `id` mode for input typing (store lookup — v1.1)
- OSINT live data for construct calibration
- LLM-based scoring
- Base chain deployment
- Frontend or dashboard
- Expansion beyond community_oracle_v1

---

## 4. Users & Stakeholders

| User | Need | Sprint |
|------|------|--------|
| Claude Code / Loa | Programmatic certificate verification via MCP | 1 |
| CI/CD pipelines | Automated verification in build steps | 1 |
| Soju / Constructs Network | Concrete calibration artefact with verification command | 2 |
| Construct developers | Self-service calibration pathway | 2 |

---

## 5. Functional Requirements

### FR-1: MCP Server (Sprint 1)

**FR-1.1** The server MUST run over stdio transport (stdin/stdout).

**FR-1.2** Five tools MUST be exposed:

| Tool | Delegates To | Input | Output |
|------|-------------|-------|--------|
| `echelon_verify` | `echelon_verify.py verify` | certificate JSON (inline) + evidence bundle path | `{ overall_verdict, checks[], _meta }` |
| `echelon_inspect` | `echelon_verify.py inspect` | certificate JSON (inline) | `{ summary, _meta }` |
| `echelon_hash` | canonical hash computation | raw content (JSON or bytes) | `{ hash: "sha256:...", _meta }` |
| `echelon_schema_check` | schema validation | certificate JSON (inline) | `{ valid, errors[], _meta }` |
| `echelon_replay` | structural consistency check | template JSON (inline) + fixtures JSON (inline) | `{ consistent, mismatches[], _meta }` |

**FR-1.3** Every response MUST include `_meta` object: `{ engine_version, schema_versions, timestamp }`.

**FR-1.4** Error responses MUST use committed codes: `SCHEMA_INVALID`, `HASH_MISMATCH`, `INPUT_MALFORMED`, `INTERNAL_ERROR`. Format: `{ overall_verdict: "ERROR", error_code, error_message, _meta }`.

**FR-1.5** All JSON content parameters MUST use inline mode objects: `{"mode": "inline", "value": {...}}`. `id` mode deferred to v1.1.

**FR-1.6** Errata MUST be applied:
- Replace all "RFC 8785" references with "Echelon Canonical JSON v0"
- Reuse existing canonical hash utility (import from pipeline's canonical module)
- `resolved_inputs` sorted lexicographically by `(param, id)` before hashing

**FR-1.7** All five tools MUST be pure functions — no network calls, no side effects, no state.

**FR-1.8** Existing Cycle-007 certificates MUST verify via MCP `echelon_verify` tool.

### FR-2: Construct Calibration (Sprint 2)

**FR-2.1** CONSTRUCT_CALIBRATION_V1 template MUST define three criteria: precision (0.40), recall (0.40), reply_accuracy (0.20).

**FR-2.2** `construct_calibration_scorer.py` MUST score against pre-annotated fixtures (deterministic — no LLM calls at scoring time).

**FR-2.3** Fixture dataset MUST contain 10+ records from community_oracle_v1 replay data. Each record has `inputs` (PR diff, construct output, Q&A pairs), `expected_outputs` (ground truth annotations).

**FR-2.4** `scripts/run_construct_calibration.py` MUST be a dedicated entrypoint. MUST NOT import from or call `run_two_rail_certificates.py`.

**FR-2.5** The runner MUST accept `--construct community_oracle_v1` and `--construct-source` override.

**FR-2.6** Evidence bundle MUST follow FR-2 layout: `inputs/`, `expected/`, `scores/`, `manifest.json`.

**FR-2.7** Certificate MUST verify via MCP `echelon_verify` tool (PASS).

**FR-2.8** Re-run MUST produce identical evidence bundle hash (determinism).

**FR-2.9** Results summary MUST be produced at `reports/construct_calibration_pilot.md`.

---

## 6. Non-Functional Requirements

**NFR-1** All tools deterministic — same input produces identical output.

**NFR-2** No new external dependencies beyond MCP SDK (`mcp` Python package).

**NFR-3** All existing tests MUST pass (447+ from Cycles 002–007).

**NFR-4** New tests: 15–20 for MCP tools (Sprint 1), 10+ for scorer/integration (Sprint 2).

**NFR-5** Construct scoring uses float-safe comparison, not Decimal arithmetic (semantic accuracy, not financial precision).

---

## 7. Success Criteria

### Sprint 1
1. MCP server runs over stdio
2. Five tools functional (verify, inspect, hash, schema_check, replay)
3. Errata applied (Echelon Canonical JSON v0, resolved_inputs sorting)
4. All existing Cycle-007 certificates verify via MCP tools
5. Standardised error responses for malformed inputs
6. 15–20 new tests passing

### Sprint 2
7. CONSTRUCT_CALIBRATION_V1 template created
8. construct_calibration_scorer.py implements 3 criteria (deterministic)
9. community_oracle_v1 fixture dataset created (10+ records)
10. Certificate generated via dedicated runner
11. Certificate verified via MCP `echelon_verify` tool (PASS)
12. Evidence bundle has manifest, inputs, expected, scores
13. Evidence bundle hash is deterministic (rerun produces same hash)
14. Results summary produced for Soju
15. All existing tests pass (447+)
16. New tests pass (scorer + integration + MCP verification loop)

---

## 8. Dependency Chain

```
Cycle-004 (pipeline hardening)
  → Cycle-005 (registry v0.6.0, 77 sources)
    → Cycle-006 (live OSINT certificate)
      → Cycle-007 (unified Two-Rail pipeline, 4 templates PASS)
        → Cycle-008 Sprint 1 (MCP Server — makes verifier callable)
          → Cycle-008 Sprint 2 (construct calibration — first MCP consumer)
```

---

## 9. Existing Data

### First-Run Certificate (`product_observer_v1_first_run.json`)

```
certificate_id: 402f03b0-7852-48e2-8881-f82ea5bc005a
construct_id: community_oracle_v1
template_id: product_observer_v1
criteria: precision (0.4), recall (0.4), reply_accuracy (0.2)
scores: precision 0.8, recall 0.55, reply_accuracy 0.8
composite_score: 0.700
replay_count: 10
verification_tier: UNVERIFIED
scorer_version: anthropic-claude-sonnet-4-20250514
execution_path: replay
```

### Existing API Surface (to wrap in MCP)

| Function | Location | Purpose |
|----------|----------|---------|
| `cmd_verify()` | `tools/echelon_verify.py` | Full certificate verification |
| `cmd_inspect()` | `tools/echelon_verify.py` | Certificate summary (no verification) |
| `cmd_hash()` | `tools/echelon_verify.py` | SHA-256 canonical hash |
| `cmd_schema_check()` | `tools/echelon_verify.py` | Schema validation |
| `cmd_replay()` | `tools/echelon_verify.py` | Structural consistency check |
| `canonical_hash()` | `osint_pipeline/engine/canonical.py` | RFC 8785 JSON → SHA-256 |
| `build_manifest()` | `osint_pipeline/engine/manifest_builder.py` | Deterministic file inventory |
| `CertificateGenerator` | `osint_pipeline/engine/certificate_generator.py` | Certificate construction |

### Construct Observer Repo

Source: `/Users/tobiasharber/Developer/construct-observer`

The Observer construct is a user research pipeline (24 skills, schema v3). No existing fixture data or replay records exist in the repo — fixtures must be constructed from the first-run certificate data or synthesised from the construct's template definitions.
