/**
 * Convert an ISO timestamp to a relative time string (e.g. "3m ago").
 */
export function relativeTime(isoTimestamp: string): string {
  const now = new Date();
  const then = new Date(isoTimestamp);
  const diffMs = now.getTime() - then.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);

  if (diffSeconds < 60) return `${diffSeconds}s ago`;

  const diffMinutes = Math.floor(diffSeconds / 60);
  if (diffMinutes < 60) return `${diffMinutes}m ago`;

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours}h ago`;

  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

/**
 * Format a numeric score to 4 decimal places (e.g. "0.9091").
 */
export function formatScore(score: number): string {
  return score.toFixed(4);
}

/**
 * Format a 0-1 value as a percentage string (e.g. "95%").
 */
export function formatPercentage(value: number): string {
  return `${Math.round(value * 100)}%`;
}
