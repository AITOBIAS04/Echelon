# Sprint-11: Unified Two-Rail Certificate Pipeline

**Cycle:** 007 — Two-Rail Deterministic Theatres
**Pipeline Version:** 0.7.0
**Date:** 2026-03-01

## Release Note

Sprint-11 wires all four Two-Rail templates through the OSINT pipeline infrastructure.
Each template produces a CalibrationCertificate via the same 10-step pipeline used for
live OSINT: RFC 8785 canonical JSON, flat manifests, `echelon_verify()` Verifier CLI.
ArrearsScorer built from scratch: 6 criteria, 24 state transitions, Decimal arithmetic.
Cross-path schema validated — replay certificates pass CalibrationCertificate model.
32 new tests pass with zero regressions across the full suite (239 OSINT + 176 theatre sync).
All four templates PASS the Verifier with deterministic evidence bundles.

## Routing Policy Update

```yaml
execution_path: replay
inquiry_class: INSPECTION
pipeline_version: "0.7.0"
templates:
  - escrow_milestone_release_v1
  - distribution_waterfall_v1
  - ledger_reconciliation_v1
  - arrears_resolution_v1
```

**Import order constraint:** Theatre imports (`theatre.scoring.*`) MUST precede
`osint_pipeline.echelon_verify` because `echelon_verify.py` adds `osint/osint_pipeline/`
to `sys.path` at import time, which shadows root-level `theatre/` with
`osint/osint_pipeline/theatre/` (no scoring submodule).

## Score Delta Table

| Template | Composite | Target | Delta | Verdict |
|----------|-----------|--------|-------|---------|
| `escrow_milestone_release_v1` | 0.8591 | 0.9091 | -0.0500 | Intended (A) |
| `distribution_waterfall_v1` | 0.9333 | 0.9333 | 0.0000 | On target |
| `ledger_reconciliation_v1` | 0.8933 | 0.9333 | -0.0400 | Intended (A) |
| `arrears_resolution_v1` | 0.9375 | 0.9375 | 0.0000 | On target |

Deltas are correlated failure coupling in fixture design, not bugs. Cycle-007 target
composites assumed one-failure-per-record fixtures; the unified pipeline surfaces coupled
failures because records encode compound scenarios. See
`reports/sprint11_score_delta_analysis.md` for full decomposition.

## Version Pins

```yaml
pipeline_version: "0.7.0"
escrow_scorer: v1.0.0
waterfall_scorer: v1.0.0
reconciliation_scorer: v1.0.0
arrears_scorer: v1.0.0
echelon_verify: pinned (osint_pipeline)
```

## Verification

```bash
python3 -m pytest tests/theatre/test_score_breakdown.py -v   # 8 breakdown invariant tests
python3 -m pytest tests/theatre/ -v                          # full theatre suite
```
