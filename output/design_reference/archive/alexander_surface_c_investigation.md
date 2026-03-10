# Alexander Build — Surface C: Investigation Persistence + Readiness + Certificates

**Date:** 8 March 2026
**Scope:** Frontend only. Wire investigation UI to backend parity with Cycles 017–021.
**Design references:** `echelon_investigations_v1.html`, `echelon_drift_submission_v1.html`, `echelon_readiness_certificate_v2.html`, `echelon_certificates_v1.html`, `echelon_empty_states_v1.html`

---

## What Already Exists (Frontend)

| Layer | File | Status |
|-------|------|--------|
| Types | `src/types/investigation.ts` | Complete — 45+ types covering evidence, claims, counter-signals, drift, entity, certificate, readiness. ~340 lines, no `any` types. |
| API client | `src/api/investigation.ts` | Complete — 15 functions covering all 16 backend endpoints (list, detail, evidence, claims, counter-signals, drift, readiness, certificate/build, anchor-batch) |
| Hooks | `src/hooks/useInvestigation.ts` | Complete — 8 query hooks + 6 mutation hooks. List refetches 15s, detail 10s, readiness 10s. |
| Realtime | `src/hooks/useRealtimeInvestigation.ts` | Complete — exports `useRealtimeInvalidation`; WebSocket event bridge for INVESTIGATION_STOP_CONDITION_MET, INVESTIGATION_CERTIFICATE_READY, INVESTIGATION_CERTIFICATE_ISSUED → query invalidation |
| Certificate gallery | `src/hooks/useCertificateGallery.ts` | Partial — currently maps theatre certificates only. The hook comment mentions verification certificates, but the implementation does not yet merge them. |
| Components | `src/components/investigation/` | 15 components — all use real API data via hooks, zero mock data |
| Pages | `InvestigationPage.tsx`, `CreateInvestigationPage.tsx`, `CertificatesPage.tsx` | Functional — sidebar list + tabbed detail, 5-step wizard, theatre-certificate gallery baseline |
| Routes | `src/router.tsx` | Complete — `/investigation`, `/investigation/create`, `/certificates` |

---

## What the Design Reference Specifies

### Investigations page (echelon_investigations_v1.html)

**Page state machine** (3 mutually exclusive states):
- `if (total === 0)` → EMPTY state (centered CTA, no attention strip, no KPIs)
- `else if (stalled > 0)` → ALERT state (orange strip, stalled badge on card)
- `else` → ACTIVE state (green strip, all progressing)

**Attention strip** (state-driven):
- Alert: orange, "Stalled — INV-XXXX has no new evidence in 72h"
- Active: green, "All Active — All N investigations progressing"
- Empty: hidden (no strip — the empty state card is the onboarding surface)

**4 KPI cards:**
1. Active — investigation count + stalled sub-count
2. Evidence Items — total + 24h delta
3. Claims Tracked — total + breakdown (supported · partial · unconfirmed · contradicted)
4. Stalled — count, highlighted orange if > 0

**Layout:** `1fr 300px` grid — card list + right rail.

**Investigation cards must show, where backed by list data:**
- ID (mono), status dot + label (Active/Stalled/Complete), "Open →" affordance
- Primary label from real data (prefer construct_id / inquiry_class; do not invent an inquiry question if the list response does not provide one)
- Meta row only for fields available in list data (theatre_id, created date)
- Stalled warning badge only if stalled state can be derived honestly
- Progress row: Evidence count, Claims count, Counter-Signals count, Drift Events count

**Claim status mini-bar:**
- 4-segment stacked bar: supported (green), partial (warning), unconfirmed (gray), contradicted (red)
- Inline micro-legend below bar: "N supported · N partial · N unconfirmed · N contradicted"

**Provenance dots:**
- Color per provenance class: public_primary (green), public_secondary (blue), private_leak (orange), analyst_derived (purple), third_party (gray)

**Right rail (3 panels):**
- Domain Filters: committed filters and enforcement note
- Evidence Feed: timestamped evidence/counter-signal/drift activity if the selected investigation data supports it
- Provenance Breakdown: colored dots + labels + counts where evidence manifest data is available

