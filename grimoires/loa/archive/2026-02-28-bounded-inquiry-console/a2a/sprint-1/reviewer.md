# Sprint 1 Implementation Report

> **Sprint:** sprint-1 (Foundation)
> **Global ID:** 1
> **Cycle:** cycle-001 (Bounded Inquiry Console)
> **Status:** COMPLETE
> **Commit:** feat(echelon-console): implement sprint-1 foundation

---

## Tasks Completed

### S1-T1: Project Scaffolding
- Created `echelon-inquiry-console/` at monorepo root
- Vite 5.4 + React 18.3 + TypeScript 5.3 + Tailwind 3.4
- `tailwind.config.ts` with all echelon design tokens (colours, fonts, keyframes, animations)
- `index.html` with Google Fonts preconnect (DM Sans, JetBrains Mono)
- `index.css` with Tailwind directives, body styles, hash-reveal keyframes
- `vercel.json` with SPA rewrite rule
- `postcss.config.js` and `vite.config.ts`
- `public/favicon.svg` (navy Echelon icon)

### S1-T2: Type Definitions
- `src/types/signal.ts`: `InquiryClass`, `ExecutionPath`, `Signal`
- `src/types/inquiry.ts`: `TheatreTemplate`, `CommitmentTarget`
- `src/types/execution.ts`: `Episode`, `MarketPhase`, `BundleFileEntry`
- `src/types/certificate.ts`: `CalibrationCertificate`
- All types match SDD section 5.1 exactly

### S1-T3: Mock Data Files
- `src/data/signals.ts`: 8 signals with correct `suggested_class` mapping per v13 taxonomy
  - Signal 1,2 -> INSPECTION; Signal 3 -> COUNTERFACTUAL; Signal 4 -> SURVEY
  - Signal 5 -> SCRUTINY; Signals 6,7,8 -> INVESTIGATIVE
- `src/data/templates.ts`:
  - 8 `TheatreTemplate` objects across all 5 inquiry classes
  - `COMMITMENT_TARGETS` map for all 8 templates with recursive sorted keys
  - 11 `ESCROW_EPISODES` from spec section 9 (exact criteria scores)
  - 6 `GLOBAL_CONFLICT_PHASES` from spec section 9
  - `generateMinimalEpisodes()` for remaining templates
- `src/data/certificates.ts`:
  - Pre-built ESCROW certificate with per-criteria scores from spec
  - Pre-built GLOBAL_CONFLICT certificate
  - Generated certificates for remaining templates via `buildCertificate()`
  - All `commitment_hash` values match their template sources (single source of truth)

### S1-T4: Utility Functions
- `src/utils/hash.ts`: `getCommitmentHash()`, `truncateHash()` — pure functions
- `src/utils/canonical.ts`: `toCanonicalDisplay()`, `toPrettyDisplay()` — recursive `sortKeysDeep`
- `src/utils/format.ts`: `relativeTime()`, `formatScore()`, `formatPercentage()`
- `src/utils/bundleFiles.ts`: `generateBundleFiles()` — handles PRODUCT and MARKET paths

### S1-T5: State Management Hook
- `src/hooks/useInquiryFlow.ts`:
  - `InquiryFlowState` interface
  - `InquiryAction` union type (10 actions)
  - `inquiryReducer` handling all action types per SDD section 6.1
  - `InquiryFlowProvider` component wrapping context
  - `useInquiryFlow()` hook with error if used outside provider
  - `SELECT_SIGNAL` sets signal + class + resets downstream state
  - `GO_TO_STEP` only allows backward navigation

### S1-T6: Layout Components + Routing
- `src/components/layout/Header.tsx`: "ECHELON" wordmark (uppercase, tracking)
- `src/components/layout/StepIndicator.tsx`: 5-step horizontal stepper
  - Completed: filled navy, clickable
  - Current: navy with pulse animation
  - Future: grey, disabled
  - Connectors: solid (completed) / dashed (future)
- `src/components/layout/Shell.tsx`: max-width container + Header + StepIndicator + Outlet
- `src/App.tsx`: `createBrowserRouter` with Shell layout, 5 routes + index redirect
- `src/main.tsx`: React root mount with StrictMode

---

## Verification

| Check | Result |
|-------|--------|
| `npm install` | 136 packages installed |
| `tsc --noEmit` | 0 errors |
| `npm run build` | 39 modules, dist/ built in 434ms |
| All routes resolve | Placeholder screens for all 5 routes |
| Index redirect | `/` -> `/signal-feed` |
| StepIndicator | Renders with correct visual states |
| Mock data importable | All data type-safe, no any types |
| All utilities pure | No side effects |
| Commitment hash consistency | Template hash === certificate hash |

---

## Files Created (27)

| Path | Purpose |
|------|---------|
| `echelon-inquiry-console/package.json` | Project config |
| `echelon-inquiry-console/tsconfig.json` | TypeScript config |
| `echelon-inquiry-console/vite.config.ts` | Vite config |
| `echelon-inquiry-console/tailwind.config.ts` | Tailwind with echelon tokens |
| `echelon-inquiry-console/postcss.config.js` | PostCSS config |
| `echelon-inquiry-console/vercel.json` | Vercel SPA deployment |
| `echelon-inquiry-console/index.html` | HTML with font preconnects |
| `echelon-inquiry-console/public/favicon.svg` | Echelon favicon |
| `echelon-inquiry-console/src/index.css` | Global styles + keyframes |
| `echelon-inquiry-console/src/main.tsx` | React root mount |
| `echelon-inquiry-console/src/App.tsx` | Router + provider |
| `echelon-inquiry-console/src/types/signal.ts` | Signal types |
| `echelon-inquiry-console/src/types/inquiry.ts` | Template types |
| `echelon-inquiry-console/src/types/execution.ts` | Episode/phase types |
| `echelon-inquiry-console/src/types/certificate.ts` | Certificate type |
| `echelon-inquiry-console/src/data/signals.ts` | 8 mock signals |
| `echelon-inquiry-console/src/data/templates.ts` | 8 templates + episodes + phases |
| `echelon-inquiry-console/src/data/certificates.ts` | Pre-built certificates |
| `echelon-inquiry-console/src/utils/hash.ts` | Hash utilities |
| `echelon-inquiry-console/src/utils/canonical.ts` | Canonical JSON |
| `echelon-inquiry-console/src/utils/format.ts` | Formatting utilities |
| `echelon-inquiry-console/src/utils/bundleFiles.ts` | Bundle file generator |
| `echelon-inquiry-console/src/hooks/useInquiryFlow.ts` | State management |
| `echelon-inquiry-console/src/components/layout/Header.tsx` | Header component |
| `echelon-inquiry-console/src/components/layout/StepIndicator.tsx` | Step indicator |
| `echelon-inquiry-console/src/components/layout/Shell.tsx` | App shell |

---

## Notes

- British spelling used throughout: GBP (not pound sign), "behaviour" in comments
- No emojis in any UI text
- `generateMinimalEpisodes()` uses deterministic-looking but random criteria scores for non-ESCROW templates. Sprint 2/3 can refine if needed.
- Node.js was not previously installed; installed via homebrew (v25.6.1) during this sprint.
