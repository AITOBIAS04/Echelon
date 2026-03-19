# PRD — Cycle-038b: External Theatre Orchestration

**Cycle:** cycle-038b
**Date:** 19 March 2026
**Depends on:** Cycle-037d, Cycle-037e, Cycle-038a, Cycle-038
**Sprints:** 4 (0–3)
**Builder:** Loa (backend only)
**Priority:** Orchestrator composition first, extraction fidelity second
**Planning source:** TREMOR and CORONA validated end-to-end through 037d/037e/038a; remaining gaps are automated fixture extraction and orchestrator-supplied shared event/scope keys

---

## 1. Problem Statement

### 1.1 The Stack Works, But One Step Is Still Manual

TREMOR and CORONA now validate cleanly through:

- theatre contract compilation (037d)
- theatre check execution (037e)
- comparison bundle generation (038a)
- candidate generation for cross-theatre use (038a)

The remaining operational gap: the bridge between external repos and the paradox scanner still requires manual fixture construction and hand-supplied shared identity.

### 1.2 The Missing Layer Is Orchestration

This is not a construct-quality problem. It is an Echelon runtime problem.

We need the layer that:

- extracts replayable fixture inputs from external theatre construct metadata
- assigns shared real-world identity (event_keys, scope_keys) across multiple theatre bundles
- composes extraction → execution → bundle building → candidate generation into one service call
- produces candidates consumable by the existing Cycle 038 paradox scanner

### 1.3 What Already Exists

`theatre_fixture_loader.py` (037e) already builds `TheatreFixtureInput` from construct.json metadata via `_build_deterministic_fixture()`. It generates all-passing synthetic fixtures — every settlement matches, every oracle is consistent, every functional transform is valid.

That is sufficient for smoke testing. It is not sufficient for meaningful verification because:

- all-passing fixtures produce only SETTLED bundles (never DISPUTED)
- identical synthetic values across constructs don't exercise real cross-validation divergence
- no failure scenarios exist for critical check blocking

### 1.4 The Goal Of 038b

Make external theatre verification operational:

1. **Orchestrator**: Thread shared identity through a first-class service that composes the full path without test-only wiring
2. **Enriched extraction**: Generate realistic fixtures (including failure scenarios) from construct metadata
3. **Scanner compatibility**: Prove the orchestrated output is consumable by the existing 038 paradox scanner

---

## 2. Product Contracts

### 2.1 Orchestrator Service (Primary Deliverable)

Cycle 038b must add a composition service that takes external theatre inputs and produces ready-to-scan comparison candidates in one call.

The orchestrator:

- accepts one or more `ExternalTheatreInput` descriptors
- calls fixture extraction for each
- calls 037e check execution
- calls 038a bundle building with orchestrator-supplied `event_keys` / `scope_keys`
- calls candidate generation
- returns a fully prepared comparison package

This is the first place the system treats shared identity as a first-class runtime concern rather than a test-only detail.

### 2.2 Progressive Extraction Tiers

Extraction fidelity improves progressively without blocking the orchestrator:

| Tier | Source | Fidelity | This Cycle |
|------|--------|----------|------------|
| V1 | Enriched synthetic from construct.json | Realistic scenarios including failures, derived from template resolution types, settlement tiers, oracle cross-validation structure | Yes |
| V2 | RLMF certificate replay | Real runtime data from `getCertificates()` exports | Future |
| V3 | Standardized `fixtures.json` export | Repo-authored deterministic test fixtures in a defined schema | Future |

V1 enrichment over the existing fixture loader:

- Settlement fixtures include both passing and failing templates (not all-passing)
- Oracle fixtures use construct-specific divergence thresholds (not hardcoded 0.1/0.5)
- Multi-bucket templates get multi-class outcomes (not coerced to binary)
- Calibration fixtures derive Brier parameters from the construct's declared scoring type
- Failure scenarios enable DISPUTED settlement state derivation

### 2.3 Orchestrator-Supplied Shared Identity

The orchestrator surface must accept:

- `event_keys: list[str]` — shared real-world event identifiers
- `scope_keys: list[TheatreScopeKey]` — shared scope identifiers (region, entity, time_window)
- `certificate_id: Optional[str]` — optional verification certificate reference

This is the correct boundary. Bundle builders cannot infer shared real-world identity from construct-specific template IDs (038a P1 finding).

### 2.4 Builder Feedback Surface

The orchestrator should produce structured feedback for external builders:

- **Required metadata**: what must be present for compilation + execution to succeed
- **Optional enrichment**: what would strengthen future verification quality (explicit IDs, settlement tiers, verification_checks in construct.json)
- **Extraction result**: what was successfully extracted vs what fell back to defaults

### 2.5 Deterministic Replay-First Behavior

The orchestration layer remains replay-first:

- deterministic local fixtures
- stable repo-derived artifacts
- no required live network fetches for V1

---

## 3. What This Cycle Does NOT Do

- **Does NOT redesign Cycle 038 paradox classification.**
- **Does NOT require every external construct to expose a standardized runtime export on day one.**
- **Does NOT move fixture extraction into the construct repos themselves.**
- **Does NOT require live oracle polling in CI/tests.**
- **Does NOT replace the existing `theatre_fixture_loader.py`** — extends it with an enriched extraction path.

---

## 4. Acceptance Criteria

1. An orchestration service can build `TheatreFixtureInput` for TREMOR without manual fixture dicts
2. An orchestration service can build `TheatreFixtureInput` for CORONA without manual fixture dicts
3. Enriched fixtures include both passing and failing check scenarios (not all-passing)
4. Shared `event_keys` / `scope_keys` flow through a first-class orchestration surface
5. TREMOR and CORONA can be prepared into real `ComparisonCandidateSet` outputs through orchestration, not test-only wiring
6. The resulting candidates are consumable by the existing 038 scanner path
7. Builder feedback distinguishes required metadata from optional enrichment
8. ≥30 new tests pass

---

## 5. Test Plan

| Area | Tests | Coverage |
|---|---|---|
| Orchestration schemas | 5 | ExternalTheatreInput, PreparationRequest, PreparationResult shape validation |
| Enriched extraction — TREMOR | 4 | settlement (pass+fail), oracle (emsc, iris_dmc), calibration, functional |
| Enriched extraction — CORONA | 4 | settlement (pass+fail), oracle (nasa_donki, gfz_potsdam), calibration, functional |
| Extraction edge cases | 3 | missing construct.json, malformed metadata, empty templates |
| Orchestrator composition | 5 | single input, paired input, shared identity threading, no-keys fallback, error propagation |
| End-to-end preparation | 4 | TREMOR→candidates, CORONA→candidates, TREMOR+CORONA→cross-theatre candidates, DISPUTED bundle path |
| 038 scanner compatibility | 3 | candidates consumable by CrossTheatreParadoxScanner input shape |
| Builder feedback | 3 | required vs optional, extraction summary, TREMOR vs CORONA report |
| **Total** | **~31** | |

---

## 6. Why This Matters

Cycle 038b turns "ready now, with one manual step" into a smooth external-builder experience.

It gives Echelon a practical operating path for external theatres: ingest → execute → compare → scan.

That is the feedback loop El Captain needs — TREMOR and CORONA are structurally strong, no repo rewrites needed, and the orchestrator makes the runtime convenient.
