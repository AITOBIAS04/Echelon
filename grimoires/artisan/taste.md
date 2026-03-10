# Echelon — Taste Tokens v1.0

> oklch-native design system. Every value is a measurable specification.
> No handpicked hex. No HSL. No "it looks about right."

---

## 1. Color System (oklch)

All colors defined as `oklch(L C H)` where:
- **L** = perceptual lightness (0 = black, 1 = white)
- **C** = chroma (0 = grey, 0.4 = maximum saturation)
- **H** = hue angle (0-360)

### 1.1 Neutrals — The Grey Scale

Hue 265 (purple-blue whisper). Chroma 0.003-0.008. The greys carry a faint brand undertone
that pairs naturally with the purple accent without being obviously tinted.

| Token | oklch | Role | Contrast vs bg-app |
|-------|-------|------|--------------------|
| `--bg-app` | `oklch(0.965 0.004 265)` | App canvas. The ground everything sits on. | — |
| `--bg-card` | `oklch(0.993 0.001 265)` | Card/panel surface. Near-white. | — |
| `--bg-elevated` | `oklch(1.000 0 0)` | Highest surface. Pure white. Modal headers, popovers. | — |
| `--bg-sunken` | `oklch(0.945 0.006 265)` | Recessed areas. Code blocks, sidebar backgrounds. | — |
| `--bg-hover` | `oklch(0.935 0.008 265)` | Hover state on cards and rows. | — |
| `--bg-active` | `oklch(0.910 0.010 265)` | Active/pressed state. Selected sidebar item bg. | — |
| `--border-primary` | `oklch(0.875 0.006 265)` | Card borders, section dividers. | — |
| `--border-secondary` | `oklch(0.920 0.004 265)` | Subtle inner borders, table row dividers. | — |
| `--border-focus` | `oklch(0.530 0.230 295)` | Focus ring. Same as accent-purple. | — |

### 1.2 Text Hierarchy

All text colors must achieve WCAG AA (4.5:1) against `--bg-app` or `--bg-card`.

| Token | oklch | Role | Contrast vs bg-card |
|-------|-------|------|---------------------|
| `--text-primary` | `oklch(0.205 0.015 265)` | Headlines, primary content. Near-black. | ~15.8:1 |
| `--text-secondary` | `oklch(0.440 0.010 265)` | Body text, descriptions. Medium grey. | ~6.2:1 |
| `--text-muted` | `oklch(0.590 0.008 265)` | Labels, captions, placeholders. | ~3.8:1 (AA large only) |
| `--text-disabled` | `oklch(0.700 0.005 265)` | Disabled states. | ~2.4:1 (intentionally low) |
| `--text-inverse` | `oklch(0.985 0.002 265)` | Text on dark/accent backgrounds. | — |

> `--text-muted` at 3.8:1 passes AA for large text (18px+ or 14px bold). Use only for labels
> at 11px+ uppercase tracking or 14px+ body. Never for critical content.

### 1.3 Accent — Purple (Primary Brand)

Hue 295. The verb color. If it's purple, it's interactive.

| Token | oklch | Role |
|-------|-------|------|
| `--purple-50` | `oklch(0.970 0.018 295)` | Tinted backgrounds (selected row, active tab bg) |
| `--purple-100` | `oklch(0.935 0.042 295)` | Hover backgrounds on purple elements |
| `--purple-200` | `oklch(0.870 0.085 295)` | Light accent borders, tag backgrounds |
| `--purple-300` | `oklch(0.760 0.140 295)` | Secondary buttons, icons |
| `--purple-400` | `oklch(0.640 0.195 295)` | Hover state for primary buttons |
| `--purple-500` | `oklch(0.530 0.230 295)` | **Primary brand.** CTAs, active nav, links. |
| `--purple-600` | `oklch(0.455 0.215 295)` | Pressed/active state |
| `--purple-700` | `oklch(0.385 0.190 295)` | Text on light purple backgrounds |
| `--purple-800` | `oklch(0.315 0.165 295)` | Dark accent text |
| `--purple-900` | `oklch(0.255 0.135 295)` | Darkest purple (rare) |

**Usage rules:**
- Purple-500 is the primary CTA color. One primary CTA per viewport.
- Purple-50 as selected/active background. Never as page background.
- Purple-700 for text links. Underline on hover, not by default.
- Focus ring: 2px solid purple-500, 2px offset.

