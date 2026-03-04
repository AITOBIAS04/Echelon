# SDD: Verifier MCP Server + Loa Construct Calibration Pilot (Cycle-008)

**Cycle:** 008
**Date:** 2026-03-01
**PRD:** `grimoires/loa/prd.md`

---

## 1. Architecture Overview

Two components, sequential dependency:

```
Sprint 1: MCP Server
  mcp/
  ├── server.py              ← stdio MCP entry point
  ├── tools/                 ← 5 tool handlers (verify, inspect, hash, schema_check, replay)
  ├── models/                ← _meta envelope, error codes, input mode objects
  └── tests/                 ← 15-20 tests

Sprint 2: Construct Calibration
  theatre/fixtures/construct_calibration/
  ├── templates/             ← CONSTRUCT_CALIBRATION_V1.template.json
  └── datasets/              ← community_oracle_v1_fixtures.json
  theatre/scoring/
  └── construct_calibration_scorer.py
  scripts/
  └── run_construct_calibration.py   ← Dedicated entrypoint (NOT run_two_rail_certificates.py)
  tests/
  ├── theatre/test_construct_calibration.py
  └── mcp/test_mcp_integration.py
```

---

## 2. Sprint 1 — MCP Server Design

### 2.1 Transport

stdio only (v1.0). The MCP SDK's `StdioServerTransport` handles framing. The server reads JSON-RPC messages from stdin, dispatches to tool handlers, writes responses to stdout.

### 2.2 Server Entry Point

`mcp/server.py`:

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server

app = Server("echelon-verifier")

@app.list_tools()
async def list_tools() -> list[Tool]: ...

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[Content]: ...

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())
```

### 2.3 Tool Handlers

Each tool handler lives in `mcp/tools/` and delegates to existing pipeline functions.

#### `echelon_verify` → `mcp/tools/verify.py`

- **Input:** `{ certificate: { mode: "inline", value: {...} }, evidence_bundle_path: string }`
- **Process:** Write certificate to temp file → call verification logic from `tools/echelon_verify.py` → collect `VerificationReport`
- **Output:** `{ overall_verdict: "PASS"|"FAIL", checks: [...], _meta: {...} }`
- **Delegates to:** `VerificationReport` construction from `echelon_verify.py`

#### `echelon_inspect` → `mcp/tools/inspect.py`

- **Input:** `{ certificate: { mode: "inline", value: {...} } }`
- **Process:** Parse certificate, extract summary fields
- **Output:** `{ summary: { certificate_id, template_id, composite_score, verification_tier, ... }, _meta: {...} }`
- **No verification performed**

#### `echelon_hash` → `mcp/tools/hash.py`

- **Input:** `{ content: { mode: "inline", value: {...} } }`
- **Process:** `canonical_hash(value)` from `osint_pipeline/engine/canonical.py`
- **Output:** `{ hash: "sha256:abcdef...", _meta: {...} }`
- **Reuses existing canonical hash utility — no new implementation**

#### `echelon_schema_check` → `mcp/tools/schema_check.py`

- **Input:** `{ certificate: { mode: "inline", value: {...} } }`
- **Process:** Run schema validation checks (SCHEMA-001 through SCHEMA-HASH-*)
- **Output:** `{ valid: bool, errors: [...], _meta: {...} }`

#### `echelon_replay` → `mcp/tools/replay.py`

- **Input:** `{ template: { mode: "inline", value: {...} }, fixtures: { mode: "inline", value: {...} } }`
- **Process:** Structural consistency check (REPLAY-001 through REPLAY-006)
- **Output:** `{ consistent: bool, mismatches: [...], _meta: {...} }`

### 2.4 Models

#### `_meta` Envelope (`mcp/models/meta.py`)

```python
@dataclass
class Meta:
    engine_version: str       # "0.8.0" (cycle-008)
    schema_versions: dict     # { "certificate": "1.0.0", "theatre": "2.0.0" }
    timestamp: str            # ISO-8601 UTC
    resolved_inputs: list[dict] | None  # For tools with store lookups (v1.1)
    resolved_inputs_hash: str | None    # SHA-256 of sorted resolved_inputs
```

#### Error Codes (`mcp/models/errors.py`)

```python
ERROR_CODES = {
    "SCHEMA_INVALID": "Certificate does not conform to required schema",
    "HASH_MISMATCH": "Computed hash does not match declared hash",
    "INPUT_MALFORMED": "Input parameters are malformed or missing required fields",
    "INTERNAL_ERROR": "Unexpected internal error during processing",
}
```

Error response format:
```json
{
  "overall_verdict": "ERROR",
  "error_code": "INPUT_MALFORMED",
  "error_message": "Missing required field: certificate",
  "_meta": { "engine_version": "0.8.0", "timestamp": "..." }
}
```

#### Input Mode Objects (`mcp/models/inputs.py`)

```python
@dataclass
class InlineInput:
    mode: Literal["inline"] = "inline"
    value: Any  # The actual JSON content

