# PRD — Cycle-014c: Investigation Toolset Implementation

**Cycle:** cycle-014c
**Date:** 5 March 2026
**Predecessor:** cycle-014 (Bounded Inquiry Markets), cycle-013 (Agent Runtime), cycle-010a (LMSR)
**Sprints:** 3
**Design input:** `Echelon_Investigation_Toolset_Design_Note_v1.md` (v1.3.0)
**Baseline:** ≥942 passed (full suite), 15 skipped, 13 pre-existing collection errors

---

## 1. Problem Statement

Cycle-014 built the bounded inquiry lifecycle with five inquiry classes (Counterfactual, Investigative, Inspection, Survey, Scrutiny), but the INVESTIGATIVE class has no dedicated tooling beyond what other classes share. An investigation-class inquiry cannot:

- Structure evidence with provenance tracking and immutability guarantees
- Build a Merkle-hashed claim graph linking evidence to conclusions
- Track investigation-level counter-signals (separate from pipeline-level OSINT counter-signals)
- Monitor commitment drift in the investigation target
- Scan for anomalies across OSINT domain filters
- Resolve entities across multiple sources with provenance per source
- Enforce the hard corroboration invariant: no claim SUPPORTED without ≥2 independent upstream groups
- Produce an investigation-specific certificate with 30+ fields, routing logic, and anchoring metadata

Without this toolset, INVESTIGATIVE class inquiries are functionally identical to other inquiry classes — they have distinct resolution triggers and agent behaviour profiles, but no investigation-specific data structures or analysis capabilities.

> Sources: echelon_cycle_014c.md:11-16, echelon_platform_roadmap.md:160-167

## 2. Objective

Build the runtime models, services, and hashing infrastructure for the 8-tool investigation toolset. All tools use mock/stub backends — this cycle does NOT depend on live collectors beyond what cycle-015 already provides (WM + Companies House).

### 8 Investigation Tools

| # | Tool | Purpose |
|---|------|---------|
| 1 | Evidence Envelope | Append-only evidence container with provenance classes and Merkle-based envelope hash |
| 2 | Claim Graph | FACT/CAUSAL/ATTRIBUTION claims linked to evidence, Merkle root hashing |
| 3 | Investigation Counter-Signal Feed | 11-class taxonomy separate from pipeline counter-signals |
| 4 | Commitment Monitor | Drift detection with impact assessment and Paradox Engine integration point |
| 5 | Signal Scanner | DeltaBrief output, domain filters mapped to OSINT registry source groups |
| 6 | Entity Resolver | Multi-source entity profiles with provenance metadata per source |
| 7 | Investigation Corroboration Checker | Claim-centric independence enforcement (≥2 upstream groups for SUPPORTED) |
| 8 | Investigation Certificate | 30+ field extension of CalibrationCertificate with routing logic |

### Supporting Infrastructure

- **Stop condition contract** — `stop_condition` + `stop_config` committed immutably at theatre creation, wired through commitment hashing and resolution engine
- **Deterministic artefact writers** — canonical JSON output files with reproducible hashing
- **Integration orchestrator** — `InvestigationToolset` class wiring all 8 tools together

## 3. Success Criteria

### SC-1: Evidence Envelope
1. Append-only submission with sequential IDs (`E001`, `E002`, ...)
2. SHA-256 content hashing per item
3. 5 provenance classes: PUBLIC_PRIMARY, PUBLIC_SECONDARY, PRIVATE_LEAK, ANALYST_DERIVED, THIRD_PARTY_TOOL_OUTPUT
4. Redaction events logged but do NOT alter envelope hash
5. Envelope hash is deterministic for same content in same order

### SC-2: Claim Graph
1. 3 claim types: FACT, CAUSAL, ATTRIBUTION
2. 4 claim statuses: SUPPORTED, PARTIALLY_SUPPORTED, UNCONFIRMED, CONTRADICTED
3. Evidence linkage via evidence_refs to Evidence Envelope item IDs
4. Merkle root hashing per design note §3.7: canonical JSON, SHA-256 pairwise, odd leaf duplicated
5. Uses existing `canonical_json()` from `theatre.engine.canonical_json`

### SC-3: Investigation Counter-Signals
1. 11 investigation-specific classes (separate enum from pipeline counter-signals)
2. Classes 10 (MARKET_DIVERGENCE) and 11 (WITNESS_SOURCE_RECANTATION) only count toward `checked` when explicitly logged
3. Summary includes checked/gaps/material_contradictions counts
4. Detail output matches certificate schema requirements

### SC-4: Commitment Monitor
1. 5 drift types tracked with impact assessment (MATERIAL/NON_MATERIAL)
2. `has_material_drift()` triggers `routing_hint: REVIEW_REQUIRED` in certificate

