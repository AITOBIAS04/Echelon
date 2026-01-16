/**
 * ParadoxProximityBar Props
 */
export interface ParadoxProximityBarProps {
  /** Paradox proximity score (0-100, where 100 = imminent paradox) */
  proximity: number;
  /** Whether to show the "PARADOX RISK" label above the bar */
  showLabel?: boolean;
}

/**
 * ParadoxProximityBar Component
 * 
 * Displays a thin progress bar indicating proximity to Paradox threshold.
 * The bar uses a gradient from cyan (low risk) to red (high risk) to visually
 * represent the danger level.
 * 
 * @example
 * ```tsx
 * <ParadoxProximityBar proximity={75} />
 * <ParadoxProximityBar proximity={45} showLabel={true} />
 * ```
 */
export function ParadoxProximityBar({ 
  proximity, 
  showLabel = false 
}: ParadoxProximityBarProps) {
  // Clamp proximity to valid range
  const clampedProximity = Math.max(0, Math.min(100, proximity));
  
  // CSS gradient from cyan (#00D4FF) to red (#FF3B3B)
  const gradientStyle: React.CSSProperties = {
    background: 'linear-gradient(to right, #00D4FF 0%, #FF3B3B 100%)',
    width: `${clampedProximity}%`,
    height: '100%',
    borderRadius: '9999px', // rounded-full equivalent
    transition: 'width 0.3s ease',
  };
  
  return (
    <div className="w-full">
      {showLabel && (
        <div className="text-xs text-terminal-muted mb-1.5">
          PARADOX RISK
        </div>
      )}
      <div 
        className="w-full h-1 rounded-full"
        style={{
          backgroundColor: '#1A1A1A',
        }}
      >
        <div style={gradientStyle} />
      </div>
    </div>
  );
}
