# PRD — Cycle-014: Bounded Inquiry Markets

**Cycle:** cycle-014
**Date:** 4 March 2026
**Predecessor:** cycle-013 (Agent Runtime) + cycle-013-remediation (MCP Auth + Baseline Drift)
**Sprints:** 2
**Baseline:** 741 passed, 13 pre-existing failures

---

## 1. Problem Statement

After 13 cycles, Echelon has autonomous agents trading in LMSR markets settled by OSINT evidence. But every market is treated identically — the system doesn't know *what kind of question* it's asking.

The System Bible v13 §X defines five inquiry classes (Counterfactual, Investigative, Inspection, Survey, Scrutiny), each with distinct evidence accumulation rules, resolution triggers, and agent behaviour profiles. Today:

1. **No canonical Python enum.** Frontend uses `COUNTERFACTUAL | INVESTIGATIVE | INSPECTION | SURVEY | SCRUTINY` (`echelon-inquiry-console/src/types/signal.ts`). Certificate pipeline uses `INSPECTION | INVESTIGATION | AUDIT` (`osint/osint_pipeline/models/certificate.py:39`). Backend theatre schema has no inquiry class at all.

2. **Enum mismatch.** `INVESTIGATIVE` (System Bible / frontend) vs `INVESTIGATION` (certificate pipeline). `AUDIT` (certificate pipeline) vs `SCRUTINY` (System Bible). `SURVEY` absent from backend entirely.

3. **Runtime is template-family driven, not inquiry-class driven.** Resolution engine (`backend/market/resolution.py`) does generic deterministic settlement. Evidence collector (`backend/services/theatre_evidence.py`) treats all markets identically. Agent T0 context (`backend/agents/context_compiler.py`) has no inquiry_class field.

4. **Template library is thin.** One concrete inquiry template exists (`inspection_corporate_status_v1.json`). Four inquiry classes have no templates.

## 2. Objective

Make bounded inquiries a first-class runtime concept. After Cycle-014:
- Every market knows what kind of question it's asking
- The inquiry class influences resolution triggers, evidence accumulation, and agent behaviour
- The entire stack (schema, database, API, runtime, templates, certificates) agrees on a single five-value taxonomy
- E2E tests prove the wiring for each inquiry class

## 3. Success Criteria

1. Single `InquiryClass` enum with exactly 5 values is the sole source of truth
2. Alias map resolves `INVESTIGATION` → `INVESTIGATIVE` and `AUDIT` → `SCRUTINY`
3. Theatre schema (`backend/schemas/theatre.py`), database (`backend/database/models.py`), API (`backend/api/theatre_routes.py`), and certificate (`osint/osint_pipeline/models/certificate.py`) all carry `inquiry_class`
4. Existing theatres default to `COUNTERFACTUAL`
5. Agent T0 context includes `inquiry_class`
6. Resolution engine uses inquiry-class-specific triggers
7. Agent T1 behaviour adapts per inquiry class (§X.4 domain adaptation matrix)
8. At least one template per inquiry class exists
9. E2E test passes for each of the five inquiry classes
10. Existing 012 and 013 tests pass unchanged
11. Zero new test failures vs baseline

## 4. Codebase Grounding

### 4.1 Files That Need Creation

| File | Purpose |
|------|---------|
| `backend/schemas/inquiry.py` | Canonical `InquiryClass` StrEnum + alias map + `resolve_inquiry_class()` |
| `backend/agents/inquiry_behaviour.py` | `InquiryBehaviourAdapter` — archetype decision profile adaptation per inquiry class |
| `backend/services/evidence_service.py` | Evidence accumulation rules per inquiry class (extends existing `theatre_evidence.py`) |
| `backend/tests/test_bounded_inquiry_e2e.py` | 5 E2E tests, one per inquiry class |
| `osint/osint_pipeline/theatre/templates/counterfactual_geopolitical_v1.json` | Counterfactual template |
| `osint/osint_pipeline/theatre/templates/investigative_corporate_v1.json` | Investigative template |
| `osint/osint_pipeline/theatre/templates/survey_asset_valuation_v1.json` | Survey template |
| `osint/osint_pipeline/theatre/templates/scrutiny_tvl_audit_v1.json` | Scrutiny template |

### 4.2 Files That Need Modification

| File | Change |
|------|--------|
| `backend/schemas/theatre.py` | Add `inquiry_class: InquiryClass` to TheatreCreate, TheatreResponse, TheatreCertificate |
| `backend/database/models.py` | Add `inquiry_class` column to Theatre and TheatreTemplate models |
| `backend/api/theatre_routes.py` | Require `inquiry_class` on create, include in response, validate via alias resolution |
| `backend/market/resolution.py` | Inquiry-class-aware resolution triggers |
| `backend/agents/context_compiler.py` | Add `inquiry_class` to T0Context |
| `backend/agents/rules_engine.py` | T1 rules adapt per inquiry class |
| `backend/services/theatre_evidence.py` | Evidence accumulation rules per inquiry class |
| `osint/osint_pipeline/models/certificate.py` | Replace stale enum with canonical `InquiryClass` import |
| `osint/osint_pipeline/engine/certificate_generator.py` | Include `inquiry_class` + `resolution_trigger_reason` in certificate |
| `osint/osint_pipeline/theatre/templates/inspection_corporate_status_v1.json` | Already has `inquiry_class` — no change needed |

