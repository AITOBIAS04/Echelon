# Sprint 3 (Global 45) — Implementation Report

**Cycle:** cycle-017 (Policy Surface)
**Sprint:** sprint-3 (Registry Schema Expansion)
**Date:** 2026-03-06

## Task 3.1: Source Registry Model + Seed Data

**Status:** COMPLETE

**Files modified:**
- `backend/osint/sources.json` — added policy fields to all 4 existing sources + 2 new seed sources

**Changes:**
- Added `query_determinism`, `receipt_body_required`, `requires_legal_review` to all existing sources (worldmonitor_cii, worldmonitor_finance, worldmonitor_maritime, companies_house_api)
- Added `polymarket_api` source: `pure_id_lookup`, no receipt, no legal review
- Added `private_leak_source` source: `bulk_export`, receipt required, legal review required
- Companies House updated: `search_endpoint`, receipt required, no legal review
- All WorldMonitor sources: `pure_id_lookup`, no receipt, no legal review

**Test:** `test_registry_policy_fields` — verifies all 3 seed archetypes + validation passes

## Task 3.2: Evidence Submission — Receipt Enforcement

**Status:** COMPLETE

**Files modified:**
- `backend/schemas/investigation_schemas.py:27-35` — added `source_id` and `receipt_body` fields to `EvidenceSubmitRequest`
- `backend/api/investigation_routes.py:69-83` — added `_get_registry()` lazy singleton for `RegistryLoader`
- `backend/api/investigation_routes.py:296-304` — receipt enforcement check before evidence submission

**Changes:**
- `EvidenceSubmitRequest` now accepts optional `source_id` (str, default "") and `receipt_body` (str, default "")
- When `source_id` is provided and the source has `receipt_body_required=True`, submission without `receipt_body` returns HTTP 422 with clear error message
- Non-required sources and submissions without `source_id` are unaffected (backwards compatible)
- Registry loaded lazily to avoid import-time file I/O

**Tests:**
- `test_evidence_submit_without_receipt_returns_422` — Companies House source, no receipt -> 422
- `test_evidence_submit_with_receipt_succeeds` — Companies House source, receipt provided -> 201

## Task 3.3: Legal Review Flag — Investigation Detail API

**Status:** COMPLETE

**Files modified:**
- `backend/schemas/investigation_schemas.py:188` — added `has_legal_review_requirement: bool = False` to `InvestigationDetailResponse`
- `backend/api/investigation_routes.py:240-241` — track `source_ids` set on investigation entry
- `backend/api/investigation_routes.py:312-315` — track source_id on evidence submission
- `backend/api/investigation_routes.py:262-270` — compute `has_legal_review_requirement` from registry lookup

**Changes:**
- Investigation entries now track a `source_ids` set populated on evidence submission
- `get_investigation` endpoint computes `has_legal_review_requirement` by checking if any tracked source has `requires_legal_review=True` in the registry
- Defaults to `false` when no legal-review sources present

**Test:** `test_investigation_detail_legal_review_flag` — verifies default false, then true after private_leak evidence

## Task 3.4: Frontend — Registry Badges (Behind Flag)

**Status:** COMPLETE

**Files modified:**
- `frontend/src/types/investigation.ts:228-243` — added `has_legal_review_requirement?: boolean` to `InvestigationDetail`, `source_id?: string` and `query_determinism?: string` to `EvidenceItem`
- `frontend/src/pages/InvestigationPage.tsx:10-11` — imported `ShieldAlert` icon and `isEnabled`
- `frontend/src/pages/InvestigationPage.tsx:136-143` — legal review warning badge in OverviewTab, gated behind `CYCLE_017_REGISTRY_SCHEMA`
- `frontend/src/components/investigation/EvidenceEnvelopePanel.tsx:8` — imported `isEnabled`
- `frontend/src/components/investigation/EvidenceEnvelopePanel.tsx:23-42` — added `QueryDeterminismBadge` component with color coding (green=pure_id_lookup, amber=search_endpoint, red=bulk_export)
- `frontend/src/components/investigation/EvidenceEnvelopePanel.tsx:47-49` — query determinism badge in `EvidenceItemCard`, gated behind `CYCLE_017_REGISTRY_SCHEMA`

**No tests** — visual integration behind flag, consistent with Sprint 1/2 precedent.

## Test Summary

| Test | Status |
|------|--------|
| `test_registry_policy_fields` | PASS |
| `test_evidence_submit_without_receipt_returns_422` | PASS |
| `test_evidence_submit_with_receipt_succeeds` | PASS |
| `test_investigation_detail_legal_review_flag` | PASS |

**4/4 passing, 0 regressions (Sprint 2: 6/6 still passing, 24/24 cycle-017 total)**