# v1.1: IdInput with mode="id" for store lookups
```

### 2.5 Errata Application

1. All documentation and code comments: "Echelon Canonical JSON v0" (not "RFC 8785")
2. `echelon_hash` tool: import `canonical_hash` from `osint_pipeline/engine/canonical.py`
3. `resolved_inputs` (when present): sorted by `(param, id)` tuple before hashing

### 2.6 Test Strategy (Sprint 1)

| Test File | Tests | What It Validates |
|-----------|-------|-------------------|
| `mcp/tests/test_verify.py` | 3-4 | PASS for valid cert, FAIL for tampered, ERROR for malformed |
| `mcp/tests/test_inspect.py` | 2-3 | Summary extraction, error on invalid JSON |
| `mcp/tests/test_hash.py` | 3-4 | Canonical hash parity with existing utility, bytes input, JSON input |
| `mcp/tests/test_schema_check.py` | 2-3 | Valid schema, schema violations |
| `mcp/tests/test_replay.py` | 2-3 | Consistent template+fixtures, mismatches detected |
| `mcp/tests/test_errors.py` | 2-3 | Standardised error format for each error code |

Total: 15-20 tests

---

## 3. Sprint 2 — Construct Calibration Design

### 3.1 Template

`theatre/fixtures/construct_calibration/templates/CONSTRUCT_CALIBRATION_V1.template.json`:

```json
{
  "template_id": "CONSTRUCT_CALIBRATION_V1",
  "template_family": "PRODUCT",
  "execution_path": "replay",
  "inquiry_class": "INSPECTION",
  "domain": "construct_verification",
  "criteria": {
    "criteria_ids": ["precision", "recall", "reply_accuracy"],
    "criteria_human": "Precision: fraction of oracle claims supported by PR diff. Recall: fraction of important changes surfaced. Reply Accuracy: factual grounding of follow-up responses.",
    "weights": {
      "precision": 0.40,
      "recall": 0.40,
      "reply_accuracy": 0.20
    }
  },
  "dataset_hash": "<sha256 of canonical fixtures JSON>",
  "version": "1.0.0"
}
```

### 3.2 Scorer

`theatre/scoring/construct_calibration_scorer.py`:

Deterministic scoring against pre-annotated fixtures. Each fixture record contains binary pass/fail annotations per criterion per claim.

```python
class ConstructCalibrationScorer:
    """Deterministic construct calibration scorer.

    Unlike Two-Rail scorers (Decimal arithmetic for financial precision),
    this scorer uses float-safe comparison for semantic accuracy metrics.
    """

    CRITERIA = {"precision", "recall", "reply_accuracy"}

    async def score(
        self,
        criteria_id: str,
        ground_truth: dict[str, Any],
        oracle_output: dict[str, Any],
    ) -> float:
        """Score a single criterion for a single record.

        ground_truth contains pre-annotated pass/fail per claim.
        Returns pass_rate (0.0-1.0) for the criterion.
        """
        ...
```

**Precision scoring:** Count claims in construct output that are supported by PR diff ground truth. `precision = supported_claims / total_claims`.

**Recall scoring:** Count important PR changes that appear in construct summary. `recall = surfaced_changes / total_important_changes`.

**Reply accuracy scoring:** Count factually grounded follow-up answers. `reply_accuracy = grounded_answers / total_answers`.

All comparisons are against pre-annotated ground truth in the fixture — no LLM call at scoring time.

### 3.3 Fixture Dataset

`theatre/fixtures/construct_calibration/datasets/community_oracle_v1_fixtures.json`:

Each record encodes one PR replay with pre-annotated ground truth:

```json
{
  "records": [
    {
      "record_id": "oracle_0001",
      "input_data": {
        "pr_diff": "...",
        "construct_summary": "...",
        "followup_qa": [
          { "question": "...", "answer": "..." }
        ]
      },
      "expected_output": {
        "precision_annotations": {
          "claims": [
            { "claim": "...", "supported": true },
            { "claim": "...", "supported": false }
          ]
        },
        "recall_annotations": {
          "important_changes": [
            { "change": "...", "surfaced": true },
            { "change": "...", "surfaced": false }
          ]
        },
        "reply_accuracy_annotations": {
          "answers": [
            { "question": "...", "grounded": true }
          ]
        }
      }
    }
  ]
}
```

Source data: first-run certificate had 10 replays with precision 0.8, recall 0.55, reply_accuracy 0.8. Fixture records must reproduce these score distributions.

### 3.4 Dedicated Runner

`scripts/run_construct_calibration.py`:

**Separate entrypoint.** MUST NOT import from or call `run_two_rail_certificates.py`. Runner semantics differ: construct semantic calibration vs Two-Rail arithmetic determinism.

Shared utility logic (manifest building, canonical hashing, certificate generation) MAY be extracted into `scripts/_certificate_pipeline.py` only if duplication exceeds ~30 lines. Entrypoints MUST remain separate.

```
run_construct_calibration.py
  1. Accept --construct community_oracle_v1 [--construct-source PATH]
  2. Load CONSTRUCT_CALIBRATION_V1 template
  3. Load construct-observer artefacts from construct-source
  4. Map artefacts to ConstructCalibrationInput
  5. Load fixture dataset
  6. Score each record via construct_calibration_scorer (N=10+)
  7. Build evidence bundle:
     - inputs/ — construct artefacts
     - expected/ — pre-annotated ground truth
     - scores/ — per-record + aggregate
     - manifest.json
  8. Compute evidence bundle hash
  9. Generate CalibrationCertificate
  10. Verify via MCP echelon_verify (Sprint 1 dep)
  11. Write to output/construct_calibration/community_oracle_v1/
  12. Produce index.json for batch runs
