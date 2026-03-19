# PRD — Cycle-037d: Theatre Construct Verification

**Cycle:** cycle-037d
**Date:** 19 March 2026
**Depends on:** Cycle-037 (contract substrate), Cycle-037b (multi-evaluator), Cycle-037c (domain packs + security checks)
**Sprints:** 4 (0-3)
**Builder:** Loa (backend only)
**Planning source:** context_037d.md, TREMOR construct analysis, CORONA construct analysis, codebase validation

> Sources: context_037d.md, TREMOR BUTTERFREEZONE.md, CORONA BUTTERFREEZONE.md, codebase analysis of spec_loader.py, check_planner.py, construct_anchor_mapper.py, models.py

---

## 1. Problem Statement

### 1.1 The Contract System Assumes Every Construct Is A Skill

`ConstructSpec` has no `construct_class` field (spec_loader.py:13-22). The `skill_manifest` field and all check families (RUBRIC, BENCHMARK, ANCHOR) are designed for constructs that produce text or code outputs. Theatre constructs — which ingest live data, run prediction markets, settle against external oracles, and export calibration artifacts — are a fundamentally different verification target.

### 1.2 Theatre Constructs Are Often Easier To Verify

Theatre constructs like TREMOR and CORONA are unusually well-suited to deterministic verification:

- settlement accuracy is recomputable (binary outcomes against public oracles)
- Brier scores are recomputable (pure arithmetic over position history)
- oracle consistency is recomputable (cross-source comparison)
- confidence discounting is often a pure function

This means theatre-construct certificates can become the **highest-credibility certificate class** because the full evaluation chain can be deterministic and externally anchored.

### 1.3 TREMOR And CORONA Prove The Pattern

Two external theatre constructs now exist:

- **TREMOR** (seismic) — 5 theatre types, USGS/EMSC oracles, 48 tests, Brier-scored RLMF certificates
- **CORONA** (space weather) — 5 theatre types, NOAA SWPC/NASA DONKI oracles, 60 tests, same certificate schema

Both share identical architectural patterns: oracle polling, evidence bundles, theatre-scoped prediction markets, RLMF export. They demonstrate that theatre constructs need their own verification families — not rubric scoring, but settlement and calibration correctness.

### 1.4 The Goal Is Not "Hardcode Theatre Checks Everywhere"

Cycle 037d follows the same design principle as 037c: it is a **construct-class layer** on top of the general substrate. The base contract pipeline (037) remains untouched. Theatre-specific check families are additive, selected when `construct_class == "theatre"`.

---

## 2. Product Contracts

### 2.1 Construct Class Differentiation

Add a `construct_class` field to `ConstructSpec` and `ConstructRegistration`:

Recommended classes:
- `skill` — code/text output constructs (current default)
- `theatre` — live data ingestion, prediction markets, oracle-settled constructs
- `bridge` — reserved for future cross-construct orchestration

When `construct_class` is absent or unrecognized, default to `skill` to preserve backward compatibility with all existing constructs.

### 2.2 Theatre-Oriented Check Families

New check types for theatre constructs, selected when `construct_class == "theatre"`:

| Check Type | What It Verifies | Anchor Class |
|---|---|---|
| `SETTLEMENT_ACCURACY` | Binary/multi-class outcomes match oracle ground truth | `LIVE_EXTERNAL_EVIDENCE` |
| `ORACLE_CONSISTENCY` | Cross-source oracle agreement within tolerance | `LIVE_EXTERNAL_EVIDENCE` |
| `CALIBRATION_VALIDITY` | Brier scores, calibration buckets, ECE are arithmetically consistent | `DETERMINISTIC_CHECK` |
| `FUNCTIONAL_CORRECTNESS` | Theatre template logic produces correct state transitions | `DETERMINISTIC_CHECK` |

These checks are **stronger than rubric-based evaluation** because they resolve against arithmetic and public data, not subjective scoring.

### 2.3 Theatre Check Planner

Add `backend/services/theatre_check_planner.py` following the pattern of `security_check_planner.py`:

- `plan_theatre_checks(spec, construct_json)` — generates theatre-specific `PlannedCheck` entries
- `merge_theatre_checks(base_checks, theatre_checks)` — merges with base checks, preserving sort order and deduplication

The caller-side merge pattern from 037c is preserved: `contract_service.py` calls the theatre planner and merges, the base planner is not modified.

### 2.4 Construct JSON Ingestion

TREMOR and CORONA both ship a `construct.json` (or `spec/construct.json`) that declares:

