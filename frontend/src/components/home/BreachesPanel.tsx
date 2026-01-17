import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBreaches } from '../../hooks/useBreaches';
import type { Breach } from '../../types/breach';

function formatTimeAgo(iso: string): string {
  const ms = Date.now() - Date.parse(iso);
  if (Number.isNaN(ms) || ms < 0) return 'now';
  const sec = Math.floor(ms / 1000);
  if (sec < 60) return `${sec}s`; 
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m`;
  const hr = Math.floor(min / 60);
  if (hr < 48) return `${hr}h`;
  const day = Math.floor(hr / 24);
  return `${day}d`;
}

function severityColor(sev: Breach['severity']): string {
  switch (sev) {
    case 'low':
      return 'bg-green-500/70';
    case 'medium':
      return 'bg-amber-500/70';
    case 'high':
      return 'bg-orange-500/70';
    case 'critical':
      return 'bg-red-500/80';
  }
}

function categoryLabel(cat: Breach['category']): string {
  switch (cat) {
    case 'logic_gap_spike':
      return 'GAP';
    case 'sensor_contradiction':
      return 'SENSOR';
    case 'sabotage_cluster':
      return 'SABOTAGE';
    case 'oracle_flip':
      return 'ORACLE';
    case 'stability_collapse':
      return 'STABILITY';
    case 'paradox_detonation':
      return 'PARADOX';
  }
}

export function BreachesPanel({ maxItems = 8 }: { maxItems?: number }) {
  const navigate = useNavigate();
  const { data: breaches = [], isLoading } = useBreaches();

  const active = useMemo(() => {
    // Keep it terminal-like: show active/investigating first, newest first.
    const sorted = [...breaches].sort((a, b) => Date.parse(b.timestamp) - Date.parse(a.timestamp));
    return sorted.slice(0, maxItems);
  }, [breaches, maxItems]);

  return (
    <div className="flex flex-col h-full min-h-0">
      <div className="flex items-center justify-between px-3 py-2 border-b border-terminal-border/50 bg-terminal-bg/95 backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-[#AA66FF]" />
          <h3 className="text-sm font-bold text-terminal-text uppercase tracking-wide">Breaches</h3>
        </div>
        <button
          onClick={() => navigate('/breaches')}
          className="text-[11px] text-terminal-muted hover:text-terminal-text transition"
        >
          View all
        </button>
      </div>

      <div className="flex-1 min-h-0 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
        {isLoading ? (
          <div className="text-terminal-muted text-xs py-6 text-center">Loading breaches…</div>
        ) : active.length === 0 ? (
          <div className="text-terminal-muted text-xs py-6 text-center">No active breaches</div>
        ) : (
          <div className="flex flex-col">
            {active.map((b) => (
              <button
                key={b.id}
                onClick={() => navigate('/breaches')}
                className="text-left px-3 py-2 hover:bg-white/5 border-b border-terminal-border/30 last:border-b-0 transition"
              >
                <div className="flex items-center gap-2">
                  <span className={`w-1.5 h-1.5 rounded-full ${severityColor(b.severity)}`} />
                  <span className="text-[10px] font-mono text-terminal-muted">{categoryLabel(b.category)}</span>
                  <span className="text-[10px] font-mono text-terminal-muted ml-auto">{formatTimeAgo(b.timestamp)}</span>
                </div>
                <div className="text-xs text-terminal-text truncate mt-0.5">{b.title}</div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
