# Sprint 4 (sprint-40) Implementation Report

## Cycle-016: Results Surface
## Sprint 4: Investigation Lifecycle Console + Navigation Redesign

### Summary

Implemented the full investigation lifecycle UI: a 5-step creation wizard, real-time progress tracking per stop-condition type, navigation restructuring with investigation sub-routes, and an aggregated signal feed with source-badged cards. All tests pass (81/81), TSC clean.

---

### Task 4.1: Investigation Creation Wizard

**Status**: COMPLETED

**Files**:
- `src/components/investigation/CreateInvestigationWizard.tsx` — NEW
- `src/components/investigation/DomainFilterSelector.tsx` — NEW
- `src/components/investigation/StopConditionConfigurator.tsx` — NEW
- `src/hooks/useInvestigation.ts` — MODIFIED (added `useCreateInvestigation` mutation)

**Implementation Details**:

1. **CreateInvestigationWizard** — 5-step wizard flow:
   - Step 1: Inquiry Question (textarea + inquiry class selector: INVESTIGATIVE/MONITORING/VERIFICATION)
   - Step 2: Template selection (placeholder, auto-advances)
   - Step 3: Domain Filters (9 OSINT categories with source group previews)
   - Step 4: Stop Condition (3 types with per-type config)
   - Step 5: Review & Commit with immutability warning

2. **DomainFilterSelector** — 9 domain categories:
   - financial_filings, regulatory, corporate_registry, litigation, media_news, social_sentiment, supply_chain, geopolitical, technical
   - Each shows source group preview badges, toggle selection with category count

3. **StopConditionConfigurator** — 3 stop conditions:
   - OUTCOME_RESOLUTION: Default, no extra config
   - EVIDENCE_THRESHOLD: min_supported_claims (number), min_corroboration_score (0-1 float)
   - SPONSOR_DEFINED: milestone_timestamp (datetime-local input)

4. **useCreateInvestigation** — TanStack Query mutation wrapping `createInvestigation` API, invalidates `['investigations']` on success

**Acceptance Criteria**: Met. Wizard navigates through all 5 steps, validates per-step, shows immutability warning, POSTs via mutation hook.

---

### Task 4.2: Investigation Progress Tracker

**Status**: COMPLETED

**Files**:
- `src/components/investigation/InvestigationProgressBar.tsx` — NEW
- `src/components/investigation/StopConditionProgress.tsx` — NEW

**Implementation Details**:

1. **StopConditionProgress** — Per-stop-condition visualization:
   - OUTCOME_RESOLUTION: Informational text
   - EVIDENCE_THRESHOLD: Progress bar showing supported claims vs. min_supported_claims target
   - SPONSOR_DEFINED: Days/hours remaining until milestone timestamp
   - Common stats grid: Evidence count, Claims count, Signals count

2. **InvestigationProgressBar** — Composite component:
   - Integrates StopConditionProgress
   - Claim status distribution bar (supported/partially_supported/unconfirmed/contradicted)
   - Material counter-signal warning banner

**Acceptance Criteria**: Met. Shows progress for all 3 stop condition types, claim distribution, corroboration indicator.

---

### Task 4.3: Navigation Redesign

**Status**: COMPLETED

**Files**:
- `src/components/layout/Sidebar.tsx` — MODIFIED
- `src/router.tsx` — MODIFIED
- `src/pages/CreateInvestigationPage.tsx` — NEW (thin wrapper)
- `src/pages/SignalFeedPage.tsx` — NEW (thin wrapper)

**Implementation Details**:

1. **Sidebar restructuring**:
   - Added Dashboard (Home icon) as first nav item
   - Added Investigations with matchPrefixes: ['/investigation']
   - Removed VRF and Launchpad from main nav (routes preserved)
   - Added INVESTIGATION_SUBNAV: Active, Signal Feed, Create
   - Extended NavContent to accept `isInvestigationSection` prop
   - Unified subnav rendering for both Agents and Investigation sections

2. **Router updates**:
   - Default route changed from `/marketplace` to `/home`
   - Added `/home` → HomePage
   - Added `/investigation/signals` → SignalFeedPage
   - Added `/investigation/create` → CreateInvestigationPage