### SC-5: Signal Scanner
1. 9 domain filters mapped to OSINT registry source groups
2. DeltaBrief output with content hash
3. Access-tier policy enforced: only tier A by default, B/C skipped with reason
4. Scanner manifest includes requested/resolved/skipped groups

### SC-6: Entity Resolver
1. EntityProfile with provenance metadata per source
2. Profile hash deterministic via canonical JSON
3. Companies House + London Gazette backends stubbed

### SC-7: Corroboration Checker
1. SUPPORTED requires ≥2 distinct `independence_upstream_id` groups (hard invariant, no override)
2. PRIVATE_LEAK-only evidence cannot achieve SUPPORTED status
3. Single upstream group yields PARTIALLY_SUPPORTED at most

### SC-8: Investigation Certificate
1. All 30+ fields from design note §6 present
2. Routing logic: material drift, material counter-signal, single provenance class, anchoring pending → REVIEW_REQUIRED
3. Default routing: ALLOWED
4. Anchor state defaults to LOCAL_UNANCHORED

### SC-9: Stop Conditions
1. Three types: OUTCOME_RESOLUTION, EVIDENCE_THRESHOLD, SPONSOR_DEFINED
2. `stop_condition` and `stop_config` persisted on theatre at creation, included in commitment hash
3. Immutable post-COMMITTED — mutation attempt returns 400/422
4. Resolution engine reads committed values only (no runtime override)

### SC-10: Test Gate
1. ≥942 passed (current baseline)
2. Zero new test failures
3. 67+ new investigation toolset tests pass
4. Post-014c expected: ≥1009 passed

## 4. Codebase Grounding

### Existing Infrastructure (No Changes Needed)

| Component | Location | Relevance |
|-----------|----------|-----------|
| LMSR Market Engine | `backend/market/` | Investigation markets use existing engine |
| Bounded Inquiry Lifecycle | `backend/schemas/inquiry.py`, `backend/services/evidence_service.py` | INVESTIGATIVE class has distinct evidence rules and resolution triggers |
| Corroboration Engine | `backend/osint/engine/corroboration.py` | Independence-weighted dedup, distinct group counting |
| Pipeline Counter-Signals | `backend/osint/engine/counter_signal.py` | 11 pipeline-level classes (kept separate from investigation classes) |
| Evidence Models | `backend/osint/models/evidence.py` | EvidenceBundle, HTTPTranscriptReceipt, CollectionResult |
| Certificate Pipeline | `backend/services/certificate_pipeline.py` | CalibrationCertificate, CertificatePipeline.generate() |
| Theatre State Machine | `theatre/engine/state_machine.py` | DRAFT → COMMITTED → ACTIVE → SETTLING → RESOLVED → ARCHIVED |
| Resolution Engine | `backend/market/resolution.py` | ResolutionTrigger enum, check_resolution_ready() |
| Canonical JSON | `theatre/engine/canonical_json.py` | canonical_json() for deterministic serialisation |

### Files Modified (Shared Schema)

| File | Change |
|------|--------|
| `backend/schemas/theatre.py` | Add `stop_condition` and `stop_config` fields to theatre create/commit schemas |
| `backend/database/models.py` | Add `stop_condition` and `stop_config` columns to Theatre model |
| `backend/api/theatre_routes.py` | Add immutability enforcement for stop fields post-COMMITTED, include in commitment hash |
| New Alembic migration | Add stop_condition/stop_config columns |

### New Package

All new code lives in `backend/investigation/`:

```
backend/investigation/
├── __init__.py
├── models.py                    # ProvenanceClass, EvidenceItem
├── evidence_envelope.py         # EvidenceEnvelope, RedactionEvent
├── claim_graph.py               # ClaimGraph, ClaimNode, ClaimType, ClaimStatus
├── counter_signals.py           # InvestigationCounterSignalClass, InvestigationCounterSignalFeed
├── commitment_monitor.py        # CommitmentMonitor, DriftType, DriftEvent
├── signal_scanner.py            # SignalScanner, DomainFilter, DeltaBrief
├── entity_resolver.py           # EntityResolver, EntityProfile
├── corroboration_checker.py     # InvestigationCorroborationChecker, CorroborationCheck
├── certificate.py               # InvestigationCertificate, InvestigationCertificateBuilder
├── stop_conditions.py           # InvestigationStopConditionEvaluator, StopCondition
├── artifacts.py                 # Deterministic JSON artefact writers
├── toolset.py                   # InvestigationToolset orchestrator
└── tests/
    ├── __init__.py
    ├── test_evidence_envelope.py
    ├── test_claim_graph.py
    ├── test_counter_signals.py
    ├── test_commitment_monitor.py
    ├── test_signal_scanner.py
    ├── test_entity_resolver.py
    ├── test_corroboration_checker.py
    ├── test_certificate.py
    ├── test_stop_conditions.py
    ├── test_stop_condition_commitment.py
    ├── test_artifacts.py
    └── test_toolset_e2e.py
```

