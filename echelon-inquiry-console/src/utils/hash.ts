import { TEMPLATES } from '../data/templates';

/**
 * Look up the pre-computed commitment hash for a given template.
 */
export function getCommitmentHash(templateId: string): string {
  const template = TEMPLATES.find((t) => t.template_id === templateId);
  return template?.commitment_hash ?? '';
}

/**
 * Truncate a hex hash to a specified number of characters with ellipsis.
 * Default: first 8 characters + "..."
 */
export function truncateHash(hash: string, chars: number = 8): string {
  if (hash.length <= chars) return hash;
  return `${hash.slice(0, chars)}...`;
}
