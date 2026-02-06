import type { LaunchPhase, LaunchCategory } from '../types/launchpad';

/** Phase badge colours — single source of truth across all Launchpad components */
export const PHASE_COLORS: Record<LaunchPhase, { bg: string; text: string; label: string }> = {
  draft:     { bg: '#64748B', text: '#FFFFFF', label: 'DRAFT' },
  sandbox:   { bg: '#F59E0B', text: '#FFFFFF', label: 'SANDBOX' },
  pilot:     { bg: '#22D3EE', text: '#000000', label: 'PILOT' },
  graduated: { bg: '#10B981', text: '#FFFFFF', label: 'GRADUATED' },
  failed:    { bg: '#EF4444', text: '#FFFFFF', label: 'FAILED' },
};

/** Category badge colours — single source of truth */
export const CATEGORY_COLORS: Record<LaunchCategory, string> = {
  theatre: '#22D3EE', // echelon-cyan
  osint:   '#8B5CF6', // status-paradox
};

/** Quality score colour thresholds */
export function getQualityColor(score: number): string {
  if (score >= 80) return '#10B981'; // emerald
  if (score >= 60) return '#F59E0B'; // amber
  return '#EF4444'; // red
}