**Empty state:**
- Centered icon + "No investigations yet" + description text + "New Investigation" CTA button

### Investigation detail (echelon_investigations_v1.html — detail view)

**Layout:** `280px 1fr` grid — sidebar list + detail main area.

**Investigation sidebar list:**
- Each item: ID, status badge, optional CERT READY badge, primary label from real data (construct_id / inquiry_class unless a richer label is actually available), evidence/claims counts
- Selected item: purple left border + purple-50 background

**Tab bar:** Evidence | Claims | Counter-Signals | Drift | Readiness
- Readiness tab has a "new" tag badge

**Tab panels (placeholder structure in design reference — wire to real API):**
- Evidence: `GET /api/v1/investigations/{id}/evidence` → evidence envelope items
- Claims: `GET /api/v1/investigations/{id}/claims` → claim graph nodes (FACT/CAUSAL/ATTRIBUTION)
- Counter-Signals: `GET /api/v1/investigations/{id}/counter-signals` → contradicting evidence
- Drift: `GET /api/v1/investigations/{id}/drift` → commitment monitor events
- Readiness: certificate lifecycle panel (see below)

### Readiness & Certificate Lifecycle (echelon_readiness_certificate_v2.html)

**5 states (mutually exclusive):**

| State | Readiness Badge | Build CTA | Lifecycle Stepper | Routing |
|-------|----------------|-----------|-------------------|---------|
| 1. Not Ready | NOT_READY (gray) | Hidden | All pending | Hidden |
| 2. Ready, No Certificate | READY (green) | Visible — "Build Certificate" button | All pending, "Awaiting build" | Hidden |
| 3. Certificate Built (READY) | READY (green) | Hidden | READY reached, ANCHORED active (pulsing), ISSUED pending | Shown — ALLOWED or REVIEW_REQUIRED |
| 4. Issued (terminal) | READY (green) | Hidden | All reached, ANCHORED + ISSUED share same 00:00 UTC timestamp | Shown |
| 5. Review Required | READY (green) | Hidden | Same as state 3 | REVIEW_REQUIRED with amber banner: "Batch-anchor progression is not blocked by routing decision" |

**Stop Condition Readiness section:**
- Readiness badge: NOT_READY (gray panel) or READY (green)
- Meta rows: Stop Condition (humanized label), Detail (progress text), Last Evaluated (mono timestamp)

**Certificate Lifecycle stepper:**
- 3 steps: READY → ANCHORED → ISSUED
- Circle states: pending (gray), active (pulsing cyan/purple), reached (green with checkmark)
- Connector lines: gray (pending) or green (reached)
- Timestamp below each step (mono, tabular-nums)
- Batch note: "Queued for next 00:00 UTC batch-anchor cycle" (when READY, awaiting anchor)

**Build Certificate CTA:**
- Cyan/purple background area with shield icon
- Text: "Stop condition met. This investigation is ready for certificate issuance. The certificate will be queued for the next 00:00 UTC batch-anchor cycle."
- POST to `/api/v1/investigations/{id}/certificate/build`
- 409 if certificate already exists or stop_condition_status != READY

**Certificate Record (post-build):**
- Grid of key/value: Certificate ID, Status, Hash, Anchor Hash (after issuance)

**Review Required banner:**
- Amber background with alert icon
- "Routing decision: REVIEW_REQUIRED — coherence gate evaluation triggered. Batch-anchor progression is not blocked by routing decision in the current implementation."

**Implementation truth:**
- ANCHORED is a transient bookkeeping state, not durably observable. anchored_at and issued_at receive the same batch_timestamp.
- routing_decision is recorded at build time but does NOT gate batch-anchor progression.
- REVIEW_REQUIRED triggers coherence gate evaluation but does not block issuance.

### Drift Submission (echelon_drift_submission_v1.html)

**4 states:**
1. Empty — "No drift events detected" message
2. Populated — drift history with material + non-material events
3. Form ready — submission form expanded
4. Validation/error — form with error state

