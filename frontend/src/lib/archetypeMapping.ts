/**
 * Archetype Mapping Layer
 *
 * Backend seed data uses named identities (MEGALODON, CARDINAL, RAVEN, VIPER, etc.)
 * while the frontend type system uses categorical archetypes (SHARK, SPY, DIPLOMAT, etc.).
 *
 * This layer maps backend identity names → frontend archetype categories until the
 * taxonomy unification prerequisite is completed in Cycle 017.
 *
 * Once unified: replace AgentArchetype type with the canonical enum and delete this file.
 */

import type { AgentArchetype } from '../types/agents';

// ── Backend identity → frontend archetype mapping ───────────────────────

const IDENTITY_TO_ARCHETYPE: Record<string, AgentArchetype> = {
  // Predator class → SHARK
  MEGALODON: 'SHARK',
  THRESHER: 'SHARK',
  HAMMERHEAD: 'SHARK',
  MAKO: 'SHARK',

  // Intelligence class → SPY
  CARDINAL: 'SPY',
  RAVEN: 'SPY',
  FALCON: 'SPY',
  OSPREY: 'SPY',

  // Diplomatic class → DIPLOMAT
  ENVOY: 'DIPLOMAT',
  ARBITER: 'DIPLOMAT',
  AMBASSADOR: 'DIPLOMAT',
  CONSUL: 'DIPLOMAT',

  // Saboteur class → SABOTEUR
  VIPER: 'SABOTEUR',
  COBRA: 'SABOTEUR',
  MAMBA: 'SABOTEUR',
  ASP: 'SABOTEUR',

  // Capital class → WHALE
  LEVIATHAN: 'WHALE',
  BEHEMOTH: 'WHALE',
  KRAKEN: 'WHALE',
  TITAN: 'WHALE',

  // Speculator class → DEGEN
  JACKAL: 'DEGEN',
  HYENA: 'DEGEN',
  COYOTE: 'DEGEN',
  VULTURE: 'DEGEN',
};

// ── Known frontend archetypes (pass-through) ────────────────────────────

const KNOWN_ARCHETYPES = new Set<string>([
  'SHARK',
  'SPY',
  'DIPLOMAT',
  'SABOTEUR',
  'WHALE',
  'DEGEN',
]);

// ── Public API ──────────────────────────────────────────────────────────

/**
 * Normalize any archetype string from the backend into a known frontend AgentArchetype.
 *
 * Handles three cases:
 * 1. Already a known frontend archetype (SHARK, SPY, etc.) → pass through
 * 2. A backend named identity (MEGALODON, CARDINAL, etc.) → map to category
 * 3. Unknown → fallback to DEGEN (most permissive default)
 */
export function normalizeArchetype(raw: string | undefined | null): AgentArchetype {
  if (!raw) return 'DEGEN';

  const upper = raw.toUpperCase().trim();

  // Already a frontend archetype
  if (KNOWN_ARCHETYPES.has(upper)) {
    return upper as AgentArchetype;
  }

  // Backend identity → frontend category
  const mapped = IDENTITY_TO_ARCHETYPE[upper];
  if (mapped) return mapped;

  // Unknown — safe fallback
  return 'DEGEN';
}

/**
 * Get the display label for an archetype.
 * Uses title case for UI presentation.
 */
export function archetypeLabel(archetype: AgentArchetype): string {
  const labels: Record<AgentArchetype, string> = {
    SHARK: 'Predator',
    SPY: 'Intelligence',
    DIPLOMAT: 'Diplomat',
    SABOTEUR: 'Saboteur',
    WHALE: 'Capital',
    DEGEN: 'Speculator',
  };
  return labels[archetype] ?? 'Unknown';
}

/**
 * Get the identity name if known, otherwise return the archetype label.
 * Useful for agent detail pages where the specific identity matters.
 */
export function identityOrArchetype(raw: string | undefined | null): string {
  if (!raw) return 'Unknown';
  const upper = raw.toUpperCase().trim();

  // If it's a known identity, return the original casing
  if (IDENTITY_TO_ARCHETYPE[upper]) {
    return raw.charAt(0).toUpperCase() + raw.slice(1).toLowerCase();
  }

  // Otherwise it's already an archetype category
  return archetypeLabel(normalizeArchetype(raw));
}
