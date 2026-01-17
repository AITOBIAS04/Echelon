import type { OpsCard } from '../types/opsBoard';

type Tone = 'green' | 'amber' | 'red' | 'purple';

function clamp(n: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, n));
}

function minutesFromSeconds(sec: number): number {
  return Math.max(0, sec) / 60;
}

export function computeTrendingScore(card: OpsCard): number {
  // Only timelines participate in most signal scoring, but allow launches to sort sensibly.
  let score = 0;

  const tags = card.tags ?? [];

  // Discrete signal weights
  if (tags.includes('fork_soon')) score += 100;
  if (tags.includes('disclosure_active')) score += 80;
  if (tags.includes('paradox_active')) score += 70;
  if (tags.includes('evidence_flip')) score += 60;
  if (tags.includes('sabotage_heat')) score += 40;
  if (tags.includes('brittle')) score += 25;

  // Urgency
  if (typeof card.nextForkEtaSec === 'number') {
    const etaMin = minutesFromSeconds(card.nextForkEtaSec);
    score += Math.max(0, 50 - etaMin);
  }

  // Volatility
  if (typeof card.logicGap === 'number') {
    score += clamp(card.logicGap, 0, 60) * 0.5;
  }
  if (typeof card.entropyRate === 'number') {
    score += clamp(Math.abs(card.entropyRate), 0, 10) * 2;
  }

  // Activity
  if (typeof card.sabotageHeat24h === 'number') {
    score += clamp(card.sabotageHeat24h, 0, 10) * 3;
  }

  // Freshness
  // createdAt is ISO, but be defensive.
  const createdAtMs = Date.parse(card.createdAt);
  if (!Number.isNaN(createdAtMs)) {
    const ageMs = Date.now() - createdAtMs;
    const ageHrs = ageMs / (1000 * 60 * 60);
    if (ageHrs <= 1) score += 20;
    else if (ageHrs <= 24) score += 10;
  }

  // Small bias to timelines vs launches in trending
  if (card.type === 'timeline') score += 5;

  return score;
}

function formatEtaLabel(seconds: number): string {
  const sec = Math.max(0, Math.floor(seconds));
  if (sec < 60) return `Fork in ${sec}s`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `Fork in ${min}m`;
  const hrs = Math.floor(min / 60);
  return `Fork in ${hrs}h`;
}

export function getTrendingReason(card: OpsCard): { label: string; tone: Tone } {
  const tags = card.tags ?? [];

  // Priority order
  if (typeof card.nextForkEtaSec === 'number' && card.nextForkEtaSec <= 3600) {
    return { label: formatEtaLabel(card.nextForkEtaSec), tone: 'amber' };
  }
  if (tags.includes('fork_soon')) {
    const eta = typeof card.nextForkEtaSec === 'number' ? formatEtaLabel(card.nextForkEtaSec) : 'Fork soon';
    return { label: eta, tone: 'amber' };
  }
  if (tags.includes('disclosure_active')) {
    return { label: 'Disclosure live', tone: 'amber' };
  }
  if (tags.includes('paradox_active')) {
    return { label: 'Paradox active', tone: 'red' };
  }
  if (tags.includes('evidence_flip')) {
    return { label: 'Evidence flip', tone: 'purple' };
  }
  if (typeof card.sabotageHeat24h === 'number' && card.sabotageHeat24h >= 5) {
    return { label: `Heat ${Math.round(clamp(card.sabotageHeat24h, 0, 10))}/10`, tone: 'red' };
  }
  if (tags.includes('sabotage_heat')) {
    return { label: 'Sabotage heat', tone: 'red' };
  }
  if (typeof card.logicGap === 'number') {
    return { label: `Gap ${Math.round(card.logicGap)}%`, tone: card.logicGap >= 60 ? 'red' : 'amber' };
  }

  return { label: 'Active', tone: 'green' };
}