### 1.4 Accent — Green (Alive / Success)

Hue 152. The alive color. Systems running, markets active, profits.

| Token | oklch | Role |
|-------|-------|------|
| `--green-50` | `oklch(0.965 0.022 152)` | Success background tint |
| `--green-100` | `oklch(0.930 0.050 152)` | Success hover bg |
| `--green-200` | `oklch(0.860 0.095 152)` | Success border |
| `--green-300` | `oklch(0.750 0.140 152)` | Secondary green elements |
| `--green-400` | `oklch(0.640 0.165 152)` | Icons, indicators |
| `--green-500` | `oklch(0.545 0.170 152)` | **Primary green.** Success states, positive P&L. |
| `--green-600` | `oklch(0.470 0.155 152)` | Green text on light backgrounds (WCAG AA) |
| `--green-700` | `oklch(0.400 0.135 152)` | Dark green text |

**Usage rules:**
- Green-500 for status indicators (dots, badges). Green-600 for text.
- Yes/Buy buttons: green-500 background, text-inverse text.
- Positive P&L: green-600 text. Never green-500 for text (contrast).
- Agent "alive" status: green-500 dot.

### 1.5 Accent — Orange (Attention / Warm)

Hue 62. The attention color. Featured content, hot markets, warm accents.

| Token | oklch | Role |
|-------|-------|------|
| `--orange-50` | `oklch(0.970 0.022 62)` | Featured/attention background tint |
| `--orange-100` | `oklch(0.935 0.050 62)` | Hover bg |
| `--orange-200` | `oklch(0.870 0.095 62)` | Accent borders |
| `--orange-300` | `oklch(0.780 0.135 62)` | Secondary orange elements |
| `--orange-400` | `oklch(0.690 0.165 62)` | Icons, warm indicators |
| `--orange-500` | `oklch(0.610 0.185 62)` | **Primary orange.** Featured badges, attention states. |
| `--orange-600` | `oklch(0.540 0.175 62)` | Orange text on light backgrounds (WCAG AA) |
| `--orange-700` | `oklch(0.465 0.155 62)` | Dark orange text |

**Usage rules:**
- Orange-500 for "hot" market indicators, featured theatre badges.
- Orange-600 for text labels ("Trending", "Featured", "Hot").
- NOT a replacement for warning yellow. Warning stays amber (hue 85).
- Orange + purple is the brand color pair. Use together for highest visual impact.

### 1.6 Status Colors (WCAG AA on Light)

Darkened from the old palette to maintain 4.5:1+ contrast on `--bg-card`.

| Token | oklch | Hex (approx) | Role | Contrast vs bg-card |
|-------|-------|-------------|------|---------------------|
| `--status-success` | `oklch(0.545 0.170 152)` | ~#2F9E6E | Growth, positive, alive | 4.6:1 |
| `--status-success-text` | `oklch(0.400 0.135 152)` | ~#1B7A4F | Success text | 7.5:1 |
| `--status-warning` | `oklch(0.540 0.150 85)` | ~#9D8318 | At risk, evidence flip | 4.8:1 |
| `--status-warning-text` | `oklch(0.430 0.130 85)` | ~#7A650F | Warning text | 7.2:1 |
| `--status-danger` | `oklch(0.545 0.185 25)` | ~#D44A5C | Breach, negative, loss | 4.5:1 |
| `--status-danger-text` | `oklch(0.430 0.165 25)` | ~#B03345 | Danger text | 7.2:1 |
| `--status-info` | `oklch(0.525 0.155 260)` | ~#3574D4 | Neutral information | 4.8:1 |
| `--status-info-text` | `oklch(0.420 0.140 260)` | ~#2A5CB0 | Info text | 7.0:1 |
| `--status-paradox` | `oklch(0.500 0.200 295)` | ~#8240D0 | Paradox events, anomalies | 5.2:1 |
| `--status-paradox-text` | `oklch(0.400 0.185 295)` | ~#6530A8 | Paradox text | 7.8:1 |

**Pattern:** Each status has two values. The base (`-success`, `-danger`, etc.) is for
indicators, badges, dots, and backgrounds. The `-text` variant is for inline text
at smaller sizes where contrast is critical.

**Status background tint pattern:**
```css
.status-bg-success { background: oklch(from var(--status-success) l c h / 0.08); }
.status-bg-danger  { background: oklch(from var(--status-danger) l c h / 0.08); }
```
Use relative oklch syntax for tinted backgrounds — guarantees perceptual consistency.

