# PRD: Echelon Bounded Inquiry Console

> **Version:** 1.0
> **Date:** 2026-02-28
> **Status:** DRAFT
> **Author:** AI-assisted, grounded in `Echelon_Bounded_Inquiry_Console_Spec_v1_1.md` + `Echelon_Bounded_Inquiry_Console_Patch_v1_1.md`

---

## 1. Problem Statement

Echelon's verification pipeline (Theatre lifecycle, commitment protocol, calibration certificates, tier gating) exists as backend code but has no interactive demonstration. Soju and potential partners cannot see the bounded inquiry lifecycle in action. The core thesis — "constructs must earn the trust that autonomy gives them" — remains abstract without a visual walkthrough.

> Sources: `echelon_platform_roadmap.md:9-17`, `Echelon_Bounded_Inquiry_Console_Spec_v1_1.md:6-8`

---

## 2. Vision & Mission

**Vision:** A 60-second interactive demo that makes the Echelon verification lifecycle tangible — signal arrives, inquiry is configured, construct executes, certificate is issued, tier gates routing consequences.

**Mission:** Build a standalone Vite+React+TypeScript+Tailwind application at `echelon-inquiry-console/` in the monorepo root. All data is hardcoded mock. No backend. Protocol fidelity to System Bible v13 taxonomy. Deploy as a separate Vercel site.

**Soju framing:** "This demo shows the bounded inquiry lifecycle: we commit the inquiry's evidence bounds + template + pins into a reproducible hash, run the resolution programme (replay or market), emit a calibration certificate, and then the certificate gates routing/tier consequences."

> Sources: `Echelon_Bounded_Inquiry_Console_Spec_v1_1.md:6-8`, `Echelon_Bounded_Inquiry_Console_Spec_v1_1.md:1013-1019`, confirmed by user (separate app, Vercel deploy)

---

## 3. Goals & Success Metrics

| Goal | Metric | Target |
|------|--------|--------|
| Demonstrate full lifecycle | All 5 screens navigable in sequence | 100% |
| Protocol fidelity | Inquiry classes match v13 canonical taxonomy | COUNTERFACTUAL, INVESTIGATIVE, INSPECTION, SURVEY, SCRUTINY |
| Commitment hash integrity | Hash on certificate matches hash committed in Screen 2 | Deterministic match |
| Execution path awareness | PRODUCT and MARKET paths render distinct execution views | Both paths functional |
| Deployment | Live Vercel URL shareable with Soju | Deployed and accessible |
| Zero backend dependency | All data hardcoded, runs fully offline | No API calls |

> Sources: `Echelon_Bounded_Inquiry_Console_Spec_v1_1.md:988-1011` (21 acceptance criteria)

---

## 4. User & Stakeholder Context

### Primary User: Soju (0xHoneyJar / Constructs Network)
- **Need:** See the verification lifecycle that will gate construct routing in Hounfour
- **Journey:** Open demo → see signals → configure inquiry → watch execution → inspect certificate → understand tier consequences
- **Decision context:** Evaluating Echelon as verification substrate for entire Constructs Network ecosystem

### Secondary Users
- **Potential partners / investors:** Quick visual comprehension of Echelon's value proposition
- **Internal team:** Reference implementation of UI patterns for Cycle-035 (Theatre Command UI)

> Sources: `echelon_platform_roadmap.md:22-59`

---

## 5. Functional Requirements

### 5.1 Screen 1: Signal Feed
- 8 pre-loaded mock signals with staggered load animation (200ms delay each)
- Two-column layout: signal list (60%) + detail panel (40%)
- Each signal: source icon, jurisdiction badge, headline, timestamp, confidence bar, settlement eligibility
- Detail panel: full headline, summary, source metadata, "Create Inquiry" button
- Signal sources: Companies House, SEC EDGAR, Polymarket, INPI RNE, Bank of England, GDELT, PACER, AIS Maritime

### 5.2 Screen 2: Inquiry Configuration
**Section A — Inquiry Class Selector:** 5 horizontal cards (COUNTERFACTUAL, INVESTIGATIVE, INSPECTION, SURVEY, SCRUTINY). Pre-selects class matching selected signal. Each card shows execution path badge (PRODUCT/Replay or MARKET/LMSR).

**Section B — Template Selection:** 8 templates across classes, each showing execution path, criteria count, fixture count (pass/fail), composite score, optional tags.

