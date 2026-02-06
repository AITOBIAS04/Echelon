/**
 * EntropySparkline Props
 */
export interface EntropySparklineProps {
  /** Array of 6 entropy readings (most recent last) */
  history: number[];
  /** Current decay rate per hour (percentage) */
  currentRate: number;
}

/**
 * EntropySparkline Component
 * 
 * Renders a mini sparkline chart showing entropy rate over the last hour.
 * Displays 6 data points as a simple line chart with the current rate label below.
 * 
 * @example
 * ```tsx
 * <EntropySparkline 
 *   history={[-2.1, -2.3, -2.0, -2.5, -2.2, -2.4]} 
 *   currentRate={-2.3} 
 * />
 * ```
 */
export function EntropySparkline({ 
  history, 
  currentRate 
}: EntropySparklineProps) {
  const width = 60;
  const height = 20;
  const strokeWidth = 1.5;
  const lineColor = '#F59E0B'; // muted amber
  
  // X positions: evenly distributed across 60px (0, 12, 24, 36, 48, 60)
  const xPositions = [0, 12, 24, 36, 48, 60];
  
  // Calculate Y positions
  let points: string = '';
  
  if (!history || history.length === 0) {
    // Handle empty history: flat line at midpoint (10px from top)
    const midY = height / 2;
    points = xPositions.map(x => `${x},${midY}`).join(' ');
  } else {
    // Find min and max values for scaling
    const values = history.slice(-6); // Ensure we only use up to 6 values
    
    // Pad values if we have fewer than 6 (repeat first value at beginning)
    const paddedValues = [...values];
    while (paddedValues.length < 6) {
      paddedValues.unshift(paddedValues[0] ?? 0);
    }
    
    const minValue = Math.min(...paddedValues);
    const maxValue = Math.max(...paddedValues);
    const valueRange = maxValue - minValue || 1; // Avoid division by zero
    
    // Scale values to fit 0-20px range and invert Y (SVG Y is top-down)
    // We'll use a small padding (1px) from edges
    const padding = 1;
    const chartHeight = height - (padding * 2);
    
    const yPositions = paddedValues.map((value) => {
      // Normalize value to 0-1 range
      const normalized = (value - minValue) / valueRange;
      // Scale to chart height and invert (SVG Y increases downward)
      const y = height - padding - (normalized * chartHeight);
      return y;
    });
    
    // Create points string for polyline
    points = xPositions
      .map((x, i) => `${x},${yPositions[i]}`)
      .join(' ');
  }
  
  return (
    <div className="flex flex-col items-center">
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        className="overflow-visible"
      >
        <polyline
          points={points}
          fill="none"
          stroke={lineColor}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <div className="text-xs text-terminal-text-muted mt-0.5">
        {currentRate.toFixed(1)}%/hr
      </div>
    </div>
  );
}
