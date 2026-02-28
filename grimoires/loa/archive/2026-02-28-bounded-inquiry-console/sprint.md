# Sprint Plan: Echelon Bounded Inquiry Console

> **Cycle:** cycle-001 (Bounded Inquiry Console)
> **PRD:** `grimoires/loa/prd.md`
> **SDD:** `grimoires/loa/sdd.md`
> **Sprints:** 3
> **Agent:** Single (AI)

---

## Sprint Overview

| Sprint | Goal | Key Deliverable |
|--------|------|-----------------|
| sprint-1 | Foundation — scaffolding, types, data, hooks, layout, utilities | Buildable app with routing, state management, all mock data, layout shell |
| sprint-2 | Screens 1-2 — Signal Feed + Inquiry Configuration | Interactive signal selection → class/template selection → parameter commit with hash reveal |
| sprint-3 | Screens 3-5 — Execution + Certificate + Tier Gate + Deploy | Animated execution, certificate display, tier gate, Vercel deployment |

---

## Sprint 1: Foundation

**Goal:** Buildable Vite+React+TS+Tailwind app with routing, state management, mock data, layout components, and utility functions. No visible screens yet, but `npm run dev` serves the shell with step indicator and all routes resolve.

### Tasks

#### S1-T1: Project Scaffolding
**Description:** Create `echelon-inquiry-console/` in monorepo root. Initialise Vite + React + TypeScript project. Install dependencies (react-router-dom, tailwindcss, postcss, autoprefixer). Configure `tailwind.config.ts` with echelon design tokens (colours, fonts, keyframes, animations). Create `index.html` with Google Fonts preconnect. Create `index.css` with Tailwind directives, body styles, and hash-reveal keyframes. Create `vercel.json` with SPA rewrite. Create `vite.config.ts`.

**Acceptance Criteria:**
- `npm run dev` starts Vite dev server without errors
- `npm run build` produces `dist/` with no TypeScript errors
- Tailwind classes using `echelon-*` tokens compile correctly
- DM Sans and JetBrains Mono load from Google Fonts
- `vercel.json` present with SPA rewrite rule

**Complexity:** Low

---

#### S1-T2: Type Definitions
**Description:** Create all TypeScript type files in `src/types/`:
- `signal.ts`: `InquiryClass`, `ExecutionPath`, `Signal`
- `inquiry.ts`: `TheatreTemplate`, `CommitmentTarget`
- `execution.ts`: `Episode`, `MarketPhase`, `BundleFileEntry`
- `certificate.ts`: `CalibrationCertificate`

Exact types from SDD §5.1.

**Acceptance Criteria:**
- All 4 type files exist with types matching SDD
- All types export correctly (verified by importing in a test file)
- No `any` types

**Complexity:** Trivial

---

#### S1-T3: Mock Data Files
**Description:** Create all mock data in `src/data/`:
- `signals.ts`: 8 `Signal` objects from spec Section 9 (Companies House, SEC EDGAR, Polymarket, INPI RNE, BoE, GDELT, PACER, AIS Maritime)
- `templates.ts`: 8 `TheatreTemplate` objects, `COMMITMENT_TARGETS` map, 11 `ESCROW_EPISODES`, 6 `GLOBAL_CONFLICT_PHASES`, minimal episode generators for remaining templates
- `certificates.ts`: Pre-built `CalibrationCertificate` per template. ESCROW certificate `commitment_hash` must match the value in `COMMITMENT_TARGETS`

**Acceptance Criteria:**
- 8 signals with correct `suggested_class` mapping
- 8 templates across all 5 inquiry classes
- 11 escrow episodes with exact criteria scores from spec
- 6 market lifecycle phases from spec
- Certificate commitment hashes match commitment target hashes (single source of truth)
- All data type-safe (no TypeScript errors)

**Complexity:** Medium (data entry volume)

---

#### S1-T4: Utility Functions
**Description:** Create utility files in `src/utils/`:
- `hash.ts`: `getCommitmentHash(templateId)`, `truncateHash(hash, chars=8)`
- `canonical.ts`: `toCanonicalDisplay(obj)` (minified, sorted keys recursive), `toPrettyDisplay(obj)` (formatted, sorted keys recursive). Implement `sortKeysDeep` helper.
- `format.ts`: `relativeTime(iso)`, `formatScore(num)`, `formatPercentage(num)`
- `bundleFiles.ts`: `generateBundleFiles(template, episodes|phases)` returning `BundleFileEntry[]` for PRODUCT and MARKET paths