**Drift event row:**
- Drift type badge (5 types: entity_restructure, contract_amendment, market_rule_change, regulatory_status_change, jurisdiction_change)
- Impact badge: MATERIAL (red) or NON_MATERIAL (gray)
- Original → New value transition
- Evidence reference link
- Relative timestamp

**Material drift warning banner:**
- Red background: "Material drift detected — may trigger stop condition re-evaluation"

**Submission form:**
- Drift type dropdown (5 options)
- Original value + New value text fields
- Impact assessment radio: MATERIAL / NON_MATERIAL
- Evidence reference (optional)
- Submit button
- POST triggers stop-condition evaluation after persisting event

### Certificates page (echelon_certificates_v1.html)

**Product distinction:**
- Certificates = authenticated portfolio/history (THIS PAGE)
- Verify = public certificate checker (separate page, already wired)

**Character:** Trustworthy, archival, clean, official. Document ledger, not a trading page.

**Stats bar (7 items):**
- Total Certificates, Issued (scoped to period), Verified, Disputed, Under Review, Linked Theatres, Linked Investigations

**Filter tabs:** All | Verified | Disputed | Under Review — with counts

**Certificate table (document ledger style):**
- Columns: Certificate ID (mono, purple link), Theatre/Market (title + type badge + meta link), Outcome (colored: yes/no/range/pending), Verification Status (PRIMARY visual signal — badge with dot), Issue Date (mono), Tier (standard/enhanced badge), Actions (View/Verify buttons)
- Row states: disputed (red tint), under-review (amber tint)
- Disputed/review rows show inline reason text below status badge

**Market type badges:** binary (purple), continuous (blue), temporal (orange), investigative (green), regulatory (red)

**Right rail (3 panels, sticky):**
- Recent Certificates: mini-list with status dots
- Active Disputes: dispute ID + reason
- Type Distribution: horizontal bar chart by market type

**Empty state:** centered icon + "No certificates issued yet" + description + CTAs ("Browse Theatres" and "Verify a Certificate")

---

## Backend API Contract (Source of Truth)

### Investigations
- `GET /api/v1/investigations/` — list all investigations
- `POST /api/v1/investigations/` — create (theatre_id, construct_id, inquiry_class, domain_filters, stop_condition, stop_config)
- `GET /api/v1/investigations/{id}` — detail with evidence, claims, counter_signals, drift, has_legal_review_requirement

### Sub-resources
- `GET /api/v1/investigations/{id}/evidence` — EvidenceEnvelopeManifest
- `POST /api/v1/investigations/{id}/evidence` — submit evidence (domain filter enforced, triggers stop-condition eval + paradox risk recompute)
- `GET /api/v1/investigations/{id}/claims` — ClaimGraphSummary
- `POST /api/v1/investigations/{id}/claims` — submit claim (triggers stop-condition eval)
- `GET /api/v1/investigations/{id}/counter-signals` — CounterSignalFeedResponse
- `POST /api/v1/investigations/{id}/counter-signals` — submit counter-signal (domain filter enforced, triggers stop-condition eval + paradox risk recompute)
- `GET /api/v1/investigations/{id}/drift` — DriftFeedResponse
- `POST /api/v1/investigations/{id}/drift` — submit drift event (triggers stop-condition eval)

### Readiness + Certificate
- `GET /api/v1/investigations/{id}/readiness` — ReadinessResponse (status, stop_condition, stop_condition_status, stop_condition_reason, stop_condition_evaluated_at, has_certificate, certificate_status)
- `GET /api/v1/investigations/{id}/certificate` — CertificateRecordResponse (404 if none)
- `POST /api/v1/investigations/{id}/certificate/build` — build certificate (201; 409 if exists or not READY)
- `POST /api/v1/investigations/certificates/anchor-batch` — batch transition READY→ANCHORED→ISSUED (00:00 UTC)

### WebSocket Events
- `INVESTIGATION_STOP_CONDITION_MET` — stop condition changed to READY
- `INVESTIGATION_CERTIFICATE_READY` — certificate built
- `INVESTIGATION_CERTIFICATE_ISSUED` — certificate issued via batch anchor
- `INVESTIGATION_STATUS_CHANGED` — investigation status change

