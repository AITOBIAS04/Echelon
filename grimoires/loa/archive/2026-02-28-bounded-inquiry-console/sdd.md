# SDD: Echelon Bounded Inquiry Console

> **Version:** 1.0
> **Date:** 2026-02-28
> **PRD:** `grimoires/loa/prd.md`
> **Spec:** `Echelon_Bounded_Inquiry_Console_Spec_v1_1.md` + Patch v1.1

---

## 1. Executive Summary

Standalone Vite+React+TypeScript+Tailwind SPA demonstrating the Echelon bounded inquiry lifecycle across 5 screens. All data is hardcoded mock. No backend, no API calls. Deploys as its own Vercel site. ~30 component files, ~3 hooks, ~8 mock data files, ~4 utility files.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Browser (SPA)                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  React Router v6 ──→ Shell (layout) ──→ StepIndicator   │
│       │                                                  │
│       ├── /signal-feed     → SignalFeed                  │
│       ├── /configure       → InquiryConfig               │
│       ├── /execute         → ExecutionView               │
│       ├── /certificate     → CertificateView             │
│       └── /tier-gate       → TierGate                    │
│                                                          │
│  State: useInquiryFlow (React Context + useReducer)      │
│  Timer: useExecutionSimulator | useMarketSimulator       │
│  Data:  Static imports from src/data/*.ts                │
│                                                          │
│  No network calls. No localStorage. No service workers.  │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

```
Mock Data (static imports)
    │
    ▼
useInquiryFlow (context + reducer)
    │
    ├── selectedSignal ──→ SignalFeed
    ├── selectedClass ───→ ClassSelector
    ├── selectedTemplate → TemplatePanel + ParameterCommit
    ├── isCommitted ────→ CommitmentHash
    ├── executionProgress → EpisodeProgress | MarketLifecycle
    └── certificate ────→ CertificateView + TierGate
```

---

## 3. Technology Stack

| Layer | Choice | Justification |
|-------|--------|---------------|
| Build | Vite 5.4 | Fast dev server, standard for new React projects |
| UI | React 18.3 | Per spec (not 19 — standalone app, no need for latest) |
| Language | TypeScript 5.3 | Type safety for mock data contracts |
| Styling | Tailwind CSS 3.4 | Utility-first, fast iteration, design token support |
| Routing | react-router-dom 6.20 | Standard, lightweight, supports layout routes |
| Animation | CSS transitions + @keyframes | Spec mandates no animation libraries |
| Fonts | Google Fonts (DM Sans, JetBrains Mono) | CDN with preconnect for fast loading |

### No Additional Dependencies

The spec explicitly requires a lean build. No state management library (React context + useReducer suffices), no animation library, no UI component library.

---

## 4. Component Design

### 4.1 Layout Components

#### `Shell.tsx`
Wraps all screens. Provides max-width container, padding, and renders `StepIndicator` + `Header` above the `<Outlet />`.

```tsx
// Props: none (uses Outlet from react-router)
// Renders: Header, StepIndicator, <Outlet />
// Layout: max-w-[1200px] mx-auto px-8
```

#### `StepIndicator.tsx`
Fixed horizontal stepper at top. 5 steps. Reads `currentStep` from `useInquiryFlow`.

```tsx
interface StepIndicatorProps {
  currentStep: 1 | 2 | 3 | 4 | 5;
  completedSteps: Set<number>;
  onStepClick: (step: number) => void; // only completed steps clickable
}
```

Steps: `Signal → Configure → Execute → Certificate → Tier Gate`

Visual states:
- Completed: filled circle, deep navy (`#1E3A5F`)
- Current: filled circle with subtle pulse animation
- Future: hollow circle, light grey
- Connectors: solid (completed), dashed (future)

#### `Header.tsx`
Minimal. "ECHELON" wordmark in DM Sans 700, uppercase, letter-spacing 0.1em.

### 4.2 Screen 1: Signal Feed

#### `SignalFeed.tsx`
Page component. Two-column layout (60/40). Manages selected signal state locally, delegates to context on "Create Inquiry".

```tsx
// Internal state: hoveredSignal, selectedSignal
// Context interaction: dispatch({ type: 'SELECT_SIGNAL', payload: signal })
// Navigation: navigates to /configure on "Create Inquiry"
```

#### `SignalCard.tsx`
```tsx
interface SignalCardProps {
  signal: Signal;
  isSelected: boolean;
  animationDelay: number; // staggered entry: index * 200ms
  onClick: () => void;
}
```

Renders: source name, jurisdiction badge, headline (truncated), relative timestamp, confidence bar (percentage width), settlement dot (green/grey).

Entry animation: `opacity-0 translate-y-2` → `opacity-100 translate-y-0` with staggered delay via `style={{ animationDelay }}`.

#### `SourceBadge.tsx`
```tsx
interface SourceBadgeProps {
  jurisdiction: string; // "GB", "US", "EU", "Global"
}
```

Small text badge with border. No flag emojis.

### 4.3 Screen 2: Inquiry Configuration

#### `InquiryConfig.tsx`
Page component. Three vertically stacked sections. Reads suggested class from context, manages local class/template selection.

#### `ClassSelector.tsx`
```tsx
interface ClassSelectorProps {
  suggestedClass: InquiryClass;
  selectedClass: InquiryClass | null;
  onSelect: (cls: InquiryClass) => void;
}
```

5 horizontal cards. Each card:
- Class name (uppercase, DM Sans 600, letter-spacing 0.05em)
- One-line definition
- Execution path badge
- Template count
- Geometric icon placeholder (CSS-only — a div with border/transform)

Suggested class has highlighted border on initial render. User can override.

#### `TemplatePanel.tsx`
```tsx
interface TemplatePanelProps {
  selectedClass: InquiryClass;
  selectedTemplate: TheatreTemplate | null;
  onSelect: (template: TheatreTemplate) => void;
}
```

Filters `TEMPLATES` data by `inquiry_class`. Each template card shows: name, execution path badge, criteria count, fixture count with pass/fail, composite score, optional tags as small pills.

#### `ParameterCommit.tsx`
```tsx
interface ParameterCommitProps {
  template: TheatreTemplate;
  isCommitted: boolean;
  onCommit: () => void;
}
```

Shows criteria IDs as pills, scoring thresholds, construct/scorer version pins. Read-only. "Commit" button at bottom — label varies by execution path.

#### `CommitmentHash.tsx`
```tsx
interface CommitmentHashProps {
  commitmentTarget: CommitmentTarget;
  isCommitted: boolean;
  executionPath: ExecutionPath;
}
```

Two display modes via toggle: "Pretty (display)" and "Hash bytes (canonical)".

**Pretty mode:** Formatted JSON in a monospace code block (JetBrains Mono). Indented, syntax-highlighted with Tailwind classes.

**Canonical mode:** Minified JSON string, single line, sorted keys. Displayed in monospace with horizontal scroll if needed.

**Commit animation:**
1. Toggle auto-switches to canonical mode
2. Background pulse on canonical bytes (CSS `@keyframes bgPulse`)
3. SHA-256 hash reveals character-by-character below (CSS `@keyframes typewriter` — `width` from 0 to 100% with `overflow: hidden` and `white-space: nowrap` on a monospace element, stepping by `ch` units)

### 4.4 Screen 3: Construct Execution

#### `ExecutionView.tsx`
Page component. Reads `selectedTemplate.execution_path` from context. Renders either `EpisodeProgress` (PRODUCT) or `MarketLifecycle` (MARKET) in the left column, and `EvidenceBundleBuilder` in the right column. Both paths share the same two-column layout and "Skip to Results" / "Certificate Ready" behaviour.

#### `EpisodeProgress.tsx`
```tsx
interface EpisodeProgressProps {
  episodes: Episode[];
  currentIndex: number;
  totalEpisodes: number;
  templateName: string;
  constructId: string;
  constructVersion: string;
}
```

Progress bar: smooth CSS transition on width. Below: scrolling list of completed episodes. Each row shows episode ID, ground truth summary (truncated), score, status, and per-criteria dots (green/red/amber via `bg-emerald-500`/`bg-red-500`/`bg-amber-500` circles).

Timer logic lives in `useExecutionSimulator`, not here.

#### `MarketLifecycle.tsx`
```tsx
interface MarketLifecycleProps {
  phases: MarketPhase[];
  currentPhaseIndex: number;
  templateName: string;
  constructId: string;
  constructVersion: string;
}
```

6 lifecycle rows. Each animates from `pending` → `complete` with checkmark and detail text. Same 1.5s cadence.

#### `ScoreStream.tsx`
Optional component showing running composite score updating as episodes complete. Animated number (count-up effect via `requestAnimationFrame`).

#### `EvidenceBundleBuilder.tsx`
```tsx
interface EvidenceBundleBuilderProps {
  executionPath: ExecutionPath;
  completedCount: number;
  totalCount: number;
  bundleFiles: BundleFileEntry[];
}
```

Tree visualisation using indentation and `├──`/`└──` characters in monospace. Files appear one-by-one as episodes complete. Hash shows `[building...]` until episode done, then reveals truncated hash. Merkle root shows `[computing...]` until all episodes finish.

`BundleFileEntry`:
```tsx
interface BundleFileEntry {
  path: string;       // e.g. "ground_truth/ep_001.json"
  hash?: string;      // truncated SHA-256, undefined while building
  status: 'committed' | 'building' | 'complete';
}
```

### 4.5 Screen 4: Certificate Issued

#### `CertificateView.tsx`
Page component. Single-column, centred card. Reads certificate from context.

**Composite score:** Large text, animated count-up from 0.000 to final value over ~1s. Uses `requestAnimationFrame` with easing.

**"View Raw JSON" toggle:** Renders full certificate object in a `<pre>` block with JetBrains Mono. JSON pretty-printed with 2-space indent.

#### `CriteriaBreakdown.tsx`
```tsx
interface CriteriaBreakdownProps {
  criteriaScores: Record<string, number>;
}
```

Horizontal bar chart. Each row: criteria ID label, score value, coloured bar (`bg-emerald-500` >= 0.9, `bg-amber-500` >= 0.5, `bg-red-500` < 0.5). Bar width proportional to score (percentage).

#### `ReproducibilityPins.tsx`
```tsx
interface ReproducibilityPinsProps {
  constructVersion: string;
  scorerVersion: string;
  methodology: string;
  datasetHashes: Record<string, string>;
  evidenceBundleHash: string;
  commitmentHash: string;
}
```

Two monospace code blocks: "Version Pins" and "Cryptographic Chain". JetBrains Mono, slate text on light grey background.

#### `HashVerificationPanel.tsx`
```tsx
interface HashVerificationPanelProps {
  commitmentHashFromConfig: string; // from Screen 2
  commitmentHashFromCert: string;   // from certificate
  merkleRoot: string;
  datasetHashMatch: boolean;
}
```

Three verification rows, each with checkmark + label + detail + status badge (IDENTICAL / VERIFIED / ANCHORED). Green checkmarks.

#### `TierBadge.tsx`
```tsx
interface TierBadgeProps {
  tier: 'UNVERIFIED' | 'BACKTESTED' | 'PROVEN';
  size?: 'sm' | 'md' | 'lg';
}
```

Colour mapping:
- UNVERIFIED: amber (`bg-amber-100 text-amber-800 border-amber-300`)
- BACKTESTED: blue (`bg-blue-100 text-blue-800 border-blue-300`)
- PROVEN: emerald (`bg-emerald-100 text-emerald-800 border-emerald-300`)

### 4.6 Screen 5: Tier Gate

#### `TierGate.tsx`
Page component. Three-column layout for tier cards + journey indicator + constraint yielding callout + restart button.

#### `ModelPoolMap.tsx`
```tsx
interface ModelPoolMapProps {
  currentTier: 'UNVERIFIED' | 'BACKTESTED' | 'PROVEN';
}
```

Three tier cards side-by-side. Current tier has highlighted border (glow effect via `ring-2 ring-amber-400` or similar). Each card: tier name, requirement, model pool, routing, constraint yielding, expiry.

#### `ConstraintYieldingIndicator.tsx`
```tsx
interface ConstraintYieldingIndicatorProps {
  declaredReview: string; // e.g. "skip"
  effectiveReview: string; // e.g. "full"
  tier: 'UNVERIFIED' | 'BACKTESTED' | 'PROVEN';
}
```

Callout box with explanation text. Shows declared vs effective review level.

---

## 5. Data Architecture

### 5.1 Type Definitions

All types in `src/types/`. Direct transcription from spec Section 4.

**`signal.ts`:**
```tsx
export type InquiryClass = 'COUNTERFACTUAL' | 'INVESTIGATIVE' | 'INSPECTION' | 'SURVEY' | 'SCRUTINY';
export type ExecutionPath = 'PRODUCT' | 'MARKET';

export interface Signal {
  id: string;
  source_id: string;
  source_group: string;
  source_name: string;
  jurisdiction: string;
  headline: string;
  summary: string;
  timestamp: string;
  confidence: number;
  settlement_eligible: boolean;
  access_surface: 'public_api' | 'paid_gateway' | 'portal_scrape';
  receipt_mode: 'http_transcript' | 'signed_payload' | 'screenshot';
  suggested_class: InquiryClass;
}
```

**`inquiry.ts`:**
```tsx
export interface TheatreTemplate {
  template_id: string;
  name: string;
  inquiry_class: InquiryClass;
  execution_path: ExecutionPath;
  criteria_ids: string[];
  fixture_count: number;
  pass_count: number;
  fail_count: number;
  existing_composite: number;
  construct_id: string;
  construct_version: string;
  scorer_version: string;
  commitment_hash: string;
  template_tags?: string[];
}

export interface CommitmentTarget {
  dataset_hashes: { ground_truth: string; fixtures: string };
  template: {
    template_id: string;
    version: string;
    criteria_ids: string[];
    scoring_thresholds: Record<string, number>;
  };
  version_pins: { construct: string; scorer: string; methodology: string };
}
```

**`execution.ts`:**
```tsx
export interface Episode {
  episode_id: string;
  ground_truth_summary: string;
  expected_class: 'PASS' | 'FAIL';
  construct_output_class: 'PASS' | 'FAIL';
  criteria_scores: Record<string, number>;
  composite_score: number;
  ground_truth_hash: string;
  invocation_hash: string;
}

export interface MarketPhase {
  phase_number: number;
  label: string;
  detail: string;
  hash?: string;
  status: 'pending' | 'active' | 'complete';
}

export interface BundleFileEntry {
  path: string;
  hash?: string;
  status: 'committed' | 'building' | 'complete';
}
```

**`certificate.ts`:**
```tsx
export interface CalibrationCertificate {
  certificate_id: string;
  template_id: string;
  inquiry_class: InquiryClass;
  execution_path: ExecutionPath;
  construct_id: string;
  construct_version: string;
  scorer_version: string;
  issued_at: string;
  expires_at: string;
  replay_count: number;
  criteria_ids: string[];
  criteria_scores: Record<string, number>;
  composite_score: number;
  verification_tier: 'UNVERIFIED' | 'BACKTESTED' | 'PROVEN';
  dataset_hash: string;
  evidence_bundle_hash: string;
  commitment_hash: string;
  methodology: string;
}
```

### 5.2 Mock Data Files

**`src/data/signals.ts`:** Array of 8 `Signal` objects. Staggered timestamps. Data from spec Section 9.

**`src/data/templates.ts`:**
- `TEMPLATES`: Array of 8 `TheatreTemplate` objects
- `COMMITMENT_TARGETS`: Map of `template_id → CommitmentTarget`
- `ESCROW_EPISODES`: Array of 11 `Episode` objects (from spec)
- `GLOBAL_CONFLICT_PHASES`: Array of 6 `MarketPhase` objects (from spec)
- Episode generators for remaining templates (minimal: 1-3 episodes with pass/fail variety)

**`src/data/certificates.ts`:** Pre-built `CalibrationCertificate` objects per template. The ESCROW certificate uses `commitment_hash` matching the value displayed in Screen 2.

### 5.3 Evidence Bundle File Generators

`src/utils/bundleFiles.ts` — pure function that generates the `BundleFileEntry[]` array for a given template:

```tsx
export function generateBundleFiles(
  template: TheatreTemplate,
  episodes: Episode[] | MarketPhase[]
): BundleFileEntry[]
```

For PRODUCT path: `manifest.json`, `template.json`, `ground_truth/ep_NNN.json`, `invocations/ep_NNN_response.json`, `scores/ep_NNN_score.json`, `merkle_root`.

For MARKET path: `manifest.json`, `template.json`, `commitment_receipt.json`, `market_state/opening_state.json`, `market_state/trade_log.json`, `market_state/closing_state.json`, `resolution/evidence_submission.json`, `resolution/settlement_output.json`, `merkle_root`.

---

## 6. State Management

### 6.1 InquiryFlow Context

Single React Context with `useReducer`.

```tsx
interface InquiryFlowState {
  currentStep: 1 | 2 | 3 | 4 | 5;
  selectedSignal: Signal | null;
  selectedClass: InquiryClass | null;
  selectedTemplate: TheatreTemplate | null;
  commitmentTarget: CommitmentTarget | null;
  isCommitted: boolean;
  executionProgress: {
    currentEpisode: number;
    totalEpisodes: number;
    completedEpisodes: Episode[];
    currentPhase: number;
    totalPhases: number;
    completedPhases: MarketPhase[];
    isComplete: boolean;
  };
  certificate: CalibrationCertificate | null;
}

type InquiryAction =
  | { type: 'SELECT_SIGNAL'; payload: Signal }
  | { type: 'SELECT_CLASS'; payload: InquiryClass }
  | { type: 'SELECT_TEMPLATE'; payload: TheatreTemplate }
  | { type: 'COMMIT' }
  | { type: 'ADVANCE_EPISODE'; payload: Episode }
  | { type: 'ADVANCE_PHASE'; payload: MarketPhase }
  | { type: 'COMPLETE_EXECUTION' }
  | { type: 'SET_CERTIFICATE'; payload: CalibrationCertificate }
  | { type: 'GO_TO_STEP'; payload: 1 | 2 | 3 | 4 | 5 }
  | { type: 'RESET' };
```

Provider wraps `<Shell />` in `App.tsx`. All screen components access state via `useInquiryFlow()` hook.

### 6.2 Execution Simulators

**`useExecutionSimulator(episodes, isCommitted, onComplete)`:**
- Starts `setInterval(1500ms)` when `isCommitted` becomes true and execution path is PRODUCT
- Each tick dispatches `ADVANCE_EPISODE` with next episode
- Clears interval and calls `onComplete` when all episodes done
- Returns `{ skip: () => void }` for "Skip to Results"
- Cleanup on unmount

**`useMarketSimulator(phases, isCommitted, onComplete)`:**
- Same pattern, dispatches `ADVANCE_PHASE` with next phase
- 1.5s interval per phase

Both hooks are only active on Screen 3. They read committed state from context and advance automatically.

---

## 7. Routing

```tsx
// src/App.tsx
const router = createBrowserRouter([
  {
    element: <Shell />,
    children: [
      { index: true, element: <Navigate to="/signal-feed" replace /> },
      { path: 'signal-feed', element: <SignalFeed /> },
      { path: 'configure', element: <InquiryConfig /> },
      { path: 'execute', element: <ExecutionView /> },
      { path: 'certificate', element: <CertificateView /> },
      { path: 'tier-gate', element: <TierGate /> },
    ],
  },
]);
```

Navigation guard: screens check required context state on mount. If a user navigates directly to `/certificate` without a certificate in state, redirect to `/signal-feed`.

---

## 8. Styling Architecture

### 8.1 Tailwind Configuration

```ts
// tailwind.config.ts
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        echelon: {
          bg: '#FAFBFC',
          surface: '#FFFFFF',
          border: '#E2E8F0',
          navy: '#1E3A5F',
          blue: '#2563EB',
          success: '#059669',
          warning: '#D97706',
          error: '#DC2626',
          'data-text': '#334155',
          'data-bg': '#F1F5F9',
        },
      },
      fontFamily: {
        sans: ['DM Sans', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      maxWidth: {
        container: '1200px',
      },
      keyframes: {
        fadeSlideUp: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulse: {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(30, 58, 95, 0.4)' },
          '50%': { boxShadow: '0 0 0 6px rgba(30, 58, 95, 0)' },
        },
        bgPulse: {
          '0%, 100%': { backgroundColor: 'rgb(241 245 249)' },
          '50%': { backgroundColor: 'rgb(226 232 240)' },
        },
      },
      animation: {
        'fade-slide-up': 'fadeSlideUp 150ms ease-out forwards',
        'step-pulse': 'pulse 2s ease-in-out infinite',
        'bg-pulse': 'bgPulse 600ms ease-in-out',
      },
    },
  },
  plugins: [],
};
```

### 8.2 Global CSS (`index.css`)

```css
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  @apply bg-echelon-bg font-sans text-slate-800 antialiased;
}

/* Typewriter effect for hash reveal */
.hash-reveal {
  overflow: hidden;
  white-space: nowrap;
  border-right: 2px solid #1E3A5F;
  animation: typewriter 2s steps(64) forwards, blink 0.75s step-end infinite;
}