**Acceptance Criteria**: Met. Dashboard as default, investigation sub-routes accessible, agents subnav preserved.

---

### Task 4.4: Signal Feed Migration

**Status**: COMPLETED

**Files**:
- `src/components/investigation/SignalCard.tsx` — NEW
- `src/components/investigation/SignalFeedPanel.tsx` — NEW

**Implementation Details**:

1. **SignalCard** — Source-badged counter-signal card:
   - 11 signal_class color mappings (official_denial, regulatory_clearance, market_contradiction, etc.)
   - Shows signal class badge, material indicator, detection method, resolution impact, evidence ref
   - Optional "Create Investigation from Signal" button

2. **SignalFeedPanel** — Aggregated signal feed:
   - Uses useInvestigationList + useInvestigationDetail hooks
   - Investigation filter buttons when multiple investigations exist
   - Auto-selects first investigation with signals
   - Sorts signals by detected_at (newest first)
   - Empty state with informational message

**Acceptance Criteria**: Met. Signals rendered with source badges, click-through to create investigation, empty state.

---

### Task 4.5: Sprint 4 Tests

**Status**: COMPLETED

**Files**:
- `src/components/investigation/__tests__/CreateInvestigationWizard.test.tsx` — NEW (6 tests)
- `src/components/investigation/__tests__/InvestigationProgressBar.test.tsx` — NEW (4 tests)
- `src/components/investigation/__tests__/SignalFeedPanel.test.tsx` — NEW (2 tests)
- `src/components/layout/__tests__/Navigation.test.tsx` — NEW (5 tests)

**Test Coverage**:

1. **CreateInvestigationWizard tests** (6):
   - Renders step 1 with inquiry question input
   - Navigates forward and backward through steps
   - Cancel button calls onCancel
   - Immutability warning on review step
   - Domain filter selector shows 9 categories
   - Stop condition configurator shows 3 types

2. **InvestigationProgressBar tests** (4):
   - OUTCOME_RESOLUTION progress display
   - EVIDENCE_THRESHOLD with supported claims bar
   - SPONSOR_DEFINED with milestone countdown
   - Material counter-signal warning

3. **SignalFeedPanel tests** (2):
   - Renders signals with source badges and material indicator
   - Empty state when no signals

4. **Navigation tests** (5):
   - All 8 primary nav items render
   - Investigation subnav shown on investigation routes
   - Agents subnav shown on agents routes
   - Investigation subnav hidden on non-investigation routes
   - All nav links point to valid routes

**Verification**: 81 tests passing, 20 test files, TSC clean (zero errors).

---

### Files Created/Modified Summary

| File | Action | Task |
|------|--------|------|
| `src/components/investigation/CreateInvestigationWizard.tsx` | NEW | 4.1 |
| `src/components/investigation/DomainFilterSelector.tsx` | NEW | 4.1 |
| `src/components/investigation/StopConditionConfigurator.tsx` | NEW | 4.1 |
| `src/hooks/useInvestigation.ts` | MODIFIED | 4.1 |
| `src/components/investigation/InvestigationProgressBar.tsx` | NEW | 4.2 |
| `src/components/investigation/StopConditionProgress.tsx` | NEW | 4.2 |
| `src/components/layout/Sidebar.tsx` | MODIFIED | 4.3 |
| `src/router.tsx` | MODIFIED | 4.3 |
| `src/pages/CreateInvestigationPage.tsx` | NEW | 4.3 |
| `src/pages/SignalFeedPage.tsx` | NEW | 4.3 |
| `src/components/investigation/SignalCard.tsx` | NEW | 4.4 |
| `src/components/investigation/SignalFeedPanel.tsx` | NEW | 4.4 |
| `src/components/investigation/__tests__/CreateInvestigationWizard.test.tsx` | NEW | 4.5 |
| `src/components/investigation/__tests__/InvestigationProgressBar.test.tsx` | NEW | 4.5 |
| `src/components/investigation/__tests__/SignalFeedPanel.test.tsx` | NEW | 4.5 |
| `src/components/layout/__tests__/Navigation.test.tsx` | NEW | 4.5 |

### Verification

- `npx vitest run` — 81 tests, 20 files, 0 failures
- `npx tsc -b --noEmit` — 0 errors
