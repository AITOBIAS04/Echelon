# Composed Oracle Spec v2 — Registry Field Addendum

**Date:** 1 March 2026
**Applies to:** Echelon_OSINT_Composed_Oracle_Spec_v2.md
**Triggered by:** Intelligence Database Expansion v1.0.0 (same date)
**Status:** Normative addendum — these fields are referenced by the Composed Oracle pipeline and must be honoured by collectors, the corroboration stage, and the scorer.

---

## Context

The Composed Oracle Spec v2 defines the three-stage pipeline (Collection, Corroboration, Scoring) and references per-source registry fields throughout. The Intelligence Database Expansion v1.0.0 added 9 new fields to the registry schema. Three of those fields directly affect pipeline behaviour and must be documented here so that Loa and the pipeline codebase treat them as normative, not advisory.

---

## New Fields Affecting Pipeline Behaviour

### 1. settlement_requires_corroboration

**Type:** Boolean (default: false)
**Registry location:** Per-source field
**Pipeline stage affected:** Corroboration (Stage 2)

When `true`, this source cannot serve as the sole settlement anchor for a Theatre. It must be corroborated by at least one independent source (per the existing `corroboration_minimum_met` criterion) even if the Theatre template would otherwise accept a single source.

**Rationale:** Some sources are broadly useful but epistemically weak as sole settlement anchors. Wikidata is the canonical example — community-edited, revision_policy is `latest_only`, and edits can be reverted. Valuable for governance Theatres (election results, heads of state) but must be cross-referenced.

**Pipeline enforcement:**
- The corroboration stage checks this flag before declaring `corroboration_minimum_met`.
- If `settlement_requires_corroboration=true` for the primary source AND no independent corroborating source has returned an `EvidenceBundle` with `GapKind.SIGNAL_ABSENCE` or positive match, the criterion FAILS regardless of the Theatre's configured corroboration minimum.
- This flag is checked AFTER the `independence_upstream_dedupe_runner` (AC-2) to prevent Sybil sources from satisfying the corroboration requirement.

**Example:**
```json
{
  "source_id": "wikidata_sparql",
  "settlement_eligible": true,
  "settlement_requires_corroboration": true,
  "independence_notes": "Community-edited. Valuable for structured governance facts but revisions can be reverted. Must be corroborated by official_gov or judicial_record source."
}
```

---

### 2. settlement_latest_only_override

**Type:** Boolean (default: false)
**Registry location:** Per-source field
**Pipeline stage affected:** Scoring (Stage 3) — settlement eligibility gate

The registry enforces a guardrail: sources with `revision_policy: "latest_only"` are automatically set to `settlement_eligible: false` because mutable data cannot be trusted for deterministic settlement. This override allows exceptions where `latest_only` is acceptable with justification.

**When to use:** Only when the source's mutability is bounded and the evidence bundle captures the state at query time with a valid receipt. The `independence_notes` field must document why the override is justified.

**Pipeline enforcement:**
- The scorer's settlement eligibility gate checks `revision_policy`.
- If `revision_policy == "latest_only"` AND `settlement_eligible == true` AND `settlement_latest_only_override == false`: FAIL (validator rejects this configuration).
- If `revision_policy == "latest_only"` AND `settlement_eligible == true` AND `settlement_latest_only_override == true`: PASS with a confidence penalty of 0.80x (per AC-4 confidence capping).
- The validator (strict mode) logs a warning for any source using this override.

**Example:**
```json
{
  "source_id": "example_mutable_api",
  "revision_policy": "latest_only",
  "settlement_eligible": true,
  "settlement_latest_only_override": true,
  "independence_notes": "API returns current state only but HTTP transcript receipt captures the exact response at query time. Acceptable for settlement when corroborated."
}
```

---

### 3. independence_notes

**Type:** String or null
**Registry location:** Per-source field
**Pipeline stage affected:** Corroboration (Stage 2) — audit trail only

Free-text explanation documenting why a source's independence classification is what it is. This field is consumed by auditors and the evidence bundle's audit trail, not by the pipeline logic itself.

**Primary use cases:**
- Documenting shared upstream lineage when `independence_upstream_id` is set (e.g., CourtListener and PACER sharing the PACER backend but CourtListener providing independent indexing via RECAP).
- Justifying `settlement_latest_only_override` decisions.
- Explaining why `settlement_requires_corroboration` is set for a particular source.

**Pipeline enforcement:**
- No direct pipeline enforcement. This field is informational.
- The evidence bundle includes `independence_notes` in the audit trail section for any source that contributed to settlement.
- The validator warns (non-blocking) if `independence_upstream_id` is set but `independence_notes` is null — the combination suggests the upstream relationship is known but undocumented.

**Example:**
```json
{
  "source_id": "courtlistener_api",
  "independence_upstream_id": "pacer_uscourts",
  "independence_notes": "Shares PACER as upstream data source but provides independent full-text indexing via RECAP project. CourtListener adds value through de-duplication, OCR, and citation extraction not available in raw PACER. Counts as same upstream for corroboration purposes but is the preferred collector due to richer API."
}
```

---

## Other New Fields (Pipeline-Adjacent)

The following 6 fields from the Intelligence Database Expansion v1.0.0 do not directly affect the three-stage pipeline but are referenced by the registry validator and consumption surface routing:

| Field | Type | Pipeline impact |
|-------|------|----------------|
| `consumption_surfaces` | Array of objects | Routing only. Determines which surfaces receive this source's data. Does not affect collection, corroboration, or scoring logic. |
| `access_tier` | Enum (tier_a/tier_b/tier_c/paid) | Build priority only. Does not affect pipeline behaviour at runtime. |
| `api_endpoint` | String or null | Collector configuration. Overrides `api_url` for the actual callable endpoint. |
| `collector_status` | Enum (active/planned/enumerated) | Build status only. Pipeline skips sources with `collector_status: "enumerated"` (no collector exists). |
| `rate_limit_policy` | String or null | Collector configuration. Informs retry/backoff strategy but does not affect corroboration or scoring. |
| `dashboard_permitted` | Boolean | Consumption surface routing. Does not affect settlement pipeline. |

---

## Cycle-004 Cross-References

The 6 Architectural Concerns resolved in Cycle-004 directly interact with these new fields:

- **AC-1 (GapKind):** `settlement_requires_corroboration` interacts with signal absence vs intelligence gap. A corroborating source returning `GapKind.INTELLIGENCE_GAP` does NOT satisfy the corroboration requirement — only `EvidenceBundle` (including signal absence with valid receipt) counts.
- **AC-2 (Upstream Dedup):** The `independence_upstream_dedupe_runner` must run BEFORE checking `settlement_requires_corroboration`. Otherwise, two Sybil sources could appear to corroborate each other.
- **AC-3 (Receipt Enforcement):** Sources using `settlement_latest_only_override` are under heightened receipt scrutiny — the receipt must capture the mutable state at query time.
- **AC-4 (Confidence Capping):** The 0.80x penalty for `revision_policy: "latest_only"` applies regardless of `settlement_latest_only_override`. The override allows settlement eligibility, not confidence exemption.
