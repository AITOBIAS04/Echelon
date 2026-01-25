/**
 * SabotageHeatDots Props
 */
export interface SabotageHeatDotsProps {
  /** Number of sabotage attempts in the last hour */
  count: number;
}

/**
 * SabotageHeatDots Component
 * 
 * Displays 5 dots in a horizontal row indicating sabotage pressure.
 * The first {count} dots are "lit" (red with glow), representing active sabotage attempts.
 * 
 * @example
 * ```tsx
 * <SabotageHeatDots count={3} />  // 3 lit dots, 2 unlit
 * <SabotageHeatDots count={0} />  // All unlit
 * <SabotageHeatDots count={7} />  // All 5 lit (capped at 5)
 * ```
 */
export function SabotageHeatDots({ count }: SabotageHeatDotsProps) {
  const maxDots = 5;
  const litCount = Math.min(Math.max(0, count), maxDots); // Clamp between 0 and 5
  
  const litColor = '#EF4444'; // crimson
  const unlitColor = '#2A2D33'; // terminal border

  return (
    <div className="flex items-center gap-1">
      {Array.from({ length: maxDots }, (_, index) => {
        const isLit = index < litCount;

        return (
          <div
            key={index}
            className="w-1.5 h-1.5 rounded-full"
            style={{
              backgroundColor: isLit ? litColor : unlitColor,
              boxShadow: isLit ? 'none' : 'none',
            }}
          />
        );
      })}
    </div>
  );
}