| Class | Template | Execution Path | Criteria | Fixtures |
|-------|----------|----------------|----------|----------|
| COUNTERFACTUAL | GLOBAL_CONFLICT_V1 | MARKET / LMSR | 4 | 6 (4p/2f) |
| INVESTIGATIVE | OSINT_COMPOSED_ORACLE_V1 | PRODUCT / Replay | 6 | 10 (6p/4f) |
| INSPECTION | ESCROW_MILESTONE_RELEASE_V1 | PRODUCT / Replay | 5 | 11 (6p/5f) |
| INSPECTION | DISTRIBUTION_WATERFALL_V1 | PRODUCT / Replay | 5 | 10 (10p/0f) |
| INSPECTION | LEDGER_RECONCILIATION_V1 | PRODUCT / Replay | 5 | 10 (10p/0f) |
| SURVEY | PRODUCT_OBSERVER_V1 | PRODUCT / Replay | 5 | 1 (1p/0f) |
| SCRUTINY | QUANT_MARKET_HYGIENE_V1 | PRODUCT / Replay | 19 | 10 (3p/7f) |
| SCRUTINY | QUANT_MARKET_PERTURBATION_HARNESS_V1 | PRODUCT / Replay | 7 | 10 (9p/1f) |

**Section C — Parameter Commitment:** Criteria IDs as pills, scoring thresholds, construct/scorer version pins. Commitment Hash Panel with Pretty/Hash bytes toggle. Commit action button adapts to execution path: "Commit Parameters (local)" for PRODUCT, "Commit + Publish (log)" for MARKET. SHA-256 hash reveals character-by-character on commit.

### 5.3 Screen 3: Construct Execution

**Path A (PRODUCT / Replay):** Two-column. Left: episode progress with per-episode criteria score dots (green/red/amber). Auto-advances 1.5s/episode. Right: evidence bundle tree building progressively.

**Path B (MARKET / LMSR):** Two-column. Left: 6 market lifecycle phases animating sequentially. Right: market evidence bundle with trade log hash, LMSR state snapshots.

Both paths: "Skip to Results" button, "Certificate Ready" banner on completion.

### 5.4 Screen 4: Certificate Issued
- Composite score (animated count-up)
- Tier badge (UNVERIFIED/BACKTESTED/PROVEN)
- Per-criteria breakdown with coloured bars
- Reproducibility Pins (Version Pins + Cryptographic Chain)
- Hash Verification Panel (commitment match, evidence chain, dataset anchoring)
- "View Raw JSON" toggle showing full certificate object

### 5.5 Screen 5: Tier Gate
- Three-column tier comparison (UNVERIFIED/BACKTESTED/PROVEN) with current tier highlighted
- Construct Journey indicator showing progress to next tier
- Constraint Yielding Gate explanation (UNVERIFIED overrides `review: skip` to `review: full`)
- "Restart Demo" button

### 5.6 Navigation
- Horizontal step indicator fixed at top (5 steps)
- Sequential forward navigation only (via completing current step)
- Back navigation to completed steps allowed

> Sources: `Echelon_Bounded_Inquiry_Console_Spec_v1_1.md:116-498`, `Echelon_Bounded_Inquiry_Console_Patch_v1_1.md` (all 6 patches)

---

## 6. Technical Requirements

### 6.1 Stack
- **Framework:** Vite + React + TypeScript + Tailwind CSS
- **Router:** react-router-dom v6
- **Animation:** CSS transitions and @keyframes only (no animation libraries)
- **Fonts:** DM Sans (headings/body), JetBrains Mono (data/hashes/JSON)
- **React:** v18.3 (per spec — not React 19 from existing frontend)

### 6.2 Design System
- **Theme:** Light mode only (mandatory)
- **Background:** `#FAFBFC`
- **Surface:** `#FFFFFF` with `1px solid #E2E8F0`
- **Primary accent:** `#1E3A5F` (deep navy)
- **Secondary accent:** `#2563EB` (electric blue)
- **Success:** `#059669` (emerald)
- **Warning:** `#D97706` (amber)
- **Error:** `#DC2626` (red)
- **Data/mono:** `#334155` on `#F1F5F9`
- **Max-width:** 1200px, centred
- **Cards:** `rounded-lg` with `shadow-sm`, no border-radius above 12px
- **Aesthetic:** "Bloomberg Terminal intelligence meets Linear's clarity" — precision-trust, institutional