@keyframes typewriter {
  from { width: 0; }
  to { width: 100%; }
}

@keyframes blink {
  50% { border-color: transparent; }
}

/* Score count-up uses JS, not CSS */
```

### 8.3 Component Style Patterns

| Pattern | Implementation |
|---------|---------------|
| Card | `bg-white rounded-lg border border-echelon-border shadow-sm` |
| Section heading | `font-semibold uppercase tracking-wider text-sm text-echelon-navy` |
| Data label | `text-xs text-slate-500 uppercase tracking-wider` |
| Data value | `font-mono text-echelon-data-text` |
| Code block | `bg-echelon-data-bg rounded-md p-4 font-mono text-sm` |
| Primary button | `bg-echelon-navy text-white rounded-md px-6 py-2.5 font-medium hover:bg-opacity-90 transition-colors` |
| Badge (execution path) | `text-xs font-medium px-2 py-0.5 rounded border` |
| Pill (criteria ID) | `bg-echelon-data-bg text-echelon-data-text text-xs px-2.5 py-1 rounded-full font-mono` |

---

## 9. Utility Functions

### `src/utils/hash.ts`
```tsx
// Pre-computed hashes. No real SHA-256 computation.
export function getCommitmentHash(templateId: string): string
export function truncateHash(hash: string, chars?: number): string
```

### `src/utils/canonical.ts`
```tsx
// Canonical JSON display (sorted keys, minified)
export function toCanonicalDisplay(obj: CommitmentTarget): string
// Pretty JSON display (sorted keys, formatted)
export function toPrettyDisplay(obj: CommitmentTarget): string
```

Uses `JSON.stringify(obj, Object.keys(obj).sort(), 2)` for pretty, `JSON.stringify(obj, Object.keys(obj).sort())` for canonical (with recursive key sorting via a replacer function).

### `src/utils/format.ts`
```tsx
export function relativeTime(isoTimestamp: string): string  // "3m ago"
export function formatScore(score: number): string           // "0.9091"
export function formatPercentage(value: number): string      // "95%"
```

---

## 10. Animation Specifications

| Animation | Trigger | Implementation | Duration |
|-----------|---------|----------------|----------|
| Signal card entry | Page load | CSS `animation: fadeSlideUp` with staggered `animation-delay` | 150ms + index*200ms |
| Step pulse | Current step | CSS `animation: stepPulse` infinite | 2s loop |
| Page transition | Route change | CSS `animation: fadeSlideUp` on page wrapper | 150ms |
| Hash reveal | Commit click | CSS `width: 0 → 100%` with `steps(64)` on monospace element | 2s |
| Background pulse | Commit click | CSS `animation: bgPulse` on canonical bytes container | 600ms |
| Score count-up | Certificate load | JS `requestAnimationFrame` with ease-out interpolation | 1s |
| Episode row entry | Timer tick | CSS `animation: fadeSlideUp` | 150ms |
| Progress bar | Episode advance | CSS `transition: width 300ms ease-out` | 300ms |
| Bundle file appear | Episode complete | CSS `animation: fadeSlideUp` | 150ms |
| Certificate Ready banner | Execution complete | CSS `animation: fadeSlideUp` after 500ms delay | 150ms |

---

## 11. Deployment Architecture

### Vercel Configuration

```json
// vercel.json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

