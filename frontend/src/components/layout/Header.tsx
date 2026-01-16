import { Shield, Radio, AlertTriangle, User } from 'lucide-react';

interface HeaderProps {
  paradoxCount: number;
  onBreachesClick: () => void;
}

export function Header({ paradoxCount, onBreachesClick }: HeaderProps) {
  return (
    <header className="h-14 bg-terminal-panel border-b border-terminal-border flex items-center justify-between px-6">
      {/* Logo */}
      <div className="flex items-center gap-3">
        <Shield className="w-6 h-6 text-echelon-cyan" />
        <span className="font-display text-xl tracking-wider text-echelon-cyan glow-green">
          ECHELON
        </span>
        <span className="text-xs text-terminal-muted uppercase tracking-widest">
          Situation Room
        </span>
      </div>

      {/* Status Indicators */}
      <div className="flex items-center gap-6">
        {/* Live Feed Status */}
        <div className="flex items-center gap-2">
          <Radio className="w-4 h-4 text-echelon-green animate-pulse" />
          <span className="text-xs text-echelon-green uppercase">Live</span>
        </div>

        {/* Paradox Alert - Clickable */}
        {paradoxCount > 0 && (
          <button 
            onClick={onBreachesClick}
            className="flex items-center gap-2 px-3 py-1.5 bg-echelon-red/20 border border-echelon-red/50 rounded animate-pulse hover:bg-echelon-red/30 transition"
          >
            <AlertTriangle className="w-4 h-4 text-echelon-red" />
            <span className="text-xs text-echelon-red uppercase font-bold">
              {paradoxCount} Active Breach{paradoxCount > 1 ? 'es' : ''}
            </span>
          </button>
        )}

        {/* User */}
        <button className="flex items-center gap-2 text-terminal-muted hover:text-terminal-text transition">
          <User className="w-4 h-4" />
          <span className="text-xs">Connect</span>
        </button>
      </div>
    </header>
  );
}