---

## Implementation Tasks

### C1. Investigation Browse Page — Match Design Reference Layout

**Current state:** InvestigationPage renders sidebar + tabbed detail. Browse view may differ from design reference card layout.

**Target:** Match `echelon_investigations_v1.html` browse view specification.

- Attention strip: derive from investigation list data
  - Hidden if `investigations.length === 0`
  - Alert (orange) if any investigation has no new evidence in 72h (derive from last evidence timestamp if available, or from investigation metadata)
  - Active (green) otherwise
- 4 KPI cards: Active count, Evidence Items (aggregate from investigation details if available, or show per-investigation counts), Claims Tracked (aggregate with status breakdown), Stalled count
- Investigation cards in `1fr 300px` grid with right rail
- Card structure: ID, status, "Open →", question, meta row (theatre chip, created date, humanized stop condition, provenance dots), progress row (evidence count, claims with mini-bar, counter-signals count, drift events count)

**Implementation truth:**
- KPI aggregation requires fetching sub-resource counts. If the list endpoint does not include evidence/claims counts, KPI cards should derive only from data available in the list response. Do not make N+1 queries to populate aggregate KPIs.
- The list endpoint does not currently provide an inquiry question, stop_condition, domain_filters, provenance summary, or stalled flag. Do not fabricate browse-card text or meta rows that rely on those fields.
- "Stalled" detection: if the backend does not surface a stalled flag or last_evidence_timestamp on the list response, defer the stalled detection or derive from what the detail response provides for the selected investigation only.
- Provenance dot breakdown requires evidence manifest data. If showing on browse cards requires per-investigation evidence fetches, show provenance dots only on the detail view (not on browse cards) to avoid N+1 queries.

**Rule:** Only show data that can be honestly derived from available API responses without excessive fetching. If the browse view cannot support the full card grid honestly, preserve the existing summary list structure and align the styling rather than fabricating richer cards.

### C2. Investigation Detail — Tab Panel Visual Alignment

**Current state:** 15 components exist and are wired to real data via hooks. Tab structure (Evidence, Claims, Counter-Signals, Drift, Readiness) exists.

**Target:** Match the design reference tab panel and section card patterns.

- Detail layout: `280px 1fr` grid — investigation sidebar list + tabbed main area
- Sidebar list: each item shows ID, optional CERT READY badge (from readiness data), status, question, evidence/claims counts
- Selected item: purple left border + purple-50 background
- Tab bar: underline-indicator tabs in sunken background strip
- Readiness tab: "new" tag badge

**Component-specific alignment:**

| Component | Design Reference Pattern |
|-----------|------------------------|
| EvidenceEnvelopePanel | Section card with sunken header. Evidence items chronological, provenance class badges (5 classes), content hashes, timestamps, redaction indicators. |
| ClaimGraphPanel | Section card. Claim nodes with type (FACT/CAUSAL/ATTRIBUTION) and status badges (SUPPORTED/PARTIALLY_SUPPORTED/UNCONFIRMED/CONTRADICTED). Confidence bars. Independence groups. |
| CounterSignalPanel | Section card. Signal class badges, materiality flags, detection_method, resolution_impact. Summary statistics. |
| DriftEventsPanel | Section card per `echelon_drift_submission_v1.html`. Drift type badges (5 types), impact badges (MATERIAL/NON_MATERIAL), original→new value, evidence refs. Material drift warning banner. Submission form. |
| ReadinessCertificatePanel | 5-state panel per `echelon_readiness_certificate_v2.html`. Stop condition readiness badge, lifecycle stepper, build CTA, routing decision, certificate record. |

**Rule:** Each component already renders real data. The work is visual alignment to section card patterns, badge styles, and layout structures specified in design references. Do not add mock data.

### C3. Readiness & Certificate Lifecycle — 5-State Visual Match

**Current state:** ReadinessCertificatePanel exists with lifecycle stepper and build action.

**Target:** Match all 5 states from `echelon_readiness_certificate_v2.html` exactly.