```

### 3.5 MCP Verification Loop

Integration test at `tests/mcp/test_mcp_integration.py`:

1. Generate certificate via `run_construct_calibration.py`
2. Call MCP `echelon_verify` tool programmatically
3. Assert PASS
4. Tamper with certificate → assert FAIL

### 3.6 Test Strategy (Sprint 2)

| Test File | Tests | What It Validates |
|-----------|-------|-------------------|
| `tests/theatre/test_construct_calibration.py` | 6-8 | Scorer per-criterion, composite, fixture structure, template schema |
| `tests/mcp/test_mcp_integration.py` | 3-4 | End-to-end: generate → verify PASS, tamper → verify FAIL |

Total: 10-12 new tests

---

## 4. File Inventory

### Sprint 1 (New Files)

| File | Purpose |
|------|---------|
| `mcp/__init__.py` | Package init |
| `mcp/server.py` | stdio MCP server entry point |
| `mcp/tools/__init__.py` | Tools package |
| `mcp/tools/verify.py` | echelon_verify handler |
| `mcp/tools/inspect.py` | echelon_inspect handler |
| `mcp/tools/hash.py` | echelon_hash handler |
| `mcp/tools/schema_check.py` | echelon_schema_check handler |
| `mcp/tools/replay.py` | echelon_replay handler |
| `mcp/models/__init__.py` | Models package |
| `mcp/models/meta.py` | _meta envelope |
| `mcp/models/errors.py` | Error codes and format |
| `mcp/models/inputs.py` | Input mode objects |
| `mcp/tests/__init__.py` | Tests package |
| `mcp/tests/test_verify.py` | Verify tool tests |
| `mcp/tests/test_inspect.py` | Inspect tool tests |
| `mcp/tests/test_hash.py` | Hash tool tests |
| `mcp/tests/test_schema_check.py` | Schema check tests |
| `mcp/tests/test_replay.py` | Replay tool tests |
| `mcp/tests/test_errors.py` | Error format tests |

### Sprint 2 (New Files)

| File | Purpose |
|------|---------|
| `theatre/fixtures/construct_calibration/templates/CONSTRUCT_CALIBRATION_V1.template.json` | Template |
| `theatre/fixtures/construct_calibration/datasets/community_oracle_v1_fixtures.json` | Fixtures |
| `theatre/scoring/construct_calibration_scorer.py` | 3-criteria scorer |
| `scripts/run_construct_calibration.py` | Dedicated runner |
| `tests/theatre/test_construct_calibration.py` | Scorer + fixture tests |
| `tests/mcp/test_mcp_integration.py` | MCP verification loop |
| `reports/construct_calibration_pilot.md` | Results summary for Soju |

### Modified Files

| File | Change |
|------|--------|
| `requirements.txt` (or equivalent) | Add `mcp` SDK dependency |

---

## 5. Integration Points

### Sprint 1 Imports (MCP → existing pipeline)

| MCP Tool | Imports From | Function |
|----------|-------------|----------|
| verify | `tools/echelon_verify.py` | Verification logic |
| inspect | `tools/echelon_verify.py` | Certificate parsing |
| hash | `osint_pipeline/engine/canonical.py` | `canonical_hash()` |
| schema_check | `tools/echelon_verify.py` | Schema validation checks |
| replay | `tools/echelon_verify.py` | Structural consistency |

### Sprint 2 Imports (runner → pipeline)

| Runner | Imports From | Function |
|--------|-------------|----------|
| run_construct_calibration.py | `osint_pipeline/engine/canonical.py` | `canonical_hash()` |
| run_construct_calibration.py | `osint_pipeline/engine/manifest_builder.py` | `build_manifest()`, `manifest_hash()` |
| run_construct_calibration.py | `osint_pipeline/engine/certificate_generator.py` | `CertificateGenerator` |
| run_construct_calibration.py | `theatre/scoring/construct_calibration_scorer.py` | `ConstructCalibrationScorer` |
| run_construct_calibration.py | `mcp/tools/verify.py` | MCP verify (integration test) |

---

## 6. Constraints

1. **No network calls** in MCP tools — all pure functions
2. **No Decimal arithmetic** in construct scorer — uses float comparison (semantic, not financial)
3. **No import from `run_two_rail_certificates.py`** in construct calibration runner
4. **Errata-first** — Echelon Canonical JSON v0 naming throughout
5. **Determinism** — rerun produces identical evidence bundle hash
6. **Existing tests MUST pass** — 447+ from Cycles 002-007