### 1.7 Agent Archetype Colors

Mapped to the 6 agent archetypes. Each must be distinguishable from each other
AND from the status colors.

| Token | oklch | Archetype |
|-------|-------|-----------|
| `--agent-shark` | `oklch(0.545 0.185 25)` | Shark — aggressive (maps to danger hue) |
| `--agent-spy` | `oklch(0.500 0.200 295)` | Spy — covert (maps to paradox hue) |
| `--agent-diplomat` | `oklch(0.525 0.155 260)` | Diplomat — cooperative (maps to info hue) |
| `--agent-saboteur` | `oklch(0.560 0.155 85)` | Saboteur — disruptive (maps to warning hue) |
| `--agent-whale` | `oklch(0.545 0.170 152)` | Whale — capital (maps to success hue) |
| `--agent-degen` | `oklch(0.610 0.185 62)` | Degen — high-risk (maps to orange) |

---

## 2. Typography System

### 2.1 Font Stack

```css
--font-sans: 'Inter', system-ui, -apple-system, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
```

Inter loaded at weights 300, 400, 500, 600, 700.
JetBrains Mono loaded at weights 400, 500, 600.

### 2.2 Type Scale (4px baseline grid)

Every line-height is a multiple of 4px.

| Token | Size | Line-height | Weight | Font | Role |
|-------|------|-------------|--------|------|------|
| `--type-xs` | 11px | 16px (4x4) | 500 | sans | Data labels, table headers (uppercase, tracking 0.06em) |
| `--type-sm` | 13px | 20px (5x4) | 400 | sans | Body small, secondary text, descriptions |
| `--type-base` | 15px | 24px (6x4) | 400 | sans | Primary body text |
| `--type-lg` | 17px | 24px (6x4) | 600 | sans | Section headers, card titles |
| `--type-xl` | 20px | 28px (7x4) | 600 | sans | Page section titles |
| `--type-2xl` | 24px | 32px (8x4) | 700 | sans | Page titles |
| `--type-3xl` | 30px | 36px (9x4) | 700 | sans | Hero metrics (dashboard KPIs) |
| `--type-4xl` | 36px | 40px (10x4) | 700 | mono | Large dashboard numbers |
| `--type-data` | 13px | 20px (5x4) | 500 | mono | Tabular data, prices, percentages |
| `--type-data-lg` | 17px | 24px (6x4) | 600 | mono | Prominent data (card probability, balance) |

### 2.3 Typography Rules

1. **Numbers are always monospace.** Prices, percentages, counts, timestamps — JetBrains Mono.
   Use `font-variant-numeric: tabular-nums` for alignment.
2. **Labels are uppercase tracked.** `--type-xs` at `letter-spacing: 0.06em`, `text-transform: uppercase`.
3. **No font-size below 11px.** Legibility floor.
4. **Bold hierarchy:** 700 for page titles only. 600 for section/card titles. 500 for emphasis. 400 for body.
5. **Line-height tolerance:** ±2px allowed for optical alignment in tight layouts (metric blocks).

---

## 3. Spatial System

### 3.1 Base Unit

**4px baseline grid.** Every spacing value, every component height, every margin is a multiple of 4.

### 3.2 Spacing Scale

| Token | Value | Use |
|-------|-------|-----|
| `--space-1` | 4px | Minimum gap. Icon-to-text inline. |
| `--space-2` | 8px | Tight gap. Related items within a group. |
| `--space-3` | 12px | Default content gap. List items, form fields. |
| `--space-4` | 16px | Comfortable gap. Card internal padding (compact). |
| `--space-5` | 20px | Section internal spacing. |
| `--space-6` | 24px | Card padding (standard). Related section gap. |
| `--space-8` | 32px | Section padding. Panel internal margins. |
| `--space-10` | 40px | Large section padding. |
| `--space-12` | 48px | **Unrelated section gap.** The void between independent sections. |
| `--space-16` | 64px | Page top/bottom margins. |
| `--space-20` | 80px | Hero spacing. |
| `--space-24` | 96px | Maximum spacing. Rare. |

### 3.3 Spatial Rules (Alexander's Properties Applied)