**Acceptance Criteria:**
- `toCanonicalDisplay` and `toPrettyDisplay` produce identical key ordering (recursive sort)
- `truncateHash` returns `"7a3f8c1d..."` format
- `relativeTime` produces "3m ago" style strings
- `generateBundleFiles` returns correct file tree for both PRODUCT and MARKET paths
- All functions are pure (no side effects)

**Complexity:** Low

---

#### S1-T5: State Management Hook
**Description:** Create `src/hooks/useInquiryFlow.ts`:
- `InquiryFlowState` interface
- `InquiryAction` union type (10 actions)
- `inquiryReducer` function handling all action types
- `InquiryFlowContext` and `InquiryFlowProvider` component
- `useInquiryFlow()` hook returning `[state, dispatch]`

Reducer logic per SDD §6.1:
- `SELECT_SIGNAL`: sets signal, sets `currentStep: 2`, sets `selectedClass` to signal's `suggested_class`
- `SELECT_CLASS`: sets class, clears template
- `SELECT_TEMPLATE`: sets template, sets `commitmentTarget` from `COMMITMENT_TARGETS`
- `COMMIT`: sets `isCommitted: true`
- `ADVANCE_EPISODE`: appends episode to `completedEpisodes`, increments `currentEpisode`
- `ADVANCE_PHASE`: appends phase to `completedPhases`, increments `currentPhase`
- `COMPLETE_EXECUTION`: sets `isComplete: true`, sets `currentStep: 4`
- `SET_CERTIFICATE`: sets certificate, sets `currentStep: 4`
- `GO_TO_STEP`: sets `currentStep` (only to completed or current+1)
- `RESET`: returns initial state

**Acceptance Criteria:**
- All 10 action types produce correct state transitions
- `RESET` returns clean initial state
- `GO_TO_STEP` only allows backward navigation to completed steps or forward to next step
- Provider wraps children correctly
- `useInquiryFlow` throws if used outside provider

**Complexity:** Medium

---

#### S1-T6: Layout Components + Routing
**Description:** Create:
- `src/components/layout/Header.tsx`: "ECHELON" wordmark (DM Sans 700, uppercase, tracking-widest)
- `src/components/layout/StepIndicator.tsx`: 5-step horizontal stepper with completed/current/future visual states, pulse animation on current, click to navigate to completed steps
- `src/components/layout/Shell.tsx`: max-width container with Header + StepIndicator + `<Outlet />`
- `src/App.tsx`: `createBrowserRouter` with Shell layout route, 5 child routes + index redirect to `/signal-feed`, wrap in `InquiryFlowProvider`
- `src/main.tsx`: React root mount

**Acceptance Criteria:**
- All 5 routes resolve (show placeholder content for now)
- `/` redirects to `/signal-feed`
- StepIndicator shows correct visual state based on `currentStep`
- Clicking a completed step navigates to it
- Future steps are not clickable
- Header renders "ECHELON" wordmark
- Shell constrains content to 1200px max-width

**Complexity:** Medium

---

### Sprint 1 Definition of Done
- `npm run dev` serves the app
- `npm run build` succeeds with 0 TypeScript errors
- All routes render (placeholder content acceptable)
- StepIndicator correctly reflects step state
- All mock data importable and type-safe
- All utility functions work correctly
- State management dispatches all actions correctly

---

## Sprint 2: Screens 1–2 (Signal Feed + Inquiry Configuration)

**Goal:** Complete interactive flow from signal selection through inquiry configuration to parameter commitment with hash reveal animation. User can: browse signals → select one → choose inquiry class → pick template → commit parameters → see hash animate.

### Tasks

#### S2-T1: Screen 1 — Signal Feed
**Description:** Implement `SignalFeed.tsx`, `SignalCard.tsx`, `SourceBadge.tsx`.

`SignalFeed`: Two-column layout (60/40 grid). Left: signal list. Right: detail panel showing full signal info when selected. "Create Inquiry" button dispatches `SELECT_SIGNAL` and navigates to `/configure`.