### 4.3 Current State Summary

| Layer | Status | Location |
|-------|--------|----------|
| Frontend InquiryClass | Complete (5 values) | `echelon-inquiry-console/src/types/signal.ts` |
| Backend InquiryClass | **MISSING** | Needs `backend/schemas/inquiry.py` |
| Theatre DB column | **MISSING** | `backend/database/models.py` Theatre model |
| Theatre API | **MISSING** | `backend/api/theatre_routes.py` |
| Certificate model | Stale enum | `osint/osint_pipeline/models/certificate.py:39` |
| Certificate generator | Stale docstring | `osint/osint_pipeline/engine/certificate_generator.py:44` |
| Agent T0 context | **MISSING** | `backend/agents/context_compiler.py` |
| Agent T1 rules | No inquiry adaptation | `backend/agents/rules_engine.py` |
| Resolution engine | Generic settlement | `backend/market/resolution.py` |
| Evidence collector | No inquiry awareness | `backend/services/theatre_evidence.py` |
| Templates | 1 of 5 | Only `inspection_corporate_status_v1.json` |

## 5. Inquiry Class Taxonomy (System Bible v13 §X)

| Inquiry Class | Evidence Accumulation | Resolution Trigger | Agent Adaptation (§X.4) |
|---|---|---|---|
| COUNTERFACTUAL | Simulation divergence or OSINT (Mode 0/1) | Simulation terminal state or evidence threshold | Shark=momentum, Spy=OSINT intel, Diplomat=treaty |
| INVESTIGATIVE | OSINT discovery over real-world sources | Evidence threshold met or time window closes | Shark=evidence front-running, Spy=primary discovery, Diplomat=source corroboration |
| INSPECTION | Artefact under inspection (single-source OK) | All committed criteria evaluated | Shark=rapid certification, Spy=audit trail, Diplomat=compliance mediation |
| SURVEY | Structured opinion (market's own trading activity) | Participation threshold or time window closes | Shark=sentiment tracking, Spy=opinion mining, Diplomat=consensus building |
| SCRUTINY | Adversarial audit against committed evidence | Claim verified or falsified | Shark=short-selling unverified, Spy=deep verification, Diplomat=dispute resolution |

## 6. Constraints

- **No new execution paths.** Uses existing `replay` and `market` paths. Inquiry class is orthogonal.
- **No multi-tier market hierarchy.** Operates at Macro only (§X.2 tiers deferred).
- **No investigative tooling.** §X.5 OSINT agent tools deferred.
- **No on-chain commitment.** Database-only commitment hashes.
- **Templates are minimal fixtures.** Proof-of-wiring, not production market designs.
- **OSINT registry is WM-only.** Three WorldMonitor sources at runtime (D2 from remediation). `corroboration_minimum` requiring independent upstreams cannot be satisfied until Cycle-015.

## 7. Sprint Structure

### Sprint 1: Canonical Taxonomy + Schema Alignment
- Canonical `InquiryClass` StrEnum + alias map
- Schema alignment across theatre/database/API/certificate/agent T0
- Existing template migration (`inspection_corporate_status_v1.json`)
- Stale enum cleanup (`INVESTIGATION` → `INVESTIGATIVE`, `AUDIT` → `SCRUTINY`)
- Unit tests for enum, schema, alias resolution

### Sprint 2: Inquiry-Aware Runtime + Templates + E2E
- Inquiry-class-aware resolution triggers
- Evidence accumulation rules per inquiry class
- Agent T1 behaviour adaptation (§X.4 domain adaptation matrix)
- 4 new templates (one per missing inquiry class)
- Inquiry-aware certificate generation
- 5 E2E tests (one per inquiry class)
- Backward compatibility validation (012 + 013 tests pass)

## 8. Regression Target

**Baseline:** `python3 -m pytest -q` — 741 passed, 13 pre-existing failures
**Scoped:** `python3 -m pytest -q backend/ osint/ theatre/ mcp/` — 710 passed, 13 pre-existing
**Gate rule:** Zero new failures. Pre-existing 13 may persist but must be listed and unchanged.

## 9. What 014 Unlocks

- **015 (WM Live + Non-WM Collector):** Real evidence flowing into inquiry-class-aware markets
- **016 (Results Surface):** Markets displayed/filtered by inquiry class
- **RLMF diversity:** Agent traces vary by inquiry class → richer training data across 5 market types
