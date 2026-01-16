import { ArrowUp, ArrowDown, Minus } from 'lucide-react';

/**
 * StabilityTrendArrow Props
 */
export interface StabilityTrendArrowProps {
  /** Stability trend direction */
  trend: 'up' | 'down' | 'flat';
}

/**
 * StabilityTrendArrow Component
 * 
 * Displays an arrow icon indicating stability direction.
 * 
 * - up: Green arrow pointing upward (increasing stability)
 * - down: Red arrow pointing downward (decreasing stability)
 * - flat: Grey horizontal line (stable, no change)
 * 
 * @example
 * ```tsx
 * <StabilityTrendArrow trend="up" />    // Green ↑
 * <StabilityTrendArrow trend="down" />  // Red ↓
 * <StabilityTrendArrow trend="flat" />  // Grey —
 * ```
 */
export function StabilityTrendArrow({ trend }: StabilityTrendArrowProps) {
  const colors = {
    up: '#00FF41',    // green
    down: '#FF3B3B',  // red
    flat: '#666666',  // grey
  };
  
  const color = colors[trend];
  
  return (
    <div className="flex items-center justify-center">
      {trend === 'up' && (
        <ArrowUp className="w-3 h-3" style={{ color }} />
      )}
      {trend === 'down' && (
        <ArrowDown className="w-3 h-3" style={{ color }} />
      )}
      {trend === 'flat' && (
        <Minus className="w-3 h-3" style={{ color }} />
      )}
    </div>
  );
}