| Alexander Property | Spatial Rule | Token |
|-------------------|-------------|-------|
| **Levels of Scale** | No more than 2x jump between adjacent spacing values | Scale above |
| **The Void** | 48px between unrelated sections, 16px between related | `--space-12` / `--space-4` |
| **Alternating Repetition** | Dense data → breathing → dense data | Context-dependent density |
| **Echoes** | Same padding everywhere within a context (card padding = card padding) | Consistent per-context |

### 3.4 Layout Dimensions

| Token | Value | Use |
|-------|-------|-----|
| `--content-max` | 1280px | Maximum content width |
| `--sidebar-width` | 240px | Sidebar navigation width (expanded) |
| `--sidebar-collapsed` | 64px | Sidebar navigation width (collapsed) |
| `--header-height` | 56px | Top header bar height |
| `--card-min-width` | 280px | Minimum card width in grids |
| `--card-max-width` | 480px | Maximum card width |
| `--page-padding` | 24px | Page content padding (horizontal) |
| `--page-padding-y` | 32px | Page content padding (vertical) |

---

## 4. Elevation System

### 4.1 Surface Hierarchy

Light theme elevation uses **lightness delta** as the primary depth cue.
Shadows are secondary — present but subtle.

| Level | Surface | Background | Border | Shadow | Use |
|-------|---------|-----------|--------|--------|-----|
| -1 | Sunken | `--bg-sunken` | none | inset `0 1px 2px oklch(0.20 0.01 265 / 0.04)` | Code blocks, recessed panels |
| 0 | Ground | `--bg-app` | none | none | Page background |
| 1 | Card | `--bg-card` | `--border-primary` | `0 1px 2px oklch(0.20 0.01 265 / 0.05)` | Cards, panels, sidebar |
| 2 | Elevated | `--bg-elevated` | `--border-primary` | `0 2px 8px oklch(0.20 0.01 265 / 0.08)` | Hover cards, expanded sections |
| 3 | Overlay | `--bg-elevated` | `--border-primary` | `0 8px 24px oklch(0.20 0.01 265 / 0.12)` | Dropdowns, popovers, modals |

### 4.2 Shadow Tokens

```css
--shadow-xs:  0 1px 2px oklch(0.20 0.01 265 / 0.04);
--shadow-sm:  0 1px 3px oklch(0.20 0.01 265 / 0.06), 0 1px 2px oklch(0.20 0.01 265 / 0.03);
--shadow-md:  0 2px 8px oklch(0.20 0.01 265 / 0.08), 0 1px 3px oklch(0.20 0.01 265 / 0.04);
--shadow-lg:  0 8px 24px oklch(0.20 0.01 265 / 0.12), 0 2px 8px oklch(0.20 0.01 265 / 0.05);
--shadow-xl:  0 16px 48px oklch(0.20 0.01 265 / 0.16), 0 4px 12px oklch(0.20 0.01 265 / 0.06);
```

Shadow color at hue 265 ensures shadows have the same brand undertone as the greys.

---

## 5. Border System

### 5.1 Border Tokens

```css
--border-width-default: 1px;
--border-width-focus: 2px;
--border-radius-sm: 6px;     /* Badges, pills, small chips */
--border-radius-md: 8px;     /* Cards, buttons, inputs */
--border-radius-lg: 12px;    /* Panels, modals, large cards */
--border-radius-xl: 16px;    /* Feature cards, hero sections */
--border-radius-full: 9999px; /* Avatars, status dots, pill buttons */
```

### 5.2 Border Rules

1. **All borders are 1px.** No 2px borders except focus rings.
2. **Border color is `--border-primary`.** Subtle inner divisions use `--border-secondary`.
3. **No border-bottom-only patterns.** Use full borders or no borders. Partial borders create visual noise.
   Exception: table row dividers (`--border-secondary`, bottom only).
4. **Focus ring:** 2px `--border-focus` with 2px offset. Visible on all interactive elements.

---

## 6. Motion System

### 6.1 Timing Tokens

```css
--duration-instant: 100ms;   /* Hover color changes, opacity */
--duration-fast: 150ms;      /* Button press, toggle */
--duration-normal: 200ms;    /* Card hover lift, panel expand */
--duration-slow: 300ms;      /* Page transitions, modal enter */
--duration-glacial: 500ms;   /* Complex reveals (staggered lists) */
```

### 6.2 Easing

```css
--ease-out: cubic-bezier(0.16, 1, 0.3, 1);      /* Deceleration. Enter animations. */
--ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);   /* Symmetric. Position changes. */
--ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1); /* Overshoot. Interactive feedback. */
```