SPA fallback rewrite ensures all routes resolve to `index.html` for client-side routing.

### Build

```json
// package.json scripts
{
  "dev": "vite",
  "build": "tsc && vite build",
  "preview": "vite preview"
}
```

### Font Loading Strategy

```html
<!-- index.html <head> -->
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
```

`font-display: swap` is default for Google Fonts — text renders immediately with system font, swaps when custom font loads.

---

## 12. Security Considerations

Minimal attack surface — pure static SPA with no user input processing, no backend, no authentication, no PII.

| Concern | Mitigation |
|---------|------------|
| XSS via mock data | All data is static TypeScript imports, not user-generated |
| Dependency supply chain | Minimal deps (React, react-router, Tailwind dev only) |
| Content injection | No `dangerouslySetInnerHTML`, no dynamic HTML |

---

## 13. Testing Strategy

### Unit Tests (Vitest)
- Utility functions: `toCanonicalDisplay`, `toPrettyDisplay`, `relativeTime`, `formatScore`, `truncateHash`
- Reducer: verify all `InquiryAction` types produce correct state transitions
- `generateBundleFiles`: correct file lists for PRODUCT and MARKET paths

### Component Tests (Vitest + React Testing Library)
- `StepIndicator`: renders correct visual states for each step
- `ClassSelector`: pre-selects suggested class, filters on click
- `CommitmentHash`: toggles between pretty/canonical, shows hash on commit
- `CriteriaBreakdown`: renders correct colours for score thresholds
- `TierBadge`: renders correct tier colour