- theatre templates with resolution rules
- OSINT source definitions
- verification checks with oracle references
- settlement tiers

Add an optional `construct_json` parameter to the contract pipeline (parallel to `corpus_skills` from 037c) that the theatre check planner can consume.

### 2.5 Theatre Anchor Mapping Rules

Extend `construct_anchor_mapper.py` with theatre-specific mapping rules:

| Dimension Keywords | Anchor Class |
|---|---|
| `settlement`, `oracle`, `ground_truth` | `LIVE_EXTERNAL_EVIDENCE` |
| `brier`, `calibration`, `ece` | `DETERMINISTIC_CHECK` |
| `position_history`, `temporal_analysis` | `DETERMINISTIC_CHECK` |
| `usgs`, `emsc`, `swpc`, `donki`, `noaa` | `LIVE_EXTERNAL_EVIDENCE` |

### 2.6 Theatre Precise Domains

Register theatre-specific precise domains in `KNOWN_PRECISE_DOMAINS` following the pattern of `security_policy_rules.py`:

- `seismic_intelligence`
- `space_weather`
- `oracle_verification`
- `settlement_verification`
- `calibration_analysis`

This prevents `normalize()` from classifying theatre-oriented domain claims as vague.

### 2.7 TREMOR As First Fixture

TREMOR is the first theatre-construct fixture:

- 5 theatre templates → check planning should detect and plan for each
- USGS + EMSC oracles → oracle consistency checks
- Brier-scored certificates → calibration validity checks
- Binary/multi-class settlements → settlement accuracy checks

CORONA is the second fixture (same pattern, different domain).

---

## 3. What This Cycle Does NOT Do

- **Does NOT modify the base contract pipeline** (037 substrate stays untouched)
- **Does NOT add theatre runtime logic** (the constructs run independently; this is verification only)
- **Does NOT add cross-theatre paradox detection** (that is Cycle 038)
- **Does NOT require database migrations** (construct_class can be derived from construct.json or stored as a JSON field on existing models)
- **Does NOT make theatre-class mandatory** (absent class defaults to skill)

---

## 4. Acceptance Criteria

1. `ConstructSpec` supports an optional `construct_class` field; absent defaults to `"skill"`
2. `plan_theatre_checks()` generates 4 theatre-specific check types from a construct.json
3. `merge_theatre_checks()` combines theatre checks with base checks, preserving sort/dedup
4. `contract_service.create_contract()` accepts optional `construct_json` and routes to theatre check planner when `construct_class == "theatre"`
5. Theatre anchor mapping rules added (settlement, oracle, calibration, USGS/EMSC/SWPC keywords)
6. Theatre precise domains registered, `normalize()` classifies them as precise
7. TREMOR fixture produces SETTLEMENT_ACCURACY + ORACLE_CONSISTENCY + CALIBRATION_VALIDITY checks
8. All existing 037/037b/037c tests pass unchanged (zero regression)
9. >= 28 new tests

---

## 5. Test Plan

| Area | Tests | Coverage |
|---|---|---|
| Construct class parsing | 4 | theatre, skill, absent/default, unknown |
| Theatre check planner | 6 | 4 check types, sort order, determinism |
| Theatre check merging | 4 | merge with base, dedup, sort, no theatre without class |
| Theatre anchor mapping | 4 | settlement → LIVE_EXTERNAL, brier → DETERMINISTIC, USGS keyword, unrecognized |
| Theatre domain registration | 4 | precise classification, vague fallback, normalize integration |
| TREMOR fixture | 4 | all 4 check types from TREMOR construct.json |
| CORONA fixture | 2 | same pattern, different domain claims |
| Regression | 4 | skill constructs unchanged, security checks still work, hash determinism |
| **Total** | **~32** | |

---

## 6. Dependency Chain

```
037  (contract substrate)
 ├── 037b (multi-evaluator orchestration)
 ├── 037c (domain packs + security checks)
 │    └── 037c-fix (import registration + API corpus wiring)
 └── 037d (theatre construct verification) ← THIS CYCLE
      └── 038 (cross-theatre paradox detection)
```

---

## 7. Why This Matters

Theatre constructs are the first Echelon construct class where every claim can be verified deterministically against public oracles. If 037d ships cleanly, Echelon can issue a **higher-credibility certificate class** for theatre operators than for any skill-based construct — because the evaluation chain is fully recomputable.

That positions theatre-construct certificates as the trust anchor for the broader network, and sets up Cycle 038's cross-theatre paradox detection with verified theatre records to compare.
