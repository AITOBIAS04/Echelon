# Implementation Report — Sprint 33 (local sprint-1)

**Cycle:** cycle-014c (Investigation Toolset Implementation)
**Sprint:** Evidence Envelope + Claim Graph (Core Data Layer)
**Date:** 2026-03-05

## Summary

All 5 tasks implemented. 17 new tests, all passing. Zero regressions.

## Task Completion

### Task 1.1: Package Init + ProvenanceClass + EvidenceItem Model ✓

**Files created:**
- `backend/investigation/__init__.py` — package docstring
- `backend/investigation/tests/__init__.py` — empty init
- `backend/investigation/models.py` — ProvenanceClass enum (5 values) + EvidenceItem frozen Pydantic model

**Details:**
- ProvenanceClass: PUBLIC_PRIMARY, PUBLIC_SECONDARY, PRIVATE_LEAK, ANALYST_DERIVED, THIRD_PARTY_TOOL_OUTPUT
- EvidenceItem: frozen=True, all fields typed, references defaults to empty list

### Task 1.2: Evidence Envelope Service ✓

**File created:** `backend/investigation/evidence_envelope.py`

**Details:**
- `RedactionEvent` frozen Pydantic model with sequential IDs (R001, R002, ...)
- `EvidenceEnvelope` class:
  - `submit()`: append-only, sequential IDs (E001, E002, ...), SHA-256 content hash
  - `redact()`: logs RedactionEvent, does NOT alter envelope hash
  - `get_item()`: retrieve by evidence_id
  - `get_manifest()`: full JSON-serialisable manifest with items, redactions, provenance summary
  - `compute_envelope_hash()`: SHA-256 of pipe-separated content_hashes in submission order
  - Properties: `items`, `redactions`, `provenance_summary`
- No `delete()` method — immutability enforced by design
- Redacted items remain in hash computation

### Task 1.3: Evidence Envelope Tests ✓

**File created:** `backend/investigation/tests/test_evidence_envelope.py`

8 tests:
1. `test_submit_and_retrieve` ✓
2. `test_append_only` ✓
3. `test_provenance_summary` ✓
4. `test_envelope_hash_deterministic` ✓
5. `test_envelope_hash_changes_on_new_item` ✓
6. `test_redaction_preserves_hash` ✓
7. `test_redaction_logged` ✓
8. `test_manifest_format` ✓

### Task 1.4: Claim Graph Model + Merkle Hashing ✓

**File created:** `backend/investigation/claim_graph.py`

**Details:**
- `ClaimType` enum: FACT, CAUSAL, ATTRIBUTION
- `ClaimStatus` enum: SUPPORTED, PARTIALLY_SUPPORTED, UNCONFIRMED, CONTRADICTED
- `CorroborationCheck` frozen Pydantic model (forward declaration for sprint 2)
- `ClaimNode` frozen Pydantic model: claim_id, claim_text, claim_type, evidence_refs, osint_checks, counter_signals, status, confidence, independence_groups
- `ClaimGraph` class:
  - `add_claim()`: sequential IDs (C001, C002, ...)
  - `update_claim_status()`: replaces frozen node with new instance
  - `link_counter_signal()`: appends counter-signal ID to claim
  - `compute_root_hash()`: Merkle root per §3.7 — canonical_json → SHA-256 leaf → pairwise merge, odd leaf duplicated
  - `get_status_summary()`: {status_value: count}
- Uses `canonical_json()` from `theatre.engine.canonical_json`
- Uses `model_dump(mode="json")` for datetime serialisation compatibility

### Task 1.5: Claim Graph Tests ✓

**File created:** `backend/investigation/tests/test_claim_graph.py`

9 tests:
1. `test_add_claim` ✓
2. `test_status_update` ✓
3. `test_merkle_root_deterministic` ✓
4. `test_merkle_root_single_claim` ✓ (exact hash verification)
5. `test_merkle_root_two_claims` ✓ (exact hash verification)
6. `test_merkle_root_odd_count` ✓ (exact hash verification)
7. `test_merkle_root_uses_canonical_json` ✓
8. `test_status_summary` ✓
9. `test_link_counter_signal` ✓

## Test Results

```
17 passed in 0.13s
```

Broader regression check (445 relevant tests): 445 passed, 11 skipped, 0 failures.

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `backend/investigation/__init__.py` | 1 | Package init |
| `backend/investigation/models.py` | 30 | ProvenanceClass + EvidenceItem |
| `backend/investigation/evidence_envelope.py` | 119 | EvidenceEnvelope + RedactionEvent |
| `backend/investigation/claim_graph.py` | 150 | ClaimGraph + ClaimNode + Merkle root |
| `backend/investigation/tests/__init__.py` | 0 | Test package init |
| `backend/investigation/tests/test_evidence_envelope.py` | 109 | 8 tests |
| `backend/investigation/tests/test_claim_graph.py` | 140 | 9 tests |