### Smoke Tests
- Navigation flow: signal → configure → execute → certificate → tier-gate
- Reset: "Restart Demo" clears state and returns to signal feed
- Guard: direct navigation to `/certificate` redirects to `/signal-feed`

---

## 14. File Inventory

| Path | Purpose | Complexity |
|------|---------|------------|
| `src/main.tsx` | React root mount | Trivial |
| `src/App.tsx` | Router + InquiryFlowProvider | Low |
| `src/types/signal.ts` | Signal, InquiryClass, ExecutionPath | Trivial |
| `src/types/inquiry.ts` | TheatreTemplate, CommitmentTarget | Trivial |
| `src/types/execution.ts` | Episode, MarketPhase, BundleFileEntry | Trivial |
| `src/types/certificate.ts` | CalibrationCertificate | Trivial |
| `src/data/signals.ts` | 8 mock signals | Low (data entry) |
| `src/data/templates.ts` | 8 templates + episodes + phases + commitment targets | Medium (data entry) |
| `src/data/certificates.ts` | Pre-built certificates | Low (data entry) |
| `src/hooks/useInquiryFlow.ts` | Context + reducer + provider | Medium |
| `src/hooks/useExecutionSimulator.ts` | Timer-driven episode advancement | Medium |
| `src/hooks/useMarketSimulator.ts` | Timer-driven phase advancement | Low (mirrors episode sim) |
| `src/utils/hash.ts` | Hash lookup + truncation | Trivial |
| `src/utils/canonical.ts` | Canonical/pretty JSON formatting | Low |
| `src/utils/format.ts` | Time/score formatting | Trivial |
| `src/utils/bundleFiles.ts` | Evidence bundle file list generator | Low |
| `src/components/layout/Shell.tsx` | App shell with Outlet | Low |
| `src/components/layout/StepIndicator.tsx` | 5-step horizontal stepper | Medium |
| `src/components/layout/Header.tsx` | Wordmark header | Trivial |
| `src/components/signal-feed/SignalFeed.tsx` | Screen 1 page | Medium |
| `src/components/signal-feed/SignalCard.tsx` | Signal list item | Medium |
| `src/components/signal-feed/SourceBadge.tsx` | Jurisdiction badge | Trivial |
| `src/components/inquiry-config/InquiryConfig.tsx` | Screen 2 page | Medium |
| `src/components/inquiry-config/ClassSelector.tsx` | 5 inquiry class cards | Medium |
| `src/components/inquiry-config/TemplatePanel.tsx` | Template list/cards | Medium |
| `src/components/inquiry-config/ParameterCommit.tsx` | Criteria + pins display + commit button | Medium |
| `src/components/inquiry-config/CommitmentHash.tsx` | Pretty/canonical toggle + hash reveal | High |
| `src/components/execution/ExecutionView.tsx` | Screen 3 page (path switcher) | Low |
| `src/components/execution/EpisodeProgress.tsx` | PRODUCT episode list + progress bar | High |
| `src/components/execution/MarketLifecycle.tsx` | MARKET phase list | Medium |
| `src/components/execution/ScoreStream.tsx` | Running composite score | Low |
| `src/components/execution/EvidenceBundleBuilder.tsx` | Tree visualisation | High |
| `src/components/certificate/CertificateView.tsx` | Screen 4 page | Medium |
| `src/components/certificate/CriteriaBreakdown.tsx` | Bar chart breakdown | Medium |
| `src/components/certificate/ReproducibilityPins.tsx` | Version + crypto chain | Low |
| `src/components/certificate/HashVerificationPanel.tsx` | 3 verification checks | Medium |
| `src/components/certificate/TierBadge.tsx` | Coloured tier badge | Trivial |
| `src/components/tier-gate/TierGate.tsx` | Screen 5 page | Medium |
| `src/components/tier-gate/ModelPoolMap.tsx` | 3-column tier cards | Medium |
| `src/components/tier-gate/ConstraintYieldingIndicator.tsx` | Callout box | Low |

**Total:** ~38 files. ~30 component files, 3 hook files, 3 data files, 4 utility files, 4 type files.

---

## 15. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Mock data volume (11 episodes × 5 criteria each) | Spec provides exact data — transcribe directly |
| Hash consistency across screens | Single source of truth: `COMMITMENT_TARGETS` map, referenced by `template_id` |
| Timer cleanup on unmount / navigation | `useEffect` cleanup in simulator hooks |
| Canonical JSON key sorting (recursive) | Custom `sortKeysDeep` utility, tested |
| Typewriter animation on variable-length hashes | Use `ch` units in CSS steps, or calculate character count at render |

---

## 16. Future Considerations

This app serves as the UI reference for Cycle-035 (Theatre Command UI). Design patterns, component structure, and visual language established here will migrate to the production frontend. Key patterns to preserve:

- Evidence bundle tree visualisation → reusable component
- Commitment hash panel → production use with real SHA-256
- Tier badge system → shared design token
- Step indicator pattern → multi-phase workflow pattern

No technical debt anticipated — this is a disposable demo with clean patterns.