`SignalCard`: Renders source name, `SourceBadge`, headline (line-clamp-1), relative timestamp, confidence bar (percentage width `bg-echelon-blue`), settlement dot (green/grey). Entry animation: `animate-fade-slide-up` with `animationDelay: index * 200ms`. Selected state: `ring-2 ring-echelon-blue`.

`SourceBadge`: Jurisdiction text badge (border + text, no emojis).

**Acceptance Criteria:**
- 8 signals render with staggered 200ms entry animation
- Clicking a signal shows full detail in right panel (headline, summary, source metadata)
- "Create Inquiry" button visible in detail panel
- Clicking "Create Inquiry" navigates to `/configure` with signal in context
- Confidence bar renders at correct width
- Settlement eligibility indicator shows green/grey dot
- Responsive: columns stack on narrow viewports

**Complexity:** Medium

---

#### S2-T2: Screen 2 Section A — Class Selector
**Description:** Implement `ClassSelector.tsx` within `InquiryConfig.tsx`.

5 horizontal cards for COUNTERFACTUAL, INVESTIGATIVE, INSPECTION, SURVEY, SCRUTINY. Each shows:
- Class name (uppercase, tracking)
- One-line definition
- Execution path badge ("PRODUCT / Replay" or "MARKET / LMSR")
- Template count (filtered from TEMPLATES data)
- Geometric icon placeholder (CSS shape — rotated square for COUNTERFACTUAL, circle for INVESTIGATIVE, etc.)

Pre-selects the class matching `selectedSignal.suggested_class`. User can override by clicking another card. Selection dispatches `SELECT_CLASS`.

**Acceptance Criteria:**
- All 5 classes render as cards in a horizontal row
- Suggested class is pre-highlighted on mount
- Clicking a different class updates selection and filters templates below
- Execution path badge renders correctly (COUNTERFACTUAL = MARKET, others = PRODUCT)
- Template count is accurate per class

**Complexity:** Medium

---

#### S2-T3: Screen 2 Section B — Template Selection
**Description:** Implement `TemplatePanel.tsx`.

Shows templates filtered by selected inquiry class. Each template card displays:
- Template name (e.g. `ESCROW_MILESTONE_RELEASE_V1`)
- Execution path badge
- Criteria count
- Fixture count with pass/fail breakdown
- Existing composite score
- Optional template tags as small pills (e.g. "audit", "adversarial")

Clicking a template dispatches `SELECT_TEMPLATE`.

**Acceptance Criteria:**
- Template list filters correctly when inquiry class changes
- All 8 templates reachable across the 5 classes
- Template card shows all required fields
- Tags render as small pills when present
- Selected template has highlighted state

**Complexity:** Medium

---

#### S2-T4: Screen 2 Section C — Parameter Commit + Hash Panel
**Description:** Implement `ParameterCommit.tsx` and `CommitmentHash.tsx`.

`ParameterCommit`: Displays criteria IDs as pills, scoring thresholds, construct version pin, scorer version pin. All read-only. Commit button at bottom:
- PRODUCT templates: "Commit Parameters (local)"
- MARKET templates: "Commit + Publish (log)"

`CommitmentHash`: Below parameter display. Shows commitment target object in two modes:
- **Pretty (display)**: Formatted JSON, sorted keys, `toPrettyDisplay()` output in monospace code block
- **Hash bytes (canonical)**: Minified JSON, `toCanonicalDisplay()` output in monospace

Toggle between modes. On commit:
1. Auto-switch to canonical mode
2. Background pulse animation on canonical bytes (`animate-bg-pulse`)
3. SHA-256 hash reveals character-by-character below (`.hash-reveal` CSS class)
4. Parameters become read-only
5. "Run Replay" (PRODUCT) or "Publish Commitment" (MARKET) button appears
6. Clicking that button dispatches `COMMIT` + sets `currentStep: 3` + navigates to `/execute`

**Acceptance Criteria:**
- Pretty/canonical toggle works, shows correct JSON in each mode
- Canonical JSON has sorted keys at all nesting levels
- Commit button label matches execution path
- Commit animation: auto-switch to canonical → bg pulse → hash typewriter reveal
- After commit: parameters read-only, action button appears
- Hash displayed matches `commitment_hash` from template data
- Action button navigates to `/execute`

**Complexity:** High

---

### Sprint 2 Definition of Done
- Full interactive flow: signal → class → template → commit → hash reveal
- Navigation guards: `/configure` redirects to `/signal-feed` if no signal selected
- All animations specified in SDD §10 for Screens 1-2 working
- British English throughout
- No emojis in UI
- `npm run build` succeeds