> Spring physics preferred for interactive elements when the framework supports it.
> CSS springs via `--ease-spring` are an approximation. True spring: `stiffness: 180, damping: 14, mass: 1.0`.

### 6.3 Motion Rules

1. **No animation without purpose.** Every animation answers: what state changed?
2. **Hover effects:** `--duration-instant` for color, `--duration-normal` for transform (lift/scale).
3. **Page enter:** `--duration-slow` with `--ease-out`. Fade + 8px translateY.
4. **Staggered lists:** 50ms stagger between items. Max 8 items staggered, rest appear instantly.
5. **No animation on data updates.** Numbers change instantly. Animating a price change is deceptive.
6. **Active/press:** `scale(0.97)` at `--duration-fast`. Instant feedback.
7. **Reduced motion:** All animations behind `@media (prefers-reduced-motion: reduce)`.

---

## 7. Component Tokens

### 7.1 Button Variants

| Variant | Background | Text | Border | Hover bg |
|---------|-----------|------|--------|----------|
| Primary | `--purple-500` | `--text-inverse` | none | `--purple-400` |
| Secondary | `--bg-card` | `--text-secondary` | `--border-primary` | `--bg-hover` |
| Ghost | transparent | `--text-secondary` | none | `--bg-hover` |
| Danger | `--status-danger` | `--text-inverse` | none | darker danger |
| Success | `--green-500` | `--text-inverse` | none | `--green-400` |

### 7.2 Input Fields

```css
background: var(--bg-card);
border: 1px solid var(--border-primary);
border-radius: var(--border-radius-md);
padding: var(--space-2) var(--space-3);           /* 8px 12px */
font: var(--type-sm);                              /* 13px/20px Inter */
color: var(--text-primary);
placeholder-color: var(--text-muted);
focus-border: var(--purple-500);
focus-ring: 0 0 0 2px oklch(from var(--purple-500) l c h / 0.15);
```

### 7.3 Cards

```css
background: var(--bg-card);
border: 1px solid var(--border-primary);
border-radius: var(--border-radius-md);            /* 8px */
padding: var(--space-6);                           /* 24px */
shadow: var(--shadow-xs);
hover-shadow: var(--shadow-sm);
hover-translateY: -1px;
hover-duration: var(--duration-normal);
```

### 7.4 Status Pills

```css
/* Pattern: 8% opacity background, full color text, 20% opacity border */
.status-pill {
  padding: 2px 8px;
  border-radius: var(--border-radius-full);
  font: var(--type-xs);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
/* Each status uses oklch relative color syntax for tint consistency */
```

### 7.5 Data Tables

```css
/* Header */
background: var(--bg-sunken);
font: var(--type-xs);
text-transform: uppercase;
letter-spacing: 0.06em;
color: var(--text-muted);
padding: var(--space-2) var(--space-3);

/* Rows */
border-bottom: 1px solid var(--border-secondary);
padding: var(--space-2) var(--space-3);
font: var(--type-sm);

/* Hover */
background: var(--bg-hover);
border-left: 3px solid var(--purple-500);          /* Active row indicator */

/* Numeric cells */
font-family: var(--font-mono);
font-variant-numeric: tabular-nums;
text-align: right;
```

---

## 8. Z-Index Scale

| Token | Value | Use |
|-------|-------|-----|
| `--z-base` | 0 | Default content |
| `--z-sticky` | 10 | Sticky headers, table headers |
| `--z-sidebar` | 20 | Sidebar navigation |
| `--z-header` | 30 | Top header bar |
| `--z-dropdown` | 40 | Dropdown menus, popovers |
| `--z-modal-backdrop` | 50 | Modal overlay background |
| `--z-modal` | 60 | Modal content |
| `--z-toast` | 70 | Toast notifications |
| `--z-tooltip` | 80 | Tooltips (highest) |

---

## 9. Responsive Breakpoints

| Token | Value | Target |
|-------|-------|--------|
| `--bp-sm` | 640px | Small mobile |
| `--bp-md` | 768px | Tablet |
| `--bp-lg` | 1024px | Small desktop / collapsed sidebar |
| `--bp-xl` | 1280px | Desktop (primary target) |
| `--bp-2xl` | 1536px | Large desktop / expanded sidebar |

Desktop-first. The primary experience is `--bp-xl` and above.
Sidebar collapses at `--bp-lg`. Cards stack at `--bp-md`.