- State 1 (Not Ready): NOT_READY badge (gray), all lifecycle circles pending, no build CTA
- State 2 (Ready, No Certificate): READY badge (green), build CTA with shield icon and batch note, all lifecycle pending
- State 3 (Certificate Built, READY): READY badge, lifecycle READY=reached ANCHORED=active(pulsing) ISSUED=pending, routing row, certificate record grid
- State 4 (Issued): all lifecycle reached, ANCHORED+ISSUED timestamps identical (00:00 UTC), routing row, full certificate record
- State 5 (Review Required): same as state 3 but with amber REVIEW_REQUIRED banner: "Batch-anchor progression is not blocked by routing decision in the current implementation"

**Lifecycle stepper visual spec:**
- Circle states: pending (gray bg, gray border), active (cyan/purple bg, pulsing animation), reached (green bg, checkmark icon)
- Connector lines: gray default, green when reached
- Timestamps in mono, tabular-nums. Show "—" when pending.
- Batch note below stepper: "Queued for next 00:00 UTC batch-anchor cycle"

**Build Certificate button:**
- POST `/api/v1/investigations/{id}/certificate/build`
- Handle 409 (already exists or not READY) with clear error message
- On success: invalidate readiness + certificate queries, transition to state 3

**Implementation truth:**
- ANCHORED is transient — the UI will almost never observe ANCHORED as a durable state. After batch-anchor, the certificate goes directly to ISSUED. The stepper should still show ANCHORED as a step for lifecycle completeness.
- routing_decision does NOT block anchoring. The REVIEW_REQUIRED banner is informational only.

### C4. Drift Events Panel — Match Drift Submission Reference

**Current state:** DriftEventsPanel displays drift events and includes a submission form.

**Target:** Match `echelon_drift_submission_v1.html` specification.

- Event rows: drift type badge, impact badge (MATERIAL red / NON_MATERIAL gray), original→new value, evidence ref, timestamp
- Material drift warning banner (red): shown when any drift event has impact_assessment === "material"
- Submission form: drift_type dropdown (5 options), original/new value fields, impact_assessment radio (MATERIAL/NON_MATERIAL), evidence_ref (optional), submit button
- Validation: drift_type required
- POST triggers stop-condition re-evaluation (backend handles this; frontend should invalidate readiness query after drift submission)

### C5. Certificates Page — Match Document Ledger Layout

**Current state:** CertificatesPage exists, but `useCertificateGallery` currently surfaces theatre certificates only even though its comment mentions verification certificates.

**Target:** Match `echelon_certificates_v1.html` document ledger specification.

- Stats bar: Total, Issued (period-scoped), Verified, Disputed, Under Review, Linked Theatres, Linked Investigations
- Filter tabs: All | Verified | Disputed | Under Review (with counts)
- Certificate table: document ledger style with columns — Certificate ID (mono purple), Theatre/Market (title + type badge), Outcome, Verification Status (PRIMARY visual signal), Issue Date, Tier, Actions
- Row states: disputed (red tint), under-review (amber tint) with inline reason
- Right rail (sticky): Recent Certificates mini-list, Active Disputes, Type Distribution bar

**Implementation truth:**
- The current `useCertificateGallery` hook does **not** yet combine theatre + verification certificates in practice. Treat verification-source rows as deferred unless the hook is explicitly extended in this pass.
- The design reference shows a richer certificate model (market type, outcome, verification status, dispute reasons) than what the current UnifiedCertificate type surfaces.
- Stats bar values (Verified, Disputed, Under Review) require verification_status on certificates. If the backend does not surface these fields on the list endpoint, show only the stats that can be honestly derived. Defer stats that would require per-certificate detail fetches.
- Linked Theatres / Linked Investigations counts: derive from certificate data if theatre_id / investigation links are present.
- "Verify" action button: opens the public Verify page (`/verify`) with the certificate hash.

**Rule:** Certificates page is archival and formal. Verification state is the primary visual signal. Do not show stats or filters that cannot be backed by real API data.

### C6. WebSocket Event Integration — Certificate Lifecycle Real-time Updates

