import { useTimelines } from '../../hooks/useWingFlaps';
import { Target, TrendingUp, TrendingDown, Minus, Zap } from 'lucide-react';
import { clsx } from 'clsx';
import { useMemo } from 'react';

interface GravityWell {
  keyword: string;
  strength: number;  // 0-1
  agentCount: number;
  trend: 'up' | 'down' | 'stable';
  relatedTimelines: string[];
}

export function GravityField() {
  const { data: timelinesData, isLoading } = useTimelines();
  const timelines = timelinesData?.timelines || [];

  // Extract and aggregate keywords from timelines
  const gravityWells: GravityWell[] = useMemo(() => {
    const keywordMap = new Map<string, {
      strength: number;
      agentCount: number;
      timelines: string[];
      volumes: number[];
    }>();

    timelines.forEach((timeline: any) => {
      // Use gravity_factors as keywords if available, otherwise extract from name
      const keywords: string[] = [];
      if (timeline.gravity_factors && typeof timeline.gravity_factors === 'object') {
        keywords.push(...Object.keys(timeline.gravity_factors));
      }
      // Fallback: extract keywords from timeline name
      if (keywords.length === 0 && timeline.name) {
        const words = timeline.name.split(/[\s-]+/).filter((w: string) => w.length > 3);
        keywords.push(...words.slice(0, 3));
      }

      const gravity = timeline.gravity_score || 50;
      const agents = timeline.active_agent_count || 0;

      keywords.forEach((keyword: string) => {
        const existing = keywordMap.get(keyword) || {
          strength: 0,
          agentCount: 0,
          timelines: [],
          volumes: []
        };
        existing.strength = Math.max(existing.strength, gravity);
        existing.agentCount += agents;
        existing.timelines.push(timeline.name);
        existing.volumes.push(timeline.total_volume_usd || 0);
        keywordMap.set(keyword, existing);
      });
    });

    return Array.from(keywordMap.entries())
      .map(([keyword, data]): GravityWell => ({
        keyword: keyword.toUpperCase(),
        strength: Math.min(data.strength / 100, 1), // Normalise to 0-1
        agentCount: data.agentCount,
        trend: (data.strength > 70 ? 'up' : data.strength < 40 ? 'down' : 'stable') as 'up' | 'down' | 'stable',
        relatedTimelines: data.timelines
      }))
      .sort((a, b) => b.strength - a.strength)
      .slice(0, 8); // Top 8 keywords
  }, [timelines]);

  const getStrengthColor = (strength: number): string => {
    if (strength > 0.7) return 'text-echelon-red';
    if (strength > 0.4) return 'text-echelon-amber';
    return 'text-echelon-green';
  };

  const getBarColor = (strength: number): string => {
    if (strength > 0.7) return 'bg-red-500';
    if (strength > 0.4) return 'bg-amber-500';
    return 'bg-emerald-500';
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <TrendingUp className="w-3 h-3 text-echelon-green" />;
      case 'down': return <TrendingDown className="w-3 h-3 text-echelon-red" />;
      default: return <Minus className="w-3 h-3 text-terminal-text-muted" />;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-echelon-blue animate-pulse" />
          <span className="text-terminal-text-secondary text-xs">Loading gravity data...</span>
        </div>
      </div>
    );
  }

  if (gravityWells.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-terminal-text-secondary">
        <Target className="w-8 h-8 mb-2 text-terminal-text-muted opacity-50" />
        <span className="text-xs">No gravity wells detected</span>
      </div>
    );
  }

  // Find dominant keyword
  const dominant = gravityWells[0];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
      {/* Radar Visualization */}
      <div className="bg-terminal-panel border border-terminal-border rounded p-3">
        <div className="text-xs font-medium text-terminal-text mb-2 flex items-center gap-2">
          <Target className="w-3.5 h-3.5 text-echelon-blue" />
          Keyword Radar
        </div>

        <div className="relative w-full aspect-square max-w-[180px] mx-auto">
          {/* Radar circles */}
          <svg viewBox="0 0 100 100" className="w-full h-full">
            {/* Concentric circles */}
            <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="0.5" className="text-terminal-text-muted" />
            <circle cx="50" cy="50" r="30" fill="none" stroke="currentColor" strokeWidth="0.5" className="text-terminal-text-muted" />
            <circle cx="50" cy="50" r="15" fill="none" stroke="currentColor" strokeWidth="0.5" className="text-terminal-text-muted" />

            {/* Plot keywords as dots */}
            {gravityWells.slice(0, 6).map((well, i) => {
              // Position in a spiral pattern
              const angle = (i * 60) * (Math.PI / 180);
              const radius = 15 + (1 - well.strength) * 30; // Higher strength = closer to center
              const x = 50 + Math.cos(angle) * radius;
              const y = 50 + Math.sin(angle) * radius;
              const dotSize = 2 + well.strength * 3;

              return (
                <g key={well.keyword}>
                  <circle
                    cx={x}
                    cy={y}
                    r={dotSize}
                    className={clsx(
                      'transition-all',
                      well.strength > 0.7 ? 'fill-red-500' :
                      well.strength > 0.4 ? 'fill-amber-500' : 'fill-emerald-500'
                    )}
                  />
                  <text
                    x={x}
                    y={y - dotSize - 2}
                    textAnchor="middle"
                    className={clsx(
                      'text-[5px] font-medium',
                      well.strength > 0.7 ? 'fill-red-400' :
                      well.strength > 0.4 ? 'fill-amber-400' : 'fill-emerald-400'
                    )}
                  >
                    {well.keyword}
                  </text>
                </g>
              );
            })}
          </svg>

          {/* Center label */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="text-center">
              <div className="text-[9px] text-terminal-text-muted">DOM</div>
              <div className={clsx(
                'font-bold text-sm',
                getStrengthColor(dominant.strength)
              )}>
                {dominant.keyword}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Gravity Well Strength List */}
      <div className="bg-terminal-panel border border-terminal-border rounded p-3">
        <div className="text-xs font-medium text-terminal-text mb-2">Gravity Wells</div>

        <div className="space-y-2">
          {gravityWells.map((well) => (
            <div key={well.keyword} className="flex items-center gap-2">
              <span className={clsx(
                'w-16 text-xs font-bold truncate',
                getStrengthColor(well.strength)
              )}>
                {well.keyword}
              </span>

              <div className="flex-1 h-2 bg-terminal-card border border-terminal-border rounded-full overflow-hidden">
                <div
                  className={clsx(
                    'h-full rounded-full transition-all',
                    getBarColor(well.strength)
                  )}
                  style={{ width: `${well.strength * 100}%` }}
                />
              </div>

              <span className={clsx(
                'w-10 text-xs font-mono text-right',
                getStrengthColor(well.strength)
              )}>
                {well.strength.toFixed(1)}
              </span>

              {getTrendIcon(well.trend)}

              <span className="text-[10px] text-terminal-text-muted w-12 text-right">
                {well.agentCount}
              </span>
            </div>
          ))}
        </div>

        {/* Legend */}
        <div className="mt-2 pt-2 border-t border-terminal-border text-[10px] text-terminal-text-muted flex gap-3">
          <span><span className="text-echelon-green">●</span> Low</span>
          <span><span className="text-echelon-amber">●</span> Med</span>
          <span><span className="text-echelon-red">●</span> High</span>
        </div>
      </div>
    </div>
  );
}

export default GravityField;