---

## Sprint 3: Screens 3–5 (Execution + Certificate + Tier Gate) + Deploy

**Goal:** Complete the execution animation, certificate display, tier gate, and deploy to Vercel. Full demo loop works end-to-end.

### Tasks

#### S3-T1: Execution Simulator Hooks
**Description:** Implement `useExecutionSimulator.ts` and `useMarketSimulator.ts`.

`useExecutionSimulator(episodes, isCommitted, onComplete)`:
- Starts `setInterval(1500)` when `isCommitted` and execution path is PRODUCT
- Each tick dispatches `ADVANCE_EPISODE` with next episode from array
- On final episode: clears interval, calls `onComplete`
- Returns `{ skip: () => void }` — immediately advances all remaining episodes and calls `onComplete`
- Cleanup: clears interval on unmount

`useMarketSimulator(phases, isCommitted, onComplete)`:
- Same pattern with `ADVANCE_PHASE`

**Acceptance Criteria:**
- Episodes/phases advance at 1.5s intervals
- Skip immediately completes all remaining
- Interval cleaned up on unmount (no state updates after unmount)
- `onComplete` fires exactly once

**Complexity:** Medium

---

#### S3-T2: Screen 3 — Execution View (PRODUCT Path)
**Description:** Implement `ExecutionView.tsx`, `EpisodeProgress.tsx`, `ScoreStream.tsx`, `EvidenceBundleBuilder.tsx`.

`ExecutionView`: Two-column (55/45). Reads execution path from context. Renders `EpisodeProgress` or `MarketLifecycle` on left, `EvidenceBundleBuilder` on right. "Skip to Results" button. "Certificate Ready" banner with fade-slide-up after execution completes (500ms delay). "View Certificate" button navigates to `/certificate`.

`EpisodeProgress`: Header with template name + construct ID + version + "PRODUCT / Replay" badge. Progress bar (`Episode N of M`). Scrolling list of completed episode rows with per-criteria score dots. Rows animate in with `fade-slide-up`.

`ScoreStream`: Small running composite score display updating as episodes complete.

`EvidenceBundleBuilder`: Monospace tree using `├──`/`└──` characters. Files appear as episodes complete. Hashes show `[building...]` → truncated hash. Merkle root shows `[computing...]` → hash when all done. Uses `generateBundleFiles` utility.

**Acceptance Criteria:**
- Episode rows appear one-by-one on 1.5s timer
- Progress bar advances smoothly
- Per-criteria dots: green (1.0), red (0.0), amber (partial)
- Evidence bundle tree builds progressively
- "Skip to Results" completes execution immediately
- "Certificate Ready" banner appears 500ms after completion
- "View Certificate" navigates to `/certificate`

**Complexity:** High

---

#### S3-T3: Screen 3 — Execution View (MARKET Path)
**Description:** Implement `MarketLifecycle.tsx` within `ExecutionView.tsx`.

6 lifecycle phases animate in sequentially at 1.5s each. Each row: phase number, label, detail text, optional hash, checkmark on completion. Market evidence bundle tree (different file structure: `market_state/`, `resolution/`).

**Acceptance Criteria:**
- 6 phases animate in at 1.5s intervals
- Phase details and hashes match mock data
- Market-specific evidence bundle tree renders correctly
- Skip works identically to PRODUCT path
- "Certificate Ready" behaviour identical

**Complexity:** Medium

---

#### S3-T4: Screen 4 — Certificate Issued
**Description:** Implement `CertificateView.tsx`, `CriteriaBreakdown.tsx`, `ReproducibilityPins.tsx`, `HashVerificationPanel.tsx`, `TierBadge.tsx`.

`CertificateView`: Single-column centred card. Header: "CALIBRATION CERTIFICATE" + certificate ID + issued date. Large composite score with animated count-up (0.000 → final, 1s, requestAnimationFrame + ease-out). `TierBadge` next to score. Subtext: "N episodes scored across M criteria". Renders `CriteriaBreakdown`, `ReproducibilityPins`, `HashVerificationPanel`. "View Raw JSON" toggle showing full certificate JSON. "View Tier Assignment" button navigates to `/tier-gate`.

