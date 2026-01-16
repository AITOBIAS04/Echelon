/**
 * Logic Gap Severity Utilities
 * =============================
 * 
 * Provides severity classification and color mapping for Logic Gap values.
 * Logic Gap represents the instability/contradiction level in a timeline.
 * 
 * Thresholds:
 * - healthy: gap < 20 (stable timeline)
 * - warning: gap >= 20 and < 50 (moderate instability)
 * - critical: gap >= 50 (high instability, paradox risk)
 */

/**
 * Severity level for Logic Gap values
 */
export type Severity = 'healthy' | 'warning' | 'critical';

/**
 * Color mapping for severity levels
 * Uses Echelon's terminal color palette
 */
export const SEVERITY_COLORS = {
  healthy: '#00FF41',  // green
  warning: '#FF9500',  // amber
  critical: '#FF3B3B', // red
} as const;

/**
 * Determines the severity level based on Logic Gap value
 * 
 * @param gap - Logic Gap percentage (0-100)
 * @returns Severity level
 * 
 * @example
 * ```ts
 * getLogicGapSeverity(15)  // 'healthy'
 * getLogicGapSeverity(35)  // 'warning'
 * getLogicGapSeverity(75)  // 'critical'
 * ```
 */
export function getLogicGapSeverity(gap: number): Severity {
  if (gap < 20) {
    return 'healthy';
  }
  
  if (gap >= 20 && gap < 50) {
    return 'warning';
  }
  
  return 'critical';
}

/**
 * Returns the color associated with a severity level
 * 
 * @param severity - Severity level
 * @returns Hex color string
 * 
 * @example
 * ```ts
 * getSeverityColor('healthy')  // '#00FF41'
 * getSeverityColor('warning')  // '#FF9500'
 * getSeverityColor('critical') // '#FF3B3B'
 * ```
 */
export function getSeverityColor(severity: Severity): string {
  return SEVERITY_COLORS[severity];
}