### 6.3 State Management
- Single `useInquiryFlow` hook managing 5-step flow state
- `useExecutionSimulator` hook for PRODUCT/Replay timer-driven episode progression
- `useMarketSimulator` hook for MARKET/LMSR timer-driven phase progression

### 6.4 Routing
| Route | Screen |
|-------|--------|
| `/` | Redirect to `/signal-feed` |
| `/signal-feed` | Screen 1: Signal Feed |
| `/configure` | Screen 2: Inquiry Configuration |
| `/execute` | Screen 3: Construct Execution |
| `/certificate` | Screen 4: Certificate Issued |
| `/tier-gate` | Screen 5: Tier Gate |

### 6.5 Localisation
- British English throughout (colour, behaviour, organisation, etc.)
- No emojis in the UI

> Sources: `Echelon_Bounded_Inquiry_Console_Spec_v1_1.md:80-114`, `Echelon_Bounded_Inquiry_Console_Spec_v1_1.md:698-724`

---

## 7. Project Structure

```
echelon-inquiry-console/
├── index.html
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── vite.config.ts
├── vercel.json
├── public/
│   └── favicon.svg
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── index.css
│   ├── types/
│   │   ├── signal.ts
│   │   ├── inquiry.ts
│   │   ├── execution.ts
│   │   └── certificate.ts
│   ├── data/
│   │   ├── signals.ts
│   │   ├── templates.ts
│   │   └── certificates.ts
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Shell.tsx
│   │   │   ├── StepIndicator.tsx
│   │   │   └── Header.tsx
│   │   ├── signal-feed/
│   │   │   ├── SignalFeed.tsx
│   │   │   ├── SignalCard.tsx
│   │   │   └── SourceBadge.tsx
│   │   ├── inquiry-config/
│   │   │   ├── InquiryConfig.tsx
│   │   │   ├── ClassSelector.tsx
│   │   │   ├── TemplatePanel.tsx
│   │   │   ├── ParameterCommit.tsx
│   │   │   └── CommitmentHash.tsx
│   │   ├── execution/
│   │   │   ├── ExecutionView.tsx
│   │   │   ├── EpisodeProgress.tsx
│   │   │   ├── MarketLifecycle.tsx
│   │   │   ├── ScoreStream.tsx
│   │   │   └── EvidenceBundleBuilder.tsx
│   │   ├── certificate/
│   │   │   ├── CertificateView.tsx
│   │   │   ├── CriteriaBreakdown.tsx
│   │   │   ├── ReproducibilityPins.tsx
│   │   │   ├── HashVerificationPanel.tsx
│   │   │   └── TierBadge.tsx
│   │   └── tier-gate/
│   │       ├── TierGate.tsx
│   │       ├── ModelPoolMap.tsx
│   │       └── ConstraintYieldingIndicator.tsx
│   ├── hooks/
│   │   ├── useInquiryFlow.ts
│   │   ├── useExecutionSimulator.ts
│   │   └── useMarketSimulator.ts
│   └── utils/
│       ├── hash.ts
│       ├── canonical.ts
│       └── format.ts
```

> Source: `Echelon_Bounded_Inquiry_Console_Spec_v1_1.md:13-76`

---

## 8. Mock Data Requirements

### 8.1 Signals (8 total)
Pre-loaded with staggered timestamps. Each maps to a suggested inquiry class. Full signal definitions in spec Section 9.

### 8.2 Episodes
- **ESCROW_MILESTONE_RELEASE_V1:** 11 episodes (6 pass / 5 fail) with per-criteria binary scores
- **GLOBAL_CONFLICT_V1:** 6 market lifecycle phases

All other templates use generated/minimal mock data sufficient for the demo flow.

### 8.3 Commitment Targets
Pre-computed SHA-256 hashes per template. The commitment target object (dataset_hashes + template + version_pins) is displayed in both pretty and canonical formats.

### 8.4 Certificates
Pre-computed CalibrationCertificate JSON matching `echelon_certificate_schema.json` structure.

> Sources: `Echelon_Bounded_Inquiry_Console_Spec_v1_1.md:727-955`

---

## 9. Scope & Prioritisation