**Current state:** `useRealtimeInvalidation.ts` already maps investigation lifecycle events to query invalidation.

**Target:** Verify and refine WebSocket integration.

- `INVESTIGATION_STOP_CONDITION_MET`: invalidate `['investigation', invId, 'readiness']` → triggers re-render of ReadinessCertificatePanel
- `INVESTIGATION_CERTIFICATE_READY`: invalidate readiness + certificate queries → transition from state 2 to state 3
- `INVESTIGATION_CERTIFICATE_ISSUED`: invalidate readiness + certificate queries → transition to state 4
- `INVESTIGATION_STATUS_CHANGED`: invalidate investigation list + detail

**Verify:** The sidebar "CERT READY" badge should appear/disappear reactively when certificate readiness changes via WebSocket.

---

## Backend Limitations to Surface Honestly

1. **No stalled detection on list endpoint** — the list response may not include last_evidence_timestamp or a stalled flag. Stalled KPI and attention strip stalled state may need to be deferred or derived from detail-only data for the selected investigation.
2. **No inquiry question / stop condition / provenance on list endpoint** — browse cards cannot honestly show those fields unless the backend expands the summary response.
3. **No aggregate KPIs on list endpoint** — evidence counts, claims breakdowns are per-investigation sub-resource data. Aggregate KPI cards may need to show investigation-level counts only (number of investigations) rather than cross-investigation totals, unless the list response includes summary fields.
4. **Provenance breakdown per investigation** — requires evidence manifest fetch per investigation. On browse cards, provenance dots may need to be deferred to detail view to avoid N+1 queries.
5. **Certificate verification_status** — the certificates list may not include Disputed/Under Review/Verified status distinctions. Stats bar and filter tabs should only show categories supported by real data.
6. **Investigation certificate vs theatre certificate distinction** — the current certificate gallery does not yet merge verification certificates in practice, and the design reference shows a richer certificate model than the hook currently surfaces.
7. **Scanner Status panel** — the right rail scanner panel requires a scanner API. If no scanner endpoint exists, show as deferred.

---

## Acceptance Criteria

1. Investigation browse page shows real investigation data with attention strip derived from investigation state — no mock data
2. KPI cards derive from real API responses; aggregate values shown only where data is available without excessive fetching
3. Investigation browse cards or list rows match the design language while staying constrained to real summary fields; do not fabricate question/meta data the list API does not provide
4. Investigation detail sidebar + tabbed layout matches design reference grid structure
5. All 5 tab panels (Evidence, Claims, Counter-Signals, Drift, Readiness) render real API data through existing hooks
6. Readiness panel correctly shows all 5 states with lifecycle stepper visual match
7. Build Certificate action works: POST succeeds, 409 handled, queries invalidated on success
8. Drift events panel matches drift submission reference — event rows, material banner, submission form
9. Certificates page matches document ledger layout as far as current certificate data supports — defer verification/dispute-specific views that the current hook does not surface
10. WebSocket events update investigation state reactively (CERT READY badge, lifecycle transitions)
11. Empty states follow `echelon_empty_states_v1.html` patterns for all zero-data scenarios
12. `npm run build` passes

---

## Intentionally Deferred

- Stalled investigation detection (no backend signal for 72h evidence gap on list endpoint — defer to backend enhancement or detail-only derivation)
- Cross-investigation aggregate KPIs (evidence total, claims total across all investigations — defer unless list endpoint surfaces summary data)
- Provenance dots on browse cards (N+1 fetch concern — show only on detail view)
- Scanner Status right rail panel (no scanner API)
- Certificate dispute/review workflow actions (no dispute submission endpoints in current backend)
- Entity Profile panel data population (depends on EntityResolver integration maturity)
- DeltaBrief panel data population (depends on SignalScanner integration maturity)
- Verification-source rows in certificate gallery (hook currently maps theatre certificates only)

---

## Summary Format Per Pass

After each implementation pass, report:
1. What changed (files, components, hooks)
2. What remains intentionally deferred
3. Any backend limitations discovered
4. Any design reference corrections needed
5. Exact `npm run build` result