## 5. Sprint Breakdown

### Sprint 1: Evidence Envelope + Claim Graph (Core Data Layer)

The two foundational models — everything else depends on them.

| Task | Description | Tests |
|------|-------------|-------|
| 1.1 | ProvenanceClass enum + EvidenceItem model | — |
| 1.2 | EvidenceEnvelope service (append-only, redaction, Merkle hash) | 8 |
| 1.3 | ClaimGraph model + Merkle root hashing (§3.7 spec) | 9 |

**Sprint 1 total:** 17 tests

### Sprint 2: Counter-Signals + Monitor + Scanner + Resolver + Checker

| Task | Description | Tests |
|------|-------------|-------|
| 2.1 | InvestigationCounterSignalClass enum + InvestigationCounterSignalFeed | 6 |
| 2.2 | CommitmentMonitor (drift detection, impact assessment) | 5 |
| 2.3 | SignalScanner (domain filters, DeltaBrief, access-tier policy) | 5 |
| 2.4 | EntityResolver (multi-source profiles, provenance per source) | 4 |
| 2.6 | InvestigationCorroborationChecker (independence enforcement) | 5 |

**Sprint 2 total:** 25 tests

### Sprint 3: Certificate Extension + Stop Conditions + E2E

| Task | Description | Tests |
|------|-------------|-------|
| 3.0 | Stop condition contract (schema + persistence + commitment hash) | 4 |
| 3.1 | InvestigationCertificate model (30+ fields) | — |
| 3.2 | InvestigationCertificateBuilder (routing logic) | 8 |
| 3.3 | Stop condition evaluator (3 types) | 5 |
| 3.4 | InvestigationToolset orchestrator | — |
| 3.5 | Deterministic artefact writers | 5 |
| 3.6 | E2E integration tests | 3 |

**Sprint 3 total:** 25 tests

**Grand total:** 67 new tests. Post-014c expected: ≥1009 passed.

## 6. Non-Functional Requirements

### NFR-1: Determinism
All hash computations (envelope hash, claim graph Merkle root, artefact hashes, commitment hash) must be deterministic given the same inputs. Use `canonical_json()` for JSON serialisation.

### NFR-2: Immutability
Evidence Envelope is append-only — no delete method. Redaction adds metadata without altering the hash chain. Stop conditions are immutable post-COMMITTED.

### NFR-3: Independence
Investigation counter-signals are a separate taxonomy from pipeline counter-signals. No shared state, no shared enum values. Both can coexist for the same theatre.

### NFR-4: Backward Compatibility
All changes to shared schema files (theatre.py, models.py, theatre_routes.py) must preserve existing behaviour for non-INVESTIGATIVE inquiry classes. Stop condition fields are optional with defaults.

## 7. Out of Scope

- Base contract deployment and on-chain anchoring enforcement (requires Solidity)
- Paid-tier (B/C) source activation in Signal Scanner without explicit access approval
- Full live-query coverage across all domain filters
- Domain filter UI (requires Cycle-016 Results Surface)
- RLMF export from investigation markets (existing RLMF export applies)
- Blockchain forensics, leaked data sourcing, KYC/AML (design note §7 exclusions)
- Entity Resolver jurisdictions beyond Companies House + London Gazette stubs

## 8. Dependencies

| Dependency | Status | Impact |
|------------|--------|--------|
| Cycle-014 (Bounded Inquiries) | ✓ Complete | INVESTIGATIVE class lifecycle, evidence rules |
| Cycle-013 (Agent Runtime) | ✓ Complete | Agent behaviour profiles for INVESTIGATIVE |
| Cycle-010a (LMSR) | ✓ Complete | Market engine for investigation markets |
| Cycle-015 (Live WM + CH) | ✓ Complete | Optional live adapters for scanner/resolver |
| `canonical_json()` | ✓ Exists | `theatre/engine/canonical_json.py` |
| `CorroborationEngine` | ✓ Exists | `backend/osint/engine/corroboration.py` |

## 9. What This Unlocks

- **Investigation-class inquiries become functional** — full evidence-receipting, claim-structuring, counter-signal-monitoring investigation platform
- **Certificate consumers get actionable artefacts** — claim graph root hash, provenance summary, independence groups, counter-signal detail, drift events
- **Foundation for Cycle-016 (Results Surface)** — toolset models define the data the UI will display
- **Foundation for live investigations** — Signal Scanner and Entity Resolver can use optional live adapters without interface changes
