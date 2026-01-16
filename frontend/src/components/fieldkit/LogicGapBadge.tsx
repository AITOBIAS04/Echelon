import { ArrowUp, ArrowDown } from 'lucide-react';
import { getLogicGapSeverity, getSeverityColor } from '../../utils/severity';
import type { Severity } from '../../utils/severity';

/**
 * LogicGapBadge Props
 */
export interface LogicGapBadgeProps {
  /** Logic Gap percentage (0-100) */
  gap: number;
  /** Whether to show trend indicator */
  showTrend?: boolean;
  /** Trend direction */
  trend?: 'widening' | 'narrowing' | 'stable';
}

/**
 * LogicGapBadge Component
 * 
 * Displays a colored pill badge showing Logic Gap percentage with optional trend indicator.
 * 
 * Severity levels:
 * - healthy (green): gap < 20
 * - warning (amber): gap 20-49
 * - critical (red): gap >= 50
 */
export function LogicGapBadge({ 
  gap, 
  showTrend = false, 
  trend 
}: LogicGapBadgeProps) {
  const severity: Severity = getLogicGapSeverity(gap);
  const color = getSeverityColor(severity);
  
  // Convert hex color to RGB for opacity
  const hexToRgb = (hex: string): [number, number, number] => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result
      ? [
          parseInt(result[1], 16),
          parseInt(result[2], 16),
          parseInt(result[3], 16),
        ]
      : [0, 0, 0];
  };
  
  const [r, g, b] = hexToRgb(color);
  const bgColor = `rgba(${r}, ${g}, ${b}, 0.2)`;
  
  return (
    <span
      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium"
      style={{
        backgroundColor: bgColor,
        color: color,
      }}
    >
      <span>GAP: {gap}%</span>
      {showTrend && trend && trend !== 'stable' && (
        <>
          {trend === 'widening' && (
            <ArrowUp className="w-3 h-3" style={{ color: color }} />
          )}
          {trend === 'narrowing' && (
            <ArrowDown className="w-3 h-3" style={{ color: color }} />
          )}
        </>
      )}
    </span>
  );
}
