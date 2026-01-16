import { useTimelines } from '../../hooks/useWingFlaps';
import { Target, TrendingUp, TrendingDown, Minus } from 'lucide-react';
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

  const getStrengthColour = (strength: number) => {
    if (strength > 0.7) return 'text-red-400';
    if (strength > 0.4) return 'text-amber-400';
    return 'text-green-400';
  };

  const getBarColour = (strength: number) => {
    if (strength > 0.7) return 'bg-red-500';
    if (strength > 0.4) return 'bg-amber-500';
    return 'bg-green-500';
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <TrendingUp className="w-3 h-3 text-green-400" />;
      case 'down': return <TrendingDown className="w-3 h-3 text-red-400" />;
      default: return <Minus className="w-3 h-3 text-gray-400" />;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <span className="text-[#00FF41] animate-pulse">SCANNING GRAVITY WELLS...</span>
      </div>
    );
  }

  if (gravityWells.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-500">
        <Target className="w-12 h-12 mb-4 opacity-50" />
        <span>No gravity wells detected</span>
      </div>
    );
  }

  // Find dominant keyword
  const dominant = gravityWells[0];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      
      {/* Radar Visualization */}
      <div className="bg-[#0a0a0a] border border-[#1a3a1a] rounded-lg p-4">
        <div className="text-xs text-gray-500 mb-3 flex items-center gap-2">
          <Target className="w-4 h-4" />
          KEYWORD RADAR — GHOST_TANKER CLUSTER
        </div>
        
        <div className="relative w-full aspect-square max-w-[300px] mx-auto">
          {/* Radar circles */}
          <svg viewBox="0 0 200 200" className="w-full h-full">
            {/* Concentric circles */}
            <circle cx="100" cy="100" r="90" fill="none" stroke="#1a3a1a" strokeWidth="1" />
            <circle cx="100" cy="100" r="60" fill="none" stroke="#1a3a1a" strokeWidth="1" />
            <circle cx="100" cy="100" r="30" fill="none" stroke="#1a3a1a" strokeWidth="1" />
            
            {/* Radar sweep */}
            <line 
              x1="100" y1="100" x2="100" y2="10" 
              stroke="#00FF41" 
              strokeWidth="1" 
              opacity="0.3"
              className="origin-center"
              style={{ 
                transformOrigin: '100px 100px',
                animation: 'spin 4s linear infinite'
              }}
            />
            
            {/* Plot keywords as dots */}
            {gravityWells.slice(0, 6).map((well, i) => {
              // Position in a spiral pattern
              const angle = (i * 60) * (Math.PI / 180);
              const radius = 30 + (1 - well.strength) * 60; // Higher strength = closer to center
              const x = 100 + Math.cos(angle) * radius;
              const y = 100 + Math.sin(angle) * radius;
              const dotSize = 4 + well.strength * 6;
              
              return (
                <g key={well.keyword}>
                  <circle 
                    cx={x} 
                    cy={y} 
                    r={dotSize}
                    className={clsx(
                      well.strength > 0.7 ? 'fill-red-500' :
                      well.strength > 0.4 ? 'fill-amber-500' : 'fill-green-500',
                      well.strength > 0.7 && 'animate-pulse'
                    )}
                  />
                  <text 
                    x={x} 
                    y={y - dotSize - 4} 
                    textAnchor="middle"
                    className={clsx(
                      'text-[8px]',
                      well.strength > 0.7 ? 'fill-red-400' :
                      well.strength > 0.4 ? 'fill-amber-400' : 'fill-green-400'
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
              <div className="text-xs text-gray-500">DOMINANT</div>
              <div className={clsx(
                'font-bold',
                getStrengthColour(dominant.strength)
              )} style={{ textShadow: '0 0 10px currentColor' }}>
                {dominant.keyword}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Gravity Well Strength List */}
      <div className="bg-[#0a0a0a] border border-[#1a3a1a] rounded-lg p-4">
        <div className="text-xs text-gray-500 mb-3">GRAVITY WELL STRENGTH</div>
        
        <div className="space-y-3">
          {gravityWells.map((well) => (
            <div key={well.keyword} className="flex items-center gap-3">
              <span className={clsx(
                'w-24 font-bold text-sm truncate',
                getStrengthColour(well.strength)
              )}>
                {well.keyword}
              </span>
              
              <div className="flex-1 h-3 bg-[#1a3a1a] rounded overflow-hidden">
                <div 
                  className={clsx(
                    'h-full rounded transition-all duration-500',
                    getBarColour(well.strength),
                    well.strength > 0.7 && 'animate-pulse'
                  )}
                  style={{ width: `${well.strength * 100}%` }}
                />
              </div>
              
              <span className={clsx(
                'w-10 text-sm font-mono',
                getStrengthColour(well.strength)
              )}>
                {well.strength.toFixed(2)}
              </span>
              
              {getTrendIcon(well.trend)}
              
              <span className="text-xs text-gray-600 w-16">
                {well.agentCount} agents
              </span>
            </div>
          ))}
        </div>

        {/* Legend */}
        <div className="mt-4 pt-4 border-t border-[#1a3a1a] text-xs text-gray-500">
          <span className="text-green-400">●</span> Low (&lt;0.4) 
          <span className="text-amber-400 ml-4">●</span> Medium (0.4-0.7) 
          <span className="text-red-400 ml-4">●</span> High (&gt;0.7) — OSINT prioritising
        </div>
      </div>
    </div>
  );
}

export default GravityField;