`CriteriaBreakdown`: Horizontal bars per criterion. Green >= 0.9, amber >= 0.5, red < 0.5.

`ReproducibilityPins`: Two monospace blocks — Version Pins and Cryptographic Chain.

`HashVerificationPanel`: Three rows — commitment hash match (IDENTICAL), evidence chain (VERIFIED), dataset hash (ANCHORED). All green checkmarks.

`TierBadge`: Coloured badge — amber (UNVERIFIED), blue (BACKTESTED), emerald (PROVEN).

**Acceptance Criteria:**
- Composite score animates from 0 to final value over ~1s
- Criteria bars coloured correctly by threshold
- Commitment hash on certificate matches the hash from Screen 2
- Hash verification panel shows all 3 checks passing
- "View Raw JSON" toggles full certificate JSON
- "View Tier Assignment" navigates to `/tier-gate`
- TierBadge renders correct colour for tier

**Complexity:** High

---

#### S3-T5: Screen 5 — Tier Gate
**Description:** Implement `TierGate.tsx`, `ModelPoolMap.tsx`, `ConstraintYieldingIndicator.tsx`.

`TierGate`: Three-column tier cards + journey indicator + constraint yielding callout + "Restart Demo" button.

`ModelPoolMap`: Three side-by-side cards (UNVERIFIED / BACKTESTED / PROVEN). Each shows: requirement, model pool, routing, constraint yielding, expiry. Current tier highlighted with ring/glow.

Journey indicator: horizontal bar showing `[Current: UNVERIFIED] ── 39 more replays needed ──> [BACKTESTED] ── 3 months + telemetry ──> [PROVEN]`

`ConstraintYieldingIndicator`: Callout box explaining that `review: skip` is overridden to `review: full` for UNVERIFIED tier.

"Restart Demo" dispatches `RESET` and navigates to `/signal-feed`.

**Acceptance Criteria:**
- All 3 tier cards render with correct content
- Current tier card highlighted (amber glow for UNVERIFIED)
- Journey indicator shows correct remaining requirements
- Constraint yielding explanation present and correct
- "Restart Demo" clears all state and returns to signal feed
- Full end-to-end loop: can restart and run through demo again

**Complexity:** Medium

---

#### S3-T6: Navigation Guards + Polish + Deploy
**Description:**
- Add navigation guards: each screen checks required context state on mount. If missing, redirect to `/signal-feed`.
- Ensure page transitions use `animate-fade-slide-up` on page wrapper divs.
- Verify British English throughout all visible text.
- Verify no emojis anywhere.
- Verify JetBrains Mono on all hashes/scores/JSON, DM Sans elsewhere.
- Run `npm run build` — fix any TypeScript errors.
- Test full demo flow end-to-end (both PRODUCT and MARKET paths).
- Push to repository.
- Configure Vercel deployment.

**Acceptance Criteria:**
- Direct URL to `/certificate` without context redirects to `/signal-feed`
- All 21 PRD acceptance criteria pass
- `npm run build` succeeds with 0 errors
- Full PRODUCT path demo loop works (Signal 1 → INSPECTION → ESCROW → commit → episodes → cert → tier → restart)
- Full MARKET path demo loop works (Signal 3 → COUNTERFACTUAL → GLOBAL_CONFLICT → commit → phases → cert → tier → restart)
- British spelling verified
- No emojis verified
- Deployed to Vercel (or ready for deployment)

**Complexity:** Medium

---

### Sprint 3 Definition of Done
- All 5 screens complete and navigable
- Both execution paths (PRODUCT and MARKET) working
- All 21 acceptance criteria from PRD pass
- Full demo loop restartable
- Deployed to Vercel

---

## Dependencies

```
Sprint 1 ──→ Sprint 2 ──→ Sprint 3
(foundation)  (input)      (output + deploy)
```

Strict sequential dependency. Each sprint depends on all prior sprint deliverables.

---

## Risk Buffer

| Risk | Sprint | Mitigation |
|------|--------|------------|
| Mock data transcription errors | 1 | Verify episode scores sum correctly |
| Hash consistency bugs | 2 | Single source of truth in `COMMITMENT_TARGETS` |
| Timer race conditions | 3 | Strict cleanup in `useEffect` return |
| CSS animation cross-browser | 3 | Test in Chrome + Safari |
| Vercel deployment config | 3 | Standard Vite SPA config, well-documented |
