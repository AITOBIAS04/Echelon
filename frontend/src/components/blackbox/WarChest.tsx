import { useTimelines } from '../../hooks/useWingFlaps';
import { useWingFlaps } from '../../hooks/useWingFlaps';
import { useUserPosition } from '../../hooks/useUserPositions';
import { Skull, Shield, Swords, Activity, User } from 'lucide-react';
import { clsx } from 'clsx';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

interface WarData {
  timeline_id: string;
  timeline_name: string;
  image_url?: string;
  sabotage_pool: number;
  shield_pool: number;
  total_pool: number;
  sabotage_pct: number;
  recent_attacks: Array<{ agent_name: string; amount: number; timestamp: string }>;
  recent_shields: Array<{ agent_name: string; amount: number; timestamp: string }>;
}

export function WarChest() {
  const navigate = useNavigate();
  const { data: timelinesData, isLoading: timelinesLoading } = useTimelines();
  const { data: flapsData, isLoading: flapsLoading } = useWingFlaps();

  const timelines = timelinesData?.timelines || [];
  const wingFlaps = flapsData?.flaps || [];

  // Calculate war data from wing flaps
  const warData: WarData[] = useMemo(() => {
    return timelines.map((timeline: any) => {
      const timelineFlaps = wingFlaps.filter((f: any) => f.timeline_id === timeline.id);

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
        image_url: timeline.image_url,
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
      <div className="flex items-center justify-center h-32">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-blue-400 animate-pulse" />
          <span className="text-slate-400 text-xs">Loading war data...</span>
        </div>
      </div>
    );
  }

  if (warData.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-slate-400">
        <Swords className="w-8 h-8 mb-2 text-slate-600 opacity-50" />
        <span className="text-xs">No active conflicts</span>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {warData.map((war) => (
        <WarCard key={war.timeline_id} war={war} onClick={() => navigate(`/timeline/${war.timeline_id}`)} />
      ))}
    </div>
  );
}

function WarCard({ war, onClick }: { war: WarData; onClick: () => void }) {
  const { position } = useUserPosition(war.timeline_id);
  const isUnderSiege = war.sabotage_pct > 70;
  const isDefended = war.sabotage_pct < 30;
  const isContested = !isUnderSiege && !isDefended;

  // Calculate user's stake relative to pool
  const userStakePercent = position && war.total_pool > 0
    ? (position.totalNotional / war.total_pool) * 100
    : 0;

  return (
    <div
      className={clsx(
        'bg-slate-900/50 border border-slate-700/50 rounded p-3',
        isUnderSiege ? 'border-red-500/30' :
        isDefended ? 'border-emerald-500/30' :
        'border-amber-500/30'
      )}
    >
      {/* Header Row */}
      <div className="flex items-start gap-3 mb-3">
        {/* Timeline Image Tile - 40x40px */}
        <div className="flex-shrink-0 w-10 h-10 border border-slate-700/50 rounded bg-slate-800/30 flex items-center justify-center overflow-hidden">
          {war.image_url ? (
            <img 
              src={war.image_url} 
              alt={war.timeline_name}
              className="w-full h-full object-cover"
            />
          ) : (
            <Swords className="w-4 h-4 text-slate-600" />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex justify-between items-start gap-2">
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-slate-200 text-sm truncate cursor-pointer hover:text-blue-400" onClick={onClick}>
                {war.timeline_name}
              </h3>
              <span className="text-[10px] text-slate-500 font-mono">${war.total_pool.toLocaleString()} pool</span>
            </div>
            <span className={clsx(
              'text-[10px] flex items-center gap-1 flex-shrink-0',
              isUnderSiege ? 'text-red-400' :
              isDefended ? 'text-emerald-400' :
              'text-amber-400'
            )}>
              {isUnderSiege && <Skull className="w-3 h-3" />}
              {isDefended && <Shield className="w-3 h-3" />}
              {isContested && <Swords className="w-3 h-3" />}
              {isUnderSiege ? 'Siege' : isDefended ? 'Defended' : 'Contested'}
            </span>
          </div>

          {/* User Position */}
          {position && position.totalNotional > 0 && (
            <div className="flex items-center gap-2 mt-1.5">
              <User className="w-3 h-3 text-blue-400" />
              <span className="text-[10px] text-slate-400">
                <span className="text-slate-200 font-mono">${position.totalNotional.toLocaleString()}</span>
              </span>
              <span className={clsx(
                'text-[10px] px-1.5 py-0.5 rounded',
                position.netDirection === 'YES' && 'bg-emerald-500/10 text-emerald-400',
                position.netDirection === 'NO' && 'bg-red-500/10 text-red-400'
              )}>
                {position.netDirection}
              </span>
              <span className={clsx(
                'text-[10px] font-mono',
                position.pnlValue >= 0 ? 'text-emerald-400' : 'text-red-400'
              )}>
                {position.pnlPercent >= 0 ? '+' : ''}{position.pnlPercent.toFixed(1)}%
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Tug of War Bar - Compact */}
      <div className="relative h-6 rounded overflow-hidden mb-2 bg-slate-800/50 border border-slate-700/50">
        <div className="absolute inset-0 flex">
          {/* Sabotage (Red) Side */}
          <div
            className={clsx(
              'flex items-center justify-start pl-2 transition-all duration-300',
              isUnderSiege ? 'bg-red-500' : 'bg-red-500/70'
            )}
            style={{ width: `${Math.max(war.sabotage_pct, 5)}%` }}
          />

          {/* Shield (Emerald) Side */}
          <div
            className={clsx(
              'flex items-center justify-end pr-2 transition-all duration-300 ml-auto',
              isDefended ? 'bg-emerald-500' : 'bg-emerald-500/70'
            )}
            style={{ width: `${Math.max(100 - war.sabotage_pct, 5)}%` }}
          />
        </div>

        {/* User Stake Marker */}
        {userStakePercent > 0 && (
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-blue-400 z-10"
            style={{ left: `${Math.min(userStakePercent, 100)}%` }}
            title={`Your stake: ${userStakePercent.toFixed(1)}%`}
          >
            <div className="absolute -top-1 -translate-x-1/2 w-1.5 h-1.5 bg-blue-400 rounded-full" />
          </div>
        )}

        {/* Center Line */}
        <div className="absolute inset-y-0 left-1/2 w-px bg-white/20" />
      </div>

      {/* Pool Values */}
      <div className="flex justify-between items-center text-xs mb-2">
        <span className="text-red-400 font-mono flex items-center gap-1">
          <Skull className="w-3 h-3" />
          ${war.sabotage_pool.toLocaleString()}
        </span>
        <span className={clsx(
          'text-[10px]',
          isUnderSiege ? 'text-red-400 font-bold' : 'text-slate-500'
        )}>
          {war.sabotage_pct.toFixed(0)}%
        </span>
        <span className="text-slate-500 text-[10px]">
          {Math.round(war.sabotage_pct / 10)} / 10
        </span>
        <span className={clsx(
          'text-[10px]',
          isDefended ? 'text-emerald-400 font-bold' : 'text-slate-500'
        )}>
          {(100 - war.sabotage_pct).toFixed(0)}%
        </span>
        <span className="text-emerald-400 font-mono flex items-center gap-1">
          ${war.shield_pool.toLocaleString()}
          <Shield className="w-3 h-3" />
        </span>
      </div>

      {/* Activity Preview */}
      <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-700/30">
        {/* Attackers */}
        <div>
          <div className="flex items-center gap-1 mb-1">
            <Skull className="w-3 h-3 text-red-400" />
            <span className="text-[10px] text-red-400 font-medium">Attackers</span>
          </div>
          <div className="space-y-0.5">
            {war.recent_attacks.slice(0, 2).map((attack, i) => (
              <div key={i} className="flex items-center gap-1.5">
                <span className="text-[10px] text-red-400">💀</span>
                <span className="text-[10px] text-slate-400 truncate flex-1">{attack.agent_name}</span>
                <span className="text-[10px] text-slate-500 font-mono">${(attack.amount / 1000).toFixed(0)}K</span>
              </div>
            ))}
            {war.recent_attacks.length === 0 && (
              <span className="text-[10px] text-slate-600">No attacks</span>
            )}
          </div>
        </div>

        {/* Defenders */}
        <div>
          <div className="flex items-center gap-1 mb-1">
            <Shield className="w-3 h-3 text-emerald-400" />
            <span className="text-[10px] text-emerald-400 font-medium">Defenders</span>
          </div>
          <div className="space-y-0.5">
            {war.recent_shields.slice(0, 2).map((shield, i) => (
              <div key={i} className="flex items-center gap-1.5">
                <span className="text-[10px] text-emerald-400">🛡️</span>
                <span className="text-[10px] text-slate-400 truncate flex-1">{shield.agent_name}</span>
                <span className="text-[10px] text-slate-500 font-mono">${(shield.amount / 1000).toFixed(0)}K</span>
              </div>
            ))}
            {war.recent_shields.length === 0 && (
              <span className="text-[10px] text-slate-600">No shields</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default WarChest;
