import type { CommitmentTarget } from '../types/inquiry';

/**
 * Recursively sort all keys in an object for deterministic serialisation.
 */
function sortKeysDeep(obj: unknown): unknown {
  if (Array.isArray(obj)) {
    return obj.map(sortKeysDeep);
  }
  if (obj !== null && typeof obj === 'object') {
    const sorted: Record<string, unknown> = {};
    for (const key of Object.keys(obj as Record<string, unknown>).sort()) {
      sorted[key] = sortKeysDeep((obj as Record<string, unknown>)[key]);
    }
    return sorted;
  }
  return obj;
}

/**
 * Canonical JSON display (minified, recursively sorted keys).
 * Approximates RFC 8785 canonical form for display purposes.
 */
export function toCanonicalDisplay(obj: CommitmentTarget): string {
  return JSON.stringify(sortKeysDeep(obj));
}

/**
 * Pretty JSON display (formatted, recursively sorted keys).
 */
export function toPrettyDisplay(obj: CommitmentTarget): string {
  return JSON.stringify(sortKeysDeep(obj), null, 2);
}
