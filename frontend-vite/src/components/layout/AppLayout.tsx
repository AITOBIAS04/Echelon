import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { Shield, Radio, AlertTriangle, User, Activity, Briefcase, Database, Wallet, X, ExternalLink } from 'lucide-react';
import { useParadoxes } from '../../hooks/useParadoxes';
import { clsx } from 'clsx';
import { useState } from 'react';

export function AppLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { data: paradoxData } = useParadoxes();
  const paradoxCount = paradoxData?.total_active || 0;
  const [showConnectModal, setShowConnectModal] = useState(false);
  
  // Determine view mode based on current route
  const viewMode = location.pathname === '/fieldkit' ? 'personal' : 'global';
  
  const handleViewModeChange = (mode: 'global' | 'personal') => {
    if (mode === 'global') {
      navigate('/sigint');
    } else {
      navigate('/fieldkit');
    }
  };

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
        
        {/* View Mode Toggle */}
        <div className="flex items-center bg-terminal-bg rounded-lg p-1 border border-terminal-border">
          <button
            onClick={() => handleViewModeChange('global')}
            className={clsx(
              'px-3 py-1.5 rounded text-sm font-bold transition-colors',
              viewMode === 'global'
                ? 'bg-echelon-cyan/20 text-echelon-cyan'
                : 'text-terminal-muted hover:text-terminal-text'
            )}
          >
            📡 GLOBAL SIGINT
          </button>
          <button
            onClick={() => handleViewModeChange('personal')}
            className={clsx(
              'px-3 py-1.5 rounded text-sm font-bold transition-colors',
              viewMode === 'personal'
                ? 'bg-echelon-purple/20 text-echelon-purple'
                : 'text-terminal-muted hover:text-terminal-text'
            )}
          >
            🎒 FIELD KIT
          </button>
        </div>

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
            className="flex items-center gap-2 px-4 py-2 border border-terminal-border rounded-lg text-terminal-muted hover:text-terminal-text hover:border-echelon-cyan transition-all"
          >
            <User className="w-4 h-4" />
            <span>Connect</span>
          </button>
        </div>
      </header>

      {/* Connect Wallet Modal */}
      {showConnectModal && (
        <div 
          className="fixed inset-0 bg-black/90 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={() => setShowConnectModal(false)}
        >
          <div 
            className="bg-[#0D0D0D] border border-echelon-cyan/50 rounded-lg p-6 max-w-md w-full relative animate-in fade-in zoom-in-95 duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            <button 
              onClick={() => setShowConnectModal(false)}
              className="absolute top-4 right-4 text-terminal-muted hover:text-terminal-text transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
            
            <div className="flex justify-center mb-6">
              <div className="w-20 h-20 bg-gradient-to-br from-echelon-cyan/20 to-echelon-purple/20 rounded-full flex items-center justify-center border border-echelon-cyan/30">
                <Wallet className="w-10 h-10 text-echelon-cyan" />
              </div>
            </div>
            
            <h3 className="text-echelon-cyan font-bold text-xl text-center mb-2">
              CONNECT WALLET
            </h3>
            <p className="text-terminal-muted text-sm text-center mb-6">
              Connect to trade Shards, hire Agents, and earn Founder's Yield
            </p>
            
            <div className="space-y-3 mb-6">
              <button 
                disabled
                className="w-full flex items-center gap-4 px-4 py-3.5 bg-terminal-bg border border-terminal-border rounded-lg text-terminal-muted cursor-not-allowed group"
              >
                <div className="w-8 h-8 rounded-full bg-orange-500/20 flex items-center justify-center">
                  <span className="text-lg">🦊</span>
                </div>
                <span className="flex-1 text-left">MetaMask</span>
                <span className="text-xs bg-terminal-bg px-2 py-1 rounded">SOON</span>
              </button>
              
              <button 
                disabled
                className="w-full flex items-center gap-4 px-4 py-3.5 bg-terminal-bg border border-terminal-border rounded-lg text-terminal-muted cursor-not-allowed"
              >
                <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center">
                  <span className="text-white text-sm font-bold">C</span>
                </div>
                <span className="flex-1 text-left">Coinbase Wallet</span>
                <span className="text-xs bg-terminal-bg px-2 py-1 rounded">SOON</span>
              </button>
              
              <button 
                disabled
                className="w-full flex items-center gap-4 px-4 py-3.5 bg-terminal-bg border border-terminal-border rounded-lg text-terminal-muted cursor-not-allowed"
              >
                <div className="w-8 h-8 rounded-full bg-echelon-purple/20 flex items-center justify-center">
                  <span className="text-white text-sm font-bold">W</span>
                </div>
                <span className="flex-1 text-left">WalletConnect</span>
                <span className="text-xs bg-terminal-bg px-2 py-1 rounded">SOON</span>
              </button>
            </div>
            
            <div className="bg-gradient-to-r from-echelon-cyan/20 to-echelon-purple/20 border border-echelon-cyan/30 rounded-lg p-4 text-center mb-6">
              <p className="text-echelon-cyan font-bold mb-1">🚀 Launching Q1 2025</p>
              <p className="text-terminal-muted text-sm">
                Join the waitlist for early access
              </p>
            </div>
            
            <div className="flex justify-center gap-6 text-sm">
              <a 
                href="https://x.com/play_echelon" 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 text-terminal-muted hover:text-echelon-cyan transition-colors"
              >
                <span>@play_echelon</span>
                <ExternalLink className="w-3 h-3" />
              </a>
              <a 
                href="mailto:playechelon0@gmail.com"
                className="flex items-center gap-1.5 text-terminal-muted hover:text-echelon-cyan transition-colors"
              >
                <span>Contact</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
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