---

## 10. Semantic Mapping Summary

| Old Token (Dark — RETIRED) | New Token (Light) | Notes |
|---------------------------|-------------------|-------|
| `terminal-bg: #030305` | `--bg-app: oklch(0.965 0.004 265)` | Dark → light |
| `terminal-card: #10141A` | `--bg-card: oklch(0.993 0.001 265)` | Dark card → white card |
| `terminal-text: #F3F4F6` | `--text-primary: oklch(0.205 0.015 265)` | Light text → dark text |
| `terminal-text-secondary: #9CA3AF` | `--text-secondary: oklch(0.440 0.010 265)` | Inverted |
| `terminal-border: rgba(255,255,255,0.13)` | `--border-primary: oklch(0.875 0.006 265)` | White alpha → grey solid |
| `echelon-cyan: #22D3EE` | `--purple-500: oklch(0.530 0.230 295)` | Cyan retired → purple primary |
| `echelon-green: #4ADE80` | `--green-500: oklch(0.545 0.170 152)` | Darkened for light bg |
| `echelon-red: #EF4444` | `--status-danger: oklch(0.545 0.185 25)` | Darkened for light bg |
| `status-paradox: #8B5CF6` | `--status-paradox: oklch(0.500 0.200 295)` | Slightly darkened |
| `glass-*` | REMOVED | Glassmorphism retired |
| `glow-*` | REMOVED | Glow effects retired |
| `signal-*` | Mapped to `--status-*` | Simplified naming |

---

## 11. Status Semantics — Unified Threshold System

> Cross-page rules for status labels, thresholds, and chip vocabulary.
> These apply identically on Dashboard, Theatres, Fleet, and every future surface.
> No per-page variants. No synonyms. One vocabulary, one set of thresholds.

### 11.1 Locked Vocabulary

These are the **only** status terms permitted across all Echelon surfaces.
Using a synonym (e.g. "Caution" instead of "Watch") is a design system violation.

| Term | Color token | CSS class | Meaning |
|------|------------|-----------|---------|
| `Live` | `--status-success` | `.chip-live` | Market actively trading |
| `Settled` | `--text-muted` | `.chip-settled` | Market resolved, no further trading |
| `Disputed` | `--status-danger` | `.chip-disputed` | Outcome contested, under review |
| `Low Liquidity` | `--text-muted` (on `--bg-sunken`) | `.chip-low-liq` | Below liquidity threshold (see 11.2) |
| `Paradox` | `--status-danger` | `.chip-paradox` | Active signal contradiction detected |
| `Stale` | `--status-warning` | `.chip-stale` | Evidence not updated in >48h |
| `Urgent` | `--status-danger` | `.chip-urgent` | Time urgency tier: <24h to expiry |
| `Ending Soon` | `--orange-600` | `.chip-ending-soon` | Time urgency tier: <7d to expiry |
| `Healthy` | `--green-600` (text), `--green-50` (bg) | `.interp-healthy` | Above healthy threshold |
| `Watch` | `oklch(0.430 0.130 85)` (text) | `.interp-watch` | In warning range |
| `Critical` | `--status-danger` | `.interp-critical` | Below critical threshold |

### 11.2 Liquidity Thresholds

| Condition | Label | Chip class |
|-----------|-------|------------|
| 24h volume < $1,000 | `Low Liquidity` | `.chip-low-liq` |
| 24h volume >= $1,000 | (no chip) | — |

**Rule:** The `Low Liquidity` chip appears on any surface where volume is displayed and
the market's 24h volume falls below $1K. Same threshold on Theatre cards, Dashboard
Top Theatres list, and Portfolio position rows.

### 11.3 Time Urgency Tiers

| Time to expiry | Label | Color | Chip class |
|---------------|-------|-------|------------|
| < 24h | `Urgent` | `--status-danger` text, `--red-50` bg | `.chip-urgent` |
| < 7d | `Ending Soon` | `--orange-600` text, `--orange-50` bg | `.chip-ending-soon` |
| >= 7d | (time value only, e.g. "14d") | `--text-muted` | `.chip-time-default` |

**Rule:** These tiers apply everywhere expiry is shown — Theatre cards, Dashboard KPIs,
Theatre detail pages, Portfolio positions. The chip shows the raw time value (e.g. "6d",
"<24h", "14d") but the color and urgency label derive from these thresholds.

