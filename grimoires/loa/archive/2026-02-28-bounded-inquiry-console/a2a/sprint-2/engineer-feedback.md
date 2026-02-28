# Sprint 2 Review — Engineer Feedback

> **Reviewer:** Senior Technical Lead
> **Sprint:** sprint-2 (Screens 1-2)
> **Verdict:** All good

---

## Review Summary

All 4 tasks meet their acceptance criteria. Code is clean, type-safe, and follows the SDD specifications. `npm run build` succeeds with 0 TypeScript errors. 10 files created/modified. No blocking issues.

## Verification Against Acceptance Criteria

### S2-T1: Screen 1 — Signal Feed
- [x] 8 signals render with staggered 200ms entry animation (`animationDelay={idx * 200}`)
- [x] Clicking a signal shows full detail in right panel (headline, summary, source metadata)
- [x] "Create Inquiry" button visible in detail panel
- [x] Clicking "Create Inquiry" navigates to `/configure` with signal in context (dispatches `SELECT_SIGNAL`)
- [x] Confidence bar renders at correct width (percentage from `formatPercentage`)
- [x] Settlement eligibility indicator shows green/grey dot
- [x] Responsive: columns stack on narrow viewports (`grid-cols-1 md:grid-cols-5`)

### S2-T2: Screen 2 Section A — Class Selector
- [x] All 5 classes render as cards in a horizontal row (`lg:grid-cols-5`)
- [x] Suggested class is pre-highlighted on mount (`active = selectedClass ?? suggestedClass`)
- [x] Clicking a different class updates selection and filters templates below
- [x] Execution path badge renders correctly (COUNTERFACTUAL = MARKET, others = PRODUCT)
- [x] Template count is accurate per class (dynamically computed)

### S2-T3: Screen 2 Section B — Template Selection
- [x] Template list filters correctly when inquiry class changes
- [x] All 8 templates reachable across the 5 classes
- [x] Template card shows all required fields (template_id, name, path badge, criteria, fixtures P/F, composite)
- [x] Tags render as small pills when present
- [x] Selected template has highlighted state (`ring-2 ring-echelon-blue`)

### S2-T4: Screen 2 Section C — Parameter Commit + Hash Panel
- [x] Pretty/canonical toggle works, shows correct JSON in each mode
- [x] Canonical JSON has sorted keys at all nesting levels (via `sortKeysDeep`)
- [x] Commit button label matches execution path
- [x] Commit animation: auto-switch to canonical + bg pulse + hash typewriter reveal
- [x] After commit: parameters read-only (opacity reduction), action button appears
- [x] Hash displayed matches `commitment_hash` from template data
- [x] Action button navigates to `/execute`

### Sprint 2 Definition of Done
- [x] Full interactive flow: signal → class → template → commit → hash reveal
- [x] Navigation guard: `/configure` redirects to `/signal-feed` if no signal selected
- [x] All animations specified in SDD §10 for Screens 1-2 working
- [x] British English throughout
- [x] No emojis in UI
- [x] `npm run build` succeeds

## Observations (Non-blocking)

1. **Good pattern**: `ClassSelector` computes template counts dynamically from `TEMPLATES` rather than hardcoding — stays in sync automatically if templates change.

2. **Good pattern**: `CommitmentHash` uses `useEffect` cleanup on the setTimeout for the hash reveal delay — prevents state updates on unmounted components.

3. **GO_TO_STEP updated**: Correctly changed to allow forward navigation to `currentStep + 1` (was backward-only in Sprint 1). The Sprint 1 acceptance criteria said "only allows backward navigation to completed steps" — the new behaviour is a superset that also supports the required forward step. Appropriate for the proceed-to-next-screen flow.