### In Scope (MVP)
- All 5 screens with full navigation
- 8 mock signals with class mapping
- PRODUCT/Replay execution path (episode-by-episode scoring with evidence bundle)
- MARKET/LMSR execution path (lifecycle phase view)
- Commitment hash panel with Pretty/Hash bytes toggle
- Certificate with criteria breakdown, reproducibility pins, hash verification
- Tier Gate with constraint yielding explanation
- Light theme, DM Sans + JetBrains Mono typography
- CSS-only animations (no libraries)
- Vercel deployment configuration

### Out of Scope
- Backend integration or real API calls
- Real SHA-256 computation (pre-computed fake hashes, displayed with character reveal)
- Dark mode
- Mobile-optimised layouts (should not break, but not a priority)
- Internationalisation
- Analytics or tracking
- User authentication
- Episode data for templates beyond ESCROW_MILESTONE_RELEASE_V1 and GLOBAL_CONFLICT_V1 (other templates can use generated/minimal data)

---

## 10. Risks & Dependencies

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Font loading (DM Sans, JetBrains Mono) | Low | Medium | Use Google Fonts CDN with preconnect |
| Taxonomy drift from System Bible | Low | High | v13 canonical taxonomy locked in spec patch v1.1 |
| Spec ambiguity on remaining template episodes | Medium | Low | Generate minimal data — only ESCROW and GLOBAL_CONFLICT need full episode sets |
| Vercel deployment config | Low | Low | Standard Vite SPA deployment with vercel.json |

### External Dependencies
- None. Fully self-contained with mock data.

---

## 11. Acceptance Criteria

1. All 5 screens render and are navigable in sequence
2. Signal feed shows 8 mock signals with staggered load animation
3. Selecting a signal pre-selects the matching inquiry class (v13 canonical taxonomy)
4. All 5 inquiry classes are selectable and filter the template list
5. Each template card shows execution path badge (PRODUCT / Replay or MARKET / LMSR)
6. Commitment hash panel shows normative hash target object with Pretty/Hash bytes toggle
7. "Commit Parameters" switches to canonical view and reveals SHA-256 hash character-by-character
8. PRODUCT path: execution screen auto-advances episodes on 1.5s timer
9. MARKET path: execution screen auto-advances lifecycle phases on 1.5s timer
10. Evidence bundle tree builds progressively as episodes/phases complete
11. Certificate shows correct composite score and per-criteria breakdown
12. Hash Verification Panel shows commitment hash match, evidence chain integrity, and dataset anchoring
13. Commitment hash on certificate matches the one shown in Screen 2
14. Tier Gate shows all 3 tiers with current tier highlighted
15. Constraint Yielding Gate explanation is present
16. "Restart Demo" returns to Screen 1 with state cleared
17. Light theme throughout, no dark mode
18. All text uses British spelling (colour, behaviour, organisation, etc.)
19. No emojis anywhere in the UI
20. JetBrains Mono for all hashes, scores, JSON, and technical data
21. DM Sans for all headings and body text

> Source: `Echelon_Bounded_Inquiry_Console_Spec_v1_1.md:988-1011`

---

## 12. Source Tracing

| Section | Primary Sources |
|---------|----------------|
| Problem Statement | `echelon_platform_roadmap.md:9-17` |
| Vision | `Echelon_Bounded_Inquiry_Console_Spec_v1_1.md:6-8` |
| Inquiry Classes | `Echelon_Bounded_Inquiry_Console_Patch_v1_1.md:26-33` (v13 taxonomy) |
| Template Library | `Echelon_Bounded_Inquiry_Console_Patch_v1_1.md:57-68` |
| Commitment Hash | `Echelon_Bounded_Inquiry_Console_Patch_v1_1.md:150-219` |
| Screen Specs | `Echelon_Bounded_Inquiry_Console_Spec_v1_1.md:116-498` |
| Mock Data | `Echelon_Bounded_Inquiry_Console_Spec_v1_1.md:727-955` |
| Design System | `Echelon_Bounded_Inquiry_Console_Spec_v1_1.md:80-114` |
| Type Definitions | `Echelon_Bounded_Inquiry_Console_Spec_v1_1.md:501-629` |
| Tier Rules | `echelon_cycle_031.md:263-304` |
| Project Location | User confirmed: separate app in monorepo root |
| Deployment | User confirmed: separate Vercel site |