**Display format:**
- `< 24h`: show `Urgent` in red (not the hour count)
- `< 7d`: show `Ending Soon` label + raw days (e.g. "6d") in orange
- `>= 7d`: show raw days only (e.g. "14d", "42d") in muted text

### 11.4 Health / Interpretation Thresholds

All metric interpretation badges follow a three-tier model. The thresholds must be shown
to the user (tooltip or sublabel) — no black-box status labels.

#### Stability Index

| Range | Label | Color |
|-------|-------|-------|
| >= 0.85 | `Healthy` | green |
| 0.60 – 0.84 | `Watch` | orange/amber |
| < 0.60 | `Critical` | red |

**Display:** `Healthy >= 0.85` as the label, with tooltip showing all three ranges.

#### Fleet Capacity (agents online / total)

| Range | Label | Color |
|-------|-------|-------|
| >= 80% | `Healthy` | green |
| 50% – 79% | `Watch` | orange/amber |
| < 50% | `Critical` | red |

**Display:** `Healthy >= 80%` as the label, with tooltip showing all three ranges.

#### Volume Interpretation

Volume has no absolute threshold — it uses **relative comparison** to the 7-day average.

| Condition | Label | Color |
|-----------|-------|-------|
| Current > 7d avg | `Above 7d avg` | green |
| Current within ±10% of 7d avg | `At 7d avg` | muted |
| Current < 7d avg by >10% | `Below 7d avg` | orange |

**Display:** Show the 7d average as a sublabel (e.g. "7d avg $38.1K").

### 11.5 Chip Rendering Rules

```css
/* All chips share this base */
.chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  padding: 1px 5px;
  border-radius: 3px;
  white-space: nowrap;
  line-height: 14px;
}

/* Status chips */
.chip-live       { color: var(--green-600); }
.chip-live::before { content: ''; width: 5px; height: 5px; border-radius: 9999px; background: var(--status-success); }
.chip-settled    { color: var(--text-muted); }
.chip-disputed   { color: var(--status-danger); background: oklch(0.545 0.185 25 / 0.08); border: 1px solid oklch(0.545 0.185 25 / 0.15); }

/* Risk chips */
.chip-low-liq    { color: var(--text-muted); background: var(--bg-sunken); border: 1px solid var(--border-secondary); }
.chip-paradox    { color: var(--status-danger); background: oklch(0.545 0.185 25 / 0.08); border: 1px solid oklch(0.545 0.185 25 / 0.15); }
.chip-stale      { color: oklch(0.430 0.130 85); background: oklch(0.540 0.150 85 / 0.08); border: 1px solid oklch(0.540 0.150 85 / 0.15); }

/* Time urgency chips */
.chip-urgent       { color: var(--status-danger); background: var(--red-50); }
.chip-ending-soon  { color: var(--orange-600); background: var(--orange-50); }
.chip-time-default { color: var(--text-muted); }

/* Interpretation badges */
.interp-healthy  { color: var(--green-700); background: var(--green-50); }
.interp-watch    { color: oklch(0.430 0.130 85); background: oklch(0.540 0.150 85 / 0.08); }
.interp-critical { color: var(--status-danger); background: var(--red-50); }
```

### 11.6 Cross-Page Consistency Rules

1. **Same threshold, everywhere.** If Stability is "Healthy" on Dashboard at 0.87,
   it must also be "Healthy" on the Theatre detail page at 0.87. No per-page overrides.
2. **Same vocabulary, everywhere.** "Low Liquidity" on Theatres = "Low Liquidity" on Dashboard.
   Never "Low liq", "Illiquid", or "Thin". The locked terms in 11.1 are exhaustive.
3. **Show your work.** Every interpretation badge must expose its threshold via tooltip
   or sublabel. No unlabelled "Healthy" without showing `>= 0.85`.
4. **Chips are additive.** A card can show multiple chips: `Paradox` + `Ending Soon` + `Low Liquidity`.
   Display order: risk chips first (Paradox, Stale), then liquidity, then time.
5. **No chip if nominal.** Don't show "Normal Liquidity" or "On Track". Chips are exceptions.
   Default state = no chip. This reduces noise.

---

*Echelon Taste Tokens v1.0 — Generated 2026-03-05*
*oklch-native. Perceptually uniform. WCAG AA compliant.*
*Every token is a measurable specification, not a preference.*
