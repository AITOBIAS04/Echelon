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
          <Activity className="w-4 h-4 text-echelon-blue animate-pulse" />
          <span className="text-terminal-text-secondary text-xs">Loading war data...</span>
        </div>
      </div>
    );
  }

  if (warData.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-terminal-text-secondary">
        <Swords className="w-8 h-8 mb-2 text-terminal-text-muted opacity-50" />
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
        'bg-terminal-panel border border-terminal-border rounded p-3',
        isUnderSiege ? 'border-echelon-red/30' :
        isDefended ? 'border-echelon-green/30' :
        'border-echelon-amber/30'
      )}
    >
      {/* Header Row */}
      <div className="flex items-start gap-3 mb-3">
        {/* Timeline Image Tile - 40x40px */}
        <div className="flex-shrink-0 w-10 h-10 border border-terminal-border rounded bg-terminal-card flex items-center justify-center overflow-hidden">
          {war.image_url ? (
            <img 
              src={war.image_url} 
              alt={war.timeline_name}
              className="w-full h-full object-cover"
            />
          ) : (
            <Swords className="w-4 h-4 text-terminal-text-muted" />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex justify-between items-start gap-2">
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-terminal-text text-sm truncate cursor-pointer hover:text-echelon-blue" onClick={onClick}>
                {war.timeline_name}
              </h3>
              <span className="text-[10px] text-terminal-text-muted font-mono">${war.total_pool.toLocaleString()} pool</span>
            </div>
            <span className={clsx(
              'text-[10px] flex items-center gap-1 flex-shrink-0',
              isUnderSiege ? 'text-echelon-red' :
              isDefended ? 'text-echelon-green' :
              'text-echelon-amber'
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
              <User className="w-3 h-3 text-echelon-blue" />
              <span className="text-[10px] text-terminal-text-secondary">
                <span className="text-terminal-text font-mono">${position.totalNotional.toLocaleString()}</span>
              </span>
              <span className={clsx(
                'text-[10px] px-1.5 py-0.5 rounded',
                position.netDirection === 'YES' && 'bg-echelon-green/10 text-echelon-green',
                position.netDirection === 'NO' && 'bg-echelon-red/10 text-echelon-red'
              )}>
                {position.netDirection}
              </span>
              <span className={clsx(
                'text-[10px] font-mono',
                position.pnlValue >= 0 ? 'text-echelon-green' : 'text-echelon-red'
              )}>
                {position.pnlPercent >= 0 ? '+' : ''}{position.pnlPercent.toFixed(1)}%
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Tug of War Bar - Compact */}
      <div className="relative h-6 rounded overflow-hidden mb-2 bg-terminal-card border border-terminal-border">
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
        <span className="text-echelon-red font-mono flex items-center gap-1">
          <Skull className="w-3 h-3" />
          ${war.sabotage_pool.toLocaleString()}
        </span>
        <span className={clsx(
          'text-[10px]',
          isUnderSiege ? 'text-echelon-red font-bold' : 'text-terminal-text-muted'
        )}>
          {war.sabotage_pct.toFixed(0)}%
        </span>
        <span className="text-terminal-text-muted text-[10px]">
          {Math.round(war.sabotage_pct / 10)} / 10
        </span>
        <span className={clsx(
          'text-[10px]',
          isDefended ? 'text-echelon-green font-bold' : 'text-terminal-text-muted'
        )}>
          {(100 - war.sabotage_pct).toFixed(0)}%
        </span>
        <span className="text-echelon-green font-mono flex items-center gap-1">
          ${war.shield_pool.toLocaleString()}
          <Shield className="w-3 h-3" />
        </span>
      </div>

      {/* Activity Preview */}
      <div className="grid grid-cols-2 gap-2 pt-2 border-t border-terminal-border">
        {/* Attackers */}
        <div>
          <div className="flex items-center gap-1 mb-1">
            <Skull className="w-3 h-3 text-echelon-red" />
            <span className="text-[10px] text-echelon-red font-medium">Attackers</span>
          </div>
          <div className="space-y-0.5">
            {war.recent_attacks.slice(0, 2).map((attack, i) => (
              <div key={i} className="flex items-center gap-1.5">
                <span className="text-[10px] text-echelon-red">💀</span>
                <span className="text-[10px] text-terminal-text-secondary truncate flex-1">{attack.agent_name}</span>
                <span className="text-[10px] text-terminal-text-muted font-mono">${(attack.amount / 1000).toFixed(0)}K</span>
              </div>
            ))}
            {war.recent_attacks.length === 0 && (
              <span className="text-[10px] text-terminal-text-muted">No attacks</span>
            )}
          </div>
        </div>

        {/* Defenders */}
        <div>
          <div className="flex items-center gap-1 mb-1">
            <Shield className="w-3 h-3 text-echelon-green" />
            <span className="text-[10px] text-echelon-green font-medium">Defenders</span>
          </div>
          <div className="space-y-0.5">
            {war.recent_shields.slice(0, 2).map((shield, i) => (
              <div key={i} className="flex items-center gap-1.5">
                <span className="text-[10px] text-echelon-green">🛡️</span>
                <span className="text-[10px] text-terminal-text-secondary truncate flex-1">{shield.agent_name}</span>
                <span className="text-[10px] text-terminal-text-muted font-mono">${(shield.amount / 1000).toFixed(0)}K</span>
              </div>
            ))}
            {war.recent_shields.length === 0 && (
              <span className="text-[10px] text-terminal-text-muted">No shields</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default WarChest;
