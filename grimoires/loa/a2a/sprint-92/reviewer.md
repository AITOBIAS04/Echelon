# Sprint 92 — Construct Anchor Mapping (Cycle-026a Sprint 3)

## Summary

Implements the construct anchor mapper that connects evaluation dimensions to external evidence anchors via keyword-based matching rules. Dimensions with no recognized anchor are explicitly flagged as weakly anchored.

## Files Created

| File | Purpose |
|------|---------|
| `backend/services/construct_anchor_mapper.py` | Core mapper: `map_dimension_anchors()` and `map_contract_anchors()` |
| `backend/scripts/build_eval_asset_manifest.py` | CLI utility to generate an asset manifest from a local folder |
| `backend/tests/test_cycle026a_sprint3.py` | 7 test classes, 20+ test cases for anchor mapping |

## Design Decisions

### Keyword Matching Strategy

Mapping rules are defined as a flat list of `(keywords, anchor_class, anchor_id, rationale)` tuples. A dimension matches a rule if any keyword appears as a substring of the lowercased dimension name. This is intentionally simple and deterministic:

- No regex, no NLP, no scoring
- Multiple rules can match a single dimension (multi-anchor support)
- Unknown dimensions are cleanly flagged as weakly anchored with empty anchors

### Initial Mapping Rules

| Keywords | Anchor Class | Anchor ID |
|----------|-------------|-----------|
| code, compile, lint, test, syntax, type_check, static_analysis | DETERMINISTIC_CHECK | code_verification |
| benchmark, eval_score, humaneval, mbpp, mmlu, hellaswag, swe_bench | BENCHMARK_DATASET | benchmark_suite |
| accessibility, wcag, aria, a11y, ui_compliance, standard, compliance | PUBLIC_STANDARD | public_standard_check |
| factual, real_world, live, external, osint, market_data, regulatory | LIVE_EXTERNAL_EVIDENCE | live_evidence_feed |

### available_anchors Filter

`map_dimension_anchors` accepts an optional `available_anchors` list. When provided, only matched anchors whose `anchor_id` appears in this list are included. If filtering eliminates all matches, the dimension becomes weakly anchored.

## Test Coverage

| Test Class | What It Covers |
|-----------|---------------|
| TestFullyAnchoredMapping | Each anchor class resolves from its keywords; anchors have required fields |
| TestMixedMapping | Contract with both recognized and unrecognized dimensions |
| TestWeakOnlyMapping | Unrecognized dimensions are weakly anchored with empty anchors |
| TestMultiAnchorDimension | Single dimension matching multiple anchor rules |
| TestCaseInsensitiveMatching | Uppercase/mixed-case dimension names still match |
| TestContractMappingSemantics | Order preservation, length preservation, empty contract |
| TestAvailableAnchorsFiltering | Anchor ID allowlist and exclusion-to-weak fallback |

## Review Checklist

- [x] Imports from `backend.schemas.construct_anchor_schema` (not inline definitions)
- [x] Keyword matching is case-insensitive
- [x] A dimension can match multiple anchor classes
- [x] `map_contract_anchors` returns one result per input dimension in order
- [x] Weakly anchored dimensions have `weakly_anchored=True` and empty `anchors`
- [x] CLI script uses argparse and imports `build_manifest` from `r2_manifest_builder`
- [x] Tests do NOT rely on external paths
- [x] All cycle-026a tests pass with 0 regressions
