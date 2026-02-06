import React, { useState, useCallback } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { clsx } from 'clsx';
import {
  LayoutDashboard,
  BarChart3,
  Briefcase,
  Cpu,
  Shield,
  Users,
  Rocket,
  AlertTriangle,
  Upload
} from 'lucide-react';

interface NavItem {
  path: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  matchPrefixes?: string[];
}

interface SubNavItem {
  path: string;
  label: string;
  icon?: React.ComponentType<{ className?: string }>;
}

const NAV_ITEMS: NavItem[] = [
  { path: '/marketplace', label: 'Marketplace', icon: LayoutDashboard },
  { path: '/analytics', label: 'Analytics', icon: BarChart3 },
  { path: '/portfolio', label: 'Portfolio', icon: Briefcase },
  { path: '/rlmf', label: 'RLMF', icon: Cpu },
  { path: '/launchpad', label: 'Launchpad', icon: Rocket },
  { path: '/vrf', label: 'VRF', icon: Shield },
  { path: '/agents', label: 'Agents', icon: Users, matchPrefixes: ['/agents', '/agent/'] },
];

const AGENTS_SUBNAV: SubNavItem[] = [
  { path: '/agents/breach', label: 'Breach Console', icon: AlertTriangle },
  { path: '/agents/export', label: 'Export Console', icon: Upload },
];

export function Sidebar() {
  const location = useLocation();
  const [isExpanded, setIsExpanded] = useState(false);
  const collapseTimeoutRef = React.useRef<number | null>(null);

  const isActive = useCallback((item: NavItem) => {
    if (location.pathname === item.path) return true;
    if (item.matchPrefixes) {
      return item.matchPrefixes.some((p) => location.pathname.startsWith(p));
    }
    return false;
  }, [location.pathname]);

  // Check if we're in the Agents section
  const isAgentsSection = location.pathname.startsWith('/agents') || location.pathname.startsWith('/agent/');

  const handleMouseEnter = useCallback(() => {
    if (collapseTimeoutRef.current) {
      window.clearTimeout(collapseTimeoutRef.current);
      collapseTimeoutRef.current = null;
    }
    setIsExpanded(true);
  }, []);

  const handleMouseLeave = useCallback(() => {
    collapseTimeoutRef.current = window.setTimeout(() => {
      setIsExpanded(false);
    }, 250);
  }, []);

  const NavIcon = ({ item, className }: { item: NavItem; className?: string }) => {
    const Icon = item.icon;
    return <Icon className={className} />;
  };

  return (
    <aside
      className="h-full flex-shrink-0 bg-terminal-panel border-r border-terminal-border flex flex-col py-3 gap-2 overflow-hidden transition-all duration-300 ease-out"
      style={{
        width: isExpanded ? '180px' : '64px',
        boxShadow: 'inset -1px 0 0 rgba(255,255,255,0.04), 2px 0 8px rgba(0,0,0,0.3)',
      }}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* Brand */}
      <div className={clsx(
        "flex items-center px-3 py-2 border border-terminal-border rounded-lg transition-all duration-300",
        "bg-gradient-to-r from-echelon-cyan/[0.06] to-transparent",
        isExpanded ? "justify-start gap-2.5 mx-2" : "justify-center mx-1.5"
      )}
        style={{ boxShadow: '0 0 20px rgba(34,211,238,0.10)' }}
      >
        {isExpanded ? (
          <span className="font-extrabold tracking-[0.14em] text-sm text-terminal-text whitespace-nowrap">
            ECHELON
          </span>
        ) : (
          <span className="w-8 h-8 rounded-lg bg-echelon-cyan/[0.12] border border-echelon-cyan/25 flex items-center justify-center font-extrabold tracking-[0.14em] text-sm text-terminal-text shadow-glow-cyan">
            E
          </span>
        )}
      </div>

      {/* Separator */}
      <div className="h-px bg-terminal-border/40 mx-3 my-1" />

      {/* Nav group */}
      <nav className={clsx(
        "flex flex-col gap-1 transition-all duration-300",
        isExpanded ? "px-2 mt-1" : "px-1.5 mt-0"
      )}>
        {isExpanded && (
          <span className="text-[10px] tracking-[0.08em] uppercase text-terminal-text-muted px-2 mt-1 mb-1">
            Console
          </span>
        )}

        {NAV_ITEMS.map((item) => {
          const active = isActive(item);
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={clsx(
                'flex items-center gap-2.5 py-2.5 rounded-r-lg text-xs font-semibold transition-all duration-200 select-none',
                isExpanded ? 'px-3' : 'px-2.5 justify-center',
                active
                  ? 'border-l-[3px] border-l-echelon-cyan bg-echelon-cyan/[0.10] text-terminal-text'
                  : 'border-l-[3px] border-l-transparent text-terminal-text-secondary hover:bg-terminal-card hover:text-terminal-text'
              )}
            >
              {isExpanded ? (
                <span className="whitespace-nowrap">{item.label}</span>
              ) : (
                <div className={clsx(
                  'p-1.5 rounded-lg transition-all duration-200',
                  active && 'ring-1 ring-echelon-cyan/25'
                )}>
                  <NavIcon item={item} className="w-4 h-4" />
                </div>
              )}
            </NavLink>
          );
        })}

        {/* Agents Subnav - shown when expanded and in Agents section */}
        {isExpanded && isAgentsSection && (
          <>
          <div className="h-px bg-terminal-border/40 mx-3 my-1" />
          <div className="mt-1 flex flex-col gap-1 pl-2 border-l border-terminal-border ml-3">
            {AGENTS_SUBNAV.map((item) => {
              const active = location.pathname === item.path;
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={clsx(
                    'flex items-center gap-2 px-2.5 py-2 rounded-lg text-xs font-medium transition-all duration-200',
                    active
                      ? 'text-status-info bg-status-info/10'
                      : 'text-terminal-text-muted hover:text-terminal-text-secondary hover:bg-terminal-panel'
                  )}
                >
                  {Icon && <Icon className="w-3.5 h-3.5 flex-shrink-0" />}
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </div>
          </>
        )}
      </nav>
    </aside>
  );
}

export default Sidebar;
