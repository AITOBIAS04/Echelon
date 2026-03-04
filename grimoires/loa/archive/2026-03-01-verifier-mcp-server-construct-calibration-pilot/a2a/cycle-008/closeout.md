# Cycle-008 Close-out — Verifier MCP Server + Construct Calibration Pilot

**Cycle**: cycle-008
**Branch**: `feature/cycle-008-mcp-server`
**Status**: COMPLETE
**Date**: 2026-03-01

---

## A) Executive Summary

Cycle-008 delivers two capabilities that did not previously exist in the Echelon stack.

Sprint-1 (global sprint-12) shipped the **Echelon Verifier MCP Server v0.8.0** — a stdio-based JSON-RPC 2.0 server exposing five stateless verification tools. Any MCP-compatible client can now programmatically verify certificates, inspect their structure, compute canonical hashes, validate schemas, and perform structural replays without importing Python modules directly. The server requires Python 3.9+ and carries zero SDK dependencies.

Sprint-2 (global sprint-13) shipped the **Loa Construct Calibration Pilot**, proving that a PRODUCT-family theatre template can score a construct's semantic accuracy against pre-annotated ground truth using the existing replay engine. The `community_oracle_v1` construct was calibrated across precision, recall, and reply accuracy, producing a certificate that passes `echelon_verify`. This establishes the pattern for calibrating any future construct.

Together, these sprints close the loop: constructs can be calibrated deterministically, and the resulting certificates can be verified over a standard protocol boundary.

---

## B) Artefacts & Version Pins

| Item | Value |
|------|-------|
| Branch | `feature/cycle-008-mcp-server` |
| MCP Server Version | `0.8.0` |
| MCP Tools | `echelon_verify`, `echelon_inspect`, `echelon_hash`, `echelon_schema_check`, `echelon_replay` |
| Template ID | `CONSTRUCT_CALIBRATION_V1` |
| Construct ID | `community_oracle_v1` |
| Evidence Bundle Hash | `cabd0288dc5386fbdc8748b8ce6931b1eb6aca2aeadb32a14afaa133788b36c2` |
| Commitment Hash | `1d258c8ce6070b43cd00e1ebe8cc96d0eeba4ccd13162a32ddf5873c18084287` |
| Certificate ID | `a64c7236-d229-5c6d-acb5-b4f6dfc2cd22` |
| Certificate Output | `output/construct_calibration/community_oracle_v1/certificates/CONSTRUCT_CALIBRATION_V1.json` |
| Evidence Output | `output/construct_calibration/community_oracle_v1/evidence/` |
| MCP Server Entry | `mcp/server.py` |
| Runner Script | `scripts/run_construct_calibration.py` |

---

## C) Acceptance Criteria Checklist

- [x] MCP server tools work over stdio (JSON-RPC 2.0, tested with raw JSON payloads)
- [x] Construct runner exists at `scripts/run_construct_calibration.py` and does not import `run_two_rail_certificates.py`
- [x] Evidence bundle contains `inputs/`, `expected/`, `scores/`, and `manifest.json`
- [x] Rerun determinism — same evidence bundle hash across consecutive runs (verified in `tests/test_mcp_integration.py::test_deterministic_evidence_bundle_hash`)
- [x] `echelon_verify` returns PASS for generated certificate
- [x] 23 new tests pass (19 theatre + 4 MCP integration)
- [x] Tampered certificate correctly fails verification

---

## D) Known Limits

- Verification tier is **UNVERIFIED** (N=12 replays; 50+ required for BACKTESTED).
- MCP server does not yet expose `echelon_status` or `echelon_calibrate` tools.
- No public hosted UI or HTTP transport for the MCP server (stdio only).
- Recall score (0.5417) is lower than precision/reply accuracy by design — the fixture dataset models realistic scenarios where constructs miss subtle changes. This is not a defect.
- The construct calibration runner is a standalone script; it is not yet integrated into the unified `run_two_rail_certificates.py` pipeline.

---

## E) Next Cycle Recommendation

Two options for Cycle-009, in order of recommendation:

1. **Status tool + deployability routing** — Add `echelon_status` and `echelon_calibrate` MCP tools, implement HTTP/SSE transport alongside stdio, and create a deployment configuration (Docker or serverless) so the verifier can run as a persistent service rather than a subprocess.

2. **Certificate display page wired to MCP** — Build a minimal frontend view that calls the MCP server to render certificate details, verification results, and evidence bundle contents in a human-readable format.

Registry expansion work is queued but not recommended for Cycle-009.
