/**
 * Feature Flag System — Echelon Cycle 017 Staged Integration
 *
 * Simple env + localStorage override system. Flags gate Cycle 017 capabilities
 * that don't have backend contracts yet. When 017 ships, flip flags on and
 * eventually remove the gates entirely.
 *
 * Priority: localStorage override > env var > default (false)
 *
 * Usage:
 *   import { isEnabled } from '../lib/featureFlags';
 *   if (isEnabled('CYCLE_017_TAO_FLOW')) { ... }
 */

// ── Flag definitions ────────────────────────────────────────────────────

export type FeatureFlag =
  | 'CYCLE_017_DEPLOYABILITY_ROUTING'   // routing_hint, review_reason_code on certificates
  | 'CYCLE_017_TAO_FLOW'               // net_inflow_24h/7d on timelines, feed ranking
  | 'CYCLE_017_REGISTRY_SCHEMA'        // query_determinism, receipt_body_required, requires_legal_review
  | 'CYCLE_017_COHERENCE_GATES'        // post-routing policy
  | 'WEBSOCKET_REALTIME';              // live WS updates (ship after REST is solid)

// ── Env var mapping ─────────────────────────────────────────────────────

const ENV_PREFIX = 'VITE_FF_';
const LS_PREFIX = 'ff_';

function envKey(flag: FeatureFlag): string {
  return `${ENV_PREFIX}${flag}`;
}

function lsKey(flag: FeatureFlag): string {
  return `${LS_PREFIX}${flag.toLowerCase()}`;
}

// ── Core check ──────────────────────────────────────────────────────────

/**
 * Check whether a feature flag is enabled.
 *
 * Resolution order:
 * 1. localStorage `ff_<flag_lowercase>` — "true" / "false" string
 * 2. Vite env var `VITE_FF_<FLAG>` — "true" / "false" string
 * 3. Default: false
 */
export function isEnabled(flag: FeatureFlag): boolean {
  // 1. localStorage override (dev convenience)
  try {
    const lsValue = localStorage.getItem(lsKey(flag));
    if (lsValue === 'true') return true;
    if (lsValue === 'false') return false;
  } catch {
    // localStorage unavailable (SSR, privacy mode) — fall through
  }

  // 2. Vite env var
  const envValue = import.meta.env[envKey(flag)] as string | undefined;
  if (envValue === 'true') return true;
  if (envValue === 'false') return false;

  // 3. Default off
  return false;
}

// ── Dev helpers ──────────────────────────────────────────────────────────

/**
 * Override a flag via localStorage (for dev/testing).
 * Pass `null` to clear the override and fall back to env var.
 */
export function setFlagOverride(flag: FeatureFlag, value: boolean | null): void {
  try {
    if (value === null) {
      localStorage.removeItem(lsKey(flag));
    } else {
      localStorage.setItem(lsKey(flag), String(value));
    }
  } catch {
    // localStorage unavailable
  }
}

/**
 * List all flags with their current resolved values.
 * Useful for debug panels.
 */
export function getAllFlags(): Record<FeatureFlag, boolean> {
  const flags: FeatureFlag[] = [
    'CYCLE_017_DEPLOYABILITY_ROUTING',
    'CYCLE_017_TAO_FLOW',
    'CYCLE_017_REGISTRY_SCHEMA',
    'CYCLE_017_COHERENCE_GATES',
    'WEBSOCKET_REALTIME',
  ];

  return Object.fromEntries(flags.map((f) => [f, isEnabled(f)])) as Record<FeatureFlag, boolean>;
}
