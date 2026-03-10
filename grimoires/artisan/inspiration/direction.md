# Design Direction — Echelon

## Core Vision

**Institutional intelligence, not crypto dashboard.** Echelon is a light-theme prediction market platform that feels like a Bloomberg terminal reimagined by someone who understands negative space. Data-dense where density serves comprehension. Breathing where breathing serves parsing. Purple as the verb color — the thing you act on. Green as the alive color — the thing that's working. Orange as the attention color — the thing that needs you. Everything else is grey, and the grey has a whisper of the brand in it.

The palette is oklch-native. Every derived shade maintains perceptual uniformity by mathematical guarantee. No handpicked hex values that break when you derive tints.

## We Want

| Attribute | Description | Source |
|-----------|-------------|--------|
| Off-white background | Not pure white (too bright for sustained data reading), not cream (too casual). Cool neutral with brand undertone at hue 265. | Kree8 #f5f5f5, Parcl #fafafa — split the difference |
| Purple-as-action | Primary CTAs, active nav, focus rings, selected states. Purple is the highest-chroma element on any surface. | Pyth purple dominance, adapted for light |
| Inter + JetBrains Mono | Sans for UI, mono for data. No third typeface. Variable weight 300-700 for Inter. | All references use Inter. Constraint from brief |
| Card-based architecture | White cards on light grey background. Lightness delta is the elevation. | Kree8, Parcl, Pyth — unanimous |
| Stat cards with large numbers | KPI display: large mono numeral + small label + optional trend indicator | Pyth, Parcl — data platform standard |
| Hairline structural borders | 1px borders at low opacity, not decorative. Borders encode structure. | Kree8 subtlety, Pyth minimalism |
| Context-dependent density | Dashboard/Analytics/Fleet = packed. Theatres/Verify/Investigations = spacious. | Pyth density + Kree8 breathing |
| Status color system | Green/yellow/red/blue/purple map to success/warning/danger/info/paradox. Darkened for WCAG AA on light. | Brief constraint, adapted from existing |
| Monospace for all numerics | Tabular figures, right-aligned in data columns. JetBrains Mono. | Bloomberg density concept |
| Zero decorative animation | Every animation communicates state change or computation. Nothing moves for beauty alone. | Alexander principle: Simplicity & Inner Calm |

## We Avoid

| Attribute | Description | Why |
|-----------|-------------|-----|
| Dark backgrounds | Slate-950 palette, dark terminals, charcoal cards | Tobias explicitly rejected. Retired. |
| Glow effects | Box-shadow glows, neon borders, halo animations | Crypto dashboard cliche. Chrome louder than data. |
| Gradient backgrounds | Hero gradients, gradient borders, gradient cards | Decorative. Violates Color is Information. |
| Glassmorphism | Blur effects, transparent overlays, frosted glass | Decorative elevation. Structure should come from borders and lightness delta, not blur. |
| Teal/cyan as brand color | The old #22D3EE accent | Retired with the dark palette. Purple replaces it. |
| Generic SaaS stat cards | Oversized cards with icons and percentage badges | Parcl/Pyth show density is possible without bloat |
| "Coming Soon" placeholders | Empty pages with placeholder text | Design failure. Every surface gets a designed empty state. |
| Floating orbs / particles | Decorative motion in backgrounds or headers | Layer Violation. Animation channel reserved for state. |
| HSL color definitions | Any color defined in hsl() or hex without oklch equivalent | Perceptual Lie. oklch or nothing. |

## Key Tensions (Resolved)

| Tension | Resolution | Principle |
|---------|------------|-----------|
| Background warmth (cool vs warm) | Cool neutral at hue 265 — whisper of purple-blue in the grey. Accent colors provide warmth. | Color is Information — background recedes |
| Density (spacious vs packed) | Context-dependent. Dense for operational pages, spacious for transactional pages. | Alternating Repetition — rhythm encodes purpose |
| Elevation (shadows vs flat) | Lightness delta + hairline borders. Shadows only for hover states and overlays. | Thick Boundaries — structural, not decorative |
| Purple weight (dominant vs subtle) | Primary brand accent for actions. Not background, not decoration. | Strong Centers — highest contrast = act here |
| Orange role (status vs accent) | Dual purpose: warm UI accent AND attention/featured indicator. Not a status color replacement. | Levels of Scale — serves at multiple scales |

## Priority Rules

When attributes conflict:
1. **Data legibility wins over aesthetic preference.** If a color choice makes data harder to read, the data wins.
2. **Structure before material.** Get the layout right before touching color. Get composition right before animating.
3. **WCAG AA minimum on all text.** No exceptions. Status colors must hit 4.5:1 contrast on the app background.
4. **Purple is reserved for interactive elements.** If it's not clickable or selected, it's not purple.
5. **Monospace for numbers, sans for words.** No mixing within a single data display context.

---

*Generated by /envision on 2026-03-05*
*References: pyth.network, kree8.studio, parcl.co, insights.pyth.network*
*Direction: light theme, oklch-native, purple-accent intelligence platform*
*Run /envision --refine to update*
