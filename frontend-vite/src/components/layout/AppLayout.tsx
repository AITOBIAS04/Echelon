import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { Shield, Radio, AlertTriangle, User, Activity, Briefcase, Database } from 'lucide-react';
import { useParadoxes } from '../../hooks/useParadoxes';
import { clsx } from 'clsx';
import { useState } from 'react';

export function AppLayout() {
  const location = useLocation();
  const { data: paradoxData } = useParadoxes();
  const paradoxCount = paradoxData?.total_active || 0;
  const [showConnectModal, setShowConnectModal] = useState(false);

  const navItems = [
    { path: '/sigint', label: 'SIGINT', icon: Radio },
    { path: '/fieldkit', label: 'Field Kit', icon: Briefcase },
    { path: '/blackbox', label: 'Blackbox', icon: Database },
    { path: '/agents', label: 'Agents', icon: User },
  ];

  return (
    <div className="h-screen flex flex-col bg-terminal-bg overflow-hidden">
      {/* Header - fixed height */}
      <header className="flex-shrink-0 h-14 bg-terminal-panel border-b border-terminal-border flex items-center justify-between px-6">
        {/* Logo */}
        <NavLink to="/" className="flex items-center gap-3">
          <Shield className="w-6 h-6 text-echelon-cyan" />
          <span className="font-display text-xl tracking-wider text-echelon-cyan glow-green">
            ECHELON
          </span>
        </NavLink>

        {/* Navigation */}
        <nav className="flex items-center gap-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              location.pathname === item.path ||
              (item.path === '/sigint' && location.pathname === '/');

            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={clsx(
                  'flex items-center gap-2 px-4 py-2 rounded transition-all',
                  isActive
                    ? 'bg-echelon-cyan/20 text-echelon-cyan border border-echelon-cyan/30'
                    : 'text-terminal-muted hover:text-terminal-text hover:bg-terminal-bg'
                )}
              >
                <Icon className="w-4 h-4" />
                <span className="text-sm font-medium">{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Right Side */}
        <div className="flex items-center gap-4">
          {/* Live Indicator */}
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-echelon-green animate-pulse" />
            <span className="text-xs text-echelon-green uppercase">Live</span>
          </div>

          {/* Paradox Alert */}
          {paradoxCount > 0 && (
            <NavLink
              to="/sigint"
              className="flex items-center gap-2 px-3 py-1.5 bg-echelon-red/20 border border-echelon-red/50 rounded animate-pulse"
            >
              <AlertTriangle className="w-4 h-4 text-echelon-red" />
              <span className="text-xs text-echelon-red uppercase font-bold">
                {paradoxCount} Active Breach{paradoxCount > 1 ? 'es' : ''}
              </span>
            </NavLink>
          )}

          {/* Connect Button */}
          <button 
            onClick={() => setShowConnectModal(true)}
            className="flex items-center gap-2 px-4 py-2 border border-terminal-border rounded text-terminal-muted hover:text-terminal-text hover:border-echelon-cyan transition"
          >
            <User className="w-4 h-4" />
            <span className="text-sm">Connect</span>
          </button>
        </div>
      </header>

      {/* Connect Wallet Modal */}
      {showConnectModal && (
        <div 
          className="fixed inset-0 bg-black/80 flex items-center justify-center z-50"
          onClick={() => setShowConnectModal(false)}
        >
          <div 
            className="bg-[#0D0D0D] border border-echelon-cyan/50 rounded-lg p-6 max-w-md text-center"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="text-4xl mb-4">🔐</div>
            <h3 className="text-echelon-cyan font-bold text-lg mb-2">WALLET CONNECTION</h3>
            <p className="text-terminal-muted text-sm mb-4">
              Connect your wallet to trade Shards, hire Agents, and earn Founder's Yield.
            </p>
            <div className="bg-echelon-amber/20 border border-echelon-amber/30 rounded p-3 mb-6">
              <p className="text-echelon-amber text-xs">
                ⚡ Coming Q1 2025 — Join the waitlist at{' '}
                <span className="text-echelon-cyan">playechelon.io</span>
              </p>
            </div>
            <button 
              onClick={() => setShowConnectModal(false)}
              className="px-6 py-2 bg-echelon-cyan/20 border border-echelon-cyan text-echelon-cyan rounded hover:bg-echelon-cyan/30 transition-colors"
            >
              CLOSE
            </button>
          </div>
        </div>
      )}

      {/* Main content - takes remaining space, no overflow */}
      <main className="flex-1 min-h-0 overflow-hidden p-6">
        {/* Child panels handle their own scrolling */}
        <Outlet />
      </main>
    </div>
  );
}

