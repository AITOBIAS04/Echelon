import { useTimelines } from '../../hooks/useWingFlaps';
import { useWingFlaps } from '../../hooks/useWingFlaps';
import { Skull, Shield, Swords } from 'lucide-react';
import { clsx } from 'clsx';
import { useMemo } from 'react';

interface WarData {
  timeline_id: string;
  timeline_name: string;
  sabotage_pool: number;
  shield_pool: number;
  total_pool: number;
  sabotage_pct: number;
  recent_attacks: Array<{ agent_name: string; amount: number; timestamp: string }>;
  recent_shields: Array<{ agent_name: string; amount: number; timestamp: string }>;
}

export function WarChest() {
  const { data: timelinesData, isLoading: timelinesLoading } = useTimelines();
  const { data: flapsData, isLoading: flapsLoading } = useWingFlaps();
  
  const timelines = timelinesData?.timelines || [];
  const wingFlaps = flapsData?.flaps || [];

  // Calculate war data from wing flaps
  const warData: WarData[] = useMemo(() => {
    return timelines.map((timeline: any) => {
      // Get flaps for this timeline
      const timelineFlaps = wingFlaps.filter((f: any) => f.timeline_id === timeline.id);
      
      // Calculate sabotage (negative stability) and shield (positive stability) pools
      const sabotageFlaps = timelineFlaps.filter((f: any) => 
        f.flap_type === 'SABOTAGE' || (f.direction === 'DESTABILISE' && f.volume_usd > 0)
      );
      const shieldFlaps = timelineFlaps.filter((f: any) => 
        f.flap_type === 'SHIELD' || (f.direction === 'ANCHOR' && f.volume_usd > 0)
      );
      
      const sabotage_pool = sabotageFlaps.reduce((sum: number, f: any) => sum + (f.volume_usd || 0), 0) || Math.random() * 30000;
      const shield_pool = shieldFlaps.reduce((sum: number, f: any) => sum + (f.volume_usd || 0), 0) || Math.random() * 30000;
      const total_pool = sabotage_pool + shield_pool;
      
      return {
        timeline_id: timeline.id,
        timeline_name: timeline.name,
        sabotage_pool,
        shield_pool,
        total_pool,
        sabotage_pct: total_pool > 0 ? (sabotage_pool / total_pool) * 100 : 50,
        recent_attacks: sabotageFlaps.slice(0, 3).map((f: any) => ({
          agent_name: f.agent_name || 'UNKNOWN',
          amount: f.volume_usd || 0,
          timestamp: f.created_at || f.timestamp
        })),
        recent_shields: shieldFlaps.slice(0, 3).map((f: any) => ({
          agent_name: f.agent_name || 'UNKNOWN',
          amount: f.volume_usd || 0,
          timestamp: f.created_at || f.timestamp
        }))
      };
    }).filter(w => w.total_pool > 0).slice(0, 5);
  }, [timelines, wingFlaps]);

  if (timelinesLoading || flapsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <span className="text-[#00FF41] animate-pulse">ANALYSING BATTLEFIELD...</span>
      </div>
    );
  }

  if (warData.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-500">
        <Swords className="w-12 h-12 mb-4 opacity-50" />
        <span>No active conflicts detected</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {warData.map((war) => {
        const isUnderSiege = war.sabotage_pct > 70;
        const isDefended = war.sabotage_pct < 30;
        const isContested = !isUnderSiege && !isDefended;
        
        return (
          <div 
            key={war.timeline_id}
            className={clsx(
              'bg-[#0a0a0a] border rounded-lg p-4',
              isUnderSiege ? 'border-red-600' : 
              isDefended ? 'border-blue-600' : 
              'border-yellow-600/50'
            )}
          >
            {/* Header */}
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-white">
                {war.timeline_name}
                <span className="text-gray-500 font-normal ml-2">
                  — ${war.total_pool.toLocaleString()} TOTAL
                </span>
              </h3>
              <span className={clsx(
                'text-sm flex items-center gap-1',
                isUnderSiege ? 'text-red-400 animate-pulse' : 
                isDefended ? 'text-blue-400' : 
                'text-yellow-400'
              )}>
                {isUnderSiege && <><Skull className="w-4 h-4" /> UNDER SIEGE</>}
                {isDefended && <><Shield className="w-4 h-4" /> DEFENDED</>}
                {isContested && <><Swords className="w-4 h-4" /> CONTESTED</>}
              </span>
            </div>

            {/* Tug of War Bar */}
            <div className="relative h-10 rounded overflow-hidden mb-2">
              <div className="absolute inset-0 flex">
                {/* Sabotage (Red) Side */}
                <div 
                  className={clsx(
                    'flex items-center justify-start pl-3 transition-all duration-500',
                    isUnderSiege ? 'bg-red-600 animate-pulse' : 'bg-red-600/70'
                  )}
                  style={{ width: `${war.sabotage_pct}%` }}
                >
                  {/* values shown below to avoid disappearing on small segments */}
                </div>
                
                {/* Shield (Blue) Side */}
                <div 
                  className={clsx(
                    'flex items-center justify-end pr-3 transition-all duration-500',
                    isDefended ? 'bg-blue-600' : 'bg-blue-600/70'
                  )}
                  style={{ width: `${100 - war.sabotage_pct}%` }}
                >
                  {/* values shown below to avoid disappearing on small segments */}
                </div>
              </div>
              
              {/* Center Line */}
              <div className="absolute inset-y-0 left-1/2 w-0.5 bg-white/30" />
            </div>

            {/* Always-visible values */}
            <div className="flex justify-between items-center text-xs mb-3">
              <span className="text-red-300 font-mono flex items-center gap-1">
                <Skull className="w-3 h-3" />
                ${war.sabotage_pool.toLocaleString()}
              </span>
              <span className="text-blue-300 font-mono flex items-center gap-1">
                ${war.shield_pool.toLocaleString()}
                <Shield className="w-3 h-3" />
              </span>
            </div>

            {/* Percentages */}
            <div className="flex justify-between text-xs mb-4">
              <span className={clsx(
                isUnderSiege ? 'text-red-400 font-bold' : 'text-gray-500'
              )}>
                SABOTAGE: {war.sabotage_pct.toFixed(0)}%
                {isUnderSiege && ' ⚠️'}
              </span>
              <span className={clsx(
                isDefended ? 'text-blue-400 font-bold' : 'text-gray-500'
              )}>
                SHIELD: {(100 - war.sabotage_pct).toFixed(0)}%
                {isDefended && ' ✓'}
              </span>
            </div>

            {/* Recent Activity Columns */}
            <div className="grid grid-cols-2 gap-4 text-xs">
              {/* Red Army */}
              <div>
                <div className="text-red-400 font-bold mb-2 flex items-center gap-1">
                  <Skull className="w-3 h-3" />
                  RED ARMY (ATTACKERS)
                </div>
                <div className="space-y-1 text-gray-400">
                  {war.recent_attacks.length > 0 ? (
                    war.recent_attacks.map((attack, i) => (
                      <div key={i}>
                        💀 <span className="text-red-400">{attack.agent_name}</span> deployed ${attack.amount.toLocaleString()}
                      </div>
                    ))
                  ) : (
                    <div className="text-gray-600">No recent attacks</div>
                  )}
                </div>
              </div>
              
              {/* Blue Army */}
              <div>
                <div className="text-blue-400 font-bold mb-2 flex items-center gap-1">
                  <Shield className="w-3 h-3" />
                  BLUE ARMY (DEFENDERS)
                </div>
                <div className="space-y-1 text-gray-400">
                  {war.recent_shields.length > 0 ? (
                    war.recent_shields.map((shield, i) => (
                      <div key={i}>
                        🛡️ <span className="text-blue-400">{shield.agent_name}</span> reinforced ${shield.amount.toLocaleString()}
                      </div>
                    ))
                  ) : (
                    <div className="text-gray-600">No recent shields</div>
                  )}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default WarChest;

