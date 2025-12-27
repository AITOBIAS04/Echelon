import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { Shield, Radio, AlertTriangle, User, Briefcase, Database, Wallet, X, ExternalLink, Zap, ChevronDown } from 'lucide-react';
import { useParadoxes } from '../../hooks/useParadoxes';
import { ButlerWidget } from '../ButlerWidget';
import { clsx } from 'clsx';
import { useState } from 'react';

export function AppLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { data: paradoxData } = useParadoxes();
  const paradoxCount = paradoxData?.total_active || 0;
  const [showConnectModal, setShowConnectModal] = useState(false);
  const [showYieldModal, setShowYieldModal] = useState(false);

  // Mock yield data (would come from API in production)
  const pendingYield = 127.50;
  const totalEarned = 1842.30;
  const activeTimelines = 3;
  
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
      {/* Header - fixed height, ensure no horizontal overflow */}
      <header className="flex-shrink-0 h-14 bg-terminal-panel border-b border-terminal-border flex items-center justify-between px-2 sm:px-3 md:px-4 gap-1 sm:gap-2 overflow-hidden">
        {/* Left section - Logo + Nav */}
        <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0 min-w-0">
          {/* Logo - Always visible, minimal space */}
          <NavLink to="/" className="flex items-center gap-1.5 sm:gap-2 flex-shrink-0">
            <Shield className="w-5 h-5 sm:w-6 sm:h-6 text-echelon-cyan flex-shrink-0" />
            <span className="font-display text-base sm:text-lg md:text-xl tracking-wider text-echelon-cyan glow-green whitespace-nowrap hidden sm:inline">
              ECHELON
            </span>
          </NavLink>

          {/* Divider - Hidden on very small screens */}
          <div className="h-6 w-px bg-gray-700 flex-shrink-0 hidden sm:block" />

          {/* Main Navigation - Primary Tabs - More compact, hide labels on smaller screens */}
          <nav className="hidden md:flex items-center gap-0.5 sm:gap-1 flex-shrink-0 min-w-0">
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
                    'flex items-center gap-1 px-1.5 sm:px-2 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all whitespace-nowrap flex-shrink-0',
                    isActive
                      ? 'bg-echelon-cyan/20 text-echelon-cyan border border-echelon-cyan/30'
                      : 'text-terminal-muted hover:text-terminal-text hover:bg-terminal-bg'
                  )}
                  title={item.label}
                >
                  <Icon className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />
                  <span className="hidden lg:inline">{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Right section - Status indicators + Connect - Always visible */}
        <div className="flex items-center gap-1 sm:gap-1.5 flex-shrink-0">
          {/* View Mode Toggle - Hidden on smaller screens to save space */}
          <div className="hidden lg:flex items-center bg-terminal-bg rounded-lg p-0.5 border border-terminal-border flex-shrink-0">
            <button
              onClick={() => handleViewModeChange('global')}
              className={clsx(
                'px-1.5 py-1 rounded text-xs font-bold transition-colors whitespace-nowrap',
                viewMode === 'global'
                  ? 'bg-echelon-cyan/20 text-echelon-cyan border border-echelon-cyan/30'
                  : 'text-terminal-muted hover:text-terminal-text'
              )}
            >
              📡
            </button>
            <button
              onClick={() => handleViewModeChange('personal')}
              className={clsx(
                'px-1.5 py-1 rounded text-xs font-bold transition-colors whitespace-nowrap',
                viewMode === 'personal'
                  ? 'bg-echelon-purple/20 text-echelon-purple border border-echelon-purple/30'
                  : 'text-terminal-muted hover:text-terminal-text'
              )}
            >
              🎒
            </button>
          </div>

          {/* Divider - Hidden on small screens */}
          <div className="h-6 w-px bg-gray-700 flex-shrink-0 hidden lg:block" />

          {/* Live Indicator - Compact, icon only on very small screens */}
          <div className="flex items-center gap-0.5 sm:gap-1 px-1 sm:px-1.5 py-1 bg-green-900/30 border border-green-500/30 rounded-lg flex-shrink-0">
            <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-green-500 rounded-full animate-pulse flex-shrink-0" />
            <span className="text-green-400 text-[10px] sm:text-xs font-bold uppercase whitespace-nowrap hidden sm:inline">LIVE</span>
          </div>

          {/* Paradox Alert - Ultra compact, show only icon + number on small screens */}
          {paradoxCount > 0 && (
            <NavLink
              to="/sigint"
              className="flex items-center gap-0.5 sm:gap-1 px-1 sm:px-1.5 py-1 bg-echelon-red/20 border border-echelon-red/50 rounded-lg animate-pulse whitespace-nowrap flex-shrink-0"
            >
              <AlertTriangle className="w-3 h-3 text-echelon-red flex-shrink-0" />
              <span className="text-[10px] sm:text-xs text-echelon-red font-bold">
                {paradoxCount}
              </span>
              <span className="text-[10px] sm:text-xs text-echelon-red uppercase font-bold hidden md:inline">
                BREACH{paradoxCount > 1 ? 'ES' : ''}
              </span>
            </NavLink>
          )}

          {/* Founder's Yield Widget - Hide on smaller screens to ensure Connect button is always visible */}
          <div className="relative flex-shrink-0 hidden lg:block">
            <button
              onClick={() => setShowYieldModal(!showYieldModal)}
              className="flex items-center gap-1 px-1.5 sm:px-2 py-1 bg-amber-900/20 border border-amber-500/30 rounded-lg hover:border-amber-500/50 transition-all group whitespace-nowrap"
            >
              <Zap className="w-3 h-3 text-amber-400 flex-shrink-0" />
              <span className="text-amber-400 text-[10px] sm:text-xs font-bold font-mono">
                ${pendingYield.toFixed(2)}
              </span>
              <ChevronDown className={clsx(
                'w-3 h-3 text-amber-400/50 transition-transform flex-shrink-0 hidden xl:block',
                showYieldModal && 'rotate-180'
              )} />
            </button>

            {/* Yield Dropdown */}
            {showYieldModal && (
              <div className="absolute top-full right-0 mt-2 w-72 bg-[#0D0D0D] border border-amber-500/30 rounded-lg shadow-xl z-[60] overflow-hidden">
                {/* Header */}
                <div className="p-4 border-b border-gray-800 bg-amber-900/10">
                  <div className="flex items-center justify-between">
                    <h3 className="text-amber-400 font-bold flex items-center gap-2">
                      <Zap className="w-4 h-4" />
                      FOUNDER'S YIELD
                    </h3>
                    <button onClick={() => setShowYieldModal(false)} className="text-gray-500 hover:text-white">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  <p className="text-gray-500 text-xs mt-1">Passive income from your timelines</p>
                </div>

                {/* Stats */}
                <div className="p-4 space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400 text-sm">Pending Yield</span>
                    <span className="text-amber-400 font-bold font-mono text-lg">${pendingYield.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400 text-sm">Total Earned</span>
                    <span className="text-green-400 font-mono">${totalEarned.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400 text-sm">Active Timelines</span>
                    <span className="text-cyan-400">{activeTimelines} earning</span>
                  </div>

                  {/* Timeline Breakdown */}
                  <div className="pt-3 border-t border-gray-800">
                    <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">Yield by Timeline</p>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-gray-300">Oil Crisis - Hormuz</span>
                        <span className="text-amber-400 font-mono">$52.30/hr</span>
                      </div>
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-gray-300">Fed Rate Decision</span>
                        <span className="text-amber-400 font-mono">$38.10/hr</span>
                      </div>
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-gray-300">Contagion Zero</span>
                        <span className="text-amber-400 font-mono">$37.10/hr</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Claim Button */}
                <div className="p-4 border-t border-gray-800 bg-gray-900/50">
                  <button
                    disabled
                    className="w-full px-4 py-3 bg-amber-900/30 border border-amber-500/30 text-amber-400/50 rounded-lg font-bold cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    <Zap className="w-4 h-4" />
                    CONNECT WALLET TO CLAIM
                  </button>
                  <p className="text-center text-gray-600 text-xs mt-2">
                    Min. claim: $50.00
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Connect Button - ALWAYS visible, highest priority, never gets cut off */}
          <button 
            onClick={() => setShowConnectModal(true)}
            className="flex items-center justify-center gap-1 px-2 sm:px-2.5 md:px-3 py-1.5 sm:py-2 border border-gray-600 text-gray-300 rounded-lg hover:border-echelon-cyan hover:text-echelon-cyan transition-all whitespace-nowrap flex-shrink-0 min-w-[40px] sm:min-w-[44px]"
            title="Connect Wallet"
          >
            <User className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />
            <span className="hidden sm:inline text-xs sm:text-sm">Connect</span>
          </button>
        </div>
      </header>

      {/* Connect Wallet Modal */}
      {showConnectModal && (
        <div 
          className="fixed inset-0 z-[100] flex items-center justify-center p-4"
          onClick={() => setShowConnectModal(false)}
        >
          {/* Dark overlay */}
          <div className="absolute inset-0 bg-black/90 backdrop-blur-sm" />
          
          {/* Modal content - above overlay */}
          <div 
            className="relative z-10 bg-[#0D0D0D] border border-echelon-cyan/50 rounded-lg p-6 max-w-md w-full mx-4 animate-in fade-in zoom-in-95 duration-200"
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

      {/* Butler Widget - Floating CTA */}
      <ButlerWidget />
    </div>
  );
}

