import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { Shield, Radio, AlertTriangle, User, Briefcase, Database, Wallet, X, ExternalLink, Zap, ChevronDown, Menu, BarChart3, Activity } from 'lucide-react';
import { useParadoxes } from '../../hooks/useParadoxes';
import { ButlerWidget } from '../ButlerWidget';
import { clsx } from 'clsx';
import { useState, useEffect, useRef } from 'react';

export function AppLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { data: paradoxData } = useParadoxes();
  const paradoxCount = paradoxData?.total_active || 0;
  const [showConnectModal, setShowConnectModal] = useState(false);
  const [showYieldModal, setShowYieldModal] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const yieldButtonRef = useRef<HTMLDivElement>(null);
  const [yieldDropdownPosition, setYieldDropdownPosition] = useState({ top: 0, right: 0 });

  // Mock yield data (would come from API in production)
  const pendingYield = 127.50;
  const totalEarned = 1842.30;
  const activeTimelines = 3;

  // Calculate dropdown position when opening
  useEffect(() => {
    if (showYieldModal && yieldButtonRef.current) {
      const rect = yieldButtonRef.current.getBoundingClientRect();
      setYieldDropdownPosition({
        top: rect.bottom + window.scrollY + 8,
        right: window.innerWidth - rect.right,
      });
    }
  }, [showYieldModal]);

  // Lock body scroll when modals are open
  useEffect(() => {
    if (showConnectModal || showYieldModal || showMobileMenu) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [showConnectModal, showYieldModal, showMobileMenu]);
  
  // Determine view mode based on current route
  const viewMode = location.pathname === '/fieldkit' ? 'personal' : 'global';
  
  const handleViewModeChange = (mode: 'global' | 'personal') => {
    if (mode === 'global') {
      navigate('/'); // SIGINT now points to HOME (Ops Board)
    } else {
      navigate('/fieldkit');
    }
  };

  const navItems = [
    { path: '/', label: 'Markets', icon: BarChart3 },
    { path: '/fieldkit', label: 'Portfolio', icon: Briefcase },
    { path: '/blackbox', label: 'Analytics', icon: Activity },
    { path: '/breaches', label: 'Alerts', icon: AlertTriangle },
    { path: '/agents', label: 'Agents', icon: User },
  ];

  return (
    <div className="min-h-[100dvh] h-[100dvh] flex flex-col bg-terminal-bg overflow-hidden">
      {/* Header - fixed height, max 64px, ensure no horizontal overflow but allow dropdowns to overflow */}
      <header className="flex-shrink-0 h-14 max-h-16 bg-terminal-panel border-b border-terminal-border flex items-center justify-between px-2 sm:px-3 md:px-4 gap-1 sm:gap-2 overflow-x-auto overflow-y-visible">
        {/* Left section - Logo + Nav */}
        <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0 min-w-0">
          {/* Logo - Always visible, minimal space */}
          <NavLink to="/" className="flex items-center gap-1.5 sm:gap-2 flex-shrink-0">
            <Shield className="w-5 h-5 sm:w-6 sm:h-6 text-status-success flex-shrink-0" />
            <span className="font-sans text-base sm:text-lg md:text-xl font-bold tracking-wide text-terminal-text whitespace-nowrap hidden sm:inline">
              ECHELON
            </span>
          </NavLink>

          {/* Divider - Hidden on very small screens */}
          <div className="h-6 w-px bg-gray-700 flex-shrink-0 hidden sm:block" />

          {/* Mobile Menu Button */}
          <button
            onClick={() => setShowMobileMenu(!showMobileMenu)}
            className="md:hidden flex items-center justify-center p-1.5 text-terminal-muted hover:text-terminal-text transition-colors"
            aria-label="Toggle menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Main Navigation - Primary Tabs - Desktop */}
          <nav className="hidden md:flex items-center gap-0.5 sm:gap-1 flex-shrink-0 min-w-0">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = item.path === '/' 
                ? location.pathname === '/' 
                : location.pathname === item.path;

              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={clsx(
                    'flex items-center gap-1 px-1.5 sm:px-2 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all whitespace-nowrap flex-shrink-0',
                    isActive
                      ? 'bg-status-info/10 text-status-info border border-status-info/20'
                      : 'text-terminal-text-secondary hover:text-terminal-text hover:bg-terminal-bg'
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
                  ? 'bg-status-info/10 text-status-info border border-status-info/20'
                  : 'text-terminal-text-secondary hover:text-terminal-text'
              )}
            >
              <BarChart3 className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => handleViewModeChange('personal')}
              className={clsx(
                'px-1.5 py-1 rounded text-xs font-bold transition-colors whitespace-nowrap',
                viewMode === 'personal'
                  ? 'bg-status-success/10 text-status-success border border-status-success/20'
                  : 'text-terminal-text-secondary hover:text-terminal-text'
              )}
            >
              <Briefcase className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Divider - Hidden on small screens */}
          <div className="h-6 w-px bg-gray-700 flex-shrink-0 hidden lg:block" />

          {/* Live Indicator - Compact, icon only on very small screens */}
          <div className="flex items-center gap-0.5 sm:gap-1 px-1 sm:px-1.5 py-1 bg-status-success/10 border border-status-success/20 rounded-lg flex-shrink-0">
            <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-status-success rounded-full animate-pulse flex-shrink-0" />
            <span className="text-status-success text-[10px] sm:text-xs font-semibold uppercase whitespace-nowrap hidden sm:inline">LIVE</span>
          </div>

          {/* Paradox Alert - Ultra compact, show only icon + number on small screens */}
          {paradoxCount > 0 && (
            <NavLink
              to="/breaches"
              className="flex items-center gap-0.5 sm:gap-1 px-1 sm:px-1.5 py-1 bg-status-danger/10 border border-status-danger/20 rounded-lg animate-pulse whitespace-nowrap flex-shrink-0"
            >
              <AlertTriangle className="w-3 h-3 text-status-danger flex-shrink-0" />
              <span className="text-[10px] sm:text-xs text-status-danger font-bold">
                {paradoxCount}
              </span>
              <span className="text-[10px] sm:text-xs text-status-danger font-semibold uppercase hidden md:inline">
                ALERT{paradoxCount > 1 ? 'S' : ''}
              </span>
            </NavLink>
          )}

          {/* Mobile Yield Button (so yield is always discoverable on phones) */}
          <button
            onClick={() => setShowYieldModal(true)}
            className="lg:hidden flex items-center gap-1 px-2 py-1 bg-status-warning/10 border border-status-warning/20 rounded-lg hover:border-status-warning/30 transition-all whitespace-nowrap flex-shrink-0"
            title="Yield"
          >
            <Zap className="w-4 h-4 text-status-warning flex-shrink-0" />
            <span className="text-status-warning text-[10px] font-bold font-mono hidden sm:inline">
              ${pendingYield.toFixed(2)}
            </span>
          </button>

          {/* Founder's Yield Widget - Hide on smaller screens to ensure Connect button is always visible */}
          <div ref={yieldButtonRef} className="relative flex-shrink-0 hidden lg:block z-50">
            <button
              onClick={() => setShowYieldModal(!showYieldModal)}
              className="flex items-center gap-1 px-1.5 sm:px-2 py-1 bg-status-warning/10 border border-status-warning/20 rounded-lg hover:border-status-warning/30 transition-all group whitespace-nowrap"
            >
              <Zap className="w-3 h-3 text-status-warning flex-shrink-0" />
              <span className="text-status-warning text-[10px] sm:text-xs font-bold font-mono">
                ${pendingYield.toFixed(2)}
              </span>
              <ChevronDown className={clsx(
                'w-3 h-3 text-status-warning/50 transition-transform flex-shrink-0 hidden xl:block',
                showYieldModal && 'rotate-180'
              )} />
            </button>

            {/* Yield Dropdown - Fixed positioning to escape header overflow */}
            {showYieldModal && (
              <>
                {/* Backdrop to close on outside click */}
                <div 
                  className="fixed inset-0 z-[9998]" 
                  onClick={() => setShowYieldModal(false)}
                />
                <div 
                  className="fixed w-72 sm:w-80 bg-[#0D0D0D] border border-amber-500/30 rounded-lg shadow-xl z-[9999] overflow-hidden"
                  style={{ 
                    top: `${yieldDropdownPosition.top}px`,
                    right: `${yieldDropdownPosition.right}px`,
                    maxWidth: 'calc(100vw - 1rem)',
                  }}
                >
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
              </>
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

      {/* Mobile Navigation Menu */}
      {showMobileMenu && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 bg-black/80 z-[9980] md:hidden"
            onClick={() => setShowMobileMenu(false)}
          />
          {/* Menu */}
          <div className="fixed top-14 left-0 right-0 bg-terminal-panel border-b border-terminal-border z-[9985] md:hidden shadow-xl">
            <nav className="flex flex-col p-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = item.path === '/' 
                ? location.pathname === '/' 
                : location.pathname === item.path;

                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    onClick={() => setShowMobileMenu(false)}
                    className={clsx(
                      'flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all',
                      isActive
                        ? 'bg-echelon-cyan/20 text-echelon-cyan border border-echelon-cyan/30'
                        : 'text-terminal-muted hover:text-terminal-text hover:bg-terminal-bg'
                    )}
                  >
                    <Icon className="w-5 h-5 flex-shrink-0" />
                    <span>{item.label}</span>
                  </NavLink>
                );
              })}
            </nav>
          </div>
        </>
      )}

      {/* Mobile Founder's Yield Modal (phones don't render the desktop dropdown) */}
      {showYieldModal && (
        <>
          <div
            className="fixed inset-0 bg-black/95 backdrop-blur-md z-[9990] lg:hidden"
            onClick={() => setShowYieldModal(false)}
          />
          <div className="fixed inset-0 z-[9995] flex items-center justify-center p-4 lg:hidden">
            <div
              className="relative w-full max-w-md bg-[#0D0D0D] border border-amber-500/30 rounded-lg shadow-2xl overflow-hidden max-h-[90dvh] overflow-y-auto overscroll-contain"
              style={{ WebkitOverflowScrolling: 'touch' }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-4 border-b border-gray-800 bg-amber-900/10 sticky top-0 z-10">
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

                <div className="pt-3 border-t border-gray-800">
                  <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">Yield by Timeline</p>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center text-sm gap-3">
                      <span className="text-gray-300 truncate">Oil Crisis - Hormuz</span>
                      <span className="text-amber-400 font-mono whitespace-nowrap">$52.30/hr</span>
                    </div>
                    <div className="flex justify-between items-center text-sm gap-3">
                      <span className="text-gray-300 truncate">Fed Rate Decision</span>
                      <span className="text-amber-400 font-mono whitespace-nowrap">$38.10/hr</span>
                    </div>
                    <div className="flex justify-between items-center text-sm gap-3">
                      <span className="text-gray-300 truncate">Contagion Zero</span>
                      <span className="text-amber-400 font-mono whitespace-nowrap">$37.10/hr</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="p-4 border-t border-gray-800 bg-gray-900/50">
                <button
                  disabled
                  className="w-full px-4 py-3 bg-amber-900/30 border border-amber-500/30 text-amber-400/50 rounded-lg font-bold cursor-not-allowed flex items-center justify-center gap-2"
                >
                  <Zap className="w-4 h-4" />
                  CONNECT WALLET TO CLAIM
                </button>
                <p className="text-center text-gray-600 text-xs mt-2">Min. claim: $50.00</p>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Connect Wallet Modal */}
      {showConnectModal && (
        <>
          {/* Dark overlay - blocks all background content and pointer events */}
          <div 
            className="fixed inset-0 bg-black/95 backdrop-blur-md z-[9990]"
            style={{ pointerEvents: 'auto' }}
            onClick={() => setShowConnectModal(false)}
          />
          
          {/* Modal content - above overlay */}
          <div 
            className="fixed inset-0 z-[9995] flex items-center justify-center p-4 pointer-events-none"
            onClick={() => setShowConnectModal(false)}
          >
            <div 
              className="bg-[#0D0D0D] border border-echelon-cyan/50 rounded-lg p-4 sm:p-6 max-w-md w-full mx-2 sm:mx-4 animate-in fade-in zoom-in-95 duration-200 max-h-[90vh] overflow-y-auto pointer-events-auto"
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
        </>
      )}

      {/* Main content - takes remaining space, no overflow */}
      <main className="flex-1 min-h-0 overflow-hidden p-2 sm:p-4 md:p-6 pb-20 md:pb-6">
        {/* Child panels handle their own scrolling */}
        <Outlet />
      </main>

      {/* Mobile Bottom Tabs (primary navigation on phones) */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-[60] bg-terminal-panel/95 backdrop-blur border-t border-terminal-border">
        <div className="flex items-center justify-around px-2 py-2 pb-[calc(env(safe-area-inset-bottom)+0.5rem)]">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;

            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => setShowMobileMenu(false)}
                className={clsx(
                  'flex flex-col items-center justify-center gap-1 px-3 py-1.5 rounded-lg min-w-[64px]',
                  isActive
                    ? 'text-echelon-cyan'
                    : 'text-terminal-muted hover:text-terminal-text'
                )}
              >
                <Icon className={clsx('w-5 h-5', isActive && 'glow-green')} />
                <span className={clsx('text-[10px] font-bold', isActive && 'text-echelon-cyan')}>
                  {item.label}
                </span>
              </NavLink>
            );
          })}
        </div>
      </nav>

      {/* Butler Widget - Floating CTA */}
      <ButlerWidget />
    </div>
  );
}

