/** Chart colors for SVG contexts — matches tailwind token values */
export const CHART = {
  BID: '#4ADE80',      // echelon-green
  ASK: '#EF4444',      // echelon-red
  CYAN: '#22D3EE',     // echelon-cyan
  BLUE: '#3B82F6',     // echelon-blue
  GRID: 'rgba(255,255,255,0.06)',
  LABEL: '#6B7280',    // terminal-text-muted
  COST_CURVE: '#22D3EE', // echelon-cyan — impact curve line
} as const;
